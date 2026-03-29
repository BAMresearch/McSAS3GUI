from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

REQUIRED_MCSAS3_MODULES = (
    "mcsas3.workflows",
    "mcsas3.data_adapters",
    "mcsas3.data_model",
)


def _has_canonical_mcsas3() -> bool:
    return all(importlib.util.find_spec(module_name) is not None for module_name in REQUIRED_MCSAS3_MODULES)


def _candidate_mcsas3_src_paths() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[2]
    return [
        repo_root.parent / "McSAS3" / "src",
    ]


def _clear_imported_mcsas3_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "mcsas3" or module_name.startswith("mcsas3."):
            sys.modules.pop(module_name, None)


def ensure_compatible_mcsas3() -> Path | None:
    """Ensure the canonical McSAS3 API is importable, preferring a sibling source checkout if needed."""

    if _has_canonical_mcsas3():
        return None

    for candidate in _candidate_mcsas3_src_paths():
        if not candidate.is_dir():
            continue
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)
        _clear_imported_mcsas3_modules()
        importlib.invalidate_caches()
        if _has_canonical_mcsas3():
            return candidate

    raise ImportError(
        "McSAS3GUI requires a McSAS3 installation with the canonical workflow API "
        "(mcsas3.workflows, mcsas3.data_adapters, mcsas3.data_model). "
        "Install the current McSAS3 package or place the McSAS3 source checkout next to McSAS3GUI."
    )
