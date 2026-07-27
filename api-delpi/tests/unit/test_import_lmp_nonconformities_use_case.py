"""Unit — importação em lote de NCs LMP."""

from __future__ import annotations

from typing import Any

from app.application.use_cases.lmp_nonconformity.import_lmp_nonconformities_use_case import (
    ImportLmpNonconformitiesUseCase,
    normalize_import_item,
)


class _FakeRepo:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []
        self.by_id: dict[str, dict[str, Any]] = {}
        self.duplicates: list[dict[str, Any]] = []

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        return self.by_id.get(record_id)

    def find_import_duplicate(
        self,
        *,
        sale_number: str | None,
        defect_description: str | None,
        problem_tags: list[str] | None,
    ) -> dict[str, Any] | None:
        wanted = {
            str(tag).strip().casefold()
            for tag in (problem_tags or [])
            if str(tag).strip()
        }
        for item in self.duplicates:
            if (item.get("sale_number") or None) != (sale_number or None):
                continue
            if (item.get("defect_description") or None) != (defect_description or None):
                continue
            tags = {
                str(tag).strip().casefold()
                for tag in (item.get("problem_tags") or [])
                if str(tag).strip()
            }
            if tags == wanted:
                return item
        return None

    def create_record(self, **kwargs: Any) -> dict[str, Any]:
        record = {"id": f"new-{len(self.created) + 1}", **kwargs}
        self.created.append(record)
        return record


def test_normalize_import_item_strips_server_fields() -> None:
    fields = normalize_import_item(
        {
            "id": "abc",
            "registered_at": "2026-01-01T00:00:00Z",
            "created_by": "x",
            "product_codes": ["90001"],
            "status": "done",
            "sale_number": "123",
            "lmp_number": "LEG-9",
            "problem_tags": ["Medida"],
            "products": [],
        }
    )
    assert "id" not in fields or fields.get("source_id") == "abc"
    assert fields["status"] == "done"
    assert fields["sale_number"] == "123"
    assert fields["lmp_number"] == "LEG-9"
    assert fields["products"] == [{"product_code": "90001", "product_description": ""}]
    assert fields["problem_tags"] == ["Medida"]


def test_import_creates_and_skips_by_id() -> None:
    repo = _FakeRepo()
    repo.by_id["existing"] = {"id": "existing", "sale_number": "1"}
    use_case = ImportLmpNonconformitiesUseCase(repo)

    result = use_case.execute(
        [
            {"id": "existing", "status": "open", "sale_number": "1"},
            {
                "status": "open",
                "sale_number": "999",
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

    assert result.skipped == 1
    assert result.created == 1
    assert result.errors == 0
    assert repo.created[0]["sale_number"] == "999"
    assert repo.created[0]["actor_user_id"] == "u1"


def test_import_dry_run_does_not_persist() -> None:
    repo = _FakeRepo()
    use_case = ImportLmpNonconformitiesUseCase(repo)
    result = use_case.execute(
        [{"status": "open", "sale_number": "1", "defect_description": "A"}],
        dry_run=True,
    )
    assert result.created == 1
    assert result.items[0]["result"] == "would_create"
    assert repo.created == []


def test_import_skips_natural_duplicate() -> None:
    repo = _FakeRepo()
    repo.duplicates.append(
        {
            "id": "dup-1",
            "sale_number": "123",
            "defect_description": "Folga",
            "problem_tags": ["Medida"],
        }
    )
    use_case = ImportLmpNonconformitiesUseCase(repo)
    result = use_case.execute(
        [
            {
                "status": "open",
                "sale_number": "123",
                "defect_description": "Folga",
                "problem_tags": ["Medida"],
            }
        ]
    )
    assert result.skipped == 1
    assert result.created == 0
    assert result.items[0]["reason"] == "already_exists"
