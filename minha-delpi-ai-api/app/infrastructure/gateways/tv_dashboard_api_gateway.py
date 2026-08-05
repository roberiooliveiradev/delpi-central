"""Cliente HTTP do BFF TV Dashboard (copiloto → preview + CRUD /playlists)."""

from __future__ import annotations

from typing import Any

import requests

from app.infrastructure.config.settings import Settings

_CRUD_ALLOWED_METHODS = frozenset({"GET", "POST", "PATCH", "DELETE"})


class TvDashboardApiGateway:
    def __init__(self, *, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or Settings.TV_DASHBOARD_API_BASE_URL).rstrip("/")
        self.timeout = timeout if timeout is not None else Settings.TV_DASHBOARD_API_TIMEOUT_SECONDS

    def get_capabilities(self, access_token: str) -> dict[str, Any]:
        """GET /data/copilot/capabilities — catálogo versionado (sem ops embutidas na AI)."""
        return self._get("/data/copilot/capabilities", access_token=access_token)

    def suggest_ops(
        self,
        *,
        message: str,
        host_context: dict[str, Any] | None,
        access_token: str,
    ) -> dict[str, Any]:
        """POST /data/copilot/suggest-ops — NL + host → ops tipadas no BFF."""
        return self._post(
            "/data/copilot/suggest-ops",
            {
                "message": str(message or ""),
                "hostContext": host_context if isinstance(host_context, dict) else {},
            },
            access_token=access_token,
        )

    def preview_patch(
        self,
        envelope: dict[str, Any],
        *,
        access_token: str,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        return self._post(
            "/data/copilot/preview-patch",
            {
                "target": envelope.get("target") or {},
                "ops": envelope.get("ops") or [],
                "includeFingerprint": include_fingerprint,
            },
            access_token=access_token,
        )

    def apply_patch(
        self,
        envelope: dict[str, Any],
        *,
        access_token: str,
    ) -> dict[str, Any]:
        """Legado: dry-run no BFF. Persistência via ``execute_crud_command``."""
        return self._post(
            "/data/copilot/apply-patch",
            {
                "target": envelope.get("target") or {},
                "ops": envelope.get("ops") or [],
            },
            access_token=access_token,
        )

    def execute_crud_command(
        self,
        command: dict[str, Any],
        *,
        access_token: str,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        """Executa um comando CRUD allowlisted em ``/playlists/**`` com o JWT do usuário."""
        if not isinstance(command, dict):
            raise ValueError("CRUD command must be an object")

        method = str(command.get("method") or "").strip().upper()
        if method not in _CRUD_ALLOWED_METHODS:
            raise ValueError(f"HTTP method not allowlisted: {method or '?'}")

        path = self._validate_crud_path(command.get("path"))
        headers = {
            **self._auth_headers(access_token),
            "Accept": "application/json",
        }
        if expected_revision is not None and bool(command.get("requiresIfMatch")):
            headers["If-Match"] = f'"{int(expected_revision)}"'

        url = f"{self.base_url}{path}"
        request_kwargs: dict[str, Any] = {
            "headers": headers,
            "timeout": self.timeout,
        }
        body = command.get("body")
        if method in {"POST", "PATCH"} and body is not None:
            headers["Content-Type"] = "application/json"
            request_kwargs["json"] = body

        response = requests.request(method, url, **request_kwargs)
        return self._normalize_crud_response(response)

    @staticmethod
    def _validate_crud_path(path: Any) -> str:
        path_s = str(path or "").strip()
        if not path_s:
            raise ValueError("CRUD path is required")
        lowered = path_s.lower()
        if (
            "://" in path_s
            or path_s.startswith("//")
            or lowered.startswith("http:")
            or lowered.startswith("https:")
        ):
            raise ValueError(f"CRUD path must be relative (no URL/host): {path_s}")
        if ".." in path_s:
            raise ValueError(f"CRUD path traversal rejected: {path_s}")
        if not path_s.startswith("/playlists"):
            raise ValueError(f"CRUD path outside /playlists: {path_s}")
        return path_s

    def _auth_headers(self, access_token: str) -> dict[str, str]:
        bearer = (
            access_token
            if access_token.startswith("Bearer ")
            else f"Bearer {access_token}"
        )
        return {
            "Authorization": bearer,
            "Accept": "application/json",
        }

    def _get(self, path: str, *, access_token: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = requests.get(
            url,
            headers=self._auth_headers(access_token),
            timeout=self.timeout,
        )
        return self._normalize_response(response)

    def _post(self, path: str, body: dict[str, Any], *, access_token: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            **self._auth_headers(access_token),
            "Content-Type": "application/json",
        }
        response = requests.post(url, json=body, headers=headers, timeout=self.timeout)
        return self._normalize_response(response)

    @staticmethod
    def _normalize_response(response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        if not isinstance(payload, dict):
            payload = {"data": payload}
        payload.setdefault("_httpStatus", response.status_code)
        payload.setdefault("_ok", response.ok)
        return payload

    @classmethod
    def _normalize_crud_response(cls, response: requests.Response) -> dict[str, Any]:
        payload = cls._normalize_response(response)
        revision = cls._extract_playlist_revision(payload, response)
        if revision is not None:
            payload["playlistRevision"] = revision
        return payload

    @staticmethod
    def _extract_playlist_revision(
        payload: dict[str, Any],
        response: requests.Response,
    ) -> int | None:
        candidates: list[Any] = [payload.get("playlistRevision")]
        data = payload.get("data")
        if isinstance(data, dict):
            candidates.append(data.get("playlistRevision"))
        header = response.headers.get("X-Playlist-Revision") or response.headers.get(
            "x-playlist-revision"
        )
        if header is not None:
            candidates.append(header)
        for raw in candidates:
            if raw is None or raw == "":
                continue
            try:
                return int(raw)
            except (TypeError, ValueError):
                continue
        return None
