"""Smoke tests: every example script must run to completion.

The list of example scripts is discovered at collection time. If no
scripts are found, parametrize emits zero rows and `test_example_script_runs_to_completion`
is auto-skipped by pytest's empty-parametrize behaviour. The
companion `test_examples_directory_contains_at_least_one_script` test
guards against the discovery accidentally returning empty.
"""

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parents[1].parent / "examples"
EXAMPLES = sorted(EXAMPLES_DIR.glob("*.py"))


def test_examples_directory_contains_at_least_one_script():
    # Arrange
    examples = EXAMPLES
    # Act
    actual = len(examples)
    # Assert
    assert actual > 0, f"no example scripts found in {EXAMPLES_DIR}"


@pytest.mark.parametrize("example_path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_example_script_runs_to_completion(example_path, tmp_path):
    # Arrange
    cmd = [sys.executable, str(example_path)]
    # Act
    r = subprocess.run(
        cmd,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Assert
    assert r.returncode == 0, f"{example_path.name} failed: {r.stderr}"
