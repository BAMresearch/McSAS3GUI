"""Runtime hook to point frozen PyQt6 builds at the bundled Qt paths on macOS."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _bundle_roots() -> list[Path]:
    roots: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))
    executable = Path(sys.executable).resolve()
    roots.append(executable.parent.parent / "Resources")
    roots.append(executable.parent.parent / "Frameworks")
    return roots


if sys.platform == "darwin":
    for root in _bundle_roots():
        qt_root = root / "PyQt6" / "Qt6"
        plugins = qt_root / "plugins"
        qml = qt_root / "qml"
        if plugins.is_dir():
            os.environ.setdefault("QT_PLUGIN_PATH", str(plugins))
            if qml.is_dir():
                os.environ.setdefault("QML2_IMPORT_PATH", str(qml))
            break
