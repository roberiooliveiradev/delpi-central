"""R45 selection timeout rework — structural ticket capability shortcut.

TASK: DELIA-C3-R45-PAGINATION-INTEGRITY-AND-PRODUCTION-SSH-VALIDATION-01

Locks:
- ticket COUNT/LIST with a sole schema advertising action=tickets
  selects without a model capability-selection stage
- CAPABILITY_SELECTION timeout no longer blocks owner READ for that class
- write / multi-match / non-ticket surfaces stay on the model path
- no provider hardcode (renamed / non-MCP ids still work)
"""

from __future__ import annotations

from typing import Any

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
    ProviderSurface,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.paginated_result_semantics import (
    schema_supports_ticket_list_action,
    unique_structural_ticket_list_capability,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import ModelRef, SourceRef
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)


TEST_MODEL_REF = ModelRef(
    model_id="r45-sel", version="1", owner_ref="DELPI"
)

_TICKETS_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["session", "capabilities", "tickets", "ticket"],
        },
        "page": {"type": "integer"},
        "page_size": {"type": "integer"},
    },
    "required": ["action"],
}

_OTHER_READ_SCHEMA = {
    "type": "object",
    "properties": {"topic": {"type": "string"}},
}


def _cap(
    group_id: str,
    provider_id: str,
    name: str,
    op_class: SpecialistOperationClass,
    schema: dict[str, Any] | None = None,
) -> ProviderCapability:
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description=name,
        input_schema=schema or {"type": "object", "properties": {}},
        binding={"ref": name},
    )


def _helpdesk_cap(
    *,
    group_id: str = "mcp:teo",
    provider_id: str = "mcp:teo",
    name: str = "helpdesk_read",
) -> ProviderCapability:
    return _cap(
        group_id,
        provider_id,
        name,
        SpecialistOperationClass.READ,
        _TICKETS_SCHEMA,
    )


# --- Unit: structural helper (SEL-T01..T12 core) -----------------------------


def test_sel_t01_ticket_count():
    cap = _helpdesk_cap()
    assert (
        unique_structural_ticket_list_capability(
            [cap], "Quantos chamados tem para mim?"
        )
        is cap
    )


def test_sel_t02_assigned_to_me():
    cap = _helpdesk_cap()
    assert (
        unique_structural_ticket_list_capability(
            [cap], "Quantos chamados estão atribuídos a mim?"
        )
        is cap
    )


def test_sel_t03_requested_by_me():
    cap = _helpdesk_cap()
    assert (
        unique_structural_ticket_list_capability(
            [cap], "Quantos chamados eu abri?"
        )
        is cap
    )


def test_sel_t05_small_valid_surface():
    caps = [
        _cap(
            "g",
            "p",
            "other",
            SpecialistOperationClass.READ,
            _OTHER_READ_SCHEMA,
        ),
        _helpdesk_cap(group_id="g", provider_id="p"),
    ]
    selected = unique_structural_ticket_list_capability(
        caps, "Liste meus chamados."
    )
    assert selected is not None
    assert selected.remote_name == "helpdesk_read"


def test_sel_t06_large_valid_surface_still_unique_tickets():
    caps = [
        _cap(
            "g",
            "p",
            f"tool_{i}",
            SpecialistOperationClass.READ,
            _OTHER_READ_SCHEMA,
        )
        for i in range(12)
    ]
    tickets = _helpdesk_cap(group_id="g", provider_id="p", name="ops_list")
    caps.append(tickets)
    selected = unique_structural_ticket_list_capability(
        caps, "Quantos chamados estão em aberto?"
    )
    assert selected is tickets


def test_sel_t07_renamed_provider():
    cap = _helpdesk_cap(
        group_id="ops-alpha",
        provider_id="ops-alpha",
        name="ticket_browse",
    )
    assert schema_supports_ticket_list_action(cap.input_schema)
    assert (
        unique_structural_ticket_list_capability(
            [cap], "Quantos chamados visíveis existem?"
        )
        is cap
    )


def test_sel_t08_non_mcp_provider():
    cap = _helpdesk_cap(
        group_id="a2a:helpdesk",
        provider_id="a2a:helpdesk",
        name="list_tickets",
    )
    assert (
        unique_structural_ticket_list_capability(
            [cap], "Quantos chamados tem para mim?"
        )
        is cap
    )


def test_sel_t09_model_invalid_selection_no_unique_match():
    a = _helpdesk_cap(name="helpdesk_a")
    b = _helpdesk_cap(name="helpdesk_b")
    assert (
        unique_structural_ticket_list_capability(
            [a, b], "Quantos chamados tem para mim?"
        )
        is None
    )


def test_sel_t12_ambiguous_write_does_not_structural_select():
    cap = _helpdesk_cap()
    assert (
        unique_structural_ticket_list_capability(
            [cap], "Crie um chamado de suporte urgente"
        )
        is None
    )


def test_sel_non_ticket_domain_skipped():
    cap = _helpdesk_cap()
    assert (
        unique_structural_ticket_list_capability(
            [cap], "Quantos produtos tem no catálogo?"
        )
        is None
    )


# --- Integration: timeout of capability stage vs structural recovery --------


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += float(seconds)


class FakeProposalModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(
        self,
        proposal: dict[str, Any],
        *,
        clock: FakeClock | None = None,
        timeout_purposes: frozenset[str] = frozenset(),
    ) -> None:
        self._proposal = dict(proposal)
        self.requests: list[Any] = []
        self._clock = clock
        self._timeout_purposes = frozenset(timeout_purposes)

    def invoke(self, request):
        self.requests.append(request)
        purpose = request.task_purpose_id
        if purpose in self._timeout_purposes:
            if self._clock is not None:
                self._clock.advance(
                    max(0.0, request.timeout_seconds or 10.0)
                )
            raise ModelInvocationError(
                TIMEOUT, "simulated stage timeout"
            )
        resolved = self._proposal.get(purpose)
        return ProviderInvocationPayload(
            structured_output=resolved,
            generated_at="2026-01-01T00:00:00+00:00",
        )


