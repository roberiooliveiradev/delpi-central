import logging
logger = logging.getLogger("invoice_posting")

def log_error(message: str) -> None:
    logger.error(message)
