#!/usr/bin/env python3
"""Probe authenticated tools/list for each new MCP (Task 28 diagnostic)."""
import json
import sys
import urllib.request
import urllib.parse

CANDS = {
    "caio": ("http://commercial-api:8000/mcp", "mcp-commercial"),
    "clara": ("http://controllership-finance-api:8000/mcp", "mcp-controllership-finance"),
    "suri": ("http://supplies-mcp:8000/mcp", "mcp-supplies"),
    "eva": ("http://engineering-api:8000/mcp", "mcp-engineering"),
    "davi": ("http://api-delpi:8000/mcp", "mcp-api-delpi"),
}

import os
creds = dict(os.environ)
for path in ("/tmp/env.local", "/tmp/infra.env"):
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


# mint subject token (same as eval)
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

target = sys.argv[1] if len(sys.argv) > 1 else "caio"
endpoint, audience = CANDS[target]

xfields = {
    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
    "client_id": "delia-api",
    "client_secret": creds["DELIA_EXCHANGE_CLIENT_SECRET"],
    "subject_token": subject,
    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
    "audience": audience,
    "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
}
try:
    r = post(
        "http://infra-keycloak-1:8080/auth/realms/delpi/protocol/openid-connect/token",
        xfields,
    )
    tok = json.loads(r.read())["access_token"]
    print("EXCHANGE_OK", target)
except urllib.error.HTTPError as e:
    print("EXCHANGE_FAIL", target, e.code, e.read()[:250])
    sys.exit(0)

body = json.dumps(
    {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
).encode()
req = urllib.request.Request(
    endpoint,
    data=body,
    headers={
        "Authorization": "Bearer " + tok,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8000",
    },
)
try:
    resp = urllib.request.urlopen(req, timeout=20)
    raw = resp.read().decode()
    if raw.startswith("data:"):
        raw = raw[5:].strip()
        if raw.startswith("data:"):
            raw = raw[5:].strip()
    data = json.loads(raw)
    tools = data.get("result", {}).get("tools") or data.get("tools") or []
    names = [t.get("name") for t in tools]
    print("TOOLS", target, resp.status, len(names), names[:12])
except urllib.error.HTTPError as e:
    print("TOOLS_FAIL", target, e.code, e.read()[:250])
