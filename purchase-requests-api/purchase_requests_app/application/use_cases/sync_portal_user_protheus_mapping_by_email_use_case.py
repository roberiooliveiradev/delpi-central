from __future__ import annotations

from typing import Any

from delpi_api_client.client import DelpiApiError

from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_portal_user_manage,
)
from purchase_requests_app.domain.services.protheus_user_candidate_resolver import (
    pick_protheus_user_candidate,
)
from purchase_requests_app.infrastructure.gateways.delpi_purchase_requests_gateway import (
    DelpiPurchaseRequestsGateway,
)
from purchase_requests_app.infrastructure.persistence.repositories.user_protheus_mapping_repository import (
    UserProtheusMappingRepository,
)


class TotvsLookupUnavailableError(RuntimeError):
    """api-delpi / TOTVS indisponível para consulta SYS_USR."""


class SyncPortalUserProtheusMappingByEmailUseCase:
    def __init__(
        self,
        *,
        gateway: DelpiPurchaseRequestsGateway | None = None,
        repository: UserProtheusMappingRepository | None = None,
    ) -> None:
        self._gateway = gateway or DelpiPurchaseRequestsGateway()
        self._repository = repository or UserProtheusMappingRepository()

    def execute(
        self,
        *,
        actor,
        user_id: str,
        email: str,
        portal_user_name: str | None = None,
    ) -> dict[str, Any]:
        if not has_portal_user_manage(actor):
            raise PermissionError("Sem permissão para gerenciar usuários do portal.")

        normalized_email = (email or "").strip().lower()
        if not normalized_email or "@" not in normalized_email:
            raise ValueError("E-mail inválido para sincronização.")

        try:
            lookup = self._gateway.get_protheus_user_by_email(normalized_email)
        except DelpiApiError as exc:
            if exc.status_code in {503, 502, 504}:
                raise TotvsLookupUnavailableError(
                    "Não foi possível consultar o TOTVS (SYS_USR). Verifique a api-delpi e o SQL Server."
                ) from exc
            raise LookupError(exc.detail or "Falha ao consultar usuário Protheus por e-mail.") from exc

        protheus_user = lookup.get("user")
        if lookup.get("ambiguous"):
            candidates = lookup.get("candidates") or []
            protheus_user = pick_protheus_user_candidate(
                candidates,
                portal_user_name=portal_user_name,
            )
            if not protheus_user:
                raise LookupError(
                    "Mais de um usuário Protheus com este e-mail. "
                    "Não foi possível desambiguar pelo nome do portal."
                )
        elif not lookup.get("found") or not protheus_user:
            raise LookupError(
                "Nenhum usuário Protheus com USR_EMAIL igual ao e-mail do portal."
            )

        protheus_user_id = str(protheus_user.get("protheus_user_id") or "").strip()
        if not protheus_user_id:
            raise LookupError("Usuário Protheus retornado sem USR_ID.")

        mapping = self._repository.upsert_mapping(
            user_id=user_id,
            protheus_user_id=protheus_user_id,
            protheus_user_code=protheus_user.get("code"),
            mapping_status="mapped",
            mapping_source="email_match",
            verified=True,
        )
        return {
            "mapping": mapping,
            "protheus_user": protheus_user,
            "synced_by_email": normalized_email,
        }
