"""DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-01.

Baseline reproduction harness — CI-01..CI-18 priority cases on
provider-neutral fake owners whose vocabulary shares nothing with
TÉO/DAVI/VISTA. Model proposals are SCRIPTED to reproduce the exact
sequences observed in production traces (2026-10-15, delpi-delia-api);
deterministic gates and pipeline behavior are the object under test.

Diagnostic labels used in docstrings/comments are report vocabulary
(INTENT_FAILURE, SELECTION_FAILURE, ARGUMENT_COMPLETENESS_FAILURE,
EVIDENCE_SUFFICIENCY_FAILURE, RESPONSE_COMPOSITION_FAILURE,
POLICY_OR_CONTRACT_FAILURE) — not new domain enums.

No PREPARE/ACT is ever executed against a real owner: every provider
here is a fake port; ACT calls are faked or scripted to fail.
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
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _is_open_vocabulary,
    _requires_owner_vocabulary,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import (
    EpistemicClass,
    ModelRef,
    SourceRef,
)
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
    model_id="baseline-model", version="1", owner_ref="DELPI"
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


_PURPOSE_IDS = frozenset(
    {
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        GOAL_INSTRUCTION_ID,
        SYNTHESIS_INSTRUCTION_ID,
    }
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


def _outcome(group_id, remote_name, text, structured=None, limitations=()):
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
        limitations=limitations,
    )


def _select(group_key, remote_name, arguments=None, arg_payload=None,
            extra=None):
    proposal = {
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": group_key,
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": remote_name,
        },
        ARGUMENTS_INSTRUCTION_ID: (
            arg_payload
            if arg_payload is not None
            else {"arguments": arguments or {}}
        ),
    }
    if extra:
        proposal.update(extra)
    return proposal


def _orchestrator(providers, proposal):
    model = FakeProposalModel(proposal)
    return (
        OperationalCapabilityOrchestrator(
            providers,
            invoke_model=InvokeModel(model),
            model_ref=TEST_MODEL_REF,
        ),
        model,
    )


def _proposal_purpose(model, instruction_id):
    return [
        request for request in model.requests
        if request.task_purpose_id == instruction_id
    ]


# ---------------------------------------------------------------------
# CASE A (CI-01/CI-02) — guidance question on an open-vocabulary
# string argument. Production 2026-10-15: "como criar um processo?"
# selected get_product_guide, arguments stage invented topic='processo',
# owner rejected with the available-topics error -> SOURCE_UNAVAILABLE.
# ---------------------------------------------------------------------

_GUIDE_GROUP = ("acme-wiki", "docs")
_GUIDE_SCHEMA = {
    "type": "object",
    "properties": {"topic": {"type": "string"}},
    "required": ["topic"],
}


def _guide_provider(outcomes):
    return FakeProvider(
        _GUIDE_GROUP[0],
        [
            _group(
                _GUIDE_GROUP[0],
                _GUIDE_GROUP[1],
                [
                    _cap(
                        "docs", "acme-wiki", "read_guide",
                        SpecialistOperationClass.READ,
                        schema=_GUIDE_SCHEMA,
                        desc="read the how-to guide for a topic",
                    ),
                ],
            )
        ],
        outcomes=outcomes,
    )


def test_ci01_open_string_field_does_not_trigger_owner_vocabulary():
    """RW-S03-01: a free string on READ is open text, not catalog need.
    Opaque envelopes remain the vocabulary path; optional strings too."""
    descriptor = _cap(
        "docs", "acme-wiki", "read_guide",
        SpecialistOperationClass.READ,
        schema=_GUIDE_SCHEMA,
    )
    assert _is_open_vocabulary(_GUIDE_SCHEMA["properties"]["topic"]) is False
    assert _requires_owner_vocabulary(descriptor) is False
    optional_only = _cap(
        "docs", "acme-wiki", "analyze",
        SpecialistOperationClass.READ,
        schema={
            "type": "object",
            "properties": {"view": {"type": "string"}},
        },
    )
    assert _requires_owner_vocabulary(optional_only) is False


def test_ci01_guidance_question_with_invented_topic_fails():
    """Without a DISCOVERY peer the READ guide still has no vocabulary
    injection — invented topic reaches the owner and fails closed."""
    provider = _guide_provider(
        {
            ("docs", "read_guide"): CapabilityProviderError(
                "mcp_protocol_error",
                "unknown guide topic 'processo'; "
                "available: ['process','revision','dashboard']",
            )
        }
    )
    orch, model = _orchestrator(
        [provider],
        _select("docs", "read_guide", arguments={"topic": "processo"}),
    )
    attempt = orch.attempt("Como criar um processo?")

    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "mcp_protocol_error"
    # No DISCOVERY peer → direct READ invoke with invented value.
    assert provider.calls == [("read_guide", {"topic": "processo"})]
    arg_requests = _proposal_purpose(model, ARGUMENTS_INSTRUCTION_ID)
    assert len(arg_requests) == 1
    payload = arg_requests[0].input_text
    assert "owner_vocabulary" not in payload


def test_ci01_sibling_valid_topic_answers_through_same_path():
    """Positive sibling: a topic inside the owner's vocabulary answers
    — the selection/invoke path is sound; the gap is the missing
    vocabulary for the argument VALUE."""
    provider = _guide_provider(
        {
            ("docs", "read_guide"): _outcome(
                "docs", "read_guide", "guide",
                structured={
                    "data": {
                        "items": [
                            {
                                "topic": "process",
                                "content": "Crie pelo menu Processos.",
                            }
                        ]
                    }
                },
            )
        }
    )
    orch, model = _orchestrator(
        [provider],
        _select(
            "docs", "read_guide",
            arguments={"topic": "process"},
            extra={
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["content"]}
                    ]
                }
            },
        ),
    )
    attempt = orch.attempt("Como criar um processo?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "Processos" in (attempt.content or "")


def test_ci01_goal_class_has_no_orientation_class():
    """Structural evidence: the goal contract cannot represent
    'orient the user' — 'como criar' is forced into an action class."""
    orch, model = _orchestrator(
        [_guide_provider({})],
        _select(
            "docs", "read_guide",
            arguments={"topic": "process"},
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "orient",
                    "business_subject": "processo",
                }
            },
        ),
    )
    provider_outcome = _outcome(
        "docs", "read_guide", "guide",
        structured={
            "data": {"items": [{"content": "texto do guia"}]}
        },
    )
    provider2 = FakeProvider(
        _GUIDE_GROUP[0],
        _guide_provider({})._groups,
        outcomes={("docs", "read_guide"): provider_outcome},
    )
    orch, model = _orchestrator(
        [provider2],
        _select(
            "docs", "read_guide",
            arguments={"topic": "process"},
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "orient",
                    "business_subject": "processo",
                },
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["content"]}
                    ]
                },
            },
        ),
    )
    attempt = orch.attempt("Como criar um processo?")
    # The runtime silently normalizes the unknown class to "read" —
    # no orientation semantic survives the boundary.
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    from app.application.capability_provision.orchestration import (
        OperationalCapabilityOrchestrator as _O,
    )

    assert "orient" not in _O._GOAL_CLASSES


def test_ci01_hazard_guidance_question_can_reach_prepare():
    """Residual hazard (stage-02): the finality gate reconciles the
    write-class selection against the validated goal — but a goal
    proposal that misclassifies a guidance question as
    create_or_modify still reaches the governed write chain. The gate
    depends on semantic interpretation quality; owner governance
    remains the blast-radius bound (SELECTION_FAILURE residual)."""
    provider = FakeProvider(
        "acme-flow",
        [
            _group(
                "acme-flow",
                "registry",
                [
                    _cap(
                        "registry", "acme-flow", "read_guide",
                        SpecialistOperationClass.READ,
                        schema=_GUIDE_SCHEMA,
                        desc="read the how-to guide",
                    ),
                    _cap(
                        "registry", "acme-flow", "stage_record",
                        SpecialistOperationClass.PREPARE,
                        schema={
                            "type": "object",
                            "properties": {
                                "entity": {"type": "string"},
                                "operation": {"type": "string"},
                                "changes": {"type": "object"},
                            },
                            "required": [
                                "entity", "operation", "changes",
                            ],
                        },
                        desc="stage a record change for review",
                    ),
                ],
            )
        ],
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {},
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                }
            },
        ),
    )
    attempt = orch.attempt("Como criar um processo?")
    # A guidance question still reaches the owner PREPARE call when the
    # goal proposal declares action intent — the gate cannot correct a
    # misclassified goal; the fake owner's outcome bounds the blast
    # radius.
    assert ("stage_record", {
        "entity": "process", "operation": "create", "changes": {},
    }) in provider.calls


# ---------------------------------------------------------------------
# CASE B (CI-03..CI-05) — create with inner-entity required field.
# Production trace: prepare selected, get_catalog ran (entity_schemas
# required=[nome_processo, status_processo] inside owner_vocabulary),
# arguments declared complete (missing=0) with changes={'nome_processo'},
# PREPARE READY, owner declared direct execution, ACT commit rejected
# with "status_processo Field required".
# ---------------------------------------------------------------------

_PROCESS_GROUP = ("acme-flow", "registry")

_PROCESS_CAPS = [
    _cap(
        "registry", "acme-flow", "get_catalog",
        SpecialistOperationClass.DISCOVERY,
        desc="list entities, fields and operation vocabulary",
    ),
    _cap(
        "registry", "acme-flow", "stage_record",
        SpecialistOperationClass.PREPARE,
        schema={
            "type": "object",
            "properties": {
                "entity": {"type": "string"},
                "operation": {"type": "string"},
                "record_id": {"type": "string"},
                "changes": {"type": "object"},
            },
            "required": ["entity", "operation", "changes"],
        },
        desc="prepare a governed record change",
    ),
    _cap(
        "registry", "acme-flow", "commit_record",
        SpecialistOperationClass.ACT,
        schema={
            "type": "object",
            "properties": {
                "proposal_handle": {"type": "string"},
                "confirmation": {"type": "boolean"},
            },
            "required": ["proposal_handle", "confirmation"],
        },
        desc="commit a staged change",
    ),
]

_CATALOG_OUTCOME_STRUCTURED = {
    "data": {
        "entity_schemas": {
            "process": {
                "required": ["nome_processo", "status_processo"],
                "enums": {
                    "status_processo": [
                        "ativo", "em_implantacao", "descontinuado",
                    ]
                },
                "defaults": {},
            }
        },
        "operations": {"create": {"entity": "process"}},
    }
}


def _direct_ready_proposal(group_id, remote_name):
    return _outcome(
        group_id,
        remote_name,
        "Proposta pronta.",
        structured={
            "data": {
                "capability": "stage_record",
                "proposal_handle": "prop-handle-x",
                "exact_change": {"entity": "process", "operation": "create"},
                "ready": True,
                "validation_result": {"ready": True},
                "confirmation_requirement": {
                    "explicit_user_confirmation": False,
                },
            }
        },
    )


def _process_provider(commit_outcome=None, prepare_outcome=None):
    outcomes = {
        ("registry", "get_catalog"): _outcome(
            "registry", "get_catalog", "catalog",
            structured=_CATALOG_OUTCOME_STRUCTURED,
        ),
        ("registry", "stage_record"): (
            prepare_outcome or _direct_ready_proposal(
                "registry", "stage_record"
            )
        ),
    }
    if commit_outcome is not None:
        outcomes[("registry", "commit_record")] = commit_outcome
    return FakeProvider("acme-flow", [_group(*_PROCESS_GROUP, _PROCESS_CAPS)],
                      outcomes=outcomes)


def test_ci04_inner_required_field_blocks_prepare_before_act():
    """Stage 04 GREEN: owner entity_schemas required inner fields are
    checked before PREPARE — incomplete ``changes`` clarify; no ACT.
    """
    provider = _process_provider()
    orch, model = _orchestrator(
        [provider],
        _select(
            "registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {"nome_processo": "processo teste"},
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                }
            },
        ),
    )
    attempt = orch.attempt(
        "Crie um processo chamado processo teste",
        actor_user_id="u1",
        session_id="s1",
    )

    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert [name for name, _ in provider.calls] == ["get_catalog"]
    assert "stage_record" not in [name for name, _ in provider.calls]
    assert "commit_record" not in [name for name, _ in provider.calls]
    arg_requests = _proposal_purpose(model, ARGUMENTS_INSTRUCTION_ID)
    stage_arg = [
        r for r in arg_requests
        if "stage_record" in r.input_text
    ]
    assert stage_arg, "arguments proposal for stage_record missing"
    assert "status_processo" in stage_arg[0].input_text


def _apply_pending(orch, attempt, actor="u1", session="s1"):
    """Typed APPLY_PREPARED turn bound to the pending proposal."""
    ctx = attempt.confirmation_context
    return orch.attempt(
        "",
        actor_user_id=actor,
        session_id=session,
        confirmation={
            "decision": "CONFIRM",
            "proposal_digest": ctx["proposal_digest"],
            "preview_fingerprint": ctx["preview_fingerprint"],
            "session_id": ctx["session_id"],
        },
    )


def test_ci03_sibling_complete_changes_commit_directly():
    """Positive sibling: complete inner changes flow through the same
    governed chain — MESSAGE -> PREPARE+pending -> bound APPLY -> ACT —
    the chain itself is sound when the payload is complete."""
    provider = _process_provider(
        commit_outcome=_outcome(
            "registry", "commit_record", "created",
            structured={
                "data": {
                    "entity": "process",
                    "record_id": "PROC-0099",
                    "nome_processo": "processo teste",
                }
            },
        )
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {
                    "nome_processo": "processo teste",
                    "status_processo": "ativo",
                },
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                }
            },
        ),
    )
    attempt = orch.attempt(
        "Crie um processo chamado processo teste",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    assert "commit_record" not in [name for name, _ in provider.calls]
    applied = _apply_pending(orch, attempt)
    assert applied.status is GovernedCapabilityStatus.SUCCESS
    assert [name for name, _ in provider.calls] == [
        "get_catalog", "stage_record", "commit_record",
    ]


def test_ci05_negative_prepare_not_ready_never_reaches_act():
    """Negative sibling: a NOT_READY owner projection renders
    truthfully and the ACT capability is never invoked."""
    provider = _process_provider(
        prepare_outcome=_outcome(
            "registry", "stage_record", "",
            structured={
                "data": {
                    "capability": "stage_record",
                    "ready": False,
                    "missing_fields": ["status_processo"],
                    "validation_result": {"ready": False},
                }
            },
        )
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                # Inner entity completeness satisfied so the owner
                # NOT_READY projection is reached (Stage 04 gate).
                "changes": {
                    "nome_processo": "processo teste",
                    "status_processo": "ativo",
                },
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                }
            },
        ),
    )
    attempt = orch.attempt("Crie um processo chamado processo teste")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "commit_record" not in [name for name, _ in provider.calls]


# ---------------------------------------------------------------------
# CASE C (CI-07/CI-08) — "qual o último cadastrado?": the synthesis
# stage selects WHICH record to show but nothing verifies ordering,
# recency or coverage — EVIDENCE_SUFFICIENCY_FAILURE.
# ---------------------------------------------------------------------

def _unordered_records(with_dates: bool):
    items = []
    for index in range(10):
        record = {
            "codigo": f"REC-{index:04d}",
            "nome": f"Registro {index}",
        }
        if with_dates:
            # 'atualizado_em' is a mutation date, NOT a creation date —
            # ambiguous for "último cadastrado".
            record["atualizado_em"] = f"2026-10-{index + 1:02d}"
        items.append(record)
    return {"data": {"items": items}}


def _list_provider(structured):
    return FakeProvider(
        "acme-flow",
        [
            _group(
                "acme-flow",
                "registry",
                [
                    _cap(
                        "registry", "acme-flow", "list_records",
                        SpecialistOperationClass.READ,
                        schema={"type": "object", "properties": {}},
                        desc="list records",
                    ),
                ],
            )
        ],
        outcomes={
            ("registry", "list_records"): _outcome(
                "registry", "list_records", "records",
                structured=structured,
            )
        },
    )


def test_ci07_last_record_claim_without_ordering_evidence():
    """RED: unordered records with no creation field — the synthesis
    proposal picks an index and the renderer presents it. Nothing
    verifies 'último cadastrado'; the claim's correctness rests on
    model selection alone (EVIDENCE_SUFFICIENCY_FAILURE)."""
    provider = _list_provider(_unordered_records(with_dates=False))
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "list_records",
            extra={
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {
                            "record_index": 9,
                            "fields": ["codigo", "nome"],
                        }
                    ],
                    "presentation": "detail",
                }
            },
        ),
    )
    attempt = orch.attempt("Qual o último processo cadastrado?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    # The selected record is rendered — no ordering/coverage caveat is
    # attached; 'Registro 9' is presented as the answer.
    assert "Registro 9" in (attempt.content or "")
    assert not attempt.limitations


def test_ci08_sibling_with_dates_still_unverified_ordering():
    """Sibling: even with a date field present, the same pipeline
    asserts nothing about ordering semantics — a mutation timestamp
    is silently usable as a creation-order proxy."""
    provider = _list_provider(_unordered_records(with_dates=True))
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "list_records",
            extra={
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {
                            "record_index": 9,
                            "fields": [
                                "codigo", "nome", "atualizado_em",
                            ],
                        }
                    ],
                    "presentation": "detail",
                }
            },
        ),
    )
    attempt = orch.attempt("Qual o último processo cadastrado?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "Registro 9" in (attempt.content or "")


def test_ci07_sibling_empty_selection_is_honest_insufficiency():
    """Stage 05: empty synthesis selection is insufficient evidence —
    honest limitation, not a raw dump of every record."""
    from app.application.interaction.contracts import (
        LIMITATION_INSUFFICIENT_EVIDENCE,
    )

    provider = _list_provider(_unordered_records(with_dates=False))
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "list_records",
            extra={SYNTHESIS_INSTRUCTION_ID: {"items": []}},
        ),
    )
    attempt = orch.attempt("Qual o último processo cadastrado?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "não invento" in (attempt.content or "").lower()
    assert "Registro 9" not in (attempt.content or "")
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations


# ---------------------------------------------------------------------
# CASE D (CI-09) — positive control: single-record factual answer is
# composed deterministically, no synthesis call needed.
# ---------------------------------------------------------------------

def test_ci09_single_leaf_answer_skips_synthesis_proposal():
    provider = FakeProvider(
        "acme-stock",
        [
            _group(
                "acme-stock",
                "items",
                [
                    _cap(
                        "items", "acme-stock", "read_item",
                        SpecialistOperationClass.READ,
                        schema={
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"}
                            },
                            "required": ["code"],
                        },
                        desc="read a single item",
                    ),
                ],
            )
        ],
        outcomes={
            ("items", "read_item"): _outcome(
                "items", "read_item", "item",
                structured={
                    "data": {
                        "items": [
                            {"descricao": "Parafuso sextavado M8"}
                        ]
                    }
                },
            )
        },
    )
    orch, model = _orchestrator(
        [provider],
        _select("items", "read_item", arguments={"code": "10090034"}),
    )
    attempt = orch.attempt("Qual a descrição do produto 10090034?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "Parafuso sextavado M8" in (attempt.content or "")
    # Deterministic composer path — no synthesis proposal consumed.
    assert not _proposal_purpose(model, SYNTHESIS_INSTRUCTION_ID)


# ---------------------------------------------------------------------
# CASE E (CI-10) — rename invariance: identical behavior on a fake
# owner whose names share nothing with the cases above.
# ---------------------------------------------------------------------

def test_ci10_open_vocab_gap_is_name_invariant():
    """Same Case-A defect on a differently-named owner — the gap is
    structural, not coupled to TÉO/DAVI/VISTA vocabulary."""
    provider = FakeProvider(
        "x9-manuals",
        [
            _group(
                "x9-manuals",
                "library",
                [
                    _cap(
                        "library", "x9-manuals", "fetch_chapter",
                        SpecialistOperationClass.READ,
                        schema={
                            "type": "object",
                            "properties": {
                                "section": {"type": "string"}
                            },
                            "required": ["section"],
                        },
                        desc="fetch a documentation chapter",
                    ),
                ],
            )
        ],
        outcomes={
            ("library", "fetch_chapter"): CapabilityProviderError(
                "mcp_protocol_error",
                "unknown chapter 'capitulo-x'",
            )
        },
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "library", "fetch_chapter",
            arguments={"section": "capitulo-x"},
        ),
    )
    attempt = orch.attempt("Como configuro o capítulo X?")
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert provider.calls == [
        ("fetch_chapter", {"section": "capitulo-x"})
    ]


def test_ci10_inner_schema_gap_is_name_invariant():
    """Same Case-B defect: outer schema satisfied, inner entity field
    missing, direct commit rejected — on renamed capabilities."""
    caps = [
        _cap(
            "vault", "x7-core", "describe_surface",
            SpecialistOperationClass.DISCOVERY,
            desc="describe entities",
        ),
        _cap(
            "vault", "x7-core", "propose_mutation",
            SpecialistOperationClass.PREPARE,
            schema={
                "type": "object",
                "properties": {
                    "entity": {"type": "string"},
                    "operation": {"type": "string"},
                    "payload": {"type": "object"},
                },
                "required": ["entity", "operation", "payload"],
            },
            desc="propose a mutation",
        ),
        _cap(
            "vault", "x7-core", "apply_mutation",
            SpecialistOperationClass.ACT,
            schema={
                "type": "object",
                "properties": {
                    "proposal_handle": {"type": "string"},
                    "confirmation": {"type": "boolean"},
                },
                "required": ["proposal_handle", "confirmation"],
            },
            desc="apply a staged mutation",
        ),
    ]
    provider = FakeProvider(
        "x7-core",
        [_group("x7-core", "vault", caps)],
        outcomes={
            ("vault", "describe_surface"): _outcome(
                "vault", "describe_surface", "catalog",
                structured={
                    "data": {
                        "entity_schemas": {
                            "thing": {
                                "required": ["label", "state"],
                                "defaults": {},
                            }
                        }
                    }
                },
            ),
            ("vault", "propose_mutation"): _outcome(
                "vault", "propose_mutation", "ok",
                structured={
                    "data": {
                        "capability": "propose_mutation",
                        "proposal_handle": "h-1",
                        "exact_change": {"entity": "thing", "operation": "create"},
                        "ready": True,
                        "validation_result": {"ready": True},
                        "confirmation_requirement": {
                            "explicit_user_confirmation": False,
                        },
                    }
                },
            ),
            ("vault", "apply_mutation"): CapabilityProviderError(
                "mcp_protocol_error",
                "1 validation error: state Field required",
            ),
        },
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "vault", "propose_mutation",
            arguments={
                "entity": "thing",
                "operation": "create",
                "payload": {"label": "item teste"},
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                }
            },
        ),
    )
    attempt = orch.attempt(
        "Crie um item chamado item teste",
        actor_user_id="u1",
        session_id="s1",
    )
    # Name-invariant Stage 04: incomplete inner payload clarifies;
    # PREPARE/ACT never reached (same structural gate as CI-04).
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert [name for name, _ in provider.calls] == ["describe_surface"]
    assert "propose_mutation" not in [name for name, _ in provider.calls]
    assert "apply_mutation" not in [name for name, _ in provider.calls]


# ---------------------------------------------------------------------
# Budget evidence — model calls per governed path (production turn
# observed 5 model proposals before the write invocation).
# ---------------------------------------------------------------------

def test_budget_model_calls_per_guided_write_path():
    # Second group forces select_group + native_assessment —
    # mirroring the production 3-group topology where 5 model
    # proposals precede the write invocation.
    shadow = FakeProvider(
        "x-shadow",
        [
            _group(
                "x-shadow", "misc",
                [
                    _cap(
                        "misc", "x-shadow", "peek",
                        SpecialistOperationClass.READ,
                    ),
                ],
            )
        ],
    )
    provider = _process_provider(
        commit_outcome=_outcome(
            "registry", "commit_record", "created",
            structured={"data": {"record_id": "R-1"}},
        )
    )
    orch, model = _orchestrator(
        [provider, shadow],
        _select(
            "acme-flow:registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {
                    "nome_processo": "x",
                    "status_processo": "ativo",
                },
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                }
            },
        ),
    )
    attempt = orch.attempt(
        "Crie um processo chamado x",
        actor_user_id="u1",
        session_id="s1",
    )
    # B2 closure (§6.184): the MESSAGE ends at PREPARE + pending scope
    # choice — the bound APPLY turn runs zero extra model proposals.
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    purposes = [r.task_purpose_id for r in model.requests]
    # select_group + select_capability + turn_goal +
    # native_assessment + arguments (target) — discovery args are
    # resolved without a proposal (empty schema short-circuit).
    assert len(purposes) == 5
    assert purposes.count(ARGUMENTS_INSTRUCTION_ID) == 1
    applied = _apply_pending(orch, attempt)
    assert applied.status is GovernedCapabilityStatus.SUCCESS
    assert len(model.requests) == 5


# ---------------------------------------------------------------------
# CASE S2 (DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-02)
# — intent/finality coherence. The validated turn goal is the only
# semantic statement of what the user wants: a write-class target
# (PREPARE/ACT) is structurally incompatible with a non-action goal
# and must be reconciled deterministically before the governed write
# chain runs. Scripted proposals isolate pipeline behavior — the gate
# compares the validated goal class to the owner-declared operation
# class, never to provider/capability names.
# ---------------------------------------------------------------------

_S2_GUIDE_STRUCTURED = {
    "data": {
        "items": [
            {"topic": "process", "content": "Crie pelo menu Processos."}
        ]
    }
}


def _s2_guided_write_caps(
    provider_id="acme-flow", group_id="registry", read_name="read_guide",
    write_name="stage_record",
):
    """One owner surface advertising a guidance READ and a PREPARE —
    the stage-01 hazard shape on neutral vocabulary."""
    return [
        _cap(
            group_id, provider_id, read_name,
            SpecialistOperationClass.READ,
            schema=_GUIDE_SCHEMA,
            desc="read the how-to guide for a topic",
        ),
        _cap(
            group_id, provider_id, write_name,
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
            desc="stage a record change for review",
        ),
    ]


def _s2_guided_write_provider(
    provider_id="acme-flow", group_id="registry",
):
    return FakeProvider(
        provider_id,
        [
            _group(
                provider_id,
                group_id,
                _s2_guided_write_caps(provider_id, group_id),
            )
        ],
        outcomes={
            (group_id, "read_guide"): _outcome(
                group_id, "read_guide", "guide",
                structured=_S2_GUIDE_STRUCTURED,
            ),
        },
    )


def test_s2_orientation_demotes_write_selection_to_read():
    """'Como criar um processo?' — the model selected the PREPARE
    capability while the validated goal is information-seeking. The
    deterministic finality gate must demote the write-class target and
    reselect a non-mutating capability on the same owner surface; the
    write call must never reach the provider."""
    provider = _s2_guided_write_provider()
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "stage_record",
                },
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "read",
                    "business_subject": "processo",
                },
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "read_guide",
                },
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"topic": "process"},
                },
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["content"]}
                    ]
                },
            },
        ],
    )
    attempt = orch.attempt("Como criar um processo?")
    assert [name for name, _ in provider.calls] == ["read_guide"]
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "Processos" in (attempt.content or "")


def test_s2_write_only_surface_never_writes_on_information_goal():
    """'Não execute nada; apenas explique.' on an owner surface that
    advertises ONLY the write capability — there is nothing to demote
    to, so the turn must end truthfully instead of running the write
    by elimination."""
    provider = FakeProvider(
        "acme-flow",
        [
            _group(
                "acme-flow",
                "registry",
                [
                    _cap(
                        "registry", "acme-flow", "stage_record",
                        SpecialistOperationClass.PREPARE,
                        schema={
                            "type": "object",
                            "properties": {
                                "entity": {"type": "string"},
                                "operation": {"type": "string"},
                                "changes": {"type": "object"},
                            },
                            "required": [
                                "entity", "operation", "changes",
                            ],
                        },
                        desc="stage a record change for review",
                    ),
                ],
            )
        ],
    )
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "stage_record",
                },
                GOAL_INSTRUCTION_ID: {"goal_class": "read"},
                # Arguments for the write are satisfiable — without
                # the gate the PREPARE call fires on a negated
                # execution request.
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {
                        "entity": "process",
                        "operation": "create",
                        "changes": {},
                    }
                },
            }
        ],
    )
    attempt = orch.attempt("Não execute nada; apenas explique.")
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE


def test_s2_ambiguous_request_clarifies_without_writing():
    """'Preciso criar um processo.' — the model could not decide
    between guidance and execution (goal_class=clarify) yet selected
    a write capability. The gate must ask a proportional business
    clarification instead of presuming material intent."""
    provider = _s2_guided_write_provider()
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "stage_record",
                },
                GOAL_INSTRUCTION_ID: {"goal_class": "clarify"},
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {
                        "entity": "process",
                        "operation": "create",
                        "changes": {},
                    }
                },
            }
        ],
    )
    attempt = orch.attempt("Preciso criar um processo.")
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    content = attempt.content or ""
    assert content
    assert "stage_record" not in content


def test_s2_explicit_create_keeps_governed_write_path():
    """Positive control: goal=create_or_modify with a write selection
    is compatible — the governed chain (discovery -> prepare -> bound
    APPLY -> ACT) runs; a MESSAGE alone never commits."""
    provider = _process_provider(
        commit_outcome=_outcome(
            "registry", "commit_record", "created",
            structured={"data": {"record_id": "R-1"}},
        )
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {
                    "nome_processo": "x",
                    "status_processo": "ativo",
                },
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                    "business_subject": "processo",
                }
            },
        ),
    )
    attempt = orch.attempt(
        "Quero que você cadastre um processo x",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    assert "commit_record" not in [name for name, _ in provider.calls]
    applied = _apply_pending(orch, attempt)
    assert applied.status is GovernedCapabilityStatus.SUCCESS
    assert [name for name, _ in provider.calls] == [
        "get_catalog", "stage_record", "commit_record",
    ]


def test_s2_prepare_only_request_stops_at_confirmation():
    """'Prepare um cadastro, mas não aplique.' — action intent reaches
    PREPARE; the owner seals explicit user confirmation and no ACT
    call happens before the user confirms. Write governance is
    unchanged by the intent layer."""
    provider = _process_provider(
        prepare_outcome=_outcome(
            "registry", "stage_record", "",
            structured={
                "data": {
                    "capability": "stage_record",
                    "proposal_handle": "h-9",
                    "exact_change": {
                        "entity": "process",
                        "operation": "create",
                    },
                    "ready": True,
                    "validation_result": {"ready": True},
                    "confirmation_requirement": {
                        "explicit_user_confirmation": True,
                    },
                }
            },
        )
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {
                    "nome_processo": "x",
                    "status_processo": "ativo",
                },
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                }
            },
        ),
    )
    attempt = orch.attempt("Prepare um cadastro, mas não aplique.")
    assert attempt.status is (
        GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    )
    assert "commit_record" not in [name for name, _ in provider.calls]


def test_s2_prior_action_turns_do_not_escalate_guidance():
    """Multi-turn coherence: a prior turn that executed a change must
    not convert a later 'how do I' question into a write — the
    validated goal of THIS turn governs compatibility."""
    provider = _s2_guided_write_provider()
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "stage_record",
                },
                GOAL_INSTRUCTION_ID: {"goal_class": "read"},
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "read_guide",
                },
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"topic": "process"},
                },
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["content"]}
                    ]
                },
            },
        ],
    )
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Crie um processo chamado x",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="Processo criado.",
        ),
    )
    attempt = orch.attempt(
        "Como criar um processo?", prior_turns=prior
    )
    assert [name for name, _ in provider.calls] == ["read_guide"]


def test_s2_intent_gate_is_name_invariant():
    """Same demotion on differently-named owner/tools — the gate
    compares the validated goal class to the owner-declared operation
    class, never to names."""
    provider = FakeProvider(
        "x9-manuals",
        [
            _group(
                "x9-manuals",
                "library",
                _s2_guided_write_caps(
                    "x9-manuals", "library",
                    read_name="fetch_chapter",
                    write_name="propose_mutation",
                ),
            )
        ],
        outcomes={
            ("library", "fetch_chapter"): _outcome(
                "library", "fetch_chapter", "chapter",
                structured={
                    "data": {
                        "items": [
                            {
                                "section": "creation",
                                "content": "Capítulo de criação.",
                            }
                        ]
                    }
                },
            ),
        },
    )
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "propose_mutation",
                },
                GOAL_INSTRUCTION_ID: {"goal_class": "read"},
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "fetch_chapter",
                },
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"topic": "creation"},
                },
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 0, "fields": ["content"]}
                    ]
                },
            },
        ],
    )
    attempt = orch.attempt("Quais são as etapas para criar?")
    assert [name for name, _ in provider.calls] == ["fetch_chapter"]
    assert attempt.status is GovernedCapabilityStatus.SUCCESS


def test_s2r1_uninterpreted_goal_never_promotes_write():
    """B1 (§6.174): 'Você consegue criar?' is an ability/information
    question — an ABSENT goal interpretation is not evidence of a
    change request. A write-class selection with no validated goal
    must not silently proceed to PREPARE; the honest bounded path is
    a proportional clarification ask-back."""
    provider = _s2_guided_write_provider()
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "stage_record",
                },
                # No GOAL payload — no declared interpretation.
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {
                        "entity": "process",
                        "operation": "create",
                        "changes": {},
                    }
                },
            },
        ],
    )
    attempt = orch.attempt("Você consegue criar?")
    assert provider.calls == []
    assert attempt.status is (
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    )


def test_s2r1_invalid_goal_guidance_never_writes():
    """B1 (§6.174): 'Como criar um processo?' with a goal proposal
    that carries a surplus unknown key — keys are stripped, the
    declared read class is kept, and the PREPARE selection must not
    execute. Zero write-class invocation."""
    provider = _s2_guided_write_provider()
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "stage_record",
                },
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "read",
                    # Surplus key is stripped; goal_class remains.
                    "invented_field": True,
                },
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {
                        "entity": "process",
                        "operation": "create",
                        "changes": {},
                    }
                },
            },
        ],
    )
    attempt = orch.attempt("Como criar um processo?")
    assert provider.calls == []
    assert attempt.status in (
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        GovernedCapabilityStatus.NOT_APPLICABLE,
    )
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS


def test_s2r1_uninterpreted_write_only_surface_never_writes():
    """B1-05 (§6.174): owner surface with ONLY write-class
    capabilities + absent goal — no write by elimination, and no
    safe non-mutating alternative exists to demote to."""
    provider = FakeProvider(
        "acme-flow",
        [
            _group(
                "acme-flow",
                "registry",
                [
                    _cap(
                        "registry", "acme-flow", "stage_record",
                        SpecialistOperationClass.PREPARE,
                        schema={
                            "type": "object",
                            "properties": {
                                "entity": {"type": "string"},
                                "operation": {"type": "string"},
                                "changes": {"type": "object"},
                            },
                            "required": [
                                "entity", "operation", "changes",
                            ],
                        },
                        desc="stage a record change for review",
                    ),
                ],
            )
        ],
    )
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "stage_record",
                },
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {
                        "entity": "process",
                        "operation": "create",
                        "changes": {},
                    }
                },
            }
        ],
    )
    attempt = orch.attempt("Você consegue cadastrar?")
    assert provider.calls == []
    assert attempt.status is (
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    )


def test_s2r1_uninterpreted_gate_is_name_invariant():
    """B1 on a fully renamed owner/capability surface — the gate
    reacts to operation class and declared goal only, never to
    provider or remote names."""
    provider = FakeProvider(
        "x9-manuals",
        [
            _group(
                "x9-manuals",
                "library",
                _s2_guided_write_caps(
                    "x9-manuals", "library",
                    read_name="fetch_chapter",
                    write_name="propose_mutation",
                ),
            )
        ],
    )
    orch, _ = _orchestrator(
        [provider],
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "propose_mutation",
                },
                # No GOAL payload.
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {
                        "entity": "process",
                        "operation": "create",
                        "changes": {},
                    }
                },
            },
        ],
    )
    attempt = orch.attempt("Você consegue alterar?")
    assert provider.calls == []
    assert attempt.status is (
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    )


def test_s2r1_prepare_only_bound_blocks_direct_act():
    """B2-01 (§6.174): 'Prepare um cadastro, mas não aplique.' — the
    validated goal declares action intent AND an explicit
    prepare_only execution bound. With request ceiling None and an
    owner that seals explicit_user_confirmation=False (direct
    governed continuation), the textual bound must still cap the
    turn: PREPARE may run, ACT must never be invoked."""
    provider = _process_provider(
        commit_outcome=_outcome(
            "registry", "commit_record", "created",
            structured={"data": {"record_id": "R-1"}},
        )
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {
                    "nome_processo": "x",
                    "status_processo": "ativo",
                },
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                    "execution_bound": "prepare_only",
                }
            },
        ),
    )
    attempt = orch.attempt(
        "Prepare um cadastro, mas não aplique."
    )
    assert attempt.status is (
        GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    )
    assert "commit_record" not in [
        name for name, _ in provider.calls
    ]
    assert "stage_record" in [name for name, _ in provider.calls]


def test_s2r1_execution_bound_semantic_variants():
    """B2-06 (§6.174): equivalent formulations of an explicit
    prepare-only bound produce the same capped outcome — the bound
    comes from the validated goal interpretation, not keyword
    matching."""
    phrases = (
        "Somente prepare a alteração.",
        "Monte a proposta, sem executá-la.",
        "Quero apenas uma prévia.",
        "Não aplique nenhuma mudança.",
        "Prepare agora; depois decidimos se executamos.",
    )
    for phrase in phrases:
        provider = _process_provider(
            commit_outcome=_outcome(
                "registry", "commit_record", "created",
                structured={"data": {"record_id": "R-1"}},
            )
        )
        orch, _ = _orchestrator(
            [provider],
            _select(
                "registry", "stage_record",
                arguments={
                    "entity": "process",
                    "operation": "create",
                    "changes": {
                        "nome_processo": "x",
                        "status_processo": "ativo",
                    },
                },
                extra={
                    GOAL_INSTRUCTION_ID: {
                        "goal_class": "create_or_modify",
                        "execution_bound": "prepare_only",
                    }
                },
            ),
        )
        attempt = orch.attempt(phrase)
        assert attempt.status is (
            GovernedCapabilityStatus.CONFIRMATION_REQUIRED
        ), phrase
        assert "commit_record" not in [
            name for name, _ in provider.calls
        ], phrase


def test_s2r1_unrestricted_create_keeps_direct_continuation():
    """B2-03 control (§6.174/§6.184): explicit action request with a
    model-declared `unrestricted` bound and owner direct policy — the
    bound carries no permissive value, so the MESSAGE caps at PREPARE +
    pending; the typed bound APPLY still reaches the governed ACT
    without an extra owner confirmation step."""
    provider = _process_provider(
        commit_outcome=_outcome(
            "registry", "commit_record", "created",
            structured={"data": {"record_id": "R-1"}},
        )
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "stage_record",
            arguments={
                "entity": "process",
                "operation": "create",
                "changes": {
                    "nome_processo": "x",
                    "status_processo": "ativo",
                },
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                    "execution_bound": "unrestricted",
                }
            },
        ),
    )
    attempt = orch.attempt(
        "Crie um processo chamado x",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    assert "commit_record" not in [name for name, _ in provider.calls]
    applied = _apply_pending(orch, attempt)
    assert applied.status is GovernedCapabilityStatus.SUCCESS
    assert [name for name, _ in provider.calls] == [
        "get_catalog", "stage_record", "commit_record",
    ]


def test_s2r1_prepare_only_bound_blocks_cold_act_selection():
    """B2 sibling: the same textual bound caps a cold ACT selection
    too — an ACT-class target under a declared prepare-only goal is
    refused by the execution ceiling, never invoked."""
    provider = _process_provider(
        commit_outcome=_outcome(
            "registry", "commit_record", "created",
            structured={"data": {"record_id": "R-1"}},
        )
    )
    orch, _ = _orchestrator(
        [provider],
        _select(
            "registry", "commit_record",
            arguments={
                "proposal_handle": "x",
                "confirmation": True,
            },
            extra={
                GOAL_INSTRUCTION_ID: {
                    "goal_class": "create_or_modify",
                    "execution_bound": "prepare_only",
                }
            },
        ),
    )
    attempt = orch.attempt("Somente prepare; não execute.")
    assert attempt.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert attempt.error_code == "execution_ceiling"
    assert provider.calls == []


def test_s2_ineligible_or_invented_selection_rejected():
    """Regression: a capability whose owner class is UNKNOWN — or a
    remote_name absent from the live surface — is never invocable;
    deterministic revalidation rejects both before any invocation."""
    provider = FakeProvider(
        "acme-flow",
        [
            _group(
                "acme-flow",
                "registry",
                [
                    _cap(
                        "registry", "acme-flow", "read_guide",
                        SpecialistOperationClass.READ,
                        schema=_GUIDE_SCHEMA,
                        desc="read the how-to guide",
                    ),
                    _cap(
                        "registry", "acme-flow", "mystery_op",
                        SpecialistOperationClass.UNKNOWN,
                        desc="unclassified owner operation",
                    ),
                ],
            )
        ],
    )
    for remote_name in ("mystery_op", "invented_tool"):
        orch, _ = _orchestrator(
            [provider],
            [
                {
                    CAPABILITY_SELECTION_INSTRUCTION_ID: {
                        "applicable": True,
                        "remote_name": remote_name,
                    },
                }
            ],
        )
        attempt = orch.attempt("Me explica como cadastrar.")
        assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert provider.calls == []
