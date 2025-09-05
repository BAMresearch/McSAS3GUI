import logging
import re
from pathlib import Path
from typing import Sequence

import h5py
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from mcsas3.mc_hat import McHat
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QComboBox, QDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget
from sasmodels.core import load_model_info

from ..utils.file_utils import get_default_config_files, get_main_path
from ..utils.yaml_utils import load_yaml_file
from .yaml_editor_widget import YAMLEditorWidget

logger = logging.getLogger("McSAS3")


class RunSettingsTab(QWidget):
    """Tab for configuring run settings, including YAML editor and test optimization."""

    default_configs = []  # List to hold default configuration files
    _temp_dir = None  # provided by __main__

    def __init__(self, parent=None, data_loading_tab=None, temp_dir: Path = None):
        super().__init__(parent)
        assert temp_dir.is_dir(), f"Given temp dir '{temp_dir}' does not exist!"
        self._temp_dir = temp_dir
        self.data_loading_tab = data_loading_tab
        self.config_path = get_main_path() / "configurations/run"
        self.update_timer = QTimer(self)  # Timer for debouncing updates
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_info_field)

        layout = QVBoxLayout()

        # Dropdown for default run configuration files
        self.config_dropdown = QComboBox()

        self.refresh_config_dropdown()
        layout.addWidget(QLabel("Select Default Run Configuration:"))
        layout.addWidget(self.config_dropdown)
        self.config_dropdown.currentTextChanged.connect(self.handle_dropdown_change)

        # YAML Editor for run settings configuration
        self.yaml_editor_widget = YAMLEditorWidget(self.config_path, parent=self, multipart=False)
        layout.addWidget(QLabel("Run Configuration (YAML):"))
        layout.addWidget(self.yaml_editor_widget)

        # Monitor changes in the YAML editor to detect custom changes
        self.yaml_editor_widget.yaml_editor.textChanged.connect(self.on_yaml_editor_change)
        self.yaml_editor_widget.fileSaved.connect(
            self.refresh_config_dropdown
        )  # Refresh dropdown after save

        # Test Run Button
        test_run_button = QPushButton("Test single repetition on loaded Test Data")
        test_run_button.clicked.connect(self.run_test_optimization)
        layout.addWidget(test_run_button)

        # Info text field for model parameters
        self.info_field = QTextEdit()
        self.info_field.setStyleSheet(
            """
            QTextEdit, QPlainTextEdit {
                background-color: palette(base);
                color: palette(text);
            }
            """
        )
        self.info_field.setReadOnly(True)
        layout.addWidget(QLabel("Model Parameters Info:"))
        layout.addWidget(self.info_field)

        self.setLayout(layout)
        if self.config_dropdown.count() > 0:
            self.config_dropdown.setCurrentIndex(0)
            self.load_selected_default_config()

    def refresh_config_dropdown(
        self, savedName: str | None = None
    ):  # args is a dummy argument to handle signals
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
            self.update_info_field()

    def on_yaml_editor_change(self):
        """Mark the dropdown as <Custom...> if the YAML content is modified and debounce updates."""
        if self.config_dropdown.currentText() != "<Custom...>":
            self.config_dropdown.setCurrentText("<Custom...>")
        self.update_timer.start(400)  # Debounce updates with a 400 ms delay

    def update_info_field(self):
        """Update the info field based on the YAML content in the editor."""
        yaml_content = self.yaml_editor_widget.get_yaml_content()

        if not yaml_content:
            self.info_field.setPlainText("Invalid YAML or empty configuration.")
            return

        if not isinstance(yaml_content, list):
            yaml_content = [yaml_content]  # Ensure we always process as a list

        info_text = "Configuration Details:\n"

        for idx, document in enumerate(yaml_content):
            if not isinstance(document, dict):
                info_text += f"\nDocument {idx + 1}: Not a valid configuration.\n"
                continue

            info_text += f"\nDocument {idx + 1}: \n"

            model_name = document.get("modelName", "Unknown Model")
            info_text += f"  Model Name: {model_name}\n"

            max_iter = document.get("maxIter", "Not specified")
            conv_crit = document.get("convCrit", "Not specified")
            n_cores = document.get("nCores", "Not specified")
            info_text += f"  Max Iterations: {max_iter}\n"
            info_text += f"  Convergence Criterion: {conv_crit}\n"
            info_text += f"  Cores: {n_cores}\n"

            # do nothing if the model name is empty (None):
            if not model_name:
                info_text += "  Model Name is empty. No parameters available.\n"
                continue

            if model_name.startswith("mcsas_"):
                info_text += "  Using internal McSAS model. No additional parameters available.\n"
                continue
            if model_name.startswith("sim"):
                info_text += """
                    Using model based on simulated data. \n
                    The following additional parameters must be defined in the run configuration: \n
                    fitParameterLimits:
                        factor: [1, 80] # scaling factor for the model data to try in McSAS3
                            optimization
                    staticParameters:
                        extrapY0: e.g. 9.33e-11, porod slope extrapolation of the model according
                            to extrapY0 + Q ** (-4) * extrapScaling
                        extrapScaling: e.g. 95.5, porod slope extrapolation of the model according
                            to extrapY0 + Q ** (-4) * extrapScaling
                        simDataQ1: null # intended for 2D simulated model data
                        simDataQ0: [list of Q values]
                        simDataI: [list of I values]
                        simDataISigma: [list of I uncertainties (=1 standard deviation)]
                    """
                continue
            try:
                model_info = load_model_info(model_name)
                model_parameters = model_info.parameters.defaults.copy()
                exclude_patterns = [r"up_.*", r".*_M0", r".*_mtheta", r".*_mphi"]
                filtered_parameters = {
                    param: default_value
                    for param, default_value in model_parameters.items()
                    if not any(re.match(pattern, param) for pattern in exclude_patterns)
                }

                info_text += "  Sasmodels Parameters: \n"
                for param, default_value in filtered_parameters.items():
                    info_text += f"    - {param}: {default_value}\n"  # noqa: E221

                info_text += (
                    "  To configure parameters, add each to 'fitParameterLimits'"
                    " or 'staticParameters' in the YAML editor.\n"
                )
                info_text += "  For 'fitParameterLimits', specify lower and upper limits as a list."
            except Exception as e:
                info_text += f"  Error loading model parameters: {e}\n"
                logger.error(f"Error loading model parameters: {e}")

        self.info_field.setPlainText(info_text)

    def run_test_optimization(self):
        """Run a single optimization repetition on the loaded test data."""
        try:
            # Retrieve data from the DataLoadingTab
            mds = self.data_loading_tab.mds
            if not mds:
                self.info_field.setPlainText("No data loaded in the Data Loading tab.")
                return

            # Parse the YAML configuration for the optimizer
            yaml_content = self.yaml_editor_widget.get_yaml_content()
            if not yaml_content:
                self.info_field.setPlainText("Invalid or missing run configuration.")
                return

            # Ensure YAML content is a dictionary for the optimizer
            if isinstance(yaml_content, list):
                # Combine all documents into a single dictionary, overriding keys if repeated
                combined_yaml_content = {}
                for doc in yaml_content:
                    if not isinstance(doc, dict):
                        self.info_field.setPlainText(
                            "One or more YAML documents are not valid configurations."
                        )
                        return
                    combined_yaml_content.update(doc)
                yaml_content = combined_yaml_content

            # Create a temporary file to save data for the optimizer
            temp_file = self._temp_dir / "test_data.hdf5"
            self.tempFileName = Path(temp_file.name)
            logger.debug(f"Temporary HDF5 file created at: {self.tempFileName}")

            mds.store(self.tempFileName)
            yaml_content.update({"nRep": 1})  # Update configuration for single repetition

            mh = McHat(**yaml_content)
            mh.run(mds.measData.copy(), self.tempFileName)

            self.info_field.setPlainText("Optimization completed successfully.")

            with h5py.File(self.tempFileName, "r") as h5f:
                fitQ = h5f["/analyses/MCResult1/mcdata/measData/Q"][()].flatten()  # model Q
                fitI = h5f["/analyses/MCResult1/optimization/repetition0/modelI"][
                    ()
                ]  # model intensity
                acceptedGofs = h5f["/analyses/MCResult1/optimization/repetition0/acceptedGofs"][
                    ()
                ]  # list of GOFs
                acceptedSteps = h5f["/analyses/MCResult1/optimization/repetition0/acceptedSteps"][
                    ()
                ]  # steps accepted
                maxIter = h5f["/analyses/MCResult1/optimization/repetition0/maxIter"][
                    ()
                ]  # max iterations
                maxAccept = h5f["/analyses/MCResult1/optimization/repetition0/maxAccept"][
                    ()
                ]  # max accepts
                x0 = h5f["/analyses/MCResult1/optimization/repetition0/x0"][
                    ()
                ]  # scaling and background

            self._plot_fit(
                fit_q=fitQ,
                fit_intensity=fitI,
                accepted_gofs=acceptedGofs,
                accepted_steps=acceptedSteps,
                max_iter=maxIter,
                max_accept=maxAccept,
                x0=x0,
            )

            # Clean up the temporary file
            self.tempFileName.unlink()

        except Exception as e:
            logger.error(f"Error during test optimization: {e}")
            self.info_field.setPlainText(f"Error during test optimization: {e}")

    def _plot_fit(
        self,
        fit_q: Sequence[float],
        fit_intensity: Sequence[float],
        accepted_gofs: Sequence[float],
        accepted_steps: Sequence[int],
        max_iter: int,
        max_accept: int,
        x0: Sequence[float],
    ) -> None:
        """
        Plot the fit results in the existing data plot or reopen it if not open,
        and create a new plot for optimization metrics.

        Args:
            fit_q (array-like): Q values of the fit.
            fit_intensity (array-like): Intensity values of the fit.
            accepted_gofs (array-like): Accepted goodness-of-fit values.
            accepted_steps (array-like): Steps where fits were accepted.
            max_iter (int): Maximum iteration setting.
            max_accept (int): Maximum accept setting.
            x0 (array-like): Scaling and background [scale, background].
        """
        try:
            # Retrieve the data plot from the DataLoadingTab
            data_tab = self.data_loading_tab

            ax = data_tab.show_plot_popup(self.data_loading_tab.mds)

            # Plot the fit on the existing data plot with zorder for proper layering
            scaled_fit_intensity = x0[0] * fit_intensity + x0[1]
            ax.plot(fit_q, scaled_fit_intensity, "r--", label="Test McSAS3 Optimization", zorder=10)
            ax.legend()
            data_tab.fig.canvas.draw()

            # Plot optimization metrics in a new figure
            self._plot_optimization_metrics(accepted_gofs, accepted_steps, max_iter, max_accept)

        except Exception as e:
            logger.error(f"Error plotting fit results: {e}")
            self.info_field.append(f"Error plotting fit results: {e}")

    def _plot_optimization_metrics(self, accepted_gofs, accepted_steps, max_iter, max_accept):
        """
        Plot the optimization metrics:
            accepted goodness-of-fit values vs. accepted steps in a QDialog.

        Args:
            accepted_gofs (array-like): Accepted goodness-of-fit values.
            accepted_steps (array-like): Steps where fits were accepted.
            max_iter (int): Maximum number of iterations.
            max_accept (int): Maximum number of accepted steps.
        """
        try:
            # Check if the optimization metrics dialog is open, create it if necessary
            if (
                not hasattr(self, "metrics_dialog")
                or self.metrics_dialog is None
                or not self.metrics_dialog.isVisible()
            ):
                self.metrics_dialog = (
                    QDialog()
                )  # do not use self or it'll end up on the main window
                self.metrics_dialog.setWindowTitle("Optimization Metrics")
                self.metrics_dialog.setMinimumSize(700, 500)
                layout = QVBoxLayout(self.metrics_dialog)

                # Create the matplotlib figure and axes
                self.metrics_fig, self.metrics_ax = plt.subplots(figsize=(6, 4), dpi=100)
                canvas = FigureCanvas(self.metrics_fig)
                layout.addWidget(canvas)

                # Embed the canvas in the dialog layout
                self.metrics_dialog.setLayout(layout)
                # Show the dialog
                self.metrics_dialog.show()

            # Clear the previous plot and redraw
            self.metrics_ax.clear()
            self.metrics_ax.plot(accepted_steps, accepted_gofs, "bo-", label="Accepted GOFs")
            self.metrics_ax.set_xscale("linear")
            self.metrics_ax.set_yscale("log")
            self.metrics_ax.set_xlabel("Total Attempts")
            self.metrics_ax.set_ylabel("Goodness of Fit (GOF)")
            self.metrics_ax.set_title("Optimization Metrics")

            # Display maxIter and maxAccept as annotations
            self.metrics_ax.text(
                0.95,
                0.75,
                f"Max Iter: {max_iter}\nMax Accept: {max_accept}",
                transform=self.metrics_ax.transAxes,
                fontsize=10,
                verticalalignment="bottom",
                horizontalalignment="right",
                bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"),
            )

            self.metrics_ax.legend()
            self.metrics_fig.tight_layout()
            self.metrics_fig.canvas.draw()

        except Exception as e:
            logger.error(f"Error plotting optimization metrics: {e}")
            self.info_field.append(f"Error plotting optimization metrics: {e}")
