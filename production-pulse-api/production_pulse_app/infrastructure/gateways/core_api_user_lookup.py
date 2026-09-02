from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

CORE_API_URL = (
    os.getenv("DELPI_AUTH_CORE_API_URL") or os.getenv("CORE_API_URL") or "http://core-api:8000"
)
LOOKUP_TIMEOUT_SECONDS = float(os.getenv("DELPI_AUTH_RBAC_TIMEOUT_SECONDS", "2.5"))


def lookup_directory_users_by_ids(
    user_ids: list[str],
    authorization: str | None,
) -> dict[str, dict[str, str | None]]:
    """Resolve nome e e-mail via POST /me/directory/users/lookup (core-api)."""
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
                "command_audit_user_lookup_failed status=%s core_api_url=%s",
                response.status_code,
                CORE_API_URL,
            )
            return {}

        items = response.json().get("items") or []
        profiles: dict[str, dict[str, str | None]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            user_id = item.get("id")
            if not user_id:
                continue
            name = item.get("name")
            email = item.get("email")
            profiles[str(user_id)] = {
                "name": name.strip() if isinstance(name, str) and name.strip() else None,
                "email": email.strip() if isinstance(email, str) and email.strip() else None,
            }
        return profiles
    except Exception:
        logger.warning(
            "command_audit_user_lookup_failed core_api_url=%s",
            CORE_API_URL,
            exc_info=True,
        )
        return {}
