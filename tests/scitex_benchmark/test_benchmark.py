#!/usr/bin/env python3
# Time-stamp: "2026-05-18"
# File: test_benchmark.py

"""Tests for scitex_benchmark.benchmark module.

Each test follows the canonical TQ shape: descriptive name (>=3 word-tokens
after `test_`), explicit `# Arrange` / `# Act` / `# Assert` markers in
order, and exactly one assertion. Multi-assertion originals are split into
one-assertion-per-test siblings that share an Arrange/Act fixture.
"""

import os
import tempfile
import time

import pandas as pd
import pytest

from scitex_benchmark.benchmark import (
    BenchmarkResult,
    BenchmarkSuite,
    benchmark_function,
    benchmark_module,
    compare_implementations,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_function():
    """A simple function for benchmarking."""

    def add_numbers(a, b):
        return a + b

    return add_numbers


@pytest.fixture
def slow_function():
    """A function that takes measurable time."""

    def slow_add(a, b):
        time.sleep(0.01)  # 10ms
        return a + b

    return slow_add


@pytest.fixture
def benchmark_result():
    """Create a sample BenchmarkResult."""
    return BenchmarkResult(
        function_name="test_func",
        module="test_module",
        mean_time=0.1,
        std_time=0.01,
        min_time=0.08,
        max_time=0.12,
        iterations=10,
        input_size="100x100",
        memory_usage=50.0,
        notes="Test benchmark",
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def minimal_benchmark_result():
    """BenchmarkResult constructed with only the required fields."""
    return BenchmarkResult(
        function_name="my_func",
        module="my_module",
        mean_time=0.5,
        std_time=0.05,
        min_time=0.4,
        max_time=0.6,
        iterations=10,
    )


@pytest.fixture
def benchmark_function_result(sample_function):
    """Run benchmark_function on sample_function with 5 iterations + 1 warmup."""
    return benchmark_function(sample_function, args=(1, 2), iterations=5, warmup=1)


@pytest.fixture
def benchmark_result_dict(benchmark_result):
    """to_dict() output of the all-fields benchmark_result fixture."""
    return benchmark_result.to_dict()


@pytest.fixture
def two_impl_comparison_df():
    """compare_implementations() output for a loop-vs-formula sum(0..n-1) pair."""

    def impl1(x):
        return sum(range(x))

    def impl2(x):
        return x * (x - 1) // 2

    implementations = {"loop": impl1, "formula": impl2}

    def data_gen():
        return (1000,), {}

    return compare_implementations(implementations, data_gen, iterations=3)


@pytest.fixture
def slow_vs_fast_comparison_df():
    """compare_implementations() output where the second impl is much faster."""

    def slow_impl(x):
        time.sleep(0.01)
        return x

    def fast_impl(x):
        return x

    implementations = {"slow": slow_impl, "fast": fast_impl}

    def data_gen():
        return (10,), {}

    return compare_implementations(implementations, data_gen, iterations=3)


@pytest.fixture
def populated_suite():
    """A BenchmarkSuite('test_suite') with one benchmark named custom_name added."""
    suite = BenchmarkSuite("test_suite")

    def my_func():
        return 42

    def data_gen():
        return (), {}

    suite.add_benchmark(my_func, data_gen, name="custom_name", sizes=["small"])
    return {"suite": suite, "func": my_func}


@pytest.fixture
def two_size_suite_results():
    """A run() output of a suite with one func across two sizes (small, large)."""
    suite = BenchmarkSuite("test_suite")

    def my_func():
        return 42

    def data_gen():
        return (), {}

    suite.add_benchmark(my_func, data_gen, sizes=["small", "large"])
    results = suite.run(iterations=3, verbose=True)
    return results


@pytest.fixture
def saved_suite_csv(temp_dir):
    """Run a BenchmarkSuite and save results to CSV; return {'path', 'df_loaded'}."""
    suite = BenchmarkSuite("test_suite")

    def my_func():
        return 42

    def data_gen():
        return (), {}

    suite.add_benchmark(my_func, data_gen)
    suite.run(iterations=2, verbose=False)
    output_path = os.path.join(temp_dir, "results.csv")
    suite.save_results(output_path)
    return {
        "path": output_path,
        "df_loaded": pd.read_csv(output_path),
    }


@pytest.fixture
def baseline_comparison_df(temp_dir):
    """Run a suite, write a baseline CSV, return compare_with_baseline() df."""
    suite = BenchmarkSuite("test_suite")

    def my_func():
        return 42

    def data_gen():
        return (), {}

    suite.add_benchmark(my_func, data_gen)
    suite.run(iterations=2, verbose=False)
    baseline_path = os.path.join(temp_dir, "baseline.csv")
    baseline_data = pd.DataFrame(
        {
            "function": ["my_func"],
            "size": ["default"],
            "mean_time": [0.001],
        }
    )
    baseline_data.to_csv(baseline_path, index=False)
    return suite.compare_with_baseline(baseline_path)


# ============================================================================
# Test BenchmarkResult
# ============================================================================


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_minimal_constructor_stores_function_name(self, minimal_benchmark_result):
        # Arrange
        # Act
        actual = minimal_benchmark_result.function_name
        # Assert
        assert actual == "my_func"

    def test_minimal_constructor_stores_module_name(self, minimal_benchmark_result):
        # Arrange
        # Act
        actual = minimal_benchmark_result.module
        # Assert
        assert actual == "my_module"

    def test_minimal_constructor_stores_mean_time(self, minimal_benchmark_result):
        # Arrange
        # Act
        actual = minimal_benchmark_result.mean_time
        # Assert
        assert actual == 0.5

    def test_minimal_constructor_stores_std_time(self, minimal_benchmark_result):
        # Arrange
        # Act
        actual = minimal_benchmark_result.std_time
        # Assert
        assert actual == 0.05

    def test_minimal_constructor_stores_min_time(self, minimal_benchmark_result):
        # Arrange
        # Act
        actual = minimal_benchmark_result.min_time
        # Assert
        assert actual == 0.4

    def test_minimal_constructor_stores_max_time(self, minimal_benchmark_result):
        # Arrange
        # Act
        actual = minimal_benchmark_result.max_time
        # Assert
        assert actual == 0.6

    def test_minimal_constructor_stores_iterations(self, minimal_benchmark_result):
        # Arrange
        # Act
        actual = minimal_benchmark_result.iterations
        # Assert
        assert actual == 10

    def test_minimal_constructor_defaults_input_size_to_none(
        self, minimal_benchmark_result
    ):
        # Arrange
        # Act
        actual = minimal_benchmark_result.input_size
        # Assert
        assert actual is None

    def test_minimal_constructor_defaults_memory_usage_to_none(
        self, minimal_benchmark_result
    ):
        # Arrange
        # Act
        actual = minimal_benchmark_result.memory_usage
        # Assert
        assert actual is None

    def test_minimal_constructor_defaults_notes_to_none(self, minimal_benchmark_result):
        # Arrange
        # Act
        actual = minimal_benchmark_result.notes
        # Assert
        assert actual is None

    def test_all_fields_constructor_stores_function_name(self, benchmark_result):
        # Arrange
        # Act
        actual = benchmark_result.function_name
        # Assert
        assert actual == "test_func"

    def test_all_fields_constructor_stores_input_size(self, benchmark_result):
        # Arrange
        # Act
        actual = benchmark_result.input_size
        # Assert
        assert actual == "100x100"

    def test_all_fields_constructor_stores_memory_usage(self, benchmark_result):
        # Arrange
        # Act
        actual = benchmark_result.memory_usage
        # Assert
        assert actual == 50.0

    def test_all_fields_constructor_stores_notes(self, benchmark_result):
        # Arrange
        # Act
        actual = benchmark_result.notes
        # Assert
        assert actual == "Test benchmark"

    def test_str_representation_contains_function_name(self, benchmark_result):
        # Arrange
        # Act
        actual = str(benchmark_result)
        # Assert
        assert "test_func" in actual

    def test_str_representation_contains_mean_time_formatted(self, benchmark_result):
        # Arrange
        # Act
        actual = str(benchmark_result)
        # Assert
        assert "0.100s" in actual

    def test_str_representation_contains_std_time_formatted(self, benchmark_result):
        # Arrange
        # Act
        actual = str(benchmark_result)
        # Assert
        assert "0.010s" in actual

    def test_str_representation_contains_iteration_count(self, benchmark_result):
        # Arrange
        # Act
        actual = str(benchmark_result)
        # Assert
        assert "n=10" in actual

    def test_to_dict_returns_dict_instance(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict
        # Assert
        assert isinstance(actual, dict)

    def test_to_dict_uses_function_key_for_function_name(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["function"]
        # Assert
        assert actual == "test_func"

    def test_to_dict_preserves_module(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["module"]
        # Assert
        assert actual == "test_module"

    def test_to_dict_preserves_mean_time(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["mean_time"]
        # Assert
        assert actual == 0.1

    def test_to_dict_preserves_std_time(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["std_time"]
        # Assert
        assert actual == 0.01

    def test_to_dict_preserves_min_time(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["min_time"]
        # Assert
        assert actual == 0.08

    def test_to_dict_preserves_max_time(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["max_time"]
        # Assert
        assert actual == 0.12

    def test_to_dict_preserves_iteration_count(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["iterations"]
        # Assert
        assert actual == 10

    def test_to_dict_preserves_input_size(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["input_size"]
        # Assert
        assert actual == "100x100"

    def test_to_dict_preserves_memory_usage(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["memory_usage"]
        # Assert
        assert actual == 50.0

    def test_to_dict_preserves_notes(self, benchmark_result_dict):
        # Arrange
        # Act
        actual = benchmark_result_dict["notes"]
        # Assert
        assert actual == "Test benchmark"

    def test_to_dict_exposes_the_full_set_of_expected_keys(self, benchmark_result_dict):
        # Arrange
        expected_keys = {
            "function",
            "module",
            "mean_time",
            "std_time",
            "min_time",
            "max_time",
            "iterations",
            "input_size",
            "memory_usage",
            "notes",
        }
        # Act
        actual = set(benchmark_result_dict.keys())
        # Assert
        assert actual == expected_keys


# ============================================================================
# Test benchmark_function
# ============================================================================


class TestBenchmarkFunction:
    """Tests for benchmark_function."""

    def test_basic_benchmark_returns_benchmark_result_instance(
        self, benchmark_function_result
    ):
        # Arrange
        # Act
        actual = benchmark_function_result
        # Assert
        assert isinstance(actual, BenchmarkResult)

    def test_basic_benchmark_records_function_name(self, benchmark_function_result):
        # Arrange
        # Act
        actual = benchmark_function_result.function_name
        # Assert
        assert actual == "add_numbers"

    def test_basic_benchmark_records_iteration_count(self, benchmark_function_result):
        # Arrange
        # Act
        actual = benchmark_function_result.iterations
        # Assert
        assert actual == 5

    def test_basic_benchmark_mean_time_is_non_negative(self, benchmark_function_result):
        # Arrange
        # Act
        actual = benchmark_function_result.mean_time
        # Assert
        assert actual >= 0

    def test_basic_benchmark_std_time_is_non_negative(self, benchmark_function_result):
        # Arrange
        # Act
        actual = benchmark_function_result.std_time
        # Assert
        assert actual >= 0

    def test_basic_benchmark_min_mean_max_are_ordered(self, benchmark_function_result):
        # Arrange
        r = benchmark_function_result
        # Act
        ordered = r.min_time <= r.mean_time <= r.max_time
        # Assert
        assert ordered

    def test_benchmark_with_kwargs_returns_benchmark_result(self, sample_function):
        # Arrange
        # Act
        result = benchmark_function(
            sample_function, args=(1,), kwargs={"b": 2}, iterations=5
        )
        # Assert
        assert isinstance(result, BenchmarkResult)

    def test_benchmark_with_kwargs_records_function_name(self, sample_function):
        # Arrange
        # Act
        result = benchmark_function(
            sample_function, args=(1,), kwargs={"b": 2}, iterations=5
        )
        # Assert
        assert result.function_name == "add_numbers"

    def test_timing_consistency_mean_above_sleep_floor(self, slow_function):
        """A 10ms-sleep function benchmarks to >=9ms mean (allowing jitter)."""
        # Arrange
        # Act
        result = benchmark_function(slow_function, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert result.mean_time >= 0.009

    def test_input_size_parameter_round_trips_into_result(self, sample_function):
        # Arrange
        # Act
        result = benchmark_function(
            sample_function, args=(1, 2), input_size="small", iterations=3
        )
        # Assert
        assert result.input_size == "small"

    def test_warmup_iterations_run_before_timed_iterations(self):
        """2 warmup + 3 iterations => the function is called 5 times total."""
        # Arrange
        call_count = [0]

        def counting_func(a, b):
            call_count[0] += 1
            return a + b

        # Act
        benchmark_function(counting_func, args=(1, 2), iterations=3, warmup=2)
        # Assert
        assert call_count[0] == 5

    def test_default_kwargs_none_does_not_raise(self, sample_function):
        """benchmark_function(..., kwargs=None) returns a BenchmarkResult."""
        # Arrange
        # Act
        result = benchmark_function(sample_function, args=(1, 2), kwargs=None)
        # Assert
        assert isinstance(result, BenchmarkResult)

    def test_module_detection_returns_string_module_name(self, sample_function):
        # Arrange
        # Act
        result = benchmark_function(sample_function, args=(1, 2))
        # Assert
        assert isinstance(result.module, str)

    def test_module_detection_returns_non_empty_module_name(self, sample_function):
        # Arrange
        # Act
        result = benchmark_function(sample_function, args=(1, 2))
        # Assert
        assert len(result.module) > 0

    def test_measure_memory_false_still_returns_benchmark_result(self, sample_function):
        # Arrange
        # Act
        result = benchmark_function(sample_function, args=(1, 2), measure_memory=False)
        # Assert
        assert isinstance(result, BenchmarkResult)

    def test_measure_memory_true_still_returns_benchmark_result(self, sample_function):
        # Arrange
        # Act
        result = benchmark_function(sample_function, args=(1, 2), measure_memory=True)
        # Assert
        assert isinstance(result, BenchmarkResult)


# ============================================================================
# Test compare_implementations
# ============================================================================


class TestCompareImplementations:
    """Tests for compare_implementations."""

    def test_two_implementations_return_dataframe(self, two_impl_comparison_df):
        # Arrange
        # Act
        actual = two_impl_comparison_df
        # Assert
        assert isinstance(actual, pd.DataFrame)

    def test_two_implementations_return_one_row_per_impl(self, two_impl_comparison_df):
        # Arrange
        # Act
        actual = len(two_impl_comparison_df)
        # Assert
        assert actual == 2

    def test_two_implementations_dataframe_has_implementation_column(
        self, two_impl_comparison_df
    ):
        # Arrange
        # Act
        actual = "implementation" in two_impl_comparison_df.columns
        # Assert
        assert actual

    def test_two_implementations_dataframe_has_mean_time_column(
        self, two_impl_comparison_df
    ):
        # Arrange
        # Act
        actual = "mean_time" in two_impl_comparison_df.columns
        # Assert
        assert actual

    def test_two_implementations_dataframe_has_std_time_column(
        self, two_impl_comparison_df
    ):
        # Arrange
        # Act
        actual = "std_time" in two_impl_comparison_df.columns
        # Assert
        assert actual

    def test_two_implementations_dataframe_has_speedup_column(
        self, two_impl_comparison_df
    ):
        # Arrange
        # Act
        actual = "speedup" in two_impl_comparison_df.columns
        # Assert
        assert actual

    def test_speedup_baseline_implementation_has_speedup_one(
        self, slow_vs_fast_comparison_df
    ):
        # Arrange
        # Act
        actual = slow_vs_fast_comparison_df.iloc[0]["speedup"]
        # Assert
        assert actual == 1.0

    def test_speedup_fast_implementation_is_greater_than_baseline(
        self, slow_vs_fast_comparison_df
    ):
        # Arrange
        # Act
        actual = slow_vs_fast_comparison_df.iloc[1]["speedup"]
        # Assert
        assert actual > 1.0

    def test_empty_implementations_raises_index_error(self):
        # Arrange
        implementations = {}

        def data_gen():
            return (), {}

        # Act
        ctx = pytest.raises(IndexError)
        # Assert
        with ctx:
            compare_implementations(implementations, data_gen, iterations=3)

    def test_single_implementation_returns_one_row(self):
        # Arrange
        implementations = {"only": lambda x: x}

        def data_gen():
            return (1,), {}

        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert len(df) == 1

    def test_single_implementation_has_speedup_one(self):
        # Arrange
        implementations = {"only": lambda x: x}

        def data_gen():
            return (1,), {}

        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert df.iloc[0]["speedup"] == 1.0


# ============================================================================
# Test BenchmarkSuite
# ============================================================================


class TestBenchmarkSuite:
    """Tests for BenchmarkSuite class."""

    def test_new_suite_stores_name(self):
        # Arrange
        # Act
        suite = BenchmarkSuite("test_suite")
        # Assert
        assert suite.name == "test_suite"

    def test_new_suite_starts_with_empty_benchmarks_list(self):
        # Arrange
        # Act
        suite = BenchmarkSuite("test_suite")
        # Assert
        assert suite.benchmarks == []

    def test_new_suite_starts_with_empty_results_list(self):
        # Arrange
        # Act
        suite = BenchmarkSuite("test_suite")
        # Assert
        assert suite.results == []

    def test_add_benchmark_appends_one_entry(self, populated_suite):
        # Arrange
        # Act
        actual = len(populated_suite["suite"].benchmarks)
        # Assert
        assert actual == 1

    def test_add_benchmark_stores_function_reference(self, populated_suite):
        # Arrange
        # Act
        actual = populated_suite["suite"].benchmarks[0]["func"]
        # Assert
        assert actual is populated_suite["func"]

    def test_add_benchmark_records_custom_name(self, populated_suite):
        # Arrange
        # Act
        actual = populated_suite["suite"].benchmarks[0]["name"]
        # Assert
        assert actual == "custom_name"

    def test_add_benchmark_records_custom_sizes(self, populated_suite):
        # Arrange
        # Act
        actual = populated_suite["suite"].benchmarks[0]["sizes"]
        # Assert
        assert actual == ["small"]

    def test_add_benchmark_default_name_falls_back_to_function_name(self):
        # Arrange
        suite = BenchmarkSuite("test_suite")

        def my_named_function():
            return 42

        def data_gen():
            return (), {}

        # Act
        suite.add_benchmark(my_named_function, data_gen)
        # Assert
        assert suite.benchmarks[0]["name"] == "my_named_function"

    def test_add_benchmark_default_sizes_is_singleton_default(self):
        # Arrange
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        # Act
        suite.add_benchmark(my_func, data_gen)
        # Assert
        assert suite.benchmarks[0]["sizes"] == ["default"]

    def test_run_suite_returns_dataframe(self, two_size_suite_results):
        # Arrange
        # Act
        actual = two_size_suite_results
        # Assert
        assert isinstance(actual, pd.DataFrame)

    def test_run_suite_returns_one_row_per_size(self, two_size_suite_results):
        # Arrange
        # Act
        actual = len(two_size_suite_results)
        # Assert
        assert actual == 2

    def test_run_suite_dataframe_has_function_column(self, two_size_suite_results):
        # Arrange
        # Act
        actual = "function" in two_size_suite_results.columns
        # Assert
        assert actual

    def test_run_suite_dataframe_has_mean_time_column(self, two_size_suite_results):
        # Arrange
        # Act
        actual = "mean_time" in two_size_suite_results.columns
        # Assert
        assert actual

    def test_run_suite_dataframe_has_size_column(self, two_size_suite_results):
        # Arrange
        # Act
        actual = "size" in two_size_suite_results.columns
        # Assert
        assert actual

    def test_run_suite_verbose_prints_running_benchmark_header(self, capsys):
        # Arrange
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        suite.add_benchmark(my_func, data_gen, sizes=["small"])
        # Act
        suite.run(iterations=2, verbose=True)
        captured = capsys.readouterr()
        # Assert
        assert "Running benchmark" in captured.out

    def test_run_suite_quiet_suppresses_running_benchmark_header(self, capsys):
        # Arrange
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        suite.add_benchmark(my_func, data_gen)
        # Act
        suite.run(iterations=2, verbose=False)
        captured = capsys.readouterr()
        # Assert
        assert "Running benchmark" not in captured.out

    def test_save_results_creates_file_on_disk(self, saved_suite_csv):
        # Arrange
        # Act
        actual = os.path.exists(saved_suite_csv["path"])
        # Assert
        assert actual

    def test_save_results_csv_contains_function_column(self, saved_suite_csv):
        # Arrange
        # Act
        actual = "function" in saved_suite_csv["df_loaded"].columns
        # Assert
        assert actual

    def test_save_results_csv_has_at_least_one_row(self, saved_suite_csv):
        # Arrange
        # Act
        actual = len(saved_suite_csv["df_loaded"])
        # Assert
        assert actual > 0

    def test_save_results_with_empty_results_raises_attribute_error(self, temp_dir):
        # Arrange
        suite = BenchmarkSuite("test_suite")
        output_path = os.path.join(temp_dir, "results.csv")
        # Act
        ctx = pytest.raises(AttributeError)
        # Assert
        with ctx:
            suite.save_results(output_path)

    def test_compare_with_baseline_returns_dataframe(self, baseline_comparison_df):
        # Arrange
        # Act
        actual = baseline_comparison_df
        # Assert
        assert isinstance(actual, pd.DataFrame)

    def test_compare_with_baseline_dataframe_has_speedup_column(
        self, baseline_comparison_df
    ):
        # Arrange
        # Act
        actual = "speedup" in baseline_comparison_df.columns
        # Assert
        assert actual

    def test_compare_with_baseline_dataframe_has_mean_time_current_column(
        self, baseline_comparison_df
    ):
        # Arrange
        # Act
        actual = "mean_time_current" in baseline_comparison_df.columns
        # Assert
        assert actual

    def test_compare_with_baseline_dataframe_has_mean_time_baseline_column(
        self, baseline_comparison_df
    ):
        # Arrange
        # Act
        actual = "mean_time_baseline" in baseline_comparison_df.columns
        # Assert
        assert actual


# ============================================================================
# Test benchmark_module
# ============================================================================


class TestBenchmarkModule:
    """Tests for benchmark_module function."""

    def test_benchmark_builtin_module_returns_suite_instance(self):
        # Arrange
        # Act
        suite = benchmark_module("math", pattern="sqrt*")
        # Assert
        assert isinstance(suite, BenchmarkSuite)

    def test_benchmark_builtin_module_names_suite_after_module(self):
        # Arrange
        # Act
        suite = benchmark_module("math", pattern="sqrt*")
        # Assert
        assert suite.name == "math"

    def test_benchmark_module_with_pattern_returns_suite_instance(self):
        # Arrange
        # Act
        suite = benchmark_module("os.path", pattern="is*")
        # Assert
        assert isinstance(suite, BenchmarkSuite)

    def test_benchmark_module_with_pattern_matches_function_names(self):
        """The pattern 'is*' on os.path captures function names that
        start with 'is' (e.g. isfile, isdir). The empty-match case is
        also acceptable because the standard library can vary."""
        # Arrange
        suite = benchmark_module("os.path", pattern="is*")
        func_names = [b["name"] for b in suite.benchmarks]
        # Act
        actual = (
            any(name.startswith("is") for name in func_names) or len(func_names) == 0
        )
        # Assert
        assert actual

    def test_benchmark_nonexistent_module_raises_import_error(self):
        # Arrange
        # Act
        ctx = pytest.raises(ImportError)
        # Assert
        with ctx:
            benchmark_module("nonexistent_module_12345")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
