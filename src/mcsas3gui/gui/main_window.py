# main_window.py

# import inspect
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from .data_loading_tab import DataLoadingTab
from .getting_started_tab import GettingStartedTab
from .hist_run_tab import HistRunTab
from .hist_settings_tab import HistogramSettingsTab
from .optimization_tab import OptimizationRunTab
from .run_settings_tab import RunSettingsTab  # Import the new RunSettingsTab


class McSAS3MainWindow(QMainWindow):
    """Main window for the McSAS3 GUI application, containing all tabs."""

    # use inspect to find main path for this package

    def __init__(self, temp_dir: Path):
        super().__init__()
        self.setWindowTitle("McSAS3 Configuration Interface")
        self.setGeometry(100, 100, 800, 600)

        # Main tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Initialize and add tabs
        self.setup_tabs(temp_dir)

    def setup_tabs(self, temp_dir: Path):
        GSTab = GettingStartedTab(self, temp_dir=temp_dir)
        DLTab = DataLoadingTab(self)
        RSTab = RunSettingsTab(self, DLTab, temp_dir=temp_dir)
        HSTab = HistogramSettingsTab(self)
        HRTab = HistRunTab(self, HSTab, temp_dir=temp_dir)
        ORTab = OptimizationRunTab(self, DLTab, RSTab, HSTab, HRTab, temp_dir=temp_dir)
        self.tabs.addTab(GSTab, "Getting Started")
        self.tabs.addTab(DLTab, "Data Settings")
        self.tabs.addTab(RSTab, "Run Settings")
        self.tabs.addTab(ORTab, "McSAS3 Optimization ...")
        self.tabs.addTab(HSTab, "Histogram Settings")
        self.tabs.addTab(HRTab, "(Re-)Histogramming ...")

        # connect the tabs to the getting started tab:
        GSTab.data_loading_tab = DLTab
        GSTab.run_settings_tab = RSTab
        GSTab.optimization_tab = ORTab
        GSTab.hist_settings_tab = HSTab
        GSTab.histogramming_tab = HRTab
        # re-trigger the dropdowns in the getting started tab
        GSTab.refresh_config_dropdown(savedName="getting_started.yaml")

        # make some signal connections we can't seem to do anywhere else:
        # when a histogram file is saved in the hist settings tab,
        # set this to the current file in the hist run tab
        HSTab.yaml_editor_widget.fileSaved.connect(HRTab.histogram_config_selector.set_file_path)
        # when a data load settigns file is saved in the data settings tab,
        # set this to the current file in the optimization run tab
        DLTab.yaml_editor_widget.fileSaved.connect(ORTab.data_config_selector.set_file_path)  # Handle file save
        RSTab.yaml_editor_widget.fileSaved.connect(ORTab.run_config_selector.set_file_path)  # Handle file save
