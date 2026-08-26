from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from delpi_api_client.client import DelpiApiError

from purchase_requests_app.application.use_cases.sync_portal_user_protheus_mapping_by_email_use_case import (
    SyncPortalUserProtheusMappingByEmailUseCase,
    TotvsLookupUnavailableError,
)


def test_sync_by_email_maps_when_totvs_user_found() -> None:
    gateway = MagicMock()
    gateway.get_protheus_user_by_email.return_value = {
        "found": True,
        "match_count": 1,
        "user": {
            "protheus_user_id": "000123",
            "code": "123",
            "name": "Yago",
            "email": "compras@delpi.com.br",
        },
    }
    repository = MagicMock()
    repository.upsert_mapping.return_value = {
        "user_id": "portal-user-1",
        "protheus_user_id": "000123",
        "mapping_source": "email_match",
        "verified": True,
    }

    actor = SimpleNamespace(
        is_superadmin=False,
        permissions=["rbac.manage", "users.manage"],
    )
    result = SyncPortalUserProtheusMappingByEmailUseCase(
        gateway=gateway,
        repository=repository,
    ).execute(
        actor=actor,
        user_id="portal-user-1",
        email="compras@delpi.com.br",
    )

    assert result["mapping"]["protheus_user_id"] == "000123"
    repository.upsert_mapping.assert_called_once()
    assert repository.upsert_mapping.call_args.kwargs["mapping_source"] == "email_match"


def test_sync_by_email_requires_portal_user_manage() -> None:
    actor = SimpleNamespace(is_superadmin=False, permissions=["purchase-requests.access"])
    try:
        SyncPortalUserProtheusMappingByEmailUseCase().execute(
            actor=actor,
            user_id="u1",
            email="a@b.com",
        )
        assert False, "expected PermissionError"
    except PermissionError:
        pass


def test_sync_maps_delpi_api_503_to_totvs_unavailable() -> None:
    gateway = MagicMock()
    gateway.get_protheus_user_by_email.side_effect = DelpiApiError(
        503,
        "Não foi possível consultar o TOTVS para o usuário Protheus.",
    )
    actor = SimpleNamespace(
        is_superadmin=False,
        permissions=["rbac.manage", "users.manage"],
    )

    try:
        SyncPortalUserProtheusMappingByEmailUseCase(gateway=gateway).execute(
            actor=actor,
            user_id="u1",
            email="compras@delpi.com.br",
        )
        assert False, "expected TotvsLookupUnavailableError"
    except TotvsLookupUnavailableError:
        pass
