from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode, urljoin

import requests

from app.infrastructure.config.settings import Settings

logger = logging.getLogger("supplies-api.purchase_requests")


class PurchaseRequestsGatewayError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Any = None,
    ):
        self.status_code = status_code
        self.payload = payload
        super().__init__(message)


class PurchaseRequestsGateway:
    """HTTP client for purchase-requests-api (C1). CC fail-closed stays in PR-api."""

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
            payload = self.list_purchase_requests(
                access_token=access_token,
                params={
                    "branch": branch,
                    "overall_stage": stage,
                    "page": 1,
                    "page_size": 1,
                },
            )
            data = payload.get("data", payload) if isinstance(payload, dict) else {}
            if not isinstance(data, dict):
                continue
            try:
                total += int(data.get("total") or 0)
            except (TypeError, ValueError):
                continue
        return total

    def list_purchase_requests(
        self,
        *,
        access_token: str,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        query_string: str | None = None,
    ) -> Any:
        return self.get(
            "purchase-requests",
            access_token=access_token,
            params=params,
            query_string=query_string,
        )

    def list_requesters(
        self,
        *,
        access_token: str,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        query_string: str | None = None,
    ) -> Any:
        return self.get(
            "purchase-requests/requesters",
            access_token=access_token,
            params=params,
            query_string=query_string,
        )

    def get_purchase_request(
        self,
        *,
        access_token: str,
        branch: str,
        request_number: str,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        query_string: str | None = None,
    ) -> Any:
        path = (
            f"purchase-requests/{branch.strip()}/{request_number.strip()}"
        )
        return self.get(
            path,
            access_token=access_token,
            params=params,
            query_string=query_string,
        )

    def get(
        self,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        query_string: str | None = None,
    ) -> Any:
        url = urljoin(self.base_url, path.lstrip("/"))
        if query_string:
            url = f"{url}?{query_string.lstrip('?')}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Delpi-Caller-App": self.caller_app,
        }
        try:
            response = requests.get(
                url,
                headers=headers,
                params=None if query_string else params,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            logger.warning("purchase_requests_timeout path=%s", path)
            raise PurchaseRequestsGatewayError("purchase-requests-api timeout") from exc
        except requests.RequestException as exc:
            logger.exception("purchase_requests_failed path=%s", path)
            raise PurchaseRequestsGatewayError(
                "purchase-requests-api request failed"
            ) from exc

        payload: Any = None
        if response.content:
            try:
                payload = response.json()
            except ValueError:
                payload = None

        if response.status_code >= 400:
            raise PurchaseRequestsGatewayError(
                "purchase-requests-api error",
                status_code=response.status_code,
                payload=payload,
            )

        return payload if payload is not None else {}
