import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from ..config import ui_config


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(name: str = "chainlit_ui") -> logging.Logger:
    """Set up logger with both file and console handlers"""

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, ui_config.log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create logs directory if it doesn't exist
    log_dir = Path(ui_config.log_file).parent
    log_dir.mkdir(exist_ok=True)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        ui_config.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        "%(asctime)s | %(levelname)-8s | %(funcName)s - %(message)s", datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


# Create default logger instance
logger = setup_logger()
