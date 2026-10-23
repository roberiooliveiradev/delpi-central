"""Q02-C B2 — comparison outcome follows typed field diffs.

A rendered heading is presentation. The decision reads
``_selected_proven_differences`` from the proposal and the records.
"""

from __future__ import annotations

from pathlib import Path

from app.infrastructure.config.cri_instruction_resource import (
    load_cri_presentation_vocabulary,
)


_VOCAB_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "cri_presentation.delpi.json"
)
_LABELS = load_cri_presentation_vocabulary(_VOCAB_PATH).field_labels

import app.application.capability_provision.orchestration as orch_mod
from app.application.capability_provision.orchestration import (
    _selected_proven_differences,
)
from app.application.capability_provision.outcome_assessment import (
    _prior_supports_typed_attribute_compare,
    _synthesis_selections,
)


def _pair(left: dict, right: dict, fields: list[str]) -> tuple:
    records = (left, right)
    proposal = {
        "presentation": "list",
        "items": [
            {"record_index": 0, "fields": fields},
            {"record_index": 1, "fields": fields},
        ],
    }
    return proposal, records


def test_b2_r1_header_text_is_not_a_comparison_signal():
    assert not hasattr(orch_mod, "_typed_compare_outcome_content")
    proposal, records = _pair(
        {"code": "1", "label": "same"},
        {"code": "1", "label": "same"},
        ["code", "label"],
    )
    assert _selected_proven_differences(proposal, records) == []


def test_b2_r2_typed_diff_is_independent_of_presentation_header():
    proposal, records = _pair(
        {"code": "1", "label": "alpha"},
        {"code": "2", "label": "alpha"},
        ["code", "label"],
    )
    diffs = _selected_proven_differences(
        proposal, records, field_labels=_LABELS
    )
    assert diffs == ["- Código: 1 → 2"]
    assert all("Diferenças comprovadas:" not in line for line in diffs)


def test_b2_r3_free_text_records_are_not_a_typed_compare():
    records = (
        {"excerpt": "primeira alternativa hipotética"},
        {"excerpt": "segunda alternativa hipotética"},
    )
    assert not _prior_supports_typed_attribute_compare(records)
    proposal = {
        "items": [
            {"record_index": 0, "fields": ["excerpt"]},
            {"record_index": 1, "fields": ["excerpt"]},
        ]
    }
    assert _selected_proven_differences(proposal, records) == []


def test_b2_r4_invalid_index_is_fail_closed():
    records = ({"code": "1"}, {"code": "2"})
    proposal = {
        "items": [
            {"record_index": 9, "fields": ["code"]},
            {"record_index": 1, "fields": ["code"]},
        ]
    }
    selections, reason = _synthesis_selections(proposal, records)
    assert selections is None
    assert reason == "invalid_record_index"
    assert _selected_proven_differences(proposal, records) == []


def test_b2_r5_empty_selection_has_no_typed_diff():
    records = ({"code": "1"}, {"code": "2"})
    proposal = {"items": []}
    selections, reason = _synthesis_selections(proposal, records)
    assert selections is None
    assert reason == "empty_selection"
    assert _selected_proven_differences(proposal, records) == []


def test_b2_r6_prior_prose_does_not_become_a_field():
    records = (
        {"excerpt": "id: ticket-123 code: 9"},
        {"excerpt": "id: ticket-456 code: 8"},
    )
    proposal = {
        "items": [
            {"record_index": 0, "fields": ["excerpt"]},
            {"record_index": 1, "fields": ["excerpt"]},
        ]
    }
    assert _selected_proven_differences(proposal, records) == []


def test_b2_r7_equivalent_records_ignore_provider_order_of_fields():
    left = {"sku": "A", "state": "open"}
    right = {"state": "closed", "sku": "A"}
    proposal = {
        "items": [
            {"record_index": 0, "fields": ["state", "sku"]},
            {"record_index": 1, "fields": ["sku", "state"]},
        ]
    }
    diffs = _selected_proven_differences(
        proposal, (left, right), field_labels=_LABELS
    )
    assert diffs == ["- State: open → closed"]


def test_b2_r8_ticket_shortcut_imports_stay():
    assert hasattr(orch_mod, "unique_structural_ticket_list_capability")
    assert hasattr(orch_mod, "classify_result_intent")
