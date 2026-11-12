#!/usr/bin/env bash
# Homologação delpi-hml — operação controlada.
#
# Leitura/simulação: list, validate, config, simulate, status.
# Ativação autorizada:
#   - databases    → postgres-core, keycloak-db, postgres-plugins
#   - keycloak     → somente o serviço keycloak (--no-deps; DB já ativo)
#   - gateway      → somente delpi-hml-gateway (build imagem HML; --no-deps; exige certs TLS)
#   - core-api     → somente delpi-hml-core-api (build; migrations no Postgres Core HML)
#   - portal       → somente delpi-hml-portal (build Vite HML HTTPS; exige Core healthy)
#   - tls-activate → cutover HTTPS coordenado (gateway+keycloak+bootstrap+core-api+portal)
# Qualquer outro up/build/pull/down/stop continua recusado.
# Redis, API DELPI, Plugin UI e Production Control permanecem bloqueados.
#
# Uso, a partir da raiz do repositório:
#   ./infra/scripts/hml-compose.sh list
#   ./infra/scripts/hml-compose.sh validate
#   ./infra/scripts/hml-compose.sh config [--scenario databases|keycloak|gateway|core-api|portal|tls-activate|...]
#   ./infra/scripts/hml-compose.sh simulate [--scenario ...] [--services a,b]
#   ./infra/scripts/hml-compose.sh status
#   ./infra/scripts/hml-compose.sh up --scenario databases
#   ./infra/scripts/hml-compose.sh up --scenario keycloak
#   ./infra/scripts/hml-compose.sh up --scenario gateway
#   ./infra/scripts/hml-compose.sh up --scenario core-api
#   ./infra/scripts/hml-compose.sh up --scenario portal
#   ./infra/scripts/hml-compose.sh up --scenario tls-activate
#   ./infra/scripts/hml-compose.sh up --scenario redis
#   ./infra/scripts/hml-compose.sh up --scenario api-delpi
#   ./infra/scripts/hml-compose.sh up --scenario plugin-ui
#   ./infra/scripts/hml-compose.sh up --scenario production-control-api
#   ./infra/scripts/hml-compose.sh up --scenario production-control-ui
#   ./infra/scripts/hml-compose.sh bootstrap-keycloak
#   ./infra/scripts/hml-compose.sh up|down|stop|build|pull   # demais: recusa

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$COMPOSE_DIR/.." && pwd)"
PROJECT="delpi-hml"
COMPOSE_FILE="docker-compose.hml.yml"
ENV_EXAMPLE="env.hml.example"
ENV_LOCAL=".env.hml"
ACTIVATION_STATUS="HOMOLOGATION_TLS_ACTIVATE_AUTHORIZED"
HEALTH_TIMEOUT_SEC="${DELPI_HML_HEALTH_TIMEOUT_SEC:-300}"

DATABASE_SERVICES=(
  postgres-core
  keycloak-db
  postgres-plugins
)
KEYCLOAK_SERVICES=(
  keycloak
)
GATEWAY_SERVICES=(
  gateway
)
CORE_API_SERVICES=(
  core-api
)
PORTAL_SERVICES=(
  portal
)
REDIS_SERVICES=(
  delpi-redis
)
API_DELPI_SERVICES=(
  api-delpi
)
PLUGIN_UI_SERVICES=(
  plugin-ui
)
PC_API_SERVICES=(
  production-control-api
)
PC_UI_SERVICES=(
  production-control
)
PLATFORM_SERVICES=(
  postgres-core
  keycloak-db
  postgres-plugins
  delpi-redis
  keycloak
  core-api
  api-delpi
  portal
  plugin-ui
  gateway
)
PC_SERVICES=(
  production-control
  production-control-api
)
START_ORDER=(
  postgres-core
  keycloak-db
  postgres-plugins
  delpi-redis
  keycloak
  core-api
  api-delpi
  portal
  plugin-ui
  production-control
  production-control-api
  gateway
)
AUTHORIZED_UP_SCENARIOS=(
  databases
  keycloak
  gateway
  core-api
  portal
  tls-activate
  redis
  api-delpi
  plugin-ui
  production-control-api
  production-control-ui
)
ALLOWED_HML_CONTAINERS_AFTER_GATEWAY=(
  delpi-hml-postgres-core
  delpi-hml-keycloak-db
  delpi-hml-postgres-plugins
  delpi-hml-keycloak
  delpi-hml-gateway
)
ALLOWED_HML_CONTAINERS_AFTER_CORE_API=(
  "${ALLOWED_HML_CONTAINERS_AFTER_GATEWAY[@]}"
  delpi-hml-core-api
)
ALLOWED_HML_CONTAINERS_AFTER_PORTAL=(
  "${ALLOWED_HML_CONTAINERS_AFTER_CORE_API[@]}"
  delpi-hml-portal
)
ALLOWED_HML_CONTAINERS_AFTER_REDIS=(
  "${ALLOWED_HML_CONTAINERS_AFTER_PORTAL[@]}"
  delpi-hml-redis
)
ALLOWED_HML_CONTAINERS_AFTER_API_DELPI=(
  "${ALLOWED_HML_CONTAINERS_AFTER_REDIS[@]}"
  delpi-hml-api-delpi
)
ALLOWED_HML_CONTAINERS_AFTER_PLUGIN_UI=(
  "${ALLOWED_HML_CONTAINERS_AFTER_API_DELPI[@]}"
  delpi-hml-plugin-ui
)
ALLOWED_HML_CONTAINERS_AFTER_PC_API=(
  "${ALLOWED_HML_CONTAINERS_AFTER_PLUGIN_UI[@]}"
  delpi-hml-production-control-api
)
ALLOWED_HML_CONTAINERS_AFTER_PC_UI=(
  "${ALLOWED_HML_CONTAINERS_AFTER_PC_API[@]}"
  delpi-hml-production-control
)

usage() {
  sed -n '2,20p' "$0"
}

refuse_activation() {
  local action="$1"
  echo "HOMOLOGATION_ACTIVATION_NOT_AUTHORIZED" >&2
  echo "Ação '$action' não executada fora dos profiles autorizados." >&2
  echo "Autorizados: up --scenario databases|keycloak|gateway|core-api|portal|tls-activate|redis|api-delpi|plugin-ui|production-control-api|production-control-ui | bootstrap-keycloak." >&2
  echo "Profiles amplos baseline/platform/production-control continuam bloqueados como up único." >&2
  exit 2
}

