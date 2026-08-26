from __future__ import annotations

from typing import Any, Mapping

from delpi_api_client import DelpiApiClient

from purchase_requests_app.infrastructure.http.auth_header import bearer_authorization_from_context


class DelpiPurchaseRequestsGateway:
    def __init__(self, client: DelpiApiClient | None = None) -> None:
        self._client = client or DelpiApiClient(caller_app="purchase-requests-api")

    def list_lines(
        self,
        *,
        params: Mapping[str, str | None | list[str]] | None = None,
    ) -> dict[str, Any]:
        return self._client.get_path(
            "/supplies/purchase-requests/lines",
            params=params,
            authorization=bearer_authorization_from_context(),
        )

    def list_requesters(
        self,
        *,
        params: Mapping[str, str | None | list[str]] | None = None,
    ) -> dict[str, Any]:
        return self._client.get_path(
            "/supplies/purchase-requests/requesters",
            params=params,
            authorization=bearer_authorization_from_context(),
        )

    def get_request_lines(
        self,
        *,
        branch: str,
        request_number: str,
        params: Mapping[str, str | None | list[str]] | None = None,
    ) -> dict[str, Any]:
        return self._client.get_path(
            f"/supplies/purchase-requests/lines/{branch}/{request_number}",
            params=params,
            authorization=bearer_authorization_from_context(),
        )

    def get_protheus_user_by_email(self, email: str) -> dict[str, Any]:
        return self._client.get_path(
            "/supplies/protheus-users/by-email",
            params={"email": email},
        )

    def list_recent_linked_orders(
        self,
        *,
        after_recno: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        return self._client.get_path(
            "/supplies/purchase-requests/recent-linked-orders",
            params={
                "after_recno": str(after_recno),
                "limit": str(limit),
            },
        )
