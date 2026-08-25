from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from subprocess import CompletedProcess


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


def test_linux_dynamic_library_path_resolves_ldconfig_entry(tmp_path, monkeypatch):
    module = _load_build_standalone_module()
    library = tmp_path / "libxcb-cursor.so.0"
    library.write_text("", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        assert cmd == ["ldconfig", "-p"]
        assert kwargs == {"check": False, "capture_output": True, "text": True}
        return CompletedProcess(
            cmd,
            0,
            stdout=f"\tlibxcb-cursor.so.0 (libc6,x86-64) => {library}\n",
            stderr="",
        )

    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module, "find_library", lambda name: "libxcb-cursor.so.0")
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module._linux_dynamic_library_path("xcb-cursor") == library


def test_linux_qt_xcb_binary_args_adds_resolved_libraries(tmp_path, monkeypatch):
    module = _load_build_standalone_module()
    libraries = {
        library_name: tmp_path / f"lib{library_name}.so.0"
        for library_name, _package_name in module.LINUX_QT_XCB_RUNTIME_LIBRARIES
    }

    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module, "_linux_dynamic_library_path", lambda name: libraries[name])

    expected_args: list[str] = []
    for library_name, _package_name in module.LINUX_QT_XCB_RUNTIME_LIBRARIES:
        expected_args.extend(["--add-binary", f"{libraries[library_name]}:."])

    assert module._linux_qt_xcb_binary_args() == expected_args


def test_linux_qt_xcb_binary_args_fails_when_library_is_missing(monkeypatch):
    module = _load_build_standalone_module()

    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module, "_linux_dynamic_library_path", lambda name: None)

    try:
        module._linux_qt_xcb_binary_args()
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected _linux_qt_xcb_binary_args to fail")

    assert "libxcb-cursor0" in message
    assert "libxkbcommon-x11-0" in message


def test_linux_qt_xcb_binary_args_skips_non_linux(monkeypatch):
    module = _load_build_standalone_module()

    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")

    assert module._linux_qt_xcb_binary_args() == []


def test_preflight_linux_glibc_allows_matching_baseline(monkeypatch):
    module = _load_build_standalone_module()

    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.platform, "libc_ver", lambda: ("glibc", "2.34"))
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_MAX_GLIBC", "2.34")

    module._preflight_linux_glibc()


def test_preflight_linux_glibc_rejects_newer_baseline(monkeypatch):
    module = _load_build_standalone_module()

    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.platform, "libc_ver", lambda: ("glibc", "2.39"))
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_MAX_GLIBC", "2.34")

    try:
        module._preflight_linux_glibc()
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected _preflight_linux_glibc to fail")

    assert "Detected glibc: 2.39" in message
    assert "Maximum allowed glibc: 2.34" in message


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


def test_maybe_sign_macos_bundle_skips_without_identity(tmp_path, monkeypatch):
    module = _load_build_standalone_module()
    calls: list[list[str]] = []

    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.delenv("MCSAS3GUI_STANDALONE_CODESIGN_IDENTITY", raising=False)
    monkeypatch.delenv("MACOS_CODESIGN_IDENTITY", raising=False)
    monkeypatch.setattr(module.subprocess, "run", lambda cmd, **kwargs: calls.append(cmd))

    module._maybe_sign_macos_bundle(tmp_path)

    assert calls == []


def test_maybe_sign_macos_bundle_uses_identity_and_keychain(tmp_path, monkeypatch):
    module = _load_build_standalone_module()
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))

    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_CODESIGN_IDENTITY", "Developer ID Application: Example")
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_CODESIGN_KEYCHAIN", "/tmp/example.keychain-db")
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    module._maybe_sign_macos_bundle(tmp_path)

    assert len(calls) == 1
    cmd, kwargs = calls[0]
    assert cmd == [
        module.sys.executable,
        str(module.ROOT / "tools" / "sign_macos_bundle.py"),
        "--bundle-root",
        str(tmp_path),
        "--identity",
        "Developer ID Application: Example",
        "--timestamp",
        "none",
        "--keychain",
        "/tmp/example.keychain-db",
    ]
    assert kwargs == {"check": True}


def test_maybe_sign_macos_bundle_can_request_timestamping(tmp_path, monkeypatch):
    module = _load_build_standalone_module()
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))

    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_CODESIGN_IDENTITY", "Developer ID Application: Example")
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_CODESIGN_TIMESTAMP", "auto")
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    module._maybe_sign_macos_bundle(tmp_path)

    assert "--timestamp" in calls[0][0]
    assert calls[0][0][calls[0][0].index("--timestamp") + 1] == "auto"


def test_preflight_macos_codesigning_checks_configured_keychain(monkeypatch):
    module = _load_build_standalone_module()
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return CompletedProcess(cmd, 0, stdout='1) ABCD "Developer ID Application: Example"\n', stderr="")

    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_CODESIGN_IDENTITY", "Developer ID Application: Example")
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_CODESIGN_KEYCHAIN", "/tmp/example.keychain-db")
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    module._preflight_macos_codesigning()

    assert calls == [
        (
            ["security", "find-identity", "-v", "-p", "codesigning", "/tmp/example.keychain-db"],
            {"check": False, "capture_output": True, "text": True},
        )
    ]


def test_preflight_macos_codesigning_fails_when_identity_is_missing(monkeypatch):
    module = _load_build_standalone_module()

    def fake_run(cmd, **kwargs):
        return CompletedProcess(cmd, 0, stdout='1) ABCD "Developer ID Application: Other"\n', stderr="")

    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MCSAS3GUI_STANDALONE_CODESIGN_IDENTITY", "Developer ID Application: Example")
    monkeypatch.delenv("MCSAS3GUI_STANDALONE_CODESIGN_KEYCHAIN", raising=False)
    monkeypatch.delenv("MACOS_SIGNING_KEYCHAIN", raising=False)
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    try:
        module._preflight_macos_codesigning()
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected _preflight_macos_codesigning to fail")

    assert "identity is not visible to codesign" in message
    assert "MACOS_SIGNING_KEYCHAIN" in message
