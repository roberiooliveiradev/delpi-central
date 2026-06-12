from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from tm_app.application.services.json_backup_service import JsonBackupService
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.responses import fail, ok
from tm_app.core.serialize import json_safe
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.interface.http.schemas.json_backup_schemas import JsonImportBody

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


@router.post("/import/preview")
def import_preview(body: JsonImportBody):
    result = JsonBackupService().preview(body.data, body.mode, body.import_format)
    if not result.get("valid"):
        return fail("Pacote JSON inválido.", 422, data=result)
    return ok(result, "Pré-visualização gerada.")


@router.post("/import/apply")
def import_apply(body: JsonImportBody, request: Request):
    user_id, user_email = actor_from_request(request)
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
        payload={
            "mode": body.mode,
            "import_format": body.import_format,
            "entities": result.get("entities"),
        },
    )
    return ok(result, "Importação concluída. Dashboard recalculado.")
