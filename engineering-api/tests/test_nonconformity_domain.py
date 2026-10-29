"""Domínio NC — streak, diff de histórico, sort whitelist e normalize.

Paridade exigida com a semântica legado (api-delpi) — mesmas entradas,
mesmas saídas (T6).
"""

from __future__ import annotations

from datetime import date

from engineering_app.domain.nonconformity.history_diff import (
    build_nc_history_changes,
)
from engineering_app.domain.nonconformity.normalize import (
    normalize_problem_tag_labels,
    normalize_products,
)
from engineering_app.domain.nonconformity.sort import resolve_nc_sort
from engineering_app.domain.nonconformity.streak import (
    coerce_occurrence_date,
    compute_occurrence_streak,
)


class TestStreak:
    def test_no_occurrences_no_anchor(self):
        result = compute_occurrence_streak([], as_of=date(2026, 5, 10))
        assert result == {
            "current_days_without_nc": 0,
            "record_days_without_nc": 0,
            "last_nc_date": None,
            "reference_start_date": None,
            "as_of_date": "2026-05-10",
            "nc_count": 0,
        }

    def test_no_occurrences_with_anchor(self):
        result = compute_occurrence_streak(
            [], as_of=date(2026, 5, 10), reference_start_date=date(2026, 5, 1)
        )
        assert result["current_days_without_nc"] == 9
        assert result["record_days_without_nc"] == 9
        assert result["reference_start_date"] == "2026-05-01"
        assert result["nc_count"] == 0

    def test_current_and_record_gaps(self):
        result = compute_occurrence_streak(
            [date(2026, 5, 1), date(2026, 5, 8), date(2026, 5, 9)],
            as_of=date(2026, 5, 10),
        )
        assert result["current_days_without_nc"] == 1
        assert result["record_days_without_nc"] == 7
        assert result["last_nc_date"] == "2026-05-09"
        assert result["nc_count"] == 3

    def test_occurrence_on_as_of_resets_to_zero(self):
        result = compute_occurrence_streak(
            [date(2026, 5, 10)], as_of=date(2026, 5, 10)
        )
        assert result["current_days_without_nc"] == 0
        assert result["nc_count"] == 1

    def test_future_dates_ignored(self):
        result = compute_occurrence_streak(
            [date(2026, 5, 1), date(2026, 6, 1)], as_of=date(2026, 5, 10)
        )
        assert result["current_days_without_nc"] == 9
        assert result["last_nc_date"] == "2026-05-01"
        assert result["nc_count"] == 1

    def test_duplicate_dates_counted_once(self):
        result = compute_occurrence_streak(
            [date(2026, 5, 1), date(2026, 5, 1)], as_of=date(2026, 5, 10)
        )
        assert result["nc_count"] == 1

    def test_coerce_variants(self):
        from datetime import datetime

        assert coerce_occurrence_date(None) is None
        assert coerce_occurrence_date("") is None
        assert coerce_occurrence_date("garbage") is None
        assert coerce_occurrence_date("2026-05-01") == date(2026, 5, 1)
        assert coerce_occurrence_date(datetime(2026, 5, 1, 12, 0)) == date(
            2026, 5, 1
        )
        assert coerce_occurrence_date(date(2026, 5, 1)) == date(2026, 5, 1)


class TestHistoryDiff:
    def test_create_lists_non_empty_fields(self):
        changes = build_nc_history_changes(
            None,
            {
                "status": "open",
                "sale_number": "003696",
                "problem_tags": ["Medida"],
                "products": [
                    {"product_code": "P1", "product_description": "Desc"}
                ],
            },
        )
        fields = {f["field"] for f in changes["fields"]}
        assert "status" in fields
        assert "sale_number" in fields
        assert "problem_tags" in fields
        assert "products" in fields
        assert "customer_name" not in fields

    def test_update_tracks_scalar_change(self):
        before = {"status": "open", "sale_number": "003696"}
        after = {"status": "done", "sale_number": "003696"}
        changes = build_nc_history_changes(before, after)
        assert changes["fields"] == [
            {"field": "status", "label": "Status", "old": "open", "new": "done"}
        ]

    def test_update_tracks_tags_and_products(self):
        before = {"problem_tags": ["Medida"], "products": []}
        after = {
            "problem_tags": ["Desenho"],
            "products": [{"product_code": "P2", "product_description": "D"}],
        }
        changes = build_nc_history_changes(before, after)
        fields = {f["field"] for f in changes["fields"]}
        assert fields == {"problem_tags", "products"}

    def test_no_change_no_fields(self):
        same = {"status": "open", "problem_tags": ["Medida"]}
        changes = build_nc_history_changes(same, dict(same))
        assert changes["fields"] == []

    def test_tag_dedup_case_insensitive(self):
        changes = build_nc_history_changes(
            None, {"problem_tags": ["Medida", "MEDIDA", "medida"]}
        )
        tag_field = next(
            f for f in changes["fields"] if f["field"] == "problem_tags"
        )
        assert tag_field["new"] == ["Medida"]


class TestSort:
    def test_defaults(self):
        assert resolve_nc_sort(None, None) == ("occurrence_date", "desc")

    def test_valid(self):
        assert resolve_nc_sort("status", "asc") == ("status", "asc")

    def test_invalid_falls_back(self):
        assert resolve_nc_sort("evil_column", "sideways") == (
            "occurrence_date",
            "desc",
        )


class TestNormalize:
    def test_tags(self):
        assert normalize_problem_tag_labels(
            ["  Medida  ", "MEDIDA", "", None, "Outra " * 20]
        ) == ["Medida", "Outra " * 13 + "Ou"]

    def test_tag_max_80(self):
        assert normalize_problem_tag_labels(["x" * 200]) == ["x" * 80]

    def test_products_dedup_upper_sorted(self):
        out = normalize_products(
            [
                {"product_code": " b2 "},
                {"product_code": "A1", "description": "Desc A"},
                {"product_code": "B2"},
                {"product_code": ""},
                "not-a-dict",
            ]
        )
        assert out == [
            {"product_code": "A1", "product_description": "Desc A"},
            {"product_code": "B2", "product_description": ""},
        ]