scenario_services() {
  local scenario="$1"
  case "$scenario" in
    databases) printf '%s\n' "${DATABASE_SERVICES[@]}" ;;
    keycloak) printf '%s\n' "${KEYCLOAK_SERVICES[@]}" ;;
    gateway) printf '%s\n' "${GATEWAY_SERVICES[@]}" ;;
    core-api) printf '%s\n' "${CORE_API_SERVICES[@]}" ;;
    portal) printf '%s\n' "${PORTAL_SERVICES[@]}" ;;
    tls-activate) printf '%s\n' "${GATEWAY_SERVICES[@]}" "${KEYCLOAK_SERVICES[@]}" "${CORE_API_SERVICES[@]}" "${PORTAL_SERVICES[@]}" ;;
    redis) printf '%s\n' "${REDIS_SERVICES[@]}" ;;
    api-delpi) printf '%s\n' "${API_DELPI_SERVICES[@]}" ;;
    plugin-ui) printf '%s\n' "${PLUGIN_UI_SERVICES[@]}" ;;
    production-control-api) printf '%s\n' "${PC_API_SERVICES[@]}" ;;
    production-control-ui) printf '%s\n' "${PC_UI_SERVICES[@]}" ;;
    baseline) printf '%s\n' "${PLATFORM_SERVICES[@]}" "${PC_SERVICES[@]}" ;;
    platform) printf '%s\n' "${PLATFORM_SERVICES[@]}" ;;
    production-control) printf '%s\n' "${PLATFORM_SERVICES[@]}" "${PC_SERVICES[@]}" ;;
    *)
      echo "Cenário desconhecido: $scenario" >&2
      exit 1
      ;;
  esac
}

assert_no_prod_markers_in_env() {
  local env_file="$1"
  local blob
  blob="$(grep -E '^(KEYCLOAK_ISSUER|VITE_KC_URL|VITE_KC_REDIRECT_URI|PUBLIC_BASE_URL|DELPI_HML_PUBLIC_ORIGIN|KC_HOSTNAME)=' \
    "$COMPOSE_DIR/$ENV_LOCAL" 2>/dev/null || true)"
  if grep -Eiq 'minhadelpi\.com\.br' <<<"$blob"; then
    echo "[ERRO] .env.hml referencia domínio produtivo em OIDC/URLs públicas. STOP." >&2
    exit 1
  fi
  if ! grep -Eq '^KEYCLOAK_ISSUER=https://192\.168\.1\.237:18443/auth/realms/delpi' "$COMPOSE_DIR/$ENV_LOCAL"; then
    echo "[ERRO] KEYCLOAK_ISSUER HTTPS HML esperado ausente/divergente em .env.hml. STOP." >&2
    exit 1
  fi
  if ! grep -Eq '^DELPI_HML_PUBLIC_ORIGIN=https://192\.168\.1\.237:18443$' "$COMPOSE_DIR/$ENV_LOCAL"; then
    echo "[ERRO] DELPI_HML_PUBLIC_ORIGIN HTTPS HML ausente/divergente. STOP." >&2
    exit 1
  fi
  if ! grep -Eq '^KEYCLOAK_AUDIENCE=delpi-central' "$COMPOSE_DIR/$ENV_LOCAL"; then
    echo "[ERRO] KEYCLOAK_AUDIENCE=delpi-central ausente em .env.hml. STOP." >&2
    exit 1
  fi
  if ! grep -Eq '^DB_HOST=postgres-core' "$COMPOSE_DIR/$ENV_LOCAL"; then
    echo "[ERRO] DB_HOST deve ser postgres-core (rede HML). STOP." >&2
    exit 1
  fi
}

assert_hml_tls_certs() {
  local crt="$COMPOSE_DIR/hml-certs/hml-gateway.crt"
  local key="$COMPOSE_DIR/hml-certs/hml-gateway.key"
  local ca="$COMPOSE_DIR/hml-certs/hml-local-ca.crt"
  if [[ ! -f "$crt" || ! -f "$key" ]]; then
    echo "[ERRO] certs TLS HML ausentes ($crt / $key). Rode ./infra/scripts/hml-tls-prepare.sh" >&2
    exit 1
  fi
  if [[ ! -f "$ca" ]]; then
    echo "[ERRO] CA pública HML ausente ($ca). Necessária para smoke com confiança." >&2
    exit 1
  fi
  if [[ -f "$COMPOSE_DIR/hml-certs/hml-local-ca.key" ]]; then
    # Permitido na VM durante geração; aviso operacional (não montar no gateway).
    echo "[AVISO] chave privada da CA presente em hml-certs — transferir para custódia e remover após backup." >&2
  fi
  openssl x509 -in "$crt" -noout -checkend 86400 >/dev/null 2>&1 || {
    echo "[ERRO] certificado do gateway expirado ou inválido." >&2
    exit 1
  }
  openssl x509 -in "$crt" -noout -text 2>/dev/null | grep -q 'IP Address:192.168.1.237' || {
    echo "[ERRO] SAN IP:192.168.1.237 ausente no certificado do gateway." >&2
    exit 1
  }
}

assert_hml_container_allowlist() {
  local -n allowed_ref=$1
  local name extras="" allowed ok
  while read -r name; do
    [[ -z "$name" ]] && continue
    allowed=false
    for ok in "${allowed_ref[@]}"; do
      [[ "$name" == "$ok" ]] && allowed=true
    done
    if [[ "$allowed" != true ]]; then
      extras+="$name"$'\n'
    fi
  done < <(docker ps -a --filter name=delpi-hml --format '{{.Names}}')
  if [[ -n "${extras//[[:space:]]/}" ]]; then
    echo "[ERRO] containers HML inesperados:" >&2
    printf '%s' "$extras" >&2
    exit 1
  fi
}

is_authorized_up() {
  local scenario="$1" s
  for s in "${AUTHORIZED_UP_SCENARIOS[@]}"; do
    [[ "$s" == "$scenario" ]] && return 0
  done
  return 1
}

ordered_selection() {
  local -a wanted=("$@")
  local svc want
  for svc in "${START_ORDER[@]}"; do
    for want in "${wanted[@]}"; do
      if [[ "$svc" == "$want" ]]; then
        printf '%s\n' "$svc"
      fi
    done
  done
}

