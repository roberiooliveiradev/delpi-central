#!/usr/bin/env bash
# Smoke / reconciliação pós-backfill — schema commercial vs pedidos_venda_abertos.
# Uso (no host com docker):
#   ./commercial-api/scripts/reconcile_portfolio_counts.sh
set -euo pipefail

CONTAINER="${PLUGINS_DB_CONTAINER:-delpi-postgres-plugins}"
DB_USER="${PLUGINS_DB_USER:-plugins_user}"
DB_NAME="${PLUGINS_DB_NAME:-plugins_hub}"

echo "[reconcile] Contagens legado vs commercial (container=$CONTAINER)"

docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<'SQL'
SELECT 'legacy.sellers' AS metric, COUNT(*)::text AS value FROM pedidos_venda_abertos.sellers
UNION ALL
SELECT 'commercial.seller_portfolios', COUNT(*)::text FROM commercial.seller_portfolios
UNION ALL
SELECT 'legacy.seller_customers', COUNT(*)::text FROM pedidos_venda_abertos.seller_customers
UNION ALL
SELECT 'commercial.seller_customers', COUNT(*)::text FROM commercial.seller_customers
UNION ALL
SELECT 'legacy.customer_avatars', COUNT(*)::text FROM pedidos_venda_abertos.customer_avatars
UNION ALL
SELECT 'commercial.customer_avatars', COUNT(*)::text FROM commercial.customer_avatars
ORDER BY 1;
SQL

echo "[OK] Compare as linhas: após backfill, pares legacy/commercial devem coincidir."
echo "[OK] Em seguida reinicie commercial-api com COMMERCIAL_PORTFOLIO_SOURCE=commercial."
