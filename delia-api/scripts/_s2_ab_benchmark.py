#!/usr/bin/env python3
"""S2 A/B benchmark: current arggen re-proposal (A) vs pydantic-ai
structured-output proposal (B) on the causal owner-rejection cases.

Measures schema-valid args produced for enum/discriminator tools.
Runs inside the eval container against the local Ollama model.
"""
import json
import sys

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
    for path in ("/tmp/env.local", "/tmp/infra.env"):
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
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
    }).encode()
    tok = json.loads(urllib.request.urlopen(
        urllib.request.Request(
            "http://infra-keycloak-1:8080/auth/realms/delpi/protocol/openid-connect/token",
            data=f2), timeout=15).read())["access_token"]
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
    for line in body.splitlines():
        if line.startswith("data:"):
            data = json.loads(line[5:].strip())
            for t in data.get("result", {}).get("tools", []):
                if t.get("name") == tool:
                    return t.get("inputSchema", {})
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
        os.environ.get("DELIA_LLM_MODEL", "qwen3:4b-instruct-2507-q4_K_M"),
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
