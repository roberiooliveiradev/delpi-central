"""DELIA-C3 semantic/CRI/evidence root-cause investigation — dev-local only.

Reproduces the PO's manual QA battery through the REAL wired path
(real Keycloak subject token -> Core /me -> DÉLIA orchestration ->
delegated MCP specialists -> CRI/presentation -> NDJSON terminal),
plus direct MCP source probes that capture the owner envelopes the
orchestrator actually consumes (agent_directives/candidates/capability
surface evidence for the D4/D5 leak trace).

Safety:
- Local Ollama only (container env); EXTERNAL_LLM_TEST_CALLS=0.
- No writes: only MESSAGE turns + READ/DISCOVERY-class MCP calls.
- Never prints tokens, secrets, or authorization headers.
- Bounded output: every source field truncated; full turn bodies kept.

Run inside a container with the delia-api env (network + KEYCLOAK_URL +
DELIA_EXCHANGE_*). Subject creds come from DEV_PORTAL_USERNAME /
DEV_PORTAL_PASSWORD env vars.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time

import requests

sys.path.insert(0, "/app")

from app.application.specialist_interop.contracts import (
    SpecialistCatalogRequest,
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import SpecialistInteropError
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.composition.root_composer import _bounded_http_get
from app.infrastructure.http.deadline_transport import deadline_http_post
from app.infrastructure.auth.core_platform_access import (
    CorePlatformAccessAdapter,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.delegation import (
    InMemoryDelegatedTokenCache,
    KeycloakDelegatedCredentialProvider,
)
from app.infrastructure.interoperability.mcp.adapter import McpSpecialistAdapter

API_URL = "http://localhost:8000/interaction/turns"
BOUND = 1200  # max chars kept per probed source field — evidence bound

QUESTIONS = [
    ("G1", "conversa", "Olá, DÉLIA! O que você pode fazer por mim?"),
    ("G2", "geral", "O que é SIPOC e como posso utilizá-lo para melhorar um processo industrial?"),
    ("G3", "industrial", "Explique a diferença entre eficiência, eficácia e produtividade com exemplos de uma fábrica."),
    ("D4", "especialistas", "Quais especialistas estão disponíveis para me ajudar com informações da DELPI?"),
    ("D5", "catalogo_viz", "Quais formatos de dados e visualizações estão disponíveis nos painéis operacionais?"),
    ("D6", "ultimo_processo", "Qual é o último processo cadastrado no Transformômetro?"),
    ("D7", "primeiro_processo", "Qual é o primeiro processo cadastrado no Transformômetro e qual sua descrição?"),
    ("D8", "material", "Qual é a descrição do material de código 10080043?"),
]

VARIATIONS = [
    ("G1v", "conversa_alt", "Oi! Em que você consegue me ajudar hoje?"),
    ("G2v", "geral_alt", "Como funciona a metodologia SIPOC na prática de melhoria de processos?"),
    ("G3v", "industrial_alt", "Qual a diferença entre ser eficiente e ser eficaz numa linha de produção?"),
    ("D4v", "especialistas_alt", "Que ferramentas ou especialistas a DÉLIA tem para consultar dados da empresa?"),
    ("D5v", "catalogo_viz_alt", "O que os dashboards operacionais conseguem exibir? Que tipos de gráfico existem?"),
    ("D6v", "ultimo_processo_alt", "Me mostre o processo mais recente registrado no Transformômetro."),
    ("D7v", "primeiro_processo_alt", "Qual foi o primeiro processo cadastrado no Transformômetro? Me descreva ele."),
    ("D8v", "material_alt", "O que é o material 10080043?"),
]

MULTITURN = [
    ("M9", "Me dê dois exemplos de terminal bala e explique suas diferenças."),
    ("M10", "Agora use o DAVI para verificar essas informações."),
    ("M11", "O MCP DAVI consegue aprofundar essa consulta?"),
    ("M12", "Compare o que você conseguiu verificar com a explicação inicial."),
]


def _claims(jwt: str) -> dict:
    return json.loads(
        base64.urlsafe_b64decode(jwt.split(".")[1] + "==")
    )


def _mint_subject_token() -> str:
    # Mint through the gateway so the issued `iss` claim matches the
    # platform audience (`http://localhost/auth/...`) — the direct
    # keycloak:8080 issuer is rejected by Core /me and the exchange.
    url = (
        f"{os.environ['DELIA_TOKEN_EXCHANGE_URL'].rsplit('/', 1)[0]}"
        "/token"
    )
    response = requests.post(
        url,
        headers={
            "Host": os.environ.get("DELIA_EXCHANGE_HOST_HEADER")
            or "minhadelpi.com.br"
        },
        data={
            "grant_type": "password",
            "client_id": "delpi-central",
            "username": os.environ["DEV_PORTAL_USERNAME"],
            "password": os.environ["DEV_PORTAL_PASSWORD"],
            "scope": "openid",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _bounded(value, limit=BOUND):
    if isinstance(value, str):
        return value[:limit] + ("…[truncated]" if len(value) > limit else "")
    if isinstance(value, dict):
        return {k: _bounded(v, limit) for k, v in list(value.items())[:40]}
    if isinstance(value, (list, tuple)):
        return [_bounded(v, limit) for v in list(value)[:40]] + (
            ["…[truncated]"] if len(value) > 40 else []
        )
    return value


def _shape(value, depth=0):
    """Field-name skeleton of a payload — structure evidence."""
    if depth > 3:
        return "…"
    if isinstance(value, dict):
        return {k: _shape(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [f"[{len(value)} items]", _shape(value[0], depth + 1) if value else "empty"]
    return type(value).__name__


def _eval_provider(settings, profiles, subject):
    from delpi_auth.jwt_validator import validate_token

    return KeycloakDelegatedCredentialProvider(
        token_url=settings.exchange_token_url,
        client_id=settings.exchange_client_id,
        client_secret=settings.exchange_client_secret,
        timeout_seconds=settings.exchange_timeout_seconds,
        http_post=deadline_http_post,
        subject_bearer_getter=lambda: subject,
        token_validator=validate_token,
        cache=InMemoryDelegatedTokenCache(
            max_ttl_seconds=settings.delegated_token_ttl_seconds
        ),
        known_resource_audiences=frozenset(
            p.resource_audience for p in profiles.values()
        ),
        host_header=settings.exchange_host_header,
    )


def _source_probes(subject: str) -> dict:
    """Direct MCP envelope capture — what the orchestrator consumes."""
    settings = Settings()
    profiles = specialist_connections_from_settings(settings)
    provider = _eval_provider(settings, profiles, subject)
    interop = SpecialistInterop(
        McpSpecialistAdapter(profiles, credential_provider=provider)
    )
    probes = {
        "davi": ("discover_delpi_information", {"query": QUESTIONS[3][2]}),
        "vista": ("get_catalog", {}),
        "teo": ("get_catalog", {}),
    }
    report: dict[str, object] = {}
    for specialist_id, (tool, args) in probes.items():
        entry: dict[str, object] = {"tool": tool}
        try:
            catalog = interop.discover_catalog(
                SpecialistCatalogRequest(
                    specialist_id=specialist_id,
                    correlation_id=f"inv-{specialist_id}",
                )
            )
            entry["catalog"] = {
                "tool_count": len(catalog.capabilities),
                "tools": {
                    c.remote_name: c.operation_class.value
                    for c in catalog.capabilities
                },
                "blocked": sorted(catalog.blocked_remote_names),
            }
        except SpecialistInteropError as exc:
            entry["catalog"] = {"error": exc.code}
        try:
            outcome = interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=specialist_id,
                    remote_capability=tool,
                    correlation_id=f"inv-{specialist_id}-call",
                    arguments=args,
                )
            )
            structured = outcome.structured
            entry["invoke"] = {
                "is_complete": outcome.is_complete,
                "content_text": _bounded(outcome.content_text),
                "structured_shape": _shape(structured) if isinstance(structured, dict) else type(structured).__name__,
                "structured": _bounded(structured),
                "envelope_fields_present": sorted(structured.keys())[:30]
                if isinstance(structured, dict)
                else [],
            }
        except SpecialistInteropError as exc:
            entry["invoke"] = {"error": exc.code, "message": str(exc)[:300]}
        report[specialist_id] = entry
    return report


def _turn(token: str, text: str, context: tuple = ()) -> dict:
    """One real NDJSON turn — activity events + terminal, fully kept."""
    started = time.monotonic()
    body: dict = {"input": text}
    if context:
        body["context"] = [
            {k: v for k, v in item.items() if v is not None}
            for item in context
        ]
    events: list[dict] = []
    terminal = None
    http_status = None
    try:
        with requests.post(
            API_URL,
            json=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/x-ndjson",
            },
            timeout=330,
            stream=True,
        ) as response:
            http_status = response.status_code
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                record = json.loads(line)
                rtype = record.get("type")
                if rtype == "activity_event":
                    events.append(
                        {
                            "t_ms": int((time.monotonic() - started) * 1000),
                            "phase": record.get("phase"),
                            "state": record.get("state"),
                            "label_code": record.get("label_code"),
                            "event": record.get("event"),
                        }
                    )
                elif rtype in ("turn_result", "turn_error"):
                    terminal = record
    except requests.RequestException as exc:
        return {"http_status": http_status, "transport_error": type(exc).__name__}

    result = (terminal or {}).get("result") or {}
    obs = result.get("observability") or {}
    return {
        "http_status": http_status,
        "wall_ms": int((time.monotonic() - started) * 1000),
        "events": events,
        "terminal_type": (terminal or {}).get("type"),
        "terminal_error": terminal if (terminal or {}).get("type") == "turn_error" else None,
        "content": result.get("content"),
        "epistemic_class": result.get("epistemic_class"),
        "grounding_status": result.get("grounding_status"),
        "limitations": result.get("limitations"),
        "provenance": result.get("provenance"),
        "presentation_kinds": [
            block.get("kind")
            for block in (result.get("presentation") or {}).get("blocks", [])
        ],
        "presentation": result.get("presentation"),
        "observability": obs,
    }


def main() -> int:
    report: dict[str, object] = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "external_llm_calls": 0,
    }
    subject = _mint_subject_token()
    report["subject"] = {
        "sub_present": bool(_claims(subject).get("sub")),
        "azp": _claims(subject).get("azp"),
    }

    if os.getenv("INVEST_SKIP_PROBES") != "1":
        report["source_probes"] = _source_probes(subject)
        if os.getenv("INVEST_ONLY_PROBES") == "1":
            print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
            return 0

    cases: dict[str, object] = {}
    token_issued = time.monotonic()

    def _token() -> str:
        nonlocal subject, token_issued
        if time.monotonic() - token_issued > 240:  # re-mint before 300s exp
            subject = _mint_subject_token()
            token_issued = time.monotonic()
        return subject

    for case_id, _label, question in QUESTIONS + VARIATIONS:
        cases[case_id] = {
            "question": question,
            **_turn(_token(), question),
        }
        print(f"[done] {case_id} {cases[case_id].get('wall_ms')}ms", flush=True)

    # M9-M12 single conversation — client-supplied prior turns preserved
    context: list[dict] = []
    for case_id, question in MULTITURN:
        result = _turn(_token(), question, context=tuple(context))
        cases[case_id] = {"question": question, "context_len": len(context), **result}
        print(f"[done] {case_id} {result.get('wall_ms')}ms", flush=True)
        context.append({"kind": "USER_INPUT", "content": question})
        context.append(
            {
                "kind": "DELIA_RESULT",
                "content": result.get("content") or "",
                "epistemic_class": result.get("epistemic_class"),
            }
        )

    report["cases"] = cases
    report["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
