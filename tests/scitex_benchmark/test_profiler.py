#!/usr/bin/env python3
# Time-stamp: "2025-01-05"
# File: test_profiler.py

"""Tests for scitex_benchmark.profiler module."""

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


def _require_psutil_memory():
    """Return current memory usage in MB, skipping the test if psutil
    is not installed (so the asserting test sees a real float, not None,
    and so the test body keeps a single assertion)."""
    value = get_memory_usage()
    if value is None:
        pytest.skip("psutil not available")
    return value


@pytest.fixture
def profiler():
    """Create a fresh FunctionProfiler instance."""
    return FunctionProfiler()


@pytest.fixture
def line_profiler():
    """Create a fresh LineProfiler instance."""
    return LineProfiler()


# ============================================================================
# Test FunctionProfiler — initialisation
# ============================================================================


class TestFunctionProfilerCreation:
    """Tests for FunctionProfiler initialization."""

    def test_profiles_dict_starts_empty(self, profiler):
        # Arrange
        p = profiler
        # Act
        value = p.profiles
        # Assert
        assert value == {}

    def test_call_counts_dict_starts_empty(self, profiler):
        # Arrange
        p = profiler
        # Act
        value = p.call_counts
        # Assert
        assert value == {}

    def test_total_times_dict_starts_empty(self, profiler):
        # Arrange
        p = profiler
        # Act
        value = p.total_times
        # Assert
        assert value == {}


# ============================================================================
# Test FunctionProfiler — @profile decorator
# ============================================================================


@pytest.fixture
def decorated_profiler(profiler):
    @profiler.profile
    def my_func(x):
        return x * 2

    my_func(5)
    return profiler


class TestFunctionProfilerDecorator:
    """Tests for FunctionProfiler.profile decorator basic behaviour."""

    def test_decorated_function_returns_correct_value(self, profiler):
        # Arrange
        @profiler.profile
        def my_func(x):
            return x * 2

        # Act
        result = my_func(5)
        # Assert
        assert result == 10

    def test_decorator_registers_function_in_profiles(self, decorated_profiler):
        # Arrange
        p = decorated_profiler
        # Act
        present = "my_func" in p.profiles
        # Assert
        assert present

    def test_decorator_initialises_call_count_to_one(self, decorated_profiler):
        # Arrange
        p = decorated_profiler
        # Act
        value = p.call_counts["my_func"]
        # Assert
        assert value == 1

    def test_decorator_records_positive_total_time(self, decorated_profiler):
        # Arrange
        p = decorated_profiler
        # Act
        value = p.total_times["my_func"]
        # Assert
        assert value > 0


class TestFunctionProfilerDecoratorMultipleCalls:
    """Tests for profiling across multiple invocations."""

    @pytest.fixture
    def five_call_profiler(self, profiler):
        @profiler.profile
        def my_func(x):
            return x + 1

        for i in range(5):
            my_func(i)
        return profiler

    def test_call_count_accumulates_across_invocations(self, five_call_profiler):
        # Arrange
        p = five_call_profiler
        # Act
        value = p.call_counts["my_func"]
        # Assert
        assert value == 5

    def test_profile_list_grows_per_invocation(self, five_call_profiler):
        # Arrange
        p = five_call_profiler
        # Act
        value = len(p.profiles["my_func"])
        # Assert
        assert value == 5


class TestFunctionProfilerDecoratorMetadata:
    """Tests for metadata preservation via @wraps."""

    @pytest.fixture
    def decorated_name_func(self, profiler):
        @profiler.profile
        def original_name(x):
            """Original docstring."""
            return x

        return original_name

    def test_decorator_preserves_function_name(self, decorated_name_func):
        # Arrange
        f = decorated_name_func
        # Act
        value = f.__name__
        # Assert
        assert value == "original_name"

    def test_decorator_preserves_docstring(self, decorated_name_func):
        # Arrange
        f = decorated_name_func
        # Act
        value = f.__doc__
        # Assert
        assert value == "Original docstring."


