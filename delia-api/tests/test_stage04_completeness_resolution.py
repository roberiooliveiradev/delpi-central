"""Stage 04 — completeness, resolution, minimal dialogue (bounded).

TASK: DELIA-C3-STAGE03-CLOSURE-AND-STAGE04-IMPLEMENTATION-01 / Stage 04

Provider-neutral proofs: nested required, owner entity_schemas, defaults,
invented-id reject, ambiguity clarify, no ACT on incomplete PREPARE.
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
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _argument_completeness_gaps,
    _apply_owner_declared_defaults,
    _owner_entity_completeness_gaps,
    _schema_required_gaps,
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
    model_id="stage04-model", version="1", owner_ref="DELPI"
)

PROVIDER_ID = "nova-ops-registry"
GROUP_ID = "ops"

_PURPOSE_IDS = frozenset(
    {
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        GOAL_INSTRUCTION_ID,
        SYNTHESIS_INSTRUCTION_ID,
    }
)


class FakeProposalModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposal):
        items = list(proposal) if isinstance(proposal, list) else [proposal]
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
            correlation_id="s04",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=text,
        structured=structured,
    )


def _select(remote_name, arguments=None, *, extra=None):
    proposal = {
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": f"{PROVIDER_ID}:{GROUP_ID}",
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": remote_name,
        },
        ARGUMENTS_INSTRUCTION_ID: {"arguments": arguments or {}},
        GOAL_INSTRUCTION_ID: {"goal_class": "create_or_modify"},
    }
    if extra:
        proposal.update(extra)
    return proposal


_NESTED_SCHEMA = {
    "type": "object",
    "properties": {
        "changes": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "scope": {
                    "type": "object",
                    "properties": {"unit_id": {"type": "string"}},
                    "required": ["unit_id"],
                },
            },
            "required": ["name", "scope"],
        }
    },
    "required": ["changes"],
}


def test_nested_schema_required_gaps_detect_inner_unit():
    gaps = _schema_required_gaps(
        {"changes": {"name": "Nova operação", "scope": {}}},
        _NESTED_SCHEMA,
    )
    assert "changes.scope.unit_id" in gaps


def test_nested_schema_complete_has_no_gaps():
    gaps = _schema_required_gaps(
        {
            "changes": {
                "name": "Nova operação",
                "scope": {"unit_id": "U-1"},
            }
        },
        _NESTED_SCHEMA,
    )
    assert gaps == []


def test_owner_entity_schema_gap_without_domain_rules():
    structured = {
        "data": {
            "entity_schemas": {
                "process": {
                    "required": ["nome_processo", "status_processo"],
                    "defaults": {},
                }
            }
        }
    }
    gaps = _owner_entity_completeness_gaps(
        {
            "entity": "process",
            "operation": "create",
            "changes": {"nome_processo": "Avaliação"},
        },
        structured,
    )
    assert "status_processo" in gaps


def test_owner_declared_default_fills_only_published_keys():
    filled = _apply_owner_declared_defaults(
        {"nome_processo": "X"},
        {
            "required": ["nome_processo", "status_processo"],
            "defaults": {"status_processo": "em_implantacao"},
        },
    )
    assert filled["status_processo"] == "em_implantacao"
    assert "invented" not in filled


def test_prepare_incomplete_entity_clarifies_without_act():
    caps = [
        _cap(
            "get_catalog",
            SpecialistOperationClass.DISCOVERY,
            desc="catalog",
        ),
        _cap(
            "stage_record",
            SpecialistOperationClass.PREPARE,
            schema={
                "type": "object",
                "properties": {
                    "entity": {"type": "string"},
                    "operation": {"type": "string"},
                    "changes": {"type": "object"},
                },
                "required": ["entity", "operation", "changes"],
            },
            desc="prepare record",
        ),
        _cap(
            "commit_record",
            SpecialistOperationClass.ACT,
            schema={
                "type": "object",
                "properties": {
                    "proposal_handle": {"type": "string"},
                    "confirmation": {"type": "boolean"},
                },
                "required": ["proposal_handle", "confirmation"],
            },
            desc="commit",
        ),
    ]
    provider = FakeProvider(
        PROVIDER_ID,
        [_group(caps)],
        outcomes={
            ("ops", "get_catalog"): _outcome(
                "get_catalog",
                "catalog",
                structured={
                    "data": {
                        "entity_schemas": {
                            "process": {
                                "required": [
                                    "nome_processo",
                                    "status_processo",
                                ],
                                "defaults": {},
                            }
                        }
                    }
                },
            ),
        },
    )
    model = FakeProposalModel(
        _select(
            "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {"nome_processo": "Avaliação de eficiência"},
            },
        )
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Prepare o cadastro de um processo com o nome "
        "'Avaliação de eficiência'. Não aplique.",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert [c[0] for c in provider.calls] == ["get_catalog"]
    assert "commit_record" not in [c[0] for c in provider.calls]


def test_prepare_complete_entity_reaches_prepare_not_act_on_message():
    caps = [
        _cap(
            "get_catalog",
            SpecialistOperationClass.DISCOVERY,
            desc="catalog",
        ),
        _cap(
            "stage_record",
            SpecialistOperationClass.PREPARE,
            schema={
                "type": "object",
                "properties": {
                    "entity": {"type": "string"},
                    "operation": {"type": "string"},
                    "changes": {"type": "object"},
                },
                "required": ["entity", "operation", "changes"],
            },
            desc="prepare record",
        ),
        _cap(
            "commit_record",
            SpecialistOperationClass.ACT,
            schema={
                "type": "object",
                "properties": {
                    "proposal_handle": {"type": "string"},
                    "confirmation": {"type": "boolean"},
                },
                "required": ["proposal_handle", "confirmation"],
            },
            desc="commit",
        ),
    ]
    provider = FakeProvider(
        PROVIDER_ID,
        [_group(caps)],
        outcomes={
            ("ops", "get_catalog"): _outcome(
                "get_catalog",
                "catalog",
                structured={
                    "data": {
                        "entity_schemas": {
                            "process": {
                                "required": [
                                    "nome_processo",
                                    "status_processo",
                                ],
                                "defaults": {},
                            }
                        }
                    }
                },
            ),
            ("ops", "stage_record"): _outcome(
                "stage_record",
                "ready",
                structured={
                    "data": {
                        "capability": "stage_record",
                        "proposal_handle": "h1",
                        "ready": True,
                        "validation_result": {"ready": True},
                        "confirmation_requirement": {
                            "explicit_user_confirmation": True,
                        },
                        "exact_change": {
                            "entity": "process",
                            "operation": "create",
                        },
                    }
                },
            ),
        },
    )
    model = FakeProposalModel(
        _select(
            "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {
                    "nome_processo": "Avaliação de eficiência",
                    "status_processo": "ativo",
                },
            },
        )
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Prepare o cadastro de um processo completo. Não aplique.",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    assert [c[0] for c in provider.calls] == ["get_catalog", "stage_record"]
    assert "commit_record" not in [c[0] for c in provider.calls]


def test_argument_completeness_helper_rejects_invented_only_via_gaps():
    descriptor = _cap(
        "stage_record",
        SpecialistOperationClass.PREPARE,
        schema={
            "type": "object",
            "properties": {
                "entity": {"type": "string"},
                "changes": {"type": "object"},
            },
            "required": ["entity", "changes"],
        },
    )
    gaps = _argument_completeness_gaps(
        {
            "entity": "process",
            "changes": {"nome_processo": "X"},
        },
        descriptor,
        {
            "data": {
                "entity_schemas": {
                    "process": {"required": ["nome_processo", "filial_id"]}
                }
            }
        },
    )
    assert "filial_id" in gaps
    assert "nome_processo" not in gaps
