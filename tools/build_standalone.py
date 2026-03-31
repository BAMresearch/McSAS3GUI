#!/usr/bin/env python3
"""Build standalone GUI bundles for McSAS3GUI."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import textwrap
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


def _modacor_src_dir() -> Path:
    configured = os.environ.get("MCSAS3GUI_MODACOR_SRC") or os.environ.get("MCSAS3_MODACOR_SRC")
    if configured:
        return Path(configured).expanduser().resolve()
    return ROOT.parent / "MoDaCor" / "src"


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


def _require_modacor_src() -> Path:
    return _require_dir(
        _modacor_src_dir(),
        "the MoDaCor source tree (set MCSAS3GUI_MODACOR_SRC or MCSAS3_MODACOR_SRC to override)",
    )


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
        "--paths",
        str(_require_modacor_src()),
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
        "--paths",
        str(_require_modacor_src()),
        "--additional-hooks-dir",
        str(_core_hooks_dir()),
        "--distpath",
        str(helper_dist),
        "--workpath",
        str(BUILD_ROOT / "work-hist"),
        "--specpath",
        str(BUILD_ROOT / "spec-hist"),
        "--hidden-import",
        "modacor",
        "--hidden-import",
        "modacor.units",
        "--hidden-import",
        "modacor.dataclasses.basedata",
        "--hidden-import",
        "modacor.dataclasses.databundle",
        "--hidden-import",
        "modacor.dataclasses.processing_data",
        "--add-data",
        _add_data_arg(core_root / "example_configurations", "example_configurations"),
        "--add-data",
        _add_data_arg(core_root / "testdata" / "quickstartdemo1.csv", "testdata"),
        str(helper_script),
    ]
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
    shutil.copytree(helper_bundle, destination, dirs_exist_ok=True)


def _copy_gui_bundle_to_output(gui_bundle: Path, bundle_root: Path) -> Path:
    destination = bundle_root / gui_bundle.name
    shutil.copytree(gui_bundle, destination, dirs_exist_ok=True)
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
        f"- sibling MoDaCor checkout at {_modacor_src_dir()}",
        "- or override them with MCSAS3GUI_MCSAS3_SRC and MCSAS3GUI_MODACOR_SRC",
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


def _write_build_info(bundle_root: Path) -> None:
    payload = {
        "platform": _platform_tag(),
        "system": platform.system(),
        "machine": platform.machine(),
        "artifacts": [GUI_APP_NAME, HISTOGRAMMER_NAME],
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
    _write_build_info(bundle_root)
    archive_path = _archive_bundle(bundle_root)
    _run_smoke_test(output_gui_bundle)
    print(f"Standalone GUI bundle created at {output_gui_bundle}")
    print(f"Standalone archive created at {archive_path}")


if __name__ == "__main__":
    main()
