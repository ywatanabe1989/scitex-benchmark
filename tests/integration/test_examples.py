"""Smoke tests: every example script must run to completion."""

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = list(Path(__file__).parent.parent.joinpath("examples").glob("*.py"))


def test_examples_directory_contains_at_least_one_script():
    # Arrange
    discovered = EXAMPLES
    # Act
    count = len(discovered)
    # Assert
    assert count > 0, "no example scripts found"


@pytest.mark.parametrize(
    "example_script", EXAMPLES, ids=[e.name for e in EXAMPLES] or ["none"]
)
def test_example_script_exits_zero_when_executed(example_script, tmp_path):
    # Arrange
    cmd = [sys.executable, str(example_script)]
    # Act
    r = subprocess.run(
        cmd,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Assert
    assert r.returncode == 0, f"{example_script.name} failed: {r.stderr}"
