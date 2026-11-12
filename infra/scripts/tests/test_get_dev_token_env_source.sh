#!/usr/bin/env bash
# Targeted: get-dev-token.sh / keycloak-dev-bootstrap.sh load ONLY infra/.env.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

token_script="$ROOT/infra/scripts/get-dev-token.sh"
bootstrap_script="$ROOT/infra/scripts/keycloak-dev-bootstrap.sh"

if grep -E 'source[[:space:]]+"?\$ENV_LOCAL|"\$INFRA_DIR/\.env\.local"|env_val .*env\.local' \
  "$token_script" "$bootstrap_script"; then
  echo "FAIL: legacy .env.local still loaded as configuration source"
  exit 1
fi

if ! grep -q 'source "\$ENV_FILE"' "$token_script"; then
  echo "FAIL: get-dev-token.sh must source ENV_FILE (infra/.env)"
  exit 1
fi

if ! grep -q 'canonical exclusive source infra/\.env' "$bootstrap_script"; then
  echo "FAIL: keycloak-dev-bootstrap must document exclusive .env source"
  exit 1
fi

echo "PASS: ENV_SOURCE_PRECEDENCE (.env exclusive; .env.local not loaded)"
