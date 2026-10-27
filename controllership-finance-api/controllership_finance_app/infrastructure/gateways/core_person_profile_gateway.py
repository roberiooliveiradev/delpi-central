"""Gateway S2S para o Core Person Profile (UX-009 — Plano 113 §23.3).

Ownership de nome/foto permanece no Core (`core-api`): este adapter é
somente transporte — a BFF da Controladoria reexpõe foto/identificação a
usuários com `access` efetivo, nunca inventa perfil e nunca monta URL de
foto por convenção.

Contrato PROVEN (mesmo padrão do requests-api — referência canônica):
- `GET  /integrations/person-profiles/{user_id}/photo` → bytes da foto
- `POST /integrations/person-profiles/lookup` → metadados (`has_photo`)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from controllership_finance_app.config import settings

logger = logging.getLogger("controllership_finance.person_profile")

MAX_LOOKUP_IDS = 50
_PHOTO_MAX_BYTES = 2 * 1024 * 1024


def _service_token() -> str:
    return (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()


class CorePersonProfileGateway:
    """Chamadas S2S ao Core person-profile — best-effort e tipadas."""

    def __init__(self, *, base_url: str | None = None, timeout: float = 8.0):
        self.base_url = (
            base_url or settings.CORE_API_BASE_URL or ""
        ).rstrip("/")
        self.timeout = timeout

    def configured(self) -> bool:
        return bool(self.base_url) and bool(_service_token())

    def _headers(self, *, accept: str = "application/json") -> dict[str, str]:
        token = _service_token()
        headers = {
            "Accept": accept,
            "X-Delpi-Caller-App": "controllership-finance-api",
        }
        if token:
            headers["X-Delpi-Service-Token"] = token
            headers["Authorization"] = (
                token if token.startswith("Bearer ") else f"Bearer {token}"
            )
        return headers

    def get_photo(self, user_id: str) -> tuple[bytes, str, str] | None:
        """``(content, content_type, file_name)`` ou ``None`` (404/
        indisponível — o consumidor decide fallback honesto)."""
        uid = (user_id or "").strip()
        if not uid or not self.configured():
            return None
        try:
            response = httpx.get(
                f"{self.base_url}/integrations/person-profiles/{uid}/photo",
                headers=self._headers(accept="*/*"),
                timeout=self.timeout,
            )
        except Exception:
            logger.exception("core_person_profile_photo_failed")
            return None
        if response.status_code != 200:
            if response.status_code not in (404,):
                logger.warning(
                    "core_person_profile_photo_rejected status=%s",
                    response.status_code,
                )
            return None
        content_type = (
            response.headers.get("content-type") or "application/octet-stream"
        ).split(";")[0].strip()
        if content_type not in ("image/jpeg", "image/png", "image/webp"):
            return None
        if not response.content or len(response.content) > _PHOTO_MAX_BYTES:
            return None
        file_name = "photo.bin"
        disposition = response.headers.get("content-disposition") or ""
        if "filename=" in disposition:
            file_name = (
                disposition.split("filename=", 1)[1].strip().strip('"')
                or file_name
            )
        return response.content, content_type, file_name

    def lookup_directory_names(
        self, user_ids: list[str], *, bearer_token: str
    ) -> dict[str, str]:
        """Nomes oficiais por lote via `POST /me/directory/users/lookup`
        com o bearer do próprio caller (mesmo padrão do proxy
        `viewer-photo`): a autorização de leitura do diretório continua
        sendo a do usuário — e-mails nunca são repassados (`mask_email`
        default do Core). Falha → ``{}`` (fallback honesto no caller)."""
        ids = [str(uid).strip() for uid in user_ids if str(uid).strip()]
        token = (bearer_token or "").strip()
        if not ids or not self.base_url or not token:
            return {}
        try:
            response = httpx.post(
                f"{self.base_url}/me/directory/users/lookup",
                headers={
                    "Authorization": token
                    if token.startswith("Bearer ")
                    else f"Bearer {token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"ids": ids[:MAX_LOOKUP_IDS]},
                timeout=self.timeout,
            )
        except Exception:
            logger.exception("core_directory_lookup_failed")
            return {}
        if response.status_code >= 400:
            logger.warning(
                "core_directory_lookup_rejected status=%s",
                response.status_code,
            )
            return {}
        try:
            payload = response.json()
        except ValueError:
            return {}
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {}
        out: dict[str, str] = {}
        for row in items:
            if not isinstance(row, dict):
                continue
            uid = str(row.get("id") or "").strip()
            name = str(row.get("name") or "").strip()
            if uid and name:
                out[uid] = name
        return out

    def lookup_has_photo(self, user_ids: list[str]) -> dict[str, bool]:
        """Metadados por lote (`has_photo` por user_id). Falha → ``{}``
        (o caller apresenta fallback, nunca bloqueia a tela)."""
        ids = [str(uid).strip() for uid in user_ids if str(uid).strip()]
        if not ids or not self.configured():
            return {}
        try:
            response = httpx.post(
                f"{self.base_url}/integrations/person-profiles/lookup",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"ids": ids[:MAX_LOOKUP_IDS]},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload: Any = response.json()
        except Exception:
            logger.exception("core_person_profile_lookup_failed")
            return {}
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {}
        out: dict[str, bool] = {}
        for row in items:
            if not isinstance(row, dict):
                continue
            uid = str(row.get("user_id") or "").strip()
            if uid:
                out[uid] = bool(row.get("has_photo"))
        return out
