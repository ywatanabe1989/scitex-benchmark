# scitex-benchmark

Performance benchmarking, runtime monitoring, and profiling helpers extracted from the [SciTeX](https://github.com/ywatanabe1989/scitex-python) ecosystem as a standalone package.

## Install

```bash
pip install scitex-benchmark
```

## API

```python
import scitex_benchmark as bm

# Benchmark suite — time/memory across input sizes
suite = bm.BenchmarkSuite("io")
suite.add_benchmark(my_func, gen_input, "name", sizes=["1MB", "10MB"])
results = suite.run()

# Runtime monitor — alerts when CPU/RAM/disk thresholds breached
monitor = bm.RuntimeMonitor(cpu_threshold=80, mem_threshold=90)
with monitor:
    long_running_job()

# Profiler — quick wall-clock + memory snapshot
with bm.Profiler() as p:
    work()
print(p.summary())
```

## Status

Standalone fork of `scitex.benchmark`. Only dep is `psutil`. The umbrella
package's `scitex.benchmark` import path is preserved via a `sys.modules`-alias
bridge. Convenience builders inside `benchmark.py` import `scitex.io`/`scitex.stats`
*lazily* if you opt in — without those installed they simply error out at
the call site, but the core API works without them.

## License

AGPL-3.0-only (see [LICENSE](./LICENSE)).
