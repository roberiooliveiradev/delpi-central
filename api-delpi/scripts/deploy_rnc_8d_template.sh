#!/usr/bin/env bash
# Copia template Excel 8D WEG (WFR-20997) para o path do catálogo de export.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${ROOT}/app/content/templates/quality/weg_wfr20997_template.xlsx"
SOURCE="${RNC_8D_TEMPLATE_SOURCE:-}"

if [ -z "$SOURCE" ]; then
  for candidate in \
    "${ROOT}/../api-pac-quality/docs/RNC 14297268 (1).xlsx" \
    "${ROOT}/../../api-pac-quality/docs/RNC 14297268 (1).xlsx" \
    "/home/analistaptd/projetos/api-pac-quality/docs/RNC 14297268 (1).xlsx" \
    "/mnt/c/Users/analistaptd/Downloads/8D Fornecedores - WFR-20997-.xlsx"
  do
    if [ -f "$candidate" ]; then
      SOURCE="$candidate"
      break
    fi
  done
fi

if [ -z "$SOURCE" ] || [ ! -f "$SOURCE" ]; then
  echo "Template 8D WEG não encontrado. Defina RNC_8D_TEMPLATE_SOURCE=/caminho/WEG-8D.xlsx" >&2
  exit 1
fi

mkdir -p "$(dirname "$TARGET")"
cp "$SOURCE" "$TARGET"
echo "[OK] Template WEG copiado: $SOURCE -> $TARGET"
