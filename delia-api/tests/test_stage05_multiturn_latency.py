"""Stage 05 multiturn latency — prior continuity + selection budget.

Fake clock / fake model only. No external latency. MESSAGE ≠ ACT.
GLOBAL budget respected without raising InvokeModel.MAX_TIMEOUT.
"""

from __future__ import annotations

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    CapabilityProviderError,
    ProviderCapability,
    ProviderSurface,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    MIN_VIABLE_MODEL_STAGE_SECONDS,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    InteractiveTurnRequest,
    LIMITATION_PRIOR_TURN_CONTINUATION,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.domain.evidence.model import EpistemicClass, ModelRef, SourceRef
from app.domain.interaction.model import GroundingStatus, TurnKind
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)

TEST_MODEL_REF = ModelRef(
    model_id="latency-model", version="1", owner_ref="DELPI"
)

_PURPOSE_IDS = frozenset(
    {
        GOAL_INSTRUCTION_ID,
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        SYNTHESIS_INSTRUCTION_ID,
    }
)


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
        proposal,
        *,
        timeout_purposes: frozenset[str] = frozenset(),
        clock: FakeClock | None = None,
        advance_seconds: float = 0.0,
    ):
        items = (
            list(proposal) if isinstance(proposal, list) else [proposal]
        )
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        self._last: dict[str, object] = {}
        self._timeout_purposes = set(timeout_purposes)
        self._clock = clock
        self._advance_seconds = float(advance_seconds)
        for item in items:
            if isinstance(item, dict) and set(item) & _PURPOSE_IDS:
                for purpose, payload in item.items():
                    self._queues.setdefault(purpose, []).append(payload)
            else:
                self._generic.append(item)

    def invoke(self, request):
        self.requests.append(request)
        if self._clock is not None and self._advance_seconds:
            self._clock.advance(self._advance_seconds)
        purpose = request.task_purpose_id
        if purpose in self._timeout_purposes:
            raise ModelInvocationError(TIMEOUT, "stage timed out")
        queue = self._queues.get(purpose)
        if queue:
            resolved = queue.pop(0)
        elif self._generic:
            resolved = self._generic.pop(0)
        else:
            resolved = self._last.get(purpose)
        if resolved is None:
            from tests.support.fake_group_proposal import (
                singleton_group_proposal_from_request,
            )
            resolved = singleton_group_proposal_from_request(request)
        if resolved is not None:
            self._last[purpose] = resolved
        return ProviderInvocationPayload(
            structured_output=resolved,
            generated_at="2026-01-01T00:00:00+00:00",
        )


class FakeProvider:
    def __init__(self, provider_id, groups, outcomes=None):
        self.provider_id = provider_id
        self._groups = list(groups)
        self.calls = []
        self._outcomes = dict(outcomes or {})

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        return ProviderSurface(groups=tuple(self._groups))

    def invoke(
        self, capability, arguments, *, correlation_id,
        timeout_seconds=None,
    ):
        self.calls.append((capability.remote_name, dict(arguments)))
        key = (capability.group_id, capability.remote_name)
        outcome = self._outcomes.get(key)
        if isinstance(outcome, CapabilityProviderError):
            raise outcome
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
        )


def _cap(group_id, provider_id, name, op_class, schema=None, desc=""):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description=desc,
        input_schema=schema or {"type": "object", "properties": {}},
        binding={"ref": name},
    )


def _group(provider_id, group_id, capabilities):
    return CapabilityGroup(
        provider_id=provider_id,
        group_id=group_id,
        owner_ref=group_id,
        display_name=group_id,
        capabilities=tuple(capabilities),
        source=SourceRef(
            source_id=group_id,
            source_system=group_id,
            provider_name=group_id,
        ),
    )


def _outcome(group_id, remote_name, text, structured=None):
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id=group_id,
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="c",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=text,
        structured=structured,
    )


def _prior_pair(result_content: str = "Guia: etapa 1 — revisão."):
    return (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Como criar um produto?",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=result_content,
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )


