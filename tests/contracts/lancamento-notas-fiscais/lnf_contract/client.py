"""Cliente HTTP da suíte. Não registra o valor de token."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from lnf_contract.guard import assert_not_production, base_url, profile_token, target_name

# TOTVS_DB_HOST do DEV (192.168.1.230/DELPI) é base REAL do ERP — somente leitura.
# A suíte limita reconciliation/run a no máximo uma chamada positiva por processo.
_RECONCILE_RUN_COUNT = 0


@dataclass
class CallResult:
    status: int
    content_type: str
    body: object
    raw: bytes
    error: str = ""


class ContractClient:
    def __init__(self, url: str | None = None) -> None:
        self.url = (url or base_url()).rstrip("/")
        assert_not_production(self.url)
        self.target = target_name()

    def configured(self) -> bool:
        return bool(self.url)

    def call(
        self,
        method: str,
        path: str,
        *,
        profile: str | None,
        params: dict | None = None,
        json_body: dict | None = None,
        timeout: float = 60.0,
    ) -> CallResult:
        global _RECONCILE_RUN_COUNT
        if not self.url:
            raise RuntimeError("LNF_BASE_URL ausente")
        if method.upper() == "POST" and path.rstrip("/").endswith("/reconciliation/run"):
            if _RECONCILE_RUN_COUNT >= 1:
                return CallResult(
                    0,
                    "application/json",
                    {
                        "success": False,
                        "message": "suíte: reconciliation/run limitado a 1× por execução (ERP real)",
                        "data": None,
                        "error": {"code": "SUITE_RECONCILE_RUN_LIMIT", "recoverable": True},
                    },
                    b"",
                    error="SUITE_RECONCILE_RUN_LIMIT",
                )
            _RECONCILE_RUN_COUNT += 1
        headers: dict[str, str] = {"Accept": "application/json"}
        token = profile_token(profile) if profile else None
        if profile == "P10" and token:
            headers["X-Delpi-Service-Token"] = token
        elif token:
            headers["Authorization"] = token if token.lower().startswith("bearer ") else f"Bearer {token}"
        try:
            with httpx.Client(base_url=self.url, timeout=timeout, follow_redirects=False) as client:
                response = client.request(method, path, params=params, json=json_body, headers=headers)
        except httpx.HTTPError as exc:
            return CallResult(0, "", None, b"", error=type(exc).__name__)
        content_type = response.headers.get("content-type", "")
        raw = response.content
        if "json" in content_type:
            try:
                body: object = response.json()
            except ValueError:
                body = None
        else:
            body = None
        return CallResult(response.status_code, content_type, body, raw)
