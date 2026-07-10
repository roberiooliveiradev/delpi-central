#!/usr/bin/env bash
# Sobe ou reconstrói containers DELPI dev **um por vez** — evita OOM no WSL (~8 GB).
#
# Uso:
#   ./infra/scripts/up-dev-sequential.sh              # core + plugin-ui + todos MFEs (sem rebuild)
#   ./infra/scripts/up-dev-sequential.sh --build      # rebuild imagem de cada serviço, sequencial
#   ./infra/scripts/up-dev-sequential.sh --fase core --build
#   ./infra/scripts/up-dev-sequential.sh --fase mfe --build controle-retrabalhos public-hub
#   ./infra/scripts/up-dev-sequential.sh --fase chat --build
#   ./infra/scripts/up-dev-sequential.sh --list
#
# Pré-requisito: infra/.env (cp infra/.env.dev.example infra/.env)
#
# Doc: infra/README-ambiente.md § Inicialização segura de containers

set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$COMPOSE_DIR"

COMPOSE_BASE=(docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml --env-file .env)
COMPOSE_PLUGINS=(docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml --profile plugins --env-file .env)
COMPOSE_CHAT=(docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml --profile chat --env-file .env)

export COMPOSE_PARALLEL_LIMIT=1
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

BUILD=false
FASE="tudo"
DRY_RUN=false
EXTRA_SERVICES=()

usage() {
  sed -n '2,14p' "$0"
  echo ""
  echo "Fases:"
  echo "  core   — postgres, keycloak, core-api, api-delpi, portal, gateway"
  echo "  remote — plugin-ui (remote Module Federation — antes dos MFEs)"
  echo "  mfe    — MFEs federados (profile plugins)"
  echo "  api    — APIs de plugin (profile plugins)"
  echo "  chat   — ollama + minha-delpi-ai-api + minha-delpi-chat (sem LanguageTool/SearXNG)"
  echo "  tudo   — core → remote → mfe → api → chat (padrão)"
  echo ""
  echo "Opções:"
  echo "  --build       Rebuild da imagem de cada serviço (compose build isolado; ordem via --fase)"
  echo "  --fase FASE   Limita a uma fase (ou tudo)"
  echo "  --list        Lista ordem de subida e sai"
  echo "  --dry-run     Só imprime os comandos"
  echo "  SERVICO ...   Após --fase, restringe à lista (ex.: --fase mfe controle-retrabalhos)"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build) BUILD=true; shift ;;
    --fase) FASE="${2:?}"; shift 2 ;;
    --list)
      FASE="list"
      shift
      ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; EXTRA_SERVICES+=("$@"); break ;;
    -*) echo "Opção desconhecida: $1" >&2; usage >&2; exit 1 ;;
    *) EXTRA_SERVICES+=("$1"); shift ;;
  esac
done

# Ordem canônica — plugin-ui sempre antes dos MFEs federados.
FASE_CORE=(
  postgres-core
  keycloak-db
  postgres-plugins
  keycloak
  core-api
  api-delpi
  portal
  gateway
)

FASE_REMOTE=(plugin-ui)

FASE_MFE=(
  controle-retrabalhos
  dashboard-commercial
  dashboard-engineering
  dashboard-financial
  dashboard-hr
  dashboard-lmps
  dashboard-production
  dashboard-quality
  dashboard-supplies
  transformometro
  quality-action-plans
  cadastro-kaizen
  maintenance
  eficiencia-fabril
  minha-delpi-chat
  auditoria-5s
  inspecoes-entrada
  pedidos-venda-abertos
  propostas-comerciais
  financeiro-centro-custo
  strategic-indicators
  customer-experience
  cultura-delpi
  central-agendamento
  quality-labels
  tv-dashboard
  public-hub
  api-delpi-console
)

FASE_API=(
  strategic-indicators-api
  transformometro-api
  maintenance-api
  customer-experience-api
  tv-dashboard-api
)

FASE_CHAT=(
  ollama
  minha-delpi-ai-api
  minha-delpi-chat
)

PLUGIN_PROFILE_SERVICES=(
  "${FASE_REMOTE[@]}"
  "${FASE_MFE[@]}"
  "${FASE_API[@]}"
)

is_plugin_profile_service() {
  local svc="$1"
  local name
  for name in "${PLUGIN_PROFILE_SERVICES[@]}"; do
    if [[ "$name" == "$svc" ]]; then
      return 0
    fi
  done
  return 1
}

is_chat_profile_service() {
  local svc="$1"
  case "$svc" in
    ollama|minha-delpi-ai-api|minha-delpi-chat|searxng|languagetool) return 0 ;;
    *) return 1 ;;
  esac
}

compose_for() {
  local svc="$1"
  if is_plugin_profile_service "$svc"; then
    echo plugins
  elif is_chat_profile_service "$svc"; then
    echo chat
  else
    echo base
  fi
}

