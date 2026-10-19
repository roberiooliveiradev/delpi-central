"""S2S client for Core-owned Protheus identity associations."""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import quote

import httpx

from purchase_requests_app.config import settings

logger = logging.getLogger(__name__)

_CALLER_APP = "purchase-requests-api"


class CoreProtheusIdentityUnavailableError(RuntimeError):
    """Core API unreachable for Protheus identity."""


class CoreProtheusIdentityGateway:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        service_token: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._base_url = (
            base_url or settings.CORE_API_BASE_URL or "http://core-api:8000"
        ).rstrip("/")
        self._token = (
            service_token
            if service_token is not None
            else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        )
        self._timeout = float(
            timeout
            if timeout is not None
            else (settings.CORE_API_TIMEOUT or 10)
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "X-Delpi-Caller-App": _CALLER_APP,
        }
        token = (self._token or "").strip()
        if token:
            headers["X-Delpi-Service-Token"] = token
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def get_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        return self._get_mapping(f"/integrations/protheus-identities/by-user/{user_id}")

    def get_by_protheus_user_id(self, protheus_user_id: str) -> dict[str, Any] | None:
        path = (
            "/integrations/protheus-identities/by-protheus-user/"
            f"{quote(protheus_user_id, safe='')}"
        )
        return self._get_mapping(path)

    def list_mappings(self, *, page_size: int = 200) -> list[dict[str, Any]]:
        """Fetch all pages from Core paginated list (fail-closed)."""
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            url = (
                f"{self._base_url}/integrations/protheus-identities"
                f"?page={page}&page_size={page_size}"
            )
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    resp = client.get(url, headers=self._headers())
            except httpx.HTTPError as exc:
                raise CoreProtheusIdentityUnavailableError(
                    "Core API indisponível para listagem de identidades Protheus."
                ) from exc
            if resp.status_code >= 400:
                raise CoreProtheusIdentityUnavailableError(
                    f"Core rejeitou listagem Protheus [{resp.status_code}]."
                )
            body = resp.json() if resp.content else {}
            batch = body.get("items") if isinstance(body, dict) else None
            if not isinstance(batch, list):
                raise CoreProtheusIdentityUnavailableError(
                    "Resposta Core de listagem sem items."
                )
            items.extend([row for row in batch if isinstance(row, dict)])
            pagination = body.get("pagination") if isinstance(body, dict) else {}
            total_pages = int((pagination or {}).get("total_pages") or 1)
            if page >= total_pages:
                break
            page += 1
            if page > 500:
                raise CoreProtheusIdentityUnavailableError(
                    "Listagem Protheus excedeu limite de páginas."
                )
        return items

    def upsert(
        self,
        *,
        user_id: str,
        protheus_user_id: str | None,
        protheus_user_code: str | None,
        mapping_status: str,
        mapping_source: str | None,
        verified: bool,
        actor_user_id: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/integrations/protheus-identities/by-user/{user_id}"
        payload: dict[str, Any] = {
            "protheus_user_id": protheus_user_id,
            "protheus_user_code": protheus_user_code,
            "mapping_status": mapping_status,
            "mapping_source": mapping_source,
            "verified": verified,
        }
        if actor_user_id:
            payload["actor_user_id"] = actor_user_id
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.put(
                    url,
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise CoreProtheusIdentityUnavailableError(
                "Core API indisponível para identidade Protheus."
            ) from exc

        if resp.status_code >= 400:
            detail = resp.text[:300]
            raise CoreProtheusIdentityUnavailableError(
                f"Core rejeitou upsert de identidade Protheus [{resp.status_code}]: {detail}"
            )
        body = resp.json() if resp.content else {}
        mapping = body.get("mapping") if isinstance(body, dict) else None
        if not isinstance(mapping, dict):
            raise CoreProtheusIdentityUnavailableError(
                "Resposta Core sem mapping Protheus."
            )
        return mapping

    def _get_mapping(self, path: str) -> dict[str, Any] | None:
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(url, headers=self._headers())
        except httpx.HTTPError as exc:
            raise CoreProtheusIdentityUnavailableError(
                "Core API indisponível para identidade Protheus."
            ) from exc

        if resp.status_code == 404:
            return None
        if resp.status_code >= 400:
            raise CoreProtheusIdentityUnavailableError(
                f"Core rejeitou leitura de identidade Protheus [{resp.status_code}]."
            )
        body = resp.json() if resp.content else {}
        mapping = body.get("mapping") if isinstance(body, dict) else None
        return mapping if isinstance(mapping, dict) else None


def protheus_identity_owner() -> str:
    """legacy | core — sole writer after cutover must be core.

    Default ``legacy`` until operational data migration + cutover flip.
    Set ``PROTHEUS_IDENTITY_OWNER=core`` only after Core schema + data
    reconciliation are verified.
    """
    raw = (
        os.getenv("PROTHEUS_IDENTITY_OWNER")
        or os.getenv("PURCHASE_REQUESTS_PROTHEUS_IDENTITY_OWNER")
        or "legacy"
    ).strip().lower()
    return "core" if raw == "core" else "legacy"
