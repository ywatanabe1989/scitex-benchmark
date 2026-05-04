---
name: scitex-benchmark
description: |
  [WHAT] Benchmarking utilities for SciTeX scripts and modules — wall/CPU timers, statistical comparison runners, and scriptable harnesses for repeatable performance measurement.
  [WHEN] Comparing implementations or guarding against perf regressions in research code.
  [HOW] `from scitex_benchmark import benchmark` or `scitex-benchmark --help`.
primary_interface: python
interfaces:
  python: 3
  cli: 1
  mcp: 0
  skills: 2
  hook: 0
  http: 0
canonical-location: scitex-benchmark/src/scitex_benchmark/_skills/scitex-benchmark/SKILL.md
tags: [scitex-benchmark]
---

> **Interfaces:** Python ⭐⭐⭐ · CLI ⭐ · MCP — · Skills ⭐⭐ · Hook — · HTTP —

# scitex-benchmark

Performance benchmarking + monitoring + profiling. Decorate hot functions with `@benchmark` to record execution time and memory; wrap a block with `Monitor` to track CPU/RAM/GPU over a long-running job; `profile_call(func, ...)` runs cProfile + line_profiler in one shot. Drop-in replacement for `time.perf_counter() + tracemalloc.get_traced_memory()` boilerplate at the top of analysis scripts.

See README.md and the package's public `__init__.py` for the full
function list. This skill leaf exists so agents discover the package
exists and roughly what shape it has — refer to the source for
signatures.

## Sub-skills

### Core (01–09)
- [01_installation.md](01_installation.md) — install + import sanity check
- [02_quick-start.md](02_quick-start.md) — 30-second tour
- [03_python-api.md](03_python-api.md) — Python API surface