filter_services() {
  local -n src=$1
  local -a out=()
  if [[ ${#EXTRA_SERVICES[@]} -eq 0 ]]; then
    out=("${src[@]}")
  else
    local name want
    for want in "${EXTRA_SERVICES[@]}"; do
      for name in "${src[@]}"; do
        if [[ "$name" == "$want" ]]; then
          out+=("$name")
        fi
      done
    done
    if [[ ${#out[@]} -eq 0 ]]; then
      echo "Nenhum serviço da lista bate com: ${EXTRA_SERVICES[*]}" >&2
      exit 1
    fi
  fi
  printf '%s\n' "${out[@]}"
}

build_plan() {
  local -a plan=()
  case "$FASE" in
    core)
      mapfile -t plan < <(filter_services FASE_CORE)
      ;;
    remote)
      mapfile -t plan < <(filter_services FASE_REMOTE)
      ;;
    mfe)
      mapfile -t plan < <(filter_services FASE_MFE)
      ;;
    api)
      mapfile -t plan < <(filter_services FASE_API)
      ;;
    chat)
      mapfile -t plan < <(filter_services FASE_CHAT)
      ;;
    tudo)
      if [[ ${#EXTRA_SERVICES[@]} -gt 0 ]]; then
        echo "Com serviços extras, use --fase core|remote|mfe|api|chat (não 'tudo')." >&2
        exit 1
      fi
      mapfile -t plan < <(
        filter_services FASE_CORE
        filter_services FASE_REMOTE
        filter_services FASE_MFE
        filter_services FASE_API
        filter_services FASE_CHAT
      )
      ;;
    *)
      echo "Fase inválida: $FASE (use core|remote|mfe|api|chat|tudo|list)" >&2
      exit 1
      ;;
  esac
  printf '%s\n' "${plan[@]}"
}

if [[ "$FASE" == "list" ]]; then
  echo "=== Fase core ==="
  printf '  %s\n' "${FASE_CORE[@]}"
  echo "=== Fase remote ==="
  printf '  %s\n' "${FASE_REMOTE[@]}"
  echo "=== Fase mfe ==="
  printf '  %s\n' "${FASE_MFE[@]}"
  echo "=== Fase api ==="
  printf '  %s\n' "${FASE_API[@]}"
  echo "=== Fase chat ==="
  printf '  %s\n' "${FASE_CHAT[@]}"
  exit 0
fi

wait_pg() {
  local container="$1" user="$2" db="$3"
  echo "  Aguardando $container..."
  for _ in $(seq 1 60); do
    if docker exec "$container" pg_isready -U "$user" -d "$db" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Timeout aguardando $container" >&2
  exit 1
}

run_compose_up() {
  local svc="$1"
  local profile
  profile="$(compose_for "$svc")"
  local -a cmd
  case "$profile" in
    plugins) cmd=("${COMPOSE_PLUGINS[@]}") ;;
    chat) cmd=("${COMPOSE_CHAT[@]}") ;;
    *) cmd=("${COMPOSE_BASE[@]}") ;;
  esac

  if [[ "$BUILD" == true ]]; then
    local -a build_cmd=("${cmd[@]}" build "$svc")
    if [[ "$DRY_RUN" == true ]]; then
      echo "  [dry-run] ${build_cmd[*]}"
    else
      "${build_cmd[@]}"
    fi
  fi

  cmd+=(up -d --no-deps "$svc")

  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] ${cmd[*]}"
    return 0
  fi

  "${cmd[@]}"
}

mapfile -t PLAN < <(build_plan)
TOTAL=${#PLAN[@]}

if [[ "$TOTAL" -eq 0 ]]; then
  echo "Nada a subir." >&2
  exit 0
fi

echo "=== DELPI dev sequencial — $TOTAL serviço(s), build=$BUILD, fase=$FASE ==="
echo "COMPOSE_PARALLEL_LIMIT=$COMPOSE_PARALLEL_LIMIT"
echo ""

idx=0
for svc in "${PLAN[@]}"; do
  idx=$((idx + 1))
  echo ">>> [$idx/$TOTAL] $svc"
  run_compose_up "$svc"

  case "$svc" in
    postgres-core) wait_pg delpi-postgres-core delpi delpi_core ;;
    keycloak-db) wait_pg delpi-keycloak-db keycloak keycloak ;;
    postgres-plugins) wait_pg delpi-postgres-plugins plugins_user plugins_hub ;;
  esac

  # Pequena pausa — libera cache de build antes do próximo npm run build.
  if [[ "$BUILD" == true ]]; then
    sleep 2
  fi
done

echo ""
echo "=== Concluído ==="
echo "Portal:     http://localhost"
echo "Remote MF:  http://localhost/apps/plugin-ui/assets/remoteEntry.js"
echo ""
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep delpi | head -20 || true
if [[ $(docker ps --filter name=delpi- -q | wc -l) -gt 20 ]]; then
  echo "... ($(docker ps --filter name=delpi- -q | wc -l) containers delpi-* no total)"
fi