assert_compose_identity() {
  local name_line
  name_line="$(grep -E '^name:[[:space:]]*' "$COMPOSE_DIR/$COMPOSE_FILE" | head -n 1)"
  if [[ "$name_line" != "name: ${PROJECT}" ]]; then
    echo "Compose de homologação sem name: ${PROJECT}. Abortado." >&2
    exit 1
  fi
}

env_file_for() {
  local mode="$1"
  if [[ "$mode" == "example" ]]; then
    printf '%s\n' "$ENV_EXAMPLE"
    return 0
  fi
  if [[ -f "$COMPOSE_DIR/$ENV_LOCAL" ]]; then
    printf '%s\n' "$ENV_LOCAL"
    return 0
  fi
  printf '%s\n' "$ENV_EXAMPLE"
}

assert_env_file_allowed() {
  local env_file="$1"
  local base
  base="$(basename "$env_file")"
  case "$base" in
    .env|.env.prod|.env.dev)
      echo "Arquivo de ambiente recusado para homologação: $base" >&2
      exit 1
      ;;
  esac
  if [[ "$env_file" == *"/.env" ]]; then
    echo "infra/.env é o ambiente de produção/dev deste checkout. Homologação usa $ENV_LOCAL." >&2
    exit 1
  fi
}

compose_base_cmd() {
  local scenario="$1"
  local env_file="$2"
  assert_compose_identity
  assert_env_file_allowed "$env_file"
  local -a cmd=(
    docker compose
    --project-name "$PROJECT"
    --project-directory "$COMPOSE_DIR"
    -f "$COMPOSE_FILE"
    --env-file "$env_file"
  )
  if [[ -n "$scenario" ]]; then
    cmd+=(--profile "$scenario")
  fi
  printf '%s\0' "${cmd[@]}"
}

compose_config() {
  local scenario="$1"
  local env_file="$2"
  local -a cmd=()
  mapfile -d '' -t cmd < <(compose_base_cmd "$scenario" "$env_file")
  cmd+=(config)
  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      "${cmd[@]}"
  )
}

wait_healthy() {
  local service="$1"
  local env_file="$2"
  local profile="${3:-databases}"
  local deadline=$((SECONDS + HEALTH_TIMEOUT_SEC))
  local status cid health
  echo "Aguardando health de $service (timeout ${HEALTH_TIMEOUT_SEC}s)..."
  while (( SECONDS < deadline )); do
    status="$(
      cd "$COMPOSE_DIR"
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile "$profile" \
        ps --status running --format '{{.Health}}' "$service" 2>/dev/null || true
    )"
    if [[ "$status" == "healthy" ]]; then
      echo "HEALTH=$service:healthy"
      return 0
    fi
    local cname="delpi-hml-${service}"
    # Compose service delpi-redis → container delpi-hml-redis (sem duplicar prefixo).
    if [[ "$service" == "delpi-redis" ]]; then
      cname="delpi-hml-redis"
    fi
    cid="$(docker ps -q --filter "name=^/${cname}$" --filter "name=${cname}" | head -n 1 || true)"
    if [[ -z "$cid" ]]; then
      cid="$(docker ps -q --filter "name=${cname}" | head -n 1 || true)"
    fi
    if [[ -n "$cid" ]]; then
      health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || true)"
      if [[ "$health" == "healthy" ]]; then
        echo "HEALTH=$service:healthy"
        return 0
      fi
      if [[ "$service" == keycloak ]]; then
        if docker exec "$cid" bash -c 'exec 3<>/dev/tcp/127.0.0.1/8080' >/dev/null 2>&1; then
          echo "HEALTH=$service:tcp8080"
          return 0
        fi
      elif [[ "$service" == gateway ]]; then
        if docker exec "$cid" wget -q -O /dev/null -T 3 http://127.0.0.1/auth/realms/master >/dev/null 2>&1; then
          echo "HEALTH=$service:auth_realm"
          return 0
        fi
      elif [[ "$service" == core-api || "$service" == api-delpi || "$service" == production-control-api ]]; then
        if docker exec "$cid" python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" >/dev/null 2>&1; then
          echo "HEALTH=$service:http_health"
          return 0
        fi
      elif [[ "$service" == portal || "$service" == plugin-ui || "$service" == production-control ]]; then
        if docker exec "$cid" wget -q -O /dev/null -T 3 http://127.0.0.1/ >/dev/null 2>&1; then
          echo "HEALTH=$service:http_root"
          return 0
        fi
      elif [[ "$service" == delpi-redis ]]; then
        if docker exec "$cid" sh -c 'redis-cli -a "$DELPI_REDIS_PASSWORD" ping' 2>/dev/null | grep -q PONG; then
          echo "HEALTH=$service:redis_pong"
          return 0
        fi
      elif [[ "$health" == "running" ]]; then
        if docker exec "$cid" pg_isready -U "$(docker exec "$cid" printenv POSTGRES_USER)" -d "$(docker exec "$cid" printenv POSTGRES_DB)" >/dev/null 2>&1; then
          echo "HEALTH=$service:pg_isready"
          return 0
        fi
      fi
    fi
    sleep 2
  done
  echo "TIMEOUT aguardando health de $service" >&2
  return 1
}

