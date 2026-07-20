from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from tm_app.application.services.revisao_evidence_storage import (
    RevisaoEvidenceStorage,
    RevisaoEvidenceStorageError,
)
from tm_app.application.services.transformometro_realtime_notify import notify_entity_updated
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.responses import fail, ok
from tm_app.core.serialize import row_to_json, rows_to_json
from tm_app.infrastructure.persistence.repositories.revisao_evidence_repository import (
    RevisaoEvidenceRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro — evidências de revisão"])


class RevisaoEvidenceUpdateBody(BaseModel):
    descricao: str | None = Field(default=None, max_length=2000)


def _actor(request: Request) -> tuple[str | None, str | None]:
    user_id, user_email, _user_name = actor_from_request(request)
    return user_id, user_email


def _ensure_revisao(revisao_id: str) -> dict | None:
    return RevisaoRepository().get(revisao_id)


def _notify_evidencia(
    *,
    request: Request,
    revisao: dict,
    evidencia_id: str,
    action: str,
    extra: dict | None = None,
) -> None:
    user_id, _email = _actor(request)
    payload = {
        "revisao_id": str(revisao.get("revisao_id") or ""),
        "processo_id": str(revisao.get("processo_id") or ""),
        "instancia_id": str(revisao.get("instancia_id") or ""),
        "evidencia_id": evidencia_id,
        **(extra or {}),
    }
    notify_entity_updated(
        entity_type="revisao",
        entity_id=str(revisao["revisao_id"]),
        action=action,
        actor_user_id=user_id,
        payload=payload,
    )


@router.get("/revisoes/{revisao_id}/evidencias")
def list_revisao_evidencias(revisao_id: str):
    if not _ensure_revisao(revisao_id):
        return fail("Revisão não encontrada.", 404)
    rows = RevisaoEvidenceRepository().list_by_revisao(revisao_id)
    return ok({"total": len(rows), "items": rows_to_json(rows)}, "Evidências da revisão.")


@router.post("/revisoes/{revisao_id}/evidencias")
async def attach_revisao_evidencia(
    revisao_id: str,
    request: Request,
    tipo: str = Form(default="anexo"),
    descricao: str | None = Form(default=None),
    url_externa: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    revisao = _ensure_revisao(revisao_id)
    if not revisao:
        return fail("Revisão não encontrada.", 404)

    user_id, email = _actor(request)
    repo = RevisaoEvidenceRepository()
    fields: dict = {
        "tipo": tipo,
        "descricao": descricao,
        "enviado_por_id": user_id or "unknown",
        "enviado_por_nome": email or user_id,
    }

    if tipo == "link":
        if not url_externa:
            return fail("URL obrigatória para evidência do tipo link.", 400)
        fields["url_externa"] = url_externa.strip()
    else:
        if file is None:
            return fail("Arquivo obrigatório.", 400)
        content = await file.read()
        storage = RevisaoEvidenceStorage()
        try:
            stored_name = storage.save(
                revisao_id=revisao_id,
                original_name=file.filename or "arquivo",
                content=content,
                mime_type=file.content_type,
            )
        except RevisaoEvidenceStorageError as exc:
            return fail(str(exc), 400)
        fields.update(
            {
                "nome_arquivo": file.filename,
                "nome_armazenado": stored_name,
                "tipo_mime": file.content_type,
                "tamanho_bytes": len(content),
            }
        )

    try:
        row = repo.create(revisao_id, fields)
    except Exception as exc:
        logger.exception("attach_revisao_evidencia failed")
        return fail(f"Falha ao gravar evidência: {exc}", 500)

    evidencia_id = str(row.get("evidencia_id") or row.get("revisao_evidencia_id") or "")
    _notify_evidencia(
        request=request,
        revisao=revisao,
        evidencia_id=evidencia_id,
        action="revisao.evidencia.created",
        extra={"tipo": tipo},
    )
    return ok(row_to_json(row), "Evidência anexada.", 201)


@router.get("/revisoes/{revisao_id}/evidencias/{evidencia_id}/arquivo")
def download_revisao_evidencia(revisao_id: str, evidencia_id: str):
    repo = RevisaoEvidenceRepository()
    evidence = repo.get(revisao_id, evidencia_id)
    if not evidence or not evidence.get("nome_armazenado"):
        return fail("Evidência não encontrada.", 404)

    storage = RevisaoEvidenceStorage()
    try:
        path = storage.resolve_file(
            revisao_id=revisao_id,
            stored_name=str(evidence["nome_armazenado"]),
        )
    except RevisaoEvidenceStorageError as exc:
        return fail(str(exc), 404)

    return FileResponse(
        path,
        media_type=evidence.get("tipo_mime") or "application/octet-stream",
        filename=evidence.get("nome_arquivo") or evidence["nome_armazenado"],
    )


@router.patch("/revisoes/{revisao_id}/evidencias/{evidencia_id}")
def update_revisao_evidencia(
    revisao_id: str,
    evidencia_id: str,
    body: RevisaoEvidenceUpdateBody,
    request: Request,
):
    revisao = _ensure_revisao(revisao_id)
    if not revisao:
        return fail("Revisão não encontrada.", 404)
    repo = RevisaoEvidenceRepository()
    row = repo.update(revisao_id, evidencia_id, body.model_dump(exclude_unset=True))
    if not row:
        return fail("Evidência não encontrada.", 404)
    _notify_evidencia(
        request=request,
        revisao=revisao,
        evidencia_id=evidencia_id,
        action="revisao.evidencia.updated",
    )
    return ok(row_to_json(row), "Evidência atualizada.")


@router.delete("/revisoes/{revisao_id}/evidencias/{evidencia_id}")
def delete_revisao_evidencia(revisao_id: str, evidencia_id: str, request: Request):
    revisao = _ensure_revisao(revisao_id)
    if not revisao:
        return fail("Revisão não encontrada.", 404)
    repo = RevisaoEvidenceRepository()
    removed = repo.soft_delete(revisao_id, evidencia_id)
    if not removed:
        return fail("Evidência não encontrada.", 404)

    stored_name = removed.get("nome_armazenado")
    if stored_name:
        RevisaoEvidenceStorage().delete_file(
            revisao_id=revisao_id,
            stored_name=str(stored_name),
        )

    _notify_evidencia(
        request=request,
        revisao=revisao,
        evidencia_id=evidencia_id,
        action="revisao.evidencia.deleted",
    )
    return ok({"evidencia_id": evidencia_id, "deleted": True}, "Evidência excluída.")
