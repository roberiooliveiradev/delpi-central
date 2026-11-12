"""INT-1 — partial authorization finalize and error-class separation.

Cases:
A SUCCESS then AUTHZ_DENIED → authorized evidence preserved + partial denial
B AUTHZ_DENIED then independent SUCCESS → same
C AUTHZ_DENIED alone → terminal AUTHZ_DENIED
D NOT_FOUND / owner miss ≠ AUTHZ_DENIED
E SOURCE_UNAVAILABLE ≠ AUTHZ_DENIED
"""

from __future__ import annotations

from app.application.capability_provision.semantic_capability_support import (
    _finalize_agent_collected_attempts,
    _is_business_evidence_attempt,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _attempt_projection,
    continuity_model_retry_allowed,
)
from app.application.capability_provision.semantic_capability_support import (
    INVESTIGATION_PROGRESS_NONE,
)


def _prov() -> GovernedCapabilityProvenance:
    return GovernedCapabilityProvenance(
        source_refs=(
            SourceRef(
                source_id="owner",
                source_system="owner",
                provider_name="owner",
                observed_at="2026-01-01T00:00:00Z",
            ),
        ),
        specialist_id="owner",
        remote_capability="read",
        action_id="read",
        protocol=InteropProtocol.MCP.value,
        observed_at="2026-01-01T00:00:00Z",
        correlation_id="c-partial",
        is_complete=True,
    )


def _success(*, content: str, root: str) -> GovernedCapabilityAttempt:
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text=content,
        structured={
            "status": "ok",
            "data": {"root": {"code": root}, "items": [{"code": "C1"}]},
        },
        provenance=SpecialistResultProvenance(
            specialist_id="owner",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="c-partial",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=True,
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c-partial",
        content=content,
        limitations=(),
        outcome=outcome,
        provenance=_prov(),
    )


def _denied() -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.AUTHZ_DENIED,
        correlation_id="c-partial",
        content=None,
        limitations=(),
        outcome=None,
        error_code=MCP_AUTHORIZATION_DENIED,
    )


class _NullOrch:
    def _compose_multi_evidence(self, *args, **kwargs):  # noqa: ANN001
        return None


def test_case_a_success_then_denial_preserves_authorized_evidence():
    ok = _success(content="BOM root ALPHA authorized", root="ALPHA")
    assert _is_business_evidence_attempt(ok) is True
    result = _finalize_agent_collected_attempts(
        _NullOrch(),  # type: ignore[arg-type]
        input_text="estrutura ALPHA e processo BETA",
        collected=(ok, _denied()),
        correlation="c-partial",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert "BOM root ALPHA authorized" in (result.content or "")
    assert "authorization_denied_partial" in result.limitations
    assert result.error_code != MCP_AUTHORIZATION_DENIED
    assert "secret-denied-payload" not in (result.content or "")


def test_case_b_denial_then_independent_success_preserves_authorized():
    ok = _success(content="process tree PROC authorized", root="PROC")
    result = _finalize_agent_collected_attempts(
        _NullOrch(),  # type: ignore[arg-type]
        input_text="processo PROC e produto ALPHA",
        collected=(_denied(), ok),
        correlation="c-partial",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert "process tree PROC authorized" in (result.content or "")
    assert "authorization_denied_partial" in result.limitations
    assert continuity_model_retry_allowed(
        attempt=_denied(),
        investigation_progress=INVESTIGATION_PROGRESS_NONE,
        uncovered=("ALPHA",),
        already_used=False,
        under_tool_limit=True,
    ) is False


def test_case_c_denial_alone_is_terminal_authz():
    result = _finalize_agent_collected_attempts(
        _NullOrch(),  # type: ignore[arg-type]
        input_text="estrutura do produto ALPHA",
        collected=(_denied(),),
        correlation="c-partial",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
    )
    assert result.status is GovernedCapabilityStatus.AUTHZ_DENIED
    assert result.error_code == MCP_AUTHORIZATION_DENIED
    assert "authorization_denied" in result.limitations


def test_case_d_not_found_is_not_authorization_denied():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="c-partial",
        error_code="owner_query_miss",
        content="not found",
    )
    projection = _attempt_projection(
        attempt, observation_index=0, uncovered_after=("ALPHA",)
    )
    assert projection.get("authorization_denied") is not True
    note = (projection.get("coverage_note") or "").casefold()
    assert "authorization denied" not in note
    result = _finalize_agent_collected_attempts(
        _NullOrch(),  # type: ignore[arg-type]
        input_text="estrutura ALPHA",
        collected=(attempt,),
        correlation="c-partial",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
    )
    assert result.status is not GovernedCapabilityStatus.AUTHZ_DENIED
    assert result.error_code == "owner_query_miss"


def test_case_e_owner_unavailable_is_not_authorization_denied():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="c-partial",
        error_code="mcp_timeout",
        content="timeout",
    )
    projection = _attempt_projection(
        attempt, observation_index=0, uncovered_after=("ALPHA",)
    )
    assert projection.get("authorization_denied") is not True
    result = _finalize_agent_collected_attempts(
        _NullOrch(),  # type: ignore[arg-type]
        input_text="estrutura ALPHA",
        collected=(attempt,),
        correlation="c-partial",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
    )
    assert result.status is not GovernedCapabilityStatus.AUTHZ_DENIED
    assert result.error_code == "investigation_no_business_evidence"
