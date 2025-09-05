# src/gui/hist_run_tab.py

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget

from ..utils.file_utils import make_out_path
from ..utils.task_runner_mixin import TaskRunnerMixin
from .file_line_selection_widget import FileLineSelectionWidget
from .file_selection_widget import FileSelectionWidget

logger = logging.getLogger("McSAS3")


class HistRunTab(QWidget, TaskRunnerMixin):
    last_used_directory = Path("~").expanduser()

    def __init__(self, hist_settings_tab, parent=None, temp_dir: Path = None):
        super().__init__(parent)
        assert temp_dir.is_dir(), f"Given temp dir '{temp_dir}' does not exist!"
        self._temp_dir = temp_dir
        self.file_selection_widget = FileSelectionWidget(
            title="Select McSAS3-optimized Files for Histogramming:",
            acceptable_file_types="*.nxs *.h5 *.hdf5",
            last_used_directory=self.last_used_directory,
        )

        layout = QVBoxLayout()
        layout.addWidget(self.file_selection_widget)

        # Data Configuration Section
        self.histogram_config_selector = FileLineSelectionWidget(
            placeholder_text="Select histogramming configuration file",
            file_types="YAML hist config Files (*.yaml)",
        )
        self.histogram_config_selector.fileSelected.connect(
            self.load_hist_config_file
        )  # Handle file selection

        layout.addWidget(self.histogram_config_selector)

        # Run button
        self.run_button = QPushButton("Run Histogramming")
        self.run_button.clicked.connect(self.run_histogramming)
        layout.addWidget(self.run_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def load_hist_config_file(self, file_path: str):
        """Process the file after selection or drop."""
        if Path(file_path).exists():
            self.pdi = []  # clear any previous information
            logger.debug(f"File loaded: {file_path}")
            self.selected_file = file_path
            self.histogram_config_selector.set_file_path(self.selected_file)
        else:
            logger.warning(f"File does not exist: {file_path}")
            QMessageBox.warning(self, "File Error", f"Cannot access file: {file_path}")

    def run_histogramming(self):
        """Run histogramming on the selected files."""

        files = self.file_selection_widget.get_selected_files()
        hist_config = self.histogram_config_selector.get_file_path()

        command_template = (
            str(Path(sys.executable).as_posix())
            + " -m mcsas3.mcsas3_cli_histogrammer -r {input_file} -H {hist_config} -i 1"
        )

        files_in_out = {infn: make_out_path(infn, self._temp_dir) for infn in files}
        extra_keywords = {"hist_config": hist_config}
        self.run_tasks(files, command_template, extra_keywords)
