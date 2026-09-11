import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from mcsas3gui.gui import yaml_editor_widget
from mcsas3gui.gui.file_selection_helpers import load_existing_selector_file
from mcsas3gui.gui.yaml_editor_widget import YAML_FILE_FILTER


class DummySelector:
    def __init__(self) -> None:
        self.file_path: str | None = None

    def set_file_path(self, file_path: str) -> None:
        self.file_path = file_path


def test_yaml_load_dialog_accepts_yaml_and_yml_extensions():
    assert YAML_FILE_FILTER == "YAML Files (*.yaml *.yml)"


def test_yaml_load_emits_selected_configuration_path(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    config_path = tmp_path / "run.yml"
    config_path.write_text("maxIter: 100\n")
    monkeypatch.setattr(
        yaml_editor_widget.QFileDialog,
        "getOpenFileName",
        lambda *args: (str(config_path), YAML_FILE_FILTER),
    )
    editor = yaml_editor_widget.YAMLEditorWidget(tmp_path)
    loaded_paths = []
    editor.fileLoaded.connect(loaded_paths.append)

    editor.load_yaml()

    assert loaded_paths == [str(config_path)]
    assert editor.get_yaml_content() == [{"maxIter": 100}]
    assert app is not None


def test_load_existing_selector_file_updates_selector_and_runs_callback(tmp_path):
    target = tmp_path / "example.yaml"
    target.write_text("value: 1\n")
    selector = DummySelector()
    loaded_paths: list[Path] = []

    path = load_existing_selector_file(
        object(),
        selector,
        str(target),
        on_loaded=loaded_paths.append,
    )

    assert path == target
    assert selector.file_path == str(target)
    assert loaded_paths == [target]


def test_load_existing_selector_file_warns_for_missing_file(monkeypatch, tmp_path):
    selector = DummySelector()
    missing_file = tmp_path / "missing.yaml"
    parent = object()
    warnings: list[tuple[object, str, str]] = []

    monkeypatch.setattr(
        "mcsas3gui.gui.file_selection_helpers.QMessageBox.warning",
        lambda parent, title, message: warnings.append((parent, title, message)),
    )

    path = load_existing_selector_file(parent, selector, str(missing_file))

    assert path is None
    assert selector.file_path is None
    assert warnings == [(parent, "File Error", f"Cannot access file: {missing_file}")]
