"""POST /interaction/turns — C3-INTERACTION-RUNTIME-01 HTTP boundary.

Bounded request/response contract only. AuthN is enforced by the
registered auth middleware; AuthZ (`delia.access` / superadmin) is
enforced inside the Application use case against the Core-resolved
PlatformAccessContext. This module performs syntactic validation only.
"""

from __future__ import annotations

import json
import logging
import queue
import threading

from flask import (
    Blueprint,
    Flask,
    Response,
    current_app,
    g,
    jsonify,
    request,
)

from app.application.interaction.activity import (
    ACTIVITY_EVENT_VERSION,
    ActivityPhase,
    TURN_ERROR_RECORD_TYPE,
    TURN_RESULT_RECORD_TYPE,
)
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    current_subject_bearer,
    unbind_subject_bearer,
)
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
    {"input", "context", "confirmation", "workspace", "max_execution_stage"}
)
# LOOP-03R2A: client-requested REDUCTION of execution authority. Only
# "prepare" is admissible — escalation vocabulary is rejected at the
# syntactic boundary before it can reach the contract.
_ALLOWED_EXECUTION_CEILINGS = frozenset({"prepare"})
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

        max_execution_stage, ceiling_error = _parse_execution_ceiling(
            body.get("max_execution_stage")
        )
        if ceiling_error is not None:
            logger.info(
                "interaction_rejected reason=invalid_execution_ceiling "
                "request_id=%s",
                getattr(g, "request_id", None),
            )
            return _error(INVALID_REQUEST, ceiling_error)

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
            max_execution_stage=max_execution_stage,
        )
        if _wants_ndjson():
            return _stream_interaction_turn(
                handler, command, logger
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


# ---------------- progressive NDJSON transport (doc 70 §16) ----------------
#
# Opt-in streaming mode of the SAME route (Option A): when the client
# accepts `application/x-ndjson`, the use case runs on one bounded
# worker thread while this request thread drains an in-memory queue —
# the ONLY way a synchronous `execute()` can interleave real events
# with an open response body (gunicorn sync worker). Without it there
# is no progressive boundary — only cosmetic buffering, which the
# contract forbids. Legacy `Accept: application/json` responses are
# untouched.

_NDJSON_MIME = "application/x-ndjson"

# At most 64 observable steps per turn, matching the MFE parser budget.
# Keep room for terminal observations even if the provider emits many steps.
_MAX_INTERMEDIATE_EVENTS = 60
_MAX_TERMINAL_ACTIVITY_EVENTS = 4
_MAX_QUEUED_ITEMS = _MAX_INTERMEDIATE_EVENTS + _MAX_TERMINAL_ACTIVITY_EVENTS + 2
_TERMINAL_ACTIVITY_PHASES = frozenset({
    ActivityPhase.WAITING_CONFIRMATION,
    ActivityPhase.COMPLETED,
    ActivityPhase.PARTIAL,
    ActivityPhase.BLOCKED,
    ActivityPhase.FAILED,
    ActivityPhase.CANCELLED,
})


def _wants_ndjson() -> bool:
    # Opt-in must be explicit. MIMEAccept.quality() resolves */* and
    # would otherwise stream to legacy clients that never requested it.
    return any(
        mimetype.lower() == _NDJSON_MIME and quality > 0
        for mimetype, quality in request.accept_mimetypes
    )


def _stream_interaction_turn(handler, command, logger):
    """ActivityEvent.v1 NDJSON stream — real progressive observation.

    Preflight: the first queue item is awaited BEFORE the streaming
    Response is returned. An InteractionError raised before any event
    (AuthN/AuthZ/validation) still answers the legacy JSON error with
    its HTTP status — headers are never committed early for cases that
    must preserve their codes.
    """
    # This is a per-request transport buffer, NOT an execution queue.
    # Two slots are reserved for the authoritative terminal + sentinel.
    # All producer writes are non-blocking, including after disconnect.
    items: queue.Queue[tuple[str, object]] = queue.Queue(
        maxsize=_MAX_QUEUED_ITEMS
    )

    # DELIA-C3-NDJSON-SUBJECT-BEARER-CONTEXT-HOTFIX-01: the bearer must
    # be captured HERE, on the request thread — inside the worker there
    # is no Flask request context, so flask.g.subject_bearer is
    # unreachable (production regression: mcp_authentication_failed /
    # "subject bearer unavailable"). The worker binds the already-
    # authenticated token to its own ContextVar — never copied into the
    # command, events, logs, or the response.
    subject_bearer = current_subject_bearer()

    def run() -> None:
        intermediate_events = 0
        terminal_events = 0

        binding = (
            bind_subject_bearer(subject_bearer)
            if subject_bearer
            else None
        )

        def publish_activity(event) -> None:
            nonlocal intermediate_events, terminal_events
            if event.phase in _TERMINAL_ACTIVITY_PHASES:
                if terminal_events >= _MAX_TERMINAL_ACTIVITY_EVENTS:
                    return
                terminal_events += 1
            else:
                if intermediate_events >= _MAX_INTERMEDIATE_EVENTS:
                    return
                intermediate_events += 1
            # Guaranteed capacity: at most 64 events + terminal + done.
            # Excess intermediate observations are omitted, not invented;
            # the final turn_result/turn_error is never dropped.
            items.put_nowait(("event", event))

        try:
            result = handler.execute(
                command,
                activity_channel=publish_activity,
            )
        except InteractionError as exc:
            items.put_nowait(("error", exc))
        except Exception:
            logger.exception("interaction_stream_failed")
            items.put_nowait(
                (
                    "error",
                    InteractionError(INTERNAL_ERROR, "internal error"),
                )
            )
        else:
            items.put_nowait(("result", result))
        finally:
            # Bearer never outlives the execution context — restored
            # before the sentinel so the worker leaves no credential.
            if binding is not None:
                unbind_subject_bearer(binding)
            items.put_nowait(("done", None))

    worker = threading.Thread(
        target=run, name="delia-interaction-turn", daemon=True
    )
    worker.start()

    kind, payload = items.get()
    if kind == "error" and isinstance(payload, InteractionError):
        # Pre-stream failure: legacy error semantics fully preserved.
        logger.info(
            "interaction_failed error_code=%s request_id=%s",
            payload.code,
            getattr(g, "request_id", None),
        )
        return _error(payload.code, payload.message)

    def generate():
        first = (kind, payload)
        pending = [first]
        try:
            while True:
                item_kind, item_payload = (
                    pending.pop() if pending else items.get()
                )
                if item_kind == "event":
                    yield _activity_line(item_payload)
                elif item_kind == "result":
                    yield _terminal_line(
                        TURN_RESULT_RECORD_TYPE,
                        {"result": serialize_result(item_payload)},
                    )
                    break
                elif item_kind == "error":
                    exc = item_payload
                    yield _terminal_line(
                        TURN_ERROR_RECORD_TYPE,
                        {
                            "code": getattr(exc, "code", INTERNAL_ERROR),
                            "message": getattr(
                                exc, "message", "internal error"
                            ),
                        },
                    )
                    break
                else:  # "done" — stream ended without a terminal record
                    break
        except GeneratorExit:
            # Client disconnected: stop consuming; the worker finishes
            # bounded by the turn deadline — never re-executed.
            raise
        finally:
            worker.join(timeout=1.0)

    response = Response(
        generate(),
        status=200,
        content_type=_NDJSON_MIME,
    )
    # Progressive delivery guarantees at this boundary only — no
    # gateway change, no other service's buffering is touched.
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Cache-Control"] = "no-cache, no-store"
    return response


def _activity_line(event) -> str:
    return (
        json.dumps(event.to_record(), ensure_ascii=False, default=str)
        + "\n"
    )


def _terminal_line(record_type: str, payload: dict) -> str:
    record = {
        "type": record_type,
        "version": ACTIVITY_EVENT_VERSION,
        **payload,
    }
    return json.dumps(record, ensure_ascii=False, default=str) + "\n"


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


def _parse_execution_ceiling(
    raw: object,
) -> tuple[str | None, str | None]:
    """Syntactic validation of the client-requested execution ceiling.

    ``max_execution_stage`` can only REDUCE execution authority:
    ``"prepare"`` caps the governed chain at PREPARE. Absent/``null``
    means no client-requested reduction. Any other value — including
    escalation vocabulary like "act"/"execute"/"direct" — is a strict
    INVALID_REQUEST, never coerced or silently widened.
    """
    if raw is None:
        return None, None
    if not isinstance(raw, str):
        return None, "'max_execution_stage' must be a string"
    if raw not in _ALLOWED_EXECUTION_CEILINGS:
        return None, (
            "'max_execution_stage' only accepts 'prepare' — it can "
            "reduce, never request, execution authority"
        )
    return raw, None


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
