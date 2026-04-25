from __future__ import annotations

import importlib.util
import json
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


def test_write_build_info_records_bundle_and_helper_paths(tmp_path):
    module = _load_build_standalone_module()
    bundle_root = tmp_path / "darwin-arm64"
    bundle_root.mkdir()
    gui_bundle = bundle_root / "McSAS3GUI.app"
    archive_path = tmp_path / "mcsas3gui-standalone-darwin-arm64.zip"

    (gui_bundle / "Contents" / "MacOS").mkdir(parents=True)
    (gui_bundle / "Contents" / "Resources" / "helpers" / module.HISTOGRAMMER_NAME).mkdir(parents=True)

    module._write_build_info(bundle_root, gui_bundle, archive_path)

    payload = json.loads((bundle_root / "build_info.json").read_text(encoding="utf-8"))
    assert payload["archive_name"] == archive_path.name
    assert payload["gui_bundle"] == "McSAS3GUI.app"
    assert payload["gui_executable"] == str(module._gui_executable_path(gui_bundle).relative_to(bundle_root))
    assert payload["bundled_histogrammer"] == str(
        module._bundled_histogrammer_path(gui_bundle).relative_to(bundle_root)
    )


def test_copy_helper_into_gui_bundle_preserves_symlinks(tmp_path, monkeypatch):
    module = _load_build_standalone_module()
    gui_bundle = tmp_path / "McSAS3GUI.app"
    helper_bundle = tmp_path / module.HISTOGRAMMER_NAME
    gui_bundle.mkdir(parents=True)
    helper_bundle.mkdir()
    calls: list[tuple[Path, Path, dict[str, object]]] = []

    def fake_copytree(src, dst, **kwargs):
        calls.append((Path(src), Path(dst), dict(kwargs)))
        return dst

    monkeypatch.setattr(module.shutil, "copytree", fake_copytree)

    module._copy_helper_into_gui_bundle(gui_bundle, helper_bundle)

    assert len(calls) == 1
    source, destination, kwargs = calls[0]
    assert source == helper_bundle
    assert destination == module._helper_destination(gui_bundle)
    assert kwargs["symlinks"] is True
    assert kwargs["dirs_exist_ok"] is True


def test_copy_gui_bundle_to_output_preserves_symlinks(tmp_path, monkeypatch):
    module = _load_build_standalone_module()
    gui_bundle = tmp_path / "gui" / "McSAS3GUI.app"
    bundle_root = tmp_path / "bundle-root"
    gui_bundle.mkdir(parents=True)
    bundle_root.mkdir()
    calls: list[tuple[Path, Path, dict[str, object]]] = []

    def fake_copytree(src, dst, **kwargs):
        calls.append((Path(src), Path(dst), dict(kwargs)))
        return dst

    monkeypatch.setattr(module.shutil, "copytree", fake_copytree)

    destination = module._copy_gui_bundle_to_output(gui_bundle, bundle_root)

    assert len(calls) == 1
    source, copied_destination, kwargs = calls[0]
    assert source == gui_bundle
    assert copied_destination == bundle_root / gui_bundle.name
    assert destination == copied_destination
    assert kwargs["symlinks"] is True
    assert kwargs["dirs_exist_ok"] is True
