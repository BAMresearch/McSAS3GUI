from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from pathlib import Path

REQUIRED_MCSAS3_MODULES = (
    "mcsas3.workflows",
    "mcsas3.data_adapters",
    "mcsas3.data_model",
    "mcsas3.mcsas3_cli_histogrammer",
)
REQUIRED_MCSAS3_ATTRIBUTES = (
    "background_intensity",
    "fit_parameter_names",
    "fitted_intensity",
    "normalize_flat_background_mode",
)


def _has_canonical_mcsas3() -> bool:
    if not all(importlib.util.find_spec(module_name) is not None for module_name in REQUIRED_MCSAS3_MODULES):
        return False
    try:
        mcsas3_module = importlib.import_module("mcsas3")
    except ImportError:
        return False
    return all(hasattr(mcsas3_module, attribute) for attribute in REQUIRED_MCSAS3_ATTRIBUTES)


def _candidate_mcsas3_src_paths() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[2]
    candidates: list[Path] = []

    configured = os.environ.get("MCSAS3GUI_MCSAS3_SRC")
    if configured:
        candidates.append(Path(configured).expanduser().resolve())

    # CI checkout layout: <workspace>/McSAS3GUI/McSAS3
    candidates.append((repo_root / "McSAS3" / "src").resolve())
    # Local dev layout: sibling repos in same parent directory.
    candidates.append((repo_root.parent / "McSAS3" / "src").resolve())

    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            deduped.append(candidate)
    return deduped


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
        "McSAS3GUI requires a McSAS3 installation with the canonical workflow and fitted-background APIs "
        "(mcsas3.workflows, mcsas3.data_adapters, mcsas3.data_model, mcsas3.mcsas3_cli_histogrammer, "
        "background_intensity, fit_parameter_names, fitted_intensity, normalize_flat_background_mode). "
        "Install the current McSAS3 package, set MCSAS3GUI_MCSAS3_SRC, or place the McSAS3 source "
        "checkout next to McSAS3GUI."
    )
