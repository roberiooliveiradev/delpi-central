"""R1 + R3 — inconclusive selection terminal + projection framing.

Locks doc 35 remediation:
- R1: group/capability none and invalid proposals become
  CLARIFICATION_REQUIRED (orchestrator) so the handler never burns the
  turn budget on a second free-form model call (live L02/L06).
- Bare NOT_APPLICABLE (empty surface) preserves the ordinary
  conversational fallback when budget remains.
- R3: prior-excerpt / methodological lists are not framed as
  operational "registros".
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    _SELECTION_INCONCLUSIVE_CONTENT,
    _extraction_list_from_prior_excerpts,
    _list_header,
    _prior_excerpt_records,
    _records_are_prior_excerpts,
    _render_synthesis,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.model_invocation.errors import ModelInvocationError, TIMEOUT
from app.domain.interaction.model import GroundingStatus
from app.domain.model_invocation.model import ProviderExposureClass
from tests.test_interaction_runtime import _context
from tests.test_specialist_capability_orchestration import (
    FakePort,
    TEO_TOOLS,
    VISTA_TOOLS,
    _interop,
    _read,
    _select,
)


class _SpyModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self):
        self.requests = []

    def invoke(self, request):
        from app.application.model_invocation.contracts import (
            ProviderInvocationPayload,
        )

        self.requests.append(request)
        return ProviderInvocationPayload(
            structured_output={"answer": "fabricated"},
            generated_at="2026-01-01T00:00:00+00:00",
        )


class _StatusOrchestration:
    def __init__(self, status, content=None, error_code=None, limitations=()):
        self._status = status
        self._content = content
        self._error_code = error_code
        self._limitations = limitations
        self.calls = 0

    def attempt(self, *a, **k):
        self.calls += 1
        return GovernedCapabilityAttempt(
            status=self._status,
            correlation_id="corr-r1",
            content=self._content,
            error_code=self._error_code,
            limitations=self._limitations,
        )


def _handler(orch, model=None):
    spy = model or _SpyModel()
    return (
        HandleInteractiveConversationTurn(
            InvokeModel(spy), capability_orchestration=orch
        ),
        spy,
    )


# --- R1 -----------------------------------------------------------------


def test_t01_group_none_with_available_surface():
    """applicable=false → conversational NOT_APPLICABLE (CONV recovery).

    Operational ambiguity after a group was chosen still clarifies
    (see T02). Greetings/hypotheticals must not be forced into
    capability jargon ask-backs.
    """
    attempt = _read(
        _interop(
            FakePort(
                tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
            )
        ),
        specialist_ids=("teo", "vista"),
        proposal={GROUP_SELECTION_INSTRUCTION_ID: {"applicable": False}},
    ).attempt("5 exemplos de terminal bandeira")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE


def test_t02_capability_applicable_false_is_conversational():
    """Capability applicable=false → NOT_APPLICABLE (CONV recovery).

    Invented/invalid remote after a selected group still clarifies (T04).
    """
    attempt = _read(
        _interop(
            FakePort(
                tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
            )
        ),
        specialist_ids=("teo", "vista"),
        proposal={
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": "mcp:teo",
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {"applicable": False},
        },
    ).attempt("produtos?")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE


def test_t03_invalid_model_group():
    attempt = _read(
        _interop(
            FakePort(
                tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
            )
        ),
        specialist_ids=("teo", "vista"),
        proposal={
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": "mcp:invented",
            }
        },
    ).attempt("liste")
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED


def test_t04_invalid_model_capability():
    attempt = _read(
        _interop(FakePort(tools_by_specialist={"teo": TEO_TOOLS})),
        specialist_ids=("teo",),
        proposal=_select("teo", "mystery_tool"),
    ).attempt("resumo")
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED


def test_t05_model_timeout_is_technical_failure():
    from app.application.capability_provision.orchestration import (
        OperationalCapabilityOrchestrator,
    )
    from app.application.capability_provision.mcp_provider import (
        McpCapabilityProvider,
    )
    from tests.test_specialist_capability_orchestration import TEST_MODEL_REF

    class _TimeoutModel:
        adapter_kind = "TEST_ONLY"
        exposure_class = ProviderExposureClass.TEST_ONLY

        def invoke(self, request):
            raise ModelInvocationError(TIMEOUT, "stage timed out")

    orch = OperationalCapabilityOrchestrator(
        [
            McpCapabilityProvider(
                _interop(FakePort(tools_by_specialist={"teo": TEO_TOOLS})),
                ("teo",),
            )
        ],
        invoke_model=InvokeModel(_TimeoutModel()),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt("liste")
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code in {"model_timeout", "turn_budget_exhausted"}


def test_t06_provider_unavailable():
    from app.application.specialist_interop.errors import (
        SpecialistInteropError,
        MCP_AUTHENTICATION_FAILED,
    )

    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS},
        errors={
            ("teo", "analyze"): SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED, "auth failed"
            )
        },
    )
    attempt = _read(
        _interop(port), specialist_ids=("teo",), proposal=_select("teo", "analyze")
    ).attempt("resumo")
    assert attempt.status in {
        GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        GovernedCapabilityStatus.AUTHZ_DENIED,
    }


def test_t07_ambiguous_intent_clarifies_without_general_model():
    handler, spy = _handler(
        _StatusOrchestration(
            GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
            content=_SELECTION_INCONCLUSIVE_CONTENT,
        )
    )
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(), input_text="terminal bandeira"
        )
    )
    assert result.message_kind == "CLARIFICATION_REQUIRED"
    assert spy.requests == []
    assert result.model_invocation_id is None


def test_t08_ambiguous_write_stays_governed():
    handler, spy = _handler(
        _StatusOrchestration(
            GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
            content="Você quer que eu explique ou execute?",
        )
    )
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(),
            input_text="apague o registro do cliente",
        )
    )
    assert result.message_kind == "CLARIFICATION_REQUIRED"
    assert spy.requests == []


def test_t09_source_unavailable_is_terminal():
    handler, spy = _handler(
        _StatusOrchestration(
            GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
            error_code="owner_unreachable",
        )
    )
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(), input_text="liste produtos"
        )
    )
    assert spy.requests == []
    assert result.model_invocation_id is None
    assert result.grounding_status is GroundingStatus.NON_GROUNDED


def test_t10_handler_clarification_is_terminal_no_model():
    handler, spy = _handler(
        _StatusOrchestration(
            GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
            content=_SELECTION_INCONCLUSIVE_CONTENT,
        )
    )
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(),
            input_text="5 exemplos de terminal bandeira",
        )
    )
    assert spy.requests == []
    assert result.model_invocation_id is None
    assert result.message_kind == "CLARIFICATION_REQUIRED"
    assert "consultar" in result.content.lower() or "fonte" in (
        result.content.lower()
    )
    assert "capability" not in result.content.lower()


def test_t11_bare_not_applicable_preserves_general_fallback():
    """Empty-surface NOT_APPLICABLE remains a legitimate conversational path."""
    handler, spy = _handler(
        _StatusOrchestration(GovernedCapabilityStatus.NOT_APPLICABLE)
    )
    result = handler.execute(
        InteractiveTurnRequest(access_context=_context(), input_text="olá")
    )
    assert spy.requests
    assert result.content == "fabricated"


# --- R3 -----------------------------------------------------------------


PRIOR = (
    "method:\n"
    "- a problem or effect.\n"
    "- cause families need separation.\n"
    "- Effect statement.\n"
    "- What is the effect?\n"
    "- Which categories?\n"
    "- Evidências disponíveis\n"
    "- Quem observou?\n"
)


def test_t12_method_guidance_framing():
    records = _prior_excerpt_records(PRIOR)
    assert _records_are_prior_excerpts(records)
    header = _list_header(len(records), records=records)
    assert "registro" not in header.lower()
    assert "orientação" in header.lower() or "item" in header.lower()


def test_t13_checklist_framing():
    records = _prior_excerpt_records(PRIOR)
    rendered = _extraction_list_from_prior_excerpts(records)
    assert rendered
    assert "registro" not in rendered.split("\n", 1)[0].lower()


def test_t14_operational_record_list_framing():
    assert _list_header(2, records=({"id": "1"}, {"id": "2"})) == (
        "Encontrei 2 registros:"
    )
    assert _list_header(1, records=({"id": "1"},)) == "Encontrei 1 registro:"


def test_t15_prior_evidence_continuation():
    records = ({"excerpt": "a"}, {"excerpt": "b"}, {"excerpt": "c"})
    content, reason = _render_synthesis(
        {
            "presentation": "list",
            "items": [
                {"record_index": 0, "fields": ["excerpt"]},
                {"record_index": 1, "fields": ["excerpt"]},
                {"record_index": 2, "fields": ["excerpt"]},
            ],
        },
        records,
    )
    assert reason == "rendered"
    assert "orientação anterior" in content.lower()
    assert "registro" not in content.split("\n", 1)[0].lower()


def test_t16_grounding_preservation():
    content, reason = _render_synthesis(
        {
            "presentation": "list",
            "items": [
                {"record_index": 0, "fields": ["codigo"]},
                {"record_index": 1, "fields": ["codigo"]},
            ],
        },
        ({"codigo": "FX-1"}, {"codigo": "FX-2"}),
    )
    assert reason == "rendered"
    assert content.startswith("Encontrei 2 registros:")
    assert "FX-1" in content and "FX-2" in content


def test_t17_empty_evidence():
    assert _records_are_prior_excerpts(()) is False
    assert _list_header(0) == "Encontrei 0 registros:"
