"""Helpers de autorização — backend-first, fail-closed.

Regras (docs 14/96/99):
- `principal_type == "user"` obrigatório — service principals (minted
  superadmin) nunca executam rotas do portal humano;
- Core é a authority de effective permissions via `has_permission`;
- `rbac_unavailable` falha fechado com 503;
- `access` ≠ `manage`: leitura exige `access`; administração exige
  `manage` efetivo (escopo administrativo do slice, padrão
  `can_administer` dos bounded contexts irmãos).
"""

from __future__ import annotations

import uuid

from fastapi import Request

from delpi_auth.authz_core import has_permission

ACCESS_PERMISSION = "controllership-finance.access"
MANAGE_PERMISSION = "controllership-finance.manage"
READ_DOCUMENTS_PERMISSION = (
    "controllership-finance.closing-documents.read"
)
# DRE-019-RW02 — capability oficial da experiência DRE. A legada
# `closing-documents.read` permanece aceita SOMENTE nas superfícies DRE
# durante a migração governada (doc 115 §10); removê-la exige gate.
DRE_ACCESS_PERMISSION = "controllership-finance.access.dre"


def _human_user(request: Request):
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unauthorized")
    if getattr(user, "principal_type", None) != "user":
        raise Exception("Forbidden")
    if getattr(user, "rbac_unavailable", False):
        raise Exception("Service Unavailable")
    return user


def authorized_user(request: Request):
    """Usuário humano com `controllership-finance.access` efetivo."""
    user = _human_user(request)
    if not has_permission(user, ACCESS_PERMISSION):
        raise Exception("Forbidden")
    return user


def authorized_documents_reader(request: Request):
    """Usuário humano com capability DRE efetiva (DRE-019/RW02).

    `access.dre` é a permission oficial; `closing-documents.read` é a
    legada em compatibilidade transitória — nenhuma implica `access`
    nem `manage` e nenhuma libera rotas internas. O vínculo de entrega
    (RECIPIENT assignment + pacote SUBMITTED) é verificado na camada
    de serviço; a permission sozinha não libera documento algum.
    """
    user = _human_user(request)
    if not (
        has_permission(user, DRE_ACCESS_PERMISSION)
        or has_permission(user, READ_DOCUMENTS_PERMISSION)
    ):
        raise Exception("Forbidden")
    return user


def authorized_admin(request: Request):
    """Usuário humano com `controllership-finance.manage` efetivo.

    Escopo administrativo do slice P6-MIN = permission `manage` (única
    permission administrativa do produto); `access` sozinho não libera
    mutações administrativas.
    """
    user = _human_user(request)
    if not has_permission(user, MANAGE_PERMISSION):
        raise Exception("Forbidden")
    return user


def actor_subject(user) -> str:
    """Identidade do ator para colunas UUID (auditoria/abertura).

    Aceita somente o `id` (subject UUID resolvido pelo Core `/me`) do
    principal humano. Sem fallback para e-mail ou identidade alternativa:
    identificador ausente/malformado é rejeitado antes de persistir.
    """
    try:
        return str(uuid.UUID(str(getattr(user, "id", None))))
    except (TypeError, ValueError):
        raise Exception("Unauthorized") from None
