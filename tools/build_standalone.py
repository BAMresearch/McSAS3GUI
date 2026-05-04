#!/usr/bin/env python3
"""Build standalone GUI bundles for McSAS3GUI."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import textwrap
from ctypes.util import find_library
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
BUILD_ROOT = ROOT / "build" / "standalone"
DIST_ROOT = ROOT / "dist" / "standalone"
GUI_APP_NAME = "McSAS3GUI"
HISTOGRAMMER_NAME = "mcsas3-histogrammer"

os.environ.setdefault("PYINSTALLER_CONFIG_DIR", str(BUILD_ROOT / "pyinstaller-cache"))
os.environ.setdefault("MPLCONFIGDIR", str(BUILD_ROOT / "matplotlib-cache"))


def _platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower().replace("x86_64", "amd64")
    return f"{system}-{machine}"


def _add_data_arg(source: Path, destination: str) -> str:
    return f"{source}{':' if platform.system() != 'Windows' else ';'}{destination}"


def _bundle_root() -> Path:
    return DIST_ROOT / _platform_tag()


def _mcsas3_src_dir() -> Path:
    configured = os.environ.get("MCSAS3GUI_MCSAS3_SRC")
    if configured:
        return Path(configured).expanduser().resolve()
    return ROOT.parent / "McSAS3" / "src"


def _mcsas3_root() -> Path:
    return _mcsas3_src_dir().parent


def _require_dir(path: Path, description: str) -> Path:
    if not path.is_dir():
        raise RuntimeError(f"Standalone GUI builds require {description} at '{path}'.")
    return path


def _require_mcsas3_src() -> Path:
    return _require_dir(
        _mcsas3_src_dir(),
        "the McSAS3 source tree (set MCSAS3GUI_MCSAS3_SRC to override)",
    )


def _require_mcsas3_root() -> Path:
    root = _mcsas3_root()
    return _require_dir(root, "the McSAS3 repository root")


def _core_hooks_dir() -> Path:
    hooks_dir = _require_mcsas3_root() / "tools" / "pyinstaller_hooks"
    return _require_dir(hooks_dir, "the McSAS3 PyInstaller hooks directory")


def _hidden_import_args() -> list[str]:
    hidden_imports = [
        "mcsas3.workflows",
        "mcsas3.data_adapters",
        "mcsas3.data_model",
        "mcsas3.cli_histogram",
        "modacor",
        "modacor.units",
        "modacor.dataclasses.basedata",
        "modacor.dataclasses.databundle",
        "modacor.dataclasses.processing_data",
        "mcsas3gui.gui.main_window",
        "mcsas3gui.utils.logging_config",
    ]
    args: list[str] = []
    for module_name in hidden_imports:
        args.extend(["--hidden-import", module_name])
    return args


def _histogrammer_hidden_import_args() -> list[str]:
    hidden_imports = [
        "modacor",
        "modacor.units",
        "modacor.dataclasses.basedata",
        "modacor.dataclasses.databundle",
        "modacor.dataclasses.processing_data",
        # Result-card export writes PDF output, which lazily imports this backend.
        "matplotlib.backends.backend_pdf",
    ]
    args: list[str] = []
    for module_name in hidden_imports:
        args.extend(["--hidden-import", module_name])
    return args


def _runtime_hooks_dir() -> Path:
    hooks_dir = ROOT / "tools" / "pyinstaller_hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir


def _macos_qt_runtime_hook() -> Path:
    hook_path = _runtime_hooks_dir() / "rthook_qt_macos_paths.py"
    if not hook_path.is_file():
        raise RuntimeError(f"Missing required runtime hook at {hook_path}.")
    return hook_path


def _macos_qt_conf() -> Path:
    config_dir = BUILD_ROOT / "qt-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    qt_conf = config_dir / "qt.conf"
    qt_conf.write_text(
        textwrap.dedent(
            """\
            [Paths]
            Prefix = .
            Plugins = PyQt6/Qt6/plugins
            Qml2Imports = PyQt6/Qt6/qml
            """
        ),
        encoding="utf-8",
    )
    return qt_conf


def _linux_dynamic_library_path(library_name: str) -> Path | None:
    """Resolve a Linux shared library name to an absolute filesystem path."""
    if platform.system() != "Linux":
        return None

    library = find_library(library_name)
    names = {f"lib{library_name}.so", f"lib{library_name}.so.0"}
    if library:
        library_path = Path(library)
        if library_path.is_absolute() and library_path.is_file():
            return library_path
        names.add(library)

    result = subprocess.run(["ldconfig", "-p"], check=False, capture_output=True, text=True)
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if "=>" not in line:
                continue
            name, path = line.strip().split("=>", maxsplit=1)
            if name.split(maxsplit=1)[0] in names:
                resolved = Path(path.strip())
                if resolved.is_file():
                    return resolved

    for directory in (Path("/lib"), Path("/usr/lib"), Path("/usr/local/lib")):
        for name in names:
            candidate = directory / name
            if candidate.is_file():
                return candidate

    return None


def _linux_xcb_cursor_binary_args() -> list[str]:
    if platform.system() != "Linux":
        return []

    library_path = _linux_dynamic_library_path("xcb-cursor")
    if library_path is None:
        raise RuntimeError(
            "Linux standalone builds require libxcb-cursor.so.0 so Qt can load the xcb "
            "platform plugin. Install libxcb-cursor0 before running tox -e standalone."
        )

    return ["--add-binary", _add_data_arg(library_path, ".")]


def _gui_pyinstaller_args(gui_dist: Path) -> list[str]:
    gui_script = ROOT / "src" / "mcsas3gui" / "__main__.py"
    args = [
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name",
        GUI_APP_NAME,
        "--paths",
        str(SRC_DIR),
        "--paths",
        str(_require_mcsas3_src()),
        "--additional-hooks-dir",
        str(_core_hooks_dir()),
        "--distpath",
        str(gui_dist),
        "--workpath",
        str(BUILD_ROOT / "work-gui"),
        "--specpath",
        str(BUILD_ROOT / "spec-gui"),
        "--add-data",
        _add_data_arg(ROOT / "src" / "mcsas3gui" / "configurations", "mcsas3gui/configurations"),
        "--add-data",
        _add_data_arg(ROOT / "src" / "mcsas3gui" / "resources", "mcsas3gui/resources"),
        "--add-data",
        _add_data_arg(ROOT / "src" / "mcsas3gui" / "testdata", "mcsas3gui/testdata"),
        str(gui_script),
    ]
    if platform.system() == "Darwin":
        args.extend(
            [
                "--runtime-hook",
                str(_macos_qt_runtime_hook()),
                "--add-data",
                _add_data_arg(_macos_qt_conf(), "."),
            ]
        )
    args.extend(_linux_xcb_cursor_binary_args())
    args.extend(_hidden_import_args())
    return args


def _histogrammer_pyinstaller_args(helper_dist: Path) -> list[str]:
    core_root = _require_mcsas3_root()
    helper_script = core_root / "src" / "mcsas3" / "mcsas3_cli_histogrammer.py"
    args = [
        "--noconfirm",
        "--clean",
        "--onedir",
        "--console",
        "--name",
        HISTOGRAMMER_NAME,
        "--paths",
        str(_require_mcsas3_src()),
        "--additional-hooks-dir",
        str(_core_hooks_dir()),
        "--distpath",
        str(helper_dist),
        "--workpath",
        str(BUILD_ROOT / "work-hist"),
        "--specpath",
        str(BUILD_ROOT / "spec-hist"),
        "--add-data",
        _add_data_arg(core_root / "example_configurations", "example_configurations"),
        "--add-data",
        _add_data_arg(core_root / "testdata" / "quickstartdemo1.csv", "testdata"),
        str(helper_script),
    ]
    args.extend(_histogrammer_hidden_import_args())
    return args


def _gui_bundle_path(gui_dist: Path) -> Path:
    if platform.system() == "Darwin":
        return gui_dist / f"{GUI_APP_NAME}.app"
    return gui_dist / GUI_APP_NAME


def _helper_bundle_path(helper_dist: Path) -> Path:
    return helper_dist / HISTOGRAMMER_NAME


def _helper_destination(gui_bundle: Path) -> Path:
    if platform.system() == "Darwin":
        return gui_bundle / "Contents" / "Resources" / "helpers" / HISTOGRAMMER_NAME
    return gui_bundle / "helpers" / HISTOGRAMMER_NAME


def _copy_helper_into_gui_bundle(gui_bundle: Path, helper_bundle: Path) -> None:
    destination = _helper_destination(gui_bundle)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(helper_bundle, destination, symlinks=True, dirs_exist_ok=True)


def _copy_gui_bundle_to_output(gui_bundle: Path, bundle_root: Path) -> Path:
    destination = bundle_root / gui_bundle.name
    shutil.copytree(gui_bundle, destination, symlinks=True, dirs_exist_ok=True)
    return destination


def _gui_executable_path(gui_bundle: Path) -> Path:
    suffix = ".exe" if platform.system() == "Windows" else ""
    if platform.system() == "Darwin":
        return gui_bundle / "Contents" / "MacOS" / GUI_APP_NAME
    return gui_bundle / f"{GUI_APP_NAME}{suffix}"


def _bundled_histogrammer_path(gui_bundle: Path) -> Path:
    suffix = ".exe" if platform.system() == "Windows" else ""
    return _helper_destination(gui_bundle) / f"{HISTOGRAMMER_NAME}{suffix}"


def _write_bundle_readme(bundle_root: Path) -> None:
    lines = [
        "McSAS3GUI standalone bundle",
        "",
        "Included artifacts:",
        f"- {GUI_APP_NAME}",
        f"- bundled helper executable at helpers/{HISTOGRAMMER_NAME}/",
        "",
        "Build prerequisites:",
        f"- sibling McSAS3 checkout at {_mcsas3_src_dir()}",
        "- or override it with MCSAS3GUI_MCSAS3_SRC",
        "",
        "Smoke-test entry points:",
        f"  {GUI_APP_NAME} --smoke-test",
        f"  {HISTOGRAMMER_NAME} --help",
        "",
        "Validation note:",
        "- the builder runs the frozen GUI smoke test in headless mode",
        "- the bundled histogram helper is validated with --help",
    ]
    (bundle_root / "README_STANDALONE.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_build_info(bundle_root: Path, gui_bundle: Path, archive_path: Path) -> None:
    payload = {
        "platform": _platform_tag(),
        "system": platform.system(),
        "machine": platform.machine(),
        "artifacts": [GUI_APP_NAME, HISTOGRAMMER_NAME],
        "archive_name": archive_path.name,
        "gui_bundle": str(gui_bundle.relative_to(bundle_root)),
        "gui_executable": str(_gui_executable_path(gui_bundle).relative_to(bundle_root)),
        "bundled_histogrammer": str(_bundled_histogrammer_path(gui_bundle).relative_to(bundle_root)),
    }
    (bundle_root / "build_info.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _archive_bundle(bundle_root: Path) -> Path:
    archive_base = DIST_ROOT / f"mcsas3gui-standalone-{bundle_root.name}"
    return Path(
        shutil.make_archive(
            str(archive_base),
            "zip",
            root_dir=bundle_root.parent,
            base_dir=bundle_root.name,
        )
    )


def _expected_archive_path(bundle_root: Path) -> Path:
    return DIST_ROOT / f"mcsas3gui-standalone-{bundle_root.name}.zip"


def _macos_codesign_identity() -> str | None:
    return os.environ.get("MCSAS3GUI_STANDALONE_CODESIGN_IDENTITY") or os.environ.get(
        "MACOS_CODESIGN_IDENTITY"
    )


def _macos_codesign_keychain() -> str | None:
    return os.environ.get("MCSAS3GUI_STANDALONE_CODESIGN_KEYCHAIN") or os.environ.get(
        "MACOS_SIGNING_KEYCHAIN"
    )


def _macos_codesign_timestamp() -> str:
    timestamp = os.environ.get("MCSAS3GUI_STANDALONE_CODESIGN_TIMESTAMP", "none")
    if timestamp not in {"auto", "none"}:
        raise RuntimeError(
            "MCSAS3GUI_STANDALONE_CODESIGN_TIMESTAMP must be either 'auto' or 'none'."
        )
    return timestamp


def _preflight_macos_codesigning() -> None:
    if platform.system() != "Darwin":
        return

    identity = _macos_codesign_identity()
    if not identity:
        return

    cmd = ["security", "find-identity", "-v", "-p", "codesigning"]
    keychain = _macos_codesign_keychain()
    if keychain:
        cmd.append(keychain)

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode == 0 and identity in result.stdout:
        return

    searched = f"keychain '{keychain}'" if keychain else "the default keychain search list"
    details = result.stdout or result.stderr or "No signing identities were reported."
    raise RuntimeError(
        "macOS code signing was requested, but the identity is not visible to codesign.\n"
        f"Requested identity: {identity}\n"
        f"Searched: {searched}\n"
        "Run tools/prepare_sign_macos_bundle.sh, then export both variables it prints:\n"
        "  MACOS_CODESIGN_IDENTITY\n"
        "  MACOS_SIGNING_KEYCHAIN\n"
        f"security find-identity output:\n{details}"
    )


def _maybe_sign_macos_bundle(bundle_root: Path) -> None:
    if platform.system() != "Darwin":
        return

    identity = _macos_codesign_identity()
    if not identity:
        print(
            "Skipping macOS code signing; set "
            "MCSAS3GUI_STANDALONE_CODESIGN_IDENTITY or MACOS_CODESIGN_IDENTITY to enable it."
        )
        return

    cmd = [
        sys.executable,
        str(ROOT / "tools" / "sign_macos_bundle.py"),
        "--bundle-root",
        str(bundle_root),
        "--identity",
        identity,
        "--timestamp",
        _macos_codesign_timestamp(),
    ]
    keychain = _macos_codesign_keychain()
    if keychain:
        cmd.extend(["--keychain", keychain])
    subprocess.run(cmd, check=True)


def _run_smoke_test(gui_bundle: Path) -> None:
    gui_executable = _gui_executable_path(gui_bundle)
    histogrammer_executable = _bundled_histogrammer_path(gui_bundle)

    if not gui_executable.is_file():
        raise RuntimeError(f"Standalone GUI executable was not created at {gui_executable}.")

    gui_env = os.environ.copy()
    gui_env.setdefault("QT_QPA_PLATFORM", "offscreen")
    gui_result = subprocess.run(
        [str(gui_executable), "--smoke-test"],
        check=False,
        capture_output=True,
        text=True,
        env=gui_env,
    )
    if gui_result.returncode != 0:
        raise RuntimeError(
            f"Standalone GUI smoke test failed: exit {gui_result.returncode}\n"
            f"stdout:\n{gui_result.stdout}\n"
            f"stderr:\n{gui_result.stderr}"
        )

    histogram_result = subprocess.run(
        [str(histogrammer_executable), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    if histogram_result.returncode != 0:
        raise RuntimeError(
            f"Bundled histogrammer smoke test failed: exit {histogram_result.returncode}\n"
            f"stdout:\n{histogram_result.stdout}\n"
            f"stderr:\n{histogram_result.stderr}"
        )


def main() -> None:
    """Build a standalone GUI bundle and matching archive for the current platform."""

    bundle_root = _bundle_root()
    gui_dist = BUILD_ROOT / "dist-gui"
    helper_dist = BUILD_ROOT / "dist-helper"

    _preflight_macos_codesigning()

    shutil.rmtree(BUILD_ROOT, ignore_errors=True)
    shutil.rmtree(bundle_root, ignore_errors=True)
    bundle_root.mkdir(parents=True, exist_ok=True)

    PyInstaller.__main__.run(_gui_pyinstaller_args(gui_dist))
    PyInstaller.__main__.run(_histogrammer_pyinstaller_args(helper_dist))

    gui_bundle = _gui_bundle_path(gui_dist)
    helper_bundle = _helper_bundle_path(helper_dist)
    _copy_helper_into_gui_bundle(gui_bundle, helper_bundle)
    output_gui_bundle = _copy_gui_bundle_to_output(gui_bundle, bundle_root)

    _write_bundle_readme(bundle_root)
    archive_path = _expected_archive_path(bundle_root)
    _write_build_info(bundle_root, output_gui_bundle, archive_path)
    _run_smoke_test(output_gui_bundle)
    _maybe_sign_macos_bundle(bundle_root)
    archive_path = _archive_bundle(bundle_root)
    print(f"Standalone GUI bundle created at {output_gui_bundle}")
    print(f"Standalone archive created at {archive_path}")


if __name__ == "__main__":
    main()
