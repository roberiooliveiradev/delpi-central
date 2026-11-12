#!/usr/bin/env bash
# Homologação delpi-hml — operação controlada.
#
# Leitura/simulação: list, validate, config, simulate, status.
# Ativação autorizada:
#   - databases  → postgres-core, keycloak-db, postgres-plugins
#   - keycloak   → somente o serviço keycloak (--no-deps; DB já ativo)
#   - gateway    → somente delpi-hml-gateway (build imagem HML; --no-deps)
# Qualquer outro up/build/pull/down/stop continua recusado.
# Portal/Core/API DELPI/PC permanecem bloqueados.
#
# Uso, a partir da raiz do repositório:
#   ./infra/scripts/hml-compose.sh list
#   ./infra/scripts/hml-compose.sh validate
#   ./infra/scripts/hml-compose.sh config [--scenario databases|keycloak|gateway|baseline|...]
#   ./infra/scripts/hml-compose.sh simulate [--scenario ...] [--services a,b]
#   ./infra/scripts/hml-compose.sh status
#   ./infra/scripts/hml-compose.sh up --scenario databases
#   ./infra/scripts/hml-compose.sh up --scenario keycloak
#   ./infra/scripts/hml-compose.sh up --scenario gateway
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
ACTIVATION_STATUS="HOMOLOGATION_DATABASES_KEYCLOAK_AND_GATEWAY_AUTHORIZED"
HEALTH_TIMEOUT_SEC="${DELPI_HML_HEALTH_TIMEOUT_SEC:-180}"

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
AUTHORIZED_UP_SCENARIOS=(databases keycloak gateway)
ALLOWED_HML_CONTAINERS_AFTER_GATEWAY=(
  delpi-hml-postgres-core
  delpi-hml-keycloak-db
  delpi-hml-postgres-plugins
  delpi-hml-keycloak
  delpi-hml-gateway
)

usage() {
  sed -n '2,20p' "$0"
}

refuse_activation() {
  local action="$1"
  echo "HOMOLOGATION_ACTIVATION_NOT_AUTHORIZED" >&2
  echo "Ação '$action' não executada fora dos profiles autorizados." >&2
  echo "Autorizados: up --scenario databases|keycloak|gateway | bootstrap-keycloak." >&2
  echo "Portal, Core API, API DELPI e Production Control permanecem bloqueados." >&2
  exit 2
}

scenario_services() {
  local scenario="$1"
  case "$scenario" in
    databases) printf '%s\n' "${DATABASE_SERVICES[@]}" ;;
    keycloak) printf '%s\n' "${KEYCLOAK_SERVICES[@]}" ;;
    gateway) printf '%s\n' "${GATEWAY_SERVICES[@]}" ;;
    baseline) printf '%s\n' "${PLATFORM_SERVICES[@]}" "${PC_SERVICES[@]}" ;;
    platform) printf '%s\n' "${PLATFORM_SERVICES[@]}" ;;
    production-control) printf '%s\n' "${PLATFORM_SERVICES[@]}" "${PC_SERVICES[@]}" ;;
    *)
      echo "Cenário desconhecido: $scenario" >&2
      exit 1
      ;;
  esac
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
    .env|.env.prod|.env.prod.cpu|.env.dev)
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
    cid="$(docker ps -q --filter "name=delpi-hml-${service}" | head -n 1 || true)"
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
porta_host: \${DELPI_HML_BIND_ADDR}:18080 (gateway autorizado nesta etapa)
rede: delpi-hml-network
env: infra/$ENV_EXAMPLE → copiar para infra/$ENV_LOCAL no checkout de homologação

cenários:
  databases             postgres-core, keycloak-db, postgres-plugins (autorizado)
  keycloak              somente delpi-hml-keycloak (autorizado; --no-deps)
  gateway               somente delpi-hml-gateway (autorizado; build + --no-deps)
  baseline              plataforma + production-control (up bloqueado)
  platform              portal, core, api-delpi, plugin-ui, auth, bancos, redis, gateway
  production-control    platform + MFE e API de Production Control

ordem databases:
$(printf '  %s\n' "${DATABASE_SERVICES[@]}")
ordem keycloak:
$(printf '  %s\n' "${KEYCLOAK_SERVICES[@]}")
ordem gateway:
$(printf '  %s\n' "${GATEWAY_SERVICES[@]}")

bloqueados nesta etapa:
  portal, core-api, api-delpi, plugin-ui, production-control*, redis
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
  echo "Renderizando config (profile baseline, $env_file)..."
  compose_config baseline "$env_file" >/dev/null
  echo "Render sem profile (não deve publicar serviços)..."
  compose_config "" "$env_file" >/dev/null
  # nginx -t em container isolado (sem publicar porta; conf HML montada).
  echo "Validando sintaxe nginx.hml.conf..."
  docker run --rm \
    -v "$REPO_ROOT/gateway/nginx.hml.conf:/etc/nginx/nginx.conf:ro" \
    nginx:alpine nginx -t
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

cmd_up_gateway() {
  local env_file bind_addr
  env_file="$(require_local_env)"
  bind_addr="$(grep -E '^DELPI_HML_BIND_ADDR=' "$COMPOSE_DIR/$ENV_LOCAL" | head -1 | cut -d= -f2- | tr -d '"'"'"'\r')"
  bind_addr="${bind_addr:-192.168.1.237}"

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

  echo "ATIVACAO=gateway"
  echo "project=$PROJECT"
  echo "env=infra/$ENV_LOCAL"
  echo "bind=${bind_addr}:18080"
  echo "servicos=gateway"
  echo "modo=build gateway + up -d --no-deps (não sobe apps)"

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

  local name extras allowed
  extras=""
  while read -r name; do
    [[ -z "$name" ]] && continue
    allowed=false
    local ok
    for ok in "${ALLOWED_HML_CONTAINERS_AFTER_GATEWAY[@]}"; do
      [[ "$name" == "$ok" ]] && allowed=true
    done
    if [[ "$allowed" != true ]]; then
      extras+="$name"$'\n'
    fi
  done < <(docker ps -a --filter name=delpi-hml --format '{{.Names}}')
  if [[ -n "${extras//[[:space:]]/}" ]]; then
    echo "[ERRO] containers HML inesperados após up gateway:" >&2
    printf '%s' "$extras" >&2
    exit 1
  fi

  echo "HML_GATEWAY_UP=PASS"
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
