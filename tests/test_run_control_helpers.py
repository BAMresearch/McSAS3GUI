from mcsas3gui.gui.run_control_helpers import (
    RUNNING_BUTTON_STYLE,
    RUNNING_BUTTON_TEXT,
    set_abortable_button_state,
    worker_is_running,
)


class _FakeButton:
    def __init__(self) -> None:
        self.text = ""
        self.style = ""

    def setText(self, text: str) -> None:
        self.text = text

    def setStyleSheet(self, style: str) -> None:
        self.style = style


class _FakeWorker:
    def __init__(self, is_running: bool) -> None:
        self._is_running = is_running

    def isRunning(self) -> bool:
        return self._is_running


def test_worker_is_running_uses_worker_state():
    assert worker_is_running(None) is False
    assert worker_is_running(_FakeWorker(False)) is False
    assert worker_is_running(_FakeWorker(True)) is True


def test_set_abortable_button_state_applies_running_state():
    button = _FakeButton()

    set_abortable_button_state(
        button,
        is_running=True,
        default_text="Run",
        default_style="default",
    )

    assert button.text == RUNNING_BUTTON_TEXT
    assert button.style == RUNNING_BUTTON_STYLE


def test_set_abortable_button_state_restores_default_state():
    button = _FakeButton()

    set_abortable_button_state(
        button,
        is_running=False,
        default_text="Run",
        default_style="default",
    )

    assert button.text == "Run"
    assert button.style == "default"
