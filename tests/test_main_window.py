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


def test_main_window_forwards_loaded_configuration_paths(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = McSAS3MainWindow(tmp_path)
    data_settings_tab = window.tabs.widget(1)
    run_settings_tab = window.tabs.widget(2)
    optimization_tab = window.tabs.widget(3)
    histogram_settings_tab = window.tabs.widget(4)
    histogram_run_tab = window.tabs.widget(5)

    data_settings_tab.yaml_editor_widget.fileLoaded.emit("/tmp/data.yml")
    run_settings_tab.yaml_editor_widget.fileLoaded.emit("/tmp/run.yml")
    histogram_settings_tab.yaml_editor_widget.fileLoaded.emit("/tmp/hist.yml")

    assert optimization_tab.data_config_selector.get_file_path() == "/tmp/data.yml"
    assert optimization_tab.run_config_selector.get_file_path() == "/tmp/run.yml"
    assert histogram_run_tab.histogram_config_selector.get_file_path() == "/tmp/hist.yml"
    window.close()
    assert app is not None
