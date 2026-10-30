"""Cycle-2 contract tests — Task 19 iterative reliability.

RED tests for proven defects:
- RC-J: digit-only strings (product codes like ``10081004``) were
  date-parsed by ``fromisoformat`` and rendered as ``04/10/1008`` —
  the owner value must be rendered verbatim.
- RC-E: native_assessment must recognise a native discovery/resolution
  capability as the designation resolver.
- RC-G: turn_goal must bind the resolved referent (with identifier),
  never the requested attribute word, as business_subject.
- RC-H select_group: a named provider absent from the live surface and
  an out-of-domain subject are non-applicable.
- RC-A residual: candidate_arguments binds business_subject verbatim and
  keeps literal identifiers out of descriptive phrases.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import pytest

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "config",
    "orchestration_instructions.delpi.json",
)


def _instruction(name: str) -> str:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["instructions"][name]


# ---------- RC-J: temporal parse must not corrupt identifiers ----------


def test_digit_only_strings_are_not_temporal():
    from app.application.capability_provision.outcome_assessment import (
        parse_temporal_value,
    )

    # product codes / identifiers that fromisoformat would corrupt
    assert parse_temporal_value("10081004") is None
    assert parse_temporal_value("10080092") is None
    # real ISO dates still parse
    assert parse_temporal_value("2026-10-29") is not None
    assert parse_temporal_value("2026-10-29T14:30:00") is not None


def test_cri_scalar_text_renders_product_code_verbatim():
    from app.application.capability_provision.conversational_response import (
        cri_scalar_text,
    )

    assert cri_scalar_text("10081004") == "10081004"
    assert cri_scalar_text("2026-10-29") == "29/10/2026"


# ---------- RC-E: native discovery resolves designations ----------


def test_native_assessment_recognises_discovery_resolver():
    text = _instruction("delia.capability_orchestration.native_assessment")
    lowered = text.lower()
    assert "discovery" in lowered
    assert "designation resolver" in lowered or "resolve the designation" in lowered


# ---------- RC-G: referent binding in turn_goal ----------


def test_turn_goal_binds_resolved_referent_not_attribute_word():
    text = _instruction("delia.capability_orchestration.turn_goal").lower()
    assert "resolved" in text
    # requested attribute words are answer requirements, not the subject
    assert "answer requirement" in text
    # positional qualifiers go to requirements/constraints, not the subject
    assert "qualifier" in text or "positional" in text


# ---------- RC-H: absent provider / out-of-domain non-applicable ----------


def test_select_group_handles_absent_named_provider():
    text = _instruction("delia.capability_orchestration.select_group").lower()
    assert "not on the listed surface" in text or "absent from the listed surface" in text
    assert "substitute" in text


# ---------- RC-A residual: verbatim subject + identifier separation ----------


def test_candidate_arguments_verbatim_subject_and_identifier_split():
    text = _instruction(
        "delia.capability_orchestration.candidate_arguments"
    ).lower()
    assert "verbatim" in text
    assert "identifier" in text
    # quantity belongs in numeric fields, never in free text
    assert "numeric" in text or "page_size" in text


# ---------- ordinal/listing rule present in both select_capability texts


def test_select_capability_ordinal_listing_rule():
    for key in (
        "delia.capability_orchestration.select_capability",
        "delia.capability_orchestration.select_capability#with_goal",
    ):
        text = _instruction(key).lower()
        assert "ordinal" in text
        assert "identifier" in text


# ---------- RC-E deterministic guard: native discovery resolver ----------


def _assess_with_group(orchestrator, group):
    return orchestrator._assess_native_path(
        "Me de dois exemplos de terminal bala",
        group,
        group.capabilities[0],
        "corr-test",
        None,
        (),
        goal=None,
        deadline=None,
    )


def test_foreign_status_rejected_when_native_discovery_present():
    from app.domain.specialist_interop.model import (
        SpecialistOperationClass,
    )
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cap,
        _cri_clause,
        _group,
        _outcome,
        _query_cap,
        FakeProposalModel,
        FakeProvider,
    )

    disc = _cap(
        "alpha",
        "mcp",
        "discover_items",
        op_class=SpecialistOperationClass.DISCOVERY,
    )
    group = _group("pa", "alpha", [_query_cap(), disc])
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={("alpha", "search_items"): _outcome("ok")},
    )
    clause = _cri_clause()
    orch = build_engine(
        "delia",
        providers=[provider],
        model=FakeProposalModel(
            [{"status": "foreign_evidence_required"}]
        ),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    # A native DISCOVERY capability resolves designations itself —
    # foreign evidence violates the declared invariant.
    assert _assess_with_group(orch, group) == "sufficient"


def test_foreign_status_preserved_without_native_discovery():
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cri_clause,
        _group,
        _outcome,
        _query_cap,
        FakeProposalModel,
        FakeProvider,
    )

    group = _group("pa", "alpha", [_query_cap()])
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={("alpha", "search_items"): _outcome("ok")},
    )
    clause = _cri_clause()
    orch = build_engine(
        "delia",
        providers=[provider],
        model=FakeProposalModel(
            [{"status": "foreign_evidence_required"}]
        ),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    assert _assess_with_group(orch, group) == "foreign_evidence_required"


# ---------- RC-F guard: verbatim request in free-text args ----------


def test_verbatim_request_in_free_text_is_rejected():
    from app.application.capability_provision.orchestration import (
        _free_text_is_verbatim_request,
    )

    assert _free_text_is_verbatim_request(
        {"query": "tem algum terminal pra fio de 2,5mm?"},
        "tem algum terminal pra fio de 2,5mm?",
        "terminal para fio de 2,5mm",
    )
    assert _free_text_is_verbatim_request(
        {"query": "use o mcp sap para consultar produtos"},
        "use o mcp sap para consultar produtos",
        "produtos",
    )
    # a subject-derived value or a different search phrase is fine
    assert not _free_text_is_verbatim_request(
        {"query": "terminal 2,5mm"},
        "tem algum terminal pra fio de 2,5mm?",
        "terminal para fio de 2,5mm",
    )
    assert not _free_text_is_verbatim_request(
        {"query": "terminal para fio de 2,5mm"},
        "tem algum terminal pra fio de 2,5mm?",
        "terminal para fio de 2,5mm",
    )


def test_resolver_instruction_covers_identifier_producing_search():
    text = _instruction("delia.capability_orchestration.select_resolver")
    lowered = text.lower()
    assert "identifier" in lowered
    assert "output" in lowered or "supplies" in lowered


# ---------- Cycle 4: optional-arg elision + resolver retry ----------


def test_unproven_optional_args_are_elided():
    from app.application.capability_provision.orchestration import (
        _elide_unproven_optional_args,
    )
    from tests.test_goal_evidence_relevance import _cap

    schema = {
        "type": "object",
        "required": ["action", "entity"],
        "properties": {
            "action": {"type": "string"},
            "entity": {"type": "string"},
            "date_from": {"type": "string"},
            "date_to": {"type": "string"},
            "page_size": {"type": "integer"},
            "fase": {"type": "string"},
            "note": {"type": "string"},
            "date_field": {"type": "string"},
        },
    }
    cap = _cap("alpha", "mcp", "record_read", schema=schema)
    cleaned = _elide_unproven_optional_args(
        {
            "action": "search",
            "entity": "process",
            "page_size": 10,
            "date_from": "2024-01-01",   # invented — not in request
            "date_to": "2024-12-31",     # invented
            "fase": "",                  # empty optional
            "note": "None",              # null marker
            "date_field": "last_updated",  # invented field-name filter
        },
        cap,
        "qual o último processo do Transforma+?",
        None,
    )
    assert cleaned == {
        "action": "search",
        "entity": "process",
        "page_size": 10,
    }


def test_unproven_optional_args_preserve_proven_and_required():
    from app.application.capability_provision.orchestration import (
        _elide_unproven_optional_args,
    )
    from tests.test_goal_evidence_relevance import _cap

    schema = {
        "type": "object",
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "date_from": {"type": "string"},
            "id": {"type": "string"},
        },
    }
    cap = _cap("alpha", "mcp", "read", schema=schema)
    cleaned = _elide_unproven_optional_args(
        {
            "action": "search",
            "date_from": "2025-10-01",  # proven — present in request
            "id": "PROC-0105",          # required? no — optional id
        },
        cap,
        "mostre processos desde 2025-10-01",
        None,
    )
    # proven temporal value survives; optional id is untouched
    # (identifier provenance belongs to _unproven_identifier_inputs)
    assert cleaned["date_from"] == "2025-10-01"
    assert cleaned["id"] == "PROC-0105"


def test_resolver_select_excludes_attempted():
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cap,
        _cri_clause,
        _group,
        _outcome,
        _query_cap,
        FakeProposalModel,
        FakeProvider,
    )

    other = _cap("alpha", "mcp", "context_read")
    target = _query_cap()
    group = _group("pa", "alpha", [target, other])
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={("alpha", "search_items"): _outcome("ok")},
    )
    clause = _cri_clause()
    orch = build_engine(
        "delia",
        providers=[provider],
        model=FakeProposalModel(
            [{"applicable": True, "remote_name": "context_read"}]
        ),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    # excluding the only eligible candidate leaves none -> None
    assert (
        orch._select_resolver(
            "q",
            target,
            ("item_id",),
            group,
            None,
            (),
            "corr",
            None,
            exclude=frozenset({"context_read"}),
        )
        is None
    )


def test_unproven_optional_string_elided_free_text_kept():
    from app.application.capability_provision.orchestration import (
        _elide_unproven_optional_args,
    )
    from tests.test_goal_evidence_relevance import _cap

    schema = {
        "type": "object",
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "query": {"type": "string"},
            "date_field": {"type": "string"},
            "status": {"type": "string"},
        },
    }
    cap = _cap("alpha", "mcp", "record_read", schema=schema)
    cleaned = _elide_unproven_optional_args(
        {
            "action": "search",
            "query": "terminal bala",
            "date_field": "last_updated",
            "status": "active",
        },
        cap,
        "qual o ultimo processo?",
        None,
    )
    # free-text search keys keep reformulated values; invented
    # temporal/filter keys are dropped; other optional keys stay
    assert cleaned == {
        "action": "search",
        "query": "terminal bala",
        "status": "active",
    }
