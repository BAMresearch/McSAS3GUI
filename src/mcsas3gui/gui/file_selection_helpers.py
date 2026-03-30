import logging
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from PyQt6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger("McSAS3")


class FilePathSelector(Protocol):
    def set_file_path(self, file_path: str) -> None: ...


def load_existing_selector_file(
    parent: QWidget,
    selector: FilePathSelector,
    file_path: str,
    *,
    on_loaded: Callable[[Path], None] | None = None,
    warning_title: str = "File Error",
) -> Path | None:
    """Validate a selected file path, update the selector, and run optional follow-up work."""
    path = Path(file_path)
    if not path.exists():
        logger.warning("File does not exist: %s", file_path)
        QMessageBox.warning(parent, warning_title, f"Cannot access file: {file_path}")
        return None

    logger.debug("File loaded: %s", path)
    selector.set_file_path(str(path))
    if on_loaded is not None:
        on_loaded(path)
    return path
