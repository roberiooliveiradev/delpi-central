import time
from urllib.parse import quote

import requests


class HttpExternalActionGateway:
    def execute(
        self,
        provider: dict,
        action: dict,
        parameters: dict | None,
        body,
        access_token: str | None,
    ) -> dict:
        parameters = parameters or {}
        started_at = time.perf_counter()

        url = self._build_url(
            base_url=provider["baseUrl"],
            path=action["path"],
            parameters=parameters,
        )

        query_params = self._extract_query_params(action, parameters)
        headers = self._build_headers(provider, access_token)

        response = requests.request(
            method=action["method"],
            url=url,
            params=query_params,
            json=body if self._should_send_json_body(action, body) else None,
            data=body if self._should_send_raw_body(action, body) else None,
            headers=headers,
            timeout=provider.get("timeoutSeconds", 30),
        )

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        payload = self._parse_response(response)

        return {
            "statusCode": response.status_code,
            "durationMs": duration_ms,
            "data": payload,
            "ok": 200 <= response.status_code < 300,
        }

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

        auth_mode = provider.get("authMode") or "none"
        auth_config = provider.get("authConfig") or {}

        if auth_mode == "forward_user_bearer" and access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        if auth_mode == "static_bearer":
            token = auth_config.get("token")

            if token:
                headers["Authorization"] = f"Bearer {token}"

        if auth_mode == "api_key_header":
            header_name = auth_config.get("headerName")
            value = auth_config.get("value")

            if header_name and value:
                headers[header_name] = value

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
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            return response.json()

        text = response.text or ""

        return {
            "contentType": content_type,
            "text": text[:8000],
        }
