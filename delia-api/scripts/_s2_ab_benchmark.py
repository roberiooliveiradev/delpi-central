#!/usr/bin/env python3
"""S2 A/B benchmark: current arggen re-proposal (A) vs pydantic-ai
structured-output proposal (B) on the causal owner-rejection cases.

Measures schema-valid args produced for enum/discriminator tools.
Runs inside the eval container against the local Ollama model.
"""
import json
import sys
import os


def _runtime_model_identity() -> tuple[str, str]:
    """(provider, model_name) from the unified runtime JSON — probes
    report the resolved snapshot, never a retired env var."""
    import pathlib
    data = json.loads(
        (
            pathlib.Path(__file__).resolve().parents[1]
            / "config"
            / "pydantic_ai.runtime.delpi.json"
        ).read_text(encoding="utf-8")
    )
    profile = data["profiles"][
        os.getenv("DELIA_RUNTIME_PROFILE") or data["default_profile"]
    ]
    return (
        profile["model"]["provider"],
        profile["model"]["model_name"],
    )


# The 15 causal cases: (scenario, capability, question snippet, rejected_args)
CASES = [
    ("cmp_05", "clara.get_context", "fechamentos mensais dos últimos três períodos"),
    ("cmp_03", "caio.analyze", "propostas e oportunidades abertas dos últimos 120 dias"),
    ("cmp_13", "eva.analyze", "demandas e solicitações de engenharia recentes"),
    ("cmp_19", "teo.analyze", "iniciativas com atrasos repetidos ou mudanças de prazo"),
]


def _schema_for(capability: str) -> dict:
    """Fetch the live inputSchema from tools/list — never hardcoded."""
    import os, urllib.request, urllib.parse
    creds = dict(os.environ)
    for path in ("/tmp/env.local", "/tmp/infra.env", "/app/.battery/env.local"):
        try:
            for line in open(path):
                if "=" in line:
                    k, v = line.split("=", 1)
                    creds.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass
    sid, _, tool = capability.partition(".")
    ep = {
        "clara": ("controllership-finance-api", "mcp-controllership-finance"),
        "caio": ("commercial-api", "mcp-commercial"),
        "eva": ("engineering-api", "mcp-engineering"),
        "teo": ("transformometro-api", "mcp-transformometro"),
    }[sid]
    f = urllib.parse.urlencode({
        "grant_type": "password", "client_id": "delpi-central",
        "username": creds["DEV_PORTAL_USERNAME"],
        "password": creds["DEV_PORTAL_PASSWORD"], "scope": "openid",
    }).encode()
    subj = json.loads(urllib.request.urlopen(
        urllib.request.Request(
            "http://delpi-gateway/auth/realms/delpi/protocol/openid-connect/token",
            data=f, headers={"Host": "localhost"}), timeout=15).read())["access_token"]
    f2 = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "client_id": "delia-api",
        "client_secret": creds["DELIA_EXCHANGE_CLIENT_SECRET"],
        "subject_token": subj,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "audience": ep[1],
        "scope": "openid profile email mcp:tools",
    }).encode()
    issuer = (creds.get("KEYCLOAK_ISSUER") or "").strip()
    host_hdr = (
        creds.get("DELIA_EXCHANGE_HOST_HEADER")
        or urllib.parse.urlsplit(issuer).netloc
        or ""
    ).strip()
    token_url = creds.get(
        "S2S_TOKEN_URL",
        "http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/token",
    )
    tok = json.loads(urllib.request.urlopen(
        urllib.request.Request(
            token_url, data=f2,
            headers={"Host": host_hdr} if host_hdr else None),
        timeout=15).read())["access_token"]
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05",
                                  "capabilities": {},
                                  "clientInfo": {"name": "b", "version": "0"}}}).encode()
    hdr = {"Authorization": "Bearer " + tok, "Content-Type": "application/json",
           "Accept": "application/json, text/event-stream", "Host": "localhost:8000"}
    sid_hdr = urllib.request.urlopen(urllib.request.Request(
        f"http://{ep[0]}:8000/mcp", data=init, headers=hdr), timeout=15).headers.get("mcp-session-id") or ""
    hdr["mcp-session-id"] = sid_hdr
    urllib.request.urlopen(urllib.request.Request(
        f"http://{ep[0]}:8000/mcp", data=json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}).encode(),
        headers=hdr), timeout=10)
    r = urllib.request.Request(f"http://{ep[0]}:8000/mcp", data=json.dumps(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}).encode(), headers=hdr)
    body = urllib.request.urlopen(r, timeout=15).read().decode()
    payloads = []
    stripped = body.strip()
    if stripped.startswith("{"):
        payloads.append(json.loads(stripped))
    for line in body.splitlines():
        if line.startswith("data:"):
            payloads.append(json.loads(line[5:].strip()))
    for data in payloads:
        names = [t.get("name") for t in data.get("result", {}).get("tools", [])]
        for t in data.get("result", {}).get("tools", []):
            n = t.get("name") or ""
            if n == tool or n.endswith("." + tool) or n.endswith("_" + tool):
                return t.get("inputSchema", {})
        if names:
            print(f"tool {tool} not found; advertised: {names}")
    return {}


def _model_from_schema(schema: dict):
    """Build a dynamic pydantic model from the live JSON Schema —
    types, enums (Literal) and required honored verbatim."""
    from typing import Literal, Optional
    from pydantic import Field, create_model
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    fields = {}
    for name, spec in props.items():
        enum = spec.get("enum") or spec.get("const") and [spec["const"]]
        if enum:
            ftype = Literal[tuple(enum)]  # type: ignore[valid-type]
        else:
            ftype = {"string": str, "integer": int, "number": float,
                     "boolean": bool, "object": dict,
                     "array": list}.get(spec.get("type"), str)
        default = ... if name in required else None
        if name not in required:
            ftype = Optional[ftype]  # type: ignore[assignment]
        fields[name] = (ftype, Field(default=default))
    return create_model("Args", **fields)


def bench_pydantic(schema: dict, question: str) -> dict:
    """B: pydantic-ai structured output vs the SAME local model."""
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
    import os
    model = OpenAIChatModel(
        _runtime_model_identity()[1],
        provider=OpenAIProvider(
            base_url=os.environ.get("DELIA_LLM_BASE_URL", "http://ollama:11434/v1")),
    )
    out_model = _model_from_schema(schema)
    agent = Agent(model, output_type=out_model, retries=2)
    try:
        out = agent.run_sync(
            f"Produza os argumentos da tool para a pergunta: {question}")
        return {"ok": True, "args": out.output.model_dump()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def main() -> None:
    results = []
    for scenario, cap, q in CASES:
        schema = _schema_for(cap)
        if not schema:
            results.append({"scenario": scenario, "error": "no schema"})
            continue
        b = bench_pydantic(schema, q)
        results.append({
            "scenario": scenario, "capability": cap,
            "schema_keys": list((schema.get("properties") or {}).keys()),
            "pydantic_ai": b,
        })
        print(json.dumps(results[-1], ensure_ascii=False)[:400])
    json.dump(results, open("/app/.battery/task37/s2_ab.json", "w"), indent=2)


if __name__ == "__main__":
    main()
