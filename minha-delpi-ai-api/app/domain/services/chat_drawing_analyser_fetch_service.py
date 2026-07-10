"""Fetch leve do payload `/analyser` para âncora BOM na confirmação focal."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import requests

from app.domain.services.chat_drawing_analyser_payload_service import (
    ChatDrawingAnalyserPayloadService,
)
from app.domain.services.chat_drawing_analyser_parameter_service import (
    ChatDrawingAnalyserParameterService,
)
from app.domain.services.chat_drawing_library_service import ChatDrawingLibraryService


class ChatDrawingAnalyserFetchService:
    @classmethod
    def fetch_root(
        cls,
        *,
        product_code: str,
        access_token: str | None = None,
        view: str | None = None,
    ) -> dict[str, Any] | None:
        code = str(product_code or "").strip().upper()

        if not code:
            return None

        resolved_view = str(
            view or ChatDrawingAnalyserParameterService.FULL_VIEW
        ).strip() or ChatDrawingAnalyserParameterService.FULL_VIEW

        payload = cls._fetch_with_headers(
            code,
            view=resolved_view,
            headers=cls._build_headers(access_token),
        )

        if payload is not None:
            return payload

        if access_token:
            return cls._fetch_with_headers(
                code,
                view=resolved_view,
                headers=cls._build_headers(None),
            )

        return None

    @classmethod
    def _fetch_with_headers(
        cls,
        code: str,
        *,
        view: str,
        headers: dict[str, str],
    ) -> dict[str, Any] | None:
        base_url = ChatDrawingLibraryService.resolve_base_url()
        url = (
            f"{base_url}/products/{quote(code, safe='')}/analyser"
            f"?view={quote(view, safe='')}"
        )

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=float(os.getenv("DELPI_API_TIMEOUT", "30")),
            )
        except requests.RequestException:
            return None

        if response.status_code in {401, 403, 404} or response.status_code >= 400:
            return None

        try:
            body = response.json()
        except ValueError:
            return None

        data = body.get("data") if isinstance(body, dict) else body
        root = ChatDrawingAnalyserPayloadService.resolve_root_from_data(data)

        return root if isinstance(root, dict) and root else None

    @classmethod
    def _build_headers(cls, access_token: str | None) -> dict[str, str]:
        headers = {"Accept": "application/json"}

        token = str(access_token or "").strip()

        if token:
            headers["Authorization"] = f"Bearer {token}"
            return headers

        try:
            from delpi_auth.service_token import apply_internal_service_headers

            apply_internal_service_headers(headers)
        except ImportError:
            service_token = os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "").strip()

            if service_token:
                headers["X-Delpi-Service-Token"] = service_token
                headers["Authorization"] = (
                    service_token
                    if service_token.startswith("Bearer ")
                    else f"Bearer {service_token}"
                )

        return headers