cmd_list() {
  cat <<EOF
project: $PROJECT
compose: infra/$COMPOSE_FILE
checkout_previsto: /home/operador/projetos-teste/delpi-central
activation: $ACTIVATION_STATUS
porta_host: \${DELPI_HML_BIND_ADDR}:18080 (HTTP legado) + :18443 (HTTPS canônico)
rede: delpi-hml-network
env: infra/$ENV_EXAMPLE → copiar para infra/$ENV_LOCAL no checkout de homologação
certs: infra/hml-certs/ (hml-tls-prepare.sh; fora do Git)

cenários:
  databases             postgres-core, keycloak-db, postgres-plugins (autorizado)
  keycloak              somente delpi-hml-keycloak (autorizado; --no-deps)
  gateway               somente delpi-hml-gateway (autorizado; build TLS + --no-deps)
  core-api              somente delpi-hml-core-api (autorizado; build + --no-deps)
  portal                somente delpi-hml-portal (autorizado; build Vite HTTPS + --no-deps)
  tls-activate          cutover HTTPS coordenado (autorizado)
  redis                 somente delpi-hml-redis (autorizado; --no-deps)
  api-delpi             somente delpi-hml-api-delpi (autorizado; build + migrations plugins)
  plugin-ui             somente delpi-hml-plugin-ui (autorizado; build MF)
  production-control-api  somente API PC HML (autorizado; migrations schema PC)
  production-control-ui   somente MFE PC HML (autorizado)
  baseline              plataforma + production-control (up bloqueado como pacote)
  platform              portal, core, api-delpi, plugin-ui, auth, bancos, redis, gateway
  production-control    platform + MFE e API de Production Control

ordem databases:
$(printf '  %s\n' "${DATABASE_SERVICES[@]}")
ordem keycloak:
$(printf '  %s\n' "${KEYCLOAK_SERVICES[@]}")
ordem gateway:
$(printf '  %s\n' "${GATEWAY_SERVICES[@]}")
ordem core-api:
$(printf '  %s\n' "${CORE_API_SERVICES[@]}")
ordem portal:
$(printf '  %s\n' "${PORTAL_SERVICES[@]}")
ordem redis/api/pc:
$(printf '  %s\n' "${REDIS_SERVICES[@]}" "${API_DELPI_SERVICES[@]}" "${PLUGIN_UI_SERVICES[@]}" "${PC_API_SERVICES[@]}" "${PC_UI_SERVICES[@]}")

bloqueados como up único:
  baseline | platform | production-control (use cenários seletivos acima)
EOF
}

cmd_validate() {
  local env_file
  env_file="$(env_file_for example)"
  echo "Renderizando config (profile databases, $env_file)..."
  compose_config databases "$env_file" >/dev/null
  echo "Renderizando config (profile keycloak, $env_file)..."
  compose_config keycloak "$env_file" >/dev/null
  echo "Renderizando config (profile gateway, $env_file)..."
  compose_config gateway "$env_file" >/dev/null
  echo "Renderizando config (profile core-api, $env_file)..."
  compose_config core-api "$env_file" >/dev/null
  echo "Renderizando config (profile portal, $env_file)..."
  compose_config portal "$env_file" >/dev/null
  for p in redis api-delpi plugin-ui production-control-api production-control-ui; do
    echo "Renderizando config (profile $p, $env_file)..."
    compose_config "$p" "$env_file" >/dev/null
  done
  echo "Renderizando config (profile baseline, $env_file)..."
  compose_config baseline "$env_file" >/dev/null
  echo "Render sem profile (não deve publicar serviços)..."
  compose_config "" "$env_file" >/dev/null
  # nginx -t em container isolado (conf + snippets + certs efêmeros ou reais).
  echo "Validando sintaxe nginx.hml.conf (HTTP+HTTPS)..."
  local cert_dir tmp_certs=""
  if [[ -f "$COMPOSE_DIR/hml-certs/hml-gateway.crt" && -f "$COMPOSE_DIR/hml-certs/hml-gateway.key" ]]; then
    cert_dir="$COMPOSE_DIR/hml-certs"
  else
    tmp_certs="$(mktemp -d)"
    cert_dir="$tmp_certs"
    openssl req -x509 -newkey rsa:2048 -nodes -keyout "$cert_dir/hml-gateway.key" \
      -out "$cert_dir/hml-gateway.crt" -days 1 -subj "/CN=hml-validate" >/dev/null 2>&1
  fi
  docker run --rm \
    -v "$REPO_ROOT/gateway/nginx.hml.conf:/etc/nginx/nginx.conf:ro" \
    -v "$REPO_ROOT/gateway/snippets:/etc/nginx/snippets:ro" \
    -v "$cert_dir/hml-gateway.crt:/etc/nginx/hml-certs/hml-gateway.crt:ro" \
    -v "$cert_dir/hml-gateway.key:/etc/nginx/hml-certs/hml-gateway.key:ro" \
    nginx:alpine nginx -t
  [[ -n "$tmp_certs" ]] && rm -rf "$tmp_certs"
  python3 "$SCRIPT_DIR/tests/test_hml_compose_isolation.py"
  echo "VALIDACAO_ESTATICA=PASS"
  echo "$ACTIVATION_STATUS"
}

cmd_config() {
  local scenario="$1"
  local env_file
  env_file="$(env_file_for example)"
  compose_config "$scenario" "$env_file"
}

