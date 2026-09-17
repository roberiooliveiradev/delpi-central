from __future__ import annotations

import logging
import uuid

from flask import Flask, g, request


def register_request_logging(app: Flask, logger: logging.Logger) -> None:
    @app.before_request
    def bind_request_id():
        incoming = (request.headers.get("X-Request-Id") or "").strip()
        g.request_id = incoming or str(uuid.uuid4())

    @app.after_request
    def complete_request(response):
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-Id"] = request_id
        logger.info(
            "request_completed path=%s method=%s status=%s request_id=%s",
            request.path,
            request.method,
            response.status_code,
            request_id,
        )
        return response
