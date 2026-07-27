"""Unit — importação em lote de NCs LMP (substituição total)."""

from __future__ import annotations

from typing import Any

from app.application.use_cases.lmp_nonconformity.import_lmp_nonconformities_use_case import (
    ImportLmpNonconformitiesUseCase,
    normalize_import_item,
)


class _FakeRepo:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []
        self.deleted_all_calls = 0
        self.existing_count = 0

    def delete_all_records(self) -> int:
        self.deleted_all_calls += 1
        count = self.existing_count
        self.existing_count = 0
        return count

    def create_record(self, **kwargs: Any) -> dict[str, Any]:
        record = {"id": f"new-{len(self.created) + 1}", **kwargs}
        self.created.append(record)
        return record


def test_normalize_import_item_aligns_registered_at_to_occurrence() -> None:
    fields = normalize_import_item(
        {
            "id": "abc",
            "occurrence_date": "2025-09-23",
            "registered_at": "2025-09-23T16:19:35-03:00",
            "created_by": "x",
            "product_codes": ["90001"],
            "status": "done",
            "sale_number": "123",
            "lmp_number": "LEG-9",
            "problem_tags": ["Medida"],
            "products": [],
        }
    )
    assert fields["occurrence_date"] == "2025-09-23"
    assert fields["registered_at"] == "2025-09-23T16:19:35-03:00"
    assert fields["sale_number"] == "123"
    assert fields["lmp_number"] == "LEG-9"
    assert fields["products"] == [{"product_code": "90001", "product_description": ""}]


def test_normalize_forces_registered_at_same_day_as_occurrence() -> None:
    fields = normalize_import_item(
        {
            "status": "done",
            "occurrence_date": "2026-05-18",
            "registered_at": "2026-01-01T12:00:00-03:00",
        }
    )
    assert fields["occurrence_date"] == "2026-05-18"
    assert fields["registered_at"] == "2026-05-18T00:00:00-03:00"


def test_import_replaces_all_then_creates() -> None:
    repo = _FakeRepo()
    repo.existing_count = 7
    use_case = ImportLmpNonconformitiesUseCase(repo)

    result = use_case.execute(
        [
            {"status": "open", "sale_number": "1", "occurrence_date": "2026-01-01"},
            {
                "status": "done",
                "sale_number": "999",
                "occurrence_date": "2026-02-01",
                "defect_description": "Novo caso",
                "problem_tags": ["Desenho"],
                "products": [{"product_code": "90", "product_description": "X"}],
            },
        ],
        actor_user_id="u1",
        actor_email="a@b.c",
        actor_name="Ana",
        created_by="Ana",
    )

    assert repo.deleted_all_calls == 1
    assert result.deleted == 7
    assert result.created == 2
    assert result.skipped == 0
    assert result.errors == 0
    assert repo.created[0]["sale_number"] == "1"
    assert repo.created[0]["registered_at"] == "2026-01-01T00:00:00-03:00"
    assert repo.created[1]["sale_number"] == "999"
    assert repo.created[1]["actor_user_id"] == "u1"


def test_import_dry_run_does_not_persist() -> None:
    repo = _FakeRepo()
    repo.existing_count = 3
    use_case = ImportLmpNonconformitiesUseCase(repo)
    result = use_case.execute(
        [{"status": "open", "sale_number": "1", "defect_description": "A"}],
        dry_run=True,
    )
    assert repo.deleted_all_calls == 0
    assert result.deleted == 0
    assert result.created == 1
    assert result.items[0]["result"] == "would_replace_all"
    assert result.items[1]["result"] == "would_create"
    assert repo.created == []


def test_import_ignores_skip_existing_and_still_replaces() -> None:
    repo = _FakeRepo()
    repo.existing_count = 2
    use_case = ImportLmpNonconformitiesUseCase(repo)
    result = use_case.execute(
        [
            {
                "id": "whatever",
                "status": "open",
                "sale_number": "123",
                "occurrence_date": "2026-03-01",
                "defect_description": "Folga",
                "problem_tags": ["Medida"],
            }
        ],
        skip_existing=True,
    )
    assert repo.deleted_all_calls == 1
    assert result.deleted == 2
    assert result.created == 1
    assert result.skipped == 0
