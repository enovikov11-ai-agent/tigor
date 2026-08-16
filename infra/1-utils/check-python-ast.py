#!/usr/bin/env python3
"""Python AST validation checker - ensures all .py files are valid Python code."""

import ast
import sys
from pathlib import Path


def find_python_files(root: Path) -> list[Path]:
    """Find all .py files in the repository."""
    # Exclude common non-code directories
    exclude_dirs = {
        ".git", "__pycache__", ".venv", "venv", "node_modules",
        ".pytest_cache", ".mypy_cache", "dist", "build", "*.egg-info"
    }

    python_files = []

    for py_file in root.rglob("*.py"):
        # Check if any parent directory is in exclude list
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue
        python_files.append(py_file)

    return sorted(python_files)


def validate_python_file(file_path: Path) -> tuple[bool, str]:
    """
    Validate a Python file by parsing it with ast.parse().

    Returns:
        (is_valid, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the file without executing it
        ast.parse(content, filename=str(file_path))
        return (True, "")

    except SyntaxError as e:
        return (False, f"SyntaxError at line {e.lineno}: {e.msg}")

    except UnicodeDecodeError as e:
        return (False, f"UnicodeDecodeError: {e}")

    except Exception as e:
        return (False, f"Unexpected error: {type(e).__name__}: {e}")


def main():
    """Run Python AST validation on all .py files in the repository."""
    repo_root = Path.cwd()

    print(f"Scanning for Python files in {repo_root}...")
    python_files = find_python_files(repo_root)

    if not python_files:
        print("No Python files found")
        return 0

    print(f"Found {len(python_files)} Python files")

    failed_files = []

    for py_file in python_files:
        is_valid, error_msg = validate_python_file(py_file)

        if not is_valid:
            rel_path = py_file.relative_to(repo_root)
            failed_files.append((rel_path, error_msg))

    if not failed_files:
        print(f"✓ All {len(python_files)} Python files are valid")
        return 0

    print(f"\n✗ {len(failed_files)} file(s) failed validation:\n")
    for file_path, error_msg in failed_files:
        print(f"  {file_path}")
        print(f"    {error_msg}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
