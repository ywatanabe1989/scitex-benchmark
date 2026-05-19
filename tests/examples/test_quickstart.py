#!/usr/bin/env python3
"""Compile-only smoke test for examples/quickstart.py."""

import py_compile
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "quickstart.py"


def test_quickstart_example_file_exists_on_disk():
    # Arrange
    path = EXAMPLE
    # Act
    actual = path.is_file()
    # Assert
    assert actual, f"missing example: {path}"


def test_quickstart_example_compiles_without_syntax_error():
    # Arrange
    path = EXAMPLE
    # Act
    py_compile.compile(str(path), doraise=True)
    compiled = True
    # Assert
    assert compiled


# EOF
