#!/usr/bin/env bash
# Recarrega o delpi-gateway após (re)criar um serviço usado em `proxy_pass` estático
# — usado por up-*-sequential.sh.
#
# Nginx resolve esses hostnames só no start/reload; `up -d --no-deps <svc>` recria o
# container com IP novo e o gateway segue no IP antigo (502) até recarregar.
# A lista de serviços vem do próprio nginx conf: não manter cópia aqui.

GATEWAY_CONTAINER="${GATEWAY_CONTAINER:-delpi-gateway}"

gateway_static_upstream_services() {
  local conf="$1"
  grep -E '^[[:space:]]*proxy_pass[[:space:]]+http://[A-Za-z0-9_.-]+' "$conf" \
    | sed -E 's#^[[:space:]]*proxy_pass[[:space:]]+http://([A-Za-z0-9_.-]+).*#\1#' \
    | sort -u
}

gateway_is_static_upstream() {
  local svc="$1"
  shift
  local static
  for static in "$@"; do
    [[ "$svc" == "$static" ]] && return 0
  done
  return 1
}

gateway_is_running() {
  [[ "$(docker inspect -f '{{.State.Running}}' "$GATEWAY_CONTAINER" 2>/dev/null)" == "true" ]]
}

# Uso: gateway_reload_for_service <svc> <dry_run> <static_services...>
gateway_reload_for_service() {
  local svc="$1" dry_run="$2"
  shift 2
  gateway_is_static_upstream "$svc" "$@" || return 0

  echo "  Gateway: $svc é upstream estático — nginx -t + reload em $GATEWAY_CONTAINER"
  if [[ "$dry_run" == true ]]; then
    echo "  [dry-run] docker exec $GATEWAY_CONTAINER nginx -t -q"
    echo "  [dry-run] docker exec $GATEWAY_CONTAINER nginx -s reload"
    return 0
  fi
  if ! gateway_is_running; then
    echo "  Gateway: $GATEWAY_CONTAINER não está rodando — nada a recarregar."
    return 0
  fi
  if ! docker exec "$GATEWAY_CONTAINER" nginx -t -q; then
    echo "  Gateway: nginx -t falhou (upstream sem DNS?) — reload não aplicado; gateway segue com IPs antigos." >&2
    return 1
  fi
  docker exec "$GATEWAY_CONTAINER" nginx -s reload
}

# Roda o healthcheck do gateway com retry (upstream recém-criado pode ainda estar subindo).
# Uso: gateway_verify_upstreams <dry_run> [tentativas] [intervalo_s]
gateway_verify_upstreams() {
  local dry_run="$1" attempts="${2:-12}" interval="${3:-10}"
  local check=/usr/local/bin/gateway-healthcheck.sh
  if [[ "$dry_run" == true ]]; then
    echo "  [dry-run] docker exec $GATEWAY_CONTAINER $check"
    return 0
  fi
  gateway_is_running || return 0
  if ! docker exec "$GATEWAY_CONTAINER" test -x "$check"; then
    echo "  Gateway: imagem sem $check — rebuild do gateway para habilitar a verificação."
    return 0
  fi
  local i
  for ((i = 1; i <= attempts; i++)); do
    if docker exec "$GATEWAY_CONTAINER" "$check"; then
      echo "  Gateway: upstreams estáticos OK."
      return 0
    fi
    sleep "$interval"
  done
  echo "  Gateway: upstreams estáticos falhando após reload — ver: docker logs --tail 50 $GATEWAY_CONTAINER" >&2
  return 1
}
