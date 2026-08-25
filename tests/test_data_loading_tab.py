from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from mcsas3gui.gui import data_loading_tab


def test_external_save_refresh_keeps_custom_yaml_content(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    config_dir = tmp_path / "configurations" / "readdata"
    config_dir.mkdir(parents=True)

    monkeypatch.setattr(data_loading_tab, "get_main_path", lambda: tmp_path)
    monkeypatch.setattr(
        data_loading_tab,
        "get_default_config_files",
        lambda directory: ["default.yaml"],
    )
    monkeypatch.setattr(
        data_loading_tab,
        "load_yaml_file",
        lambda path: {"loaded_from": Path(path).name},
    )

    tab = data_loading_tab.DataLoadingTab()
    custom_yaml = "filename: custom.dat\nQUnits: 1 / angstrom\n"
    tab.yaml_editor_widget.yaml_editor.setPlainText(custom_yaml)

    tab.yaml_editor_widget.fileSaved.emit(str(tmp_path / "saved_elsewhere.yaml"))

    assert tab.config_dropdown.currentText() == "<Custom...>"
    assert tab.yaml_editor_widget.yaml_editor.toPlainText() == custom_yaml
    assert app is not None
