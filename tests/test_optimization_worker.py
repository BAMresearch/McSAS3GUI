from __future__ import annotations

import logging
from pathlib import Path

import yaml

from mcsas3gui.gui import optimization_worker


class _FakeHat:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.lastRunStopped = False
        self.stop_requested = False

    def request_stop(self) -> None:
        self.stop_requested = True


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
