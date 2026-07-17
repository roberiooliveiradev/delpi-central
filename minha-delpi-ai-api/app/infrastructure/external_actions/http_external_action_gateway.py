import re
import time
from urllib.parse import quote

import requests

from app.domain.services.external_action_http_execution_service import (
    ExternalActionHttpExecutionService,
)


class HttpExternalActionGateway:
    def execute(
        self,
        provider: dict,
        action: dict,
        parameters: dict | None,
        body,
        access_token: str | None,
        *,
        action_path: str = "",
    ) -> dict:
        parameters = parameters or {}
        resolved_path = str(action_path or action.get("path") or "")
        timeout_seconds = ExternalActionHttpExecutionService.resolve_timeout_seconds(
            provider=provider,
            action_path=resolved_path,
        )

        url = self._build_url(
            base_url=provider["baseUrl"],
            path=action["path"],
            parameters=parameters,
        )

        query_params = self._extract_query_params(action, parameters)
        headers = self._build_headers(provider, access_token)
        method = action["method"]

        for attempt_index in range(2):
            started_at = time.perf_counter()

            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=query_params,
                    json=body if self._should_send_json_body(action, body) else None,
                    data=body if self._should_send_raw_body(action, body) else None,
                    headers=headers,
                    timeout=timeout_seconds,
                )
            except requests.Timeout:
                duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

                if ExternalActionHttpExecutionService.should_retry(
                    attempt_index=attempt_index,
                    timed_out=True,
                ):
                    continue

                return {
                    "statusCode": 504,
                    "durationMs": duration_ms,
                    "data": {
                        "success": False,
                        "error": "timeout",
                        "message": "read timed out",
                    },
                    "ok": False,
                }

            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            payload = self._parse_response(response)
            result = {
                "statusCode": response.status_code,
                "durationMs": duration_ms,
                "data": payload,
                "ok": 200 <= response.status_code < 300,
            }

            if ExternalActionHttpExecutionService.should_retry(
                attempt_index=attempt_index,
                status_code=response.status_code,
            ):
                continue

            return result

        return result

    def _build_url(self, base_url: str, path: str, parameters: dict) -> str:
        final_path = path

        for key, value in parameters.items():
            token = "{" + key + "}"

            if token in final_path:
                final_path = final_path.replace(token, quote(str(value), safe=""))

        return f"{base_url.rstrip('/')}/{final_path.lstrip('/')}"

    def _extract_query_params(self, action: dict, parameters: dict) -> dict:
        query = {}

        for parameter in action.get("parametersSchema") or []:
            if parameter.get("in") != "query":
                continue

            name = parameter.get("name")

            if name in parameters:
                query[name] = parameters[name]

        return query

    def _build_headers(self, provider: dict, access_token: str | None) -> dict:
        headers = {
            "Accept": "application/json",
        }

        auth_mode = str(provider.get("authMode") or "none").strip().lower()
        auth_config = provider.get("authConfig") or {}

        if auth_mode in {"user_token", "forward_user_bearer"} and access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        if auth_mode == "static_bearer":
            token = auth_config.get("token")

            if token:
                headers["Authorization"] = f"Bearer {token}"

        if auth_mode in {"api_key", "api_key_header"}:
            header_name = auth_config.get("headerName") or "Authorization"
            api_key = auth_config.get("apiKey") or auth_config.get("value")
            scheme = str(auth_config.get("scheme") or "bearer").lower()

            if api_key:
                if scheme == "bearer":
                    headers[header_name] = f"Bearer {api_key}"
                elif scheme == "basic":
                    headers[header_name] = f"Basic {api_key}"
                else:
                    headers[header_name] = str(api_key)

        if auth_mode == "custom_headers":
            for key, value in (auth_config.get("headers") or {}).items():
                if value is not None:
                    headers[key] = str(value)

        return headers

    def _should_send_json_body(self, action: dict, body) -> bool:
        method = str(action.get("method") or "").upper()

        if method not in {"POST", "PUT", "PATCH"}:
            return False

        return body not in (None, "", {}, []) and isinstance(body, (dict, list))

    def _should_send_raw_body(self, action: dict, body) -> bool:
        method = str(action.get("method") or "").upper()

        if method not in {"POST", "PUT", "PATCH"}:
            return False

        return body not in (None, "", {}, []) and isinstance(body, str)

    def _parse_response(self, response):
        content_type = str(response.headers.get("content-type") or "")
        disposition = str(response.headers.get("content-disposition") or "")

        if "application/json" in content_type:
            return response.json()

        lower_type = content_type.lower()
        is_binary = any(
            marker in lower_type
            for marker in (
                "application/vnd.openxmlformats",
                "application/octet-stream",
                "application/pdf",
                "application/zip",
                "spreadsheetml",
            )
        ) or "attachment" in disposition.lower()

        if is_binary:
            filename = self._filename_from_content_disposition(disposition)

            return {
                "contentType": content_type,
                "contentDisposition": disposition or None,
                "filename": filename,
                "binary": True,
                "message": (
                    "Resposta binária recebida; use format=json na action de export "
                    "para obter downloadPath."
                ),
            }

        text = response.text or ""

        return {
            "contentType": content_type,
            "text": text[:8000],
        }

    @staticmethod
    def _filename_from_content_disposition(header: str) -> str | None:
        match = re.search(r'filename="?([^";]+)"?', str(header or ""), flags=re.I)

        if not match:
            return None

        return match.group(1).strip() or None
