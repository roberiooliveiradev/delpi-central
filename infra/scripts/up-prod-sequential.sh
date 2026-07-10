#!/usr/bin/env bash
# Sobe ou reconstrói containers DELPI **produção** um por vez — evita OOM no build.
#
# Uso (a partir de qualquer pasta):
#   ./infra/scripts/up-prod-sequential.sh --list
#   ./infra/scripts/up-prod-sequential.sh --pull --build
#   ./infra/scripts/up-prod-sequential.sh --fase core --build
#   ./infra/scripts/up-prod-sequential.sh --fase remote --build plugin-ui
#   ./infra/scripts/up-prod-sequential.sh --fase mfe --build minha-delpi-chat controle-retrabalhos
#   ./infra/scripts/up-prod-sequential.sh --cpu --fase chat --build
#   ./infra/scripts/up-prod-sequential.sh --heavy --build languagetool searxng
#
# Pré-requisito: infra/.env (cp infra/.env.prod.example infra/.env)
#
# Doc: infra/README-ambiente.md § Inicialização segura de containers

set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$COMPOSE_DIR/.." && pwd)"
cd "$COMPOSE_DIR"

BUILD=false
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
  echo "  mfe    — microfrontends federados"
  echo "  api    — APIs de plugin (transformometro-api, …)"
  echo "  chat   — ollama + minha-delpi-ai-api"
  echo "  heavy  — searxng + languagetool (~2,5 GB RAM extra)"
  echo "  gpu    — vllm (profile gpu)"
  echo "  tudo   — core → chat(ollama) → remote → mfe → api → gateway já em core (padrão)"
  echo ""
  echo "Opções:"
  echo "  --build       Rebuild de cada imagem antes de subir"
  echo "  --pull        git pull em $REPO_ROOT antes de subir"
  echo "  --cpu         Usa docker-compose.prod.cpu.yml (LanguageTool/SearXNG em optional-heavy)"
  echo "  --heavy       Inclui fase heavy (ou serviços searxng/languagetool)"
  echo "  --gpu         Inclui vllm (profile gpu)"
  echo "  --fase FASE   Limita a uma fase"
  echo "  --list        Lista ordem e sai"
  echo "  --dry-run     Só imprime comandos"
  echo "  SERVICO ...   Restringe à lista (com --fase; não use com tudo)"
  echo ""
  echo "Compose: docker-compose.yml + .env (+ prod.cpu.yml se --cpu)"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build) BUILD=true; shift ;;
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

FASE_CHAT=(
  ollama
  minha-delpi-ai-api
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

FASE_HEAVY=(
  searxng
  languagetool
)

FASE_GPU=(vllm)

compose_cmd() {
  if [[ "$USE_CPU" == true ]]; then
    printf '%s\n' docker compose -f docker-compose.yml -f docker-compose.prod.cpu.yml --env-file .env
  else
    printf '%s\n' docker compose -f docker-compose.yml --env-file .env
  fi
}

compose_profiles_for() {
  local svc="$1"
  case "$svc" in
    vllm) echo gpu ;;
    searxng|languagetool)
      if [[ "$USE_CPU" == true ]]; then
        echo optional-heavy
      fi
      ;;
  esac
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
    core) mapfile -t plan < <(filter_services FASE_CORE) ;;
    remote) mapfile -t plan < <(filter_services FASE_REMOTE) ;;
    mfe) mapfile -t plan < <(filter_services FASE_MFE) ;;
    api) mapfile -t plan < <(filter_services FASE_API) ;;
    chat) mapfile -t plan < <(filter_services FASE_CHAT) ;;
    heavy) mapfile -t plan < <(filter_services FASE_HEAVY) ;;
    gpu) mapfile -t plan < <(filter_services FASE_GPU) ;;
    tudo)
      if [[ ${#EXTRA_SERVICES[@]} -gt 0 ]]; then
        echo "Com serviços extras, use --fase (não 'tudo')." >&2
        exit 1
      fi
      mapfile -t plan < <(
        filter_services FASE_CORE
        filter_services FASE_CHAT
        filter_services FASE_REMOTE
        filter_services FASE_MFE
        filter_services FASE_API
      )
      if [[ "$INCLUDE_HEAVY" == true ]]; then
        plan+=("${FASE_HEAVY[@]}")
      fi
      if [[ "$INCLUDE_GPU" == true ]]; then
        plan+=("${FASE_GPU[@]}")
      fi
      ;;
    *)
      echo "Fase inválida: $FASE" >&2
      exit 1
      ;;
  esac
  printf '%s\n' "${plan[@]}"
}

if [[ "$FASE" == "list" ]]; then
  echo "=== Fase core ==="
  printf '  %s\n' "${FASE_CORE[@]}"
  echo "=== Fase chat ==="
  printf '  %s\n' "${FASE_CHAT[@]}"
  echo "=== Fase remote ==="
  printf '  %s\n' "${FASE_REMOTE[@]}"
  echo "=== Fase mfe ==="
  printf '  %s\n' "${FASE_MFE[@]}"
  echo "=== Fase api ==="
  printf '  %s\n' "${FASE_API[@]}"
  echo "=== Fase heavy (--heavy) ==="
  printf '  %s\n' "${FASE_HEAVY[@]}"
  echo "=== Fase gpu (--gpu) ==="
  printf '  %s\n' "${FASE_GPU[@]}"
  exit 0
fi

if [[ ! -f .env ]]; then
  echo "Arquivo infra/.env ausente. Copie infra/.env.prod.example → infra/.env" >&2
  exit 1
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

export COMPOSE_PARALLEL_LIMIT=1
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

wait_pg() {
  local container="$1" user="$2" db="$3"
  echo "  Aguardando $container..."
  for _ in $(seq 1 90); do
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
  mapfile -t base < <(compose_cmd)
  local -a cmd=("${base[@]}")
  local profile
  profile="$(compose_profiles_for "$svc")"
  if [[ -n "$profile" ]]; then
    cmd+=(--profile "$profile")
  fi
  cmd+=(up -d)
  if [[ "$BUILD" == true ]]; then
    cmd+=(--build)
  fi
  cmd+=("$svc")

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

echo "=== DELPI produção sequencial — $TOTAL serviço(s) ==="
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

  if [[ "$BUILD" == true ]]; then
    sleep 2
  fi
done

PUBLIC_URL="${PUBLIC_BASE_URL:-https://localhost}"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set +u
  # shellcheck disable=SC1091
  source .env 2>/dev/null || true
  set -u
  PUBLIC_URL="${PUBLIC_BASE_URL:-$PUBLIC_URL}"
fi

echo ""
echo "=== Concluído ==="
echo "Portal:     ${PUBLIC_URL}/"
echo "Remote MF:  ${PUBLIC_URL}/apps/plugin-ui/assets/remoteEntry.js"
echo ""
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep delpi | head -20 || true
total="$(docker ps --filter name=delpi- -q | wc -l)"
if [[ "$total" -gt 20 ]]; then
  echo "... ($total containers delpi-* no total)"
fi
