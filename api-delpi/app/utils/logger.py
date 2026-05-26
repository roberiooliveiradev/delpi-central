import logging
import os
import sys
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

_fmt = "%(asctime)s [%(levelname)s] %(message)s"

logging.basicConfig(
    filename=os.path.join(LOG_DIR, f"api_{datetime.now().strftime('%Y%m%d')}.log"),
    format=_fmt,
    level=logging.INFO,
)

logger = logging.getLogger("api-totvs")

_stderr_handler = logging.StreamHandler(sys.stderr)
_stderr_handler.setLevel(logging.WARNING)
_stderr_handler.setFormatter(logging.Formatter(_fmt))
logger.addHandler(_stderr_handler)


def log_info(message: str):
    logger.info(message)

def log_error(message: str):
    logger.error(message)

def log_warning(message: str):
    logger.warning(message)
