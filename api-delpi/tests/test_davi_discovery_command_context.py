"""DAVI command-context discovery corrective (DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-002).

Imperative/orchestration verbs (``gere``/``calcule``/``monte``/``emita``/
``traduza``) are request-form words: they never classify capability by
themselves. Supported topics must reach the governed READ action;
unsupported topics must return zero candidates via semantic evidence
(quarantine/admission floor), not via a verb-based hard block.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
    has_explicit_write_intent,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)

_BASELINE = (
    Path(__file__).resolve().parents[1] / "app" / "content" / "openapi_baseline.json"
)
_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "davi_discovery_command_context_v1.json"
)


@pytest.fixture()
def actions():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()
    seeded = build_technical_actions_from_baseline(
        json.loads(_BASELINE.read_text(encoding="utf-8")),
        allowlist=load_external_read_allowlist(),
    )
    set_actions_for_tests(seeded)
    yield seeded
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()


def _cases(case_type: str) -> list[dict]:
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return [c for c in fixture["cases"] if c["case_type"] == case_type]


def test_command_verbs_are_not_mutation_intent(actions):
    """The mutation guard never fires on orchestration verbs alone."""
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    for case in fixture["cases"]:
        assert has_explicit_write_intent(case["query"]) is False, case["id"]


def test_supported_command_context_reaches_expected_action(actions):
    """Every supported command-context query returns its governed capability
    inside top3 (hard floor); top1 asserted per-case where required."""
    for case in _cases("COMMAND_POSITIVE"):
        ranked = retrieve_eligible_actions(case["query"], actions, top_k=10)
        ids = [a.operation_id for a, _ in ranked]
        assert ids, f"{case['id']} returned zero candidates"
        expected = case["expected_action_ids"][0]
        assert expected in ids[:3], (
            f"{case['id']}: {expected} not in top3 -> {ids[:5]}"
        )
        if case.get("top1_required"):
            assert ids[0] == expected, (
                f"{case['id']}: expected top1 {expected} -> {ids[:5]}"
            )


def test_unsupported_command_context_returns_zero_candidates(actions):
    """Unsupported semantic topics return zero candidates — because no
    eligible action has semantic evidence (quarantine/admission), never
    because an imperative verb blocked retrieval upstream."""
    for case in _cases("COMMAND_UNSUPPORTED"):
        ranked = retrieve_eligible_actions(case["query"], actions, top_k=10)
        assert ranked == [], (
            f"{case['id']} leaked candidates: "
            f"{[a.operation_id for a, _ in ranked]}"
        )
