"""Escopo de recurso por filial — `branch_scope` (doc 103 §92/§117/§166).

`branch_scope` é dimensão de dado (MATRIX|BRANCH|BOTH), nunca permission
(doc-14/T05). O documento herda o escopo do item do snapshot ao qual está
vinculado; documento de competência (sem item) equivale a `BOTH`.

O filial-contexto do request é declarado pelo próprio request (mesma
dimensão); o backend aplica `capability AND resource_scope AND
business_rule`: recurso fora do contexto declarado é tratado como
inexistente (404 — existência nunca vaza). Não existe membership de
filial por usuário na plataforma: a audiência `access` é autorizada para
o dataset compartilhado (doc 49 §8) e permission por filial é proibida.
"""

from __future__ import annotations

from controllership_finance_app.domain.closing_checklist.errors import (
    InvalidUpload,
)

BRANCH_SCOPES = frozenset({"MATRIX", "BRANCH", "BOTH"})


def normalize_request_scope(branch_scope: str | None) -> str:
    """Filial-contexto declarado — ausente equivale a `BOTH`."""
    ctx = (branch_scope or "BOTH").strip().upper() or "BOTH"
    if ctx not in BRANCH_SCOPES:
        raise InvalidUpload(
            "branch_scope deve ser MATRIX, BRANCH ou BOTH."
        )
    return ctx


def scope_in_context(
    *, request_scope: str, document_scope: str | None
) -> bool:
    """Interseção escopo-do-recurso × contexto declarado.

    `BOTH` no request alcança qualquer escopo (contexto irrestrito);
    recurso `BOTH` pertence aos contextos MATRIX e BRANCH; contexto
    específico só alcança recurso do mesmo escopo ou `BOTH`.
    """
    scope = (document_scope or "BOTH").strip().upper()
    return (
        request_scope == "BOTH"
        or scope == "BOTH"
        or request_scope == scope
    )
