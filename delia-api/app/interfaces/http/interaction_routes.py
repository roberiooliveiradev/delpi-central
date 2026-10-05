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
    CONTEXT_TOO_LARGE,
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
from app.application.interaction.workspace_context import (
    parse_workspace_context,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import TurnKind


ALLOWED_BODY_KEYS = frozenset(
    {"input", "context", "confirmation", "workspace"}
)
CONTEXT_TURN_KEYS = frozenset({"kind", "content", "epistemic_class"})
CONFIRMATION_KEYS = frozenset(
    {
        "decision",
        "proposal_digest",
        "preview_fingerprint",
        "session_id",
    }
)
_CONTEXT_KINDS = {
    "USER_INPUT": TurnKind.USER_INPUT,
    "DELIA_RESULT": TurnKind.DELIA_RESULT,
}

_ERROR_STATUS = {
    "unauthenticated": 401,
    FORBIDDEN: 403,
    INVALID_REQUEST: 400,
    CONTEXT_TOO_LARGE: 400,
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

        prior_turns, parse_error = _parse_context(body.get("context"))
        if parse_error is not None:
            return _error(INVALID_REQUEST, parse_error)

        confirmation, conf_error = _parse_confirmation(
            body.get("confirmation")
        )
        if conf_error is not None:
            return _error(INVALID_REQUEST, conf_error)

        workspace_context, ws_error = parse_workspace_context(
            body.get("workspace")
        )
        if ws_error is not None:
            return _error(INVALID_REQUEST, ws_error)

        handler = current_app.config.get("INTERACTION_TURN_HANDLER")
        if handler is None:
            logger.warning("interaction_rejected reason=handler_not_configured")
            return _error(MODEL_UNAVAILABLE, "interaction service unavailable")

        command = InteractiveTurnRequest(
            access_context=getattr(g, "platform_access", None),
            input_text=input_text,
            prior_turns=prior_turns,
            confirmation=confirmation,
            workspace_context=workspace_context,
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


def _parse_context(
    raw: object,
) -> tuple[tuple[ConversationContextTurn, ...], str | None]:
    """Syntactic validation of untrusted client-supplied context.

    Semantic admissibility (epistemic class per kind, alternation,
    aggregate bound) belongs to the use case. Here we only guarantee a
    strict shape: a list of objects with kind/content/epistemic_class
    and no other fields — no authority, provider, or system keys can
    enter the application contract.
    """
    if raw is None:
        return (), None
    if not isinstance(raw, list):
        return (), "'context' must be a list"
    turns: list[ConversationContextTurn] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            return (), f"context[{index}] must be an object"
        extra = set(item) - CONTEXT_TURN_KEYS
        if extra:
            return (), (
                f"context[{index}] unsupported fields: {sorted(extra)}"
            )
        kind = _CONTEXT_KINDS.get(item.get("kind"))
        if kind is None:
            return (), (
                f"context[{index}].kind must be USER_INPUT or DELIA_RESULT"
            )
        content = item.get("content")
        if not isinstance(content, str):
            return (), f"context[{index}].content must be a string"
        epistemic_raw = item.get("epistemic_class")
        epistemic: EpistemicClass | None = None
        if epistemic_raw is not None:
            try:
                epistemic = EpistemicClass(epistemic_raw)
            except ValueError:
                return (), (
                    f"context[{index}].epistemic_class is not a "
                    "canonical class"
                )
        turns.append(
            ConversationContextTurn(
                kind=kind, content=content, epistemic_class=epistemic
            )
        )
    return tuple(turns), None


def _parse_confirmation(
    raw: object,
) -> tuple[dict[str, str] | None, str | None]:
    """Syntactic validation of the untrusted confirmation payload.

    A confirmation carries only structured decision fields and
    non-reversible digests — never the raw owner proposal handle, which
    stays backend-only. Semantic binding (actor/session/fingerprint/
    expiry) belongs to the orchestration layer.
    """
    if raw is None:
        return None, None
    if not isinstance(raw, dict):
        return None, "'confirmation' must be an object"
    extra = set(raw) - CONFIRMATION_KEYS
    if extra:
        return None, (
            f"'confirmation' unsupported fields: {sorted(extra)}"
        )
    confirmation: dict[str, str] = {}
    for key in CONFIRMATION_KEYS:
        value = raw.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            return None, f"'confirmation.{key}' must be a string"
        confirmation[key] = value
    if not confirmation.get("decision") or not confirmation.get(
        "proposal_digest"
    ):
        return None, (
            "'confirmation' requires 'decision' and 'proposal_digest'"
        )
    return confirmation, None


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
