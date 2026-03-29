# main.py

import logging
import os
import sys
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from mcsas3gui._bootstrap import ensure_compatible_mcsas3

ensure_compatible_mcsas3()
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mcsas3gui-matplotlib"))


def main():
    from mcsas3gui.gui.main_window import McSAS3MainWindow  # Main window with all tabs
    from mcsas3gui.utils.logging_config import setup_logging  # Import the logging configuration

    # Create a temporary directory without automatic cleanup
    temp_dir = Path(tempfile.mkdtemp())
    log_file = temp_dir / "mcsas3_debug.log"
    # Initialize logging with logging to file
    logger = setup_logging(log_level=logging.INFO, log_file=log_file)
    logger.info("Starting McSAS3 GUI application...")
    logger.info(f"Logging to temporary directory at: {log_file}")
    # Start the PyQt application
    app = QApplication(sys.argv)

    main_window = McSAS3MainWindow(temp_dir)
    main_window.show()

    logger.debug("McSAS3 GUI is now visible.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
