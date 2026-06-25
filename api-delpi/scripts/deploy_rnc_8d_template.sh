#!/usr/bin/env bash
# Copia o template Excel 8D para o path esperado pelo export (fora do git).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${ROOT}/app/content/templates/quality/rnc_8d_template.xlsx"
SOURCE="${RNC_8D_TEMPLATE_SOURCE:-}"

if [ -z "$SOURCE" ]; then
  for candidate in \
    "${ROOT}/../api-pac-quality/docs/RNC 14297268 (1).xlsx" \
    "${ROOT}/../../api-pac-quality/docs/RNC 14297268 (1).xlsx" \
    "/home/analistaptd/projetos/api-pac-quality/docs/RNC 14297268 (1).xlsx"
  do
    if [ -f "$candidate" ]; then
      SOURCE="$candidate"
      break
    fi
  done
fi

if [ -z "$SOURCE" ] || [ ! -f "$SOURCE" ]; then
  echo "Template 8D não encontrado. Defina RNC_8D_TEMPLATE_SOURCE=/caminho/RNC.xlsx" >&2
  exit 1
fi

mkdir -p "$(dirname "$TARGET")"
cp "$SOURCE" "$TARGET"
echo "[OK] Template 8D copiado: $SOURCE -> $TARGET"
