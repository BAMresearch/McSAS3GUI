from __future__ import annotations

import logging
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pandas as pd
import yaml
from mcsas3.mc_hdf import ResultIndex, loadKV
from mcsas3.workflows import prepare_1d_processing_data
from PyQt6.QtWidgets import QApplication

from mcsas3gui.gui import optimization_worker, run_settings_tab


class _FakeHat:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.lastRunStopped = False
        self.stop_requested = False

    def request_stop(self) -> None:
        self.stop_requested = True


class _FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)

    def emit(self, *args) -> None:
        for callback in self.callbacks:
            callback(*args)


class _FakePreviewWorker:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.progress_text_signal = _FakeSignal()
        self.preview_ready_signal = _FakeSignal()
        self.finished_signal = _FakeSignal()
        self.finished = _FakeSignal()
        self.started = False
        self.deleted = False

    def start(self) -> None:
        self.started = True

    def deleteLater(self) -> None:
        self.deleted = True


def test_optimization_worker_request_stop_forwards_to_active_hat(tmp_path):
    worker = optimization_worker.OptimizationWorker(
        {tmp_path / "input.dat": tmp_path / "result.h5"},
        data_config_file=tmp_path / "data.yaml",
        run_config_file=tmp_path / "run.yaml",
        result_index=2,
    )
    worker._active_hat = _FakeHat()
    worker._active_row = 3
    statuses: list[tuple[int, str]] = []
    worker.status_signal.connect(lambda row, status: statuses.append((row, status)))

    worker.request_stop()

    assert worker._stop_requested is True
    assert worker._active_hat.stop_requested is True
    assert statuses == [(3, "Stopping...")]


def test_optimization_worker_run_passes_processing_metadata(tmp_path, monkeypatch):
    input_file = tmp_path / "input.dat"
    result_file = tmp_path / "result.h5"
    input_file.write_text("data")
    data_config = tmp_path / "data.yaml"
    run_config = tmp_path / "run.yaml"
    data_config.write_text(yaml.safe_dump({"QUnits": "1 / angstrom"}))
    run_config.write_text(yaml.safe_dump({"modelName": "sphere", "nRep": 3}))

    captured: dict[str, object] = {}

    def fake_prepare(file_path: Path, *, result_index: int, **kwargs):
        captured["prepare"] = (file_path, result_index, kwargs)
        return {"processing": True}

    def fake_optimize(processing, target_file: Path, *, result_index: int, hat, processing_metadata):
        captured["optimize"] = (processing, target_file, result_index, hat, processing_metadata)

    monkeypatch.setattr(
        optimization_worker,
        "_load_mcsas3_runtime",
        lambda: (_FakeHat, fake_optimize, fake_prepare),
    )

    statuses: list[tuple[int, str]] = []
    finished: list[tuple[bool, str]] = []
    progress_values: list[int] = []

    worker = optimization_worker.OptimizationWorker(
        {input_file: result_file},
        data_config_file=data_config,
        run_config_file=run_config,
        result_index=4,
    )
    worker.status_signal.connect(lambda row, status: statuses.append((row, status)))
    worker.finished_signal.connect(lambda stopped, message: finished.append((stopped, message)))
    worker.progress_signal.connect(progress_values.append)

    worker.run()

    assert captured["prepare"][0] == input_file
    assert captured["prepare"][1] == 4
    assert captured["optimize"][0] == {"processing": True}
    assert captured["optimize"][1] == result_file
    assert captured["optimize"][2] == 4
    assert captured["optimize"][3].kwargs["resultIndex"] == 4
    assert captured["optimize"][3].kwargs["modelName"] == "sphere"
    assert captured["optimize"][4]["QUnits"] == "1 / angstrom"
    assert captured["optimize"][4]["filename"] == input_file
    assert statuses == [(0, "Running"), (0, "Complete")]
    assert progress_values == [100]
    assert finished == [(False, "All optimizations are complete.")]


def test_runtime_run_config_defaults_to_nondeterministic_seed_for_multiple_repetitions():
    runtime_config = optimization_worker._runtime_run_config({"modelName": "sphere", "nRep": 2})

    assert runtime_config["modelName"] == "sphere"
    assert runtime_config["nRep"] == 2
    assert runtime_config["seed"] is None


def test_runtime_run_config_preserves_explicit_seed():
    runtime_config = optimization_worker._runtime_run_config(
        {
            "modelName": "sphere",
            "nRep": 2,
            "seed": 7,
            "fitFlatBackground": "positive",
            "fitPorodBackground": True,
        }
    )

    assert runtime_config["seed"] == 7
    assert runtime_config["fitFlatBackground"] == "positive"
    assert runtime_config["fitPorodBackground"] is True


