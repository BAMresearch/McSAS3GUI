import os
import logging
from pathlib import Path
from tempfile import gettempdir
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QTextEdit, QFileDialog, QMessageBox, QComboBox
)
import yaml
from .yaml_editor_widget import YAMLEditorWidget
from .file_line_selection_widget import FileLineSelectionWidget
from ..utils.file_utils import get_default_config_files, get_main_path

import subprocess

logger = logging.getLogger("McSAS3")


class HistogramSettingsTab(QWidget):
    _programmatic_change = False
    default_configs = []  # List to hold default configuration files
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_path = get_main_path()  # Get the main path of the application
        self.last_used_directory = Path(gettempdir())  # Default to system temp directory
        self.test_data_file = None  # Store the selected test data file

        layout = QVBoxLayout()

        # Dropdown for histogram configurations
        self.config_dropdown = QComboBox()
        self.refresh_config_dropdown()
        layout.addWidget(QLabel("Select Default Histogramming Configuration:"))
        layout.addWidget(self.config_dropdown)
        self.config_dropdown.currentTextChanged.connect(self.handle_dropdown_change)

        # YAML Editor for histogram settings
        self.yaml_editor_widget = YAMLEditorWidget(directory=self.main_path / "hist_configurations", parent=self, multipart=True)
        layout.addWidget(QLabel("Histogramming Configuration (YAML):"))
        layout.addWidget(self.yaml_editor_widget)

        # Monitor changes in the YAML editor to detect custom changes
        self.yaml_editor_widget.yaml_editor.textChanged.connect(self.on_yaml_editor_change)
        self.yaml_editor_widget.fileSaved.connect(self.refresh_config_dropdown)  # Refresh dropdown after save

        # File Selection for Test Datafile
        self.test_file_selector = FileLineSelectionWidget(
            placeholder_text="Select test McSAS Optimization Result file",
            file_types="McSAS3 Optimization Result Files (*.nxs *.hdf5 *.h5)"
        )
        self.test_file_selector.fileSelected.connect(self.load_test_file)
        layout.addWidget(self.test_file_selector)

        # Test Button
        test_button = QPushButton("Test Histogramming")
        test_button.clicked.connect(self.test_histogramming)
        layout.addWidget(test_button)

        # Information Output
        self.info_field = QTextEdit()
        self.info_field.setReadOnly(True)
        layout.addWidget(QLabel("Test Output:"))
        layout.addWidget(self.info_field)

        self.setLayout(layout)

        # Automatically load the first configuration if available
        if self.config_dropdown.count() > 0:
            self.config_dropdown.setCurrentIndex(0)
            self.load_selected_default_config()

    def load_test_file(self, file_path:str):
        """Process the file after selection or drop."""
        if Path(file_path).exists():
            self.pdi = []   # clear any previous information
            logger.debug(f"File loaded: {file_path}")
            self.selected_file = file_path
            self.test_file_selector.set_file_path(self.selected_file)
        else:
            logger.warning(f"File does not exist: {file_path}")
            QMessageBox.warning(self, "File Error", f"Cannot access file: {file_path}")

    def refresh_config_dropdown(self, savedName:str|None = None): # args added to handle signal
        """Populate or refresh the histogramming configuration dropdown."""
        self.config_dropdown.clear()
        self.default_configs = get_default_config_files(directory= self.main_path / "hist_configurations")
        self.config_dropdown.addItems(self.default_configs)
        self.config_dropdown.addItem("<Custom...>")
        if savedName is not None: 
            listName = str(Path(savedName).name)
            if listName in self.default_configs: 
                self.config_dropdown.setCurrentText(listName)
            else:
                self.config_dropdown.setCurrentText("<Custom...>")
        else:
            self.config_dropdown.setCurrentText("<Custom...>")

    def handle_dropdown_change(self):
        """Handle dropdown changes and load the selected configuration."""
        selected_text = self.config_dropdown.currentText()
        if selected_text != "<Custom...>":
            self.load_selected_default_config()

    def load_selected_default_config(self):
        """Load the selected histogramming configuration YAML file into the editor."""
        selected_file = self.config_dropdown.currentText()
        if selected_file and selected_file != "<Custom...>":
            try:
                # Construct the full path to the selected file
                file_path = self.main_path / "hist_configurations" / selected_file
                if file_path.is_file():
                    with open(file_path, 'r') as file:
                        # Parse YAML content as structured data
                        yaml_content = list(yaml.safe_load_all(file))
                    # Pass parsed content to the YAML editor
                    # Temporarily disable the on_yaml_editor_change trigger
                    self._programmatic_change = True
                    self.yaml_editor_widget.set_yaml_content(yaml_content)
                    self._programmatic_change = False
                else:
                    logger.error(f"File not found: {file_path}")
                    QMessageBox.warning(self, "Error", f"File not found: {file_path}")
            except Exception as e:
                logger.error(f"Error loading histogramming configuration: {e}")
                QMessageBox.critical(self, "Error", f"Error loading histogramming configuration: {e}")

    def on_yaml_editor_change(self):
        """Mark the dropdown as <Custom...> if the YAML content is modified by the user."""
        if hasattr(self, "_programmatic_change") and self._programmatic_change:
            # Skip handling changes triggered programmatically
            return
        if self.config_dropdown.currentText() != "<Custom...>":
            self.config_dropdown.setCurrentText("<Custom...>")

    def test_histogramming(self):
        """Execute a histogramming test with the current settings and selected data file."""
        test_file = self.test_file_selector.get_file_path()

        try:
            if not test_file or not Path(test_file).exists():
                QMessageBox.warning(self, "Error", "Please select a valid test data file.")
                return

            yaml_content = self.yaml_editor_widget.get_yaml_content()
            if not yaml_content:
                QMessageBox.warning(self, "Error", "Please configure histogramming settings.")
                return

            # Store the yaml content in a temporary file
            yaml_file = Path(gettempdir()) / "hist_config_temp_ui.yaml"
            with open(yaml_file, 'w') as file:
                yaml.dump_all(yaml_content, file, default_flow_style=False)  # Use dump_all for multi-document YAML

            logger.debug("Launching histogramming test.")
            self.info_field.append("Launching histogramming test...")

            # Construct the command
            command = [
                "python", "-m", "mcsas3.mcsas3_cli_histogrammer",
                "-r", test_file,
                "-H", str(yaml_file),
                "-i", "1",
                # "-v", "-d"
            ]

            # Specify the working directory (replace 'desired_directory' with the actual path)
            working_directory = Path(".").resolve()  # Set the directory where the script exists

            # log the exectued command
            logger.debug(f"Executing command:\n{command}")

            # log the working directory
            logger.debug(f"Working directory is {working_directory}.")

            # Execute the command
            result = subprocess.run(
                command,
                cwd=working_directory,  # Run the command from the specified directory
                capture_output=True,    # Capture stdout and stderr
                text=True               # Decode output as text
            )

            # Handle the output
            if result.returncode == 0:
                self.info_field.append(f"Command executed successfully:\n{result.stdout}")
                logger.info(f"Command output:\n{result.stdout}")
            else:
                self.info_field.append(f"Command failed with error:\n{result.stderr}")
                logger.error(f"Command error:\n{result.stderr}")

            # Clean up the temporary file
            yaml_file.unlink()
            logger.debug("Temporary config file deleted.")
            logger.debug("Opening PDF")
            subprocess.Popen([f"open {Path(test_file).with_suffix('.pdf')}"],shell=True)

        except Exception as e:
            logger.error(f"Error during histogramming test: {e}")
            QMessageBox.critical(self, "Error", f"Error during histogramming test: {e}")