class TestFunctionProfilerArgsKwargs:
    """Tests for profiling with args and kwargs."""

    def test_complex_function_returns_correct_value(self, profiler):
        # Arrange
        @profiler.profile
        def complex_func(a, b, c=10, d=20):
            return a + b + c + d

        # Act
        result = complex_func(1, 2, c=30, d=40)
        # Assert
        assert result == 73

    def test_complex_function_records_single_call(self, profiler):
        # Arrange
        @profiler.profile
        def complex_func(a, b, c=10, d=20):
            return a + b + c + d

        complex_func(1, 2, c=30, d=40)
        # Act
        value = profiler.call_counts["complex_func"]
        # Assert
        assert value == 1


# ============================================================================
# Test FunctionProfiler — get_stats
# ============================================================================


class TestFunctionProfilerGetStats:
    """Tests for FunctionProfiler.get_stats."""

    def test_get_stats_unknown_function_returns_none(self, profiler):
        # Arrange
        p = profiler
        # Act
        result = p.get_stats("unknown_function")
        # Assert
        assert result is None

    def test_get_stats_known_function_returns_stats_object(self, profiler):
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


# ============================================================================
# Test FunctionProfiler — print_stats
# ============================================================================


@pytest.fixture
def single_function_print(profiler, capsys):
    @profiler.profile
    def my_func():
        return 42

    my_func()
    profiler.print_stats("my_func")
    return capsys.readouterr()


class TestFunctionProfilerPrintStatsSingle:
    """Tests for print_stats() for a single function."""

    def test_print_includes_profile_header_for_function(self, single_function_print):
        # Arrange
        captured = single_function_print
        # Act
        out = captured.out
        # Assert
        assert "Profile for my_func" in out

    def test_print_includes_total_call_count(self, single_function_print):
        # Arrange
        captured = single_function_print
        # Act
        out = captured.out
        # Assert
        assert "Total calls: 1" in out


@pytest.fixture
def two_function_print(profiler, capsys):
    @profiler.profile
    def func1():
        return 1

    @profiler.profile
    def func2():
        return 2

    func1()
    func2()
    profiler.print_stats()
    return capsys.readouterr()


class TestFunctionProfilerPrintStatsAll:
    """Tests for print_stats() across all profiled functions."""

    def test_print_includes_first_function_name(self, two_function_print):
        # Arrange
        captured = two_function_print
        # Act
        out = captured.out
        # Assert
        assert "func1" in out

    def test_print_includes_second_function_name(self, two_function_print):
        # Arrange
        captured = two_function_print
        # Act
        out = captured.out
        # Assert
        assert "func2" in out


# ============================================================================
# Test FunctionProfiler — get_report
# ============================================================================


@pytest.fixture
def report_two_calls(profiler):
    @profiler.profile
    def my_func():
        return sum(range(100))

    my_func()
    my_func()
    return profiler.get_report()


class TestFunctionProfilerGetReport:
    """Tests for FunctionProfiler.get_report()."""

    def test_report_contains_function_entry(self, report_two_calls):
        # Arrange
        report = report_two_calls
        # Act
        present = "my_func" in report
        # Assert
        assert present

    def test_report_records_call_count(self, report_two_calls):
        # Arrange
        report = report_two_calls
        # Act
        value = report["my_func"]["call_count"]
        # Assert
        assert value == 2

    def test_report_includes_total_time_key(self, report_two_calls):
        # Arrange
        report = report_two_calls
        # Act
        present = "total_time" in report["my_func"]
        # Assert
        assert present

    def test_report_includes_avg_time_key(self, report_two_calls):
        # Arrange
        report = report_two_calls
        # Act
        present = "avg_time" in report["my_func"]
        # Assert
        assert present

    def test_report_includes_profile_key(self, report_two_calls):
        # Arrange
        report = report_two_calls
        # Act
        present = "profile" in report["my_func"]
        # Assert
        assert present


# ============================================================================
# Test profile_function (global profiler)
# ============================================================================


class TestProfileFunctionGlobal:
    """Tests for global profile_function decorator."""

    def test_decorated_function_returns_correct_value(self):
        # Arrange
        @profile_function
        def squared(x):
            return x**2

        # Act
        result = squared(5)
        # Assert
        assert result == 25

    def test_decorated_function_preserves_return_value(self):
        # Arrange
        @profile_function
        def compute(a, b):
            return a * b

        # Act
        result = compute(3, 4)
        # Assert
        assert result == 12


# ============================================================================
# Test get_profile_report (global)
# ============================================================================