cmd_simulate() {
  local scenario="$1"
  shift
  local -a wanted=()
  if [[ $# -gt 0 ]]; then
    local raw="$1"
    IFS=',' read -r -a wanted <<<"$raw"
  else
    mapfile -t wanted < <(scenario_services "$scenario")
  fi
  local -a known=()
  mapfile -t known < <(scenario_services "$scenario")
  local svc ok have
  for svc in "${wanted[@]}"; do
    ok=false
    for have in "${known[@]}"; do
      [[ "$svc" == "$have" ]] && ok=true
    done
    if [[ "$ok" != true ]]; then
      echo "Serviço '$svc' não pertence ao cenário $scenario." >&2
      exit 1
    fi
  done
  local -a plan=()
  mapfile -t plan < <(ordered_selection "${wanted[@]}")
  echo "SIMULACAO=DRY_RUN"
  echo "project=$PROJECT"
  echo "scenario=$scenario"
  echo "activation=$ACTIVATION_STATUS"
  echo "serviços, na ordem:"
  printf '  %s\n' "${plan[@]}"
  if is_authorized_up "$scenario"; then
    echo "comando autorizado (ainda não executado neste simulate):"
    echo "  ./infra/scripts/hml-compose.sh up --scenario $scenario"
  else
    echo "comando que NÃO foi executado (up ainda não autorizado para este cenário):"
    echo "  docker compose --project-name $PROJECT -f infra/$COMPOSE_FILE --env-file infra/$ENV_LOCAL --profile $scenario up -d --no-deps ${plan[*]}"
  fi
}

cmd_status() {
  local env_file
  env_file="$(env_file_for local)"
  assert_env_file_allowed "$env_file"
  assert_compose_identity
  echo "Consulta somente leitura do projeto $PROJECT."
  (
    cd "$COMPOSE_DIR"
    docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
      -f "$COMPOSE_FILE" --env-file "$env_file" ps -a
  )
}

require_local_env() {
  local env_file
  env_file="$(env_file_for local)"
  assert_env_file_allowed "$env_file"
  assert_compose_identity
  if [[ ! -f "$COMPOSE_DIR/$ENV_LOCAL" ]]; then
    echo "infra/$ENV_LOCAL ausente. Copie de env.hml.example e defina credenciais exclusivas." >&2
    exit 1
  fi
  if [[ "$(basename "$env_file")" != "$ENV_LOCAL" ]]; then
    echo "operação exige infra/$ENV_LOCAL (não o example)." >&2
    exit 1
  fi
  printf '%s\n' "$env_file"
}

cmd_up_databases() {
  local env_file
  env_file="$(require_local_env)"
  echo "ATIVACAO=databases"
  echo "project=$PROJECT"
  echo "env=infra/$ENV_LOCAL"
  echo "servicos=${DATABASE_SERVICES[*]}"
  echo "modo=up -d --no-deps (sequencial, com health entre serviços)"

  local svc
  for svc in "${DATABASE_SERVICES[@]}"; do
    echo "=== subindo $svc ==="
    (
      cd "$COMPOSE_DIR"
      env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
        docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
          -f "$COMPOSE_FILE" --env-file "$env_file" --profile databases \
          up -d --no-deps --no-build "$svc"
    )
    wait_healthy "$svc" "$env_file" databases
  done

  echo "HML_DATABASES_UP=PASS"
  (
    cd "$COMPOSE_DIR"
    docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
      -f "$COMPOSE_FILE" --env-file "$env_file" --profile databases ps
  )
}

cmd_up_keycloak() {
  local env_file
  env_file="$(require_local_env)"

  # Bancos HML devem continuar saudáveis; não reiniciar.
  local db
  for db in delpi-hml-postgres-core delpi-hml-keycloak-db delpi-hml-postgres-plugins; do
    docker ps --format '{{.Names}} {{.Status}}' | grep -E "^${db} .*healthy" >/dev/null || {
      echo "[ERRO] $db não está healthy. Abortado sem iniciar Keycloak." >&2
      exit 1
    }
  done

  echo "ATIVACAO=keycloak"
  echo "project=$PROJECT"
  echo "env=infra/$ENV_LOCAL"
  echo "servicos=keycloak"
  echo "modo=up -d --no-deps --no-build (não sobe gateway/apps)"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile keycloak \
        up -d --no-deps --no-build keycloak
  )
  wait_healthy keycloak "$env_file" keycloak

  # Garantir que nada além dos 3 DBs + keycloak subiu.
  local extras
  extras="$(docker ps -a --filter name=delpi-hml --format '{{.Names}}' | grep -Ev 'delpi-hml-(postgres-core|keycloak-db|postgres-plugins|keycloak)$' || true)"
  if [[ -n "$extras" ]]; then
    echo "[ERRO] containers HML inesperados após up keycloak:" >&2
    echo "$extras" >&2
    exit 1
  fi

  echo "HML_KEYCLOAK_UP=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_bootstrap_keycloak() {
  require_local_env >/dev/null
  bash "$SCRIPT_DIR/keycloak-hml-bootstrap.sh"
}

require_hml_base_healthy() {
  local c
  for c in delpi-hml-postgres-core delpi-hml-keycloak-db delpi-hml-postgres-plugins \
           delpi-hml-keycloak delpi-hml-gateway delpi-hml-core-api delpi-hml-portal; do
    docker ps --format '{{.Names}} {{.Status}}' | grep -E "^${c} .*healthy" >/dev/null || {
      echo "[ERRO] $c não está healthy. Abortado." >&2
      exit 1
    }
  done
}

assert_totvs_disabled_in_render() {
  local env_file="$1" profile="$2" service="$3"
  local host
  host="$(
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile "$profile" \
        config --format json \
      | python3 -c 'import json,sys; s=json.load(sys.stdin)["services"][sys.argv[1]]["environment"];
print((s.get("DB_HOST") if isinstance(s,dict) else "") or "")' "$service"
  )"
  if [[ "$host" != "totvs-disabled.hml.invalid" && "$service" == "api-delpi" ]]; then
    echo "[ERRO] api-delpi DB_HOST='$host' (esperado totvs-disabled.hml.invalid). STOP." >&2
    exit 1
  fi
}

cmd_up_redis() {
  local env_file
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"
  require_hml_base_healthy

  # Porta 6379 não pode aparecer no host (compose ports: []).
  local ports_json
  ports_json="$(
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile redis \
        config --format json \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["services"]["delpi-redis"].get("ports") or [])'
  )"
  if [[ "$ports_json" != "[]" ]]; then
    echo "[ERRO] delpi-redis HML publicaria portas no host: $ports_json. STOP." >&2
    exit 1
  fi

  echo "ATIVACAO=redis"
  echo "project=$PROJECT"
  echo "servicos=delpi-redis"
  echo "modo=up -d --no-deps (imagem redis:7-alpine; requirepass; sem publish)"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile redis \
        up -d --no-deps --pull missing delpi-redis
  )
  wait_healthy delpi-redis "$env_file" redis
  assert_hml_container_allowlist ALLOWED_HML_CONTAINERS_AFTER_REDIS

  # Isolamento: PONG só na rede HML (via container).
  docker exec delpi-hml-redis sh -c 'redis-cli -a "$DELPI_REDIS_PASSWORD" ping' | grep -q PONG || {
    echo "[ERRO] redis-cli ping falhou dentro do container HML." >&2
    exit 1
  }
  if ss -lnt 2>/dev/null | grep -E ':6379\s' >/dev/null; then
    # Só falha se o listener for do container HML publicado — Compose garante ports [].
    if docker port delpi-hml-redis 2>/dev/null | grep -q 6379; then
      echo "[ERRO] delpi-hml-redis publicou 6379 no host. STOP." >&2
      exit 1
    fi
  fi

  echo "HML_REDIS_UP=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_up_api_delpi() {
  local env_file plugins_host
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"
  require_hml_base_healthy
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-redis .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-redis não está healthy. Rode up --scenario redis antes." >&2
    exit 1
  }
  assert_totvs_disabled_in_render "$env_file" api-delpi api-delpi

  plugins_host="$(
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile api-delpi \
        config --format json \
      | python3 -c 'import json,sys; s=json.load(sys.stdin)["services"]["api-delpi"]["environment"];
