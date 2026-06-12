from __future__ import annotations

import logging
from typing import Any

from fastapi import Request

from maint_app.core.auth_actor import actor_nome_from_request, actor_sub_from_request
from maint_app.core.errors import format_api_error
from maint_app.infrastructure.persistence.repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)

_audit_repo: AuditRepository | None = None


def _get_audit_repo() -> AuditRepository:
    global _audit_repo
    if _audit_repo is None:
        _audit_repo = AuditRepository()
    return _audit_repo


def log_ferramenta_audit(
    request: Request,
    *,
    acao: str,
    filial: str,
    codigo_ferramenta: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Registra evento de auditoria vinculado à ferramenta (não bloqueia a mutação)."""
    try:
        _get_audit_repo().log(
            entidade="ferramenta",
            entidade_id=codigo_ferramenta.strip(),
            acao=acao,
            filial=filial,
            usuario_sub=actor_sub_from_request(request),
            usuario_nome=actor_nome_from_request(request),
            payload=payload or {},
        )
    except Exception as exc:
        logger.warning(
            "audit_log_failed ferramenta=%s acao=%s err=%s",
            codigo_ferramenta,
            acao,
            format_api_error(exc),
        )
