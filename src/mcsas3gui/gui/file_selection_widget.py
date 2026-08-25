import logging
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger("McSAS3")


class FileSelectionWidget(QWidget):
    def __init__(
        self,
        title: str,
        acceptable_file_types: str = "*.*",
        last_used_directory: Path = Path("~").expanduser(),
        parent=None,
    ):
        super().__init__(parent)
        self.acceptable_file_types = acceptable_file_types
        self.last_used_directory = last_used_directory

        layout = QVBoxLayout()

        # Title Label
        layout.addWidget(QLabel(title))

        # File Table
        self.file_table = QTableWidget(0, 2)
        self.file_table.setStyleSheet(
            """
            QTableWidget, QTableView, QTableWidget::item {
                background-color: palette(base);
                color: palette(text);
                font-family: "Arial", "Helvetica", "Sans-Serif";
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;  /* light blue highlight */
                color: black;               /* ensure text is visible */
            }
            QHeaderView::section {
                background-color: palette(base);
                color: palette(text);
                padding: 4px;
                font-weight: bold;
            }
            """
        )

        self.file_table.setHorizontalHeaderLabels(["File Name", "Status"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.setColumnWidth(1, 150)  # Set fixed width for status column
        self.file_table.setAcceptDrops(True)
        self.file_table.viewport().installEventFilter(self)
        self.file_table.setDragEnabled(True)

        layout.addWidget(self.file_table)

        # Buttons for managing data files
        button_layout = QHBoxLayout()
        self.load_files_button = QPushButton("Load Datafile(s)")
        self.load_files_button.clicked.connect(self.load_data_files)
        self.clear_files_button = QPushButton("Clear Selected File(s)")
        self.clear_files_button.clicked.connect(self.clear_selected_files)
        button_layout.addWidget(self.load_files_button)
        button_layout.addWidget(self.clear_files_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_data_files(self):
        """Open a file dialog to load data files and add them to the table."""
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            str(self.last_used_directory),
            f"Files ({self.acceptable_file_types})",
        )
        if file_names:
            self.last_used_directory = Path(file_names[0]).parent
            for file_name in file_names:
                self.add_file_to_table(file_name)

    def add_file_to_table(self, file_name):
        """Add a file to the table if it's not already listed."""
        if not self.is_file_in_table(file_name):
            row_position = self.file_table.rowCount()
            self.file_table.insertRow(row_position)
            # print(f"Adding file: {file_name}, type: {type(file_name)}")
            self.file_table.setItem(row_position, 0, QTableWidgetItem(file_name))
            status_item = QTableWidgetItem("Pending")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(row_position, 1, status_item)

            logger.debug(f"Added file to table: {file_name}")

    def clear_selected_files(self):
        """Remove only the selected rows from the file table."""
        selected_rows = {index.row() for index in self.file_table.selectedIndexes()}
        for row in sorted(selected_rows, reverse=True):
            self.file_table.removeRow(row)

    def is_file_in_table(self, file_path):
        """Check if a file is already in the table to avoid duplicates."""
        for row in range(self.file_table.rowCount()):
            if self.file_table.item(row, 0).text() == file_path:
                return True
        return False

    def get_selected_files(self):
        """Retrieve the list of selected files from the table."""
        return [Path(self.file_table.item(row, 0).text()) for row in range(self.file_table.rowCount())]

    def set_status_by_row(self, row: int = None, status: str = "Pending"):
        """Set the status for a specific file."""
        if row is not None:
            self.file_table.item(row, 1).setText(status)
            return

    def set_status_by_file_name(self, file_path: str | Path, status: str = "Pending"):
        """Set the status for a specific file."""
        if isinstance(file_path, Path):
            file_path = str(file_path)

        for row in range(self.file_table.rowCount()):
            if self.file_table.item(row, 0).text() == file_path:
                self.file_table.item(row, 1).setText(status)
                break

    def eventFilter(self, source, event):
        """Handle drag-and-drop events for the file table viewport.

        The table still accepts internal drag-and-drop events, which should eventually be disabled
        because they can overwrite file names in other rows.
        """

        if source != self.file_table.viewport():
            # If the event is not from the viewport, pass it to the parent class
            return super().eventFilter(source, event)

        if event.type() not in (event.Type.DragEnter, event.Type.DragMove, event.Type.Drop):
            return super().eventFilter(source, event)

        mime_data = event.mimeData()
        if mime_data.hasUrls():
            if event.type() in (event.Type.DragEnter, event.Type.DragMove):
                event.acceptProposedAction()
                return True

            if event.type() == event.Type.Drop:
                for url in mime_data.urls():
                    logging.debug(f"Dropped URL: {url.toString()}")
                    file_path = Path(url.toLocalFile())

                    if "*.*" in self.acceptable_file_types or any(
                        file_path.suffix.lower() == ft.lower().lstrip("*") for ft in self.acceptable_file_types.split()
                    ):
                        logging.debug(f"Adding file to table: {file_path}")
                        self.add_file_to_table(str(file_path.as_posix()))
                event.acceptProposedAction()
                return True

        # this must be here to render:
        return super().eventFilter(source, event)