print(s.get("PLUGINS_DB_HOST") if isinstance(s,dict) else "")'
  )"
  if [[ "$plugins_host" != "postgres-plugins" ]]; then
    echo "[ERRO] PLUGINS_DB_HOST='$plugins_host' (esperado postgres-plugins). STOP." >&2
    exit 1
  fi

  echo "ATIVACAO=api-delpi"
  echo "project=$PROJECT"
  echo "servicos=api-delpi"
  echo "modo=build + up -d --no-deps (RUN_PLUGINS_MIGRATIONS_ON_STARTUP=true → postgres-plugins HML)"
  echo "totvs=bloqueado (totvs-disabled.hml.invalid)"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile api-delpi \
        build api-delpi
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile api-delpi \
        up -d --no-deps --no-build api-delpi
  )
  wait_healthy api-delpi "$env_file" api-delpi
  assert_hml_container_allowlist ALLOWED_HML_CONTAINERS_AFTER_API_DELPI

  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 20 \
    --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
    https://192.168.1.237:18443/apps/api-delpi/health || echo FAIL)"
  if [[ "$code" != "200" ]]; then
    echo "[ERRO] /apps/api-delpi/health via gateway HTTPS retornou $code. STOP." >&2
    exit 1
  fi
  code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 \
    --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
    https://192.168.1.237:18443/apps/api-delpi/me || echo FAIL)"
  if [[ "$code" != "401" && "$code" != "403" ]]; then
    echo "[ERRO] /apps/api-delpi/me sem token deveria 401/403, veio $code. STOP." >&2
    exit 1
  fi

  echo "HML_API_DELPI_UP=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_up_plugin_ui() {
  local env_file
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"
  require_hml_base_healthy

  echo "ATIVACAO=plugin-ui"
  echo "project=$PROJECT"
  echo "servicos=plugin-ui"
  echo "modo=build MF + up -d --no-deps"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile plugin-ui \
        build plugin-ui
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile plugin-ui \
        up -d --no-deps --no-build plugin-ui
  )
  wait_healthy plugin-ui "$env_file" plugin-ui
  assert_hml_container_allowlist ALLOWED_HML_CONTAINERS_AFTER_PLUGIN_UI

  local code ctype
  code="$(curl -sS -o /tmp/hml_remote_entry.js -w '%{http_code}' --connect-timeout 5 --max-time 20 \
    --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
    https://192.168.1.237:18443/apps/plugin-ui/assets/remoteEntry.js || echo FAIL)"
  ctype="$(file -b --mime-type /tmp/hml_remote_entry.js 2>/dev/null || echo unknown)"
  if [[ "$code" != "200" ]]; then
    # fallback path used by some nginx mappings
    code="$(curl -sS -o /tmp/hml_remote_entry.js -w '%{http_code}' --connect-timeout 5 --max-time 20 \
      --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
      https://192.168.1.237:18443/apps/plugin-ui/remoteEntry.js || echo FAIL)"
  fi
  if [[ "$code" != "200" ]]; then
    echo "[ERRO] remoteEntry.js via gateway retornou $code. STOP." >&2
    exit 1
  fi
  if grep -Eiq 'minhadelpi\.com\.br' /tmp/hml_remote_entry.js 2>/dev/null; then
    echo "[ERRO] remoteEntry.js contém domínio produtivo. STOP." >&2
    exit 1
  fi
  rm -f /tmp/hml_remote_entry.js

  echo "HML_PLUGIN_UI_UP=PASS mime=$ctype"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_up_production_control_api() {
  local env_file
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"
  require_hml_base_healthy
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-api-delpi .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-api-delpi não está healthy. Rode up --scenario api-delpi antes." >&2
    exit 1
  }

  echo "ATIVACAO=production-control-api"
  echo "project=$PROJECT"
  echo "servicos=production-control-api"
  echo "modo=build + up -d --no-deps (PC_RUN_MIGRATIONS_ON_STARTUP=true → plugins HML)"
  echo "jobs_externos=bloqueados (MES autonomous/alerts off; pulse/RH/requests vazios)"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile production-control-api \
        build production-control-api
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile production-control-api \
        up -d --no-deps --no-build production-control-api
  )
  wait_healthy production-control-api "$env_file" production-control-api
  assert_hml_container_allowlist ALLOWED_HML_CONTAINERS_AFTER_PC_API

  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 20 \
    --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
    https://192.168.1.237:18443/apps/production-control-api/health || echo FAIL)"
  if [[ "$code" != "200" ]]; then
    echo "[ERRO] /apps/production-control-api/health retornou $code. STOP." >&2
    exit 1
  fi

  echo "HML_PRODUCTION_CONTROL_API_UP=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_up_production_control_ui() {
  local env_file
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"
  require_hml_base_healthy
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-plugin-ui .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-plugin-ui não está healthy. Rode up --scenario plugin-ui antes." >&2
    exit 1
  }
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-production-control-api .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-production-control-api não está healthy. Rode up --scenario production-control-api antes." >&2
    exit 1
  }

  echo "ATIVACAO=production-control-ui"
  echo "project=$PROJECT"
  echo "servicos=production-control"
  echo "modo=build MFE + up -d --no-deps"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile production-control-ui \
        build production-control
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile production-control-ui \
        up -d --no-deps --no-build production-control
  )
  wait_healthy production-control "$env_file" production-control-ui
  assert_hml_container_allowlist ALLOWED_HML_CONTAINERS_AFTER_PC_UI

  local code
  code="$(curl -sS -o /tmp/hml_pc_index.html -w '%{http_code}' --connect-timeout 5 --max-time 20 \
    --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
    https://192.168.1.237:18443/apps/production-control/ || echo FAIL)"
  if [[ "$code" != "200" ]]; then
    echo "[ERRO] /apps/production-control/ retornou $code. STOP." >&2
    exit 1
  fi
  if grep -Eiq 'minhadelpi\.com\.br' /tmp/hml_pc_index.html 2>/dev/null; then
    echo "[ERRO] frontend PC contém domínio produtivo. STOP." >&2
    exit 1
  fi
  rm -f /tmp/hml_pc_index.html

  echo "HML_PRODUCTION_CONTROL_UI_UP=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_up_gateway() {
  local env_file bind_addr tls_port
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"
  assert_hml_tls_certs
  bind_addr="$(grep -E '^DELPI_HML_BIND_ADDR=' "$COMPOSE_DIR/$ENV_LOCAL" | head -1 | cut -d= -f2- | tr -d '"'"'"'\r')"
  bind_addr="${bind_addr:-192.168.1.237}"
  tls_port="$(grep -E '^DELPI_HML_TLS_PORT=' "$COMPOSE_DIR/$ENV_LOCAL" | head -1 | cut -d= -f2- | tr -d '"'"'"'\r')"
  tls_port="${tls_port:-18443}"

  local db
  for db in delpi-hml-postgres-core delpi-hml-keycloak-db delpi-hml-postgres-plugins; do
    docker ps --format '{{.Names}} {{.Status}}' | grep -E "^${db} .*healthy" >/dev/null || {
      echo "[ERRO] $db não está healthy. Abortado sem iniciar gateway." >&2
      exit 1
    }
  done
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-keycloak .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-keycloak não está healthy. Abortado." >&2
    exit 1
  }

  # Porta 18080 livre no bind LAN (exceto se já for o próprio gateway HML).
  if ss -lnt 2>/dev/null | grep -E ":18080\\s" >/dev/null; then
    if ! docker ps --format '{{.Names}} {{.Ports}}' | grep -q 'delpi-hml-gateway.*18080'; then
      echo "[ERRO] porta 18080 ocupada por outro processo. STOP." >&2
      ss -lnt | grep 18080 || true
      exit 1
    fi
  fi
  if ss -lnt 2>/dev/null | grep -E ":${tls_port}\\s" >/dev/null; then
    if ! docker ps --format '{{.Names}} {{.Ports}}' | grep -q "delpi-hml-gateway.*${tls_port}"; then
      echo "[ERRO] porta ${tls_port} ocupada por outro processo. STOP." >&2
      ss -lnt | grep "${tls_port}" || true
      exit 1
    fi
  fi

  echo "ATIVACAO=gateway"
  echo "project=$PROJECT"
  echo "env=infra/$ENV_LOCAL"
  echo "bind=${bind_addr}:18080 (HTTP) + ${bind_addr}:${tls_port} (HTTPS)"
  echo "servicos=gateway"
  echo "modo=build gateway TLS + up -d --no-deps (não sobe apps)"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile gateway \
        build gateway
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile gateway \
        up -d --no-deps --no-build gateway
  )
  wait_healthy gateway "$env_file" gateway

  # Após Core/Portal já ativos (cutover TLS), o allowlist canônico é o conjunto completo (7).
  assert_hml_container_allowlist ALLOWED_HML_CONTAINERS_AFTER_PORTAL

  echo "HML_GATEWAY_UP=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_up_core_api() {
  local env_file
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"

  local db
  for db in delpi-hml-postgres-core delpi-hml-keycloak-db delpi-hml-postgres-plugins; do
    docker ps --format '{{.Names}} {{.Status}}' | grep -E "^${db} .*healthy" >/dev/null || {
      echo "[ERRO] $db não está healthy. Abortado sem iniciar core-api." >&2
      exit 1
    }
  done
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-keycloak .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-keycloak não está healthy. Abortado." >&2
    exit 1
  }
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-gateway .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-gateway não está healthy. Abortado." >&2
    exit 1
  }

  # Confirma destino DB exclusivo HML (não prod) via env do compose renderizado.
  local db_host
  db_host="$(
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile core-api \
        config --format json \
      | python3 -c 'import json,sys; s=json.load(sys.stdin)["services"]["core-api"]["environment"];
