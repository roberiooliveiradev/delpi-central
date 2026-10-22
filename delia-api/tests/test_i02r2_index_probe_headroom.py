"""I02-R2 — optional index_probe headroom before model call.

RED/GREEN for TurnDeadline-aware skip of optional model probe, owner
contract-first index path (incl. PT descriptions), and no empty INDEX
READ presented as guidance when the probe was skipped for budget.
MESSAGE ≠ ACT. GLOBAL_TURN_BUDGET_SECONDS = 30.
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
    INDEX_PROBE_INSTRUCTION_ID,
    INDEX_SELECT_INSTRUCTION_ID,
    MIN_VIABLE_MODEL_STAGE_SECONDS,
    MODEL_STAGE_TIMEOUT_SECONDS,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _contract_declares_omit_returns_index,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import (
    DEFAULT_TURN_BUDGET_SECONDS,
    TurnDeadline,
)
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
    model_id="i02r2-headroom", version="1", owner_ref="DELPI"
)

_GUIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
    },
}

# Live VISTA MCP description (Portuguese) — omit→index without EN tokens.
_VISTA_PT_DESCRIPTION = (
    "Lê o registro canônico de orientação de produto do TV Dashboard "
    "(GUIDANCE_NOT_DOMAIN_TRUTH). Sem topic: índice de tópicos. Com "
    "topic (+section opcional): um guia. Orientação apenas — o "
    "catálogo vivo, leituras de domínio e contratos api-delpi/OpenAPI "
    "sempre prevalecem sobre o texto do guia."
)

# Optional probe path: no omit→index contract language.
_NO_CONTRACT_DESCRIPTION = "READ-only product guidance for a topic."


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
        clock=None,
        timeout_purposes=frozenset(),
        advance_on=None,
    ):
        items = (
            list(proposal) if isinstance(proposal, list) else [proposal]
        )
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        self._last: dict[str, object] = {}
        self._clock = clock
        self._timeout_purposes = frozenset(timeout_purposes)
        self._advance_on = dict(advance_on or {})
        purpose_ids = {
            GOAL_INSTRUCTION_ID,
            CAPABILITY_SELECTION_INSTRUCTION_ID,
            ARGUMENTS_INSTRUCTION_ID,
            NATIVE_ASSESSMENT_INSTRUCTION_ID,
            INDEX_PROBE_INSTRUCTION_ID,
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
        if purpose in self._timeout_purposes:
            if self._clock is not None:
                self._clock.advance(
                    max(0.0, request.timeout_seconds or 10.0)
                )
            raise ModelInvocationError(
                TIMEOUT, "simulated index_probe timeout"
            )
        advance = self._advance_on.get(purpose)
        if self._clock is not None and advance:
            self._clock.advance(float(advance))
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
        if isinstance(outcome, dict):
            if not arguments:
                return outcome["index"]
            return outcome["filled"]
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
                "guide": {
                    "purpose": "design guidance",
                    "use_when": ["legibility"],
                    "how_to_use": ["contrast"],
                    "limitations": "no panel inspection",
                }
            },
        )


def _cap(group_id, provider_id, name, op_class, schema=None, desc=""):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description=desc or "product guide",
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


def _outcome(remote_name, structured):
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="specialist_alpha",
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="c",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text="ok",
        structured=structured,
    )


def _base_proposals(**extra):
    payload = {
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": "get_product_guide",
        },
        GOAL_INSTRUCTION_ID: {
            "goal_class": "read",
            "prior_evidence_sufficient": False,
        },
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
        INDEX_PROBE_INSTRUCTION_ID: {"probe_index": True},
        INDEX_SELECT_INSTRUCTION_ID: {
            "selected_identifier": "display_formats",
            "argument_field": "topic",
        },
        SYNTHESIS_INSTRUCTION_ID: {
            "items": [{"record_index": 0, "fields": ["purpose"]}]
        },
    }
    payload.update(extra)
    return payload


def _required_optional_probe_headroom() -> float:
    """Same derivation as production: 2×stage + MIN_VIABLE×3."""
    return (
        MODEL_STAGE_TIMEOUT_SECONDS
        + MODEL_STAGE_TIMEOUT_SECONDS
        + MIN_VIABLE_MODEL_STAGE_SECONDS * 3
    )


def test_portuguese_owner_contract_declares_omit_returns_index():
    """Live VISTA description must authorize index without model probe."""
    guide = _cap(
        "vista",
        "vista",
        "get_product_guide",
        SpecialistOperationClass.READ,
        schema=_GUIDE_SCHEMA,
        desc=_VISTA_PT_DESCRIPTION,
    )
    assert _contract_declares_omit_returns_index(guide) is True


def test_optional_index_probe_not_started_when_headroom_insufficient():
    """With remaining < derived headroom, optional model probe must not start."""
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    required = _required_optional_probe_headroom()
    # Leave remaining below required (live class: ~20s after early stages).
    clock.advance(DEFAULT_TURN_BUDGET_SECONDS - (required - 1.0))
    assert deadline.remaining_seconds() < required

    provider = FakeProvider(
        "specialist_alpha",
        [
            _group(
                "specialist_alpha",
                "specialist_alpha",
                [
                    _cap(
                        "specialist_alpha",
                        "specialist_alpha",
                        "get_product_guide",
                        SpecialistOperationClass.READ,
                        schema=_GUIDE_SCHEMA,
                        desc=_NO_CONTRACT_DESCRIPTION,
                    )
                ],
            )
        ],
    )
    model = FakeProposalModel(
        _base_proposals(),
        clock=clock,
        timeout_purposes=frozenset({INDEX_PROBE_INSTRUCTION_ID}),
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Que critérios de legibilidade devo considerar para um painel?",
        turn_deadline=deadline,
    )
    probe_purposes = {
        r.task_purpose_id for r in model.requests
    }
    assert INDEX_PROBE_INSTRUCTION_ID not in probe_purposes
    # Empty INDEX-as-guidance must not run when probe was budget-skipped.
    # SEMARG + doc 88 CP2: budget skip is honest PROCESSING_TIMEOUT —
    # not a fabricated "provide código/filtro" clarification and never
    # a fabricated source failure when no owner was consulted.
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "turn_budget_exhausted"


def test_owner_declared_index_skips_model_probe_under_tight_budget():
    """Contract omit→index uses owner INDEX READ; no model probe."""
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    required = _required_optional_probe_headroom()
    clock.advance(DEFAULT_TURN_BUDGET_SECONDS - (required - 1.0))

    index = _outcome(
        "get_product_guide",
        {
            "data": {
                "items": [
                    {
                        "topic": "display_formats",
                        "label": "Formatos",
                        "summary": "moeda percentual",
                    },
                    {
                        "topic": "panel_legibility",
                        "label": "Legibilidade de painel",
                        "summary": "contraste tipografia visualização",
                    },
                    {"topic": "playlist", "label": "Playlist"},
                ]
            }
        },
    )
    filled = _outcome(
        "get_product_guide",
        {
            "guide": {
                "purpose": "Choose panel legibility criteria",
                "use_when": ["panel design"],
                "how_to_use": ["prefer high contrast"],
                "limitations": "no live panel inspection",
            }
        },
    )
    provider = FakeProvider(
        "renamed_provider_omega",
        [
            _group(
                "renamed_provider_omega",
                "renamed_provider_omega",
                [
                    _cap(
                        "renamed_provider_omega",
                        "renamed_provider_omega",
                        "renamed_guide_capability",
                        SpecialistOperationClass.READ,
                        schema=_GUIDE_SCHEMA,
                        desc=_VISTA_PT_DESCRIPTION,
                    )
                ],
            )
        ],
        outcomes={
            ("renamed_provider_omega", "renamed_guide_capability"): {
                "index": index,
                "filled": filled,
            }
        },
    )
    # Selection uses renamed capability; proposals must match remote_name.
    proposals = _base_proposals()
    proposals[CAPABILITY_SELECTION_INSTRUCTION_ID] = {
        "applicable": True,
        "remote_name": "renamed_guide_capability",
    }
    proposals[INDEX_SELECT_INSTRUCTION_ID] = {
        "selected_identifier": "panel_legibility",
        "argument_field": "topic",
    }
    model = FakeProposalModel(
        proposals,
        clock=clock,
        timeout_purposes=frozenset({INDEX_PROBE_INSTRUCTION_ID}),
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Que critérios de legibilidade devo considerar para um painel?",
        turn_deadline=deadline,
    )
    assert INDEX_PROBE_INSTRUCTION_ID not in {
        r.task_purpose_id for r in model.requests
    }
    assert [c[0] for c in provider.calls] == [
        "renamed_guide_capability",
        "renamed_guide_capability",
    ]
    assert provider.calls[0][1] == {}
    assert provider.calls[1][1] == {"topic": "panel_legibility"}
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "legibility" in (attempt.content or "").lower() or (
        "contrast" in (attempt.content or "").lower()
        or "formats" in (attempt.content or "").lower()
    )


def test_exploratory_free_string_is_forwarded_not_rendered_as_fact():
    """Non-id free text is not a stem veto. The answer stays owner evidence."""
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    required = _required_optional_probe_headroom()
    clock.advance(DEFAULT_TURN_BUDGET_SECONDS - (required - 1.0))
    provider = FakeProvider(
        "specialist_alpha",
        [
            _group(
                "specialist_alpha",
                "specialist_alpha",
                [
                    _cap(
                        "specialist_alpha",
                        "specialist_alpha",
                        "get_product_guide",
                        SpecialistOperationClass.READ,
                        schema=_GUIDE_SCHEMA,
                        desc=_NO_CONTRACT_DESCRIPTION,
                    )
                ],
            )
        ],
    )
    model = FakeProposalModel(
        _base_proposals(
            **{
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"topic": "invented_topic_xyz"}
                }
            }
        ),
        clock=clock,
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Quero orientação sobre um tópico específico",
        turn_deadline=deadline,
    )
    assert INDEX_PROBE_INSTRUCTION_ID not in {
        r.task_purpose_id for r in model.requests
    }
    assert provider.calls
    assert provider.calls[-1][1].get("topic") == "invented_topic_xyz"
    assert "invented_topic_xyz" not in (attempt.content or "")


def test_required_field_still_blocks_empty_read():
    schema = {
        "type": "object",
        "properties": {"topic": {"type": "string"}},
        "required": ["topic"],
    }
    guide = _cap(
        "specialist_alpha",
        "specialist_alpha",
        "get_product_guide",
        SpecialistOperationClass.READ,
        schema=schema,
        desc=_VISTA_PT_DESCRIPTION,
    )
    assert _contract_declares_omit_returns_index(guide) is True
    # Required field ⇒ not self-index eligible; contract alone must not
    # authorize empty invoke (eligibility is structural).
    from app.application.capability_provision.orchestration import (
        _eligible_self_index_probe,
    )

    assert _eligible_self_index_probe(guide) is False


def test_global_deadline_exhausted_starts_no_new_model_stage():
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    clock.advance(30.0)
    provider = FakeProvider(
        "specialist_alpha",
        [
            _group(
                "specialist_alpha",
                "specialist_alpha",
                [
                    _cap(
                        "specialist_alpha",
                        "specialist_alpha",
                        "get_product_guide",
                        SpecialistOperationClass.READ,
                        schema=_GUIDE_SCHEMA,
                        desc=_NO_CONTRACT_DESCRIPTION,
                    )
                ],
            )
        ],
    )
    model = FakeProposalModel(_base_proposals(), clock=clock)
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt("pedido", turn_deadline=deadline)
    assert attempt.error_code in {
        "model_timeout",
        "turn_budget_exhausted",
        "stage_deadline_exceeded",
    } or attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert INDEX_PROBE_INSTRUCTION_ID not in {
        r.task_purpose_id for r in model.requests
    }
    assert provider.calls == []


def test_headroom_constants_unchanged():
    assert DEFAULT_TURN_BUDGET_SECONDS == 30.0
    assert MODEL_STAGE_TIMEOUT_SECONDS == 10.0
    assert MIN_VIABLE_MODEL_STAGE_SECONDS == 2.0
    assert _required_optional_probe_headroom() == 26.0
