#!/usr/bin/env bash
# Aplica settings/limiter de dev no container SearXNG (JSON + limiter off).
# Necessário quando a imagem expande settings.yml sem search.formats.json → HTTP 403 na API.
set -euo pipefail

CONTAINER="${SEARXNG_CONTAINER:-delpi-searxng}"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "Container $CONTAINER não está em execução." >&2
  exit 1
fi

docker exec "$CONTAINER" sh -c 'cat > /etc/searxng/settings.yml << "EOF"
use_default_settings: true

general:
  debug: false
  instance_name: "DELPI SearXNG"

search:
  safe_search: 0
  autocomplete: ""
  default_lang: "pt-BR"
  formats:
    - html
    - json

server:
  bind_address: "0.0.0.0"
  port: 8080
  secret_key: "delpi-dev-searxng-secret-change-me"
  limiter: false
  image_proxy: false
EOF
cat > /etc/searxng/limiter.toml << "EOF"
[botdetection]
ipv4_prefix = 32
ipv6_prefix = 48

[botdetection.ip_lists]
pass_ip = ["127.0.0.0/8", "::1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

[botdetection.ip_limit]
filter_link_local = false
link_token = false
EOF'

docker restart "$CONTAINER" >/dev/null
sleep 4

code=$(curl -s -o /dev/null -w '%{http_code}' 'http://localhost:8088/search?q=weg&format=json' || true)
if [ "$code" = "200" ]; then
  echo "OK SearXNG JSON (HTTP $code)"
else
  echo "FAIL SearXNG JSON (HTTP $code) — verifique porta 8088 e logs do container" >&2
  exit 1
fi
