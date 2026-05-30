#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN="$ROOT/plugins/auditoria-5s"

cd "$PLUGIN"
npm ci
npm run ci

echo "[OK] build-auditoria-5s"
