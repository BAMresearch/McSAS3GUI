# src/gui/data_loading_tab.py

import logging
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import yaml
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QTextCursor, QTextOption  # Import QTextOption for word wrapping
from PyQt6.QtWidgets import QComboBox, QDialog, QLabel, QTextEdit, QVBoxLayout, QWidget

from ..utils.file_utils import get_default_config_files, get_main_path
from ..utils.yaml_utils import load_yaml_file
from .file_line_selection_widget import FileLineSelectionWidget
from .file_selection_helpers import load_existing_selector_file
from .mcsas3_bridge import prepare_processing_from_file, processing_frames_from_processing
from .yaml_editor_widget import YAMLEditorWidget

# from .drag_and_drop_mixin import DragAndDropMixin

logger = logging.getLogger("McSAS3")


class DataLoadingTab(QWidget):
    default_configs = []  # List to hold default configuration files

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot_dialog = None  # Track the plot dialog
        self.main_path = get_main_path()  # Get the main path of the application
        self.config_path = get_main_path() / "configurations/readdata"
        self.update_timer = QTimer(self)  # Timer for debouncing updates
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_and_plot)  # Trigger plot after delay
        self.pdi = []
        self.processing = None
        self.processing_frames = None
        self.selected_file = None

        layout = QVBoxLayout()

        # Dropdown for default configuration files
        self.config_dropdown = QComboBox()
        self.refresh_config_dropdown()
        layout.addWidget(QLabel("Select Default Configuration:"))
        layout.addWidget(self.config_dropdown)
        self.config_dropdown.currentTextChanged.connect(self.handle_dropdown_change)

        # YAML Editor for data loading configuration
        self.yaml_editor_widget = YAMLEditorWidget(directory=self.config_path, parent=self, multipart=False)
        layout.addWidget(QLabel("Data Loading Configuration (YAML):"))
        layout.addWidget(self.yaml_editor_widget)

        # Monitor changes in the YAML editor to detect custom changes
        self.yaml_editor_widget.yaml_editor.textChanged.connect(self.on_yaml_editor_change)
        self.yaml_editor_widget.fileSaved.connect(self.refresh_config_dropdown)  # Refresh dropdown after save

        # Reusable file selection widget
        self.file_line_selection_widget = FileLineSelectionWidget(
            placeholder_text="Select test data file", file_types="All Files (*.*)"
        )
        self.file_line_selection_widget.fileSelected.connect(self.load_file)  # Handle file selection

        layout.addWidget(self.file_line_selection_widget)

        # Error Message Display at the Bottom
        self.error_message_display = QTextEdit()
        self.error_message_display.setStyleSheet(
            """
            QTextEdit, QPlainTextEdit {
                background-color: palette(base);
                color: palette(text);
            }
            """
        )
        self.error_message_display.setReadOnly(True)  # Make the display non-editable
        self.error_message_display.setWordWrapMode(QTextOption.WrapMode.WordWrap)  # Enable word wrap
        self.error_message_display.setPlaceholderText("Messages will be displayed here.")
        # self.error_message_display.setStyleSheet("color: darkgreen;")  # Display messages in green
        layout.addWidget(self.error_message_display)

        self.setLayout(layout)
        logger.debug("DataLoadingTab initialized with auto-plotting and configuration management.")

        # Auto-load the first configuration if available
        if self.config_dropdown.count() > 0:
            self.config_dropdown.setCurrentIndex(0)
            self.load_selected_default_config()

    def close_auxiliary_windows(self) -> None:
        """Close any standalone plotting windows owned by this tab."""
        if self.plot_dialog is not None:
            self.plot_dialog.close()
            self.plot_dialog = None
        if hasattr(self, "fig") and self.fig is not None:
            plt.close(self.fig)
            self.fig = None
        if hasattr(self, "ax"):
            self.ax = None

    def display_error(self, message):
        """Display the error message in the logger and on the tab."""
        # Optionally truncate the message if needed
        # message = message if len(message) <= 200 else message[:200] + "..."
        self.error_message_display.setText(message)
        if len(self.pdi) > 0:
            self.error_message_display.append(
                f"Available datasets in file ({len(self.pdi)} found): \n" + "\n".join(self.pdi)
            )
        self.error_message_display.moveCursor(QTextCursor.MoveOperation.Start)
        logger.error(message)

    def refresh_config_dropdown(self, savedName: str | None = None):  # optional args to match signal signature
        """Populate or refresh the configuration dropdown list."""
        self.config_dropdown.clear()
        self.default_configs = get_default_config_files(directory=self.config_path)
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
            self.config_dropdown.blockSignals(True)
            self.config_dropdown.setCurrentText(selected_text)
            self.config_dropdown.blockSignals(False)

    def load_selected_default_config(self):
        """Load the selected YAML configuration file into the YAML editor."""
        selected_file = self.config_dropdown.currentText()
        if selected_file and selected_file != "<Custom...>":
            yaml_content = load_yaml_file(self.config_path / f"{selected_file}")
            self.yaml_editor_widget.set_yaml_content(yaml_content)

    def on_yaml_editor_change(self):
        """Mark the dropdown as <Custom...> if the YAML content is modified and debounce updates."""
        if self.config_dropdown.currentText() != "<Custom...>":
            self.config_dropdown.setCurrentText("<Custom...>")

        # Start/restart the debounce timer to delay plot update
        self.update_timer.start(400)  # Wait 400 ms before updating plot

    def load_file(self, file_path: str):
        """Process the file after selection or drop."""

        def on_loaded(path: Path) -> None:
            self.pdi = []
            self.selected_file = str(path)
            if path.suffix.lower() in {".hdf5", ".h5", ".nxs"}:
                self.list_hdf5_paths_and_dimensions(str(path))
            self.update_and_plot()

        load_existing_selector_file(
            self,
            self.file_line_selection_widget,
            file_path,
            on_loaded=on_loaded,
        )

    def list_hdf5_paths_and_dimensions(self, file_name: str) -> None:
        """List paths and dimensions of datasets in an HDF5/Nexus file."""
        self.error_message_display.clear()
        try:
            self.pdi = []
            with h5py.File(file_name, "r") as hdf:

                def _log_and_display_attrs(name: str, obj: h5py.HLObject) -> None:
                    if isinstance(obj, h5py.Dataset):
                        path_dim_info = f"Path: {name}, Shape: {obj.shape}"
                        self.pdi += [path_dim_info]
                        self.error_message_display.append(path_dim_info)
                        logger.debug(path_dim_info)

                hdf.visititems(_log_and_display_attrs)
            # self.error_message_display.setText(f"Available datasets in file: \n {self.pdi}")
            logger.debug(f"{self.pdi=}")
        except Exception as e:
            error_message = f"Error reading HDF5 file: {e}. Verify the file structure."
            logger.error(error_message)
            self.error_message_display.append(f"Error: {error_message}")

    def update_and_plot(self):
        """Load and plot the data file using the current YAML configuration."""
        # Clear any previous error message
        if len(self.pdi) > 0:
            self.error_message_display.setText(
                f"Available datasets in file ({len(self.pdi)} found): \n" + "\n".join(self.pdi)
            )
        else:
            self.error_message_display.setText("")

        file_path = self.file_line_selection_widget.get_file_path()  # self.file_path_line.text()
        if not file_path:
            self.clear_plot()
            return

        # Parse the YAML configuration from the editor
        try:
            yaml_content = self.yaml_editor_widget.yaml_editor.toPlainText()
            yaml_config = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            self.display_error(f"YAML Error: {e}")
            self.clear_plot()
            return

        # Load data and update the plot
        try:
            self.processing = prepare_processing_from_file(Path(file_path), yaml_config)
            self.processing_frames = processing_frames_from_processing(self.processing)
            logger.debug(f"Loaded data file: {file_path}")
            self.show_plot_popup()  # Display the plot in a popup window
        except Exception as e:
            self.processing = None
            self.processing_frames = None
            self.display_error(f"Error loading file {file_path}: {e}")
            self.clear_plot()

    def clear_plot(self):
        """Clear the plot when no valid data is available."""
        if self.plot_dialog and self.plot_dialog.isVisible():
            self.ax.clear()
            self.ax.figure.canvas.draw()

    def show_plot_popup(self, frames=None):
        """Display a popup window with the loaded data plot."""
        if frames is None:
            frames = self.processing_frames
        if frames is None:
            raise ValueError("No processed data is available for plotting.")
        # If a plot window is already open, update it
        if self.plot_dialog is None or not self.plot_dialog.isVisible():
            self.plot_dialog = QDialog()  # self removed to avoid constant placement on top of main
            self.plot_dialog.setWindowTitle("Data Plot")
            self.plot_dialog.setMinimumSize(700, 500)
            layout = QVBoxLayout(self.plot_dialog)

            # Create the matplotlib figure and axes
            self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
            canvas = FigureCanvas(self.fig)
            layout.addWidget(canvas)

            # Embed the canvas in the dialog layout
            self.plot_dialog.setLayout(layout)
            self.plot_dialog.show()

        # Clear the previous plot and redraw
        self.ax.clear()  # how to maintain position?
        title_name = Path(self.selected_file).name if self.selected_file else "selected data"
        self.plot_dialog.setWindowTitle(f"Data Plot for {title_name}")
        frames.raw.plot("Q", "I", yerr="ISigma", ax=self.ax, label="As provided data")
        frames.clipped.plot(
            "Q",
            "I",
            yerr="ISigma",
            linestyle=None,
            linewidth=0,
            marker=".",
            ax=self.ax,
            label="Clipped data",
        )
        frames.binned.plot(
            x="Q",
            y="I",
            yerr="ISigma",
            linestyle="",
            marker=".",
            ax=self.ax,
            label="Binned data",
            capsize=1,  # Optionally, add capsize for the error bars
            elinewidth=1,  # Set error bar line width if needed
        )
        self.ax.set_yscale("log")
        self.ax.set_xscale("log")
        self.ax.set_xlabel("Q (1/nm)")
        self.ax.set_ylabel("I (1/(m sr))")

        # Add vertical dashed lines for the clipped data boundaries
        if not frames.clipped.empty:
            xmin = frames.clipped["Q"].min()
            xmax = frames.clipped["Q"].max()
            self.ax.axvline(x=xmin, color="red", linestyle=":", label="Clipped boundary min")
            self.ax.axvline(x=xmax, color="red", linestyle=":", label="Clipped boundary max")

        self.ax.legend()
        self.fig.canvas.draw()
        return self.ax  # for those that need it.
