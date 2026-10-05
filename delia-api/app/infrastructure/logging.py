from __future__ import annotations

import logging
import sys


def configure_logging(service_name: str, level: str) -> logging.Logger:
    resolved = getattr(logging, level, logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    logger = logging.getLogger(service_name)
    logger.setLevel(resolved)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.propagate = False
    # Module loggers (app.application..., app.domain...) propagate to
    # the "app" parent logger. Without a handler there every bounded
    # orchestration/audit log was silently dropped — only the service
    # logger emitted. Attach the same handler so app.* logs reach
    # stdout with the same format and level.
    app_logger = logging.getLogger("app")
    app_logger.setLevel(resolved)
    if not app_logger.handlers:
        app_logger.addHandler(handler)
    app_logger.propagate = False
    return logger