class FakeProvider:
    def __init__(self, provider_id: str, groups, outcomes=None) -> None:
        self.provider_id = provider_id
        self._groups = list(groups)
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._outcomes = dict(outcomes or {})

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        return ProviderSurface(groups=tuple(self._groups))

    def invoke(
        self, capability, arguments, *, correlation_id, timeout_seconds=None
    ):
        self.calls.append((capability.remote_name, dict(arguments)))
        key = (capability.group_id, capability.remote_name)
        outcome = self._outcomes.get(key)
        if outcome is not None:
            return outcome
        return SpecialistOutcome(
            status=SpecialistResultStatus.COMPLETED,
            provenance=SpecialistResultProvenance(
                specialist_id=capability.group_id,
                remote_name=capability.remote_name,
                protocol=InteropProtocol.MCP,
                correlation_id=correlation_id,
                observed_at="2026-01-01T00:00:00+00:00",
            ),
            content_text="ok",
            structured={
                "items": [{"id": 1, "title": "t1"}],
                "page": 1,
                "page_size": 10,
                "has_more": False,
            },
        )


def _outcome(group_id: str, remote_name: str, structured: dict[str, Any]):
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id=group_id,
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="c",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text="ok",
        structured=structured,
    )


def _ticket_surface_providers(*, renamed: bool = False):
    group_id = "ops-alpha" if renamed else "mcp:teo"
    provider_id = group_id
    name = "ticket_browse" if renamed else "helpdesk_read"
    cap = _helpdesk_cap(
        group_id=group_id, provider_id=provider_id, name=name
    )
    guide = _cap(
        group_id,
        provider_id,
        "get_methodology_guide",
        SpecialistOperationClass.READ,
        _OTHER_READ_SCHEMA,
    )
    group = CapabilityGroup(
        provider_id=provider_id,
        group_id=group_id,
        owner_ref=group_id,
        display_name=group_id,
        capabilities=(cap, guide),
        source=SourceRef(
            source_id=group_id,
            source_system=group_id,
            provider_name=group_id,
        ),
    )
    tickets_page = {
        "items": [{"id": i, "title": f"T{i}"} for i in range(1, 5)],
        "page": 1,
        "page_size": 10,
        "has_more": False,
    }
    provider = FakeProvider(
        provider_id,
        [group],
        outcomes={
            (group_id, name): _outcome(group_id, name, tickets_page),
        },
    )
    return [provider], name, f"{provider_id}:{group_id}"


def test_sel_t04_group_ok_capability_timeout_structural_reaches_owner():
    """Historical live fail: select_capability timed out before owner.

    With structural ticket shortcut, CAPABILITY_SELECTION timeout must
    not fire for COUNT asks — owner READ is reached.
    """
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    providers, remote_name, group_key = _ticket_surface_providers()
    model = FakeProposalModel(
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": group_key,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": remote_name,
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {
                    "action": "tickets",
                    "page": 1,
                    "page_size": 10,
                }
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "content": "Total confirmado nesta consulta: 4."
            },
        },
        clock=clock,
        timeout_purposes=frozenset({CAPABILITY_SELECTION_INSTRUCTION_ID}),
    )
    orch = OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Quantos chamados tem para mim?",
        turn_deadline=deadline,
    )
    purposes = [r.task_purpose_id for r in model.requests]
    assert CAPABILITY_SELECTION_INSTRUCTION_ID not in purposes
    assert any(c[0] == remote_name for c in providers[0].calls)
    assert attempt.error_code != "model_timeout"
    assert attempt.status in {
        GovernedCapabilityStatus.SUCCESS,
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
    }


def test_sel_t10_model_timeout_still_terminal_without_structural():
    """Non-ticket ask + capability timeout remains terminal (no bypass)."""
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    providers, remote_name, group_key = _ticket_surface_providers()
    model = FakeProposalModel(
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": group_key,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": remote_name,
            },
        },
        clock=clock,
        timeout_purposes=frozenset({CAPABILITY_SELECTION_INSTRUCTION_ID}),
    )
    orch = OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Como conduzir análise de causas em um processo?",
        turn_deadline=deadline,
    )
    assert attempt.error_code in {
        "model_timeout",
        "turn_budget_exhausted",
    }
    assert providers[0].calls == []


def test_sel_t11_remaining_budget_low_structural_still_skips_cap_stage():
    clock = FakeClock()
    # Leave little budget after group selection would run; structural
    # must still avoid spending a model stage on capability selection.
    deadline = TurnDeadline.start(8.0, clock=clock)
    providers, remote_name, group_key = _ticket_surface_providers(
        renamed=True
    )
    model = FakeProposalModel(
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": group_key,
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {"action": "tickets", "page": 1}
            },
            SYNTHESIS_INSTRUCTION_ID: {"content": "ok"},
        },
        clock=clock,
        timeout_purposes=frozenset({CAPABILITY_SELECTION_INSTRUCTION_ID}),
    )
    orch = OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Liste meus chamados.",
        turn_deadline=deadline,
    )
    purposes = [r.task_purpose_id for r in model.requests]
    assert CAPABILITY_SELECTION_INSTRUCTION_ID not in purposes
    # May succeed or clarify on personal scope — must not be cap timeout.
    assert attempt.error_code != "model_timeout" or providers[0].calls
