from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _insert_repo_src_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


REPO_ROOT = Path(__file__).resolve().parents[1]
_insert_repo_src_path(REPO_ROOT / "src")

importlib.import_module("mcsas3gui._bootstrap").ensure_compatible_mcsas3()
