---
description: |
  [TOPIC] Quick Start
  [DETAILS] Smallest useful example demonstrating the primary use case in
  under 30 seconds.
tags: [scitex-benchmark-quick-start]
---

# Quick Start

```python
import numpy as np
import scitex_benchmark as sb


def sum_sq_python(arr):
    """Sum of squares — pure Python."""
    return sum(float(x) * float(x) for x in arr)


def sum_sq_numpy(arr):
    """Sum of squares — NumPy vectorised."""
    return float((arr.astype(np.float64) ** 2).sum())


# Single-function benchmark
rng = np.random.default_rng(0)
arr = rng.normal(size=20_000).astype(np.float32)

result = sb.benchmark_function(
    sum_sq_numpy,
    args=(arr,),
    iterations=20,
    warmup=2,
)
print(
    f"sum_sq_numpy: mean={result.mean_time * 1e6:.1f}µs "
    f"std={result.std_time * 1e6:.1f}µs over {result.iterations} iters"
)

# Compare two implementations
df = sb.compare_implementations(
    implementations={"python": sum_sq_python, "numpy": sum_sq_numpy},
    test_data_generator=lambda: ((arr,), {}),
    iterations=10,
)
print("\nCompare implementations:")
print(df.to_string(index=False))
```
