# scitex-benchmark

<!-- scitex-badges:start -->
[![PyPI](https://img.shields.io/pypi/v/scitex-benchmark.svg)](https://pypi.org/project/scitex-benchmark/)
[![Python](https://img.shields.io/pypi/pyversions/scitex-benchmark.svg)](https://pypi.org/project/scitex-benchmark/)
[![Tests](https://github.com/ywatanabe1989/scitex-benchmark/actions/workflows/test.yml/badge.svg)](https://github.com/ywatanabe1989/scitex-benchmark/actions/workflows/test.yml)
[![Install Test](https://github.com/ywatanabe1989/scitex-benchmark/actions/workflows/install-test.yml/badge.svg)](https://github.com/ywatanabe1989/scitex-benchmark/actions/workflows/install-test.yml)
[![Coverage](https://codecov.io/gh/ywatanabe1989/scitex-benchmark/graph/badge.svg)](https://codecov.io/gh/ywatanabe1989/scitex-benchmark)
[![Docs](https://readthedocs.org/projects/scitex-benchmark/badge/?version=latest)](https://scitex-benchmark.readthedocs.io/en/latest/)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
<!-- scitex-badges:end -->

<p align="center">
  <a href="https://scitex.ai">
    <img src="docs/scitex-logo-blue-cropped.png" alt="SciTeX" width="400">
  </a>
</p>

<p align="center"><b>Performance benchmarking, runtime monitoring, and profiling helpers.</b></p>

<p align="center">
  <a href="https://scitex-benchmark.readthedocs.io/">Full Documentation</a> · <code>pip install scitex-benchmark</code>
</p>

---

## Installation

```bash
pip install scitex-benchmark
```

## Quick Start

```python
import scitex_benchmark as bm

# Quick wall-clock + memory snapshot
with bm.Profiler() as p:
    work()
print(p.summary())
```

## 1 Interfaces

<details open>
<summary><strong>Python API</strong></summary>

<br>

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

</details>

## Status

Standalone fork of `scitex.benchmark`. Only dep is `psutil`. The umbrella
package's `scitex.benchmark` import path is preserved via a `sys.modules`-alias
bridge. Convenience builders inside `benchmark.py` import `scitex.io`/`scitex.stats`
*lazily* if you opt in — without those installed they simply error out at
the call site, but the core API works without them.

## Part of SciTeX

`scitex-benchmark` is part of [**SciTeX**](https://scitex.ai). Install via
the umbrella with `pip install scitex[benchmark]` to use as
`scitex.benchmark` (Python) or `scitex benchmark ...` (CLI).

>Four Freedoms for Research
>
>0. The freedom to **run** your research anywhere — your machine, your terms.
>1. The freedom to **study** how every step works — from raw data to final manuscript.
>2. The freedom to **redistribute** your workflows, not just your papers.
>3. The freedom to **modify** any module and share improvements with the community.
>
>AGPL-3.0 — because we believe research infrastructure deserves the same freedoms as the software it runs on.

## License

AGPL-3.0-only (see [LICENSE](./LICENSE)).

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
</p>
