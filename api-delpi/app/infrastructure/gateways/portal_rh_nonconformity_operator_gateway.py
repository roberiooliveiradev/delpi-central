"""Resolução S2S de matrículas para exibição no Dashboard Qualidade (#1538).

O Portal RH continua sendo autoridade do nome; indisponibilidade não elimina
as NCs, apenas mantém o código do operador visível. Credenciais nunca saem
no contrato HTTP público da Qualidade.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, str | None]] = {}
_lock = threading.Lock()
_CACHE_TTL_SECONDS = 900
_MAX_CACHE_ENTRIES = 1024


def resolve_nc_operator_name(registration: str) -> str | None:
    registration = registration.strip()
    if not registration or len(registration) > 30:
        return None

    now = time.monotonic()
    with _lock:
        cached = _cache.get(registration)
        if cached and cached[0] > now:
            return cached[1]

    base_url = os.getenv("PORTAL_RH_API_URL", "").strip().rstrip("/")
    token = os.getenv("PORTAL_RH_API_SERVICE_TOKEN", "").strip()
    if not base_url or not token:
        return None

    try:
        timeout = min(max(float(os.getenv("PORTAL_RH_API_TIMEOUT", "2")), 0.5), 3.0)
    except (ValueError, TypeError):
        timeout = 2.0

    try:
        response = httpx.get(
            f"{base_url}/api/v1/integrations/collaborators/{quote(registration, safe='')}/",
            headers={
                "Accept": "application/json",
                "X-Delpi-Service-Token": token,
            },
            timeout=timeout,
            follow_redirects=False,
        )
        if response.status_code == 404:
            name = None
        elif response.status_code == 200:
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("registration") != registration:
                logger.warning("quality_nc_operator_contract_invalid")
                return None
            name_raw = payload.get("full_name")
            name = name_raw.strip() if isinstance(name_raw, str) and name_raw.strip() else None
        else:
            logger.warning("quality_nc_operator_directory_unavailable status=%s", response.status_code)
            return None
    except (httpx.HTTPError, ValueError):
        logger.warning("quality_nc_operator_directory_request_failed")
        return None

    with _lock:
        if len(_cache) >= _MAX_CACHE_ENTRIES:
            _cache.clear()
        _cache[registration] = (time.monotonic() + _CACHE_TTL_SECONDS, name)
    return name
