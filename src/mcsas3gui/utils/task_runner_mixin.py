from PyQt6.QtWidgets import QMessageBox

from .base_worker import BaseWorker


class TaskRunnerMixin:
    def run_tasks(self, files_in_out, command_builder, extra_keywords=None):
        """
        Run tasks with the provided command template and files.

        Args:
            files_in_out (dict): Pairs for {input:output} file paths to process.
            command_builder: Callable that returns a subprocess argument list for each file.
            extra_keywords (dict): Additional keywords forwarded to the command builder.
        """
        if not files_in_out:
            QMessageBox.warning(self, "Run Tasks", "No files selected.")
            return

        self.worker = BaseWorker(files_in_out, command_builder, extra_keywords)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.update_file_status)
        self.worker.finished_signal.connect(self.tasks_finished)

        self.run_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.worker.start()

    def update_progress(self, progress):
        """Update the progress bar."""
        self.progress_bar.setValue(progress)

    def update_file_status(self, row, status):
        """Update the status of a file in the table."""
        self.file_selection_widget.set_status_by_row(row, status)

    def tasks_finished(self):
        """Re-enable the run button after tasks are complete."""
        self.run_button.setEnabled(True)
        QMessageBox.information(self, "Run Tasks", "All tasks are complete.")
