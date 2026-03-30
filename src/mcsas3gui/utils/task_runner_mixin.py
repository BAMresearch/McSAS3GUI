from PyQt6.QtWidgets import QMessageBox

from .base_worker import BaseWorker


class TaskRunnerMixin:
    task_dialog_title = "Run Tasks"

    def start_worker(self, worker) -> None:
        """Connect a worker to the shared progress/status/result handlers and start it."""
        self.worker = worker
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.update_file_status)
        self.worker.finished_signal.connect(self.tasks_finished)

        self.progress_bar.setValue(0)
        self._set_task_running_state(True)
        self.worker.start()

    def run_tasks(self, files_in_out, command_builder, extra_keywords=None):
        """
        Run tasks with the provided command template and files.

        Args:
            files_in_out (dict): Pairs for {input:output} file paths to process.
            command_builder: Callable that returns a subprocess argument list for each file.
            extra_keywords (dict): Additional keywords forwarded to the command builder.
        """
        if not files_in_out:
            QMessageBox.warning(self, self.task_dialog_title, "No files selected.")
            return

        worker = BaseWorker(files_in_out, command_builder, extra_keywords)
        self.start_worker(worker)

    def _set_task_running_state(self, is_running: bool) -> None:
        """Apply the default enabled/disabled run-button state while a worker is active."""
        self.run_button.setEnabled(not is_running)

    def update_progress(self, progress):
        """Update the progress bar."""
        self.progress_bar.setValue(progress)

    def update_file_status(self, row, status):
        """Update the status of a file in the table."""
        self.file_selection_widget.set_status_by_row(row, status)

    def tasks_finished(self, failed: bool, message: str):
        """Re-enable the run button and report the overall task result."""
        self._set_task_running_state(False)
        self.worker = None
        if failed:
            QMessageBox.warning(self, self.task_dialog_title, message)
            return
        QMessageBox.information(self, self.task_dialog_title, message)
