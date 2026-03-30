from typing import Protocol

RUNNING_BUTTON_TEXT = "Running... Click to abort."
RUNNING_BUTTON_STYLE = "QPushButton { background-color: #c65a3a; color: white; font-weight: bold; }"


class AbortableButton(Protocol):
    def setText(self, text: str) -> None: ...

    def setStyleSheet(self, style: str) -> None: ...


def worker_is_running(worker: object | None) -> bool:
    """Return whether a worker-like object exists and reports an active run."""
    return worker is not None and bool(worker.isRunning())


def set_abortable_button_state(
    button: AbortableButton,
    *,
    is_running: bool,
    default_text: str,
    default_style: str,
    running_text: str = RUNNING_BUTTON_TEXT,
    running_style: str = RUNNING_BUTTON_STYLE,
) -> None:
    """Apply the shared run/abort button state used by long-running GUI tasks."""
    if is_running:
        button.setText(running_text)
        button.setStyleSheet(running_style)
        return

    button.setText(default_text)
    button.setStyleSheet(default_style)
