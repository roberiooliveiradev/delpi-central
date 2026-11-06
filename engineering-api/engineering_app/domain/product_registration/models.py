"""Entidades, ator e máquina de estados do Product Registration.

Framework-free. Regras centrais do contrato §7:
- solicitação não é cadastro oficial; draft não é revisão publicada;
- revisão é imutável; o record vigente aponta para revisão confirmada;
- ``verify_and_complete`` sem match permanece ``under_review``;
- terminais não reabrem — nova solicitação para novo ciclo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PRC_STATUSES: tuple[str, ...] = (
    "submitted",
    "in_progress",
    "needs_information",
    "under_review",
    "completed",
    "rejected",
)
TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "rejected"})

REQUEST_TYPES: tuple[str, ...] = ("create", "update")

# Modelo de acesso aprovado pelo PO (PRODUCT-REGISTRATION-PO-DECISIONS
# -2026-11-06 §2): somente duas permissões funcionais do Portal.
ENG_ACCESS = "engineering.access"
ENG_MANAGER = "engineering.manager"

# Transições de workflow — ação → (origens válidas, destino).
_TRANSITIONS: dict[str, tuple[frozenset[str], str]] = {
    "start": (frozenset({"submitted"}), "in_progress"),
    "request_information": (
        frozenset({"in_progress", "under_review"}),
        "needs_information",
    ),
    "resume": (frozenset({"needs_information"}), "in_progress"),
    "submit_review": (frozenset({"in_progress"}), "under_review"),
    "reject": (
        frozenset(
            {"submitted", "in_progress", "needs_information", "under_review"}
        ),
        "rejected",
    ),
    "verify_and_complete": (frozenset({"under_review"}), "completed"),
}

# Ações visíveis por status (allowedActions do backend — UI nunca decide).
_ACTIONS_BY_STATUS: dict[str, tuple[str, ...]] = {
    "submitted": ("start", "reject"),
    "in_progress": (
        "edit_draft",
        "request_information",
        "submit_review",
        "reject",
    ),
    "needs_information": ("resume", "reject"),
    "under_review": (
        "verify_and_complete",
        "request_information",
        "reject",
    ),
    "completed": (),
    "rejected": (),
}

# Ação → permissão exigida — modelo de duas permissões (PO): todas as
# operações do fluxo exigem ``engineering.access``; administração
# (nenhuma exposta neste MVP) exigiria ``engineering.manager``.
_ACTION_PERMISSION: dict[str, tuple[str, ...]] = {
    "start": (ENG_ACCESS,),
    "edit_draft": (ENG_ACCESS,),
    "request_information": (ENG_ACCESS,),
    "resume": (ENG_ACCESS,),
    "submit_review": (ENG_ACCESS,),
    "reject": (ENG_ACCESS,),
    "verify_and_complete": (ENG_ACCESS,),
}


@dataclass(frozen=True)
class PrcActor:
    """Ator autenticado — Keycloak sub + permissões efetivas Core.

    ``channel`` registra a superfície da ação (``portal`` | ``eva`` |
    ``harness``) para auditoria — nunca é autorização.
    """

    user_id: str = "unknown"
    email: str | None = None
    name: str | None = None
    label: str | None = None
    permissions: frozenset[str] = frozenset()
    is_superadmin: bool = False
    channel: str = "portal"

    def _has(self, code: str) -> bool:
        return self.is_superadmin or code in self.permissions

    @property
    def _access(self) -> bool:
        return self._has(ENG_ACCESS)

    @property
    def can_create(self) -> bool:
        return self._access

    @property
    def can_read(self) -> bool:
        return self._access

    @property
    def can_process(self) -> bool:
        return self._access

    @property
    def can_verify(self) -> bool:
        return self._access

    @property
    def is_analyst(self) -> bool:
        """Fila global: todo portador de ``engineering.access`` opera o
        CRUD do módulo (decisão PO — sem perfil oculto de analista)."""
        return self._access

    @property
    def is_manager(self) -> bool:
        """Administração do Portal — fail-closed até o contrato Core
        de ``engineering.manager`` estar registrado."""
        return self._has(ENG_MANAGER)

    def has_action_permission(self, action: str) -> bool:
        required = _ACTION_PERMISSION.get(action, ())
        return all(self._has(code) for code in required)

    def allowed_actions(self, status: str) -> list[str]:
        """Ações legítimas do status filtradas pela permissão do ator."""
        return [
            action
            for action in _ACTIONS_BY_STATUS.get(status, ())
            if self.has_action_permission(action)
        ]


def transition_for(action: str, current_status: str) -> str | None:
    """Destino de uma ação; ``None`` quando a transição é inválida."""
    spec = _TRANSITIONS.get(action)
    if spec is None or current_status not in spec[0]:
        return None
    return spec[1]


def action_allowed_from(action: str, current_status: str) -> bool:
    return transition_for(action, current_status) is not None