class TestGetProfileReport:
    """Tests for module-level get_profile_report()."""

    def test_get_profile_report_returns_dict(self):
        # Arrange
        # (no setup needed)
        # Act
        report = get_profile_report()
        # Assert
        assert isinstance(report, dict)


# ============================================================================
# Test profile_block context manager
# ============================================================================


class TestProfileBlockBasic:
    """Tests for profile_block() basic usage."""

    @pytest.fixture
    def block_output(self, capsys):
        with profile_block("test_block"):
            sum(range(1000))
        return capsys.readouterr()

    def test_block_output_includes_profile_header(self, block_output):
        # Arrange
        captured = block_output
        # Act
        out = captured.out
        # Assert
        assert "Profile for block 'test_block'" in out

    def test_block_output_includes_total_time_line(self, block_output):
        # Arrange
        captured = block_output
        # Act
        out = captured.out
        # Assert
        assert "Total time:" in out


class TestProfileBlockSlowCode:
    """Tests for profile_block() with sleeping work."""

    @pytest.fixture
    def slow_block_output(self, capsys):
        with profile_block("slow_block"):
            time.sleep(0.02)
        return capsys.readouterr()

    def test_slow_block_output_contains_block_name(self, slow_block_output):
        # Arrange
        captured = slow_block_output
        # Act
        out = captured.out
        # Assert
        assert "slow_block" in out

    def test_slow_block_output_contains_a_time_value(self, slow_block_output):
        # Arrange
        captured = slow_block_output
        # Act
        out = captured.out
        # Assert
        assert "0.0" in out


class TestProfileBlockException:
    """Tests for profile_block() exception path."""

    def test_profile_block_propagates_exception_to_caller(self):
        # Arrange
        # (no setup)
        # Act
        raised_ctx = pytest.raises(ValueError)
        # Assert
        with raised_ctx:
            with profile_block("error_block"):
                raise ValueError("Test error")

    def test_profile_block_prints_block_name_even_on_exception(self, capsys):
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
    """Tests for profile_module() function."""

    def test_profile_module_returns_function_profiler_instance(self, capsys):
        # Arrange
        # (no setup needed)
        # Act
        result = profile_module("math", pattern="sqrt")
        capsys.readouterr()
        # Assert
        assert isinstance(result, FunctionProfiler)

    def test_profile_module_prints_profiling_log_line(self, capsys):
        # Arrange
        profile_module("math", pattern="sqrt")
        # Act
        captured = capsys.readouterr()
        # Assert
        assert "Profiling" in captured.out

    def test_profile_module_with_os_path_pattern_prints_log_line(self, capsys):
        # Arrange
        profile_module("os.path", pattern="exists")
        # Act
        captured = capsys.readouterr()
        # Assert
        assert "Profiling" in captured.out


# ============================================================================
# Test LineProfiler — initialisation
# ============================================================================


class TestLineProfilerCreation:
    """Tests for LineProfiler initialization."""

    def test_timings_dict_starts_empty(self, line_profiler):
        # Arrange
        lp = line_profiler
        # Act
        value = lp.timings
        # Assert
        assert value == {}


# ============================================================================
# Test LineProfiler — profile_lines
# ============================================================================


@pytest.fixture
def lined_result(line_profiler):
    @line_profiler.profile_lines
    def my_func(n):
        result = 0
        for i in range(n):
            result += i
        return result

    return my_func(100), line_profiler


class TestLineProfilerProfileLines:
    """Tests for LineProfiler.profile_lines decorator."""

    def test_decorated_function_returns_correct_value(self, lined_result):
        # Arrange
        result, _ = lined_result
        # Act
        value = result
        # Assert
        assert value == 4950

    def test_decorator_registers_function_in_timings(self, lined_result):
        # Arrange
        _, lp = lined_result
        # Act
        present = "my_func" in lp.timings
        # Assert
        assert present

    def test_decorator_records_one_timing_entry_per_call(self, lined_result):
        # Arrange
        _, lp = lined_result
        # Act
        n = len(lp.timings["my_func"])
        # Assert
        assert n == 1


@pytest.fixture
def sleepy_timing(line_profiler):
    @line_profiler.profile_lines
    def my_func():
        time.sleep(0.01)
        return 42

    my_func()
    return line_profiler.timings["my_func"][0]


