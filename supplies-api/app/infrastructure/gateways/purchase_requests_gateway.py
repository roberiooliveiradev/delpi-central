from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import requests

from app.infrastructure.config.settings import Settings

logger = logging.getLogger("supplies-api.purchase_requests")


class PurchaseRequestsGatewayError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class PurchaseRequestsGateway:
    """Thin read client for overview SC-OPEN count (CC fail-closed stays in PR-api)."""

    OPEN_STAGES = (
        "awaiting_order",
        "partially_ordered",
        "awaiting_receipt",
        "partially_received",
    )

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or Settings.PURCHASE_REQUESTS_API_URL
        ).rstrip("/") + "/"
        self.timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.PURCHASE_REQUESTS_API_TIMEOUT_SECONDS
        )
        self.caller_app = caller_app or Settings.DELPI_API_CALLER_APP

    def count_open_requests(
        self,
        *,
        access_token: str,
        branch: str,
    ) -> int:
        total = 0
        for stage in self.OPEN_STAGES:
            total += self._list_total(
                access_token=access_token,
                branch=branch,
                overall_stage=stage,
            )
        return total

    def _list_total(
        self,
        *,
        access_token: str,
        branch: str,
        overall_stage: str,
    ) -> int:
        url = urljoin(self.base_url, "purchase-requests")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Delpi-Caller-App": self.caller_app,
        }
        params = {
            "branch": branch,
            "overall_stage": overall_stage,
            "page": 1,
            "page_size": 1,
        }
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            logger.warning("purchase_requests_timeout branch=%s stage=%s", branch, overall_stage)
            raise PurchaseRequestsGatewayError("purchase-requests-api timeout") from exc
        except requests.RequestException as exc:
            logger.exception("purchase_requests_failed branch=%s", branch)
            raise PurchaseRequestsGatewayError("purchase-requests-api request failed") from exc

        if response.status_code >= 400:
            raise PurchaseRequestsGatewayError(
                "purchase-requests-api error",
                status_code=response.status_code,
            )

        payload: Any = response.json() if response.content else {}
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        if not isinstance(data, dict):
            return 0
        try:
            return int(data.get("total") or 0)
        except (TypeError, ValueError):
            return 0
