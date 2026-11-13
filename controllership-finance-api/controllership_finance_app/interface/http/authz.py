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

from delpi_auth.authz_core import has_any_permission, has_permission

from controllership_finance_app.application.invoice_posting.permissions import (
    LANCAMENTO_NOTAS_FISCAIS_ANY_PERMISSIONS,
)

ACCESS_PERMISSION = "controllership-finance.access"
MANAGE_PERMISSION = "controllership-finance.manage"
# DRE-019-RW03 — `access.dre` é a única capability da experiência DRE;
# a legada `closing-documents.read` foi descontinuada após a migração
# comprovada do papel DRE no Core (doc 115 §11).
DRE_ACCESS_PERMISSION = "controllership-finance.access.dre"

# Entrada MCP CLARA (F7-R4): CF access/manage/dre OU qualquer LNF.
CLARA_CF_ENTRY_PERMISSIONS = (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
    DRE_ACCESS_PERMISSION,
)


def _human_user(request: Request):
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unauthorized")
    if getattr(user, "principal_type", None) != "user":
        raise Exception("Forbidden")
    if getattr(user, "rbac_unavailable", False):
        raise Exception("Service Unavailable")
    return user


def has_cf_clara_entry(user) -> bool:
    """Permissão efetiva de Controladoria para a CLARA (não só .access)."""
    return bool(has_any_permission(user, CLARA_CF_ENTRY_PERMISSIONS))


def has_lnf_clara_entry(user) -> bool:
    """Qualquer permissão LNF efetiva — porta de entrada só-LNF."""
    return bool(
        has_any_permission(user, LANCAMENTO_NOTAS_FISCAIS_ANY_PERMISSIONS)
    )


def authorized_user(request: Request):
    """Usuário humano com `controllership-finance.access` efetivo.

    Gate das rotas HTTP do Portal/fechamento — inalterado (F7-R4).
    A porta de entrada da CLARA MCP é ``authorized_clara_mcp_entry``.
    """
    user = _human_user(request)
    if not has_permission(user, ACCESS_PERMISSION):
        raise Exception("Forbidden")
    return user


def authorized_clara_mcp_entry(request: Request):
    """Porta de entrada da CLARA: user + (CF* OU qualquer LNF).

    Não autoriza ações do catálogo — cada entity.action revalida o
    próprio gate; a BFF permanece autoridade nas rotas LNF/CF.
    """
    user = _human_user(request)
    if not (has_cf_clara_entry(user) or has_lnf_clara_entry(user)):
        raise Exception("Forbidden")
    return user


def authorized_documents_reader(request: Request):
    """Usuário humano com capability DRE efetiva (DRE-019/RW03).

    `access.dre` é a permission oficial — não implica `access` nem
    `manage` e não libera rotas internas. O vínculo de entrega
    (RECIPIENT assignment + pacote SUBMITTED) é verificado na camada
    de serviço; a permission sozinha não libera documento algum.
    """
    user = _human_user(request)
    if not has_permission(user, DRE_ACCESS_PERMISSION):
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
