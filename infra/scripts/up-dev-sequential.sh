#!/usr/bin/env bash
# Sobe ou reconstrói containers DELPI dev **um por vez** — evita OOM no WSL (~8 GB).
#
# Uso (a partir de qualquer pasta):
#   ./infra/scripts/up-dev-sequential.sh --list
#   ./infra/scripts/up-dev-sequential.sh --pull --build
#   ./infra/scripts/up-dev-sequential.sh --fase core --build
#   ./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
#   ./infra/scripts/up-dev-sequential.sh --fase mfe --build minha-delpi-chat controle-retrabalhos
#   ./infra/scripts/up-dev-sequential.sh --build 'minha*'
#   ./infra/scripts/up-dev-sequential.sh --no-cache --fase mfe --build 'dashboard-*'
#   ./infra/scripts/up-dev-sequential.sh --no-cache --fase mfe --build '*-production'
#   ./infra/scripts/up-dev-sequential.sh --fase chat --build
#   ./infra/scripts/up-dev-sequential.sh --heavy --build languagetool searxng
#
# Pré-requisito: infra/.env (cp infra/.env.dev.example infra/.env)
#
# Doc: infra/README-ambiente.md § Inicialização segura de containers

set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$COMPOSE_DIR/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=compose-filter-services.sh
source "$SCRIPT_DIR/compose-filter-services.sh"
cd "$COMPOSE_DIR"

COMPOSE_BASE=(docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml --env-file .env)
COMPOSE_PLUGINS=(docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml --profile plugins --env-file .env)
COMPOSE_CHAT=(docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml --profile chat --env-file .env)

export COMPOSE_PARALLEL_LIMIT=1
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export SOURCE_REVISION="${SOURCE_REVISION:-$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo dev)}"

BUILD=false
NO_CACHE=false
FASE="tudo"
DRY_RUN=false
GIT_PULL=false
USE_CPU=false
INCLUDE_HEAVY=false
INCLUDE_GPU=false
EXTRA_SERVICES=()

usage() {
  sed -n '2,15p' "$0"
  echo ""
  echo "Fases:"
  echo "  core   — postgres, keycloak, core-api, api-delpi, portal, gateway"
  echo "  remote — plugin-ui (Module Federation — antes dos MFEs)"
  echo "  mfe    — microfrontends federados (profile plugins)"
  echo "  api    — APIs de plugin (profile plugins)"
  echo "  chat   — ollama + minha-delpi-ai-api + minha-delpi-chat"
  echo "  heavy  — searxng + languagetool (profile chat; ~2,5 GB RAM extra)"
  echo "  gpu    — indisponível em dev (vllm só em produção)"
  echo "  tudo   — core → remote → mfe → api → chat (padrão)"
  echo ""
  echo "Opções:"
  echo "  --build       Rebuild da imagem de cada serviço (compose build isolado; sem bake em cascata)"
  echo "  --no-cache    Passa --no-cache ao docker compose build (evita layer CACHED stale no MFE)"
  echo "  --pull        git pull em $REPO_ROOT antes de subir"
  echo "  --cpu         No-op em dev (já usa docker-compose.minimal.yml por padrão)"
  echo "  --heavy       Inclui fase heavy (ou serviços searxng/languagetool)"
  echo "  --gpu         Indisponível em dev — use up-prod-sequential.sh para vllm"
  echo "  --fase FASE   Limita a uma fase (opcional se passar SERVICO)"
  echo "  --list        Lista ordem e sai"
  echo "  --dry-run     Só imprime comandos"
  echo "  SERVICO ...   Filtra por nome/glob ('minha*', 'dashboard-*'); --fase não é obrigatório"
  echo ""
  echo "Compose: docker-compose.dev.yml + docker-compose.minimal.yml + .env"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build) BUILD=true; shift ;;
    --no-cache) NO_CACHE=true; shift ;;
    --pull) GIT_PULL=true; shift ;;
    --cpu) USE_CPU=true; shift ;;
    --heavy) INCLUDE_HEAVY=true; shift ;;
    --gpu) INCLUDE_GPU=true; shift ;;
    --fase) FASE="${2:?}"; shift 2 ;;
    --list) FASE="list"; shift ;;
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
  scrap-monitoring
  production-appointments
  dashboard-commercial
  dashboard-engineering
  dashboard-financial
  dashboard-hr
  dashboard-lmps
  dashboard-production
  dashboard-quality
  dashboard-supplies
  estoque-seguranca
  transformometro
  quality-action-plans
  cadastro-kaizen
  maintenance
  eficiencia-fabril
  minha-delpi-chat
  auditoria-5s
  inspecoes-entrada
  inspecoes-processo
  pedidos-venda-abertos
  propostas-comerciais
  financeiro-centro-custo
  financeiro-inadimplencia
  strategic-indicators
  customer-experience
  cultura-delpi
  codigo-etica
  guias-procedimentos
  central-agendamento
  canal-denuncia
  reports
  cipa
  quality-labels
  tv-dashboard
  public-hub
  api-delpi-console
)

FASE_API=(
  strategic-indicators-api
  transformometro-api
  maintenance-api
  cipa-api
  customer-experience-api
  tv-dashboard-api
)

