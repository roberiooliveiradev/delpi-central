"""Adaptive capability routing completion — FAST / OPERATIONAL / REASONING.

Bounded characterization of:
- FAST singleton capability selection (no model)
- Native assessment skips that are NOT ``READ ⇒ skip``
- Deterministic schema arguments
- Thin prior-continuation expansion for extraction follow-ups
- Index option ranking for topic relevance
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
    INDEX_SELECT_INSTRUCTION_ID,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _deterministic_arguments_from_schema,
    _extraction_list_from_prior_excerpts,
    _rank_index_options_by_overlap,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    LIMITATION_PRIOR_TURN_CONTINUATION,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ProviderInvocationPayload,
)
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
    model_id="acr-complete", version="1", owner_ref="DELPI"
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
        purpose_ids = {
            GROUP_SELECTION_INSTRUCTION_ID,
            GOAL_INSTRUCTION_ID,
            CAPABILITY_SELECTION_INSTRUCTION_ID,
            ARGUMENTS_INSTRUCTION_ID,
            NATIVE_ASSESSMENT_INSTRUCTION_ID,
            INDEX_SELECT_INSTRUCTION_ID,
            SYNTHESIS_INSTRUCTION_ID,
        }
        for item in items:
            if isinstance(item, dict) and set(item) & purpose_ids:
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
            structured={"ok": True},
        )


def _cap(group_id, provider_id, name, op_class, schema=None, desc=""):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description=desc or name,
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


def test_fast_empty_schema_is_deterministic_arguments():
    """FAST args: empty non-orchestrated schema needs no model propose."""
    guide = _cap(
        "solo",
        "solo_p",
        "get_guide",
        SpecialistOperationClass.READ,
        schema={"type": "object", "properties": {}},
    )
    assert _deterministic_arguments_from_schema(guide) == {}


def test_native_still_runs_for_write_enrichment_path():
    """Write targets must keep native assessment (enrichment may apply)."""
    prepare = _cap(
        "w",
        "wp",
        "prepare_change",
        SpecialistOperationClass.PREPARE,
        schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
    )
    other = _cap(
        "o",
        "op",
        "other_read",
        SpecialistOperationClass.READ,
    )
    providers = [
        FakeProvider("wp", [_group("wp", "w", [prepare])]),
        FakeProvider("op", [_group("op", "o", [other])]),
    ]
    model = FakeProposalModel(
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": "wp:w",
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "prepare_change",
                "goal_class": "create_or_modify",
            },
            NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
            ARGUMENTS_INSTRUCTION_ID: {"arguments": {"x": "1"}},
        }
    )
    orch = OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    orch.attempt("prepare the change now")
    purposes = [r.task_purpose_id for r in model.requests]
    assert NATIVE_ASSESSMENT_INSTRUCTION_ID in purposes


def test_native_skipped_when_comparison_already_declared():
    left = _cap("a", "ap", "read_a", SpecialistOperationClass.READ)
    right = _cap("b", "bp", "read_b", SpecialistOperationClass.READ)
    providers = [
        FakeProvider(
            "ap",
            [_group("ap", "a", [left])],
            outcomes={
                ("a", "read_a"): SpecialistOutcome(
                    status=SpecialistResultStatus.COMPLETED,
                    provenance=SpecialistResultProvenance(
                        specialist_id="a",
                        remote_name="read_a",
                        protocol=InteropProtocol.MCP,
                        correlation_id="c",
                        observed_at="2026-01-01T00:00:00+00:00",
                    ),
                    content_text="a",
                    structured={"value": 1},
                )
            },
        ),
        FakeProvider(
            "bp",
            [_group("bp", "b", [right])],
            outcomes={
                ("b", "read_b"): SpecialistOutcome(
                    status=SpecialistResultStatus.COMPLETED,
                    provenance=SpecialistResultProvenance(
                        specialist_id="b",
                        remote_name="read_b",
                        protocol=InteropProtocol.MCP,
                        correlation_id="c",
                        observed_at="2026-01-01T00:00:00+00:00",
                    ),
                    content_text="b",
                    structured={"value": 2},
                )
            },
        ),
    ]
    model = FakeProposalModel(
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": "ap:a",
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "read_a",
                "goal_class": "compare",
                "comparison_requested": True,
            },
            # Foreign selection may run; native must not.
        }
    )
    orch = OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    orch.attempt("compare a and b sources")
    purposes = [r.task_purpose_id for r in model.requests]
    assert NATIVE_ASSESSMENT_INSTRUCTION_ID not in purposes


def test_native_still_runs_for_plain_read_multi_group():
    left = _cap("a", "ap", "read_a", SpecialistOperationClass.READ)
    right = _cap("b", "bp", "read_b", SpecialistOperationClass.READ)
    providers = [
        FakeProvider(
            "ap",
            [_group("ap", "a", [left])],
            outcomes={
                ("a", "read_a"): SpecialistOutcome(
                    status=SpecialistResultStatus.COMPLETED,
                    provenance=SpecialistResultProvenance(
                        specialist_id="a",
                        remote_name="read_a",
                        protocol=InteropProtocol.MCP,
                        correlation_id="c",
                        observed_at="2026-01-01T00:00:00+00:00",
                    ),
                    content_text="a",
                    structured={"value": 1},
                )
            },
        ),
        FakeProvider("bp", [_group("bp", "b", [right])]),
    ]
    model = FakeProposalModel(
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": "ap:a",
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "read_a",
                "goal_class": "read",
                "comparison_requested": False,
            },
            NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        }
    )
    orch = OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    orch.attempt("read value from a")
    assert NATIVE_ASSESSMENT_INSTRUCTION_ID in {
        r.task_purpose_id for r in model.requests
    }


def test_deterministic_args_single_enum_and_default():
    cap = _cap(
        "g",
        "p",
        "run",
        SpecialistOperationClass.READ,
        schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["safe"]},
                "flag": {"type": "boolean", "default": False},
            },
            "required": ["mode"],
        },
    )
    assert _deterministic_arguments_from_schema(cap) == {
        "mode": "safe",
        "flag": False,
    }


def test_opaque_methodology_schema_still_model_required():
    cap = _cap(
        "teo",
        "teo",
        "get_methodology_guide",
        SpecialistOperationClass.READ,
        schema={
            "type": "object",
            "properties": {
                "method": {"type": "string"},
                "task": {"type": "string"},
                "context": {"type": "object"},
            },
        },
    )
    assert _deterministic_arguments_from_schema(cap) is None


def test_thin_prior_continuation_expands_extraction_list():
    prior_body = "\n\n".join(
        [
            "- Levantar sintoma observado",
            "- Mapear processo afetado",
            "- Coletar evidências objetivas",
            "- Separar fato de hipótese",
            "Texto longo de contexto metodológico adicional aqui.",
        ]
    )
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Como conduzir análise de causas?",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=prior_body,
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    guide = _cap(
        "solo",
        "solo_p",
        "get_guide",
        SpecialistOperationClass.READ,
    )
    provider = FakeProvider("solo_p", [_group("solo_p", "solo", [guide])])
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": True,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_guide",
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [{"record_index": 0, "fields": ["excerpt"]}],
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
        "Com base nessa orientação, quais informações preciso levantar?",
        prior_turns=prior,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert LIMITATION_PRIOR_TURN_CONTINUATION in attempt.limitations
    assert provider.calls == []
    assert attempt.content is not None
    assert len(attempt.content) >= 120
    assert "Levantar sintoma" in attempt.content
    assert "Mapear processo" in attempt.content


def test_rank_index_options_prefers_lexical_overlap():
    options = (
        {"identifier": "display_formats", "label": "Formatos"},
        {"identifier": "legibility", "label": "Legibilidade de painel"},
        {"identifier": "color", "label": "Cores"},
    )
    ranked = _rank_index_options_by_overlap(
        "critérios de legibilidade para painéis",
        options,
    )
    assert ranked[0]["identifier"] == "legibility"


def test_extraction_helper_builds_bullet_list():
    records = (
        {"excerpt": "- Um"},
        {"excerpt": "- Dois"},
        {"excerpt": "nota solta"},
    )
    text = _extraction_list_from_prior_excerpts(records)
    assert text is not None
    assert "Um" in text and "Dois" in text


def test_write_ambiguous_still_clarifies_without_act():
    prepare = _cap(
        "w",
        "wp",
        "prepare_change",
        SpecialistOperationClass.PREPARE,
        schema={"type": "object", "properties": {"x": {"type": "string"}}},
    )
    provider = FakeProvider("wp", [_group("wp", "w", [prepare])])
    model = FakeProposalModel(
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "prepare_change",
                "goal_class": "clarify",
            }
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt("cria ou só me explica?")
    assert (
        attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    )
    assert provider.calls == []
