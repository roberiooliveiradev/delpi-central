from __future__ import annotations

import logging
import uuid

from flask import g, request

logger = logging.getLogger("supplies-api.request")


def register_request_context(app) -> None:
    @app.before_request
    def bind_request_id():
        incoming = (request.headers.get("X-Request-Id") or "").strip()
        g.request_id = incoming or str(uuid.uuid4())

    @app.after_request
    def attach_request_id(response):
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-Id"] = request_id
        return response

    @app.after_request
    def log_request(response):
        user = getattr(g, "current_user", None)
        logger.info(
            "request_completed",
            extra={
                "request_id": getattr(g, "request_id", None),
                "user_id": getattr(user, "id", None),
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
            },
        )
        return response
