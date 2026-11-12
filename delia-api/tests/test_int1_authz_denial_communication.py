"""INT-1 — governed authorization denial projection and communication.

Proves:
1. AUTHZ_DENIED is projected as authorization_denied (not NOT_FOUND /
   unavailable / generic NO_PROGRESS recovery cue).
2. Continuity ModelRetry is blocked for authorization denials.
3. Finalize preserves AUTHZ_DENIED / mcp_authorization_denied.
4. User-facing message explains access restriction without leaking
   protected data or inventing missing-record semantics.
"""

from __future__ import annotations

from app.application.capability_provision.semantic_capability_support import (
    INVESTIGATION_PROGRESS_NONE,
    _finalize_agent_collected_attempts,
    _is_business_evidence_attempt,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.handle_interactive_turn import (
    DELPI_SOURCE_DENIED_MESSAGE,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _attempt_projection,
    continuity_model_retry_allowed,
)


def _denied_attempt(
    *,
    error_code: str = MCP_AUTHORIZATION_DENIED,
) -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.AUTHZ_DENIED,
        correlation_id="c-authz",
        content=None,
        limitations=(),
        outcome=None,
        error_code=error_code,
    )


def test_authz_denied_projection_is_not_recoverable_no_progress():
    attempt = _denied_attempt()
    projection = _attempt_projection(
        attempt,
        observation_index=0,
        uncovered_after=("ITEM-1",),
    )
    assert projection["status"] == "AUTHZ_DENIED"
    assert projection["error_code"] == MCP_AUTHORIZATION_DENIED
    assert projection["authorization_denied"] is True
    assert projection["evidence_citable"] is False
    assert projection["investigation_progress"] == INVESTIGATION_PROGRESS_NONE
    note = (projection.get("coverage_note") or "").casefold()
    assert "authorization denied" in note
    assert "not missing data" in note
    assert "do not retry" in note
    assert "not_found" not in note
    assert "90260921" not in note
    assert "davi" not in note
    assert "teo" not in note
    assert _is_business_evidence_attempt(attempt) is False


def test_continuity_model_retry_blocked_for_authz_denied():
    attempt = _denied_attempt()
    assert (
        continuity_model_retry_allowed(
            attempt=attempt,
            investigation_progress=INVESTIGATION_PROGRESS_NONE,
            uncovered=("ITEM-1",),
            already_used=False,
            under_tool_limit=True,
        )
        is False
    )


def test_continuity_model_retry_still_allowed_for_non_authz_no_progress():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="c1",
        error_code="owner_not_found",
    )
    assert (
        continuity_model_retry_allowed(
            attempt=attempt,
            investigation_progress=INVESTIGATION_PROGRESS_NONE,
            uncovered=("ITEM-1",),
            already_used=False,
            under_tool_limit=True,
        )
        is True
    )


class _NullOrch:
    """Finalize helper only needs the orchestrator for compose paths."""

    def _compose_multi_evidence(self, *args, **kwargs):  # noqa: ANN001
        return None


def test_finalize_preserves_authz_denied_over_later_unrelated_failure():
    denied = _denied_attempt()
    later = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="c-authz",
        error_code="mcp_timeout",
        content="timeout",
    )
    result = _finalize_agent_collected_attempts(
        _NullOrch(),  # type: ignore[arg-type]
        input_text="Qual a estrutura do produto ITEM-1?",
        collected=(denied, later),
        correlation="c-authz",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
    )
    assert result.status is GovernedCapabilityStatus.AUTHZ_DENIED
    assert result.error_code == MCP_AUTHORIZATION_DENIED
    assert "authorization_denied" in result.limitations
    assert result.error_code != "investigation_no_business_evidence"
    assert result.error_code != "owner_query_miss"


def test_user_facing_authz_message_explains_permission_not_missing_data():
    text = DELPI_SOURCE_DENIED_MESSAGE.casefold()
    assert "permissão" in text or "permissoes" in text or "permissões" in text
    assert "minha delpi" in text
    assert "não há registro" not in text
    assert "not_found" not in text
    assert "stack" not in text
    assert "token" not in text
    assert "role" not in text