def test_execute_hat_run_multi_repetition_uses_distinct_random_starts(tmp_path):
    processing = prepare_1d_processing_data(
        pd.DataFrame(
            {
                "Q": np.array([0.1, 0.2, 0.3, 0.4], dtype=float),
                "I": np.array([10.0, 7.0, 4.0, 2.0], dtype=float),
                "ISigma": np.array([1.0, 1.0, 1.0, 1.0], dtype=float),
            }
        ),
        nbins=4,
    )
    result_file = tmp_path / "multi_rep.h5"
    McHat, optimize_processing, _prepare_processing = optimization_worker._load_mcsas3_runtime()

    optimization_worker._execute_hat_run(
        hat_factory=McHat,
        optimize_processing=optimize_processing,
        processing=processing,
        result_file=result_file,
        result_index=1,
        run_config={
            "modelName": "sphere",
            "nContrib": 20,
            "modelDType": "default",
            "fitParameterLimits": {"radius": [1.0, 100.0]},
            "staticParameters": {"sld": 33.4, "sld_solvent": 0.0, "background": 0.0},
            "maxIter": 1,
            "maxAccept": 1,
            "convCrit": 0.0,
            "fitFlatBackground": False,
            "fitPorodBackground": True,
            "nRep": 2,
            "nCores": 2,
        },
    )

    path = ResultIndex(1).nxsEntryPoint / "model"
    repetition0 = loadKV(result_file, path / "repetition0" / "parameterSet", datatype="dictToPandas")
    repetition1 = loadKV(result_file, path / "repetition1" / "parameterSet", datatype="dictToPandas")
    assert not repetition0.equals(repetition1)
    optimization_path = ResultIndex(1).nxsEntryPoint / "optimization" / "repetition0"
    fit_parameters = np.asarray(loadKV(result_file, optimization_path / "x0"), dtype=float)
    parameter_names = [value.decode() for value in loadKV(result_file, optimization_path / "x0ParameterNames")]
    assert parameter_names == ["scale", "background", "porodCoefficient"]
    assert fit_parameters.shape == (3,)
    assert fit_parameters[1] == 0.0
    assert fit_parameters[2] >= 0.0


def test_execute_hat_run_explicit_seed_offsets_by_repetition(tmp_path):
    processing = prepare_1d_processing_data(
        pd.DataFrame(
            {
                "Q": np.array([0.1, 0.2, 0.3, 0.4], dtype=float),
                "I": np.array([10.0, 7.0, 4.0, 2.0], dtype=float),
                "ISigma": np.array([1.0, 1.0, 1.0, 1.0], dtype=float),
            }
        ),
        nbins=4,
    )
    result_file = tmp_path / "seeded_multi_rep.h5"
    McHat, optimize_processing, _prepare_processing = optimization_worker._load_mcsas3_runtime()

    optimization_worker._execute_hat_run(
        hat_factory=McHat,
        optimize_processing=optimize_processing,
        processing=processing,
        result_file=result_file,
        result_index=1,
        run_config={
            "modelName": "sphere",
            "nContrib": 20,
            "modelDType": "default",
            "fitParameterLimits": {"radius": [1.0, 100.0]},
            "staticParameters": {"sld": 33.4, "sld_solvent": 0.0, "background": 0.0},
            "maxIter": 1,
            "maxAccept": 1,
            "convCrit": 0.0,
            "nRep": 2,
            "nCores": 2,
            "seed": 5000,
        },
    )

    path = ResultIndex(1).nxsEntryPoint / "model"
    repetition0 = loadKV(result_file, path / "repetition0" / "parameterSet", datatype="dictToPandas")
    repetition1 = loadKV(result_file, path / "repetition1" / "parameterSet", datatype="dictToPandas")
    seed0 = loadKV(result_file, path / "repetition0" / "seed")
    seed1 = loadKV(result_file, path / "repetition1" / "seed")

    assert int(seed0) == 5000
    assert int(seed1) == 5001
    assert not repetition0.equals(repetition1)


def test_optimization_worker_run_reports_aborted_result(tmp_path, monkeypatch):
    input_file = tmp_path / "input.dat"
    result_file = tmp_path / "result.h5"
    input_file.write_text("data")
    data_config = tmp_path / "data.yaml"
    run_config = tmp_path / "run.yaml"
    data_config.write_text(yaml.safe_dump({}))
    run_config.write_text(yaml.safe_dump({"modelName": "sphere"}))

    def fake_prepare(file_path: Path, *, result_index: int, **kwargs):
        _ = file_path, result_index, kwargs
        return {"processing": True}

    def fake_optimize(processing, target_file: Path, *, result_index: int, hat, processing_metadata):
        _ = processing, target_file, result_index, processing_metadata
        hat.lastRunStopped = True

    monkeypatch.setattr(
        optimization_worker,
        "_load_mcsas3_runtime",
        lambda: (_FakeHat, fake_optimize, fake_prepare),
    )

    statuses: list[tuple[int, str]] = []
    finished: list[tuple[bool, str]] = []

    worker = optimization_worker.OptimizationWorker(
        {input_file: result_file},
        data_config_file=data_config,
        run_config_file=run_config,
        result_index=1,
    )
    worker.status_signal.connect(lambda row, status: statuses.append((row, status)))
    worker.finished_signal.connect(lambda stopped, message: finished.append((stopped, message)))

    worker.run()

    assert statuses == [(0, "Running"), (0, "Aborted")]
    assert finished == [(True, "Optimization run stopped.")]


