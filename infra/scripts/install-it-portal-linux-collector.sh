#!/usr/bin/env bash
# Facade canônica — delega ao instalador versionado do coletor Linux (E4.S1).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec "${ROOT_DIR}/it-portal-api/collectors/linux_host/deploy/install-it-portal-linux-collector.sh" "$@"
