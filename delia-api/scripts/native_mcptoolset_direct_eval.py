"""NATIVE-MCPTOOLSET-DIRECT-ORCHESTRATION-01 — real owner eval.

Runs the REAL composed handler (real pydantic_ai investigation runtime,
real native ``MCPToolset`` discovery via the SDK client, real delegated
credential exchange, real governed ``call_remote_tool`` wire) against
the authorized specialists DAVI/TÉO/VISTA.

Scenarios:
  A DAVI single READ       — real product description
  B TÉO contextual consult — transformation initiatives
  C VISTA playlists        — operational panels
  D multi-specialist       — one question needing DAVI + VISTA data
  E generalization         — reworded variants + absent-record negative

Proof points per scenario: MCP invoke targets (governed wire calls —
process_tool_call interception precedes every one), grounding status,
content head, errors. INCONCLUSIVE is a valid outcome; nothing is
faked. Never prints tokens, secrets, or auth headers.

Env: DEV_PORTAL_USERNAME / DEV_PORTAL_PASSWORD + KEYCLOAK_URL inside
the delia-api container (or exported locally).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.environ.get("DELIA_APP_ROOT", "/app"))

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.composition.root_composer import (
    _compose_turn_handler,
    _wire_delegated_credential_provider,
)
from app.domain.evidence.model import ModelRef
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.mcp.adapter import (
    McpSpecialistAdapter,
)
from app.infrastructure.model_invocation.pydantic_ai_adapter import (
    PydanticAiModelInvocationAdapter,
)


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _subject_token() -> str:
    # Mint via the approved gateway surface — the real Portal path.
    # The token-exchange validates the subject token's issuer; a token
    # minted on the internal backchannel (keycloak:8080) carries
    # iss=localhost:8080 and is rejected with "Invalid token".
    token_url = (
        _env("KC_GATEWAY_TOKEN_BASE") or "http://delpi-gateway/auth"
    ).rstrip("/") + "/realms/delpi/protocol/openid-connect/token"
    data = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _env("VITE_KC_CLIENT_ID") or "delpi-central",
            "username": _env("DEV_PORTAL_USERNAME"),
            "password": _env("DEV_PORTAL_PASSWORD"),
            "scope": "openid",
        }
    ).encode()
    req = urllib.request.Request(token_url, data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode()).get("access_token")


class _CountingMcpAdapter:
    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.list_calls = 0
        self.invoke_calls = 0
        self.invoke_targets: list[str] = []

    def __getattr__(self, name):
        return getattr(self._adapter, name)

    def list_remote_tools(self, *args, **kwargs):
        self.list_calls += 1
        return self._adapter.list_remote_tools(*args, **kwargs)

    def call_remote_tool(self, specialist, remote_name, *a, **kw):
        self.invoke_calls += 1
        self.invoke_targets.append(
            f"{getattr(specialist, 'value', specialist)}:{remote_name}"
        )
        return self._adapter.call_remote_tool(
            specialist, remote_name, *a, **kw
        )


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="native-mcp-eval",
        name="Native MCP Eval",
        email="native-mcp-eval@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _compose():
    settings = Settings()
    if settings.llm_egress_blocked_reason:
        raise SystemExit(
            f"refused: {settings.llm_egress_blocked_reason}"
        )
    connections = specialist_connections_from_settings(settings)
    mcp = _CountingMcpAdapter(
        McpSpecialistAdapter(
            connections,
            credential_provider=_wire_delegated_credential_provider(
                settings, connections
            ),
        )
    )
    interop = SpecialistInterop(mcp)
    adapter = PydanticAiModelInvocationAdapter(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        default_max_output_units=settings.llm_max_output_tokens,
    )
    handler = _compose_turn_handler(
        InvokeModel(adapter),
        ModelRef(
            model_id=settings.llm_model,
            version="configured",
            owner_ref="DELPI",
            provider_ref="openai_compatible",
        ),
        interop,
        settings,
        connections,
    )
    return handler, mcp


def _run(handler, mcp, question: str, bearer: str) -> dict:
    started = time.monotonic()
    binding = bind_subject_bearer(bearer)
    error = None
    result = None
    before = mcp.invoke_calls
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(), input_text=question
            )
        )
    except Exception as exc:
        error = getattr(exc, "code", type(exc).__name__)
    finally:
        unbind_subject_bearer(binding)
    return {
        "elapsed_s": round(time.monotonic() - started, 1),
        "error": error,
        "grounding": str(getattr(result, "grounding_status", "")),
        "mcp_invoke_targets": mcp.invoke_targets[before:],
        "content_head": (getattr(result, "content", "") or "")[:160],
        "limitations": [
            str(x)[:80]
            for x in (getattr(result, "limitations", None) or ())
        ][:6],
    }


QUESTIONS = {
    "A_davi_product": "Qual é a descrição do produto 50220013?",
    "B_teo_transform": (
        "Quais informações estão disponíveis sobre as iniciativas "
        "de transformação digital?"
    ),
    "C_vista_playlists": (
        "Quais playlists estão disponíveis nos painéis operacionais?"
    ),
    "D_multi_mcp": (
        "Qual é a descrição do produto 50220013 e quais playlists "
        "estão disponíveis nos painéis operacionais?"
    ),
    "E1_reword_davi": "me diz o que é o item 50220013",
    "E2_reword_vista": "liste para mim as playlists dos dashboards",
    "E3_absent_record": "Qual é a descrição do produto 00000000?",
}


def main() -> int:
    for required in (
        "DEV_PORTAL_USERNAME",
        "DEV_PORTAL_PASSWORD",
        "KEYCLOAK_URL",
    ):
        if not _env(required):
            print(f"missing env {required}")
            return 2
    handler, mcp = _compose()
    out = {"model": Settings().llm_model, "scenarios": {}}
    for sid, question in QUESTIONS.items():
        try:
            res = _run(handler, mcp, question, _subject_token())
        except Exception as exc:
            res = {"error": type(exc).__name__}
        out["scenarios"][sid] = res
        print(f"== {sid}: {json.dumps(res, ensure_ascii=False)}")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