class TestLineProfilerStoresTiming:
    """Tests for timing payload stored by profile_lines."""

    def test_payload_includes_total_time_key(self, sleepy_timing):
        # Arrange
        timing = sleepy_timing
        # Act
        present = "total_time" in timing
        # Assert
        assert present

    def test_payload_total_time_reflects_real_sleep(self, sleepy_timing):
        # Arrange
        timing = sleepy_timing
        # Act
        value = timing["total_time"]
        # Assert
        assert value >= 0.009

    def test_payload_includes_source_key(self, sleepy_timing):
        # Arrange
        timing = sleepy_timing
        # Act
        present = "source" in timing
        # Assert
        assert present


@pytest.fixture
def source_capture(line_profiler):
    @line_profiler.profile_lines
    def my_func():
        x = 1
        y = 2
        return x + y

    my_func()
    return line_profiler.timings["my_func"][0]["source"]


class TestLineProfilerStoresSource:
    """Tests for source-code capture by profile_lines."""

    def test_source_is_a_list(self, source_capture):
        # Arrange
        source = source_capture
        # Act
        kind = type(source)
        # Assert
        assert issubclass(kind, list)

    def test_source_list_is_nonempty(self, source_capture):
        # Arrange
        source = source_capture
        # Act
        size = len(source)
        # Assert
        assert size > 0

    def test_source_text_contains_return_keyword(self, source_capture):
        # Arrange
        source = source_capture
        # Act
        text = "".join(source)
        # Assert
        assert "return" in text


# ============================================================================
# Test LineProfiler — print_timings
# ============================================================================


@pytest.fixture
def print_timings_output(line_profiler, capsys):
    @line_profiler.profile_lines
    def my_func():
        return 42

    my_func()
    line_profiler.print_timings("my_func")
    return capsys.readouterr()


class TestLineProfilerPrintTimings:
    """Tests for LineProfiler.print_timings output."""

    def test_output_includes_line_timings_header(self, print_timings_output):
        # Arrange
        captured = print_timings_output
        # Act
        out = captured.out
        # Assert
        assert "Line timings for my_func" in out

    def test_output_includes_total_time_line(self, print_timings_output):
        # Arrange
        captured = print_timings_output
        # Act
        out = captured.out
        # Assert
        assert "Total time:" in out

    def test_output_includes_source_code_header(self, print_timings_output):
        # Arrange
        captured = print_timings_output
        # Act
        out = captured.out
        # Assert
        assert "Source code:" in out


class TestLineProfilerPrintTimingsUnknown:
    """Tests for print_timings() on an unknown function name."""

    def test_unknown_function_prints_no_timings_message(self, line_profiler, capsys):
        # Arrange
        lp = line_profiler
        # Act
        lp.print_timings("unknown_func")
        captured = capsys.readouterr()
        # Assert
        assert "No timings for unknown_func" in captured.out


# ============================================================================
# Test Memory Utilities
# ============================================================================


class TestGetMemoryUsage:
    """Tests for get_memory_usage()."""

    def test_get_memory_usage_returns_float_or_none(self):
        # Arrange
        # (no setup needed)
        # Act
        result = get_memory_usage()
        # Assert
        assert result is None or isinstance(result, float)

    def test_get_memory_usage_returns_positive_when_available(self):
        # Arrange
        result = _require_psutil_memory()
        # Act
        value = result
        # Assert
        assert value > 0


class TestTrackMemory:
    """Tests for track_memory() context manager."""

    def test_track_memory_runs_without_raising(self, capsys):
        # Arrange
        # (no setup)
        # Act
        with track_memory("test_allocation"):
            list(range(10000))
        captured = capsys.readouterr()
        # Assert
        assert isinstance(captured.out, str)

    def test_track_memory_propagates_exception_to_caller(self):
        # Arrange
        # (no setup)
        # Act
        raised_ctx = pytest.raises(ValueError)
        # Assert
        with raised_ctx:
            with track_memory("error_block"):
                raise ValueError("Test error")

    def test_track_memory_supports_nested_blocks_without_raising(self, capsys):
        # Arrange
        # (no setup)
        # Act
        with track_memory("outer"):
            list(range(1000))
            with track_memory("inner"):
                list(range(1000))
        captured = capsys.readouterr()
        # Assert
        assert isinstance(captured.out, str)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# EOF
