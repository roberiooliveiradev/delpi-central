"""Governed iterative MCP index probe — unseen provider generalization.

TASK: DELIA-C3-MCP-ITERATIVE-TOOL-ORCHESTRATION-FIX-01

Provider ``orion-knowledge-service`` was not used in Stage 03 fixtures.
Proves INDEX READ → GUIDANCE READ without provider/field hardcode, and
that required free-text search still never triggers speculative
discovery (RW-S03-01 preserved).
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
    INDEX_PROBE_INSTRUCTION_ID,
    INDEX_SELECT_INSTRUCTION_ID,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _contract_declares_omit_returns_index,
    _eligible_self_index_probe,
    _index_declared_identifiers,
    _post_self_index_argument_gaps,
    _requires_owner_vocabulary,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
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
    model_id="orion-iterative-model", version="1", owner_ref="DELPI"
)

_PURPOSE_IDS = frozenset(
    {
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        GOAL_INSTRUCTION_ID,
        SYNTHESIS_INSTRUCTION_ID,
        INDEX_PROBE_INSTRUCTION_ID,
        INDEX_SELECT_INSTRUCTION_ID,
    }
)

PROVIDER_ID = "orion-knowledge-service"
GROUP_ID = "knowledge"

GUIDE_BODY = (
    "Para registrar uma inspeção: abra Inspeções, escolha o equipamento, "
    "preencha checklist e salve como rascunho antes da aprovação."
)


class FakeProposalModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposal):
        items = list(proposal) if isinstance(proposal, list) else [proposal]
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        for item in items:
            if isinstance(item, dict) and set(item) & _PURPOSE_IDS:
                for purpose, payload in item.items():
                    self._queues.setdefault(purpose, []).append(payload)
            else:
                self._generic.append(item)
        self._last: dict[str, object] = {}

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
        # Self-index: empty args → index outcome when registered under
        # a dedicated key, else fall through to named outcomes.
        if not arguments and (key + ("__index__",)) in self._outcomes:
            return self._outcomes[key + ("__index__",)]
        if not arguments and (key, "index") in self._outcomes:
            return self._outcomes[(key, "index")]
        outcome = self._outcomes.get(key)
        if outcome is not None:
            # Dynamic: empty vs filled for same remote
            if isinstance(outcome, dict) and "index" in outcome:
                if not arguments:
                    return outcome["index"]
                return outcome["filled"]
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


def _cap(name, op_class, schema=None, desc=""):
    return ProviderCapability(
        capability_id=f"{GROUP_ID}.{name}",
        group_id=GROUP_ID,
        provider_id=PROVIDER_ID,
        remote_name=name,
        owner=GROUP_ID,
        operation_class=op_class,
        description=desc,
        input_schema=schema or {"type": "object", "properties": {}},
        binding={"ref": name},
    )


def _group(capabilities):
    return CapabilityGroup(
        provider_id=PROVIDER_ID,
        group_id=GROUP_ID,
        owner_ref=GROUP_ID,
        display_name=GROUP_ID,
        capabilities=tuple(capabilities),
        source=SourceRef(
            source_id=GROUP_ID,
            source_system=GROUP_ID,
            provider_name=GROUP_ID,
        ),
    )


def _outcome(remote_name, text, structured=None):
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id=GROUP_ID,
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="orion",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=text,
        structured=structured,
    )


def _select(
    remote_name,
    arguments=None,
    *,
    probe_index=None,
    index_select=None,
    extra=None,
):
    proposal = {
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": GROUP_ID,
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": remote_name,
        },
        ARGUMENTS_INSTRUCTION_ID: {"arguments": arguments or {}},
        GOAL_INSTRUCTION_ID: {
            "goal_class": "read",
            "business_subject": "inspeção",
        },
    }
    if probe_index is not None:
        proposal[INDEX_PROBE_INSTRUCTION_ID] = {
            "probe_index": probe_index
        }
    if index_select is not None:
        proposal[INDEX_SELECT_INSTRUCTION_ID] = index_select
    elif isinstance(arguments, dict):
        # Default post-index bind: first non-empty free-string value.
        for field, value in arguments.items():
            if isinstance(value, str) and value.strip():
                proposal[INDEX_SELECT_INSTRUCTION_ID] = {
                    "selected_identifier": value,
                    "argument_field": field,
                }
                break
    if extra:
        proposal.update(extra)
    return proposal


_GUIDE_SCHEMA = {
    "type": "object",
    # Free optional string (not *id) — mirrors owner guide-topic contracts.
    "properties": {"topic": {"type": "string"}},
}
_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {"search_query": {"type": "string"}},
    "required": ["search_query"],
}


def test_eligible_self_index_structural_gates():
    guide = _cap(
        "get_inspection_guide",
        SpecialistOperationClass.READ,
        schema=_GUIDE_SCHEMA,
    )
    nullable = _cap(
        "get_product_guide",
        SpecialistOperationClass.READ,
        schema={
            "type": "object",
            "properties": {
                "topic": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                },
                "section": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                },
            },
        },
    )
    search = _cap(
        "search_publications",
        SpecialistOperationClass.READ,
        schema=_SEARCH_SCHEMA,
    )
    envelope = _cap(
        "apply_ops",
        SpecialistOperationClass.READ,
        schema={
            "type": "object",
            "properties": {"ops": {"type": "object"}},
            "required": ["ops"],
        },
    )
    assert _eligible_self_index_probe(guide) is True
    assert _eligible_self_index_probe(nullable) is True
    assert _eligible_self_index_probe(search) is False
    assert _requires_owner_vocabulary(envelope) is True
    assert _eligible_self_index_probe(envelope) is False


def test_orion_unseen_mcp_index_then_grounded_guide():
    guide = _cap(
        "get_inspection_guide",
        SpecialistOperationClass.READ,
        schema=_GUIDE_SCHEMA,
        desc=(
            "READ-only inspection how-to guides. Omit topic to return "
            "the index of available guides; with topic return that "
            "guide body. Never executes writes."
        ),
    )
    index = _outcome(
        "get_inspection_guide",
        "index",
        structured={
            "data": {
                "items": [
                    {
                        "topic": "equipment_inspection",
                        "label": "Inspeção de equipamentos",
                        "summary": "registrar checklist equipamentos",
                    },
                    {
                        "topic": "safety_walkthrough",
                        "label": "Safety walkthrough",
                    },
                ]
            }
        },
    )
    filled = _outcome(
        "get_inspection_guide",
        "guide",
        structured={
            "data": {
                "items": [
                    {
                        "topic": "equipment_inspection",
                        "content": GUIDE_BODY,
                    }
                ]
            }
        },
    )
    provider = FakeProvider(
        PROVIDER_ID,
        [_group([guide])],
        outcomes={
            ("knowledge", "get_inspection_guide"): {
                "index": index,
                "filled": filled,
            }
        },
    )
    model = FakeProposalModel(
        _select(
            "get_inspection_guide",
            arguments={"topic": "equipment_inspection"},
            probe_index=True,
            extra={
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["content"]}
                    ]
                }
            },
        )
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Como faço para registrar uma inspeção de equipamentos?"
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert [c[0] for c in provider.calls] == [
        "get_inspection_guide",
        "get_inspection_guide",
    ]
    assert provider.calls[0][1] == {}
    assert provider.calls[1][1] == {"topic": "equipment_inspection"}
    assert "Inspeções" in (attempt.content or "")
    assert "checklist" in (attempt.content or "")
    select_payloads = [
        r.input_text
        for r in model.requests
        if r.task_purpose_id == INDEX_SELECT_INSTRUCTION_ID
    ]
    assert select_payloads
    assert "owner_index_options" in select_payloads[-1]
    assert "equipment_inspection" in select_payloads[-1]
    from app.application.capability_provision import orchestration as orch_mod
    src = open(orch_mod.__file__, encoding="utf-8").read()
    assert "orion-knowledge-service" not in src
    assert "get_inspection_guide" not in src
    assert 'remote_name == "get_product_guide"' not in src
    assert 'if name == "topic"' not in src


def test_post_index_empty_args_do_not_reinvoke_index():
    """After INDEX READ, {} must not re-fetch the index as grounded."""
    guide = _cap(
        "get_inspection_guide",
        SpecialistOperationClass.READ,
        schema=_GUIDE_SCHEMA,
        desc=(
            "Omit topic to return the index of available guides; "
            "with topic return the guide body."
        ),
    )
    index = _outcome(
        "get_inspection_guide",
        "index",
        structured={
            "data": {"items": [{"topic": "equipment_inspection"}]}
        },
    )
    provider = FakeProvider(
        PROVIDER_ID,
        [_group([guide])],
        outcomes={
            ("knowledge", "get_inspection_guide"): {"index": index}
        },
    )
    model = FakeProposalModel(
        _select(
            "get_inspection_guide",
            arguments={},
            probe_index=False,
            index_select={
                "selected_identifier": None,
                "argument_field": None,
            },
        )
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Como faço para registrar uma inspeção de equipamentos?"
    )
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert provider.calls == [("get_inspection_guide", {})]
    assert GUIDE_BODY not in (attempt.content or "")


def test_post_index_invented_identifier_rejected():
    guide = _cap(
        "get_inspection_guide",
        SpecialistOperationClass.READ,
        schema=_GUIDE_SCHEMA,
        desc=(
            "Omit topic to return the index of available guides; "
            "with topic return the guide body."
        ),
    )
    index = _outcome(
        "get_inspection_guide",
        "index",
        structured={
            "data": {"items": [{"topic": "equipment_inspection"}]}
        },
    )
    provider = FakeProvider(
        PROVIDER_ID,
        [_group([guide])],
        outcomes={
            ("knowledge", "get_inspection_guide"): {"index": index}
        },
    )
    model = FakeProposalModel(
        _select(
            "get_inspection_guide",
            arguments={"topic": "teletransporte_quantico"},
            probe_index=False,
            index_select={
                "selected_identifier": "teletransporte_quantico",
                "argument_field": "topic",
            },
        )
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Como faço para registrar uma inspeção de equipamentos?"
    )
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert provider.calls == [("get_inspection_guide", {})]


def test_required_search_query_never_index_probes_or_catalog():
    caps = [
        _cap(
            "list_topics",
            SpecialistOperationClass.DISCOVERY,
        ),
        _cap(
            "search_publications",
            SpecialistOperationClass.READ,
            schema=_SEARCH_SCHEMA,
            desc="full-text search; search_query is free text",
        ),
    ]
    provider = FakeProvider(
        PROVIDER_ID,
        [_group(caps)],
        outcomes={
            ("knowledge", "search_publications"): _outcome(
                "search_publications",
                "hits",
                structured={
                    "data": {
                        "items": [{"title": "hit on corrosion"}]
                    }
                },
            ),
        },
    )
    model = FakeProposalModel(
        _select(
            "search_publications",
            arguments={"search_query": "corrosão"},
            probe_index=True,  # even if scripted true, eligibility blocks
            extra={
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["title"]}
                    ]
                }
            },
        )
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt("Pesquise publicações sobre corrosão")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert [c[0] for c in provider.calls] == ["search_publications"]
    assert provider.calls[0][1] == {"search_query": "corrosão"}
    # Index probe purpose must not even be consulted when ineligible
    assert not any(
        r.task_purpose_id == INDEX_PROBE_INSTRUCTION_ID
        for r in model.requests
    )


def test_contract_omit_index_runs_even_when_model_probe_false():
    """Owner description omit→index is sufficient; model false must not
    block the governed empty index invoke."""
    guide = _cap(
        "get_inspection_guide",
        SpecialistOperationClass.READ,
        schema=_GUIDE_SCHEMA,
        desc=(
            "Omit topic to return the index of available guides; "
            "with topic return the guide body."
        ),
    )
    assert _contract_declares_omit_returns_index(guide) is True
    index = _outcome(
        "get_inspection_guide",
        "index",
        structured={
            "data": {
                "items": [
                    {
                        "topic": "equipment_inspection",
                        "label": "Inspeção de equipamentos",
                        "summary": "registrar checklist equipamentos",
                    }
                ]
            }
        },
    )
    filled = _outcome(
        "get_inspection_guide",
        "guide",
        structured={
            "data": {
                "items": [
                    {
                        "topic": "equipment_inspection",
                        "content": GUIDE_BODY,
                    }
                ]
            }
        },
    )
    provider = FakeProvider(
        PROVIDER_ID,
        [_group([guide])],
        outcomes={
            ("knowledge", "get_inspection_guide"): {
                "index": index,
                "filled": filled,
            }
        },
    )
    model = FakeProposalModel(
        _select(
            "get_inspection_guide",
            arguments={"topic": "equipment_inspection"},
            probe_index=False,
            extra={
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["content"]}
                    ]
                }
            },
        )
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Como faço para registrar uma inspeção de equipamentos?"
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert provider.calls[0] == ("get_inspection_guide", {})
    assert "checklist" in (attempt.content or "")


def test_probe_index_false_skips_empty_invoke_without_contract_signal():
    guide = _cap(
        "get_inspection_guide",
        SpecialistOperationClass.READ,
        schema=_GUIDE_SCHEMA,
        desc="Read a guide by topic when you already know the topic.",
    )
    provider = FakeProvider(
        PROVIDER_ID,
        [_group([guide])],
        outcomes={
            ("knowledge", "get_inspection_guide"): _outcome(
                "get_inspection_guide",
                "guide",
                structured={
                    "data": {
                        "items": [
                            {
                                "topic": "equipment_inspection",
                                "content": "body",
                            }
                        ]
                    }
                },
            ),
        },
    )
    model = FakeProposalModel(
        _select(
            "get_inspection_guide",
            arguments={"topic": "equipment_inspection"},
            probe_index=False,
            extra={
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["content"]}
                    ]
                }
            },
        )
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt("Como registrar inspeção?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert provider.calls == [
        ("get_inspection_guide", {"topic": "equipment_inspection"})
    ]


def test_atlas_structured_index_binds_exact_id_to_grounded_guide():
    """Unseen provider: topics[] with id/title → select → guide READ."""
    atlas_id = "atlas-handbook-service"
    guide = ProviderCapability(
        capability_id="handbook.read_ops_guide",
        group_id="handbook",
        provider_id=atlas_id,
        remote_name="read_ops_guide",
        owner="handbook",
        operation_class=SpecialistOperationClass.READ,
        description=(
            "Omit guide_key to return the index of available guides; "
            "with guide_key return the guide body."
        ),
        input_schema={
            "type": "object",
            "properties": {"guide_key": {"type": "string"}},
        },
        binding={"ref": "read_ops_guide"},
    )
    group = CapabilityGroup(
        provider_id=atlas_id,
        group_id="handbook",
        owner_ref="handbook",
        display_name="handbook",
        capabilities=(guide,),
        source=SourceRef(
            source_id="handbook",
            source_system="handbook",
            provider_name="handbook",
        ),
    )
    index = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="handbook",
            remote_name="read_ops_guide",
            protocol=InteropProtocol.MCP,
            correlation_id="atlas",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text="index",
        structured={
            "data": {
                "topics": [
                    {
                        "id": "process_registration",
                        "title": "Cadastro de processos",
                        "summary": "Como cadastrar um processo operacional.",
                    },
                    {
                        "id": "baseline",
                        "title": "Baseline",
                        "summary": "Estado de referência.",
                    },
                ]
            }
        },
    )
    body = (
        "Para cadastrar um processo: abra Processos, informe nome e "
        "área, salve o rascunho e envie para revisão."
    )
    filled = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="handbook",
            remote_name="read_ops_guide",
            protocol=InteropProtocol.MCP,
            correlation_id="atlas",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text="guide",
        structured={
            "data": {
                "items": [
                    {
                        "id": "process_registration",
                        "content": body,
                    }
                ]
            }
        },
    )
    provider = FakeProvider(
        atlas_id,
        [group],
        outcomes={
            ("handbook", "read_ops_guide"): {
                "index": index,
                "filled": filled,
            }
        },
    )
    # FakeProvider._cap helpers use MODULE PROVIDER_ID; patch group
    # selection to handbook group id via custom proposal.
    proposal = {
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": "handbook",
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": "read_ops_guide",
        },
        INDEX_SELECT_INSTRUCTION_ID: {
            "selected_identifier": "process_registration",
            "argument_field": "guide_key",
        },
        GOAL_INSTRUCTION_ID: {
            "goal_class": "read",
            "business_subject": "cadastro de processo",
        },
        SYNTHESIS_INSTRUCTION_ID: {
            "items": [{"record_index": 0, "fields": ["content"]}]
        },
    }
    model = FakeProposalModel(proposal)
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Como faço para cadastrar um processo operacional?"
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert provider.calls[0] == ("read_ops_guide", {})
    assert provider.calls[1] == (
        "read_ops_guide",
        {"guide_key": "process_registration"},
    )
    assert "rascunho" in (attempt.content or "")
    assert "confirmation" not in (attempt.content or "").lower()


def test_description_text_is_not_declared_identifier():
    structured = {
        "data": {
            "topics": [
                {
                    "id": "equipment_inspection",
                    "summary": (
                        "Never use teletransporte_quantico as an id; "
                        "it is only mentioned in this description."
                    ),
                }
            ]
        }
    }
    declared = _index_declared_identifiers(
        structured, ("guide_key", "topic")
    )
    assert declared == frozenset({"equipment_inspection"})
    assert "teletransporte_quantico" not in declared
    gaps = _post_self_index_argument_gaps(
        {"topic": "teletransporte_quantico"},
        _cap(
            "read_guide",
            SpecialistOperationClass.READ,
            schema=_GUIDE_SCHEMA,
        ),
        declared,
    )
    assert "topic" in gaps


def test_post_resolver_nonexistent_id_rejected_by_exact_set():
    declared = frozenset({"process_registration"})
    gaps = _post_self_index_argument_gaps(
        {"guide_key": "not_in_index"},
        ProviderCapability(
            capability_id="h.read",
            group_id="handbook",
            provider_id="atlas-handbook-service",
            remote_name="read_ops_guide",
            owner="handbook",
            operation_class=SpecialistOperationClass.READ,
            description="omit guide_key for index",
            input_schema={
                "type": "object",
                "properties": {"guide_key": {"type": "string"}},
            },
            binding={"ref": "read_ops_guide"},
        ),
        declared,
    )
    assert gaps == ("guide_key",)


def test_index_options_preserve_ids_beyond_resolver_shortlist():
    """Catalog indexes must not truncate to resolver ambiguity size."""
    topics = [
        {"id": f"topic_{i:02d}", "title": f"Title {i}"}
        for i in range(1, 16)
    ]
    topics.append(
        {
            "id": "process_registration",
            "title": "Cadastro de processos",
            "summary": "Como cadastrar um processo.",
        }
    )
    declared = _index_declared_identifiers(
        {"data": {"topics": topics}},
        ("guide_key",),
    )
    assert len(declared) >= 16
    assert "process_registration" in declared
    assert "topic_01" in declared
