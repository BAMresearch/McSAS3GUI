from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import yaml
from PyQt6.QtCore import QThread, pyqtSignal

from mcsas3gui._bootstrap import ensure_compatible_mcsas3

ensure_compatible_mcsas3()

logger = logging.getLogger("McSAS3")
McHatFactory = Callable[..., Any]
OptimizeProcessingFn = Callable[..., Any]
PrepareFileProcessingFn = Callable[..., Any]
LoadPreviewFn = Callable[..., Any]


def _load_mcsas3_runtime() -> tuple[McHatFactory, OptimizeProcessingFn, PrepareFileProcessingFn]:
    """Import the core McSAS3 runtime lazily so GUI startup stays lightweight."""
    from mcsas3.mc_hat import McHat
    from mcsas3.workflows import optimize_processing_data, prepare_1d_processing_data_from_file

    return McHat, optimize_processing_data, prepare_1d_processing_data_from_file


def _load_bridge_runtime() -> LoadPreviewFn:
    """Import the GUI bridge lazily to avoid import cycles during module initialization."""
    from .mcsas3_bridge import load_optimization_preview

    return load_optimization_preview


def _load_yaml_mapping(config_file: Path, label: str) -> dict[str, Any]:
    """Load a single-document YAML mapping from a configuration file."""
    with open(config_file, "r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise TypeError(f"{label.capitalize()} configuration file must contain a single YAML mapping.")
    return loaded


def _unlink_if_exists(path: Path) -> None:
    """Remove a file if it already exists."""
    if path.is_file():
        path.unlink()


def _run_was_stopped(stop_requested: bool, hat: Any) -> bool:
    """Return whether a run should be treated as stopped by GUI cancellation."""
    return stop_requested or bool(getattr(hat, "lastRunStopped", False))


def _preview_run_config(run_config: Mapping[str, Any]) -> dict[str, Any]:
    """Coerce a run configuration to the single-repetition preview shape."""
    preview_config = dict(run_config)
    preview_config["nRep"] = 1
    return preview_config


def _execute_hat_run(
    *,
    hat_factory: McHatFactory,
    optimize_processing: OptimizeProcessingFn,
    processing: Any,
    result_file: Path,
    result_index: int,
    run_config: Mapping[str, Any],
    processing_metadata: Mapping[str, Any] | None = None,
) -> Any:
    """Execute a McSAS3 optimization run through a caller-supplied `McHat` factory."""
    _unlink_if_exists(result_file)
    hat = hat_factory(resultIndex=result_index, **dict(run_config))
    optimize_kwargs: dict[str, Any] = {
        "result_index": result_index,
        "hat": hat,
    }
    if processing_metadata is not None:
        optimize_kwargs["processing_metadata"] = processing_metadata
    optimize_processing(processing, result_file, **optimize_kwargs)
    return hat


class OptimizationWorker(QThread):
    """Background worker that runs canonical McSAS3 optimizations for multiple input files."""

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
            read_config = _load_yaml_mapping(self.data_config_file, "data")
            run_config = _load_yaml_mapping(self.run_config_file, "run")
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
                self.status_signal.emit(row, "Running")
                processing = prepare_file_processing(
                    input_file,
                    result_index=self.result_index,
                    **read_config,
                )
                processing_metadata = dict(read_config)
                processing_metadata["filename"] = input_file

                self._active_hat = _execute_hat_run(
                    hat_factory=McHat,
                    optimize_processing=optimize_file_processing,
                    processing=processing,
                    result_file=result_file,
                    result_index=self.result_index,
                    run_config=run_config,
                    processing_metadata=processing_metadata,
                )

                if _run_was_stopped(self._stop_requested, self._active_hat):
                    self.status_signal.emit(row, "Aborted")
                    stopped = True
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


class PreviewOptimizationWorker(QThread):
    """Background worker for the single-repetition preview optimization in the run-settings tab."""

    preview_ready_signal = pyqtSignal(object)
    finished_signal = pyqtSignal(bool, str)

    def __init__(
        self,
        *,
        processing: Any,
        result_file: Path,
        run_config: Mapping[str, Any],
        result_index: int = 1,
    ):
        super().__init__()
        self.processing = processing
        self.result_file = result_file
        self.run_config = dict(run_config)
        self.result_index = result_index
        self._stop_requested = False
        self._active_hat = None

    def request_stop(self) -> None:
        self._stop_requested = True
        if self._active_hat is not None:
            logger.info("Stop requested for active McSAS3 preview optimization.")
            self._active_hat.request_stop()

    def run(self) -> None:
        McHat, optimize_file_processing, _prepare_file_processing = _load_mcsas3_runtime()
        load_preview = _load_bridge_runtime()
        try:
            self._active_hat = _execute_hat_run(
                hat_factory=McHat,
                optimize_processing=optimize_file_processing,
                processing=self.processing,
                result_file=self.result_file,
                result_index=self.result_index,
                run_config=_preview_run_config(self.run_config),
            )

            if _run_was_stopped(self._stop_requested, self._active_hat):
                self.finished_signal.emit(True, "Preview optimization stopped.")
                return

            preview = load_preview(
                self.result_file,
                self.processing,
                result_index=self.result_index,
                repetition=0,
            )
            self.preview_ready_signal.emit(preview)
            self.finished_signal.emit(False, "Optimization completed successfully.")
        except Exception as exc:
            logger.exception("Preview optimization failed")
            self.finished_signal.emit(False, f"Error during test optimization: {exc}")
        finally:
            self._active_hat = None
