from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from tm_app.application.services.backup_package_service import (
    TransformometroBackupPackageService,
)
from tm_app.application.services.json_backup_service import JsonBackupService
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.responses import fail, ok
from tm_app.core.serialize import json_safe
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.interface.http.schemas.json_backup_schemas import JsonImportBody, JsonImportMode

router = APIRouter(prefix="/transformometro/data", tags=["Transformômetro — backup JSON"])


@router.get("/export")
def export_json(_request: Request):
    bundle = JsonBackupService().export_bundle()
    filename = f"transformometro-backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    body = json.dumps(json_safe(bundle), ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/package")
def export_package(_request: Request):
    try:
        payload = TransformometroBackupPackageService().export_package()
    except ValueError as exc:
        return fail(str(exc), 422)
    filename = (
        f"transformometro-backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.tmbackup.zip"
    )
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _read_upload_file(file: UploadFile) -> bytes:
    content = await file.read()
    if not content:
        raise ValueError("Arquivo vazio.")
    return content


@router.post("/import/package/preview")
async def import_package_preview(
    file: UploadFile = File(...),
    mode: JsonImportMode = Form(default="merge"),
    import_format: str = Form(default="auto"),
):
    try:
        raw = await _read_upload_file(file)
        result = TransformometroBackupPackageService().preview_package(
            raw, mode, import_format  # type: ignore[arg-type]
        )
    except ValueError as exc:
        return fail(str(exc), 422)
    if not result.get("valid"):
        return fail("Pacote inválido.", 422, data=result)
    return ok(result, "Pré-visualização do pacote gerada.")


@router.post("/import/package/apply")
async def import_package_apply(
    request: Request,
    file: UploadFile = File(...),
    mode: JsonImportMode = Form(default="merge"),
    import_format: str = Form(default="auto"),
):
    user_id, user_email, user_name = actor_from_request(request)
    try:
        raw = await _read_upload_file(file)
        result = TransformometroBackupPackageService().apply_package(
            raw, mode, import_format  # type: ignore[arg-type]
        )
    except ValueError as exc:
        return fail(str(exc), 422)
    except Exception as exc:
        return fail(f"Falha na importação do pacote: {exc}", 500)

    AuditRepository().log(
        entity_type="backup_package",
        entity_id="00000000-0000-0000-0000-000000000000",
        action=f"import_{mode}",
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
        payload={
            "mode": mode,
            "import_format": import_format,
            "entities": result.get("entities"),
            "evidence_files_restored": result.get("evidence_files_restored"),
        },
    )
    return ok(result, "Importação do pacote concluída. Dashboard recalculado.")


@router.post("/import/preview")
def import_preview(body: JsonImportBody):
    result = JsonBackupService().preview(body.data, body.mode, body.import_format)
    if not result.get("valid"):
        return fail("Pacote JSON inválido.", 422, data=result)
    return ok(result, "Pré-visualização gerada.")


@router.post("/import/apply")
def import_apply(body: JsonImportBody, request: Request):
    user_id, user_email, user_name = actor_from_request(request)
    try:
        result = JsonBackupService().apply(body.data, body.mode, body.import_format)
    except ValueError as exc:
        return fail(str(exc), 422)
    except Exception as exc:
        return fail(f"Falha na importação: {exc}", 500)

    AuditRepository().log(
        entity_type="json_backup",
        entity_id="00000000-0000-0000-0000-000000000000",
        action=f"import_{body.mode}",
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
        payload={
            "mode": body.mode,
            "import_format": body.import_format,
            "entities": result.get("entities"),
        },
    )
    return ok(result, "Importação concluída. Dashboard recalculado.")
