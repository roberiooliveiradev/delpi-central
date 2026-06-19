"""Busca PDF técnico na biblioteca corporativa (api-delpi) quando não há anexo."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from app.infrastructure.config.settings import Settings


@dataclass(frozen=True, slots=True)
class DrawingLibraryFetchResult:
    product_code: str
    storage_path: str
    filename: str
    source: str
    metadata: dict[str, Any]


class ChatDrawingLibraryService:
    _CACHE_SUBDIR = "drawing-library-cache"

    @classmethod
    def resolve_base_url(cls) -> str:
        return (
            os.getenv("DELPI_API_URL")
            or os.getenv("API_DELPI_BASE_URL")
            or "http://delpi-api-delpi:8000"
        ).rstrip("/")

    @classmethod
    def fetch_pdf(
        cls,
        *,
        product_code: str,
        access_token: str | None = None,
    ) -> DrawingLibraryFetchResult | None:
        code = str(product_code or "").strip().upper()

        if not code or not re.fullmatch(r"[\dA-Z]+(?:-\d+)?", code):
            return None

        base_url = cls.resolve_base_url()
        headers = cls._build_headers(access_token)

        metadata_url = f"{base_url}/products/{quote(code, safe='')}/drawing"

        try:
            metadata_response = requests.get(
                metadata_url,
                headers=headers,
                timeout=float(os.getenv("DELPI_API_TIMEOUT", "30")),
            )
        except requests.RequestException:
            return None

        if metadata_response.status_code == 404:
            return None

        if metadata_response.status_code >= 400:
            return None

        metadata_payload = cls._parse_metadata(metadata_response)
        filename = str(
            (metadata_payload or {}).get("filename")
            or f"{code}.pdf"
        ).strip()

        pdf_headers = dict(headers)
        pdf_headers["Accept"] = "application/pdf"
        pdf_url = f"{base_url}/products/{quote(code, safe='')}/drawing/pdf"

        try:
            pdf_response = requests.get(
                pdf_url,
                headers=pdf_headers,
                timeout=float(os.getenv("DELPI_API_TIMEOUT", "60")),
            )
        except requests.RequestException:
            return None

        if pdf_response.status_code != 200:
            return None

        content = pdf_response.content or b""

        if not content.startswith(b"%PDF"):
            return None

        target_path = cls._resolve_cache_path(code, filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)

        return DrawingLibraryFetchResult(
            product_code=code,
            storage_path=str(target_path),
            filename=filename,
            source="api_delpi_library",
            metadata=metadata_payload or {"product_code": code, "filename": filename},
        )

    @classmethod
    def _build_headers(cls, access_token: str | None) -> dict[str, str]:
        headers = {"Accept": "application/json"}

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
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

    @classmethod
    def _parse_metadata(cls, response: requests.Response) -> dict[str, Any] | None:
        content_type = str(response.headers.get("content-type") or "").lower()

        if "application/json" not in content_type:
            return None

        try:
            payload = response.json()
        except ValueError:
            return None

        if not isinstance(payload, dict):
            return None

        data = payload.get("data")

        return data if isinstance(data, dict) else payload

    @classmethod
    def _cache_root(cls) -> Path:
        root = Path(
            os.getenv("CHAT_ATTACHMENT_STORAGE_PATH")
            or getattr(Settings, "CHAT_ATTACHMENT_STORAGE_PATH", None)
            or "/tmp/minha-delpi-chat-attachments"
        )
        cache = (root / cls._CACHE_SUBDIR).resolve()
        cache.mkdir(parents=True, exist_ok=True)
        return cache

    @classmethod
    def _resolve_cache_path(cls, product_code: str, filename: str) -> Path:
        safe_name = Path(filename).name or f"{product_code}.pdf"
        base = cls._cache_root()
        product_dir = (base / product_code).resolve()

        if not str(product_dir).startswith(str(base)):
            raise ValueError("Caminho de cache inválido.")

        product_dir.mkdir(parents=True, exist_ok=True)
        return product_dir / safe_name
