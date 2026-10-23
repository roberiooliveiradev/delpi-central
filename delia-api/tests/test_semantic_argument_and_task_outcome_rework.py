"""SEMARG rework — no linguistic heuristic argument projection.

TASK: DELIA-C3-SEMANTIC-ARGUMENT-AND-TASK-OUTCOME-REWORK-01
"""

from __future__ import annotations

from app.application.capability_provision import orchestration as orch
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    _clarification_content,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from tests.conftest import load_test_orchestration_instructions
from tests.test_specialist_capability_orchestration import (
    FakePort,
    TEO_TOOLS,
    VISTA_TOOLS,
    _interop,
    _read,
    _select,
)


def test_semarg_t01_no_quantity_regex_helper_in_orchestration():
    """Heuristic quantity/search recovery must not exist (doc 49 REWORK)."""
    assert not hasattr(orch, "_recover_stated_arguments_from_input")
    assert not hasattr(orch, "_STATED_QUANTITY_RE")
    assert not hasattr(orch, "_STATED_SEARCH_FIELD_HINTS")
    assert not hasattr(orch, "_STATED_LIMIT_FIELD_HINTS")


def test_semarg_t03_year_not_auto_limit_via_removed_heuristic():
    # Guard: no module-level quantity regex that would treat 2026 as limit.
    source = orch.__file__
    text = open(source, encoding="utf-8").read()
    assert "_STATED_QUANTITY_RE" not in text
    assert "stated_input_recovery" not in text


def test_semarg_t05_hypothetical_admission_skips_owner():
    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("teo", "vista"),
        proposal={
            INTERACTION_ADMISSION_INSTRUCTION_ID: {
                "requires_owner_surface": False,
                "interaction_class": "hypothetical",
            }
        },
    ).attempt("Liste 2 exemplos de terminal pino.")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.list_calls == []


def test_semarg_t07_real_catalog_admission_lists_owners():
    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("teo", "vista"),
        proposal=_select("teo", "analyze", {"view": "summary"}),
    ).attempt("Quais produtos do tipo terminal pino estão cadastrados?")
    assert port.list_calls
    assert attempt.status is GovernedCapabilityStatus.SUCCESS


def test_semarg_t12_clarification_does_not_invent_codigo_filtro():
    text = _clarification_content(
        ("topic", "guide_id"),
        user_message="Liste 2 exemplos de terminal pino.",
    )
    lowered = text.lower()
    assert "código" not in lowered and "codigo" not in lowered
    assert "filtro" not in lowered
    assert "escopo" not in lowered
    # Must not quote the whole user request as a faux-specific ask.
    assert "«liste 2 exemplos" not in lowered


def test_semarg_t09_model_proposed_query_still_validated():
    """LLM proposes arguments; schema validation remains the gate."""
    attempt = _read(
        _interop(FakePort(tools_by_specialist={"vista": VISTA_TOOLS})),
        specialist_ids=("vista",),
        proposal={
            **_select("vista", "list_playlists"),
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {"query": "terminal pino", "limit": 2},
                "missing_inputs": [],
            },
        },
    ).attempt("Liste 2 exemplos de terminal pino.")
    assert attempt.status in {
        GovernedCapabilityStatus.SUCCESS,
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        GovernedCapabilityStatus.NOT_APPLICABLE,
        GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
    }


def test_semarg_t24_cold_greeting_regression():
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


def test_semarg_t21_admission_instruction_forbids_regex_intent():
    # Instruction guides the LLM; it must not encode phrase tables.
    instr = load_test_orchestration_instructions()[
        orch.INTERACTION_ADMISSION_INSTRUCTION_ID
    ].lower()
    assert "hypothetical" in instr
    assert "cadastrados" in instr or "registered" in instr
    # No terminal-pino hardcoding.
    assert "terminal pino" not in instr
