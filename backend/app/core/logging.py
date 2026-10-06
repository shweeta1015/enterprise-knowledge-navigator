"""
Logging Configuration for Enterprise Knowledge Navigator.
Provides structured console logging and daily file rotation logging.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from backend.app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures root and application loggers."""
    settings.ensure_directories_exist()
    log_file = settings.LOG_DIR / "app.log"

    # Base logging format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # File Handler (10MB max, keeping 5 backup files)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Remove existing handlers if any to avoid duplication
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    # Specific app logger
    app_logger = logging.getLogger("enterprise_navigator")
    app_logger.info("Structured logging initialized for Enterprise Knowledge Navigator.")

    return app_logger


logger = setup_logging()