print(s.get("DB_HOST") if isinstance(s,dict) else "")'
  )"
  if [[ "$db_host" != "postgres-core" ]]; then
    echo "[ERRO] DB_HOST renderizado='$db_host' (esperado postgres-core). STOP." >&2
    exit 1
  fi

  echo "ATIVACAO=core-api"
  echo "project=$PROJECT"
  echo "env=infra/$ENV_LOCAL"
  echo "servicos=core-api"
  echo "modo=build core-api + up -d --no-deps (migrations Alembic no Postgres Core HML)"
  echo "redis=nao_iniciado (stores memory)"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile core-api \
        build core-api
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile core-api \
        up -d --no-deps --no-build core-api
  )
  wait_healthy core-api "$env_file" core-api
  # Portal pode já existir no cutover TLS; allowlist = conjunto completo (7).
  assert_hml_container_allowlist ALLOWED_HML_CONTAINERS_AFTER_PORTAL

  # Smoke via gateway (sem token) — HTTP legado + HTTPS canônico
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 \
    http://192.168.1.237:18080/core-api/health || echo FAIL)"
  if [[ "$code" != "200" ]]; then
    echo "[ERRO] /core-api/health via gateway HTTP retornou $code (esperado 200). STOP." >&2
    exit 1
  fi
  assert_hml_tls_certs
  code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 \
    --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
    https://192.168.1.237:18443/core-api/health || echo FAIL)"
  if [[ "$code" != "200" ]]; then
    echo "[ERRO] /core-api/health via gateway HTTPS retornou $code (esperado 200). STOP." >&2
    exit 1
  fi

  echo "HML_CORE_API_UP=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_up_portal() {
  local env_file
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"
  assert_hml_tls_certs

  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-keycloak .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-keycloak não está healthy. Abortado." >&2
    exit 1
  }
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-core-api .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-core-api não está healthy (Gate A). Abortado." >&2
    exit 1
  }
  docker ps --format '{{.Names}} {{.Status}}' | grep -E '^delpi-hml-gateway .*healthy' >/dev/null || {
    echo "[ERRO] delpi-hml-gateway não está healthy. Abortado." >&2
    exit 1
  }

  # Guard bake-time: VITE_* devem apontar para HML HTTPS LAN.
  local vite_blob
  vite_blob="$(grep -E '^VITE_KC_(URL|REALM|CLIENT_ID|REDIRECT_URI)=' "$COMPOSE_DIR/$ENV_LOCAL" || true)"
  if ! grep -Eq '^VITE_KC_URL=https://192\.168\.1\.237:18443/auth' <<<"$vite_blob"; then
    echo "[ERRO] VITE_KC_URL HTTPS HML ausente/divergente. STOP (evita bake produtivo)." >&2
    exit 1
  fi
  if ! grep -Eq '^VITE_KC_REDIRECT_URI=https://192\.168\.1\.237:18443/' <<<"$vite_blob"; then
    echo "[ERRO] VITE_KC_REDIRECT_URI HTTPS HML ausente/divergente. STOP." >&2
    exit 1
  fi
  if grep -Eiq 'minhadelpi\.com\.br' <<<"$vite_blob"; then
    echo "[ERRO] VITE_KC_* referencia produção. STOP." >&2
    exit 1
  fi

  echo "ATIVACAO=portal"
  echo "project=$PROJECT"
  echo "env=infra/$ENV_LOCAL"
  echo "servicos=portal"
  echo "modo=build portal (VITE HML) + up -d --no-deps"
  echo "plugin-ui=nao_iniciado"

  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile portal \
        build portal
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile portal \
        up -d --no-deps --no-build portal
  )
  wait_healthy portal "$env_file" portal
  assert_hml_container_allowlist ALLOWED_HML_CONTAINERS_AFTER_PORTAL

  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 \
    http://192.168.1.237:18080/ || echo FAIL)"
  if [[ "$code" != "200" ]]; then
    echo "[ERRO] / via gateway HTTP legado retornou $code (esperado 200). STOP." >&2
    exit 1
  fi
  code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 \
    --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
    https://192.168.1.237:18443/ || echo FAIL)"
  if [[ "$code" != "200" ]]; then
    echo "[ERRO] / via gateway HTTPS retornou $code (esperado 200). STOP." >&2
    exit 1
  fi

  # Bundle não deve conter domínio produtivo nem issuer HTTP antigo
  if docker exec delpi-hml-portal sh -c 'grep -R -l minhadelpi.com.br /usr/share/nginx/html 2>/dev/null | head -5' | grep -q .; then
    echo "[ERRO] assets do Portal HML contêm minhadelpi.com.br. STOP." >&2
    exit 1
  fi
  if docker exec delpi-hml-portal sh -c 'grep -R -l "192.168.1.237:18080" /usr/share/nginx/html 2>/dev/null | head -5' | grep -q .; then
    echo "[ERRO] assets do Portal HML ainda embutem origem HTTP :18080. STOP." >&2
    exit 1
  fi
  if ! docker exec delpi-hml-portal sh -c 'grep -R -l "192.168.1.237:18443" /usr/share/nginx/html 2>/dev/null | head -5' | grep -q .; then
    echo "[ERRO] assets do Portal HML sem origem HTTPS :18443. STOP." >&2
    exit 1
  fi

  echo "HML_PORTAL_UP=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}

