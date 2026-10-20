"""PROV/CONT — provider-neutral semantic provenance and continuity.

TASK: DELIA-C3-PROVIDER-NEUTRAL-SEMANTIC-PROVENANCE-AND-CONTINUITY-REWORK-01

Locks: free-string grounding rejects incidental token overlap with
unsupported qualifiers; paraphrases of user search terms remain allowed;
prior compare/subset uses typed goal continuity without burning the
global turn budget on a redundant owner path.
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
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    MIN_VIABLE_MODEL_STAGE_SECONDS,
    MODEL_STAGE_TIMEOUT_SECONDS,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    LIMITATION_INSUFFICIENT_EVIDENCE,
    _prior_excerpt_records,
    _prior_supports_typed_attribute_compare,
    _prior_transform_probe_eligible,
)
from app.application.interaction.contracts import (
    LIMITATION_PRIOR_TURN_CONTINUATION,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import (
    DEFAULT_TURN_BUDGET_SECONDS,
    TurnDeadline,
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
    model_id="prov-cont", version="1", owner_ref="DELPI"
)

_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "description": {"type": "string"},
        "group_code": {"type": "string"},
        "customer_reference": {"type": "string"},
        "sort": {"type": "string"},
        "direction": {"type": "string"},
        "page": {"type": "integer"},
        "page_size": {"type": "integer"},
    },
}


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

    def __init__(self, proposal, *, clock=None):
        items = list(proposal) if isinstance(proposal, list) else [proposal]
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        self._last: dict[str, object] = {}
        self._clock = clock
        purpose_ids = {
            INTERACTION_ADMISSION_INSTRUCTION_ID,
            GROUP_SELECTION_INSTRUCTION_ID,
            CAPABILITY_SELECTION_INSTRUCTION_ID,
            GOAL_INSTRUCTION_ID,
            ARGUMENTS_INSTRUCTION_ID,
            NATIVE_ASSESSMENT_INSTRUCTION_ID,
            INDEX_PROBE_INSTRUCTION_ID,
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
        elif purpose == INTERACTION_ADMISSION_INSTRUCTION_ID:
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
        if self._clock is not None and purpose == GOAL_INSTRUCTION_ID:
            self._clock.advance(2.0)
        if self._clock is not None and purpose == SYNTHESIS_INSTRUCTION_ID:
            self._clock.advance(8.0)
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
        self, capability, arguments, *, correlation_id, timeout_seconds=None
    ):
        self.calls.append((capability.remote_name, dict(arguments)))
        key = (capability.group_id, capability.remote_name)
        if key in self._outcomes:
            return self._outcomes[key]
        return SpecialistOutcome(
            status=SpecialistResultStatus.COMPLETED,
            provenance=SpecialistResultProvenance(
                specialist_id=capability.group_id,
                remote_name=capability.remote_name,
                protocol=InteropProtocol.HTTP,
                correlation_id=correlation_id,
                observed_at="2026-01-01T00:00:00+00:00",
            ),
            content_text="ok",
            structured={"items": [], "total": 0},
        )


def _cap(group_id, provider_id, name, op_class, schema=None, desc=""):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description=desc or "search",
        input_schema=schema or {"type": "object", "properties": {}},
        binding={"ref": name},
    )


def _group(provider_id, group_id, capabilities, display=""):
    return CapabilityGroup(
        provider_id=provider_id,
        group_id=group_id,
        owner_ref=group_id,
        display_name=display or group_id,
        capabilities=tuple(capabilities),
        source=SourceRef(
            source_id=group_id,
            source_system=group_id,
            provider_name=display or group_id,
        ),
    )


def _tight_deadline(clock=None):
    clock = clock or FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    required = (
        MODEL_STAGE_TIMEOUT_SECONDS
        + MODEL_STAGE_TIMEOUT_SECONDS
        + MIN_VIABLE_MODEL_STAGE_SECONDS * 3
    )
    clock.advance(DEFAULT_TURN_BUDGET_SECONDS - (required - 1.0))
    return clock, deadline


def _search_proposals(arguments, *, group_key="openapi:delpi", remote="search_products"):
    return {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": group_key,
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": remote,
        },
        GOAL_INSTRUCTION_ID: {
            "goal_class": "read",
            "prior_evidence_sufficient": False,
        },
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {
            "arguments": arguments,
            "missing_inputs": [],
        },
        INDEX_PROBE_INSTRUCTION_ID: {"probe_index": True},
        SYNTHESIS_INSTRUCTION_ID: {
            "items": [
                {"record_index": 0, "fields": ["product_code", "description"]}
            ]
        },
    }


def _orch(providers, proposals, *, clock=None):
    return OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(FakeProposalModel(proposals, clock=clock)),
        model_ref=TEST_MODEL_REF,
    )


def _search_provider(provider_id="openapi", group_id="delpi", remote="search_products"):
    return FakeProvider(
        provider_id,
        [
            _group(
                provider_id,
                group_id,
                [
                    _cap(
                        group_id,
                        provider_id,
                        remote,
                        SpecialistOperationClass.READ,
                        schema=_SEARCH_SCHEMA,
                    )
                ],
            )
        ],
        outcomes={
            (group_id, remote): SpecialistOutcome(
                status=SpecialistResultStatus.COMPLETED,
                provenance=SpecialistResultProvenance(
                    specialist_id=group_id,
                    remote_name=remote,
                    protocol=InteropProtocol.HTTP,
                    correlation_id="c",
                    observed_at="2026-01-01T00:00:00+00:00",
                ),
                content_text="search ok",
                structured={
                    "items": [
                        {
                            "product_code": "A",
                            "description": "TERM. PINO A",
                        },
                        {
                            "product_code": "B",
                            "description": "TERM. PINO B",
                        },
                    ],
                    "total": 2,
                },
            )
        },
    )


# --- PROV orchestration under budget skip ---------------------------------


def test_q02b_paraphrase_without_stem_overlap_reaches_owner():
    """Exploratory search text is a typed model proposal, not a stem match."""
    clock, deadline = _tight_deadline()
    provider = _search_provider()
    orch = _orch(
        [provider],
        _search_proposals(
            {"description": "terminais de produção", "page_size": 2}
        ),
        clock=clock,
    )
    attempt = orch.attempt(
        "Quero consultar os equipamentos do chão de fábrica.",
        turn_deadline=deadline,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert provider.calls
    assert provider.calls[0][1].get("description") == "terminais de produção"
    content = (attempt.content or "").lower()
    assert "term. pino" in content
    assert "chão de fábrica" not in content


def test_prov_t02_exploratory_qualifier_is_not_rendered_as_fact():
    """Extra search words go to the owner. The answer stays owner evidence."""
    clock, deadline = _tight_deadline()
    provider = _search_provider()
    orch = _orch(
        [provider],
        _search_proposals(
            {
                "description": "terminal pino homologado anatel",
                "page_size": 2,
            }
        ),
        clock=clock,
    )
    attempt = orch.attempt(
        "Mostre terminais pino.",
        turn_deadline=deadline,
    )
    assert provider.calls
    assert (
        provider.calls[0][1].get("description")
        == "terminal pino homologado anatel"
    )
    content = (attempt.content or "").lower()
    assert "term. pino" in content
    assert "anatel" not in content
    assert "homologado" not in content


def test_q02b_invented_identifier_does_not_invoke_owner():
    clock, deadline = _tight_deadline()
    schema = {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "page_size": {"type": "integer"},
        },
    }
    provider = _search_provider()
    provider._groups[0] = _group(
        "openapi",
        "delpi",
        [
            _cap(
                "delpi",
                "openapi",
                "search_products",
                SpecialistOperationClass.READ,
                schema=schema,
            )
        ],
    )
    orch = _orch(
        [provider],
        _search_proposals({"ticket_id": "123456", "page_size": 2}),
        clock=clock,
    )
    attempt = orch.attempt(
        "Quero consultar os terminais utilizados na produção.",
        turn_deadline=deadline,
    )
    assert all(
        call[1].get("ticket_id") != "123456" for call in provider.calls
    )
    assert "123456" not in (attempt.content or "")


def test_prov_t04_orchestration_allows_paraphrase_search():
    clock, deadline = _tight_deadline()
    provider = _search_provider()
    orch = _orch(
        [provider],
        _search_proposals(
            {"description": "TERM. PINO", "page_size": 2}
        ),
        clock=clock,
    )
    attempt = orch.attempt(
        "Liste 2 produtos reais cadastrados do tipo terminal pino.",
        turn_deadline=deadline,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert provider.calls
    assert provider.calls[0][1].get("description") == "TERM. PINO"


def test_prov_t09_renamed_provider_same_provenance_rule():
    clock, deadline = _tight_deadline()
    provider = _search_provider(
        provider_id="renamed_omega",
        group_id="catalog_omega",
        remote="find_items",
    )
    orch = _orch(
        [provider],
        _search_proposals(
            {"description": "TERM. PINO", "page_size": 2},
            group_key="renamed_omega:catalog_omega",
            remote="find_items",
        ),
        clock=clock,
    )
    attempt = orch.attempt(
        "Liste terminais pino cadastrados.",
        turn_deadline=deadline,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert provider.calls[0][0] == "find_items"


def test_prov_t10_non_mcp_http_family():
    clock, deadline = _tight_deadline()
    provider = _search_provider()
    orch = _orch(
        [provider],
        _search_proposals({"description": "terminal", "page_size": 3}),
        clock=clock,
    )
    attempt = orch.attempt(
        "Pesquise produtos pela descrição terminal.",
        turn_deadline=deadline,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.provenance.provider_id == "openapi"


# --- CONT typed continuity -------------------------------------------------


def test_cont_probe_compare_goal_without_legacy_cue():
    goal = OperationalCapabilityOrchestrator._TurnGoal(
        goal_class="compare",
        comparison_requested=True,
        declared=True,
    )
    assert (
        _prior_transform_probe_eligible(
            "Compare os dois resultados.",
            goal,
        )
        is True
    )


def test_cont_t03_compare_prior_stops_without_owner_when_budget_tight():
    """Compare over prior OBSERVATION must not re-enter owner under tight budget."""
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    # Leave only ~9s — below optional-probe headroom and near resolver floor.
    clock.advance(21.0)
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Busque terminais pino cadastrados.",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=(
                "Encontrei 2 registros:\n"
                "- A — TERM. PINO A\n"
                "- B — TERM. PINO B"
            ),
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    provider = _search_provider()
    proposals = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GOAL_INSTRUCTION_ID: {
            "goal_class": "compare",
            "comparison_requested": True,
            "prior_evidence_sufficient": False,
        },
        # If fallthrough wrongly happens, these would select search again.
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": "openapi:delpi",
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": "search_products",
        },
        ARGUMENTS_INSTRUCTION_ID: {
            "arguments": {"description": "TERM. PINO"},
            "missing_inputs": [],
        },
        # Synthesis returns empty → insufficient evidence on prior path.
        SYNTHESIS_INSTRUCTION_ID: {"items": []},
    }
    orch = _orch([provider], proposals, clock=clock)
    attempt = orch.attempt(
        "Compare os dois.",
        prior_turns=prior,
        turn_deadline=deadline,
    )
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.error_code != "turn_budget_exhausted"
    content = attempt.content or ""
    # G0 rework: free-text prior bullets are never typed compare SUCCESS.
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations
    assert LIMITATION_PRIOR_TURN_CONTINUATION in attempt.limitations
    assert "Comparação a partir" not in content
    assert not content.lower().startswith("encontrei ")
    assert not content.lower().startswith("recuperei ")


def _compare_prior_attempt(prior_content: str, ask: str, proposals=None):
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Busque itens cadastrados.",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=prior_content,
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    provider = _search_provider()
    base = {
        # Q02-A: admission runs with prior turns — compare continuity is
        # operational, not a conversational skip.
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GOAL_INSTRUCTION_ID: {
            "goal_class": "compare",
            "comparison_requested": True,
            "prior_evidence_sufficient": True,
        },
        SYNTHESIS_INSTRUCTION_ID: {"items": []},
    }
    if proposals:
        base.update(proposals)
    orch = _orch([provider], base, clock=clock)
    attempt = orch.attempt(
        ask, prior_turns=prior, turn_deadline=deadline
    )
    return attempt, provider


def test_g0_rework_compare_empty_selection_is_insufficiency():
    """Empty items on free-text prior → insufficiency, never string diffs."""
    attempt, provider = _compare_prior_attempt(
        "Encontrei 2 registros:\n"
        "- 30191627 — OLHAL CERAMICA — S — PC\n"
        "- 30191751 — OLHAL PARA PARAF FRANCES — S — PC",
        "Compare os dois.",
    )
    assert provider.calls == []
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations
    assert LIMITATION_PRIOR_TURN_CONTINUATION in attempt.limitations
    content = attempt.content or ""
    assert "30191627" not in content or "→" not in content
    assert "Comparação a partir" not in content
    assert "Diferenças comprovadas:" not in content


def test_g0_rework_compare_reordered_segments_not_attributes():
    """Same tokens in different order still lack typed field provenance."""
    attempt, provider = _compare_prior_attempt(
        "Encontrei 2 registros:\n"
        "- ALPHA — 100 — KG\n"
        "- KG — 100 — ALPHA",
        "Compare os dois.",
    )
    assert provider.calls == []
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations


def test_g0_rework_compare_unequal_segment_counts_insufficient():
    attempt, provider = _compare_prior_attempt(
        "Encontrei 2 registros:\n"
        "- A — B — C — D\n"
        "- X — Y",
        "Compare os dois.",
    )
    assert provider.calls == []
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations


def test_g0_rework_compare_delimiter_inside_value_insufficient():
    attempt, provider = _compare_prior_attempt(
        "Encontrei 2 registros:\n"
        "- TERM — PINO — INDUSTRIAL — ESPECIAL\n"
        "- TERM — OLHAL — SIMPLES",
        "Compare os dois.",
    )
    assert provider.calls == []
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations


def test_g0_rework_compare_second_and_third_items_insufficient():
    """Ordinal subset compare over prose prior cannot invent attributes."""
    attempt, provider = _compare_prior_attempt(
        "Encontrei 4 registros:\n"
        "- A — ONE\n"
        "- B — TWO\n"
        "- C — THREE\n"
        "- D — FOUR",
        "Compare o segundo e o terceiro.",
    )
    assert provider.calls == []
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations


def test_g0_rework_compare_fake_identifier_in_prior_insufficient():
    attempt, provider = _compare_prior_attempt(
        "Encontrei 2 registros:\n"
        "- FAKE-ID-999 — produto inventado\n"
        "- FAKE-ID-998 — outro inventado",
        "Compare os dois.",
    )
    assert provider.calls == []
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations
    assert "FAKE-ID" not in (attempt.content or "")


def test_g0_rework_compare_invalid_index_insufficient():
    attempt, provider = _compare_prior_attempt(
        "Encontrei 2 registros:\n- A — ONE\n- B — TWO",
        "Compare os dois.",
        proposals={
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {"record_index": 99, "fields": ["excerpt"]},
                    {"record_index": 1, "fields": ["excerpt"]},
                ]
            }
        },
    )
    assert provider.calls == []
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations


def test_g0_rework_misleading_compare_header_is_not_outcome():
    import app.application.capability_provision.orchestration as orch_mod

    assert not hasattr(orch_mod, "_typed_compare_outcome_content")
    assert not _prior_supports_typed_attribute_compare(
        ({"excerpt": "- A — B"}, {"excerpt": "- C — D"})
    )
    assert _prior_supports_typed_attribute_compare(
        (
            {"code": "1", "description": "A"},
            {"code": "2", "description": "B"},
        )
    )


def test_cont_t01_subset_from_prior_when_sufficient():
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Busque terminais pino cadastrados.",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=(
                "Encontrei 4 registros:\n"
                "- A — TERM. PINO A\n"
                "- B — TERM. PINO B\n"
                "- C — TERM. PINO C\n"
                "- D — TERM. PINO D"
            ),
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    provider = _search_provider()
    proposals = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GOAL_INSTRUCTION_ID: {
            "goal_class": "read",
            "prior_evidence_sufficient": True,
        },
        SYNTHESIS_INSTRUCTION_ID: {
            "items": [
                {"record_index": 0, "fields": ["excerpt"]},
                {"record_index": 1, "fields": ["excerpt"]},
            ]
        },
    }
    orch = _orch([provider], proposals, clock=clock)
    attempt = orch.attempt(
        "Mostre dois deles.",
        prior_turns=prior,
        turn_deadline=deadline,
    )
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.content


def test_cont_t02_empty_selection_recovers_bullet_prior():
    """Q02-A: empty synthesis fails closed; no lexical bullet dump."""
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Busque terminais pino cadastrados.",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=(
                "Encontrei 2 registros:\n"
                "- A — TERM. PINO A\n"
                "- B — TERM. PINO B"
            ),
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    provider = _search_provider()
    proposals = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GOAL_INSTRUCTION_ID: {
            "goal_class": "read",
            "prior_evidence_sufficient": True,
        },
        SYNTHESIS_INSTRUCTION_ID: {"items": []},
    }
    orch = _orch([provider], proposals, clock=clock)
    attempt = orch.attempt(
        "Liste dois produtos encontrados.",
        prior_turns=prior,
        turn_deadline=deadline,
    )
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "prior_turn_evidence_only" in attempt.limitations
    assert "insufficient_evidence" in attempt.limitations
    content = attempt.content or ""
    assert "TERM. PINO A" not in content
    assert "TERM. PINO B" not in content


def test_cont_bullet_abbreviation_stays_atomic_excerpt():
    units = _prior_excerpt_records(
        "Encontrei 2 registros:\n"
        "- A — TERM. PINO A\n"
        "- B — TERM. PINO B"
    )
    excerpts = [u["excerpt"] for u in units]
    assert any("TERM. PINO A" in e for e in excerpts)
    assert any("TERM. PINO B" in e for e in excerpts)


def test_cont_t08_conversation_without_mcp():
    provider = _search_provider()
    orch = _orch(
        [provider],
        {
            INTERACTION_ADMISSION_INSTRUCTION_ID: {
                "requires_owner_surface": False,
                "interaction_class": "conversation",
            }
        },
    )
    attempt = orch.attempt("Olá")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert provider.calls == []


def test_cont_t12_global_budget_constant():
    assert DEFAULT_TURN_BUDGET_SECONDS == 30.0
