import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.infrastructure.db.models.external_action_model import ExternalActionModel
from app.infrastructure.db.models.external_action_provider_model import ExternalActionProviderModel
from app.infrastructure.db.models.external_action_test_log_model import ExternalActionTestLogModel
from app.extensions.db import db


@dataclass
class ExternalActionTestResult:
    ok: bool
    status_code: int | None
    duration_ms: int
    url: str
    response_preview: str | None
    error_message: str | None


class ExternalActionTestExecutor:
    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        provider_key: str,
        action_id: str,
        path_params: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        body: Any = None,
    ) -> ExternalActionTestResult:
        provider = ExternalActionProviderModel.query.filter_by(
            provider_key=provider_key,
            enabled=True,
        ).first()

        if not provider:
            raise ValueError("Provider/action não encontrado ou desativado.")

        action = (
            ExternalActionModel.query
            .filter_by(provider_id=provider.id, action_id=action_id, enabled=True)
            .first()
        )

        if not action:
            raise ValueError("Rota/action não encontrada ou desativada.")

        url = self._build_url(provider.base_url, action.path, path_params or {}, query or {})
        method = action.method.upper()
        headers = {
            "Accept": "application/json",
            "User-Agent": "Minha-DELPI-Action-Tester/1.0",
        }

        payload_bytes = None

        if method not in {"GET", "HEAD"} and body not in (None, ""):
            payload_bytes = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        self._apply_auth(headers, provider.auth_mode, provider.auth_config or {})

        started = time.monotonic()
        status_code = None
        response_preview = None
        error_message = None
        ok = False

        try:
            request = urllib.request.Request(
                url=url,
                data=payload_bytes,
                headers=headers,
                method=method,
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                status_code = int(response.status)
                response_body = response.read(12000)
                response_preview = response_body.decode("utf-8", errors="replace")
                ok = 200 <= status_code < 300

        except urllib.error.HTTPError as exc:
            status_code = int(exc.code)
            response_preview = exc.read(12000).decode("utf-8", errors="replace")
            error_message = f"HTTP {status_code}"
            ok = False
        except Exception as exc:
            error_message = str(exc)
            ok = False

        duration_ms = int((time.monotonic() - started) * 1000)

        log = ExternalActionTestLogModel(
            user_id=user_id,
            agent_id=agent_id,
            provider_key=provider_key,
            action_id=action_id,
            method=method,
            url=url,
            request_payload={
                "pathParams": path_params or {},
                "query": query or {},
                "body": body,
            },
            status_code=status_code,
            ok=ok,
            duration_ms=duration_ms,
            response_preview=response_preview,
            error_message=error_message,
        )
        db.session.add(log)
        db.session.flush()

        return ExternalActionTestResult(
            ok=ok,
            status_code=status_code,
            duration_ms=duration_ms,
            url=url,
            response_preview=response_preview,
            error_message=error_message,
        )

    def list_logs(
        self,
        *,
        user_id: str,
        agent_id: str,
        provider_key: str,
        action_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = (
            ExternalActionTestLogModel.query
            .filter_by(
                user_id=user_id,
                agent_id=agent_id,
                provider_key=provider_key,
                action_id=action_id,
            )
            .order_by(ExternalActionTestLogModel.created_at.desc())
            .limit(max(1, min(limit, 50)))
            .all()
        )

        return [
            {
                "id": str(row.id),
                "providerKey": row.provider_key,
                "actionId": row.action_id,
                "method": row.method,
                "url": row.url,
                "requestPayload": row.request_payload,
                "statusCode": row.status_code,
                "ok": row.ok,
                "durationMs": row.duration_ms,
                "responsePreview": row.response_preview,
                "errorMessage": row.error_message,
                "createdAt": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

    def _build_url(
        self,
        base_url: str,
        path: str,
        path_params: dict[str, Any],
        query: dict[str, Any],
    ) -> str:
        final_path = path

        for key, value in path_params.items():
            encoded = urllib.parse.quote(str(value), safe="")
            final_path = final_path.replace("{" + key + "}", encoded)

        url = base_url.rstrip("/") + "/" + final_path.lstrip("/")

        cleaned_query = {
            key: value
            for key, value in query.items()
            if value not in (None, "")
        }

        if cleaned_query:
            url += "?" + urllib.parse.urlencode(cleaned_query, doseq=True)

        return url

    def _apply_auth(
        self,
        headers: dict[str, str],
        auth_mode: str | None,
        auth_config: dict[str, Any],
    ) -> None:
        if auth_mode == "api_key":
            api_key = str(auth_config.get("apiKey") or "")
            header_name = str(auth_config.get("headerName") or "Authorization")
            scheme = str(auth_config.get("scheme") or "bearer")

            if not api_key:
                return

            if scheme == "bearer":
                headers[header_name] = f"Bearer {api_key}"
            elif scheme == "basic":
                headers[header_name] = f"Basic {api_key}"
            else:
                headers[header_name] = api_key
