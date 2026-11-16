"""PRC-CONVERSATION — domínio da conversa do caso (Issue #207).

Regras puras: validação de corpo, política de mídia, congelamento em
estado terminal e serialização de saída. Nenhuma dependência de
framework, HTTP, storage ou requests-api (padrão replicado, sem
acoplamento entre bounded contexts).
"""

from __future__ import annotations

import re

from engineering_app.domain.product_registration.models import TERMINAL_STATUSES

COMMENT_BODY_MAX_CHARS = 4000

_IMAGE_HREF_RE = re.compile(r"!\[[^\]]*]\(\s*([^\s)\"']+)", re.MULTILINE)


def validate_comment_body(body: str | None) -> str:
    """Corpo obrigatório, limitado; markdown com imagens apenas via
    ``attachment:…`` — href externo/data vira pixel de rastreamento ou
    vetor XSS e é rejeitado (mesma regra funcional do requests-api,
    reimplementada no owner)."""
    text = (body or "").strip()
    if not text:
        raise ValueError("comment_required")
    if len(text) > COMMENT_BODY_MAX_CHARS:
        raise ValueError("comment_too_large")
    for match in _IMAGE_HREF_RE.finditer(text):
        href = (match.group(1) or "").strip().lower()
        if href.startswith("attachment:"):
            continue
        if href.startswith(("http://", "https://", "data:")):
            raise ValueError("comment_media_forbidden")
    return text


def assert_conversation_open(status: str | None) -> None:
    """Conversa congelada em caso terminal — política derivada do
    próprio lifecycle PRC (``TERMINAL_STATUSES``), não copiada do
    requests-api."""
    if (status or "") in TERMINAL_STATUSES:
        raise ValueError("conversation_frozen")


def can_moderate_comment(*, actor_is_author: bool, actor_is_analyst: bool) -> bool:
    """Edição/remoção: autor ou analista da Engenharia
    (``engineering.access`` — equivalente funcional ao manage do
    requests-api dentro do modelo PrcActor)."""
    return actor_is_author or actor_is_analyst


def comment_to_api(row: dict, *, actor_user_id: str) -> dict:
    """DTO do comentário — snapshot de autoria, sem campos internos."""
    return {
        "commentId": row["id"],
        "requestId": row["request_id"],
        "authorSubject": row["author_subject"],
        "authorDisplayName": row.get("author_display_name"),
        "body": row["body"],
        "version": row["row_version"],
        "isMine": row["author_subject"] == actor_user_id,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        "edited": row["created_at"] != row["updated_at"],
    }


def comment_attachment_to_api(row: dict) -> dict:
    """DTO do anexo da conversa — nunca expõe storage_key.

    ``inspection`` honesto: validação estrutural (magic bytes), sem
    antivírus na plataforma."""
    return {
        "inspection": "structural",
        "attachmentId": row["id"],
        "requestId": row["request_id"],
        "commentId": row["comment_id"],
        "originalFileName": row["original_file_name"],
        "mediaType": row["media_type"],
        "sizeBytes": row["size_bytes"],
        "sha256": row["sha256"],
        "state": row["state"],
        "uploadedBySubject": row.get("uploaded_by_subject"),
        "uploadedByDisplayName": row.get("uploaded_by_display_name"),
        "createdAt": row["created_at"],
    }
