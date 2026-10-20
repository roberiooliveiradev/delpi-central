"""Resolve authenticated actor → Protheus codusr via Core (read-only)."""

from __future__ import annotations

from uuid import UUID

from app.application.services.integrations.protheus_supplier_create_payload import (
    validate_codusr,
)
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.infrastructure.gateways.core_protheus_identity_gateway import (
    CoreProtheusIdentityGateway,
)


def resolve_actor_codusr(
    identity_gateway: CoreProtheusIdentityGateway,
    actor_user_id: UUID,
) -> str:
    """Mapped + verified USR_ID (6 digits). Equivalence with upstream codusr is TO_INVENTORY."""
    mapping = identity_gateway.get_identity_for_user(actor_user_id)
    status = str(mapping.get("mapping_status") or "").strip().lower()
    if status == "ambiguous":
        raise ProtheusRestError(
            "Identidade Protheus ambígua; resolva o vínculo no Core antes de gravar fornecedor.",
            code="PROTHEUS_IDENTITY_AMBIGUOUS",
            status_code=422,
            recoverable=False,
        )
    if status != "mapped":
        raise ProtheusRestError(
            "Usuário sem vínculo Protheus mapeado no Core.",
            code="PROTHEUS_IDENTITY_UNMAPPED",
            status_code=422,
            recoverable=False,
        )
    if not bool(mapping.get("verified")):
        raise ProtheusRestError(
            "Identidade Protheus do usuário não está verificada.",
            code="PROTHEUS_IDENTITY_NOT_VERIFIED",
            status_code=422,
            recoverable=False,
        )
    protheus_user_id = str(mapping.get("protheus_user_id") or "").strip()
    if not protheus_user_id:
        raise ProtheusRestError(
            "Vínculo Protheus sem USR_ID.",
            code="PROTHEUS_IDENTITY_UNMAPPED",
            status_code=422,
            recoverable=False,
        )
    return validate_codusr(protheus_user_id)
