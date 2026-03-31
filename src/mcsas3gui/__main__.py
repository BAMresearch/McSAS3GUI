import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path

from mcsas3gui import __version__
from mcsas3gui._bootstrap import ensure_compatible_mcsas3

ensure_compatible_mcsas3()
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mcsas3gui-matplotlib"))


def _parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="Launch the McSAS3 GUI application.")
    parser.add_argument("--version", action="store_true", help="Print the McSAS3GUI version and exit.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Initialize the GUI and exit immediately without entering the event loop.",
    )
    return parser.parse_known_args(sys.argv[1:] if argv is None else argv)


def main(argv: list[str] | None = None) -> int:
    args, qt_args = _parse_args(argv)
    if args.version:
        print(__version__)
        return 0

    from PyQt6.QtWidgets import QApplication

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
    app = QApplication([sys.argv[0], *qt_args])

    main_window = McSAS3MainWindow(temp_dir)
    main_window.show()

    if args.smoke_test:
        logger.info("Standalone GUI smoke test completed.")
        main_window.close()
        app.quit()
        return 0

    logger.debug("McSAS3 GUI is now visible.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
