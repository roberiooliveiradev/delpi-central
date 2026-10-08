"""Identidade de solicitantes externos (P2 — cockpit do operador).

Requests podem ser criados via S2S em nome de quem não possui conta Minha
DELPI — hoje o único emissor é o cockpit de produção, que grava o solicitante
como operator:<branch>:<operator_code> (ex.: operator:02:12345).

Regra central: solicitantes externos NÃO recebem notificações de
creator/owner (não existe usuário destino na plataforma). Qualquer política
que notifique o created_by_user_id deve consultar esta função em vez de
comparar prefixos localmente.
"""

from __future__ import annotations

#: Schemes de ID reservados para atores externos sem conta na plataforma.
EXTERNAL_REQUESTER_SCHEMES: tuple[str, ...] = ("operator:",)


def is_external_requester_id(value: object) -> bool:
    """True quando o ID representa um solicitante externo (sem usuário Minha DELPI)."""
    text = str(value or "").strip()
    return any(text.startswith(scheme) for scheme in EXTERNAL_REQUESTER_SCHEMES)
