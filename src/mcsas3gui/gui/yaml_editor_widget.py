# src/gui/yaml_editor_widget.py

import logging
import re

import yaml
from PyQt6.QtCore import QEvent, QRegularExpression, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger("McSAS3")
YAML_FILE_FILTER = "YAML Files (*.yaml *.yml)"


class CustomDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(CustomDumper, self).increase_indent(flow, False)

    def represent_list(self, data):
        # Check if the list is nested (i.e., part of a parent structure)
        if any(isinstance(item, (list, dict)) for item in data):
            # Represent nested lists in block style
            return self.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=False)
        else:
            # Represent innermost lists in inline (flow) style
            return self.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)

    def represent_dict(self, data):
        # Use block style (default) for dictionaries
        return self.represent_mapping("tag:yaml.org,2002:map", data, flow_style=False)


# Register custom list representation for flow style
CustomDumper.add_representer(list, CustomDumper.represent_list)

# Register custom list representation for flow style
CustomDumper.add_representer(dict, CustomDumper.represent_dict)


class YAMLErrorHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.error_line = None
        self.error_message = None

        # Define formatting styles
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(QColor("blue"))
        self.key_format.setFontWeight(QFont.Weight.Bold)

        self.value_format = QTextCharFormat()
        self.value_format.setForeground(QColor("darkgreen"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("gray"))
        self.comment_format.setFontItalic(True)

        # Define regex patterns for YAML syntax
        self.rules = [
            (QRegularExpression(r"^\s*[^#]*:"), self.key_format),  # Keys
            (QRegularExpression(r":\s*[^#]*"), self.value_format),  # Values
            (QRegularExpression(r"#.*$"), self.comment_format),  # Comments
        ]

    def set_error(self, line, message):
        """Set the error line and message for highlighting."""
        self.error_line = line
        self.error_message = message
        self.rehighlight()  # Trigger rehighlighting to apply error highlight

    def clear_error(self):
        """Clear any syntax error highlighting."""
        self.error_line = None
        self.error_message = None
        self.rehighlight()  # Reset highlighting

    def highlightBlock(self, text):
        """Apply syntax highlighting and error highlighting if necessary."""

        # Apply YAML syntax highlighting rules
        for pattern, fmt in self.rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # Apply error highlighting if on the error line
        if self.error_line is not None and self.currentBlock().blockNumber() == self.error_line - 1:
            error_format = QTextCharFormat()
            error_format.setBackground(QColor("lightcoral"))
            self.setFormat(0, len(text), error_format)

    def eventFilter(self, obj, event):
        """Display tooltip on hover over error-highlighted line."""
        if event.type() == QEvent.Type.ToolTip and self.error_line is not None:
            # Obtain cursor at mouse position
            cursor = obj.cursorForPosition(event.pos())
            if cursor.blockNumber() == self.error_line - 1:
                QToolTip.showText(event.globalPos(), self.error_message, obj)
            else:
                QToolTip.hideText()
            return True
        return super().eventFilter(obj, event)


class YAMLEditorWidget(QWidget):
    fileSaved = pyqtSignal(str)
    fileLoaded = pyqtSignal(str)

    def __init__(self, directory, parent=None, multipart: bool = False):
        super().__init__(parent)
        self.directory = str(directory)
        self.multipart = multipart  # indicates a multipart yaml
        layout = QVBoxLayout()

        # YAML Editor with Error Highlighting
        self.yaml_editor = QTextEdit()
        self.yaml_editor.setStyleSheet(
            """
                QTextEdit, QPlainTextEdit {
                    background-color: #f7f7ff;
                    border: 1px solid #cccccc;
                    padding: 6px;
                    font-family: "Courier New", monospace;
                }
            """
        )
        self.yaml_editor.setAcceptDrops(False)  # Disable drag-and-drop
        self.error_highlighter = YAMLErrorHighlighter(self.yaml_editor.document())
        self.yaml_editor.textChanged.connect(self.validate_yaml)  # Connect validation
        self.yaml_editor.installEventFilter(self.error_highlighter)  # Install event filter for tooltip handling
        layout.addWidget(self.yaml_editor)

        # Load and Save Buttons
        button_layout = QHBoxLayout()
        load_button = QPushButton("Load Configuration")
        load_button.clicked.connect(self.load_yaml)
        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_yaml)
        button_layout.addWidget(load_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def validate_yaml(self):
        """Validate YAML content and highlight any syntax errors."""
        yaml_content = self.yaml_editor.toPlainText()

        # Temporarily disconnect the signal to avoid recursion
        self.yaml_editor.textChanged.disconnect(self.validate_yaml)

        try:
            # Attempt to parse YAML
            list(yaml.safe_load_all(yaml_content))  # Handle multipart YAML
            self.error_highlighter.clear_error()  # Clear previous error highlights if valid
        except yaml.YAMLError as e:
            error_message = str(e)
            line_number = self.extract_error_line(error_message)
            if line_number is not None:
                self.error_highlighter.set_error(line_number, error_message)  # Highlight offending line
        finally:
            # Reconnect the signal
            self.yaml_editor.textChanged.connect(self.validate_yaml)

    def extract_error_line(self, error_message):
        """Extract the line number from a YAML error message."""
        match = re.search(r"line (\d+)", error_message)
        return int(match.group(1)) if match else None

    def load_yaml(self):
        """Open a file dialog to load a YAML file and display it in the editor."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Configuration", self.directory, YAML_FILE_FILTER)
        if file_name:
            logger.debug(f"Loading YAML configuration from file: {file_name}")
            with open(file_name, "r") as file:
                try:
                    yaml_content = list(yaml.safe_load_all(file))  # Handle multipart YAML
                    yaml_text = "---\n".join(
                        yaml.dump(doc, Dumper=CustomDumper, default_flow_style=None, sort_keys=False)
                        for doc in yaml_content
                        if doc
                    )
                    self.yaml_editor.setPlainText(yaml_text)
                    self.fileLoaded.emit(file_name)
                except yaml.YAMLError as e:
                    logger.error(f"Error loading YAML file {file_name}: {e}")
                    self.yaml_editor.setPlainText("Error loading YAML file.")

    def save_yaml(self):
        """Save the content of the YAML editor to a file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Configuration", self.directory, "YAML Files (*.yaml)")
        if file_name:
            yaml_content = self.yaml_editor.toPlainText()
            try:
                with open(file_name, "w") as file:
                    if self.multipart:
                        # make sure we're not saving "None" entries after a superfluos '---'
                        parsed_content = [
                            i for i in list(yaml.safe_load_all(yaml_content)) if i
                        ]  # Validate multipart YAML
                        yaml.dump_all(
                            parsed_content,
                            file,
                            Dumper=CustomDumper,
                            default_flow_style=None,
                            sort_keys=False,
                        )
                    else:
                        parsed_content = yaml.safe_load(yaml_content)  # Validate multipart YAML
                        yaml.dump(
                            parsed_content,
                            file,
                            Dumper=CustomDumper,
                            default_flow_style=None,
                            sort_keys=False,
                        )

                logger.debug(f"Saved YAML configuration to file: {file_name}")
                self.fileSaved.emit(file_name)

            except yaml.YAMLError as e:
                logger.error(f"Error saving YAML to file {file_name}: {e}")

    def get_yaml_content(self):
        """Parse and return the YAML content from the editor as a list of dictionaries."""
        try:
            return list(yaml.safe_load_all(self.yaml_editor.toPlainText()))  # Handle multipart YAML
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            return []

    def set_yaml_content(self, yaml_content):
        """Set YAML content in the editor, formatted as a string."""
        if isinstance(yaml_content, list):
            # Convert list of YAML documents into a string with separators
            yaml_text = "---\n".join(
                yaml.dump(doc, Dumper=CustomDumper, default_flow_style=None, sort_keys=False) for doc in yaml_content
            )
        elif isinstance(yaml_content, dict):
            # Convert single YAML document into a string
            yaml_text = yaml.dump(yaml_content, Dumper=CustomDumper, default_flow_style=None, sort_keys=False)
        else:
            # Fallback to raw string if input is already serialized YAML
            yaml_text = yaml_content
        self.yaml_editor.setPlainText(yaml_text)
