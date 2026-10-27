"""Port — requests-api autenticado como usuário (Bearer encaminhado)."""

from __future__ import annotations

from typing import Any, Protocol


class RequestsApiGatewayPort(Protocol):
    def create_request_as_user(
        self,
        *,
        access_token: str,
        type_code: str,
        payload: dict[str, Any],
        branch: str | None,
        idempotency_key: str,
    ) -> dict[str, Any]: ...

    def get_request_as_user(
        self, *, access_token: str, request_id: str
    ) -> dict[str, Any]: ...
