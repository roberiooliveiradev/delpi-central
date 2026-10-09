"""C3-CENTRAL-INTERACTION-EXPERIENCE-BACKEND-01 — Interaction
Presentation Contract tests.

Proves the additive, versioned presentation projection:

- every user-facing result family carries a canonical message_kind;
- blocks come only from the closed allowlist (text / notice) and are
  built exclusively from already-governed result fields;
- owner preconditions surface as PRECONDITION_REQUIRED + verbatim
  owner_hint notice — never a URL, credential, or raw payload;
- confirmation surfaces expose only the existing CONFIRM/REJECT
  vocabulary — presentation never widens execution authority;
- the projection is additive: legacy top-level response fields are
  unchanged (backward compatibility);
- model/provider output can never inject a block kind.
"""

from __future__ import annotations

import pytest

from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    InteractiveTurnRequest,
    InteractiveTurnResult,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
    serialize_result,
)
from app.application.interaction.presentation import (
    MESSAGE_KIND_AUTHZ_DENIED,
    MESSAGE_KIND_CLARIFICATION_REQUIRED,
    MESSAGE_KIND_CONFIRMATION_REQUIRED,
    MESSAGE_KIND_PRECONDITION_REQUIRED,
    MESSAGE_KIND_RESULT,
    MESSAGE_KIND_SOURCE_UNAVAILABLE,
    MESSAGE_KIND_WRITE_REJECTED,
    PRESENTATION_CONTRACT_VERSION,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import GroundingStatus
from app.domain.model_invocation.model import ProviderExposureClass


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


class _StubModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self):
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        return ProviderInvocationPayload(
            structured_output={"answer": "prose"},
            generated_at="2026-01-01T00:00:00+00:00",
        )


class _StubOrchestration:
    def __init__(self, attempt: GovernedCapabilityAttempt):
        self._attempt = attempt

    def attempt(self, *args, **kwargs):
        return self._attempt


def _result(**overrides) -> InteractiveTurnResult:
    base = dict(
        session_id="s1",
        user_turn_id="u1",
        result_turn_id="r1",
        content="conteúdo governado",
        epistemic_class=EpistemicClass.OBSERVATION,
        limitations=(),
        generated_at="2026-01-01T00:00:00+00:00",
        model_invocation_id=None,
        grounding_status=GroundingStatus.GROUNDED,
    )
    base.update(overrides)
    return InteractiveTurnResult(**base)


def _handler_with_attempt(attempt: GovernedCapabilityAttempt):
    return HandleInteractiveConversationTurn(
        InvokeModel(_StubModel()),
        capability_orchestration=_StubOrchestration(attempt),
    )


def _execute(attempt: GovernedCapabilityAttempt) -> InteractiveTurnResult:
    return _handler_with_attempt(attempt).execute(
        InteractiveTurnRequest(
            access_context=_context(), input_text="consulta"
        )
    )


# --- composition unit tests -------------------------------------------------


def test_result_presentation_defaults_and_shape():
    presentation = serialize_result(_result())["presentation"]
    assert presentation["version"] == PRESENTATION_CONTRACT_VERSION
    assert presentation["message_kind"] == MESSAGE_KIND_RESULT
    assert presentation["semantic_status"] == "OBSERVATION"
    assert presentation["grounding_status"] == "GROUNDED"
    assert presentation["blocks"] == [
        {"kind": "text", "text": "conteúdo governado"}
    ]
    assert presentation["allowed_interactions"] == ["reply"]


def test_confirmation_request_derives_kind_and_interactions():
    presentation = serialize_result(
        _result(
            confirmation_request={
                "proposal_digest": "d1",
                "preview_fingerprint": "f1",
            }
        )
    )["presentation"]
    assert presentation["message_kind"] == (
        MESSAGE_KIND_CONFIRMATION_REQUIRED
    )
    assert presentation["allowed_interactions"] == [
        "reply",
        "confirm",
        "reject",
    ]


