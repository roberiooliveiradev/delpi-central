#!/usr/bin/env bash
# Homologação delpi-hml — operação controlada.
#
# Leitura/simulação: list, validate, config, simulate, status.
# Ativação autorizada somente para o profile `databases`
# (postgres-core, keycloak-db, postgres-plugins), com --no-deps.
# Qualquer outro up/build/pull/down/stop continua recusado.
#
# Uso, a partir da raiz do repositório:
#   ./infra/scripts/hml-compose.sh list
#   ./infra/scripts/hml-compose.sh validate
#   ./infra/scripts/hml-compose.sh config [--scenario databases|baseline|platform|production-control]
#   ./infra/scripts/hml-compose.sh simulate [--scenario ...] [--services a,b]
#   ./infra/scripts/hml-compose.sh status
#   ./infra/scripts/hml-compose.sh up --scenario databases
#   ./infra/scripts/hml-compose.sh up|down|stop|build|pull   # demais cenários: recusa

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$COMPOSE_DIR/.." && pwd)"
PROJECT="delpi-hml"
COMPOSE_FILE="docker-compose.hml.yml"
ENV_EXAMPLE="env.hml.example"
ENV_LOCAL=".env.hml"
ACTIVATION_STATUS="HOMOLOGATION_DATABASES_ONLY_AUTHORIZED"
HEALTH_TIMEOUT_SEC="${DELPI_HML_HEALTH_TIMEOUT_SEC:-120}"

DATABASE_SERVICES=(
  postgres-core
  keycloak-db
  postgres-plugins
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

usage() {
  sed -n '2,16p' "$0"
}

refuse_activation() {
  local action="$1"
  echo "HOMOLOGATION_ACTIVATION_NOT_AUTHORIZED" >&2
  echo "Ação '$action' não executada fora do profile databases." >&2
  echo "Somente './infra/scripts/hml-compose.sh up --scenario databases' está autorizado nesta etapa." >&2
  echo "Nenhum container adicional foi criado, iniciado, parado ou removido." >&2
  exit 2
}

scenario_services() {
  local scenario="$1"
  case "$scenario" in
    databases) printf '%s\n' "${DATABASE_SERVICES[@]}" ;;
    baseline) printf '%s\n' "${PLATFORM_SERVICES[@]}" "${PC_SERVICES[@]}" ;;
    platform) printf '%s\n' "${PLATFORM_SERVICES[@]}" ;;
    production-control) printf '%s\n' "${PLATFORM_SERVICES[@]}" "${PC_SERVICES[@]}" ;;
    *)
      echo "Cenário desconhecido: $scenario" >&2
      exit 1
      ;;
  esac
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
  local deadline=$((SECONDS + HEALTH_TIMEOUT_SEC))
  local status
  echo "Aguardando health de $service (timeout ${HEALTH_TIMEOUT_SEC}s)..."
  while (( SECONDS < deadline )); do
    status="$(
      cd "$COMPOSE_DIR"
      docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
        -f "$COMPOSE_FILE" --env-file "$env_file" --profile databases \
        ps --status running --format '{{.Health}}' "$service" 2>/dev/null || true
    )"
    if [[ "$status" == "healthy" ]]; then
      echo "HEALTH=$service:healthy"
      return 0
    fi
    # Fallback: alguns ps formats retornam vazio; consultar docker inspect.
    local cid
    cid="$(docker ps -q --filter "name=^/${PROJECT}-${service}-" --filter "name=^/delpi-hml-${service}$" | head -n 1 || true)"
    if [[ -z "$cid" ]]; then
      cid="$(docker ps -q --filter "name=delpi-hml-${service}" | head -n 1 || true)"
    fi
    if [[ -n "$cid" ]]; then
      local health
      health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || true)"
      if [[ "$health" == "healthy" || "$health" == "running" ]]; then
        if docker exec "$cid" pg_isready -U "$(docker exec "$cid" printenv POSTGRES_USER)" -d "$(docker exec "$cid" printenv POSTGRES_DB)" >/dev/null 2>&1; then
          echo "HEALTH=$service:pg_isready"
          return 0
        fi
        if [[ "$health" == "healthy" ]]; then
          echo "HEALTH=$service:healthy"
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
porta_host: 127.0.0.1:18080 (container 80; sem 80/443 no host; não sobe nesta etapa)
rede: delpi-hml-network
env: infra/$ENV_EXAMPLE → copiar para infra/$ENV_LOCAL no checkout de homologação

cenários:
  databases             somente postgres-core, keycloak-db, postgres-plugins (autorizado)
  baseline              plataforma + production-control (ainda não autorizado a up)
  platform              portal, core, api-delpi, plugin-ui, auth, bancos, redis, gateway
  production-control    platform + MFE e API de Production Control

ordem de subida (databases nesta etapa):
$(printf '  %s\n' "${DATABASE_SERVICES[@]}")

desligados por ausência no Compose de homologação:
  ollama, vllm, searxng, languagetool, chat, schedulers myweg,
  external-data-scheduler, demais plugins e APIs
EOF
}

cmd_validate() {
  local env_file
  env_file="$(env_file_for example)"
  echo "Renderizando config (profile databases, $env_file)..."
  compose_config databases "$env_file" >/dev/null
  echo "Renderizando config (profile baseline, $env_file)..."
  compose_config baseline "$env_file" >/dev/null
  echo "Render sem profile (não deve publicar serviços)..."
  compose_config "" "$env_file" >/dev/null
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
  local svc ok
  for svc in "${wanted[@]}"; do
    ok=false
    local have
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
  if [[ "$scenario" == "databases" ]]; then
    echo "comando autorizado (ainda não executado neste simulate):"
    echo "  ./infra/scripts/hml-compose.sh up --scenario databases"
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

cmd_up_databases() {
  local env_file
  env_file="$(env_file_for local)"
  assert_env_file_allowed "$env_file"
  assert_compose_identity
  if [[ ! -f "$COMPOSE_DIR/$ENV_LOCAL" ]]; then
    echo "infra/$ENV_LOCAL ausente. Copie de env.hml.example e defina credenciais exclusivas antes do up." >&2
    exit 1
  fi
  if [[ "$(basename "$env_file")" != "$ENV_LOCAL" ]]; then
    echo "up databases exige infra/$ENV_LOCAL (não o example)." >&2
    exit 1
  fi

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
    wait_healthy "$svc" "$env_file"
  done

  echo "HML_DATABASES_UP=PASS"
  (
    cd "$COMPOSE_DIR"
    docker compose --project-name "$PROJECT" --project-directory "$COMPOSE_DIR" \
      -f "$COMPOSE_FILE" --env-file "$env_file" --profile databases ps
  )
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
  up)
    if [[ "$SCENARIO" != "databases" ]]; then
      refuse_activation "up --scenario $SCENARIO"
    fi
    if [[ -n "$SERVICES" ]]; then
      echo "up databases não aceita --services parcial nesta etapa; sobe os três bancos na ordem canônica." >&2
      exit 1
    fi
    cmd_up_databases
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
