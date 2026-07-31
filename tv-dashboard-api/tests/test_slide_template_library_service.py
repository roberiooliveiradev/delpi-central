"""Aceite Gherkin — biblioteca de templates (serviço de domínio, sem Postgres)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import UUID, uuid4

import pytest

from tv_app.application.services.slide_template_library_service import (
    SlideTemplateConflictError,
    SlideTemplateForbiddenError,
    SlideTemplateLibraryService,
    SlideTemplateValidationError,
    parse_and_validate_mdd,
    validate_native_config,
)
from tv_app.application.services.slide_template_mdd_service import build_slide_template_mdd


class FakeRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}

    def _public(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "key": row["key"],
            "label": row["label"],
            "description": row.get("description"),
            "nativeScreenKey": row.get("native_screen_key", "custom_message"),
            "nativeConfig": deepcopy(row.get("native_config") or {}),
            "durationSec": row.get("duration_sec"),
            "status": row["status"],
            "isSystem": bool(row.get("is_system")),
            "version": int(row.get("version") or 1),
            "title": row["label"],
            "slideType": "native",
            "source": "library",
        }

    def list(
        self,
        *,
        status: str | None = None,
        q: str | None = None,
        is_system: bool | None = None,
        exclude_archived_by_default: bool = True,
    ) -> list[dict[str, Any]]:
        items = []
        for row in self.rows.values():
            if status and row["status"] != status:
                continue
            if not status and exclude_archived_by_default and row["status"] == "archived":
                continue
            if is_system is not None and bool(row.get("is_system")) != is_system:
                continue
            if q and q.strip():
                blob = f"{row['label']} {row['key']} {row.get('description') or ''}".lower()
                if q.strip().lower() not in blob:
                    continue
            items.append(self._public(row))
        return items

    def get(self, template_id: UUID) -> dict[str, Any] | None:
        row = self.rows.get(str(template_id))
        return self._public(row) if row else None

    def get_by_key(self, key: str) -> dict[str, Any] | None:
        for row in self.rows.values():
            if row["key"] == key:
                return self._public(row)
        return None

    def create(self, **kwargs: Any) -> dict[str, Any]:
        tid = str(uuid4())
        row = {
            "id": tid,
            "key": kwargs["key"],
            "label": kwargs["label"],
            "description": kwargs.get("description"),
            "native_screen_key": kwargs.get("native_screen_key", "custom_message"),
            "native_config": deepcopy(kwargs.get("native_config") or {}),
            "duration_sec": kwargs.get("duration_sec"),
            "status": kwargs.get("status", "draft"),
            "is_system": kwargs.get("is_system", False),
            "version": 1,
        }
        self.rows[tid] = row
        return self._public(row)

    def update(self, template_id: UUID, *, expected_version: int, **kwargs: Any) -> dict[str, Any] | None:
        row = self.rows.get(str(template_id))
        if not row:
            return None
        if int(row["version"]) != int(expected_version):
            return {"_conflict": True, "current": self._public(row)}
        content_changed = kwargs.get("content_changed", False)
        if kwargs.get("label") is not None:
            row["label"] = kwargs["label"]
        if kwargs.get("description") is not None:
            row["description"] = kwargs["description"]
        if kwargs.get("native_config") is not None:
            row["native_config"] = deepcopy(kwargs["native_config"])
        if kwargs.get("native_screen_key") is not None:
            row["native_screen_key"] = kwargs["native_screen_key"]
        if kwargs.get("duration_sec") is not None:
            row["duration_sec"] = kwargs["duration_sec"]
        if kwargs.get("status") is not None:
            row["status"] = kwargs["status"]
        elif content_changed and row["status"] == "published":
            row["status"] = "draft"
        row["version"] = int(row["version"]) + 1
        return self._public(row)

    def set_status(self, template_id: UUID, *, status: str, updated_by: str | None) -> dict[str, Any] | None:
        row = self.rows.get(str(template_id))
        if not row:
            return None
        row["status"] = status
        row["version"] = int(row["version"]) + 1
        return self._public(row)

    def delete(self, template_id: UUID) -> dict[str, Any] | None:
        row = self.rows.pop(str(template_id), None)
        return self._public(row) if row else None

    def allocate_unique_key(self, base: str) -> str:
        keys = {r["key"] for r in self.rows.values()}
        if base not in keys:
            return base
        i = 1
        while f"{base}_{i}" in keys:
            i += 1
        return f"{base}_{i}"

    def upsert_system(self, **kwargs: Any) -> dict[str, Any]:
        existing = self.get_by_key(kwargs["key"])
        if existing and not existing.get("isSystem"):
            return existing
        if existing:
            tid = existing["id"]
            row = self.rows[tid]
            row.update(
                {
                    "label": kwargs["label"],
                    "description": kwargs.get("description"),
                    "native_screen_key": kwargs.get("native_screen_key"),
                    "native_config": deepcopy(kwargs.get("native_config") or {}),
                    "duration_sec": kwargs.get("duration_sec"),
                    "status": "published",
                    "is_system": True,
                    "version": int(row["version"]) + 1,
                }
            )
            return self._public(row)
        return self.create(
            key=kwargs["key"],
            label=kwargs["label"],
            description=kwargs.get("description"),
            native_screen_key=kwargs.get("native_screen_key", "custom_message"),
            native_config=kwargs.get("native_config") or {},
            duration_sec=kwargs.get("duration_sec"),
            status="published",
            is_system=True,
            owner_user_id=None,
            updated_by="system-seed",
        )


@pytest.fixture
def service() -> SlideTemplateLibraryService:
    return SlideTemplateLibraryService(FakeRepo())


def test_validate_native_config_rejects_bad_blocks():
    with pytest.raises(SlideTemplateValidationError):
        validate_native_config({"blocks": "nope"})


def test_consumer_only_sees_published(service: SlideTemplateLibraryService):
    service.create(
        label="Draft",
        description=None,
        native_config={"version": 4, "blocks": []},
        status="draft",
    )
    published = service.create(
        label="Pub",
        description=None,
        native_config={"version": 4, "blocks": []},
        publish_now=True,
    )
    items = service.list_published()
    assert all(i["status"] == "published" for i in items)
    assert any(i["id"] == published["id"] for i in items)
    assert all(i["label"] != "Draft" for i in items)


def test_publish_explicit_after_edit(service: SlideTemplateLibraryService):
    item = service.create(
        label="A",
        description=None,
        native_config={"version": 4, "blocks": []},
        publish_now=True,
    )
    updated = service.update(
        UUID(item["id"]),
        expected_version=item["version"],
        native_config={"version": 4, "blocks": [{"id": "b1", "type": "text"}]},
    )
    assert updated["status"] == "draft"
    assert updated["id"] not in {i["id"] for i in service.list_published()}
    published = service.publish(UUID(item["id"]), updated_by="u1")
    assert published["status"] == "published"
    assert published["id"] in {i["id"] for i in service.list_published()}


def test_system_protected_delete_and_clone(service: SlideTemplateLibraryService):
    repo: FakeRepo = service._repo  # type: ignore[attr-defined]
    system = repo.create(
        key="sys",
        label="System",
        description=None,
        native_screen_key="custom_message",
        native_config={"version": 4, "blocks": []},
        duration_sec=45,
        status="published",
        is_system=True,
        owner_user_id=None,
        updated_by="seed",
    )
    with pytest.raises(SlideTemplateForbiddenError):
        service.delete(UUID(system["id"]))
    clone = service.clone(UUID(system["id"]), updated_by="u1", owner_user_id="u1")
    assert clone["isSystem"] is False
    assert clone["status"] == "draft"


def test_optimistic_lock(service: SlideTemplateLibraryService):
    item = service.create(
        label="Lock",
        description=None,
        native_config={"version": 4, "blocks": []},
    )
    with pytest.raises(SlideTemplateConflictError):
        service.update(
            UUID(item["id"]),
            expected_version=0,
            native_config={"version": 4, "blocks": []},
        )


def test_import_invalid_mdd():
    with pytest.raises(SlideTemplateValidationError):
        parse_and_validate_mdd(b"not-a-zip")


def test_import_valid_mdd_roundtrip(service: SlideTemplateLibraryService):
    raw, _ = build_slide_template_mdd(
        key="k1",
        label="Lab",
        description="d",
        title="T",
        duration_sec=40,
        native_config={"version": 4, "blocks": []},
    )
    preview = service.import_preview(raw)
    assert preview["label"] == "Lab"
    created = service.import_apply(raw, publish_now=False)
    assert created["status"] == "draft"
    assert created["isSystem"] is False


def test_apply_is_copy_semantics(service: SlideTemplateLibraryService):
    """Apply no MFE copia nativeConfig — o master permanece intacto após 'apply' simulado."""
    item = service.create(
        label="Master",
        description=None,
        native_config={"version": 4, "blocks": [{"id": "a"}]},
        publish_now=True,
    )
    slide_copy = deepcopy(item["nativeConfig"])
    slide_copy["blocks"] = [{"id": "mutated"}]
    still = service.get(UUID(item["id"]))
    assert still["nativeConfig"]["blocks"] == [{"id": "a"}]
    assert slide_copy["blocks"] == [{"id": "mutated"}]
