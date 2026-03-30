from __future__ import annotations

import importlib.util
from pathlib import Path


def test_generated_dependency_diagram_is_in_sync() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "tools" / "generate_dependency_diagram.py"
    output_path = repo_root / "docs" / "generated_module_dependencies.md"

    spec = importlib.util.spec_from_file_location("generate_dependency_diagram", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load dependency diagram generator from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    expected = module.generate_markdown()
    actual = output_path.read_text(encoding="utf-8")

    assert actual == expected
