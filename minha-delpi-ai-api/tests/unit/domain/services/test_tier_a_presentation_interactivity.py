"""R11 — chips pós-resposta alinhados a presentationDecision (tier A)."""

from __future__ import annotations

import pytest

from tests.fixtures.presentation_interactivity_gate import (
    build_metadata,
    interactivity_labels,
    tier_a_interactivity_cases,
    validate_tier_a_interactivity_cases,
)


@pytest.mark.parametrize(
    "case",
    tier_a_interactivity_cases(),
    ids=lambda item: str(item["id"]),
)
def test_tier_a_post_response_chips(case: dict):
    metadata = build_metadata(case)
    labels = interactivity_labels(metadata)

    for expected in case["expected_interactivity_labels"]:
        assert expected in labels, f"esperado «{expected}» em {labels}"


def test_interactivity_gate_has_no_tier_a_gaps():
    warnings = validate_tier_a_interactivity_cases()

    assert warnings == [], "\n".join(warnings)
