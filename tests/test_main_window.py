from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication, QWidget

from mcsas3gui.gui.main_window import McSAS3MainWindow


class _ClosableTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.closed_aux_windows = False

    def close_auxiliary_windows(self) -> None:
        self.closed_aux_windows = True


class _PlainTab(QWidget):
    pass


def test_main_window_close_event_closes_auxiliary_windows(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    closable_tab = _ClosableTab()
    plain_tab = _PlainTab()

    def fake_setup_tabs(self, temp_dir: Path) -> None:
        assert temp_dir == tmp_path
        self.tabs.addTab(closable_tab, "Closable")
        self.tabs.addTab(plain_tab, "Plain")

    monkeypatch.setattr(McSAS3MainWindow, "setup_tabs", fake_setup_tabs)

    window = McSAS3MainWindow(tmp_path)
    event = QCloseEvent()
    window.closeEvent(event)

    assert closable_tab.closed_aux_windows is True
    assert event.isAccepted()
    assert app is not None
