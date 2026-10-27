from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import requests
from delpi_auth.service_token import apply_internal_service_headers

from app.infrastructure.config.settings import Settings

logger = logging.getLogger("supplies-api.delpi_api")


def _extract_error(response) -> tuple[str | None, str | None, list | None]:
    """Extract (code, message, fields) from the api-delpi error envelope.

    The route layer decides what is safe to project — this helper only reads
    the published envelope shape ({success, message, error:{code, fields}})
    and the generic {detail, code} form.
    """
    try:
        payload = response.json()
    except ValueError:
        return None, None, None
    if not isinstance(payload, dict):
        return None, None, None
    error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
    code = payload.get("code") or error.get("code")
    message = payload.get("message") or payload.get("detail")
    fields = error.get("fields") or payload.get("fields")
    return (
        code if isinstance(code, str) and code else None,
        message if isinstance(message, str) and message else None,
        fields if isinstance(fields, list) else None,
    )


class DelpiApiGatewayError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        upstream_message: str | None = None,
        fields: list | None = None,
    ):
        self.status_code = status_code
        self.code = code
        # Sanitized upstream text/field list — the route layer republishes
        # only for allowlisted codes; never trust it for unknown codes.
        self.upstream_message = upstream_message
        self.fields = fields
        super().__init__(message)


class DelpiApiGateway:
    """HTTP client for api-delpi reads — timeout required, no blind write retries."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self.base_url = (base_url or Settings.DELPI_API_URL).rstrip("/") + "/"
        self.timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.DELPI_API_TIMEOUT_SECONDS
        )
        self.caller_app = caller_app or Settings.SUPPLIES_CALLER_APP

    def get(
        self,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._request("GET", path, access_token=access_token, params=params)

    def post(
        self,
        path: str,
        *,
        access_token: str,
        json_body: dict[str, Any],
    ) -> Any:
        return self._request("POST", path, access_token=access_token, json_body=json_body)

    def put(
        self,
        path: str,
        *,
        access_token: str,
        json_body: dict[str, Any],
    ) -> Any:
        return self._request("PUT", path, access_token=access_token, json_body=json_body)

    def _build_headers(self, access_token: str) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Delpi-Caller-App": self.caller_app,
        }
        apply_internal_service_headers(headers)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        method_upper = method.upper()
        if method_upper in {"POST", "PUT", "PATCH", "DELETE"} and json_body is not None:
            # Explicit writes allowed only as single attempt — never retry here.
            pass

        url = urljoin(self.base_url, path.lstrip("/"))
        headers = self._build_headers(access_token)
        try:
            from flask import g, has_request_context

            if has_request_context():
                request_id = getattr(g, "request_id", None)
                if request_id:
                    headers["X-Request-Id"] = str(request_id)
        except ImportError:
            pass

        try:
            response = requests.request(
                method_upper,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            logger.warning("delpi_api_timeout path=%s", path)
            raise DelpiApiGatewayError("api-delpi timeout") from exc
        except requests.RequestException as exc:
            logger.exception("delpi_api_request_failed path=%s", path)
            raise DelpiApiGatewayError("api-delpi request failed") from exc

        if response.status_code >= 400:
            code, upstream_message, fields = _extract_error(response)
            raise DelpiApiGatewayError(
                "api-delpi server error"
                if response.status_code >= 500
                else "api-delpi client error",
                status_code=response.status_code,
                code=code,
                upstream_message=upstream_message,
                fields=fields,
            )

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise DelpiApiGatewayError("api-delpi invalid JSON") from exc
