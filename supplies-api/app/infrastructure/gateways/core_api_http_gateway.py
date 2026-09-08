from __future__ import annotations

import logging
from urllib.parse import urljoin

import requests

from app.domain.exceptions import CoreApiUnavailableError
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("supplies-api.core_api")


class CoreApiHttpGateway:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or Settings.CORE_API_BASE_URL).rstrip("/") + "/"
        self.timeout = timeout_seconds if timeout_seconds is not None else Settings.CORE_API_TIMEOUT_SECONDS

    def get_me(self, access_token: str) -> dict:
        url = urljoin(self.base_url, "me")
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.exception("core_api_request_failed path=me")
            raise CoreApiUnavailableError("Core API request failed") from exc

        if response.status_code >= 500:
            raise CoreApiUnavailableError("Core API server error")

        if response.status_code in (401, 403):
            raise CoreApiUnavailableError("Core API refused authorization lookup")

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise CoreApiUnavailableError("Invalid Core API response") from exc

        if not isinstance(data, dict):
            raise CoreApiUnavailableError("Invalid Core API response")

        return data
