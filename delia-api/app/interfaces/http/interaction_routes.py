"""POST /interaction/turns — C3-INTERACTION-RUNTIME-01 HTTP boundary.

Bounded request/response contract only. AuthN is enforced by the
registered auth middleware; AuthZ (`delia.access` / superadmin) is
enforced inside the Application use case against the Core-resolved
PlatformAccessContext. This module performs syntactic validation only.
"""

from __future__ import annotations

import logging

from flask import Blueprint, Flask, current_app, g, jsonify, request

from app.application.interaction.contracts import (
    InteractiveTurnRequest,
    InteractiveTurnResult,
)
from app.application.interaction.errors import (
    FORBIDDEN,
    INTERNAL_ERROR,
    INVALID_MODEL_OUTPUT,
    INVALID_REQUEST,
    MODEL_TIMEOUT,
    MODEL_UNAVAILABLE,
    InteractionError,
)
from app.application.interaction.handle_interactive_turn import (
    serialize_result,
)


ALLOWED_BODY_KEYS = frozenset({"input"})

_ERROR_STATUS = {
    "unauthenticated": 401,
    FORBIDDEN: 403,
    INVALID_REQUEST: 400,
    MODEL_UNAVAILABLE: 503,
    MODEL_TIMEOUT: 504,
    INVALID_MODEL_OUTPUT: 502,
    "forbidden_model_output": 502,
    INTERNAL_ERROR: 500,
}


def register_interaction_routes(app: Flask, logger: logging.Logger) -> None:
    bp = Blueprint("interaction", __name__)

    @bp.post("/interaction/turns")
    def submit_delia_interaction_turn():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            logger.info(
                "interaction_rejected reason=malformed_body request_id=%s",
                getattr(g, "request_id", None),
            )
            return _error(INVALID_REQUEST, "request body must be a JSON object")

        extra_keys = set(body) - ALLOWED_BODY_KEYS
        if extra_keys:
            logger.info(
                "interaction_rejected reason=forbidden_fields request_id=%s",
                getattr(g, "request_id", None),
            )
            return _error(
                INVALID_REQUEST,
                f"unsupported request fields: {sorted(extra_keys)}",
            )

        input_text = body.get("input")
        if not isinstance(input_text, str):
            return _error(INVALID_REQUEST, "'input' must be a string")

        handler = current_app.config.get("INTERACTION_TURN_HANDLER")
        if handler is None:
            logger.warning("interaction_rejected reason=handler_not_configured")
            return _error(MODEL_UNAVAILABLE, "interaction service unavailable")

        command = InteractiveTurnRequest(
            access_context=getattr(g, "platform_access", None),
            input_text=input_text,
        )
        try:
            result = handler.execute(command)
        except InteractionError as exc:
            logger.info(
                "interaction_failed error_code=%s request_id=%s",
                exc.code,
                getattr(g, "request_id", None),
            )
            return _error(exc.code, exc.message)
        except Exception:
            logger.exception("interaction_failed error_code=internal_error")
            return _error(INTERNAL_ERROR, "internal error")

        _log_result(logger, result)
        return jsonify(serialize_result(result)), 200

    app.register_blueprint(bp)


def _log_result(logger: logging.Logger, result: InteractiveTurnResult) -> None:
    # Safe observability only: correlation IDs. Never logs input text,
    # generated content, tokens, or authority context.
    logger.info(
        "interaction_completed session_id=%s user_turn_id=%s "
        "result_turn_id=%s model_invocation_id=%s",
        result.session_id,
        result.user_turn_id,
        result.result_turn_id,
        result.model_invocation_id,
    )


def _error(code: str, message: str):
    status = _ERROR_STATUS.get(code, 500)
    return jsonify({"detail": message, "code": code}), status
