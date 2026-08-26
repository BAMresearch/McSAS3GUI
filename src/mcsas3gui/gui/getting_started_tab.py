import logging
from pathlib import Path

import yaml
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QComboBox, QLabel, QTextBrowser, QVBoxLayout, QWidget

from mcsas3gui.utils.file_utils import get_default_config_files, get_main_path
from mcsas3gui.utils.yaml_utils import load_yaml_file

from .yaml_editor_widget import CustomDumper

CustomDumper.add_representer(dict, CustomDumper.represent_dict)
CustomDumper.add_representer(list, CustomDumper.represent_list)
logger = logging.getLogger("McSAS3")


def write_yaml_file(data: object, filepath: Path) -> None:
    """Write a single YAML document to disk using the GUI dumper."""

    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(data, f, Dumper=CustomDumper, default_flow_style=None, sort_keys=False)


def write_hist_yaml_block(hist_configs: object, filepath: Path) -> None:
    """Write one or more histogram YAML documents to disk."""

    with open(filepath, "w", encoding="utf-8") as f:
        if isinstance(hist_configs, list):
            if len(hist_configs) == 1:
                yaml.dump(
                    hist_configs[0],
                    f,
                    Dumper=CustomDumper,
                    default_flow_style=None,
                    sort_keys=False,
                )
            else:
                for i, block in enumerate(hist_configs):
                    # if i > 0:
                    f.write("---\n")
                    yaml.dump(block, f, Dumper=CustomDumper, default_flow_style=None, sort_keys=False)
        else:
            # fallback for single dict passed instead of a list
            yaml.dump(hist_configs, f, Dumper=CustomDumper, default_flow_style=None, sort_keys=False)


