"""Provider-neutral referential detail after a prior listing (C2 class).

Fixtures use generic list_entities / get_entity_context names — never
owner-specific branches. MESSAGE ≠ ACT.
"""

from __future__ import annotations

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
    ProviderSurface,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    RESOLVER_SELECTION_INSTRUCTION_ID,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _prior_listing_hint,
    _user_list_ordinal,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ProviderInvocationPayload,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import EpistemicClass, ModelRef, SourceRef
from app.domain.interaction.model import TurnKind
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)

TEST_MODEL_REF = ModelRef(
    model_id="referential-detail", version="1", owner_ref="DELPI"
)

_PURPOSE_IDS = frozenset(
    {
        GOAL_INSTRUCTION_ID,
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        RESOLVER_SELECTION_INSTRUCTION_ID,
        SYNTHESIS_INSTRUCTION_ID,
    }
)

PRIOR_LISTING = (
    "id: ent-alpha-001\n"
    "name: Alpha Board\n"
    "id: ent-beta-002\n"
    "name: Beta Board"
)


class FakeProposalModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposal):
        items = (
            list(proposal) if isinstance(proposal, list) else [proposal]
        )
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        self._last: dict[str, object] = {}
        for item in items:
            if isinstance(item, dict) and set(item) & _PURPOSE_IDS:
                for purpose, payload in item.items():
                    self._queues.setdefault(purpose, []).append(payload)
            else:
                self._generic.append(item)

    def invoke(self, request):
        self.requests.append(request)
        purpose = request.task_purpose_id
        queue = self._queues.get(purpose)
        if queue:
            resolved = queue.pop(0)
        elif purpose == "delia.capability_orchestration.interaction_admission":
            resolved = self._last.get(purpose)
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


def _prior(content: str = PRIOR_LISTING):
    return (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Liste as entidades disponíveis.",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=content,
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )


def _surface_caps():
    return [
        _cap(
            "ops",
            "holdout",
            "list_entities",
            SpecialistOperationClass.READ,
            desc="list available entities",
        ),
        _cap(
            "ops",
            "holdout",
            "get_entity_context",
            SpecialistOperationClass.READ,
            schema={
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                },
                "required": ["entity_id"],
            },
            desc="detail context for one entity",
        ),
    ]


def _list_outcome():
    return _outcome(
        "ops",
        "list_entities",
        PRIOR_LISTING,
        structured={
            "data": {
                "items": [
                    {
                        "id": "ent-alpha-001",
                        "name": "Alpha Board",
                        "screens": ["s1"],
                        "blocks": ["b1"],
                    },
                    {
                        "id": "ent-beta-002",
                        "name": "Beta Board",
                        "screens": ["s2"],
                        "blocks": ["b2"],
                    },
                ]
            }
        },
    )


def _detail_outcome():
    return _outcome(
        "ops",
        "get_entity_context",
        "detail",
        structured={
            "data": {
                "items": [
                    {
                        "entity_id": "ent-alpha-001",
                        "screens": "painel-a",
                        "blocks": "bloco-1",
                    }
                ]
            }
        },
    )


def test_user_list_ordinal_first():
    assert _user_list_ordinal(
        "Da primeira programação encontrada, mostre as telas."
    ) == 0
    assert _user_list_ordinal("the second item please") == 1
    assert _user_list_ordinal("mostre qualquer um") is None


def test_resolver_budget_allows_follow_up_headroom():
    """Live C2: ~11s remaining must still allow same-owner resolve."""
    class _Clock:
        def __init__(self) -> None:
            self.now = 1000.0

        def __call__(self) -> float:
            return self.now

    clock = _Clock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    clock.now += 18.8  # ~11.2s remaining — observed live skip under old floor
    orch = OperationalCapabilityOrchestrator(
        [],
        invoke_model=InvokeModel(FakeProposalModel({})),
        model_ref=TEST_MODEL_REF,
        model_stage_timeout_seconds=30.0,
    )
    assert orch._budget_allows_resolver(deadline) is True
    clock.now += 8.0  # ~3.2s left — below floor
    assert orch._budget_allows_resolver(deadline) is False


def test_prior_listing_hint_from_observation():
    hint = _prior_listing_hint(_prior())
    assert hint is not None
    assert hint["prior_result_available"] is True
    assert hint["listed_identifier_count"] >= 1
    assert hint["ordered_listing"] is True


def test_selection_payload_embeds_prior_listing_hint():
    provider = FakeProvider(
        "holdout", [_group("holdout", "ops", _surface_caps())]
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": False,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_entity_context",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": None,
                "missing_inputs": ["entity_id"],
            },
            RESOLVER_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "list_entities",
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {
                        "record_index": 0,
                        "fields": ["screens", "blocks"],
                    }
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
    orch.attempt(
        "Da primeira entidade encontrada, mostre telas e blocos.",
        prior_turns=_prior(),
    )
    select_req = next(
        r
        for r in model.requests
        if r.task_purpose_id == CAPABILITY_SELECTION_INSTRUCTION_ID
    )
    assert "prior_listing" in select_req.input_text
    assert "listed_identifier_count" in select_req.input_text


