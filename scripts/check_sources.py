"""Dependency-free syntax and JSON validation."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

MINIMUM_PYTHON_MINOR = 9


def main() -> int:
    root = Path(__file__).parents[1]
    source_roots = (root / "src", root / "tests", root / "scripts")

    python_files = sorted(
        path
        for source_root in source_roots
        for path in source_root.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    for path in python_files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(
            source,
            filename=str(path),
            mode="exec",
            feature_version=MINIMUM_PYTHON_MINOR,
        )
        compile(tree, str(path), "exec")

    json_files = sorted((root / "src" / "anki_lookup").glob("*.json"))
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8"))

    print(f"Validated {len(python_files)} Python files and {len(json_files)} JSON files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
