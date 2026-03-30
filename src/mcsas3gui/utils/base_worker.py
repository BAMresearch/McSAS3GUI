import logging
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("McSAS3")
CommandBuilder = Callable[[Path, Path, Mapping[str, Any]], list[str]]


class BaseWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, files_in_out, command_builder: CommandBuilder, extra_keywords=None):
        """
        Args:
            files_in_out (dict): Pairs for {input:output} file paths to process.
            command_builder: Callable that returns a subprocess argument list for each file.
            extra_keywords (dict): Additional keywords for replacing in the command template.
        """
        super().__init__()
        self.files_in_out = files_in_out
        self.command_builder = command_builder
        self.extra_keywords = extra_keywords or {}

    def run(self):
        """Run commands sequentially."""
        total_files = len(self.files_in_out)
        failed_files: list[Path] = []
        for row, (file_name, result_file) in enumerate(self.files_in_out.items()):
            if result_file.is_file():
                result_file.unlink()

            command = self.command_builder(Path(file_name), Path(result_file), self.extra_keywords)

            logger.info(f"Running command: {command}")

            try:
                self.status_signal.emit(row, "Running")
                subprocess.run(command, check=True)
                self.status_signal.emit(row, "Complete")
            except subprocess.CalledProcessError:
                logger.exception("Task command failed for %s", file_name)
                failed_files.append(Path(file_name))
                self.status_signal.emit(row, "Failed")
            except Exception:
                logger.exception("Task runner failed for %s", file_name)
                failed_files.append(Path(file_name))
                self.status_signal.emit(row, "Failed")

            # Update progress
            progress = int((row + 1) / total_files * 100)
            self.progress_signal.emit(progress)

        if failed_files:
            failed_list = ", ".join(path.name for path in failed_files)
            self.finished_signal.emit(True, f"Tasks finished with failures for: {failed_list}")
            return
        self.finished_signal.emit(False, "All tasks are complete.")
