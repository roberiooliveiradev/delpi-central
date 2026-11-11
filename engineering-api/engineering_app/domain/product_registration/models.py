"""Entidades, ator e máquina de estados do Product Registration.

Framework-free. Regras centrais (PRC-REF-020 + REF-022):
- solicitação não é cadastro oficial; draft não é revisão publicada;
- revisão publicada é imutável; o record vigente aponta para ela;
- conclusão ``complete`` exige verificação oficial integral;
- falha de verificação permanece em ``in_progress`` (sem revisão);
- ``needs_correction`` — devolução estruturada da ficha ao solicitante;
- ``needs_information`` / ``under_review`` são legados (leitura/histórico);
- terminais não reabrem — nova solicitação para novo ciclo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PRC_STATUSES: tuple[str, ...] = (
    "submitted",
    "in_progress",
    "needs_information",  # legado REF-019
    "needs_correction",  # PRC-REF-022
    "under_review",  # legado — compatível para leitura/histórico
    "completed",
    "rejected",
)
TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "rejected"})

REQUEST_TYPES: tuple[str, ...] = ("create", "update")

# Modelo de acesso aprovado pelo PO (PRODUCT-REGISTRATION-PO-DECISIONS
# -2026-11-06 §2): somente duas permissões funcionais do Portal.
ENG_ACCESS = "engineering.access"
ENG_MANAGER = "engineering.manager"

# PRC-REF-023-F04 — solicitante de Minhas Solicitações (decisão PO):
# opera o próprio caso PRC sem ``engineering.access``. São os códigos
# já governados pelo Core para o módulo my-requests — nenhum papel novo
# é criado. A object AuthZ do service restringe cada operação ao
# requester/assigned do caso; ``is_analyst``/fila global continuam
# exclusivos de ``engineering.access``.
MR_ACCESS = "my-requests.access"
MR_PRC_CREATE = "my-requests.raw-material-creation.create"

# Transições de workflow — ação → (origens válidas, destino).
_TRANSITIONS: dict[str, tuple[frozenset[str], str]] = {
    "start": (frozenset({"submitted"}), "in_progress"),
    # Legado REF-019 — permanece para casos abertos; não é o fluxo novo.
    "request_information": (
        frozenset({"in_progress", "under_review"}),
        "needs_information",
    ),
    "resume": (frozenset({"needs_information"}), "in_progress"),
    "submit_review": (frozenset({"in_progress"}), "under_review"),
    "return_to_attendance": (frozenset({"under_review"}), "in_progress"),
    # PRC-REF-022
    "return_for_correction": (
        frozenset({"in_progress"}),
        "needs_correction",
    ),
    "resubmit_correction": (
        frozenset({"needs_correction"}),
        "in_progress",
    ),
    "complete": (frozenset({"in_progress", "under_review"}), "completed"),
    "verify_and_complete": (
        frozenset({"in_progress", "under_review"}),
        "completed",
    ),
    "reject": (
        frozenset(
            {
                "submitted",
                "in_progress",
                "needs_information",
                "needs_correction",
                "under_review",
            }
        ),
        "rejected",
    ),
}

# Ações visíveis por status (allowedActions do backend — UI nunca decide).
# Object AuthZ adicional (requester vs analista) é aplicada no service.
# PRC-REF-023-EDIT-POLICY-FIX-08 — ``edit_draft`` migra para
# ``submitted``: a ficha (e os documentos) só é mutável antes do início
# do atendimento e somente pelo criador do caso. Em ``in_progress`` a
# ficha submetida é somente leitura para ambos os portais — a
# Engenharia atende, devolve, verifica e conclui, nunca reescreve a
# ficha por edição genérica.
_ACTIONS_BY_STATUS: dict[str, tuple[str, ...]] = {
    "submitted": ("start", "edit_draft", "reject"),
    "in_progress": (
        "return_for_correction",
        "complete",
        "reject",
    ),
    "needs_information": ("resume", "reject"),
    "needs_correction": (
        "save_returned_fields",
        "resubmit_correction",
        "reject",
    ),
    "under_review": (
        "return_to_attendance",
        "complete",
        "verify_and_complete",
        "request_information",
        "reject",
    ),
    "completed": (),
    "rejected": (),
}

# Ação → conjuntos alternativos de permissão (OR de ANDs).
# Ações de atendimento continuam exclusivas de ENG_ACCESS.
# PRC-REF-023-F04: save_returned_fields/resubmit_correction também
# aceitam o código de criação de Minhas Solicitações — o service ainda
# exige object AuthZ (somente o requester do caso corrige/reenvia).
_ACTION_PERMISSION: dict[str, tuple[tuple[str, ...], ...]] = {
    "start": ((ENG_ACCESS,),),
    # FIX-08 — edit_draft é do criador do caso (escopo por objeto no
    # service); ``engineering.access`` sozinho não habilita a ação.
    "edit_draft": ((ENG_ACCESS,), (MR_PRC_CREATE,)),
    "request_information": ((ENG_ACCESS,),),
    "resume": ((ENG_ACCESS,),),
    "submit_review": ((ENG_ACCESS,),),
    "return_to_attendance": ((ENG_ACCESS,),),
    "return_for_correction": ((ENG_ACCESS,),),
    "save_returned_fields": ((ENG_ACCESS,), (MR_PRC_CREATE,)),
    "resubmit_correction": ((ENG_ACCESS,), (MR_PRC_CREATE,)),
    "complete": ((ENG_ACCESS,),),
    "reject": ((ENG_ACCESS,),),
    "verify_and_complete": ((ENG_ACCESS,),),
    "route_divergence": ((ENG_ACCESS,),),
}

# PRC-REF-021 — decisões de encaminhamento por item divergente (legado).
DIVERGENCE_ROUTE_DECISIONS: frozenset[str] = frozenset(
    {
        "REQUESTER_CORRECTION",
        "ERP_MANUAL_CORRECTION",
        "NEEDS_CLARIFICATION",
    }
)
DIVERGENCE_TARGET_TYPES: frozenset[str] = frozenset({"FIELD", "SUPPLIER_LINK"})
DIVERGENCE_ROUTE_FROM: frozenset[str] = frozenset(
    {"in_progress", "needs_information", "under_review"}
)


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
        # Engenheiro cria pelo Portal; solicitante cria pelo código de
        # matéria-prima de Minhas Solicitações (PRC-REF-023-F04).
        return self._access or self._has(MR_PRC_CREATE)

    @property
    def can_read(self) -> bool:
        # Escopo do objeto é decidido no service: analista vê a fila
        # global; demais atores só os próprios casos.
        return (
            self._access
            or self._has(MR_ACCESS)
            or self._has(MR_PRC_CREATE)
        )

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
        alternatives = _ACTION_PERMISSION.get(action, ())
        return any(
            all(self._has(code) for code in required)
            for required in alternatives
        )

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
