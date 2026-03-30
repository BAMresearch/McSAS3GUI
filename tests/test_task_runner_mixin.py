from mcsas3gui.utils.task_runner_mixin import TaskRunnerMixin


class _Signal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback) -> None:
        self._callbacks.append(callback)

    def emit(self, *args) -> None:
        for callback in self._callbacks:
            callback(*args)


class _FakeWorker:
    def __init__(self) -> None:
        self.progress_signal = _Signal()
        self.status_signal = _Signal()
        self.finished_signal = _Signal()
        self.started = False

    def start(self) -> None:
        self.started = True


class _FakeButton:
    def __init__(self) -> None:
        self.enabled = True

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled


class _FakeProgressBar:
    def __init__(self) -> None:
        self.value = None

    def setValue(self, value: int) -> None:
        self.value = value


class _FakeFileSelectionWidget:
    def __init__(self) -> None:
        self.statuses = []

    def set_status_by_row(self, row: int, status: str) -> None:
        self.statuses.append((row, status))


class _FakeRunner(TaskRunnerMixin):
    task_dialog_title = "Histogramming"

    def __init__(self) -> None:
        self.worker = None
        self.run_button = _FakeButton()
        self.progress_bar = _FakeProgressBar()
        self.file_selection_widget = _FakeFileSelectionWidget()


def test_start_worker_connects_signals_and_starts_worker():
    runner = _FakeRunner()
    worker = _FakeWorker()

    runner.start_worker(worker)
    worker.progress_signal.emit(75)
    worker.status_signal.emit(2, "Complete")

    assert runner.worker is worker
    assert worker.started is True
    assert runner.run_button.enabled is False
    assert runner.progress_bar.value == 75
    assert runner.file_selection_widget.statuses == [(2, "Complete")]


def test_tasks_finished_resets_state_and_reports_success(monkeypatch):
    runner = _FakeRunner()
    runner.worker = object()
    info_messages = []

    monkeypatch.setattr(
        "mcsas3gui.utils.task_runner_mixin.QMessageBox.information",
        lambda parent, title, message: info_messages.append((parent, title, message)),
    )

    runner.tasks_finished(False, "All tasks are complete.")

    assert runner.worker is None
    assert runner.run_button.enabled is True
    assert info_messages == [(runner, "Histogramming", "All tasks are complete.")]
