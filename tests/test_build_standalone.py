from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_build_standalone_module():
    pyinstaller = types.ModuleType("PyInstaller")
    pyinstaller_main = types.ModuleType("PyInstaller.__main__")
    pyinstaller.__main__ = pyinstaller_main
    sys.modules.setdefault("PyInstaller", pyinstaller)
    sys.modules.setdefault("PyInstaller.__main__", pyinstaller_main)

    script_path = Path(__file__).resolve().parents[1] / "tools" / "build_standalone.py"
    spec = importlib.util.spec_from_file_location("build_standalone", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_histogrammer_hidden_imports_include_pdf_backend():
    module = _load_build_standalone_module()

    args = module._histogrammer_hidden_import_args()

    assert "--hidden-import" in args
    assert "matplotlib.backends.backend_pdf" in args
