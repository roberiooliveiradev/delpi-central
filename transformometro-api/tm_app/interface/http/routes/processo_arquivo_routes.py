from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from tm_app.application.services.processo_arquivo_storage import (
    ProcessoArquivoStorage,
    ProcessoArquivoStorageError,
)
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.responses import fail, ok
from tm_app.core.serialize import row_to_json, rows_to_json
from tm_app.infrastructure.persistence.repositories.processo_arquivo_repository import (
    ProcessoArquivoRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro — arquivos do processo"])


class ProcessoArquivoUpdateBody(BaseModel):
    descricao: str | None = Field(default=None, max_length=2000)


def _actor(request: Request) -> tuple[str | None, str | None]:
    user_id, email = actor_from_request(request)
    return user_id, email


def _ensure_processo(processo_id: str) -> dict | None:
    return ProcessoRepository().get(processo_id)


@router.get("/processos/{processo_id}/arquivos")
def list_processo_arquivos(processo_id: str):
    if not _ensure_processo(processo_id):
        return fail("Processo não encontrado.", 404)
    rows = ProcessoArquivoRepository().list_by_processo(processo_id)
    return ok({"total": len(rows), "items": rows_to_json(rows)}, "Arquivos do processo.")


@router.post("/processos/{processo_id}/arquivos")
async def attach_processo_arquivo(
    processo_id: str,
    request: Request,
    tipo: str = Form(default="anexo"),
    descricao: str | None = Form(default=None),
    url_externa: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    if not _ensure_processo(processo_id):
        return fail("Processo não encontrado.", 404)

    user_id, email = _actor(request)
    repo = ProcessoArquivoRepository()
    fields: dict = {
        "tipo": tipo,
        "descricao": descricao,
        "enviado_por_id": user_id or "unknown",
        "enviado_por_nome": email or user_id,
    }

    if tipo == "link":
        if not url_externa:
            return fail("URL obrigatória para arquivo do tipo link.", 400)
        fields["url_externa"] = url_externa.strip()
    else:
        if file is None:
            return fail("Arquivo obrigatório.", 400)
        content = await file.read()
        storage = ProcessoArquivoStorage()
        try:
            stored_name = storage.save(
                processo_id=processo_id,
                original_name=file.filename or "arquivo",
                content=content,
                mime_type=file.content_type,
            )
        except ProcessoArquivoStorageError as exc:
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
        row = repo.create(processo_id, fields)
    except Exception as exc:
        logger.exception("attach_processo_arquivo failed")
        return fail(f"Falha ao gravar arquivo: {exc}", 500)

    return ok(row_to_json(row), "Arquivo anexado.", 201)


@router.get("/processos/{processo_id}/arquivos/{arquivo_id}/arquivo")
def download_processo_arquivo(processo_id: str, arquivo_id: str):
    repo = ProcessoArquivoRepository()
    arquivo = repo.get(processo_id, arquivo_id)
    if not arquivo or not arquivo.get("nome_armazenado"):
        return fail("Arquivo não encontrado.", 404)

    storage = ProcessoArquivoStorage()
    try:
        path = storage.resolve_file(
            processo_id=processo_id,
            stored_name=str(arquivo["nome_armazenado"]),
        )
    except ProcessoArquivoStorageError as exc:
        return fail(str(exc), 404)

    return FileResponse(
        path,
        media_type=arquivo.get("tipo_mime") or "application/octet-stream",
        filename=arquivo.get("nome_arquivo") or arquivo["nome_armazenado"],
    )


@router.patch("/processos/{processo_id}/arquivos/{arquivo_id}")
def update_processo_arquivo(
    processo_id: str,
    arquivo_id: str,
    body: ProcessoArquivoUpdateBody,
):
    repo = ProcessoArquivoRepository()
    row = repo.update(processo_id, arquivo_id, body.model_dump(exclude_unset=True))
    if not row:
        return fail("Arquivo não encontrado.", 404)
    return ok(row_to_json(row), "Arquivo atualizado.")


@router.delete("/processos/{processo_id}/arquivos/{arquivo_id}")
def delete_processo_arquivo(processo_id: str, arquivo_id: str):
    repo = ProcessoArquivoRepository()
    removed = repo.soft_delete(processo_id, arquivo_id)
    if not removed:
        return fail("Arquivo não encontrado.", 404)

    stored_name = removed.get("nome_armazenado")
    if stored_name:
        ProcessoArquivoStorage().delete_file(
            processo_id=processo_id,
            stored_name=str(stored_name),
        )

    return ok({"arquivo_id": arquivo_id, "deleted": True}, "Arquivo excluído.")
