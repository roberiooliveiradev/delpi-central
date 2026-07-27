"""Unit — normalização de labels de tags NC LMP."""

from __future__ import annotations

from app.domain.services.lmp.lmp_problem_tag_normalize import (
    normalize_problem_tag_label,
    normalize_problem_tag_labels,
)


def test_normalize_label_trims_and_collapses() -> None:
    assert normalize_problem_tag_label("  Medida  ") == "Medida"
    assert normalize_problem_tag_label("  a   b  ") == "a b"
    assert normalize_problem_tag_label("   ") is None


def test_normalize_labels_dedupes_casefold() -> None:
    assert normalize_problem_tag_labels(["Medida", "medida", "Desenho", ""]) == [
        "Medida",
        "Desenho",
    ]
