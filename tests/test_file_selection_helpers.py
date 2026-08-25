from pathlib import Path

from mcsas3gui.gui.file_selection_helpers import load_existing_selector_file


class DummySelector:
    def __init__(self) -> None:
        self.file_path: str | None = None

    def set_file_path(self, file_path: str) -> None:
        self.file_path = file_path


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
