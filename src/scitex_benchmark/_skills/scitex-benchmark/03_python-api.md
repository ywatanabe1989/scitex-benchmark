---
description: |
  [TOPIC] Python API
  [DETAILS] Public Python API of scitex-benchmark — exported functions, signatures,
  return types, and minimal usage examples per function.
tags: [scitex-benchmark-python-api]
---

# Python API

```python
from scitex_benchmark import (
    benchmark_function,         # Single-function benchmark
    compare_implementations,    # Compare multiple implementations
    BenchmarkResult,            # Dataclass holding per-run results
    BenchmarkSuite,             # Collection of benchmarks for a module
    run_all_benchmarks,         # Run all pre-defined benchmark suites
    profile_function,           # Decorator — profile a single function
    profile_module,             # Profile all matching functions in a module
    get_profile_report,         # Retrieve profiling report from global profiler
    PerformanceMonitor,         # Monitor CPU/RAM/error metrics over time
    track_performance,          # Decorator — track function performance
    get_performance_stats,      # Get aggregated performance statistics
)
```

## benchmark_function(func, args=(), kwargs=None, iterations=10, warmup=2, input_size=None, measure_memory=False) -> BenchmarkResult

Run repeated timed calls to `func(*args, **kwargs)`, optionally measuring memory via `psutil`.

```python
result = benchmark_function(sum, args=(range(10**6),), iterations=5)
print(result.mean_time)   # average wall-clock seconds
print(result.min_time)    # fastest single run
print(result.std_time)    # std deviation across runs
```

## compare_implementations(implementations, test_data_generator, iterations=10, sizes=None) -> pd.DataFrame

Compare N implementations on the same input. Returns a DataFrame with columns `implementation`, `mean_time`, `std_time`, `speedup`.

```python
df = compare_implementations(
    implementations={"loop": fn_loop, "numpy": fn_numpy},
    test_data_generator=lambda: ((arr,), {}),
    iterations=10,
)
```

## BenchmarkSuite(name)

Collection of benchmarks sharing a common name/theme.

| Method | Description |
|---|---|
| `add_benchmark(func, data_gen, name=None, sizes=None)` | Register a benchmark |
| `run(iterations=10, verbose=True)` | Execute all and return results as DataFrame |
| `save_results(path)` | Save to CSV |
| `compare_with_baseline(baseline_path)` | Compare against a previous run CSV |

## profile_function(func) -> Callable

Decorator that instruments every call to `func` with `cProfile`.

```python
@profile_function
def my_func(x):
    return x ** 2
```

## profile_block(name) -> contextmanager

Context manager that profiles a block of code.

```python
with profile_block("data_processing"):
    data = process_data()
```

## get_profile_report() -> dict

Return profiling summary for all functions tracked by the global profiler. Keys are function names; each value contains `call_count`, `total_time`, `avg_time`, and `profile` (the cProfile text dump).

## PerformanceMonitor(max_history=1000)

Long-running resource and performance monitor.

| Method | Description |
|---|---|
| `start()` / `stop()` | Begin / end monitoring session |
| `record_metric(metric)` | Record a `PerformanceMetric` |
| `get_stats(function=None)` | Get aggregated stats (optionally for one function) |
| `save_metrics(path)` | Serialise all metrics as JSON |
| `load_metrics(path)` | Restore metrics from JSON |
| `add_alert_callback(callback)` | Register a handler for threshold alerts |

## track_performance(func) -> Callable

Decorator that records wall-clock time, memory delta, argument/result sizes, and exceptions to the global `PerformanceMonitor`.

```python
@track_performance
def my_func(x):
    return x ** 2
```

## get_performance_stats(function=None) -> dict

Return aggregated statistics from the global `PerformanceMonitor`.

## profile_module(module_name, pattern="*") -> FunctionProfiler

Wrap every callable in `module_name` matching `pattern` with profiling. Returns a `FunctionProfiler` instance whose `get_report()` produces the summary.

```python
profiler = profile_module("math", pattern="sqrt")
# now call math.sqrt(...) normally
report = profiler.get_report()
```
