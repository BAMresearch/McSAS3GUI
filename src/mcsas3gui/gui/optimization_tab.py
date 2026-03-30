import logging
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget

from ..utils.file_utils import make_out_path
from ..utils.task_runner_mixin import TaskRunnerMixin
from .file_line_selection_widget import FileLineSelectionWidget
from .file_selection_helpers import load_existing_selector_file
from .file_selection_widget import FileSelectionWidget
from .optimization_worker import OptimizationWorker

logger = logging.getLogger("McSAS3")


class OptimizationRunTab(QWidget, TaskRunnerMixin):
    last_used_directory = Path("~").expanduser()
    task_dialog_title = "McSAS3 Optimization"
    _temp_dir = None  # provided by __main__, for testdata results, out-of-source
    _running_button_style = "QPushButton { background-color: #c65a3a; color: white; font-weight: bold; }"

    def __init__(
        self,
        parent=None,
        data_loading_tab=None,
        run_settings_tab=None,
        hist_settings_tab=None,
        histogramming_tab=None,
        temp_dir: Path = None,
    ):
        super().__init__(parent)
        if temp_dir is None or not temp_dir.is_dir():
            raise FileNotFoundError(f"Given temp dir '{temp_dir}' does not exist!")
        self._temp_dir = temp_dir
        self.data_loading_tab = data_loading_tab
        self.run_settings_tab = run_settings_tab
        self.hist_settings_tab = hist_settings_tab
        self.histogramming_tab = histogramming_tab
        self.worker: OptimizationWorker | None = None

        self.file_selection_widget = FileSelectionWidget(
            title="Loaded Files:",
            acceptable_file_types="*.*",
            last_used_directory=self.last_used_directory,
        )

        layout = QVBoxLayout()
        layout.addWidget(self.file_selection_widget)

        # Data Configuration Section
        self.data_config_selector = FileLineSelectionWidget(
            placeholder_text="Select data load configuration file",
            file_types="YAML data config Files (*.yaml)",
        )
        self.data_config_selector.fileSelected.connect(self.load_data_config_file)  # Handle file selection
        # self.data_loading_tab.yaml_editor_widget.yaml_editor.fileSaved.\
        # connect(self.data_config_selector.set_file_path)  # Handle file save

        layout.addWidget(self.data_config_selector)

        # Run Configuration Section
        self.run_config_selector = FileLineSelectionWidget(
            placeholder_text="Select run configuration file",
            file_types="YAML run config Files (*.yaml)",
        )
        self.run_config_selector.fileSelected.connect(self.load_run_config_file)  # Handle file selection
        # self.run_settings_tab.yaml_editor_widget.yaml_editor.fileSaved.\
        # connect(self.run_config_selector.set_file_path)  # Handle file save

        layout.addWidget(self.run_config_selector)

        # Progress and Run Controls
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.run_button = QPushButton("Run McSAS3 Optimization ...")
        self._default_run_button_style = self.run_button.styleSheet()
        self.run_button.clicked.connect(self.handle_run_button_clicked)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

    def load_data_config_file(self, file_path: str):
        """Process the file after selection or drop."""
        load_existing_selector_file(self, self.data_config_selector, file_path)

    def load_run_config_file(self, file_path: str):
        """Process the file after selection or drop."""
        load_existing_selector_file(self, self.run_config_selector, file_path)

    def _set_expected_output(self, outpath):
        if self.hist_settings_tab:
            self.hist_settings_tab.test_file_selector.set_file_path(str(outpath))
        if self.histogramming_tab:
            self.histogramming_tab.file_selection_widget.add_file_to_table(str(outpath))

    def handle_run_button_clicked(self):
        if self.worker is not None and self.worker.isRunning():
            self.request_stop()
            return
        self.start_optimizations()

    def _set_task_running_state(self, is_running: bool) -> None:
        if is_running:
            self.run_button.setText("Running... Click to abort.")
            self.run_button.setStyleSheet(self._running_button_style)
            return

        self.run_button.setText("Run McSAS3 Optimization ...")
        self.run_button.setStyleSheet(self._default_run_button_style)

    def start_optimizations(self):
        files = self.file_selection_widget.get_selected_files()
        data_config = self.data_config_selector.get_file_path()
        run_config = self.run_config_selector.get_file_path()
        if not files:
            QMessageBox.warning(self, "McSAS3 Optimization", "No files selected.")
            return
        if not data_config:
            QMessageBox.warning(self, "McSAS3 Optimization", "Select a data load configuration file first.")
            return
        if not run_config:
            QMessageBox.warning(self, "McSAS3 Optimization", "Select a run configuration file first.")
            return

        files_in_out = {infn: make_out_path(infn, self._temp_dir) for infn in files}
        self._set_expected_output(list(files_in_out.values())[0])  # forward the first output file

        self.worker = OptimizationWorker(
            files_in_out,
            data_config_file=Path(data_config),
            run_config_file=Path(run_config),
            result_index=1,
        )
        self.start_worker(self.worker)

    def request_stop(self):
        if self.worker is None or not self.worker.isRunning():
            return
        logger.info("Abort requested from optimization tab.")
        self.worker.request_stop()

    def tasks_finished(self, stopped: bool, message: str):
        self._set_task_running_state(False)
        self.worker = None
        QMessageBox.information(self, self.task_dialog_title, message)