class GettingStartedTab(QWidget):
    _temp_dir = None  # stores sub-configurations extracted from prefab config files

    def __init__(
        self,
        parent=None,
        data_loading_tab=None,
        run_settings_tab=None,
        optimization_tab=None,
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
        self.optimization_tab = optimization_tab
        self.hist_settings_tab = hist_settings_tab
        self.histogramming_tab = histogramming_tab
        layout = QVBoxLayout()

        # self.data_loading_tab = data_loading_tab
        self.main_path = get_main_path()  # Get the main path
        self.config_path = self.main_path / "configurations/prefab"
        self.update_timer = QTimer(self)  # Timer for debouncing updates
        self.update_timer.setSingleShot(True)
        # self.update_timer.timeout.connect(self.update_info_field)

        # Dropdown for default run configuration files
        self.config_dropdown = QComboBox()

        self.refresh_config_dropdown()
        layout.addWidget(QLabel("Select prefab template:"))
        layout.addWidget(self.config_dropdown)
        self.config_dropdown.currentIndexChanged.connect(self.handle_dropdown_change)

        self.info_viewer = QTextBrowser()
        self.info_viewer.setOpenExternalLinks(True)
        self.info_viewer.setStyleSheet(
            """
            QTextBrowser {
                background-color: palette(base);
                color: palette(text);
                border: 1px solid #ccc;
                padding: 8px;
            }
            """
        )

        # Load HTML content
        html_content = "<h1>Welcome to McSAS3</h1> - select a template from the dropdown menu above to start exploring!"
        self.info_viewer.setHtml(html_content)

        layout.addWidget(self.info_viewer)

        self.setLayout(layout)

        if self.config_dropdown.count() > 0:
            # self.config_dropdown.setCurrentIndex(0)
            self.load_selected_default_config()

    def apply_yaml_to_tab_pulldown(self, tab, config_path_rel_str: str):
        """Generic helper to load YAML into a settings tab."""
        config_path_rel = Path(config_path_rel_str)
        list_name = config_path_rel.name

        if list_name in tab.default_configs:
            tab.config_dropdown.setCurrentText(list_name)
        else:
            tab.config_dropdown.setCurrentText("<Custom...>")
            try:
                yaml_content = load_yaml_file(self.main_path / config_path_rel)
                tab.yaml_editor_widget.set_yaml_content(yaml_content)
            except Exception as e:
                logger.warning("Failed to load YAML content for %s: %s", list_name, e)

    def refresh_config_dropdown(
        self, savedName: str | None = "getting_started.yaml"
    ):  # args is a dummy argument to handle signals
        """Populate or refresh the configuration dropdown list."""
        self.config_dropdown.clear()
        default_configs = get_default_config_files(directory=self.config_path)
        # sort entries alphabetically, but make sure "getting_started.yaml" is always first
        if savedName and savedName in default_configs:
            default_configs.remove(savedName)
        default_configs.sort()
        if savedName:
            default_configs.insert(0, savedName)

        self.config_dropdown.addItems(default_configs)
        self.config_dropdown.setCurrentText(savedName)  # Set a default selection

    def load_template(self, template_path: Path) -> dict:
        """
        Load a project template (contained in a YAML structure)
        and generate temp files if inline configurations exist.

        Returns the full parsed dictionary so GUI can populate HTML, files, etc.
        """

        read_config_path = self._temp_dir / "data.yaml"
        run_config_path = self._temp_dir / "run.yaml"
        hist_config_path = self._temp_dir / "hist.yaml"

        with open(template_path, "r", encoding="utf-8") as f:
            template = yaml.safe_load(f)

        if "configurations" not in template:
            template["configurations"] = {}

        # Save inline configs to temp files if present
        if "read_configuration" in template:
            write_yaml_file(template["read_configuration"], read_config_path)
            # update read configuration file to point at the temp file

            template["configurations"]["read_configuration_file"] = str(read_config_path)

        if "run_configuration" in template:
            write_yaml_file(template["run_configuration"], run_config_path)
            # update run configuration file to point at the temp file
            template["configurations"]["run_configuration_file"] = str(run_config_path)

        if "hist_configuration" in template:
            hist_config = template["hist_configuration"]
            if isinstance(hist_config, list):
                write_hist_yaml_block(hist_config, hist_config_path)
            else:
                logger.warning("'hist_configuration' must be a list of dicts.")
            # update hist configuration file to point at the temp file
            template["configurations"]["hist_configuration_file"] = str(hist_config_path)

        return template  # can be passed to GUI components

    def load_selected_default_config(self):
        """Load the selected YAML configuration file."""

        selected_file = self.config_dropdown.currentText()
        if selected_file:
            try:
                yaml_content = self.load_template(self.config_path / selected_file)
                self.info_viewer.setHtml(yaml_content.get("html_description", "<p>No description available.</p>"))

                # Apply data reading settings
                file_dict = yaml_content.get("configurations", {})
                if self.data_loading_tab and "read_configuration_file" in file_dict:
                    self.apply_yaml_to_tab_pulldown(self.data_loading_tab, file_dict["read_configuration_file"])
                    self.optimization_tab.data_config_selector.set_file_path(
                        str((self.main_path / file_dict["read_configuration_file"]).as_posix())
                    )

                # Apply run settings
                if self.run_settings_tab and "run_configuration_file" in file_dict:
                    self.apply_yaml_to_tab_pulldown(self.run_settings_tab, file_dict["run_configuration_file"])
                    self.optimization_tab.run_config_selector.set_file_path(
                        str((self.main_path / file_dict["run_configuration_file"]).as_posix())
                    )

                # Apply hist settings
                if self.hist_settings_tab and "hist_configuration_file" in file_dict:
                    self.apply_yaml_to_tab_pulldown(self.hist_settings_tab, file_dict["hist_configuration_file"])
                    self.histogramming_tab.histogram_config_selector.set_file_path(
                        str((self.main_path / file_dict["hist_configuration_file"]).as_posix())
                    )

                # set data files for the tabs:
                yaml_content = yaml_content.get("data_files", {})
                if self.data_loading_tab and "read_test_file" in yaml_content:
                    self.data_loading_tab.file_line_selection_widget.set_file_path(
                        str(self.main_path / yaml_content["read_test_file"])
                    )

                if (
                    self.hist_settings_tab and "histogramming_test_file" in yaml_content
                ):  # does not show as it doesn't exist.. unfortunately
                    self.hist_settings_tab.test_file_selector.set_file_path(
                        str(self.main_path / yaml_content["histogramming_test_file"])
                    )

                # Lastly, fill the files into the optimization tab and histogramming run tab
                self._apply_optimization_files(yaml_content.get("optimization_files") or [])

                # Lastly, fill the files into the optimization tab and histogramming run tab
                if self.histogramming_tab and "histogramming_files" in yaml_content:
                    for file_path in yaml_content["histogramming_files"]:
                        self.histogramming_tab.file_selection_widget.add_file_to_table(str(self.main_path / file_path))

            except Exception as e:
                self.info_viewer.setHtml(f"<p>Error loading template: {e}</p>")

    def handle_dropdown_change(self, index: int):
        # selected_text = self.config_dropdown.itemText(index)
        self.load_selected_default_config()

    def _apply_optimization_files(self, optimization_files: list[str]):
        if not self.optimization_tab:
            return

        file_selection_widget = self.optimization_tab.file_selection_widget
        file_selection_widget.clear_all_files()
        for file_path in optimization_files:
            file_selection_widget.add_file_to_table(str(self.main_path / file_path))