def _context():
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def test_second_turn_transforms_prior_without_reselection():
    """Follow-up transforms prior excerpts; skips selection/MCP."""
    provider = FakeProvider(
        "teo",
        [
            _group(
                "teo",
                "teo",
                [
                    _cap(
                        "teo",
                        "teo",
                        "get_product_guide",
                        SpecialistOperationClass.READ,
                    ),
                    _cap(
                        "teo",
                        "teo",
                        "list_topics",
                        SpecialistOperationClass.DISCOVERY,
                    ),
                ],
            )
        ],
        {
            ("teo", "get_product_guide"): _outcome(
                "teo", "get_product_guide", "should-not-run"
            )
        },
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": True,
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {"record_index": 0, "fields": ["excerpt"]},
                    {"record_index": 1, "fields": ["excerpt"]},
                ],
                "presentation": "answer",
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    prior = _prior_pair(
        "Primeira orientação sobre revisão. "
        "Segunda orientação com etapas. "
        "Limitação: não cobre instâncias."
    )
    attempt = orch.attempt(
        "Resuma o que você acabou de explicar.",
        prior_turns=prior,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.outcome is None
    assert attempt.content != prior[1].content
    assert "Primeira orientação" in (attempt.content or "")
    assert LIMITATION_PRIOR_TURN_CONTINUATION in attempt.limitations
    assert provider.calls == []
    purposes = [r.task_purpose_id for r in model.requests]
    # Q02-A: admission always runs with prior turns (topic-change gate).
    assert GOAL_INSTRUCTION_ID in purposes
    assert SYNTHESIS_INSTRUCTION_ID in purposes
    assert purposes[-2:] == [GOAL_INSTRUCTION_ID, SYNTHESIS_INSTRUCTION_ID]
    assert GROUP_SELECTION_INSTRUCTION_ID not in purposes
    assert CAPABILITY_SELECTION_INSTRUCTION_ID not in purposes


def test_topic_change_requires_new_selection_without_prior_on_select():
    """New subject must reselect; selection stages omit prior_turns."""
    provider = FakeProvider(
        "teo",
        [
            _group(
                "teo",
                "teo",
                [
                    _cap(
                        "teo",
                        "teo",
                        "get_product_guide",
                        SpecialistOperationClass.READ,
                    ),
                    _cap(
                        "teo",
                        "teo",
                        "get_indicator",
                        SpecialistOperationClass.READ,
                    ),
                ],
            )
        ],
        {
            ("teo", "get_indicator"): _outcome(
                "teo",
                "get_indicator",
                "Indicador X = 42",
                structured={"data": {"items": [{"nome": "X", "valor": 42}]}},
            )
        },
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": False,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_indicator",
            },
            ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {"record_index": 0, "fields": ["nome", "valor"]}
                ],
                "presentation": "answer",
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    prior = _prior_pair()
    attempt = orch.attempt(
        "Agora mostre o indicador X.",
        prior_turns=prior,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.outcome is not None
    assert provider.calls
    assert provider.calls[0][0] == "get_indicator"
    select_reqs = [
        r
        for r in model.requests
        if r.task_purpose_id == CAPABILITY_SELECTION_INSTRUCTION_ID
    ]
    assert select_reqs
    assert select_reqs[0].prior_context == ()


def test_insufficient_prior_content_does_not_reuse():
    """prior_evidence_sufficient without extractable content falls through."""
    provider = FakeProvider(
        "teo",
        [
            _group(
                "teo",
                "teo",
                [
                    _cap(
                        "teo",
                        "teo",
                        "get_product_guide",
                        SpecialistOperationClass.READ,
                    )
                ],
            )
        ],
        {
            ("teo", "get_product_guide"): _outcome(
                "teo", "get_product_guide", "guia fresco"
            )
        },
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": True,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_product_guide",
            },
            ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT, content="pergunta"
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="   ",
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    attempt = orch.attempt("continue", prior_turns=prior)
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.outcome is not None
    assert provider.calls
    assert LIMITATION_PRIOR_TURN_CONTINUATION not in attempt.limitations


def test_unknown_provider_equivalent_selection_omits_prior_context():
    """Unseen owner with equivalent READ surface — selection has no prior."""
    provider = FakeProvider(
        "zephyr-unknown",
        [
            _group(
                "zephyr-unknown",
                "widgets",
                [
                    _cap(
                        "widgets",
                        "zephyr-unknown",
                        "list_widgets",
                        SpecialistOperationClass.READ,
                    )
                ],
            )
        ],
        {
            ("widgets", "list_widgets"): _outcome(
                "widgets", "list_widgets", "W-1"
            )
        },
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": False,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "list_widgets",
            },
            ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Liste widgets",
        prior_turns=_prior_pair("contexto irrelevante"),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    select_reqs = [
        r
        for r in model.requests
        if r.task_purpose_id == CAPABILITY_SELECTION_INSTRUCTION_ID
    ]
    assert select_reqs
    assert select_reqs[0].prior_context == ()
    assert provider.calls == [("list_widgets", {})]


def test_dependency_timeout_is_terminal_not_success():
    provider = FakeProvider(
        "teo",
        [
            _group(
                "teo",
                "teo",
                [
                    _cap(
                        "teo",
                        "teo",
                        "a",
                        SpecialistOperationClass.READ,
                    ),
                    _cap(
                        "teo",
                        "teo",
                        "b",
                        SpecialistOperationClass.READ,
                    ),
                ],
            )
        ],
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": False,
            },
        },
        timeout_purposes=frozenset({CAPABILITY_SELECTION_INSTRUCTION_ID}),
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Quero o item B",
        prior_turns=_prior_pair(),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "model_timeout"
    assert provider.calls == []


