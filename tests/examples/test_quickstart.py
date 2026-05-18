#!/usr/bin/env python3
"""Compile-only smoke test for examples/quickstart.py."""

import py_compile
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "quickstart.py"


def test_quickstart_example_file_exists_on_disk():
    # Arrange
    expected = EXAMPLE
    # Act
    is_file = expected.is_file()
    # Assert
    assert is_file, f"missing example: {expected}"


def test_quickstart_example_compiles_without_syntax_errors():
    # Arrange
    target = str(EXAMPLE)
    # Act
    py_compile.compile(target, doraise=True)
    # Assert
    assert EXAMPLE.is_file()


# EOF