cmd_up_tls_activate() {
  local env_file
  env_file="$(require_local_env)"
  assert_no_prod_markers_in_env "$env_file"
  assert_hml_tls_certs

  echo "ATIVACAO=tls-activate"
  echo "project=$PROJECT"
  echo "cutover=HTTPS https://192.168.1.237:18443"
  echo "ordem=gateway → keycloak --force-recreate → bootstrap → core-api → portal"

  # 1) Gateway TLS
  cmd_up_gateway

  # 2) Keycloak com KC_HOSTNAME_PORT/HTTPS (recreate para aplicar env)
  echo "=== recreate keycloak com issuer HTTPS ==="
  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME \
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile keycloak \
        up -d --no-deps --force-recreate --no-build keycloak
  )
  wait_healthy keycloak "$env_file" keycloak

  # 3) Bootstrap realm/client/redirects HTTPS
  cmd_bootstrap_keycloak

  # 4) Core API com KEYCLOAK_ISSUER HTTPS
  cmd_up_core_api

  # 5) Portal bake Vite HTTPS
  cmd_up_portal

  # Smoke OIDC discovery público HTTPS
  local issuer disc
  disc="$(curl -sS --connect-timeout 5 --max-time 20 \
    --cacert "$COMPOSE_DIR/hml-certs/hml-local-ca.crt" \
    https://192.168.1.237:18443/auth/realms/delpi/.well-known/openid-configuration)"
  issuer="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("issuer",""))' <<<"$disc")"
  if [[ "$issuer" != "https://192.168.1.237:18443/auth/realms/delpi" ]]; then
    echo "[ERRO] issuer público HTTPS divergente: $issuer" >&2
    exit 1
  fi
  echo "OIDC_PUBLIC_DISCOVERY=PASS issuer=$issuer"
  echo "HML_TLS_ACTIVATE=PASS"
  docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
}


SCENARIO="baseline"
SERVICES=""
ACTION="${1:-}"
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario)
      SCENARIO="${2:?}"
      shift 2
      ;;
    --services)
      SERVICES="${2:?}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Opção desconhecida: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$ACTION" in
  list) cmd_list ;;
  validate) cmd_validate ;;
  config) cmd_config "$SCENARIO" ;;
  simulate)
    if [[ -n "$SERVICES" ]]; then
      cmd_simulate "$SCENARIO" "$SERVICES"
    else
      cmd_simulate "$SCENARIO"
    fi
    ;;
  status) cmd_status ;;
  bootstrap-keycloak) cmd_bootstrap_keycloak ;;
  up)
    if ! is_authorized_up "$SCENARIO"; then
      refuse_activation "up --scenario $SCENARIO"
    fi
    if [[ -n "$SERVICES" ]]; then
      echo "up autorizado não aceita --services parcial; use o cenário canônico." >&2
      exit 1
    fi
    case "$SCENARIO" in
      databases) cmd_up_databases ;;
      keycloak) cmd_up_keycloak ;;
      gateway) cmd_up_gateway ;;
      core-api) cmd_up_core_api ;;
      portal) cmd_up_portal ;;
      tls-activate) cmd_up_tls_activate ;;
      redis) cmd_up_redis ;;
      api-delpi) cmd_up_api_delpi ;;
      plugin-ui) cmd_up_plugin_ui ;;
      production-control-api) cmd_up_production_control_api ;;
      production-control-ui) cmd_up_production_control_ui ;;
      *) refuse_activation "up --scenario $SCENARIO" ;;
    esac
    ;;
  down|stop|start|restart|build|pull|rm|kill|push)
    refuse_activation "$ACTION"
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    echo "Comando desconhecido: $ACTION" >&2
    usage >&2
    exit 1
    ;;
esac
