from __future__ import annotations

import mcsas3gui.__main__ as gui_main


def test_main_prints_version(capsys):
    exit_code = gui_main.main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip()


def test_main_smoke_test_exits_without_event_loop(monkeypatch):
    events: list[str] = []

    class DummyApp:
        def __init__(self, argv):
            self.argv = argv

        def quit(self) -> None:
            events.append("app_quit")

        def exec(self) -> int:
            events.append("app_exec")
            return 99

    class DummyWindow:
        def __init__(self, temp_dir):
            self.temp_dir = temp_dir

        def show(self) -> None:
            events.append("window_show")

        def close(self) -> None:
            events.append("window_close")

    monkeypatch.setattr("PyQt6.QtWidgets.QApplication", DummyApp)
    monkeypatch.setattr("mcsas3gui.gui.main_window.McSAS3MainWindow", DummyWindow)

    exit_code = gui_main.main(["--smoke-test"])

    assert exit_code == 0
    assert events == ["window_show", "window_close", "app_quit"]
