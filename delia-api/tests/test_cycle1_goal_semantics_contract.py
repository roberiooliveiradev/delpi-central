"""Task 19 cycle 1 (DELIA-C3-LOCAL-INTELLIGENCE-ITERATIVE-RELIABILITY-80PCT-01):
semantic contract gaps proven by the v28 baseline battery.

Each assertion pins a contract element whose absence produced a
trace-proven failure on the real local chain (Qwen3 4B, LangGraph B1):

- b_faston: select_capability emitted business_subject
  "tipos de conector faston" — request-pattern quantifier verbiage
  copied as the business subject — and candidate_arguments bound it
  verbatim into the lexical description search, returning an empty
  collection while the oracle returned 8 records.
- e_proc_followup: turn_goal classified "quem e o responsavel por
  ele?" as clarify even though the referent PROC-0105 was present in
  the prior DELIA result — an unnecessary clarification in place of
  referent resolution.
- ord_latest: select_capability chose get_process_timeline (requires
  processo_id) for "o ultimo processo" — an ordinal/listing goal —
  producing a legitimate missing-input clarification instead of the
  owner-resolvable listing.
- a_playlist_noctx: select_group returned applicable=false for a
  create_or_modify playlist goal although the vista group advertises
  PREPARE-class capabilities.

These are contract completeness assertions, not keyword routing: the
model still decides; the contract must stop hiding the decision rule.
"""

from __future__ import annotations

import json
from pathlib import Path

_RESOURCE = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "orchestration_instructions.delpi.json"
)


def _instruction(key: str) -> str:
    return json.loads(_RESOURCE.read_text(encoding="utf-8"))[
        "instructions"
    ][key]


def test_business_subject_excludes_request_verbiage():
    """business_subject names the business thing — request-pattern
    quantifiers and format words ("tipos de", "exemplos de", "N
    exemplos", "liste", "mostre") are answer requirements, never part
    of the subject designation."""
    for key in (
        "delia.capability_orchestration.turn_goal",
        "delia.capability_orchestration.select_capability#with_goal",
    ):
        text = _instruction(key).lower()
        assert "answer requirement" in text or "answer_requirements" in text
        assert "not part of the subject" in text


def test_clarify_excludes_resolvable_anaphora():
    """goal_class "clarify" must not apply when the referent is
    already present in earlier conversation turns — anaphoric
    follow-ups resolve by continuity, not by asking the user what
    they already established."""
    text = _instruction("delia.capability_orchestration.turn_goal")
    assert "clarify" in text
    assert "referent" in text.lower()
    assert "anaphor" in text.lower() or "ele\"" in text.lower()


def test_ordinal_goals_prefer_listing_capabilities():
    """A descriptive ordinal/superlative ("ultimo", "mais recente",
    "primeiro") identifies by ordering, not by identifier — the
    selection must prefer a capability whose required arguments do
    not demand that entity's literal identifier."""
    for key in (
        "delia.capability_orchestration.select_capability",
        "delia.capability_orchestration.select_capability#with_goal",
    ):
        text = _instruction(key).lower()
        assert "ordinal" in text or "superlative" in text
        assert "identifier" in text


def test_select_group_covers_create_or_modify_goals():
    """select_group must treat create/prepare/modify requests for a
    governed object (e.g. playlist of TV programming) as applicable
    to the group advertising PREPARE-class capabilities for that
    domain — preparation is a legitimate governed operation, not a
    non-applicable request."""
    text = _instruction("delia.capability_orchestration.select_group")
    lowered = text.lower()
    assert "create_or_modify" in lowered or "prepare" in lowered
    assert "prepare" in lowered


def test_four_status_vocabulary_unchanged():
    """Cycle-1 edits must not alter the native_assessment four-status
    contract delivered by v28."""
    text = _instruction("delia.capability_orchestration.native_assessment")
    for status in (
        "sufficient",
        "foreign_evidence_required",
        "corroboration_requested",
        "inconclusive",
    ):
        assert f'"{status}"' in text
