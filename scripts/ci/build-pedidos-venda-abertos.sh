#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN="$ROOT/plugins/pedidos-venda-abertos"

cd "$PLUGIN"
npm ci
npm run ci

echo "[OK] build-pedidos-venda-abertos"
