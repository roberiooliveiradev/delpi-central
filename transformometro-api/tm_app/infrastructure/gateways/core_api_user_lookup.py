from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

CORE_API_URL = (
    os.getenv("DELPI_AUTH_CORE_API_URL") or os.getenv("CORE_API_URL") or "http://core-api:8000"
)
LOOKUP_TIMEOUT_SECONDS = float(os.getenv("DELPI_AUTH_RBAC_TIMEOUT_SECONDS", "2.5"))


def lookup_user_names_by_ids(
    user_ids: list[str],
    authorization: str | None,
) -> dict[str, str]:
    """Resolve nomes de exibição via POST /me/directory/users/lookup (core-api)."""
    normalized = [str(value).strip() for value in user_ids if value and str(value).strip()]
    if not normalized or not authorization:
        return {}

    try:
        timeout = httpx.Timeout(LOOKUP_TIMEOUT_SECONDS, connect=LOOKUP_TIMEOUT_SECONDS)
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{CORE_API_URL.rstrip('/')}/me/directory/users/lookup",
                json={"ids": normalized},
                headers={"Authorization": authorization},
            )
        if response.status_code != 200:
            logger.warning(
                "audit_user_name_lookup_failed status=%s core_api_url=%s",
                response.status_code,
                CORE_API_URL,
            )
            return {}

        items = response.json().get("items") or []
        names: dict[str, str] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            user_id = item.get("id")
            name = item.get("name")
            if user_id and isinstance(name, str) and name.strip():
                names[str(user_id)] = name.strip()
        return names
    except Exception:
        logger.warning(
            "audit_user_name_lookup_failed core_api_url=%s",
            CORE_API_URL,
            exc_info=True,
        )
        return {}
