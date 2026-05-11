import logging
import time
from uuid import uuid4

from flask import g, request


logger = logging.getLogger("minha-delpi-ai-api.http")


def register_request_logging(app):
    @app.before_request
    def before_request():
        g.request_id = request.headers.get("X-Request-ID") or str(uuid4())
        g.request_started_at = time.perf_counter()

    @app.after_request
    def after_request(response):
        duration_ms = None

        if hasattr(g, "request_started_at"):
            duration_ms = round((time.perf_counter() - g.request_started_at) * 1000, 2)

        logger.info(
            "http_request",
            extra={
                "request_id": getattr(g, "request_id", None),
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
            },
        )

        response.headers["X-Request-ID"] = getattr(g, "request_id", "")

        return response
