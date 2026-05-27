import logging
from urllib.parse import urljoin

import requests

from app.domain.exceptions.authorization_exceptions import CoreApiUnavailableError
from app.domain.ports.core_api_gateway_port import CoreApiGatewayPort
from app.infrastructure.config.settings import Settings


logger = logging.getLogger("minha-delpi-ai-api.core_api")


class CoreApiHttpGateway(CoreApiGatewayPort):
    def __init__(self):
        self.base_url = Settings.CORE_API_BASE_URL.rstrip("/") + "/"
        self.timeout = Settings.CORE_API_TIMEOUT_SECONDS

    def get_me(self, access_token: str) -> dict:
        return self._get("me", access_token)

    def get_apps(self, access_token: str) -> list[dict]:
        data = self._get("me/apps", access_token)
        return data if isinstance(data, list) else []

    def get_access_profile(self, access_token: str) -> dict:
        data = self._get("me/access-profile", access_token)
        return data if isinstance(data, dict) else {}

    def get_routes(self, access_token: str) -> list[dict]:
        data = self._get("me/routes", access_token)
        return data if isinstance(data, list) else []

    def search_directory_users(
        self,
        access_token: str,
        *,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        from urllib.parse import urlencode

        params = urlencode({"q": query, "limit": max(1, min(limit, 20))})
        data = self._get(f"me/directory/users?{params}", access_token)

        if isinstance(data, dict):
            items = data.get("items")
            return items if isinstance(items, list) else []

        return []

    def lookup_directory_users(
        self,
        access_token: str,
        user_ids: list[str],
    ) -> list[dict]:
        url = urljoin(self.base_url, "me/directory/users/lookup")

        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"ids": user_ids},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.exception("core_api_lookup_users_failed")
            raise CoreApiUnavailableError("Core API request failed") from exc

        if response.status_code >= 500:
            raise CoreApiUnavailableError("Core API server error")

        if response.status_code in (401, 403):
            return []

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise CoreApiUnavailableError("Invalid Core API response") from exc

        if isinstance(data, dict):
            items = data.get("items")
            return items if isinstance(items, list) else []

        return []

    def _get(self, path: str, access_token: str):
        url = urljoin(self.base_url, path)

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
            logger.exception("core_api_request_failed", extra={"path": path})
            raise CoreApiUnavailableError("Core API request failed") from exc

        if response.status_code >= 500:
            logger.error(
                "core_api_server_error",
                extra={
                    "path": path,
                    "status_code": response.status_code,
                },
            )
            raise CoreApiUnavailableError("Core API server error")

        if response.status_code in (401, 403):
            return {
                "authorized": False,
                "permissions": [],
                "status_code": response.status_code,
            }

        try:
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.exception(
                "core_api_invalid_response",
                extra={
                    "path": path,
                    "status_code": response.status_code,
                },
            )
            raise CoreApiUnavailableError("Invalid Core API response") from exc