def test_referential_detail_ordinal_binds_proven_id():
    """GREEN: detail capability + missing id → list resolver → ordinal."""
    provider = FakeProvider(
        "holdout",
        [_group("holdout", "ops", _surface_caps())],
        outcomes={
            ("ops", "list_entities"): _list_outcome(),
            ("ops", "get_entity_context"): _detail_outcome(),
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
                "remote_name": "get_entity_context",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": None,
                "missing_inputs": ["entity_id"],
            },
            RESOLVER_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "list_entities",
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {
                        "record_index": 0,
                        "fields": ["screens", "blocks"],
                    }
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
    attempt = orch.attempt(
        "Da primeira entidade encontrada, mostre as telas e os blocos.",
        prior_turns=_prior(),
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert [c[0] for c in provider.calls] == [
        "list_entities",
        "get_entity_context",
    ]
    assert provider.calls[1][1].get("entity_id") == "ent-alpha-001"
    assert "painel-a" in (attempt.content or "").lower() or (
        "bloco" in (attempt.content or "").lower()
    )


def test_ambiguous_without_ordinal_clarifies():
    provider = FakeProvider(
        "holdout",
        [_group("holdout", "ops", _surface_caps())],
        outcomes={("ops", "list_entities"): _list_outcome()},
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": False,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_entity_context",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": None,
                "missing_inputs": ["entity_id"],
            },
            RESOLVER_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "list_entities",
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Mostre o contexto de uma das entidades.",
        prior_turns=_prior(),
    )
    assert (
        attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    )
    assert [c[0] for c in provider.calls] == ["list_entities"]
    assert "get_entity_context" not in [c[0] for c in provider.calls]


def test_invented_identifier_not_accepted_from_model():
    provider = FakeProvider(
        "holdout",
        [_group("holdout", "ops", _surface_caps())],
        outcomes={("ops", "list_entities"): _list_outcome()},
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": False,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_entity_context",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {"entity_id": "invented-not-in-owner"},
            },
            RESOLVER_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "list_entities",
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Mostre o contexto da entidade.",
        prior_turns=_prior(),
    )
    # Invented id demoted → resolver; without ordinal → clarify.
    assert attempt.status in {
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        GovernedCapabilityStatus.NOT_APPLICABLE,
        GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
    }
    assert "get_entity_context" not in [c[0] for c in provider.calls]


def test_empty_prior_list_does_not_fabricate_detail():
    provider = FakeProvider(
        "holdout",
        [_group("holdout", "ops", _surface_caps())],
        outcomes={
            ("ops", "list_entities"): _outcome(
                "ops",
                "list_entities",
                "vazio",
                structured={"data": {"items": []}},
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
                "remote_name": "get_entity_context",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": None,
                "missing_inputs": ["entity_id"],
            },
            RESOLVER_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "list_entities",
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Da primeira entidade, mostre os blocos.",
        prior_turns=_prior("Nenhuma programação disponível."),
    )
    assert "get_entity_context" not in [c[0] for c in provider.calls]
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS or (
        attempt.outcome is None
    )


def test_message_path_never_acts_on_detail_surface():
    caps = _surface_caps() + [
        _cap(
            "ops",
            "holdout",
            "commit_entity",
            SpecialistOperationClass.ACT,
            schema={
                "type": "object",
                "properties": {
                    "proposal_handle": {"type": "string"},
                    "confirmation": {"type": "boolean"},
                },
                "required": ["proposal_handle", "confirmation"],
            },
        )
    ]
    provider = FakeProvider(
        "holdout",
        [_group("holdout", "ops", caps)],
        outcomes={
            ("ops", "list_entities"): _list_outcome(),
            ("ops", "get_entity_context"): _detail_outcome(),
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
                "remote_name": "get_entity_context",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": None,
                "missing_inputs": ["entity_id"],
            },
            RESOLVER_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "list_entities",
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {"record_index": 0, "fields": ["screens"]}
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
    attempt = orch.attempt(
        "Da primeira entidade encontrada, mostre as telas.",
        prior_turns=_prior(),
    )
    assert "commit_entity" not in [c[0] for c in provider.calls]
    assert attempt.status is GovernedCapabilityStatus.SUCCESS


def test_renamed_detail_capability_still_resolves():
    caps = [
        _cap(
            "ops",
            "holdout",
            "catalog_scan",
            SpecialistOperationClass.READ,
            desc="scan catalog",
        ),
        _cap(
            "ops",
            "holdout",
            "fetch_item_bundle",
            SpecialistOperationClass.READ,
            schema={
                "type": "object",
                "properties": {"item_id": {"type": "string"}},
                "required": ["item_id"],
            },
            desc="bundle for one item",
        ),
    ]
    provider = FakeProvider(
        "holdout",
        [_group("holdout", "ops", caps)],
        outcomes={
            ("ops", "catalog_scan"): _outcome(
                "ops",
                "catalog_scan",
                "list",
                structured={
                    "data": {
                        "items": [
                            {"id": "item-1", "title": "One"},
                            {"id": "item-2", "title": "Two"},
                        ]
                    }
                },
            ),
            ("ops", "fetch_item_bundle"): _outcome(
                "ops",
                "fetch_item_bundle",
                "bundle",
                structured={
                    "data": {
                        "items": [
                            {"item_id": "item-1", "parts": "a,b"}
                        ]
                    }
                },
            ),
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
                "remote_name": "fetch_item_bundle",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": None,
                "missing_inputs": ["item_id"],
            },
            RESOLVER_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "catalog_scan",
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {"record_index": 0, "fields": ["parts"]}
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
    attempt = orch.attempt(
        "Da primeira, mostre as partes.",
        prior_turns=_prior(
            "id: item-1\nname: One\nid: item-2\nname: Two"
        ),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert [c[0] for c in provider.calls] == [
        "catalog_scan",
        "fetch_item_bundle",
    ]
    assert provider.calls[1][1].get("item_id") == "item-1"
