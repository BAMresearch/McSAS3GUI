from __future__ import annotations

import subprocess
from pathlib import Path

from mcsas3gui.utils.base_worker import BaseWorker


def test_base_worker_reports_success(tmp_path, monkeypatch):
    input_file = tmp_path / "input.nxs"
    result_file = tmp_path / "result.pdf"
    input_file.write_text("test")
    result_file.write_text("stale")

    captured = {"commands": []}
    statuses: list[tuple[int, str]] = []
    progress_values: list[int] = []
    finished: list[tuple[bool, str]] = []

    def command_builder(input_path: Path, output_path: Path, extra_keywords):
        assert input_path == input_file
        assert output_path == result_file
        assert extra_keywords == {"hist_config": "hist.yaml"}
        return ["echo", str(input_path), str(output_path)]

    def fake_run(command, check):
        captured["commands"].append((command, check))

    monkeypatch.setattr(subprocess, "run", fake_run)

    worker = BaseWorker({input_file: result_file}, command_builder, {"hist_config": "hist.yaml"})
    worker.status_signal.connect(lambda row, status: statuses.append((row, status)))
    worker.progress_signal.connect(progress_values.append)
    worker.finished_signal.connect(lambda failed, message: finished.append((failed, message)))

    worker.run()

    assert not result_file.exists()
    assert captured["commands"] == [(["echo", str(input_file), str(result_file)], True)]
    assert statuses == [(0, "Running"), (0, "Complete")]
    assert progress_values == [100]
    assert finished == [(False, "All tasks are complete.")]


def test_base_worker_reports_failed_files(tmp_path, monkeypatch):
    input_file = tmp_path / "input.nxs"
    result_file = tmp_path / "result.pdf"
    input_file.write_text("test")

    statuses: list[tuple[int, str]] = []
    finished: list[tuple[bool, str]] = []

    def command_builder(input_path: Path, output_path: Path, extra_keywords):
        assert input_path == input_file
        assert output_path == result_file
        assert extra_keywords == {}
        return ["false"]

    def fake_run(command, check):
        raise subprocess.CalledProcessError(returncode=1, cmd=command)

    monkeypatch.setattr(subprocess, "run", fake_run)

    worker = BaseWorker({input_file: result_file}, command_builder)
    worker.status_signal.connect(lambda row, status: statuses.append((row, status)))
    worker.finished_signal.connect(lambda failed, message: finished.append((failed, message)))

    worker.run()

    assert statuses == [(0, "Running"), (0, "Failed")]
    assert finished == [(True, "Tasks finished with failures for: input.nxs")]