def test_owner_hint_derives_precondition_kind_and_notice_block():
    hint = "Helpdesk BFF error: glpi_link_required."
    presentation = serialize_result(_result(owner_hint=hint))[
        "presentation"
    ]
    assert presentation["message_kind"] == (
        MESSAGE_KIND_PRECONDITION_REQUIRED
    )
    assert presentation["blocks"] == [
        {"kind": "text", "text": "conteúdo governado"},
        {"kind": "notice", "role": "owner_hint", "text": hint},
    ]


def test_declared_message_kind_is_respected():
    presentation = serialize_result(
        _result(message_kind=MESSAGE_KIND_CLARIFICATION_REQUIRED)
    )["presentation"]
    assert presentation["message_kind"] == (
        MESSAGE_KIND_CLARIFICATION_REQUIRED
    )
    assert presentation["allowed_interactions"] == ["reply"]


def test_unknown_message_kind_fails_closed_to_derivation():
    presentation = serialize_result(
        _result(message_kind="injected-html-block")
    )["presentation"]
    assert presentation["message_kind"] == MESSAGE_KIND_RESULT
    assert all(
        block["kind"] in ("text", "notice")
        for block in presentation["blocks"]
    )


def test_block_text_is_bounded():
    presentation = serialize_result(
        _result(content="x" * 20_000, owner_hint="h" * 20_000)
    )["presentation"]
    for block in presentation["blocks"]:
        assert len(block["text"]) <= 16_384


def test_top_level_contract_is_backward_compatible():
    body = serialize_result(_result(owner_hint="h"))
    assert set(body) == {
        "session_id",
        "user_turn_id",
        "result_turn_id",
        "content",
        "epistemic_class",
        "limitations",
        "generated_at",
        "model_invocation_id",
        "grounding_status",
        "provenance",
        "confirmation_request",
        "presentation",
    }


# --- handler wiring ----------------------------------------------------------


def _attempt(status, **kwargs) -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=status, correlation_id="c-test", **kwargs
    )


def test_source_unavailable_maps_kind():
    result = _execute(_attempt(GovernedCapabilityStatus.SOURCE_UNAVAILABLE))
    assert result.message_kind == MESSAGE_KIND_SOURCE_UNAVAILABLE
    assert serialize_result(result)["presentation"]["message_kind"] == (
        MESSAGE_KIND_SOURCE_UNAVAILABLE
    )


def test_authz_denied_maps_kind():
    result = _execute(_attempt(GovernedCapabilityStatus.AUTHZ_DENIED))
    assert result.message_kind == MESSAGE_KIND_AUTHZ_DENIED


def test_owner_precondition_maps_kind_and_carries_hint():
    hint = "Helpdesk BFF error: glpi_link_required."
    result = _execute(
        _attempt(
            GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
            error_code="mcp_protocol_error",
            owner_hint=hint,
        )
    )
    assert result.message_kind == MESSAGE_KIND_PRECONDITION_REQUIRED
    assert result.owner_hint == hint
    presentation = serialize_result(result)["presentation"]
    assert {
        "kind": "notice",
        "role": "owner_hint",
        "text": hint,
    } in presentation["blocks"]


def test_write_lifecycle_kinds():
    for status, expected in (
        (
            GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
            MESSAGE_KIND_CLARIFICATION_REQUIRED,
        ),
        (
            GovernedCapabilityStatus.WRITE_REJECTED,
            MESSAGE_KIND_WRITE_REJECTED,
        ),
        (
            GovernedCapabilityStatus.CONFIRMATION_REQUIRED,
            MESSAGE_KIND_CONFIRMATION_REQUIRED,
        ),
    ):
        attempt = _attempt(
            status,
            content="conteúdo",
            confirmation_context=(
                {"proposal_digest": "d1", "preview_fingerprint": "f1"}
                if status
                is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
                else None
            ),
        )
        result = _execute(attempt)
        assert result.message_kind == expected
