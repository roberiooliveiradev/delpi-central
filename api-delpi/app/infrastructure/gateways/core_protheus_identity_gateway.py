"""S2S read of Core Protheus identity for the authenticated portal user."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from app.config import settings
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.utils.logger import log_error


class CoreProtheusIdentityGateway:
    """Resolve mapped+verified Protheus USR_ID for a Core user UUID (read-only)."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        service_token: str | None = None,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = (
            base_url
            if base_url is not None
            else (settings.CORE_API_BASE_URL or "")
        ).rstrip("/")
        self._token = (
            service_token
            if service_token is not None
            else (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "")
        ).strip()
        self._timeout = timeout_seconds
        self._client = client

    def configured(self) -> bool:
        return bool(self._base_url and self._token)

    def get_identity_for_user(self, user_id: UUID) -> dict[str, Any]:
        if not self.configured():
            raise ProtheusRestError(
                "Integração com Core API não configurada para identidade Protheus.",
                code="PROTHEUS_IDENTITY_CORE_UNAVAILABLE",
                status_code=503,
            )

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}",
            "X-Delpi-Service-Token": self._token,
            "X-Delpi-Caller-App": "api-delpi",
        }
        url = f"{self._base_url}/integrations/protheus-identities/by-user/{user_id}"
        try:
            if self._client is not None:
                response = self._client.get(url, headers=headers, timeout=self._timeout)
            else:
                with httpx.Client(timeout=self._timeout, follow_redirects=False) as client:
                    response = client.get(url, headers=headers)
        except httpx.TimeoutException as exc:
            log_error("core_protheus_identity_timeout")
            raise ProtheusRestError(
                "Tempo esgotado ao consultar identidade Protheus no Core.",
                code="PROTHEUS_IDENTITY_CORE_UNAVAILABLE",
                status_code=503,
            ) from exc
        except httpx.HTTPError as exc:
            log_error("core_protheus_identity_unavailable")
            raise ProtheusRestError(
                "Core API indisponível ao consultar identidade Protheus.",
                code="PROTHEUS_IDENTITY_CORE_UNAVAILABLE",
                status_code=503,
            ) from exc

        if response.status_code == 404:
            raise ProtheusRestError(
                "Usuário sem identidade Protheus no Core.",
                code="PROTHEUS_IDENTITY_UNMAPPED",
                status_code=422,
                recoverable=False,
            )
        if response.status_code in {401, 403}:
            log_error(f"core_protheus_identity_auth_failed status={response.status_code}")
            raise ProtheusRestError(
                "Falha de autenticação S2S ao consultar identidade Protheus no Core.",
                code="PROTHEUS_IDENTITY_CORE_UNAVAILABLE",
                status_code=503,
            )
        if response.status_code >= 400:
            log_error(f"core_protheus_identity_http status={response.status_code}")
            raise ProtheusRestError(
                "Falha ao consultar identidade Protheus no Core.",
                code="PROTHEUS_IDENTITY_CORE_UNAVAILABLE",
                status_code=503,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProtheusRestError(
                "Resposta inválida do Core ao consultar identidade Protheus.",
                code="PROTHEUS_IDENTITY_CORE_UNAVAILABLE",
                status_code=503,
            ) from exc

        mapping = payload.get("mapping") if isinstance(payload, dict) else None
        if not isinstance(mapping, dict):
            raise ProtheusRestError(
                "Usuário sem identidade Protheus no Core.",
                code="PROTHEUS_IDENTITY_UNMAPPED",
                status_code=422,
                recoverable=False,
            )
        return mapping
