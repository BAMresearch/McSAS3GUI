import logging
import sys
from pathlib import Path

def setup_logging(log_level=logging.INFO, log_to_file=False):
    # Create a custom logger
    logger = logging.getLogger("McSAS3")
    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        log_file = Path("logs") / "mcsas3_debug.log"
        log_file.parent.mkdir(exist_ok=True)  # Create 'logs' directory if it doesn't exist
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
