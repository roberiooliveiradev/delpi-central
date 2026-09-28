#!/usr/bin/env bash
# IDENTITY-002 — export GLPI user inventory to JSON (READ-ONLY).
# Runs on the production host; queries glpi DB inside inventario-ti-db-1.
# Output JSON feeds repair_glpi_user_names.py --glpi-inventory-json.
#
#   bash export_glpi_inventory.sh > /tmp/glpi_inventory.json
set -euo pipefail

GLPI_CONTAINER="${GLPI_CONTAINER:-inventario-ti-glpi-1}"
DB_CONTAINER="${DB_CONTAINER:-inventario-ti-db-1}"
DB_NAME="${GLPI_DB_NAME:-glpi}"

DB_PW="$(docker exec "$GLPI_CONTAINER" printenv GLPI_DB_PASSWORD)"

mysql_q() {
    docker exec "$DB_CONTAINER" mysql --default-character-set=utf8mb4 -uglpi -p"$DB_PW" "$DB_NAME" -N -e "$1" 2>/dev/null
}

users_tsv="$(mysql_q "SELECT id,name,firstname,realname,is_active,authtype FROM glpi_users")"
entities_tsv="$(mysql_q "SELECT users_id,entities_id FROM glpi_profiles_users")"
emails_tsv="$(mysql_q "SELECT users_id,email FROM glpi_useremails")"

USERS_TSV="$users_tsv" ENTITIES_TSV="$entities_tsv" EMAILS_TSV="$emails_tsv" python3 - <<'PY'
import json, os

def rows(env):
    out = []
    for line in os.environ.get(env, "").splitlines():
        parts = line.split("\t")
        if parts and parts[0]:
            out.append(parts)
    return out

users = [
    {
        "id": int(r[0]),
        "name": r[1] if r[1] != "NULL" else "",
        "firstname": r[2] if r[2] != "NULL" else "",
        "realname": r[3] if r[3] != "NULL" else "",
        "is_active": int(r[4]) if r[4].isdigit() else 0,
        "authtype": int(r[5]) if r[5].lstrip("-").isdigit() else 0,
    }
    for r in rows("USERS_TSV")
]

entities = {}
for r in rows("ENTITIES_TSV"):
    entities.setdefault(r[0], set()).add(int(r[1]))
entities = {k: sorted(v) for k, v in entities.items()}

emails = {}
for r in rows("EMAILS_TSV"):
    if len(r) > 1 and r[1]:
        emails.setdefault(r[0], set()).add(r[1])
emails = {k: sorted(v) for k, v in emails.items()}

print(json.dumps({"users": users, "entities": entities, "emails": emails}, indent=1))
PY
