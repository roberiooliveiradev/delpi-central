#!/usr/bin/env bash
# Production-safe DÉLIA MCP Keycloak provisioner (PROD-MCP-RUNTIME-ALIGNMENT-01).
#
# Thin production wrapper over infra/scripts/delia_mcp_keycloak_state.py —
# the single shared engine that also powers the DEV bootstrap. This wrapper
# owns only the production safety surface:
#
#   * DEFAULT MODE = --check (no argument modifies nothing);
#   * realm `delpi` and Portal client `delpi-central` must ALREADY exist —
#     the engine fails closed otherwise (they are never created here);
#   * no user creation, no password reset, no SQL/DB access, no realm or
#     volume deletion — ever;
#   * Keycloak 24 required — production runs the KC24_LEGACY strategy
#     (legacy internal->internal token exchange, Preview feature); the
#     engine fails closed on any other major version;
#   * secrets are never printed; DELIA_EXCHANGE_CLIENT_SECRET is installed
#     ONLY when --install-secret-to <gitignored-path> is passed explicitly.
#
# Usage:
#   # read-only drift report (safe, default)
#   bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --check
#
#   # bounded apply of the DÉLIA MCP IAM contract (idempotent)
#   bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --apply
#
#   # apply + install requester secret into a gitignored env file
#   bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --apply \
#       --install-secret-to /path/to/.env
#
# Required environment (read from infra/.env unless overridden):
#   KEYCLOAK_ADMIN / KEYCLOAK_ADMIN_PASSWORD  — or KC_ADMIN_TOKEN
#   KEYCLOAK_URL / KC_BASE                    — e.g. https://host/auth
#   PUBLIC_BASE_URL                           — resource audience source
#   KEYCLOAK_REALM                            — defaults to delpi
#
# Runbook: docs/12-roadmap-e-evolucao/delia/runbooks/
#   prod-mcp-runtime-alignment.md
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENGINE="$SCRIPT_DIR/delia_mcp_keycloak_state.py"

env_val() { # KEY file — tolerant to values with spaces/comments
  grep -E "^$1=" "$2" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"'\r' || true
}

# --- load config from infra/.env when present (never prints secrets) ---
ENV_FILE="$INFRA_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  : "${KEYCLOAK_ADMIN:=$(env_val KEYCLOAK_ADMIN "$ENV_FILE")}"
  : "${KEYCLOAK_ADMIN_PASSWORD:=$(env_val KEYCLOAK_ADMIN_PASSWORD "$ENV_FILE")}"
  : "${KEYCLOAK_URL:=$(env_val KEYCLOAK_URL "$ENV_FILE")}"
  : "${KC_BASE:=$(env_val KC_BASE_URL "$ENV_FILE")}"
  : "${PUBLIC_BASE_URL:=$(env_val PUBLIC_BASE_URL "$ENV_FILE")}"
  : "${KEYCLOAK_REALM:=$(env_val KEYCLOAK_REALM "$ENV_FILE")}"
  export KEYCLOAK_ADMIN KEYCLOAK_ADMIN_PASSWORD KEYCLOAK_URL KC_BASE \
         PUBLIC_BASE_URL KEYCLOAK_REALM
fi

# --- production safety rails ---
if [ -n "${KC_BASE:-}" ]; then
  case "$KC_BASE" in
    https://*) ;;
    *)
      echo "[ERRO] produção exige KC_BASE https:// (got: ${KC_BASE%%/*}…)" >&2
      exit 1 ;;
  esac
fi
if [ -z "${PUBLIC_BASE_URL:-}" ]; then
  echo "[ERRO] PUBLIC_BASE_URL ausente — resource audiences são derivadas" >&2
  echo "       dela, nunca hardcoded. Configure-a no ambiente." >&2
  exit 1
fi

# No explicit mode argument => --check (read-only). Anything else is
# forwarded verbatim to the shared engine.
MODE="--check"
PASS=()
for arg in "$@"; do
  case "$arg" in
    --apply|--check) MODE="$arg" ;;
    *) PASS+=("$arg") ;;
  esac
done

echo "[kc-prod-provision] mode=$MODE realm=${KEYCLOAK_REALM:-delpi} base=${KC_BASE:-$KEYCLOAK_URL} strategy=KC24_LEGACY"
exec python3 "$ENGINE" "$MODE" --strategy KC24_LEGACY \
  ${PASS[@]+"${PASS[@]}"}
