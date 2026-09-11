import logging
import re
from pathlib import Path
from typing import Sequence

from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QComboBox, QDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget
from sasmodels.core import load_model_info

from ..utils.file_utils import get_default_config_files, get_main_path
from ..utils.yaml_utils import load_yaml_file
from .optimization_worker import PreviewOptimizationWorker
from .run_control_helpers import set_abortable_button_state, worker_is_running
from .run_settings_helpers import (
    cleanup_preview_result_file,
    combine_run_configuration_documents,
    format_preview_progress_message,
    format_preview_status_header,
    plot_preview_fit_curves,
    preview_result_file_path,
)
from .yaml_editor_widget import YAMLEditorWidget

logger = logging.getLogger("McSAS3")


class RunSettingsTab(QWidget):
    """Tab for configuring run settings, including YAML editor and test optimization."""

    default_configs = []  # List to hold default configuration files
    _temp_dir = None  # provided by __main__

    def __init__(self, parent=None, data_loading_tab=None, temp_dir: Path = None):
        super().__init__(parent)
        if temp_dir is None or not temp_dir.is_dir():
            raise FileNotFoundError(f"Given temp dir '{temp_dir}' does not exist!")
        self._temp_dir = temp_dir
        self.data_loading_tab = data_loading_tab
        self.config_path = get_main_path() / "configurations/run"
        self.update_timer = QTimer(self)  # Timer for debouncing updates
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_info_field)
        self.preview_worker: PreviewOptimizationWorker | None = None
        self.preview_result_file = preview_result_file_path(self._temp_dir)
        self._preview_run_config: dict | None = None

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
        self.yaml_editor_widget.fileSaved.connect(self.refresh_config_dropdown)  # Refresh dropdown after save

        # Test Run Button
        self.test_run_button = QPushButton("Test single repetition on loaded Test Data")
        self._default_test_run_button_style = self.test_run_button.styleSheet()
        self.test_run_button.clicked.connect(self.handle_test_run_button_clicked)
        layout.addWidget(self.test_run_button)

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

    def close_auxiliary_windows(self) -> None:
        """Close any standalone preview/plot windows owned by this tab."""
        if hasattr(self, "metrics_dialog") and self.metrics_dialog is not None:
            self.metrics_dialog.close()
            self.metrics_dialog = None
        if hasattr(self, "metrics_fig") and self.metrics_fig is not None:
            plt.close(self.metrics_fig)
            self.metrics_fig = None
        if hasattr(self, "metrics_ax"):
            self.metrics_ax = None

    def refresh_config_dropdown(self, savedName: str | None = None):  # args is a dummy argument to handle signals
        """Populate or refresh the configuration dropdown list."""
        self.config_dropdown.blockSignals(True)
        try:
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
        finally:
            self.config_dropdown.blockSignals(False)

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
            fit_porod_background = document.get("fitPorodBackground", False)
            info_text += f"  Max Iterations: {max_iter}\n"
            info_text += f"  Convergence Criterion: {conv_crit}\n"
            info_text += f"  Cores: {n_cores}\n"
            info_text += f"  Fit non-negative q^-4 background: {fit_porod_background}\n"

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
                    The run configuration must define the scaling factor and simulated arrays: \n
                    fitParameterLimits:
                        factor: [1, 80] # scaling factor for the model data to try in McSAS3
                            optimization
                    staticParameters:
                        # Optional high-Q extrapolation override. If omitted, extrapY0 is zero
                        # and extrapScaling is estimated from finite high-Q data at positive Q.
                        extrapY0: e.g. 0.0
                        extrapScaling: e.g. 95.5
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

    def handle_test_run_button_clicked(self):
        if worker_is_running(self.preview_worker):
            self.request_preview_stop()
            return
        self.run_test_optimization()

    def _set_test_run_button_running_state(self, is_running: bool) -> None:
        set_abortable_button_state(
            self.test_run_button,
            is_running=is_running,
            default_text="Test single repetition on loaded Test Data",
            default_style=self._default_test_run_button_style,
        )

    def _combined_yaml_content(self):
        return combine_run_configuration_documents(self.yaml_editor_widget.get_yaml_content())

    def request_preview_stop(self):
        if not worker_is_running(self.preview_worker):
            return
        logger.info("Abort requested from run settings preview button.")
        self.preview_worker.request_stop()

    def _loaded_processing(self):
        processing = self.data_loading_tab.processing
        if processing is None:
            self.info_field.setPlainText("No data loaded in the Data Loading tab.")
            return None
        return processing

    def _run_configuration(self):
        run_config = self._combined_yaml_content()
        if not run_config:
            self.info_field.setPlainText("Invalid or missing run configuration.")
            return None
        return run_config

    def _start_preview_worker(self, processing, run_config) -> None:
        cleanup_preview_result_file(self.preview_result_file)
        logger.debug("Temporary HDF5 file created at: %s", self.preview_result_file)
        self._preview_run_config = dict(run_config)
        self.preview_worker = PreviewOptimizationWorker(
            processing=processing,
            result_file=self.preview_result_file,
            run_config=run_config,
            result_index=1,
        )
        self.preview_worker.progress_text_signal.connect(self._on_preview_progress)
        self.preview_worker.preview_ready_signal.connect(self._on_preview_ready)
        self.preview_worker.finished_signal.connect(self._on_preview_finished)
        self.preview_worker.finished.connect(self._on_preview_thread_finished)
        self._set_test_run_button_running_state(True)
        self.info_field.setPlainText(format_preview_status_header(run_config))
        self.preview_worker.start()

    def run_test_optimization(self):
        """Run a single optimization repetition on the loaded test data."""
        try:
            processing = self._loaded_processing()
            if processing is None:
                return

            run_config = self._run_configuration()
            if run_config is None:
                return

            self._start_preview_worker(processing, run_config)

        except Exception as e:
            logger.error(f"Error during test optimization: {e}")
            self.info_field.setPlainText(f"Error during test optimization: {e}")

    def _on_preview_ready(self, preview) -> None:
        self._plot_fit(
            fit_q=preview.fit_q,
            fitted_intensity=preview.fitted_curve,
            background_intensity=preview.background_curve,
            accepted_gofs=preview.accepted_gofs,
            accepted_steps=preview.accepted_steps,
            max_iter=preview.max_iter,
            max_accept=preview.max_accept,
        )

    def _on_preview_finished(self, stopped: bool, message: str) -> None:
        self._set_test_run_button_running_state(False)
        self.info_field.append(message)

    def _on_preview_thread_finished(self) -> None:
        """Release preview resources only after ``QThread.run()`` has returned."""

        worker = self.preview_worker
        self.preview_worker = None
        self._preview_run_config = None
        cleanup_preview_result_file(self.preview_result_file)
        if worker is not None:
            worker.deleteLater()

    def _on_preview_progress(self, message: str) -> None:
        if not message:
            return
        formatted_message = format_preview_progress_message(
            message,
            run_config=self._preview_run_config,
        )
        self.info_field.append(formatted_message)

    def _plot_fit(
        self,
        fit_q: Sequence[float],
        fitted_intensity: Sequence[float],
        background_intensity: Sequence[float],
        accepted_gofs: Sequence[float],
        accepted_steps: Sequence[int],
        max_iter: int,
        max_accept: int,
    ) -> None:
        """
        Plot the fit results in the existing data plot or reopen it if not open,
        and create a new plot for optimization metrics.

        Args:
            fit_q (array-like): Q values of the fit.
            fitted_intensity (array-like): Complete fitted intensity values.
            background_intensity (array-like): Fitted flat plus optional Porod background.
            accepted_gofs (array-like): Accepted goodness-of-fit values.
            accepted_steps (array-like): Steps where fits were accepted.
            max_iter (int): Maximum iteration setting.
            max_accept (int): Maximum accept setting.
        """
        try:
            # Retrieve the data plot from the DataLoadingTab
            data_tab = self.data_loading_tab

            ax = data_tab.show_plot_popup()

            # Plot the fit on the existing data plot with zorder for proper layering
            plot_preview_fit_curves(
                ax,
                fit_q,
                fitted_intensity,
                background_intensity,
            )
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
                self.metrics_dialog = QDialog()  # do not use self or it'll end up on the main window
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
