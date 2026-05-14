from __future__ import annotations

import os
from typing import Any

import requests


class CoreMeGateway:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("CORE_API_BASE_URL") or "http://core-api:8000").rstrip("/")

    def get_me(self, authorization_header: str | None) -> dict[str, Any] | None:
        if not authorization_header:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/me",
                headers={"Authorization": authorization_header},
                timeout=5,
            )
        except requests.RequestException:
            return None

        if response.status_code != 200:
            return None

        payload = response.json()

        return payload if isinstance(payload, dict) else None
