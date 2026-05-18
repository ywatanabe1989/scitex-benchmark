#!/usr/bin/env python3
# Time-stamp: "2025-01-05"
# File: test_benchmark.py

"""Tests for scitex_benchmark.benchmark module."""

import os
import tempfile

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
    import time

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
def benchmark_result_required_only():
    """Create a BenchmarkResult with required fields only."""
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
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# Test BenchmarkResult — creation with required fields only
# ============================================================================


class TestBenchmarkResultRequiredFields:
    """Tests for BenchmarkResult dataclass — required-only construction."""

    def test_creation_sets_function_name_field(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.function_name
        # Assert
        assert value == "my_func"

    def test_creation_sets_module_field(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.module
        # Assert
        assert value == "my_module"

    def test_creation_sets_mean_time_field(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.mean_time
        # Assert
        assert value == 0.5

    def test_creation_sets_std_time_field(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.std_time
        # Assert
        assert value == 0.05

    def test_creation_sets_min_time_field(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.min_time
        # Assert
        assert value == 0.4

    def test_creation_sets_max_time_field(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.max_time
        # Assert
        assert value == 0.6

    def test_creation_sets_iterations_field(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.iterations
        # Assert
        assert value == 10

    def test_creation_leaves_input_size_none(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.input_size
        # Assert
        assert value is None

    def test_creation_leaves_memory_usage_none(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.memory_usage
        # Assert
        assert value is None

    def test_creation_leaves_notes_none(self, benchmark_result_required_only):
        # Arrange
        result = benchmark_result_required_only
        # Act
        value = result.notes
        # Assert
        assert value is None


# ============================================================================
# Test BenchmarkResult — creation with all fields
# ============================================================================


class TestBenchmarkResultAllFields:
    """Tests for BenchmarkResult dataclass — all-fields construction."""

    def test_creation_sets_function_name(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        value = result.function_name
        # Assert
        assert value == "test_func"

    def test_creation_sets_input_size(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        value = result.input_size
        # Assert
        assert value == "100x100"

    def test_creation_sets_memory_usage(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        value = result.memory_usage
        # Assert
        assert value == 50.0

    def test_creation_sets_notes(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        value = result.notes
        # Assert
        assert value == "Test benchmark"


# ============================================================================
# Test BenchmarkResult — __str__
# ============================================================================


class TestBenchmarkResultStr:
    """Tests for BenchmarkResult __str__ representation."""

    def test_str_includes_function_name(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        text = str(result)
        # Assert
        assert "test_func" in text

    def test_str_includes_mean_time(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        text = str(result)
        # Assert
        assert "0.100s" in text

    def test_str_includes_std_time(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        text = str(result)
        # Assert
        assert "0.010s" in text

    def test_str_includes_iteration_count(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        text = str(result)
        # Assert
        assert "n=10" in text


# ============================================================================
# Test BenchmarkResult — to_dict
# ============================================================================


class TestBenchmarkResultToDict:
    """Tests for BenchmarkResult to_dict serialization."""

    def test_to_dict_returns_dict_type(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert isinstance(d, dict)

    def test_to_dict_stores_function_under_function_key(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["function"] == "test_func"

    def test_to_dict_stores_module(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["module"] == "test_module"

    def test_to_dict_stores_mean_time(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["mean_time"] == 0.1

    def test_to_dict_stores_std_time(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["std_time"] == 0.01

    def test_to_dict_stores_min_time(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["min_time"] == 0.08

    def test_to_dict_stores_max_time(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["max_time"] == 0.12

    def test_to_dict_stores_iterations(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["iterations"] == 10

    def test_to_dict_stores_input_size(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["input_size"] == "100x100"

    def test_to_dict_stores_memory_usage(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["memory_usage"] == 50.0

    def test_to_dict_stores_notes(self, benchmark_result):
        # Arrange
        result = benchmark_result
        # Act
        d = result.to_dict()
        # Assert
        assert d["notes"] == "Test benchmark"

    def test_to_dict_has_all_expected_keys(self, benchmark_result):
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
        keys = set(benchmark_result.to_dict().keys())
        # Assert
        assert keys == expected_keys


# ============================================================================
# Test benchmark_function
# ============================================================================


class TestBenchmarkFunctionBasic:
    """Tests for benchmark_function basic call."""

    def test_basic_benchmark_returns_benchmark_result_instance(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert isinstance(result, BenchmarkResult)

    def test_basic_benchmark_returns_correct_function_name(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert result.function_name == "add_numbers"

    def test_basic_benchmark_returns_requested_iterations(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert result.iterations == 5

    def test_basic_benchmark_mean_time_is_nonnegative(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert result.mean_time >= 0

    def test_basic_benchmark_std_time_is_nonnegative(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert result.std_time >= 0

    def test_basic_benchmark_min_le_mean_le_max(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert result.min_time <= result.mean_time <= result.max_time


class TestBenchmarkFunctionKwargs:
    """Tests for benchmark_function with kwargs."""

    def test_with_kwargs_returns_benchmark_result(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1,), kwargs={"b": 2}, iterations=5)
        # Assert
        assert isinstance(result, BenchmarkResult)

    def test_with_kwargs_returns_correct_function_name(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1,), kwargs={"b": 2}, iterations=5)
        # Assert
        assert result.function_name == "add_numbers"


class TestBenchmarkFunctionTiming:
    """Tests for benchmark_function timing behaviour."""

    def test_slow_function_mean_time_at_least_nine_milliseconds(self, slow_function):
        # Arrange
        func = slow_function
        # Act
        result = benchmark_function(func, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert result.mean_time >= 0.009

    def test_slow_function_mean_time_under_a_tenth_of_a_second(self, slow_function):
        # Arrange
        func = slow_function
        # Act
        result = benchmark_function(func, args=(1, 2), iterations=5, warmup=1)
        # Assert
        assert result.mean_time < 0.1


class TestBenchmarkFunctionInputSize:
    """Tests for benchmark_function input_size parameter."""

    def test_input_size_parameter_is_recorded_on_result(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), input_size="small", iterations=3)
        # Assert
        assert result.input_size == "small"


class TestBenchmarkFunctionWarmup:
    """Tests for benchmark_function warmup."""

    def test_warmup_runs_before_benchmark_iterations(self, sample_function):
        # Arrange
        call_count = [0]

        def counting_func(a, b):
            call_count[0] += 1
            return a + b

        # Act
        benchmark_function(counting_func, args=(1, 2), iterations=3, warmup=2)
        # Assert
        assert call_count[0] == 5  # 2 warmup + 3 benchmark


class TestBenchmarkFunctionDefaultKwargs:
    """Tests for benchmark_function default kwargs."""

    def test_kwargs_none_does_not_raise(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), kwargs=None)
        # Assert
        assert isinstance(result, BenchmarkResult)


class TestBenchmarkFunctionModuleDetection:
    """Tests for benchmark_function module detection."""

    def test_module_detected_as_string(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2))
        # Assert
        assert isinstance(result.module, str)

    def test_module_detection_returns_nonempty_string(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2))
        # Assert
        assert len(result.module) > 0


class TestBenchmarkFunctionMeasureMemory:
    """Tests for benchmark_function memory measurement flag."""

    def test_measure_memory_false_returns_benchmark_result(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), measure_memory=False)
        # Assert
        assert isinstance(result, BenchmarkResult)

    def test_measure_memory_true_returns_benchmark_result(self, sample_function):
        # Arrange
        func = sample_function
        # Act
        result = benchmark_function(func, args=(1, 2), measure_memory=True)
        # Assert
        assert isinstance(result, BenchmarkResult)


# ============================================================================
# Test compare_implementations
# ============================================================================


def _two_impl_setup():
    def impl1(x):
        return sum(range(x))

    def impl2(x):
        return x * (x - 1) // 2

    implementations = {"loop": impl1, "formula": impl2}

    def data_gen():
        return (1000,), {}

    return implementations, data_gen


class TestCompareImplementationsTwo:
    """Tests for compare_implementations with two implementations."""

    def test_returns_dataframe_instance(self):
        # Arrange
        implementations, data_gen = _two_impl_setup()
        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert isinstance(df, pd.DataFrame)

    def test_returns_two_rows_for_two_implementations(self):
        # Arrange
        implementations, data_gen = _two_impl_setup()
        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert len(df) == 2

    def test_returns_implementation_column(self):
        # Arrange
        implementations, data_gen = _two_impl_setup()
        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert "implementation" in df.columns

    def test_returns_mean_time_column(self):
        # Arrange
        implementations, data_gen = _two_impl_setup()
        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert "mean_time" in df.columns

    def test_returns_std_time_column(self):
        # Arrange
        implementations, data_gen = _two_impl_setup()
        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert "std_time" in df.columns

    def test_returns_speedup_column(self):
        # Arrange
        implementations, data_gen = _two_impl_setup()
        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert "speedup" in df.columns


class TestCompareImplementationsSpeedup:
    """Tests for compare_implementations speedup calculation."""

    @pytest.fixture
    def speedup_df(self):
        import time

        def slow_impl(x):
            time.sleep(0.01)
            return x

        def fast_impl(x):
            return x

        implementations = {"slow": slow_impl, "fast": fast_impl}

        def data_gen():
            return (10,), {}

        return compare_implementations(implementations, data_gen, iterations=3)

    def test_baseline_implementation_has_speedup_of_one(self, speedup_df):
        # Arrange
        df = speedup_df
        # Act
        baseline_speedup = df.iloc[0]["speedup"]
        # Assert
        assert baseline_speedup == 1.0

    def test_faster_implementation_has_speedup_greater_than_one(self, speedup_df):
        # Arrange
        df = speedup_df
        # Act
        faster_speedup = df.iloc[1]["speedup"]
        # Assert
        assert faster_speedup > 1.0


class TestCompareImplementationsEdgeCases:
    """Tests for compare_implementations edge cases."""

    def test_empty_implementations_raises_index_error_on_baseline_access(self):
        # Arrange
        implementations = {}

        def data_gen():
            return (), {}

        call = lambda: compare_implementations(implementations, data_gen, iterations=3)
        # Act
        raised_ctx = pytest.raises(IndexError)
        # Assert
        with raised_ctx:
            call()

    def test_single_implementation_returns_single_row(self):
        # Arrange
        implementations = {"only": lambda x: x}

        def data_gen():
            return (1,), {}

        # Act
        df = compare_implementations(implementations, data_gen, iterations=3)
        # Assert
        assert len(df) == 1

    def test_single_implementation_has_speedup_of_one(self):
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


class TestBenchmarkSuiteCreation:
    """Tests for BenchmarkSuite creation."""

    def test_suite_creation_sets_name(self):
        # Arrange
        # (no setup)
        # Act
        suite = BenchmarkSuite("test_suite")
        # Assert
        assert suite.name == "test_suite"

    def test_suite_creation_starts_with_empty_benchmark_list(self):
        # Arrange
        # (no setup)
        # Act
        suite = BenchmarkSuite("test_suite")
        # Assert
        assert suite.benchmarks == []

    def test_suite_creation_starts_with_empty_results_list(self):
        # Arrange
        # (no setup)
        # Act
        suite = BenchmarkSuite("test_suite")
        # Assert
        assert suite.results == []


class TestBenchmarkSuiteAddBenchmark:
    """Tests for BenchmarkSuite.add_benchmark."""

    def test_add_benchmark_appends_to_benchmarks_list(self):
        # Arrange
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        # Act
        suite.add_benchmark(my_func, data_gen, name="custom_name", sizes=["small"])
        # Assert
        assert len(suite.benchmarks) == 1

    def test_add_benchmark_stores_func_reference(self):
        # Arrange
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        # Act
        suite.add_benchmark(my_func, data_gen, name="custom_name", sizes=["small"])
        # Assert
        assert suite.benchmarks[0]["func"] is my_func

    def test_add_benchmark_stores_custom_name(self):
        # Arrange
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        # Act
        suite.add_benchmark(my_func, data_gen, name="custom_name", sizes=["small"])
        # Assert
        assert suite.benchmarks[0]["name"] == "custom_name"

    def test_add_benchmark_stores_explicit_sizes(self):
        # Arrange
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        # Act
        suite.add_benchmark(my_func, data_gen, name="custom_name", sizes=["small"])
        # Assert
        assert suite.benchmarks[0]["sizes"] == ["small"]

    def test_add_benchmark_without_name_uses_function_name(self):
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

    def test_add_benchmark_without_sizes_uses_default_size(self):
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


class TestBenchmarkSuiteRun:
    """Tests for BenchmarkSuite.run."""

    @pytest.fixture
    def populated_suite_results(self, capsys):
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        suite.add_benchmark(my_func, data_gen, sizes=["small", "large"])
        results = suite.run(iterations=3, verbose=True)
        captured = capsys.readouterr()
        return results, captured

    def test_run_returns_dataframe(self, populated_suite_results):
        # Arrange
        results, _ = populated_suite_results
        # Act
        kind = type(results)
        # Assert
        assert issubclass(kind, pd.DataFrame)

    def test_run_returns_one_row_per_size(self, populated_suite_results):
        # Arrange
        results, _ = populated_suite_results
        # Act
        count = len(results)
        # Assert
        assert count == 2

    def test_run_dataframe_has_function_column(self, populated_suite_results):
        # Arrange
        results, _ = populated_suite_results
        # Act
        cols = results.columns
        # Assert
        assert "function" in cols

    def test_run_dataframe_has_mean_time_column(self, populated_suite_results):
        # Arrange
        results, _ = populated_suite_results
        # Act
        cols = results.columns
        # Assert
        assert "mean_time" in cols

    def test_run_dataframe_has_size_column(self, populated_suite_results):
        # Arrange
        results, _ = populated_suite_results
        # Act
        cols = results.columns
        # Assert
        assert "size" in cols

    def test_run_verbose_true_emits_running_benchmark_log(
        self, populated_suite_results
    ):
        # Arrange
        _, captured = populated_suite_results
        # Act
        out = captured.out
        # Assert
        assert "Running benchmark" in out

    def test_run_verbose_false_suppresses_running_benchmark_log(self, capsys):
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


class TestBenchmarkSuiteSaveResults:
    """Tests for BenchmarkSuite.save_results."""

    @pytest.fixture
    def saved_csv_path(self, temp_dir):
        suite = BenchmarkSuite("test_suite")

        def my_func():
            return 42

        def data_gen():
            return (), {}

        suite.add_benchmark(my_func, data_gen)
        suite.run(iterations=2, verbose=False)
        output_path = os.path.join(temp_dir, "results.csv")
        suite.save_results(output_path)
        return output_path

    def test_save_results_creates_csv_file(self, saved_csv_path):
        # Arrange
        path = saved_csv_path
        # Act
        exists = os.path.exists(path)
        # Assert
        assert exists

    def test_save_results_csv_has_function_column(self, saved_csv_path):
        # Arrange
        loaded_df = pd.read_csv(saved_csv_path)
        # Act
        cols = loaded_df.columns
        # Assert
        assert "function" in cols

    def test_save_results_csv_has_at_least_one_row(self, saved_csv_path):
        # Arrange
        loaded_df = pd.read_csv(saved_csv_path)
        # Act
        n = len(loaded_df)
        # Assert
        assert n > 0

    def test_save_results_without_run_raises_attribute_error(self, temp_dir):
        # Arrange
        suite = BenchmarkSuite("test_suite")
        output_path = os.path.join(temp_dir, "results.csv")
        # Act
        raised_ctx = pytest.raises(AttributeError)
        # Assert
        with raised_ctx:
            suite.save_results(output_path)


class TestBenchmarkSuiteCompareWithBaseline:
    """Tests for BenchmarkSuite.compare_with_baseline."""

    @pytest.fixture
    def comparison_df(self, temp_dir):
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

    def test_compare_returns_dataframe(self, comparison_df):
        # Arrange
        result = comparison_df
        # Act
        kind = type(result)
        # Assert
        assert issubclass(kind, pd.DataFrame)

    def test_compare_dataframe_has_speedup_column(self, comparison_df):
        # Arrange
        result = comparison_df
        # Act
        cols = result.columns
        # Assert
        assert "speedup" in cols

    def test_compare_dataframe_has_mean_time_current_column(self, comparison_df):
        # Arrange
        result = comparison_df
        # Act
        cols = result.columns
        # Assert
        assert "mean_time_current" in cols

    def test_compare_dataframe_has_mean_time_baseline_column(self, comparison_df):
        # Arrange
        result = comparison_df
        # Act
        cols = result.columns
        # Assert
        assert "mean_time_baseline" in cols


# ============================================================================
# Test benchmark_module
# ============================================================================


class TestBenchmarkModule:
    """Tests for benchmark_module function."""

    def test_benchmarking_math_returns_benchmark_suite(self):
        # Arrange
        module_name = "math"
        # Act
        suite = benchmark_module(module_name, pattern="sqrt*")
        # Assert
        assert isinstance(suite, BenchmarkSuite)

    def test_benchmarking_math_uses_module_name_as_suite_name(self):
        # Arrange
        module_name = "math"
        # Act
        suite = benchmark_module(module_name, pattern="sqrt*")
        # Assert
        assert suite.name == "math"

    def test_benchmarking_math_initialises_benchmarks_list(self):
        # Arrange
        module_name = "math"
        # Act
        suite = benchmark_module(module_name, pattern="sqrt*")
        # Assert
        assert isinstance(suite.benchmarks, list)

    def test_pattern_matching_returns_benchmark_suite(self):
        # Arrange
        module_name = "os.path"
        # Act
        suite = benchmark_module(module_name, pattern="is*")
        # Assert
        assert isinstance(suite, BenchmarkSuite)

    def test_nonexistent_module_raises_import_error(self):
        # Arrange
        module_name = "nonexistent_module_12345"
        # Act
        raised_ctx = pytest.raises(ImportError)
        # Assert
        with raised_ctx:
            benchmark_module(module_name)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# EOF
