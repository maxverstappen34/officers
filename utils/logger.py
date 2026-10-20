"""
Logging Setup - Officers Affairs Management System
"""

import logging
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    return logging.getLogger("officers_affairs")
