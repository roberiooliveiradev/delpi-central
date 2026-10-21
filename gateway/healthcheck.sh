#!/bin/sh
# Healthcheck do delpi-gateway — falha quando um upstream de `proxy_pass` estático
# não responde pelo próprio nginx. Esses hostnames são resolvidos só no start/reload;
# após recreate do container o IP muda e o gateway devolve 502 até recarregar.
#
# Um path por hostname estático de gateway/nginx.conf basta (todos os proxy_pass do
# mesmo host compartilham o IP resolvido no reload).
set -eu

host="${GATEWAY_HEALTHCHECK_HOST:-minhadelpi.com.br}"
paths="${GATEWAY_HEALTHCHECK_PATHS:-/ /core-api/health /apps/api-delpi/health /auth/realms/master}"
timeout_s="${GATEWAY_HEALTHCHECK_TIMEOUT_S:-5}"

for path in $paths; do
  body_file="$(mktemp)"
  if ! wget -q -O "$body_file" -T "$timeout_s" --header "Host: $host" "http://127.0.0.1$path"; then
    rm -f "$body_file"
    echo "gateway healthcheck: falha em $path" >&2
    exit 1
  fi
  # /health 200 não basta: o IP estático do Nginx pode ter sido reaproveitado
  # por outra API FastAPI que também responde /health. A api-delpi publica
  # exatamente {"status":"online"}, sem campo service.
  if [ "$path" = "/apps/api-delpi/health" ]; then
    if ! grep -q '"status":"online"' "$body_file" || grep -q '"service"' "$body_file"; then
      rm -f "$body_file"
      echo "gateway healthcheck: /apps/api-delpi/health não é a api-delpi" >&2
      exit 1
    fi
  fi
  rm -f "$body_file"
done
