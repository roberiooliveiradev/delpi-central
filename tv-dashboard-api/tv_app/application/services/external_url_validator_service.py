from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from tv_app.config import settings

SETTINGS_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_dashboard_settings.json"


@lru_cache(maxsize=1)
def _load_settings() -> dict:
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def _external_url_settings() -> dict:
    return dict(_load_settings().get("externalUrl") or {})


def _is_same_origin_portal(host: str) -> bool:
    base = (settings.PUBLIC_BASE_URL or "").strip()
    if not base:
        return False
    public_host = (urlparse(base).hostname or "").lower()
    return bool(public_host and host == public_host)


def validate_external_url(url: str) -> None:
    """Raises ValueError when the URL is not https (except localhost) or host is not whitelisted."""
    raw = (url or "").strip()
    if not raw:
        raise ValueError("URL externa é obrigatória.")

    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()

    if scheme not in {"https", "http"}:
        raise ValueError("Use uma URL https:// válida.")

    settings = _external_url_settings()
    allow_localhost = bool(settings.get("allowLocalhost", True))
    if allow_localhost and host in {"localhost", "127.0.0.1"}:
        return

    if _is_same_origin_portal(host):
        return

    if scheme != "https":
        raise ValueError("Use uma URL https:// válida.")

    suffixes = [str(item).lower() for item in (settings.get("allowedHostSuffixes") or [])]
    if any(host == suffix or host.endswith(f".{suffix}") for suffix in suffixes):
        return

    message = str(settings.get("rejectionMessage") or "Domínio não permitido para iframe.")
    raise ValueError(message)
