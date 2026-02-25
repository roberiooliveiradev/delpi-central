# app/utils/logger.py
import logging
import os
from datetime import datetime

# Garante que a pasta 'logs' exista
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configuração básica
logging.basicConfig(
    filename=os.path.join(LOG_DIR, f"api_{datetime.now().strftime('%Y%m%d')}.log"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("api-totvs")

def log_info(message: str):
    logger.info(message)

def log_error(message: str):
    logger.error(message)

def log_warning(message: str):
    logger.warning(message)
