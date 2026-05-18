#!/usr/bin/env bash
# Compara dois arquivos .env sem expor segredos.
# Uso: ./scripts/compare-env-safe.sh <arquivo_a> <arquivo_b> [rótulo_a] [rótulo_b]
set -euo pipefail

FILE_A="${1:?Informe o primeiro arquivo .env}"
FILE_B="${2:?Informe o segundo arquivo .env}"
LABEL_A="${3:-A}"
LABEL_B="${4:-B}"

if [[ ! -f "$FILE_A" ]]; then
  echo "Arquivo não encontrado: $FILE_A" >&2
  exit 1
fi
if [[ ! -f "$FILE_B" ]]; then
  echo "Arquivo não encontrado: $FILE_B" >&2
  exit 1
fi

is_secret_key() {
  local key="$1"
  [[ "$key" =~ (PASSWORD|SECRET|TOKEN|PRIVATE|CREDENTIAL|API_KEY|JWT) ]]
}

mask_value() {
  local key="$1"
  local value="$2"
  if is_secret_key "$key"; then
    if [[ -z "$value" ]]; then
      printf '(vazio)'
    else
      printf '*** [%s caracteres]' "${#value}"
    fi
  elif [[ ${#value} -gt 80 ]]; then
    printf '%s…' "${value:0:77}"
  else
    printf '%s' "$value"
  fi
}

# Extrai KEY=value (ignora comentários e linhas vazias)
parse_keys() {
  local file="$1"
  grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$file" 2>/dev/null \
    | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' \
    | grep -v '^#'
}

tmp_a="$(mktemp)"
tmp_b="$(mktemp)"
trap 'rm -f "$tmp_a" "$tmp_b"' EXIT

parse_keys "$FILE_A" >"$tmp_a"
parse_keys "$FILE_B" >"$tmp_b"

get_value() {
  local file_tmp="$1"
  local key="$2"
  grep -m1 "^${key}=" "$file_tmp" 2>/dev/null | cut -d= -f2- | sed 's/^["'\'']//; s/["'\'']$//'
}

keys_a="$(cut -d= -f1 "$tmp_a" | sort -u)"
keys_b="$(cut -d= -f1 "$tmp_b" | sort -u)"

only_a="$(comm -23 <(echo "$keys_a") <(echo "$keys_b"))"
only_b="$(comm -13 <(echo "$keys_a") <(echo "$keys_b"))"
both="$(comm -12 <(echo "$keys_a") <(echo "$keys_b"))"

echo "=============================================="
echo "Comparação segura de .env"
echo "  $LABEL_A: $FILE_A"
echo "  $LABEL_B: $FILE_B"
echo "=============================================="
echo

echo "--- Só em $LABEL_A ($(echo "$only_a" | grep -c . || true) chaves) ---"
if [[ -z "${only_a// }" ]]; then
  echo "(nenhuma)"
else
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    val="$(get_value "$tmp_a" "$key")"
    printf '  %-40s = %s\n' "$key" "$(mask_value "$key" "$val")"
  done <<<"$only_a"
fi
echo

echo "--- Só em $LABEL_B ($(echo "$only_b" | grep -c . || true) chaves) ---"
if [[ -z "${only_b// }" ]]; then
  echo "(nenhuma)"
else
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    val="$(get_value "$tmp_b" "$key")"
    printf '  %-40s = %s\n' "$key" "$(mask_value "$key" "$val")"
  done <<<"$only_b"
fi
echo

echo "--- Em ambos: valores diferentes ---"
diff_count=0
same_count=0
while IFS= read -r key; do
  [[ -z "$key" ]] && continue
  va="$(get_value "$tmp_a" "$key")"
  vb="$(get_value "$tmp_b" "$key")"
  if [[ "$va" == "$vb" ]]; then
    same_count=$((same_count + 1))
  else
    diff_count=$((diff_count + 1))
    printf '  %-40s\n' "$key"
    printf '    %-38s %s\n' "$LABEL_A:" "$(mask_value "$key" "$va")"
    printf '    %-38s %s\n' "$LABEL_B:" "$(mask_value "$key" "$vb")"
  fi
done <<<"$both"

if [[ "$diff_count" -eq 0 ]]; then
  echo "  (nenhuma diferença nos valores)"
fi
echo

echo "--- Resumo ---"
echo "  Chaves só em $LABEL_A: $(echo "$only_a" | grep -c . 2>/dev/null || echo 0)"
echo "  Chaves só em $LABEL_B: $(echo "$only_b" | grep -c . 2>/dev/null || echo 0)"
echo "  Chaves em ambos (iguais): $same_count"
echo "  Chaves em ambos (diferentes): $diff_count"
echo

echo "--- Qualidade / api-delpi (checklist rápido) ---"
quality_keys=(
  TOTVS_DB_HOST TOTVS_DB_PORT TOTVS_DB_USER TOTVS_DB_PASSWORD TOTVS_DB_DATABASE
  DB_HOST DB_PORT DB_USER DB_PASSWORD DB_DATABASE
  QUALITY_SHEET_ID QUALITY_KAIZEN_SHEET_GID QUALITY_AUDIT_5S_SHEET_GID
  GOOGLE_SHEETS_TIMEOUT
  KEYCLOAK_JWKS_URL KEYCLOAK_ISSUER KEYCLOAK_AUDIENCE
  PLUGINS_DB_HOST PLUGINS_DB_NAME PLUGINS_DB_USER PLUGINS_DB_PASSWORD
)
for key in "${quality_keys[@]}"; do
  in_a="—" in_b="—"
  grep -q "^${key}=" "$tmp_a" 2>/dev/null && in_a="sim"
  grep -q "^${key}=" "$tmp_b" 2>/dev/null && in_b="sim"
  printf '  %-32s  %-6s  %-6s\n' "$key" "$in_a" "$in_b"
done
