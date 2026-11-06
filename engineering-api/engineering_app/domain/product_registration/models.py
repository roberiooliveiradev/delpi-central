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

# Permissões granulares do vertical (declaradas no manifest do plugin).
PR_READ = "engineering.product-registration.read"
PR_CREATE = "engineering.product-registration.create"
PR_PROCESS = "engineering.product-registration.process"
PR_VERIFY = "engineering.product-registration.verify"
PR_ADMIN = "engineering.product-registration.admin"
PRC_PERMISSIONS: tuple[str, ...] = (
    PR_READ,
    PR_CREATE,
    PR_PROCESS,
    PR_VERIFY,
    PR_ADMIN,
)

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

# Ação → permissão granular exigida (além de escopo do recurso).
_ACTION_PERMISSION: dict[str, tuple[str, ...]] = {
    "start": (PR_PROCESS,),
    "edit_draft": (PR_PROCESS,),
    "request_information": (PR_PROCESS,),
    "resume": (PR_PROCESS,),
    "submit_review": (PR_PROCESS,),
    "reject": (PR_PROCESS,),
    "verify_and_complete": (PR_PROCESS, PR_VERIFY),
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
    def can_create(self) -> bool:
        return self._has(PR_CREATE) or self._has(PR_ADMIN)

    @property
    def can_read(self) -> bool:
        return any(
            self._has(code)
            for code in (PR_READ, PR_CREATE, PR_PROCESS, PR_VERIFY, PR_ADMIN)
        )

    @property
    def can_process(self) -> bool:
        return self._has(PR_PROCESS) or self._has(PR_ADMIN)

    @property
    def can_verify(self) -> bool:
        return self.can_process and self._has(PR_VERIFY)

    @property
    def is_analyst(self) -> bool:
        """Escopo de fila global: analista = process|verify|admin.

        Regra de escopo formalizada do MVP: solicitante (read/create
        apenas) enxerga somente as próprias solicitações; a fila global
        é privilégio do analista autorizado — nunca inferida do legado.
        """
        return self.is_superadmin or any(
            self._has(code) for code in (PR_PROCESS, PR_VERIFY, PR_ADMIN)
        )

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
