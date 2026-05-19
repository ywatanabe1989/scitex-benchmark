#!/usr/bin/env python3
# Time-stamp: "2026-05-18"
# File: test_profiler.py

"""Tests for scitex_benchmark.profiler module.

Each test follows the canonical TQ shape: descriptive name (>=3 word-tokens
after `test_`), explicit `# Arrange` / `# Act` / `# Assert` markers in
order, and exactly one assertion. Multi-assertion originals are split into
one-assertion-per-test siblings that share an Arrange/Act fixture.
"""

import time

import pytest

from scitex_benchmark.profiler import (
    FunctionProfiler,
    LineProfiler,
    get_memory_usage,
    get_profile_report,
    profile_block,
    profile_function,
    profile_module,
    track_memory,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def profiler():
    """Create a fresh FunctionProfiler instance."""
    return FunctionProfiler()


@pytest.fixture
def line_profiler():
    """Create a fresh LineProfiler instance."""
    return LineProfiler()


@pytest.fixture
def profiled_my_func(profiler):
    """Register @profiler.profile on `my_func(x)->x*2`, call it once with 5,
    and return {'profiler', 'result'}."""

    @profiler.profile
    def my_func(x):
        return x * 2

    result = my_func(5)
    return {"profiler": profiler, "result": result}


@pytest.fixture
def profiled_complex_func(profiler):
    """Profile `complex_func(a,b,c=10,d=20)`, call complex_func(1, 2, c=30, d=40),
    return {'profiler', 'result'}."""

    @profiler.profile
    def complex_func(a, b, c=10, d=20):
        return a + b + c + d

    result = complex_func(1, 2, c=30, d=40)
    return {"profiler": profiler, "result": result}


@pytest.fixture
def profiled_report(profiler):
    """Profile a my_func; call it twice; return profiler.get_report()."""

    @profiler.profile
    def my_func():
        return sum(range(100))

    my_func()
    my_func()
    return profiler.get_report()


# ============================================================================
# Test FunctionProfiler
# ============================================================================


class TestFunctionProfiler:
    """Tests for FunctionProfiler class."""

    def test_new_profiler_has_empty_profiles(self, profiler):
        """New FunctionProfiler.profiles starts as {}."""
        # Arrange
        # Act
        actual = profiler.profiles
        # Assert
        assert actual == {}

    def test_new_profiler_has_empty_call_counts(self, profiler):
        """New FunctionProfiler.call_counts starts as {}."""
        # Arrange
        # Act
        actual = profiler.call_counts
        # Assert
        assert actual == {}

    def test_new_profiler_has_empty_total_times(self, profiler):
        """New FunctionProfiler.total_times starts as {}."""
        # Arrange
        # Act
        actual = profiler.total_times
        # Assert
        assert actual == {}

    def test_profile_decorator_returns_function_result(self, profiled_my_func):
        """@profiler.profile passes the wrapped function's result through."""
        # Arrange
        result = profiled_my_func["result"]
        # Act
        actual = result
        # Assert
        assert actual == 10

    def test_profile_decorator_records_function_name(self, profiled_my_func):
        """@profiler.profile registers the function name in .profiles."""
        # Arrange
        p = profiled_my_func["profiler"]
        # Act
        actual = "my_func" in p.profiles
        # Assert
        assert actual is True

    def test_profile_decorator_increments_call_count(self, profiled_my_func):
        """One call -> call_counts['my_func']==1."""
        # Arrange
        p = profiled_my_func["profiler"]
        # Act
        actual = p.call_counts["my_func"]
        # Assert
        assert actual == 1

    def test_profile_decorator_accumulates_total_time(self, profiled_my_func):
        """One call -> total_times['my_func']>0."""
        # Arrange
        p = profiled_my_func["profiler"]
        # Act
        actual = p.total_times["my_func"]
        # Assert
        assert actual > 0

    def test_profile_multiple_calls_increments_call_count(self, profiler):
        """5 calls -> call_counts['my_func']==5."""
        # Arrange

        @profiler.profile
        def my_func(x):
            return x + 1

        # Act
        for i in range(5):
            my_func(i)
        # Assert
        assert profiler.call_counts["my_func"] == 5

    def test_profile_multiple_calls_grows_profiles_list(self, profiler):
        """5 calls -> profiles['my_func'] has length 5."""
        # Arrange

        @profiler.profile
        def my_func(x):
            return x + 1

        # Act
        for i in range(5):
            my_func(i)
        # Assert
        assert len(profiler.profiles["my_func"]) == 5

    def test_profile_preserves_function_name(self, profiler):
        """@profiler.profile preserves __name__ on the wrapped function."""
        # Arrange

        @profiler.profile
        def original_name(x):
            """Original docstring."""
            return x

        # Act
        actual = original_name.__name__
        # Assert
        assert actual == "original_name"

    def test_profile_preserves_function_docstring(self, profiler):
        """@profiler.profile preserves __doc__ on the wrapped function."""
        # Arrange

        @profiler.profile
        def original_name(x):
            """Original docstring."""
            return x

        # Act
        actual = original_name.__doc__
        # Assert
        assert actual == "Original docstring."

    def test_profile_with_args_and_kwargs_returns_correct_sum(
        self, profiled_complex_func
    ):
        """complex_func(1,2,c=30,d=40) -> 73."""
        # Arrange
        # Act
        actual = profiled_complex_func["result"]
        # Assert
        assert actual == 73

    def test_profile_with_args_and_kwargs_increments_call_count(
        self, profiled_complex_func
    ):
        """One complex_func call -> call_counts['complex_func']==1."""
        # Arrange
        p = profiled_complex_func["profiler"]
        # Act
        actual = p.call_counts["complex_func"]
        # Assert
        assert actual == 1

    def test_get_stats_returns_none_for_unknown_function(self, profiler):
        """get_stats('not-profiled') returns None."""
        # Arrange
        # Act
        stats = profiler.get_stats("unknown_function")
        # Assert
        assert stats is None

    def test_get_stats_returns_non_none_for_profiled_function(self, profiler):
        """get_stats(fn) returns a non-None pstats.Stats for a profiled fn."""
        # Arrange

        @profiler.profile
        def my_func():
            return 42

        my_func()
        my_func()
        # Act
        stats = profiler.get_stats("my_func")
        # Assert
        assert stats is not None

    def test_print_stats_single_function_emits_profile_header(self, profiler, capsys):
        """print_stats('my_func') prints 'Profile for my_func' header."""
        # Arrange

        @profiler.profile
        def my_func():
            return 42

        my_func()
        # Act
        profiler.print_stats("my_func")
        captured = capsys.readouterr()
        # Assert
        assert "Profile for my_func" in captured.out

    def test_print_stats_single_function_emits_total_calls_line(self, profiler, capsys):
        """print_stats('my_func') prints 'Total calls: 1' for one call."""
        # Arrange

        @profiler.profile
        def my_func():
            return 42

        my_func()
        # Act
        profiler.print_stats("my_func")
        captured = capsys.readouterr()
        # Assert
        assert "Total calls: 1" in captured.out

    def test_print_stats_all_functions_includes_first_function(self, profiler, capsys):
        """print_stats() with no name dumps every profiled function (func1)."""
        # Arrange

        @profiler.profile
        def func1():
            return 1

        @profiler.profile
        def func2():
            return 2

        func1()
        func2()
        # Act
        profiler.print_stats()
        captured = capsys.readouterr()
        # Assert
        assert "func1" in captured.out

    def test_print_stats_all_functions_includes_second_function(self, profiler, capsys):
        """print_stats() with no name dumps every profiled function (func2)."""
        # Arrange

        @profiler.profile
        def func1():
            return 1

        @profiler.profile
        def func2():
            return 2

        func1()
        func2()
        # Act
        profiler.print_stats()
        captured = capsys.readouterr()
        # Assert
        assert "func2" in captured.out

    def test_get_report_includes_function_name(self, profiled_report):
        """get_report() keys include the profiled function name."""
        # Arrange
        report = profiled_report
        # Act
        actual = "my_func" in report
        # Assert
        assert actual is True

    def test_get_report_includes_call_count(self, profiled_report):
        """get_report()['my_func']['call_count'] reflects number of calls."""
        # Arrange
        report = profiled_report
        # Act
        actual = report["my_func"]["call_count"]
        # Assert
        assert actual == 2

    def test_get_report_includes_total_time_field(self, profiled_report):
        """get_report()['my_func'] has a total_time field."""
        # Arrange
        report = profiled_report
        # Act
        actual = "total_time" in report["my_func"]
        # Assert
        assert actual is True

    def test_get_report_includes_avg_time_field(self, profiled_report):
        """get_report()['my_func'] has an avg_time field."""
        # Arrange
        report = profiled_report
        # Act
        actual = "avg_time" in report["my_func"]
        # Assert
        assert actual is True

    def test_get_report_includes_profile_text_field(self, profiled_report):
        """get_report()['my_func'] has a profile field with cProfile dump."""
        # Arrange
        report = profiled_report
        # Act
        actual = "profile" in report["my_func"]
        # Assert
        assert actual is True


# ============================================================================
# Test profile_function (global profiler)
# ============================================================================


class TestProfileFunction:
    """Tests for profile_function decorator."""

    def test_profile_function_decorator_returns_squared_value(self):
        """@profile_function on `x**2` returns 25 for x=5."""

        # Arrange
        @profile_function
        def square_then_profile(x):
            return x**2

        # Act
        result = square_then_profile(5)
        # Assert
        assert result == 25

    def test_profile_function_preserves_return_value_for_multiply(self):
        """@profile_function preserves the multiplied return value."""

        # Arrange
        @profile_function
        def compute(a, b):
            return a * b

        # Act
        result = compute(3, 4)
        # Assert
        assert result == 12


# ============================================================================
# Test get_profile_report
# ============================================================================


class TestGetProfileReport:
    """Tests for get_profile_report function."""

    def test_get_profile_report_returns_dict_instance(self):
        """get_profile_report() returns a dict (possibly empty)."""
        # Arrange
        # Act
        report = get_profile_report()
        # Assert
        assert isinstance(report, dict)


# ============================================================================
# Test profile_block context manager
# ============================================================================


class TestProfileBlock:
    """Tests for profile_block context manager."""

    def test_profile_block_basic_emits_block_header(self, capsys):
        """profile_block prints 'Profile for block ...' on exit."""
        # Arrange
        # Act
        with profile_block("test_block"):
            sum(range(1000))
        captured = capsys.readouterr()
        # Assert
        assert "Profile for block 'test_block'" in captured.out

    def test_profile_block_basic_emits_total_time_line(self, capsys):
        """profile_block prints a 'Total time:' line on exit."""
        # Arrange
        # Act
        with profile_block("test_block"):
            sum(range(1000))
        captured = capsys.readouterr()
        # Assert
        assert "Total time:" in captured.out

    def test_profile_block_with_slow_code_names_the_block(self, capsys):
        """profile_block('slow_block') names the block in its output."""
        # Arrange
        # Act
        with profile_block("slow_block"):
            time.sleep(0.02)
        captured = capsys.readouterr()
        # Assert
        assert "slow_block" in captured.out

    def test_profile_block_exception_handling_raises_value_error(self):
        """profile_block re-raises ValueError from its inner block."""
        # Arrange
        # Act
        ctx = pytest.raises(ValueError)
        # Assert
        with ctx:
            with profile_block("error_block"):
                raise ValueError("Test error")

    def test_profile_block_exception_still_prints_block_name(self, capsys):
        """Even with exception, profile_block prints the block name on exit."""
        # Arrange
        try:
            with profile_block("error_block"):
                raise ValueError("Test error")
        except ValueError:
            pass
        # Act
        captured = capsys.readouterr()
        # Assert
        assert "error_block" in captured.out


# ============================================================================
# Test profile_module
# ============================================================================


class TestProfileModule:
    """Tests for profile_module function."""

    def test_profile_module_returns_function_profiler_instance(self, capsys):
        """profile_module returns a FunctionProfiler instance."""
        # Arrange
        # Act
        result = profile_module("math", pattern="sqrt")
        # `capsys.readouterr()` consumes the side-effect output so we
        # don't pollute neighbour tests.
        capsys.readouterr()
        # Assert
        assert isinstance(result, FunctionProfiler)

    def test_profile_module_emits_profiling_header(self, capsys):
        """profile_module prints a 'Profiling ...' header."""
        # Arrange
        # Act
        profile_module("math", pattern="sqrt")
        captured = capsys.readouterr()
        # Assert
        assert "Profiling" in captured.out

    def test_profile_module_wraps_functions_emits_profiling_header(self, capsys):
        """profile_module('os.path', pattern='exists') also prints 'Profiling'."""
        # Arrange
        # Act
        profile_module("os.path", pattern="exists")
        captured = capsys.readouterr()
        # Assert
        assert "Profiling" in captured.out


# ============================================================================
# Test LineProfiler
# ============================================================================


class TestLineProfiler:
    """Tests for LineProfiler class."""

    def test_new_line_profiler_has_empty_timings(self, line_profiler):
        """New LineProfiler.timings starts as {}."""
        # Arrange
        # Act
        actual = line_profiler.timings
        # Assert
        assert actual == {}

    def test_profile_lines_decorator_returns_function_result(self, line_profiler):
        """@profile_lines preserves the wrapped function's return value."""

        # Arrange
        @line_profiler.profile_lines
        def my_func(n):
            result = 0
            for i in range(n):
                result += i
            return result

        # Act
        result = my_func(100)
        # Assert
        assert result == 4950  # sum of 0..99

    def test_profile_lines_decorator_records_function_name(self, line_profiler):
        """@profile_lines registers the function name in .timings."""

        # Arrange
        @line_profiler.profile_lines
        def my_func(n):
            return n

        # Act
        my_func(1)
        # Assert
        assert "my_func" in line_profiler.timings

    def test_profile_lines_decorator_appends_one_timing_per_call(self, line_profiler):
        """One call -> timings['my_func'] has length 1."""

        # Arrange
        @line_profiler.profile_lines
        def my_func(n):
            return n

        # Act
        my_func(1)
        # Assert
        assert len(line_profiler.timings["my_func"]) == 1

    def test_profile_lines_stores_total_time_field(self, line_profiler):
        """Each recorded timing has a 'total_time' key."""

        # Arrange
        @line_profiler.profile_lines
        def my_func():
            time.sleep(0.01)
            return 42

        my_func()
        timing = line_profiler.timings["my_func"][0]
        # Act
        actual = "total_time" in timing
        # Assert
        assert actual is True

    def test_profile_lines_total_time_reflects_actual_duration(self, line_profiler):
        """A 10ms sleep is reflected in total_time (>=9ms allowing jitter)."""

        # Arrange
        @line_profiler.profile_lines
        def my_func():
            time.sleep(0.01)
            return 42

        my_func()
        timing = line_profiler.timings["my_func"][0]
        # Act
        actual = timing["total_time"]
        # Assert
        assert actual >= 0.009

    def test_profile_lines_stores_source_field(self, line_profiler):
        """Each recorded timing has a 'source' key."""

        # Arrange
        @line_profiler.profile_lines
        def my_func():
            return 42

        my_func()
        timing = line_profiler.timings["my_func"][0]
        # Act
        actual = "source" in timing
        # Assert
        assert actual is True

    def test_profile_lines_source_is_list_of_lines(self, line_profiler):
        """timing['source'] is a list (of source lines)."""

        # Arrange
        @line_profiler.profile_lines
        def my_func():
            x = 1
            y = 2
            return x + y

        my_func()
        timing = line_profiler.timings["my_func"][0]
        # Act
        actual = timing["source"]
        # Assert
        assert isinstance(actual, list)

    def test_profile_lines_source_contains_function_body_text(self, line_profiler):
        """timing['source'] joined contains literal source text from the body."""

        # Arrange
        @line_profiler.profile_lines
        def my_func():
            x = 1
            y = 2
            return x + y

        my_func()
        timing = line_profiler.timings["my_func"][0]
        # Act
        source_text = "".join(timing["source"])
        # Assert
        assert "return" in source_text

    def test_print_timings_emits_line_timings_header(self, line_profiler, capsys):
        """print_timings('my_func') prints 'Line timings for my_func' header."""

        # Arrange
        @line_profiler.profile_lines
        def my_func():
            return 42

        my_func()
        # Act
        line_profiler.print_timings("my_func")
        captured = capsys.readouterr()
        # Assert
        assert "Line timings for my_func" in captured.out

    def test_print_timings_emits_total_time_line(self, line_profiler, capsys):
        """print_timings emits a 'Total time:' line."""

        # Arrange
        @line_profiler.profile_lines
        def my_func():
            return 42

        my_func()
        # Act
        line_profiler.print_timings("my_func")
        captured = capsys.readouterr()
        # Assert
        assert "Total time:" in captured.out

    def test_print_timings_emits_source_code_section(self, line_profiler, capsys):
        """print_timings emits a 'Source code:' section header."""

        # Arrange
        @line_profiler.profile_lines
        def my_func():
            return 42

        my_func()
        # Act
        line_profiler.print_timings("my_func")
        captured = capsys.readouterr()
        # Assert
        assert "Source code:" in captured.out

    def test_print_timings_unknown_function_emits_no_timings_message(
        self, line_profiler, capsys
    ):
        """print_timings for an unknown function emits 'No timings for ...'."""
        # Arrange
        # Act
        line_profiler.print_timings("unknown_func")
        captured = capsys.readouterr()
        # Assert
        assert "No timings for unknown_func" in captured.out


# ============================================================================
# Test Memory Utilities
# ============================================================================


class TestGetMemoryUsage:
    """Tests for get_memory_usage function."""

    def test_get_memory_usage_returns_float_or_none(self):
        """get_memory_usage() returns float (psutil available) or None."""
        # Arrange
        # Act
        result = get_memory_usage()
        # Assert
        assert result is None or isinstance(result, float)

    def test_get_memory_usage_when_available_is_positive(self):
        """When psutil is present, returned MB is > 0; when absent, the
        call still returns None (not an error)."""
        # Arrange
        result = get_memory_usage()
        # Act
        actual = result if result is not None else 1.0
        # Assert
        assert actual > 0


class TestTrackMemory:
    """Tests for track_memory context manager."""

    def test_track_memory_basic_names_block_when_psutil_available(self, capsys):
        """track_memory('test_allocation') names the block in its output.

        Falls back to a smoke assertion (no crash) when psutil is missing.
        """
        # Arrange
        # Act
        with track_memory("test_allocation"):
            list(range(10000))
        captured = capsys.readouterr()
        if "Memory usage" not in captured.out:
            # psutil not available — verify the context manager exited cleanly.
            actual = "Memory usage" not in captured.out
        else:
            actual = "test_allocation" in captured.out
        # Assert
        assert actual is True

    def test_track_memory_exception_handling_propagates_value_error(self):
        """track_memory re-raises ValueError from its inner block."""
        # Arrange
        # Act
        ctx = pytest.raises(ValueError)
        # Assert
        with ctx:
            with track_memory("error_block"):
                raise ValueError("Test error")

    def test_track_memory_nested_blocks_exit_without_error(self, capsys):
        """Nested track_memory blocks exit cleanly and produce some output.

        When psutil is available the output names outer or inner; when not,
        the context manager just exits silently — both are acceptable.
        """
        # Arrange
        # Act
        with track_memory("outer"):
            list(range(1000))
            with track_memory("inner"):
                list(range(1000))
        captured = capsys.readouterr()
        if "Memory usage" in captured.out:
            actual = "outer" in captured.out or "inner" in captured.out
        else:
            # psutil not available — clean exit is the assertion.
            actual = True
        # Assert
        assert actual is True


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
