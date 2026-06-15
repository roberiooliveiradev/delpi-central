import logging
import os
import sys
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

_fmt = "%(asctime)s [%(levelname)s] %(message)s"
_log_formatter = logging.Formatter(_fmt)

logger = logging.getLogger("api-totvs")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _log_file = os.path.join(LOG_DIR, f"api_{datetime.now().strftime('%Y%m%d')}.log")
    try:
        _file_handler = logging.FileHandler(_log_file)
        _file_handler.setLevel(logging.INFO)
        _file_handler.setFormatter(_log_formatter)
        logger.addHandler(_file_handler)
    except (OSError, PermissionError):
        pass

    _stderr_handler = logging.StreamHandler(sys.stderr)
    _stderr_handler.setLevel(logging.WARNING)
    _stderr_handler.setFormatter(_log_formatter)
    logger.addHandler(_stderr_handler)
    logger.propagate = False


def log_info(message: str):
    logger.info(message)

def log_error(message: str):
    logger.error(message)

def log_warning(message: str):
    logger.warning(message)