FASE_CHAT=(
  ollama
  minha-delpi-ai-api
  minha-delpi-chat
)

FASE_HEAVY=(
  searxng
  languagetool
)

FASE_GPU=(vllm)

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

append_filtered_phase() {
  local -n phase_arr=$1
  local -a plan_ref=()
  local -n plan_out=$2
  local output
  output="$(compose_filter_phase_services "${phase_arr[@]}")" || exit 1
  if [[ -n "$output" ]]; then
    mapfile -t plan_ref <<< "$output"
    plan_out+=("${plan_ref[@]}")
  fi
}

build_plan() {
  local -a plan=()
  case "$FASE" in
    core)
      append_filtered_phase FASE_CORE plan
      ;;
    remote)
      append_filtered_phase FASE_REMOTE plan
      ;;
    mfe)
      append_filtered_phase FASE_MFE plan
      ;;
    api)
      append_filtered_phase FASE_API plan
      ;;
    chat)
      append_filtered_phase FASE_CHAT plan
      ;;
    heavy)
      append_filtered_phase FASE_HEAVY plan
      ;;
    gpu)
      echo "Fase gpu (vllm) indisponível em dev — use up-prod-sequential.sh --gpu." >&2
      exit 1
      ;;
    tudo|auto)
      if [[ ${#EXTRA_SERVICES[@]} -gt 0 ]]; then
        # Sem --fase (ou fase auto): busca o filtro em todas as fases (ordem canônica).
        COMPOSE_FILTER_ALLOW_EMPTY=1
        append_filtered_phase FASE_CORE plan
        append_filtered_phase FASE_REMOTE plan
        append_filtered_phase FASE_MFE plan
        append_filtered_phase FASE_API plan
        append_filtered_phase FASE_CHAT plan
        if [[ "$INCLUDE_HEAVY" == true ]]; then
          append_filtered_phase FASE_HEAVY plan
        fi
        unset COMPOSE_FILTER_ALLOW_EMPTY
        if [[ ${#plan[@]} -eq 0 ]]; then
          echo "Nenhum serviço bate com: ${EXTRA_SERVICES[*]}" >&2
          echo "Dica: use aspas nos padrões glob (ex.: 'minha*', 'dashboard-*')." >&2
          echo "Ou limite com --fase (core|chat|remote|mfe|api|heavy)." >&2
          exit 1
        fi
      else
        if [[ "$FASE" == "auto" ]]; then
          echo "Fase auto exige nome ou glob de serviço (ex.: --build 'minha*')." >&2
          exit 1
        fi
        append_filtered_phase FASE_CORE plan
        append_filtered_phase FASE_REMOTE plan
        append_filtered_phase FASE_MFE plan
        append_filtered_phase FASE_API plan
        append_filtered_phase FASE_CHAT plan
        if [[ "$INCLUDE_HEAVY" == true ]]; then
          plan+=("${FASE_HEAVY[@]}")
        fi
        if [[ "$INCLUDE_GPU" == true ]]; then
          echo "Flag --gpu ignorada em dev (vllm só em produção)." >&2
        fi
      fi
      ;;
    *)
      echo "Fase inválida: $FASE (use core|remote|mfe|api|chat|heavy|tudo|list)" >&2
      exit 1
      ;;
  esac
  compose_dedupe_services "${plan[@]}"
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
  echo "=== Fase heavy (--heavy) ==="
  printf '  %s\n' "${FASE_HEAVY[@]}"
  echo "=== Fase gpu (só produção) ==="
  printf '  %s\n' "${FASE_GPU[@]}"
  exit 0
fi

# Serviço/glob sem --fase: varre todas as fases (chat + mfe + api + …).
if [[ ${#EXTRA_SERVICES[@]} -gt 0 && "$FASE" == "tudo" ]]; then
  FASE="auto"
fi

if [[ ! -f .env ]]; then
  echo "Arquivo infra/.env ausente. Copie infra/.env.dev.example → infra/.env" >&2
  exit 1
fi

if [[ "$USE_CPU" == true ]]; then
  echo "Nota: dev já usa docker-compose.minimal.yml (--cpu é equivalente ao padrão local)." >&2
fi

if [[ "$GIT_PULL" == true ]]; then
  echo "=== git pull ($REPO_ROOT) ==="
  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] git -C $REPO_ROOT pull"
  else
    git -C "$REPO_ROOT" pull
  fi
  echo ""
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
    if [[ "$NO_CACHE" == true ]]; then
      build_cmd+=(--no-cache)
    fi
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

plan_output="$(build_plan)" || exit 1
if [[ -z "$plan_output" ]]; then
  echo "Nada a subir." >&2
  exit 0
fi
mapfile -t PLAN <<< "$plan_output"
TOTAL=${#PLAN[@]}

if [[ "$TOTAL" -eq 0 ]]; then
  echo "Nada a subir." >&2
  exit 0
fi

echo "=== DELPI dev sequencial — $TOTAL serviço(s) ==="
echo "build=$BUILD fase=$FASE cpu=$USE_CPU heavy=$INCLUDE_HEAVY gpu=$INCLUDE_GPU"
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
