#!/usr/bin/env python3
"""S2 probe: authenticated tools/list + inputSchema discriminator dump per MCP owner.

Usage: python3 scripts/_s2_schema_probe.py [owner ...]
Prints, per owner, each tool name and the schema of its discriminator-ish
properties so we can verify owner-declared closed vocabularies (Literal enum).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

CANDS = {
    "caio": ("http://commercial-api:8000/mcp", "mcp-commercial"),
    "clara": ("http://controllership-finance-api:8000/mcp", "mcp-controllership-finance"),
    "suri": ("http://supplies-mcp:8000/mcp", "mcp-supplies"),
    "eva": ("http://engineering-api:8000/mcp", "mcp-engineering"),
    "teo": ("http://transformometro-api:8000/mcp", "mcp-transformometro"),
    "davi": ("http://api-delpi:8000/mcp", "mcp-api-delpi"),
}

DISCRIMINATOR_HINTS = ("topic", "analysis_type", "analysis", "mode", "kind", "view", "report")

creds = dict(os.environ)
for path in ("/tmp/env.local", "/tmp/infra.env", "/app/.battery/env.local"):
    try:
        for line in open(path):
            if "=" in line:
                k, v = line.split("=", 1)
                creds.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def post(url, fields, headers=None, timeout=15):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers=headers or {})
    return urllib.request.urlopen(req, timeout=timeout)


def _exchange_host_header():
    """Same canonical rule as Settings.exchange_host_header: issuer
    Host header so Keycloak derives `iss` consistently with the public
    issuer of the subject token."""
    issuer = (creds.get("KEYCLOAK_ISSUER") or "").strip()
    return (
        creds.get("DELIA_EXCHANGE_HOST_HEADER")
        or urllib.parse.urlsplit(issuer).netloc
        or ""
    ).strip()


fields = {
    "grant_type": "password",
    "client_id": "delpi-central",
    "username": creds["DEV_PORTAL_USERNAME"],
    "password": creds["DEV_PORTAL_PASSWORD"],
    "scope": "openid",
}
req = urllib.request.Request(
    "http://delpi-gateway/auth/realms/delpi/protocol/openid-connect/token",
    data=urllib.parse.urlencode(fields).encode(),
    headers={"Host": "localhost"},
)
subject = json.loads(urllib.request.urlopen(req, timeout=15).read())["access_token"]
print("SUBJECT_OK")


def prop_summary(schema):
    """Compact discriminator view: enum/const/anyOf-literals if present."""
    if not isinstance(schema, dict):
        return schema
    out = {}
    for key in ("type", "enum", "const", "default"):
        if key in schema:
            out[key] = schema[key]
    for comb in ("anyOf", "oneOf", "allOf"):
        if comb in schema:
            out[comb] = [prop_summary(s) for s in schema[comb]]
    if "description" in schema:
        out["description"] = schema["description"][:160]
    return out


targets = sys.argv[1:] or list(CANDS)
for target in targets:
    endpoint, audience = CANDS[target]
    xfields = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "client_id": "delia-api",
        "client_secret": creds["DELIA_EXCHANGE_CLIENT_SECRET"],
        "subject_token": subject,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "audience": audience,
        "scope": "openid profile email mcp:tools",
    }
    token_url = creds.get(
        "S2S_TOKEN_URL",
        "http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/token",
    )
    host_header = _exchange_host_header()
    try:
        r = post(
            token_url,
            xfields,
            headers={"Host": host_header} if host_header else None,
        )
        tok = json.loads(r.read())["access_token"]
        print("EXCHANGE_OK", target)
    except urllib.error.HTTPError as e:
        print("EXCHANGE_FAIL", target, e.code, e.read()[:250])
        continue

    base_headers = {
        "Authorization": "Bearer " + tok,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8000",
    }

    def rpc(method, params, session_id=None, extra_id=1):
        headers = dict(base_headers)
        if session_id:
            headers["mcp-session-id"] = session_id
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(
                {"jsonrpc": "2.0", "id": extra_id, "method": method,
                 "params": params}
            ).encode(),
            headers=headers,
        )
        resp = urllib.request.urlopen(req, timeout=20)
        return resp, resp.read().decode()

    def parse_payload(raw):
        # SSE frames: take the last `data:` JSON object.
        if raw.startswith("data:") or "event:" in raw:
            for line in reversed(raw.splitlines()):
                if line.startswith("data:"):
                    return json.loads(line[5:].strip())
        raw = raw.strip()
        if raw.startswith("data:"):
            raw = raw[5:].strip()
        return json.loads(raw)

    def notify(method, session_id):
        headers = dict(base_headers)
        headers["mcp-session-id"] = session_id
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(
                {"jsonrpc": "2.0", "method": method, "params": {}}
            ).encode(),
            headers=headers,
        )
        urllib.request.urlopen(req, timeout=20).read()

    session_id = None
    try:
        resp, raw = rpc("tools/list", {})
        data = parse_payload(raw)
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        if e.code != 400 or "session" not in body_text.lower():
            print("TOOLS_FAIL", target, e.code, body_text[:250])
            continue
        # Stateful transport (e.g. EVA): initialize → session → tools/list.
        resp, raw = rpc(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "s2-schema-probe", "version": "0.1"},
            },
        )
        session_id = resp.headers.get("mcp-session-id")
        notify("notifications/initialized", session_id)
        resp, raw = rpc("tools/list", {}, session_id=session_id)
        data = parse_payload(raw)
    tools = data.get("result", {}).get("tools") or data.get("tools") or []

    print("TOOLS", target, resp.status, len(tools))
    for t in tools:
        name = t.get("name")
        props = (t.get("inputSchema") or {}).get("properties") or {}
        interesting = {
            k: prop_summary(v)
            for k, v in props.items()
            if any(h == k or h in k for h in DISCRIMINATOR_HINTS)
        }
        required = (t.get("inputSchema") or {}).get("required") or []
        print(
            "TOOL", target, name,
            "required=" + json.dumps(required),
            "props=" + json.dumps(sorted(props.keys())),
        )
        for k, v in interesting.items():
            print("  PROP", name, k, "=", json.dumps(v, ensure_ascii=False))
