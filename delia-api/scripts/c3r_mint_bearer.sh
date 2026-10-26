#!/usr/bin/env bash
# Task scratch — mints a real dev-portal subject bearer for the C3R
# live probe and writes it to /tmp/eval_bearer. Secrets never leave
# the container: creds are parsed from the mounted /tmp/env.local and
# only the token path is exercised.
set -euo pipefail

USER_="$(grep -E '^DEV_PORTAL_USERNAME=' /tmp/env.local | cut -d= -f2- | tr -d '"'"'"'[:space:]')"
PASS_="$(grep -E '^DEV_PORTAL_PASSWORD=' /tmp/env.local | cut -d= -f2- | tr -d '"'"'"'[:space:]')"
if [ -z "$USER_" ] || [ -z "$PASS_" ]; then
  echo "dev portal creds missing in /tmp/env.local" >&2
  exit 1
fi

# Mint through the gateway with Host: localhost so the emitted issuer
# is http://localhost/auth/realms/delpi (front-channel issuer that the
# delegated exchange and MCP resource both expect).
USER_="$USER_" PASS_="$PASS_" python3 - <<'PY'
import json, os, sys, urllib.request, urllib.parse

fields = urllib.parse.urlencode({
    "grant_type": "password",
    "client_id": "delpi-central",
    "username": os.environ["USER_"],
    "password": os.environ["PASS_"],
    "scope": "openid",
}).encode()
req = urllib.request.Request(
    "http://delpi-gateway/auth/realms/delpi/protocol/openid-connect/token",
    data=fields,
    headers={"Host": "localhost"},
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        token = json.loads(resp.read().decode())["access_token"]
except urllib.error.HTTPError as exc:
    print(f"token grant failed: http {exc.code}", file=sys.stderr)
    print(exc.read()[:300].decode(errors="replace"), file=sys.stderr)
    sys.exit(1)
with open("/tmp/eval_bearer", "w") as fh:
    fh.write(token)
PY
echo "bearer written to /tmp/eval_bearer"
