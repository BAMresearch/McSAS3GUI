from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from PyQt6.QtCore import QThread, pyqtSignal

from mcsas3gui._bootstrap import ensure_compatible_mcsas3

ensure_compatible_mcsas3()

logger = logging.getLogger("McSAS3")


def _load_mcsas3_runtime():
    from mcsas3.mc_hat import McHat
    from mcsas3.workflows import optimize_processing_data, prepare_1d_processing_data_from_file

    return McHat, optimize_processing_data, prepare_1d_processing_data_from_file


class OptimizationWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(
        self,
        files_in_out: Mapping[Path, Path],
        *,
        data_config_file: Path,
        run_config_file: Path,
        result_index: int = 1,
    ):
        super().__init__()
        self.files_in_out = dict(files_in_out)
        self.data_config_file = data_config_file
        self.run_config_file = run_config_file
        self.result_index = result_index
        self._stop_requested = False
        self._active_hat = None
        self._active_row: int | None = None

    def request_stop(self) -> None:
        self._stop_requested = True
        if self._active_row is not None:
            self.status_signal.emit(self._active_row, "Stopping...")
        if self._active_hat is not None:
            logger.info("Stop requested for active McSAS3 optimization.")
            self._active_hat.request_stop()

    def run(self) -> None:
        try:
            read_config = self._load_yaml_mapping(self.data_config_file, "data")
            run_config = self._load_yaml_mapping(self.run_config_file, "run")
        except Exception as exc:
            self.finished_signal.emit(False, f"Optimization setup failed: {exc}")
            return

        McHat, optimize_file_processing, prepare_file_processing = _load_mcsas3_runtime()
        total_files = len(self.files_in_out)
        stopped = False
        failed_files: list[Path] = []

        for row, (input_file, result_file) in enumerate(self.files_in_out.items()):
            if self._stop_requested:
                stopped = True
                break

            self._active_row = row
            try:
                if result_file.is_file():
                    result_file.unlink()

                self.status_signal.emit(row, "Running")
                processing = prepare_file_processing(
                    input_file,
                    result_index=self.result_index,
                    **read_config,
                )
                processing_metadata = dict(read_config)
                processing_metadata["filename"] = input_file

                self._active_hat = McHat(resultIndex=self.result_index, **run_config)
                optimize_file_processing(
                    processing,
                    result_file,
                    result_index=self.result_index,
                    processing_metadata=processing_metadata,
                    hat=self._active_hat,
                )

                if self._stop_requested or self._active_hat.lastRunStopped:
                    self.status_signal.emit(row, "Aborted")
                    stopped = True
                    self.progress_signal.emit(int((row + 1) / total_files * 100))
                    break

                self.status_signal.emit(row, "Complete")
            except Exception:
                logger.exception("Optimization failed for %s", input_file)
                failed_files.append(input_file)
                self.status_signal.emit(row, "Failed")
                if self._stop_requested:
                    stopped = True
                    break
            finally:
                self._active_hat = None
                self._active_row = None
                self.progress_signal.emit(int((row + 1) / total_files * 100))

        if stopped:
            message = "Optimization run stopped."
        elif failed_files:
            failed_list = ", ".join(path.name for path in failed_files)
            message = f"Optimization finished with failures for: {failed_list}"
        else:
            message = "All optimizations are complete."
        self.finished_signal.emit(stopped, message)

    @staticmethod
    def _load_yaml_mapping(config_file: Path, label: str) -> dict[str, Any]:
        with open(config_file, "r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise TypeError(f"{label.capitalize()} configuration file must contain a single YAML mapping.")
        return loaded
