#!/usr/bin/env bash
# Gera CA local + certificado de servidor para HTTPS interno da homologação.
# Não inicia containers, não publica portas, não altera produção.
#
# Uso (computador local ou VM HML):
#   ./infra/scripts/hml-tls-prepare.sh
#   ./infra/scripts/hml-tls-prepare.sh --host 192.168.1.237 --days 825
#
# Saída: infra/hml-certs/ (gitignored, exceto README/.gitignore)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="${INFRA_DIR}/hml-certs"
HOST="192.168.1.237"
DAYS=825

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:?}"; shift 2 ;;
    --days) DAYS="${2:?}"; shift 2 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      echo "Opção desconhecida: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v openssl >/dev/null 2>&1; then
  echo "[ERRO] openssl não encontrado." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

CA_KEY="$OUT_DIR/hml-local-ca.key"
CA_CRT="$OUT_DIR/hml-local-ca.crt"
SRV_KEY="$OUT_DIR/hml-gateway.key"
SRV_CSR="$OUT_DIR/hml-gateway.csr"
SRV_CRT="$OUT_DIR/hml-gateway.crt"
EXT_FILE="$OUT_DIR/hml-gateway.ext"

if [[ -f "$CA_KEY" || -f "$SRV_KEY" ]]; then
  echo "[ERRO] Já existem chaves em $OUT_DIR. Remova manualmente se quiser regenerar." >&2
  exit 1
fi

openssl genrsa -out "$CA_KEY" 4096
openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days "$DAYS" \
  -subj "/CN=Delpi HML Local CA/O=Delpi Homologacao/C=BR" \
  -out "$CA_CRT"

openssl genrsa -out "$SRV_KEY" 2048
openssl req -new -key "$SRV_KEY" \
  -subj "/CN=${HOST}/O=Delpi Homologacao/C=BR" \
  -out "$SRV_CSR"

cat >"$EXT_FILE" <<EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=IP:${HOST},DNS:localhost
EOF

openssl x509 -req -in "$SRV_CSR" -CA "$CA_CRT" -CAkey "$CA_KEY" -CAcreateserial \
  -out "$SRV_CRT" -days "$DAYS" -sha256 -extfile "$EXT_FILE"

chmod 600 "$CA_KEY" "$SRV_KEY"
chmod 644 "$CA_CRT" "$SRV_CRT"
rm -f "$SRV_CSR" "$EXT_FILE" "$OUT_DIR/hml-local-ca.srl"

echo "HML_TLS_PREPARE=PASS"
echo "ca_cert=$CA_CRT"
echo "server_cert=$SRV_CRT"
echo "server_key=$SRV_KEY"
echo "san=IP:${HOST},DNS:localhost"
echo "próximo: autorizar ativação HTTPS HML (porta exclusiva, rebuild Portal/Vite, bootstrap KC)."
echo "Não versionar as chaves. Instalar a CA nos PCs de teste antes do go-live TLS."
