"""Testes de rotas/use cases de mídia — Guias e Procedimentos."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.security import api_delpi_permissions as perms
from app.application.services.guias_procedimentos.guide_media_storage import (
    GuiasProcedimentosMediaStorage,
)
from app.application.use_cases.guias_procedimentos.admin_guias_use_cases import (
    ActorContext,
)
from app.application.use_cases.guias_procedimentos.media_guias_use_cases import (
    CreateExternalVideoUseCase,
    UploadProcedureImageUseCase,
    assert_can_read_asset,
)
from app.domain.services.guias_procedimentos.exceptions import (
    GuiasNotFoundError,
    GuiasValidationError,
)
from app.interface.http.routes.guias_procedimentos import guias_procedimentos_media_router


PROC_ID = "33333333-3333-4333-8333-333333333301"
ACTOR = ActorContext("user-1", "Admin Teste")


class MediaProbeRepo:
    def __init__(self) -> None:
        self.procedures: dict[str, dict[str, Any]] = {
            PROC_ID: {
                "id": PROC_ID,
                "status": "draft",
                "slug": "demo",
                "department_active": True,
            }
        }
        self.media: dict[str, dict[str, Any]] = {}
        self.attachments: dict[str, dict[str, Any]] = {}

    def get_admin_procedure_by_id(self, procedure_id: str) -> dict[str, Any] | None:
        return self.procedures.get(procedure_id)

    def get_procedure_access_row(self, procedure_id: str) -> dict[str, Any] | None:
        row = self.procedures.get(procedure_id)
        if not row:
            return None
        return {
            "id": row["id"],
            "status": row["status"],
            "slug": row["slug"],
            "department_active": row["department_active"],
        }

    def list_media_by_procedure_id(
        self, procedure_id: str, *, include_archived: bool = False
    ) -> list[dict[str, Any]]:
        rows = [m for m in self.media.values() if m["procedure_id"] == procedure_id]
        if not include_archived:
            rows = [m for m in rows if m.get("archived_at") is None]
        return rows

    def list_attachments_by_procedure_id(
        self, procedure_id: str, *, include_archived: bool = False
    ) -> list[dict[str, Any]]:
        rows = [
            a for a in self.attachments.values() if a["procedure_id"] == procedure_id
        ]
        if not include_archived:
            rows = [a for a in rows if a.get("archived_at") is None]
        return rows

    def get_media_by_id(self, media_id: str) -> dict[str, Any] | None:
        return self.media.get(media_id)

    def create_media(self, **fields: Any) -> dict[str, Any]:
        media_id = str(uuid4())
        proc = self.procedures[fields["procedure_id"]]
        row = {
            "id": media_id,
            **fields,
            "archived_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "procedure_status": proc["status"],
            "department_active": proc["department_active"],
        }
        self.media[media_id] = row
        return row

    def update_media_metadata(self, media_id: str, **fields: Any) -> dict[str, Any]:
        row = self.media[media_id]
        row.update(fields)
        return row

    def archive_media(self, media_id: str, **fields: Any) -> dict[str, Any]:
        row = self.media[media_id]
        row["archived_at"] = datetime.now(timezone.utc)
        row.update(fields)
        return row

    def get_attachment_by_id(self, attachment_id: str) -> dict[str, Any] | None:
        return self.attachments.get(attachment_id)

    def create_attachment(self, **fields: Any) -> dict[str, Any]:
        attachment_id = str(uuid4())
        proc = self.procedures[fields["procedure_id"]]
        row = {
            "id": attachment_id,
            **fields,
            "archived_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "procedure_status": proc["status"],
            "department_active": proc["department_active"],
        }
        self.attachments[attachment_id] = row
        return row

    def update_attachment_metadata(
        self, attachment_id: str, **fields: Any
    ) -> dict[str, Any]:
        row = self.attachments[attachment_id]
        row.update(fields)
        return row

    def archive_attachment(self, attachment_id: str, **fields: Any) -> dict[str, Any]:
        row = self.attachments[attachment_id]
        row["archived_at"] = datetime.now(timezone.utc)
        row.update(fields)
        return row


def test_upload_image_use_case(tmp_path: Path) -> None:
    storage = GuiasProcedimentosMediaStorage(base_dir=str(tmp_path))
    repo = MediaProbeRepo()
    uc = UploadProcedureImageUseCase(repo, storage=storage)
    data = uc.execute(
        PROC_ID,
        original_name="a.png",
        content=b"img",
        mime_type="image/png",
        title="Figura 1",
        actor=ACTOR,
    )
    assert data["media_kind"] == "image"
    assert data["title"] == "Figura 1"
    assert data["file_path"].endswith("/file")
    assert data["stored_name"]


def test_external_video_use_case() -> None:
    repo = MediaProbeRepo()
    uc = CreateExternalVideoUseCase(repo)
    data = uc.execute(
        PROC_ID,
        url="https://www.youtube.com/watch?v=abcdefghijk",
        title="Demo",
        actor=ACTOR,
    )
    assert data["media_kind"] == "video_external"
    assert data["external_provider"] == "youtube"
    try:
        uc.execute(PROC_ID, url="https://evil.example/x", actor=ACTOR)
        raise AssertionError("deveria rejeitar")
    except GuiasValidationError:
        pass


def test_assert_can_read_draft_requires_manage() -> None:
    row = {
        "archived_at": None,
        "procedure_status": "draft",
        "department_active": True,
    }
    try:
        assert_can_read_asset(row, can_manage=False)
        raise AssertionError("deveria negar")
    except GuiasNotFoundError:
        pass
    assert_can_read_asset(row, can_manage=True)


def test_admin_upload_image_endpoint(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(
        guias_procedimentos_media_router.admin_media_router,
        prefix="/guias-procedimentos",
    )
    client = TestClient(app)
    repo = MediaProbeRepo()
    storage = GuiasProcedimentosMediaStorage(base_dir=str(tmp_path))
    user = SimpleNamespace(
        id="u1",
        name="Tester",
        is_superadmin=False,
        permissions=[perms.GUIAS_PROCEDIMENTOS_MANAGE],
    )
    with (
        patch(
            "delpi_auth.authorization.resolve_user_context",
            return_value=user,
        ),
        patch(
            "app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router.get_current_user",
            return_value=user,
        ),
        patch(
            "app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router.build_upload_procedure_image_use_case",
            return_value=UploadProcedureImageUseCase(repo, storage=storage),
        ),
    ):
        response = client.post(
            f"/guias-procedimentos/admin/procedures/{PROC_ID}/media/images",
            files={"file": ("foto.png", BytesIO(b"png-bytes"), "image/png")},
            data={"title": "Capa"},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["media_kind"] == "image"
    assert body["meta"]["operationId"] == (
        "upload_guias_procedimentos_admin_procedure_image"
    )


def test_admin_upload_requires_manage(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(
        guias_procedimentos_media_router.admin_media_router,
        prefix="/guias-procedimentos",
    )
    client = TestClient(app, raise_server_exceptions=False)
    user = SimpleNamespace(
        id="u1",
        name="Reader",
        is_superadmin=False,
        permissions=[perms.GUIAS_PROCEDIMENTOS_ACCESS],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        response = client.post(
            f"/guias-procedimentos/admin/procedures/{PROC_ID}/media/images",
            files={"file": ("foto.png", BytesIO(b"png"), "image/png")},
        )
    assert response.status_code in {401, 403, 500}
