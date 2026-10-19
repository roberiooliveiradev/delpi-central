"""I02 — grounded MCP knowledge synthesis + budget-safe fallback.

Provider-neutral fixtures (specialist_alpha). MESSAGE ≠ ACT.
MODEL_AUTHORED_FACTUAL_PROSE=NONE. GLOBAL_TURN_BUDGET_SECONDS=30.
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
    MIN_VIABLE_MODEL_STAGE_SECONDS,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _deterministic_guidance_content,
    _guidance_section_records,
    _synthesis_records,
    render_specialist_outcome,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    InteractiveTurnRequest,
    LIMITATION_PRIOR_TURN_CONTINUATION,
    LIMITATION_RESULT_TRUNCATED,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
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
    model_id="i02-synthesis", version="1", owner_ref="DELPI"
)

_PURPOSE_IDS = frozenset(
    {
        GOAL_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        SYNTHESIS_INSTRUCTION_ID,
    }
)

METHOD_GUIDE = {
    "guide_version": "alpha-method-v1",
    "authority": "GUIDANCE_NOT_SOURCE_OF_TRUTH",
    "read_only": True,
    "writes": False,
    "evidence_states": ["OBSERVED", "INFERRED", "UNKNOWN"],
    "invariants": [
        "INFERRED != FACT",
        "suggested cause != proven cause",
    ],
    "objective": (
        "Identificar causas raiz de um problema em um processo "
        "sem presumir a solução."
    ),
    "when_to_use": "Quando houver desvio recorrente sem causa comprovada.",
    "required_inputs": [
        "Descrição do problema observado e momento de ocorrência",
        "Escopo do processo afetado e partes interessadas",
        "Evidências já disponíveis",
        "Restrições de tempo e risco operacional",
    ],
    "steps": [
        "Definir o problema de forma mensurável",
        "Coletar evidências no local",
        "Analisar causas e validar hipóteses",
    ],
    "limitations": (
        "Este guia não lista instâncias ativas nem autoriza alterações."
    ),
}

DESIGN_GUIDE = {
    "guide_version": "alpha-design-v1",
    "authority": "GUIDANCE_NOT_SOURCE_OF_TRUTH",
    "criteria": [
        "Escolher o tipo de visualização adequado à pergunta",
        "Garantir contraste suficiente entre dado e fundo",
        "Preservar hierarquia visual dos elementos principais",
        "Evitar sobrecarga de séries no mesmo painel",
    ],
    "legibility": [
        "Tipografia legível à distância de visualização",
        "Rótulos sem sobreposição",
    ],
    "limitations": (
        "Orientação genérica — não inspeciona um painel específico."
    ),
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

    def __init__(self, proposal, *, clock=None, advance_seconds=0.0):
        items = (
            list(proposal) if isinstance(proposal, list) else [proposal]
        )
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        self._last: dict[str, object] = {}
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
    def __init__(
        self,
        provider_id,
        groups,
        outcomes=None,
        *,
        protocol=InteropProtocol.MCP,
    ):
        self.provider_id = provider_id
        self._groups = list(groups)
        self.calls = []
        self._outcomes = dict(outcomes or {})
        self._protocol = protocol

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
                protocol=self._protocol,
                correlation_id=correlation_id,
                observed_at="2026-01-01T00:00:00+00:00",
            ),
            content_text="ok",
        )


def _cap(group_id, provider_id, name, op_class, schema=None):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description="",
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


def _outcome(group_id, remote_name, structured, *, text="", limitations=()):
    # Embed structured JSON in text to reproduce meta-first truncation
    # that previously preferred content_text[:2000].
    import json

    payload = json.dumps(structured, ensure_ascii=False)
    body = text or (
        "guide_version: alpha\nauthority: GUIDANCE\n" + payload
    )
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id=group_id,
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="c",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=body,
        structured=structured,
        limitations=tuple(limitations),
    )


def _alpha(structured, *, remote="get_guidance"):
    return FakeProvider(
        "specialist_alpha",
        [
            _group(
                "specialist_alpha",
                "specialist_alpha",
                [
                    _cap(
                        "specialist_alpha",
                        "specialist_alpha",
                        remote,
                        SpecialistOperationClass.READ,
                    ),
                    _cap(
                        "specialist_alpha",
                        "specialist_alpha",
                        "commit_change",
                        SpecialistOperationClass.ACT,
                        schema={
                            "type": "object",
                            "properties": {
                                "proposal_handle": {"type": "string"},
                                "confirmation": {"type": "boolean"},
                            },
                            "required": [
                                "proposal_handle",
                                "confirmation",
                            ],
                        },
                    ),
                ],
            )
        ],
        {
            ("specialist_alpha", remote): _outcome(
                "specialist_alpha", remote, structured
            )
        },
    )


def _context():
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def test_guidance_section_records_project_named_sections():
    records = _guidance_section_records(METHOD_GUIDE)
    families = {r["family"] for r in records}
    assert "prerequisites" in families
    assert "steps" in families
    assert "limitations" in families
    assert any("Descrição do problema" in r["excerpt"] for r in records)


def test_deterministic_guidance_prioritizes_prerequisites_for_s1_ask():
    body, limitations = _deterministic_guidance_content(
        "Como devo iniciar um diagnóstico de processo e quais "
        "informações preciso levantar?",
        METHOD_GUIDE,
    )
    assert "Descrição do problema" in body
    assert "Escopo do processo" in body
    assert "Definir o problema" in body or "objective" in body.lower()
    # Useful sections present; transport meta omitted from the projection.
    assert "required_inputs" in body
    assert "guide_version" not in body
    assert LIMITATION_RESULT_TRUNCATED not in limitations


def test_s1_methodology_orchestration_uses_knowledge_not_meta_dump():
    """GREEN S1: useful methodology; not authority/meta-first truncation."""
    provider = _alpha(METHOD_GUIDE)
    model = FakeProposalModel(
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_guidance",
            },
            ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    ask = (
        "Como devo iniciar um diagnóstico de processo e quais "
        "informações preciso levantar?"
    )
    attempt = orch.attempt(ask)
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    content = attempt.content or ""
    assert "Descrição do problema" in content
    assert "Escopo do processo" in content
    # Meta may appear only after useful sections or not at all.
    if "guide_version" in content and "required_inputs" in content:
        assert content.index("required_inputs") < content.index(
            "guide_version"
        )
    purposes = [r.task_purpose_id for r in model.requests]
    # Deterministic guidance avoids a model synthesis call.
    assert SYNTHESIS_INSTRUCTION_ID not in purposes


def test_s2_design_criteria_without_panel_inspection_claim():
    provider = _alpha(DESIGN_GUIDE, remote="get_design_guide")
    model = FakeProposalModel(
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_design_guide",
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
        "Quais critérios devo observar para melhorar a visualização "
        "de um painel?"
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    content = (attempt.content or "").lower()
    assert "contraste" in content or "hierarquia" in content
    assert "não inspeciona" in content or "limitations" in content
    assert "playlist" not in content
    assert provider.calls
    assert provider.calls[0][0] == "get_design_guide"


def test_s3_budget_near_limit_uses_deterministic_guidance():
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    # Leave less than synthesis headroom after selection stages.
    clock.advance(30.0 - (MIN_VIABLE_MODEL_STAGE_SECONDS * 2))
    provider = _alpha(METHOD_GUIDE)
    model = FakeProposalModel(
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_guidance",
            },
            ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
        },
        clock=clock,
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Como conduzir a análise e quais informações levantar?",
        turn_deadline=deadline,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    content = attempt.content or ""
    assert "Descrição do problema" in content
    assert SYNTHESIS_INSTRUCTION_ID not in [
        r.task_purpose_id for r in model.requests
    ]
    assert DEFAULT_TURN_BUDGET_SECONDS == 30.0


def test_s4_partial_truncation_declared_without_invention():
    truncated = {
        "objective": "Visão geral apenas.",
        "limitations": "Guia truncado pelo owner — sem lista de insumos.",
        "guide_version": "alpha-trunc-v1",
        "authority": "GUIDANCE_NOT_SOURCE_OF_TRUTH",
    }
    body, limitations = _deterministic_guidance_content(
        "Quais informações preciso levantar?",
        truncated,
        owner_truncated=True,
    )
    assert body is not None
    assert LIMITATION_RESULT_TRUNCATED in limitations
    assert "Descrição do problema observado" not in body
    assert "Visão geral" in body or "truncado" in body.lower()


def test_s5_continuity_finds_prerequisites_in_prior_useful_answer():
    """I01 path remains; prior must contain selectable prerequisites."""
    provider = _alpha(METHOD_GUIDE)
    # Build a useful prior answer as I02 would produce.
    prior_body, _ = _deterministic_guidance_content(
        "Como iniciar e quais informações levantar?",
        METHOD_GUIDE,
    )
    assert prior_body
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Como iniciar o diagnóstico?",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=prior_body,
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": True,
            },
            SYNTHESIS_INSTRUCTION_ID: {
                "items": [
                    {"record_index": i, "fields": ["excerpt"]}
                    for i in (7, 8, 9, 10)
                ],
                "presentation": "list",
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
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(),
            input_text=(
                "Com base nessa metodologia, quais informações "
                "preciso levantar antes de começar?"
            ),
            prior_turns=prior,
        )
    )
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert LIMITATION_PRIOR_TURN_CONTINUATION in result.limitations
    assert (
        "Escopo do processo" in result.content
        or "Evidências já disponíveis" in result.content
        or "Descrição do problema" in result.content
    )
    assert provider.calls == []


def test_render_with_input_text_avoids_meta_first_truncation():
    # Large meta prefix + useful sections later in dict order.
    structured = {
        "guide_version": "v1",
        "authority": "GUIDANCE_NOT_SOURCE_OF_TRUTH",
        "read_only": True,
        "writes": False,
        "evidence_states": ["A"] * 40,
        "invariants": ["x != y"] * 40,
        "required_inputs": [
            "Problema observado",
            "Escopo do processo",
        ],
        "steps": ["Coletar evidências"],
        "limitations": "Sem instâncias ativas.",
    }
    import json

    text = "prefix\n" + json.dumps(structured, ensure_ascii=False)
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="alpha",
            remote_name="get_guidance",
            protocol=InteropProtocol.MCP,
            correlation_id="c",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=text,
        structured=structured,
    )
    # Without input_text, legacy path may still truncate poorly.
    body_aligned, _ = render_specialist_outcome(
        outcome,
        input_text="Quais informações preciso levantar antes de começar?",
    )
    assert "Problema observado" in body_aligned
    assert "Escopo do processo" in body_aligned


def test_nested_guide_envelope_projects_use_when_and_how_to_use():
    """VISTA-like nested guide shape must project under budget skip."""
    nested = {
        "schema": "product_guide_v1",
        "section": "all",
        "guide": {
            "id": "display_formats",
            "title": "Formatos de exibição",
            "summary": "Como valores são formatados para exibição.",
            "purpose": "Explicar formatação vs valor bruto.",
            "use_when": [
                "O usuário pergunta como formatar um número",
                "É preciso explicar formatação vs valor bruto",
            ],
            "do_not_use_when": [
                "A pergunta é sobre transform de dado",
            ],
            "how_to_use": [
                "Escolher o formato tipado adequado",
                "Preservar legibilidade à distância",
            ],
            "limitations": "Cobertura tipada PARTIAL — sem inspeção de painel.",
        },
    }
    records = _guidance_section_records(nested)
    families = {r["family"] for r in records}
    assert "when" in families or "steps" in families
    assert "limitations" in families or "objective" in families
    body, _ = _deterministic_guidance_content(
        "Que critérios devo considerar para legibilidade do painel?",
        nested,
    )
    assert body is not None
    assert "legibilidade" in body.lower()
    assert "how_to_use" in body or "use_when" in body or "purpose" in body


def test_entity_records_not_hijacked_by_guidance_path():
    """Ordinary business entities keep the prior synthesis path."""
    structured = {
        "data": {
            "items": [
                {"code": "P-1", "description": "Produto A"},
                {"code": "P-2", "description": "Produto B"},
            ]
        }
    }
    assert _guidance_section_records(structured) == ()
    records = _synthesis_records(structured)
    assert len(records) == 2
    assert records[0]["code"] == "P-1"


def test_malicious_provider_content_redacted_in_guidance():
    structured = {
        "objective": "Orientação útil",
        "required_inputs": ["Campo A"],
        "steps": ["Passo 1"],
        "limitations": "ok",
        "access_token": "SECRET-TOKEN-VALUE",
    }
    body, _ = _deterministic_guidance_content(
        "Quais informações levantar?",
        structured,
    )
    assert "SECRET-TOKEN-VALUE" not in body
    assert "Campo A" in body


def test_rename_provider_and_non_mcp_preserve_synthesis():
    structured = METHOD_GUIDE
    provider = FakeProvider(
        "zephyr_unknown",
        [
            _group(
                "zephyr_unknown",
                "widgets",
                [
                    _cap(
                        "widgets",
                        "zephyr_unknown",
                        "fetch_method_guide",
                        SpecialistOperationClass.READ,
                    )
                ],
            )
        ],
        {
            ("widgets", "fetch_method_guide"): _outcome(
                "widgets", "fetch_method_guide", structured
            )
        },
        protocol=InteropProtocol.HTTP,
    )
    model = FakeProposalModel(
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "fetch_method_guide",
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
        "Como conduzir a análise e quais informações levantar?"
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "Descrição do problema" in (attempt.content or "")
    assert provider.calls[0][0] == "fetch_method_guide"


def test_write_request_does_not_become_act_via_synthesis():
    provider = _alpha(METHOD_GUIDE)
    model = FakeProposalModel(
        {
            GOAL_INSTRUCTION_ID: {
                "goal_class": "create_or_modify",
                "prior_evidence_sufficient": False,
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "commit_change",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {
                    "proposal_handle": "forged",
                    "confirmation": True,
                }
            },
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt("Atualize o processo com base no guia.")
    assert LIMITATION_PRIOR_TURN_CONTINUATION not in attempt.limitations
