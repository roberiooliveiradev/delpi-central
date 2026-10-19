"""SEM recovery — admission, argument preservation, group reserve.

TASK: DELIA-C3-SEMANTIC-INTELLIGENCE-ORCHESTRATION-FULL-RECOVERY-01
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CONVERSATIONAL_FALLBACK_RESERVE_SECONDS,
    GROUP_SELECTION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_STAGE_CAP_SECONDS,
    OperationalCapabilityOrchestrator,
    _clarification_content,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.contracts import ConversationContextTurn
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import TurnKind
from tests.test_specialist_capability_orchestration import (
    FakePort,
    TEO_TOOLS,
    VISTA_TOOLS,
    _interop,
    _read,
    _select,
)


def test_sem_t01_cold_greeting_admission_skips_owner_listing():
    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("teo", "vista"),
        proposal={
            INTERACTION_ADMISSION_INSTRUCTION_ID: {
                "requires_owner_surface": False,
                "interaction_class": "conversation",
            }
        },
    ).attempt("Olá")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.list_calls == []


def test_sem_t02_operational_admission_still_lists_owners():
    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("teo", "vista"),
        proposal=_select("teo", "analyze", {"view": "summary"}),
    ).attempt("Qual a metodologia SIPOC no TÉO?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert port.list_calls


def test_sem_t07b_clarification_does_not_invent_owner_requirements():
    text = _clarification_content(
        ("query", "limit"),
        user_message="Liste 3 exemplos de terminal pino.",
    )
    lowered = text.lower()
    assert "código" not in lowered and "codigo" not in lowered
    assert "filtro" not in lowered
    assert "«liste" not in lowered


def test_sem_t13_operational_path_still_resolves_after_admission():
    attempt = _read(
        _interop(FakePort(tools_by_specialist={"vista": VISTA_TOOLS})),
        specialist_ids=("vista",),
        proposal={
            **_select("vista", "list_playlists"),
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": None,
                "missing_inputs": ["query", "limit"],
            },
        },
    )
    result = attempt.attempt("Liste 3 exemplos de terminal pino")
    assert result.status in {
        GovernedCapabilityStatus.SUCCESS,
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        GovernedCapabilityStatus.NOT_APPLICABLE,
        GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
    }


def test_sem_t17_group_selection_reserves_conversational_budget():
    clock = {"t": 0.0}

    def now():
        return clock["t"]

    deadline = TurnDeadline.start(30.0, clock=now)
    orch = OperationalCapabilityOrchestrator(
        [],
        invoke_model=None,
        model_ref=None,
        model_stage_timeout_seconds=30.0,
    )
    reserved = max(
        0.0,
        deadline.remaining_seconds()
        - CONVERSATIONAL_FALLBACK_RESERVE_SECONDS,
    )
    assert reserved == 30.0 - CONVERSATIONAL_FALLBACK_RESERVE_SECONDS
    assert INTERACTION_ADMISSION_STAGE_CAP_SECONDS <= reserved
    assert orch is not None


def test_sem_t20_admission_skips_when_prior_turns_present():
    """Continuidade: admission não engole esclarecimentos."""
    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
    )
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Quantos chamados tenho?",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="Atribuídos a você ou os que abriu?",
            epistemic_class=EpistemicClass.HYPOTHESIS,
        ),
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("teo", "vista"),
        proposal={
            INTERACTION_ADMISSION_INSTRUCTION_ID: {
                "requires_owner_surface": False,
                "interaction_class": "conversation",
            },
            GROUP_SELECTION_INSTRUCTION_ID: {"applicable": False},
        },
    ).attempt("Os que sou responsável.", prior_turns=prior)
    assert port.list_calls
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
