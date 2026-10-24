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

    def lookup_directory_users(
        self,
        *,
        access_token: str,
        user_ids: list[str],
        reveal_email: bool = False,
    ) -> dict[str, dict[str, str]]:
        """Best-effort directory lookup with the caller's Bearer (admin reading others).

        `reveal_email` opts into the Core contract flag that returns the real
        professional address — only for surfaces authorized to display it
        (the user profile behind self|admin). Keep masked for enrichment-only
        callers (data minimization).
        """
        ordered: list[str] = []
        seen: set[str] = set()
        for raw in user_ids:
            user_id = str(raw or "").strip()
            if not user_id or user_id in seen:
                continue
            seen.add(user_id)
            ordered.append(user_id)
        if not ordered:
            return {}

        url = urljoin(self.base_url, "me/directory/users/lookup")
        body: dict[str, object] = {"ids": ordered}
        if reveal_email:
            body["reveal_email"] = True
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.exception("core_api_directory_lookup_failed")
            return {}

        if response.status_code >= 400:
            return {}

        try:
            payload = response.json()
        except ValueError:
            return {}

        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {}

        result: dict[str, dict[str, str]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            user_id = str(item.get("id") or "").strip()
            if not user_id:
                continue
            name = str(item.get("name") or item.get("display_name") or "").strip()
            email = str(item.get("email") or "").strip()
            result[user_id] = {
                "id": user_id,
                "name": name or user_id,
                "email": email,
            }
        return result

    def lookup_protheus_identities(
        self,
        *,
        protheus_user_ids: list[str] | None = None,
        user_ids: list[str] | None = None,
    ) -> dict[str, dict] | None:
        """S2S batch resolution Protheus user id ↔ Core identity mapping.

        Core contract: POST /integrations/protheus-identities/lookup accepts
        `protheus_user_ids` and/or `user_ids` (max 50 per call, only
        `mapping_status == "mapped"` rows match). Returns items keyed by
        `protheus_user_id` and by `user_id` (each item carries both fields,
        so either direction can be resolved from a single call).
        Soft-fail on transport/auth errors: returns None when every call
        failed (degradation) and {} when nothing was requested — callers
        must degrade to source names, never fabricate identities.
        """
        token = (Settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()
        if not token:
            return {}

        ordered: list[str] = []
        seen: set[str] = set()
        for raw in protheus_user_ids or []:
            pid = str(raw or "").strip()
            if not pid or pid in seen:
                continue
            seen.add(pid)
            ordered.append(pid)

        ordered_users: list[str] = []
        seen_users: set[str] = set()
        for raw in user_ids or []:
            uid = str(raw or "").strip()
            if not uid or uid in seen_users:
                continue
            seen_users.add(uid)
            ordered_users.append(uid)

        if not ordered and not ordered_users:
            return {}

        auth = token if token.lower().startswith("bearer ") else f"Bearer {token}"
        service = token[7:].strip() if token.lower().startswith("bearer ") else token
        headers = {
            "Authorization": auth,
            "X-Delpi-Service-Token": service,
            "X-Delpi-Caller-App": "supplies-api",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        bodies: list[dict[str, list[str]]] = []
        for start in range(0, len(ordered), 50):
            bodies.append({"protheus_user_ids": ordered[start : start + 50]})
        for start in range(0, len(ordered_users), 50):
            bodies.append({"user_ids": ordered_users[start : start + 50]})

        result: dict[str, dict] = {}
        succeeded = False
        url = urljoin(self.base_url, "integrations/protheus-identities/lookup")
        for body in bodies:
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=self.timeout,
                )
            except requests.RequestException:
                logger.warning("core_api_protheus_identities_lookup_failed")
                continue
            if response.status_code in (401, 403):
                logger.warning(
                    "core_api_protheus_identities_rejected status=%s",
                    response.status_code,
                )
                return None
            if response.status_code >= 400:
                logger.warning(
                    "core_api_protheus_identities_error status=%s",
                    response.status_code,
                )
                continue
            try:
                payload = response.json()
            except ValueError:
                continue
            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                continue
            succeeded = True
            for item in items:
                if not isinstance(item, dict):
                    continue
                pid = str(item.get("protheus_user_id") or "").strip()
                if pid:
                    result[pid] = item
        return result if succeeded else None

    def lookup_person_profiles(
        self,
        *,
        user_ids: list[str],
    ) -> dict[str, dict]:
        """S2S batch person-profiles — `has_photo` per Core user id.

        Core contract: POST /integrations/person-profiles/lookup,
        max 50 ids per call. Soft-fail ({}) on errors.
        """
        token = (Settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()
        if not token:
            return {}

        ordered: list[str] = []
        seen: set[str] = set()
        for raw in user_ids:
            uid = str(raw or "").strip()
            if not uid or uid in seen:
                continue
            seen.add(uid)
            ordered.append(uid)
        if not ordered:
            return {}

        auth = token if token.lower().startswith("bearer ") else f"Bearer {token}"
        service = token[7:].strip() if token.lower().startswith("bearer ") else token
        headers = {
            "Authorization": auth,
            "X-Delpi-Service-Token": service,
            "X-Delpi-Caller-App": "supplies-api",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        result: dict[str, dict] = {}
        for start in range(0, len(ordered), 50):
            chunk = ordered[start : start + 50]
            url = urljoin(self.base_url, "integrations/person-profiles/lookup")
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json={"ids": chunk},
                    timeout=self.timeout,
                )
            except requests.RequestException:
                logger.warning("core_api_person_profiles_lookup_failed")
                continue
            if response.status_code >= 400:
                logger.warning(
                    "core_api_person_profiles_rejected status=%s",
                    response.status_code,
                )
                continue
            try:
                payload = response.json()
            except ValueError:
                continue
            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                uid = str(item.get("user_id") or "").strip()
                if uid:
                    result[uid] = item
        return result

    def get_person_profile_photo(
        self,
        user_id: str,
    ) -> tuple[bytes, str, str] | None:
        """S2S Core person photo bytes → (content, content_type, file_name).

        Soft-fail None on transport/auth/404 — callers must not break.
        """
        uid = (user_id or "").strip()
        token = (Settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()
        if not uid or not token:
            return None
        url = urljoin(self.base_url, f"integrations/person-profiles/{uid}/photo")
        auth = token if token.lower().startswith("bearer ") else f"Bearer {token}"
        service = token[7:].strip() if token.lower().startswith("bearer ") else token
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": auth,
                    "X-Delpi-Service-Token": service,
                    "X-Delpi-Caller-App": "supplies-api",
                    "Accept": "*/*",
                },
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.warning("core_api_person_photo_failed user_id=%s", uid)
            return None
        if response.status_code >= 400:
            if response.status_code != 404:
                logger.warning(
                    "core_api_person_photo_rejected status=%s user_id=%s",
                    response.status_code,
                    uid,
                )
            return None
        content_type = (
            response.headers.get("content-type") or "application/octet-stream"
        ).split(";")[0].strip()
        file_name = "photo.bin"
        disposition = response.headers.get("content-disposition") or ""
        if "filename=" in disposition:
            file_name = (
                disposition.split("filename=", 1)[1].strip().strip('"') or file_name
            )
        return response.content, content_type, file_name

    def get_person_profile(self, user_id: str) -> dict | None:
        """S2S Core person-profile (cargo/contatos). Soft-fail None se indisponível."""
        uid = (user_id or "").strip()
        token = (Settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()
        if not uid or not token:
            return None
        url = urljoin(self.base_url, f"integrations/person-profiles/{uid}")
        auth = token if token.lower().startswith("bearer ") else f"Bearer {token}"
        service = token[7:].strip() if token.lower().startswith("bearer ") else token
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": auth,
                    "X-Delpi-Service-Token": service,
                    "X-Delpi-Caller-App": "supplies-api",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.exception("core_api_person_profile_failed user_id=%s", uid)
            return None
        if response.status_code >= 400:
            logger.warning(
                "core_api_person_profile_rejected status=%s user_id=%s",
                response.status_code,
                uid,
            )
            return None
        try:
            payload = response.json()
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None