def test_preview_optimization_worker_forces_single_repetition(tmp_path, monkeypatch):
    result_file = tmp_path / "preview.h5"
    result_file.write_text("stale")
    captured: dict[str, object] = {}

    def fake_optimize(processing, target_file: Path, *, result_index: int, hat):
        captured["optimize"] = (processing, target_file, result_index, hat)
        assert not target_file.exists()

    def fake_load_preview(result_file_arg: Path, processing, *, result_index: int, repetition: int):
        captured["preview"] = (result_file_arg, processing, result_index, repetition)
        return {"preview": True}

    monkeypatch.setattr(
        optimization_worker,
        "_load_mcsas3_runtime",
        lambda: (_FakeHat, fake_optimize, lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(optimization_worker, "_load_bridge_runtime", lambda: fake_load_preview)

    previews: list[object] = []
    finished: list[tuple[bool, str]] = []
    worker = optimization_worker.PreviewOptimizationWorker(
        processing={"processing": True},
        result_file=result_file,
        run_config={"modelName": "sphere", "nRep": 99},
        result_index=2,
    )
    worker.preview_ready_signal.connect(previews.append)
    worker.finished_signal.connect(lambda stopped, message: finished.append((stopped, message)))

    worker.run()

    assert captured["optimize"][2] == 2
    assert captured["optimize"][3].kwargs["nRep"] == 1
    assert previews == [{"preview": True}]
    assert captured["preview"] == (result_file, {"processing": True}, 2, 0)
    assert finished == [(False, "Optimization completed successfully.")]


def test_preview_worker_import_failure_is_reported(tmp_path, monkeypatch):
    def fail_runtime_import():
        raise ImportError("incompatible McSAS3 core")

    monkeypatch.setattr(optimization_worker, "_load_mcsas3_runtime", fail_runtime_import)
    finished: list[tuple[bool, str]] = []
    worker = optimization_worker.PreviewOptimizationWorker(
        processing={"processing": True},
        result_file=tmp_path / "preview.h5",
        run_config={"modelName": "sphere"},
    )
    worker.finished_signal.connect(lambda stopped, message: finished.append((stopped, message)))

    worker.run()

    assert finished == [(False, "Error during test optimization: incompatible McSAS3 core")]


def test_run_settings_tab_retains_preview_worker_until_qthread_finishes(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(run_settings_tab, "get_default_config_files", lambda directory: [])
    monkeypatch.setattr(run_settings_tab, "PreviewOptimizationWorker", _FakePreviewWorker)
    tab = run_settings_tab.RunSettingsTab(temp_dir=tmp_path)

    tab._start_preview_worker({"processing": True}, {"modelName": "sphere"})
    worker = tab.preview_worker
    tab.preview_result_file.write_text("result")

    worker.finished_signal.emit(False, "Preview failed safely.")

    assert tab.preview_worker is worker
    assert tab.preview_result_file.exists()
    assert worker.deleted is False

    worker.finished.emit()

    assert tab.preview_worker is None
    assert not tab.preview_result_file.exists()
    assert worker.deleted is True
    tab.close()
    assert app is not None


def test_preview_optimization_worker_emits_live_progress_messages(tmp_path, monkeypatch):
    result_file = tmp_path / "preview.h5"

    def fake_optimize(processing, target_file: Path, *, result_index: int, hat):
        _ = processing, target_file, result_index, hat
        logging.getLogger("mcsas3.mc_core").info("Optimization of repetition 0 started.")
        logging.getLogger("mcsas3.mc_core").info("chiSqr: 1.23, N accepted: 4 / 500")

    monkeypatch.setattr(
        optimization_worker,
        "_load_mcsas3_runtime",
        lambda: (_FakeHat, fake_optimize, lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(optimization_worker, "_load_bridge_runtime", lambda: lambda *args, **kwargs: {"ok": True})

    progress_messages: list[str] = []
    worker = optimization_worker.PreviewOptimizationWorker(
        processing={"processing": True},
        result_file=result_file,
        run_config={"modelName": "sphere"},
        result_index=1,
    )
    worker.progress_text_signal.connect(progress_messages.append)

    worker.run()

    assert "Optimization of repetition 0 started." in progress_messages
    assert "chiSqr: 1.23, N accepted: 4 / 500" in progress_messages