def test_prior_continuation_preserves_authz_and_message_not_act():
    """Handler: SUCCESS without outcome → NON_GROUNDED; no ACT."""
    provider = FakeProvider(
        "teo",
        [
            _group(
                "teo",
                "teo",
                [
                    _cap(
                        "teo",
                        "teo",
                        "get_product_guide",
                        SpecialistOperationClass.READ,
                    ),
                    _cap(
                        "teo",
                        "teo",
                        "commit_proposal",
                        SpecialistOperationClass.ACT,
                        schema={
                            "type": "object",
                            "properties": {
                                "proposal_handle": {"type": "string"},
                                "confirmation": {"type": "boolean"},
                            },
                            "required": ["proposal_handle", "confirmation"],
                        },
                    ),
                ],
            )
        ],
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": True,
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {"record_index": 0, "fields": ["excerpt"]}
                ],
                "presentation": "answer",
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    handler = HandleInteractiveConversationTurn(
        InvokeModel(FakeProposalModel({})),
        capability_orchestration=orch,
    )
    prior = _prior_pair("Conteúdo anterior fundamentado.")
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(),
            input_text="Repita o essencial do que já disse.",
            prior_turns=prior,
        )
    )
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert result.epistemic_class is EpistemicClass.HYPOTHESIS
    assert LIMITATION_PRIOR_TURN_CONTINUATION in result.limitations
    assert "Conteúdo anterior" in result.content
    assert provider.calls == []
    assert all(
        name != "commit_proposal" for name, _ in provider.calls
    )


def test_global_budget_blocks_model_stage_when_remaining_too_small():
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    # Leave less than MIN_VIABLE for the next model stage.
    clock.advance(30.0 - (MIN_VIABLE_MODEL_STAGE_SECONDS / 2))
    provider = FakeProvider(
        "teo",
        [
            _group(
                "teo",
                "teo",
                [
                    _cap(
                        "teo",
                        "teo",
                        "a",
                        SpecialistOperationClass.READ,
                    ),
                    _cap(
                        "teo",
                        "teo",
                        "b",
                        SpecialistOperationClass.READ,
                    ),
                ],
            )
        ],
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": False,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "b",
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
        model_stage_timeout_seconds=10.0,
    )
    attempt = orch.attempt(
        "quero B",
        prior_turns=_prior_pair(),
        turn_deadline=deadline,
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "turn_budget_exhausted"
    # Goal may have run before budget shrank; capability select must not.
    assert CAPABILITY_SELECTION_INSTRUCTION_ID not in [
        r.task_purpose_id for r in model.requests
    ]
    assert provider.calls == []


def test_budget_starvation_attributed_in_ledger():
    """Stage 6: a slow semantic stage consuming the shared budget must
    be attributed as budget exhaustion with ZERO operational time —
    never misreported as an owner-API failure."""
    from app.application.interaction.turn_observability import (
        ModelCallLedger,
        bind_turn_call_ledger,
        reset_turn_call_ledger,
    )

    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    clock.advance(30.0 - (MIN_VIABLE_MODEL_STAGE_SECONDS / 2))
    provider = FakeProvider(
        "teo",
        [
            _group(
                "teo",
                "teo",
                [_cap("teo", "teo", "a", SpecialistOperationClass.READ)],
            )
        ],
    )
    model = FakeProposalModel(
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "a",
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
        model_stage_timeout_seconds=10.0,
    )
    ledger = ModelCallLedger()
    token = bind_turn_call_ledger(ledger)
    try:
        attempt = orch.attempt(
            "consulta a", turn_deadline=deadline
        )
    finally:
        reset_turn_call_ledger(token)
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "turn_budget_exhausted"
    # Attribution: budget ran out; no owner call ever happened.
    assert ledger.timeout_source == "budget"
    assert ledger.operational_calls == ()
    assert provider.calls == []
