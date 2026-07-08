from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.application.services.audit_5s.nc_attachment_storage import (
    Audit5sNcAttachmentStorage,
)
from app.application.services.audit_5s.response_attachment_storage import (
    Audit5sResponseAttachmentStorage,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class FakeAudit5sRepo(PostgresAudit5sRepository):
    """Repository stub focusing on response-photo helpers without Postgres."""

    def __init__(self) -> None:
        # Skip PluginBaseRepository connection wiring.
        object.__setattr__(self, "_response_attachments", {})
        object.__setattr__(self, "_nc_attachments", [])
        object.__setattr__(self, "_events", [])
        object.__setattr__(self, "_commits", 0)
        object.__setattr__(self, "_executed", [])
        self._response_attachments: dict[str, dict[str, Any]] = {}
        self._nc_attachments: list[dict[str, Any]] = []
        self._events: list[tuple[Any, ...]] = []
        self._commits = 0
        self._executed: list[tuple[str, tuple[Any, ...] | None]] = []

    def fetch_one(self, query: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        return None

    def fetch_all(self, query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        return []

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> None:
        self._executed.append((query, params))
        if auto_commit:
            self._commits += 1

    def execute_returning_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> dict[str, Any] | None:
        self._executed.append((query, params))
        if "audit_5s_nc_attachments" in query and "INSERT" in query:
            row = {
                "id": "nc-att-1",
                "nonconformity_id": params[0] if params else None,
                "attachment_type": "before",
                "original_name": params[1] if params else None,
                "stored_name": params[2] if params else None,
                "mime_type": params[3] if params else None,
                "size_bytes": params[4] if params else None,
                "uploaded_by_user_id": params[5] if params else None,
                "created_at": "2026-07-08T12:00:00Z",
            }
            self._nc_attachments.append(row)
            if auto_commit:
                self._commits += 1
            return row
        return None

    def commit(self) -> None:
        self._commits += 1

    def list_nc_attachments(self, nonconformity_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._nc_attachments
            if str(item.get("nonconformity_id")) == nonconformity_id
        ]

    def get_response_attachment_by_response_id(
        self, response_id: str
    ) -> dict[str, Any] | None:
        return self._response_attachments.get(response_id)


def test_seed_nc_before_copies_evaluation_photo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response_dir = tmp_path / "responses"
    nc_dir = tmp_path / "nc"
    monkeypatch.setattr(
        "app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository.Audit5sResponseAttachmentStorage",
        lambda: Audit5sResponseAttachmentStorage(base_dir=str(response_dir)),
    )
    monkeypatch.setattr(
        "app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository.Audit5sNcAttachmentStorage",
        lambda: Audit5sNcAttachmentStorage(base_dir=str(nc_dir)),
    )

    response_storage = Audit5sResponseAttachmentStorage(base_dir=str(response_dir))
    file_name, _ = response_storage.save(
        response_id="resp-abc",
        original_name="avaliacao.jpg",
        content=b"foto-avaliacao",
        mime_type="image/jpeg",
    )

    repo = FakeAudit5sRepo()
    repo._response_attachments["resp-abc"] = {
        "id": "att-1",
        "response_id": "resp-abc",
        "file_name": file_name,
        "original_name": "avaliacao.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": len(b"foto-avaliacao"),
        "storage_path": f"resp-abc/{file_name}",
        "uploaded_by_user_id": "user-1",
    }

    seeded = repo.seed_nc_before_from_response_attachment(
        nonconformity_id="nc-1",
        response_id="resp-abc",
        uploaded_by_user_id="user-1",
    )

    assert seeded is not None
    assert seeded["attachment_type"] == "before"
    assert seeded["original_name"] == "avaliacao.jpg"
    nc_files = list((nc_dir / "nc-1").glob("before_*"))
    assert len(nc_files) == 1
    assert nc_files[0].read_bytes() == b"foto-avaliacao"
    assert any("seeded_from_evaluation" in str(params) for _, params in repo._executed)


def test_seed_nc_before_skips_when_before_exists(tmp_path: Path) -> None:
    repo = FakeAudit5sRepo()
    repo._nc_attachments.append(
        {
            "id": "existing",
            "nonconformity_id": "nc-1",
            "attachment_type": "before",
        }
    )
    result = repo.seed_nc_before_from_response_attachment(
        nonconformity_id="nc-1",
        response_id="resp-abc",
        uploaded_by_user_id="user-1",
    )
    assert result is None


def test_seed_nc_before_skips_without_response_photo() -> None:
    repo = FakeAudit5sRepo()
    result = repo.seed_nc_before_from_response_attachment(
        nonconformity_id="nc-1",
        response_id="resp-missing",
        uploaded_by_user_id="user-1",
    )
    assert result is None


def test_upsert_response_attachment_rejects_non_nc_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = FakeAudit5sRepo()

    def fake_fetch_one(query: str, params: tuple[Any, ...] | None = None):
        if "audit_5s_audits" in query:
            return {"id": "audit-1", "status": "draft"}
        if "audit_5s_responses" in query:
            return {"id": "resp-1", "score": 5, "is_not_applicable": False}
        return None

    repo.fetch_one = fake_fetch_one  # type: ignore[method-assign]
    with pytest.raises(PluginsRepositoryError, match="Ruim \\(1\\) ou Médio \\(3\\)"):
        repo.upsert_response_attachment(
            audit_id="audit-1",
            criterion_id="crit-1",
            original_name="a.jpg",
            file_name="criterion_x.jpg",
            storage_path="resp-1/criterion_x.jpg",
            mime_type="image/jpeg",
            size_bytes=10,
            uploaded_by_user_id="user-1",
        )
