#!/usr/bin/env bash
# Sobe ou reconstrói containers DELPI **homologação (delpi-hml)** um por vez —
# espelho operacional de up-prod-sequential.sh, limitado aos serviços do
# docker-compose.hml.yml (inventário fechado atual).
#
# Uso (a partir da raiz do repositório):
#   ./infra/scripts/up-hml-sequential.sh --list
#   ./infra/scripts/up-hml-sequential.sh --pull --build
#   ./infra/scripts/up-hml-sequential.sh --fase core --build
#   ./infra/scripts/up-hml-sequential.sh --fase remote --build plugin-ui
#   ./infra/scripts/up-hml-sequential.sh --fase mfe --build my-requests engineering
#   ./infra/scripts/up-hml-sequential.sh --fase api --build engineering-api requests-api
#   ./infra/scripts/up-hml-sequential.sh --build '*-api'
#   ./infra/scripts/up-hml-sequential.sh --no-cache --build engineering
#   ./infra/scripts/up-hml-sequential.sh --dry-run --fase api engineering-api
#
# Pré-requisito: checkout HML com infra/.env.hml (cp infra/env.hml.example).
# Primeira ativação gated (TLS/bootstrap/scenarios): ./infra/scripts/hml-compose.sh
#
# Doc: infra/README-ambiente.md § Inicialização segura de containers

set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$COMPOSE_DIR/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=compose-filter-services.sh
source "$SCRIPT_DIR/compose-filter-services.sh"

PROJECT="delpi-hml"
COMPOSE_FILE="docker-compose.hml.yml"
ENV_FILE=".env.hml"
HEALTH_TIMEOUT_SEC="${DELPI_HML_HEALTH_TIMEOUT_SEC:-300}"

BUILD=false
NO_CACHE=false
FASE="tudo"
DRY_RUN=false
GIT_PULL=false
SKIP_PROVISION=false
EXTRA_SERVICES=()

# Ordem canônica = inventário atual de docker-compose.hml.yml (16 serviços).
FASE_CORE=(
  postgres-core
  keycloak-db
  postgres-plugins
  delpi-redis
  keycloak
  core-api
  api-delpi
  portal
  gateway
)
FASE_REMOTE=(plugin-ui)
FASE_MFE=(
  production-control
  my-requests
  engineering
)
FASE_API=(
  production-control-api
  requests-api
  engineering-api
)

# União ordenada (core → remote → mfe → api) — fonte única para --list / validação.
HML_ALL_SERVICES=(
  "${FASE_CORE[@]}"
  "${FASE_REMOTE[@]}"
  "${FASE_MFE[@]}"
  "${FASE_API[@]}"
)

usage() {
  sed -n '2,22p' "$0"
  echo ""
  echo "Fases (somente serviços definidos em docker-compose.hml.yml):"
  echo "  core   — postgres*, redis, keycloak, core-api, api-delpi, portal, gateway"
  echo "  remote — plugin-ui (Module Federation — antes dos MFEs)"
  echo "  mfe    — production-control, my-requests, engineering"
  echo "  api    — production-control-api, requests-api, engineering-api"
  echo "  tudo   — core → remote → mfe → api (padrão)"
  echo ""
  echo "Opções:"
  echo "  --build          Rebuild isolado de cada serviço (compose build; sem bake em cascata)"
  echo "  --no-cache       Passa --no-cache ao docker compose build"
  echo "  --pull           git pull --ff-only no checkout antes de subir"
  echo "  --fase FASE      Limita a uma fase (opcional se passar SERVICO)"
  echo "  --list           Lista ordem e sai"
  echo "  --dry-run        Só imprime comandos"
  echo "  --skip-provision Não roda hooks (dirs/eng_prc) antes de requests-api/engineering-api"
  echo "  SERVICO ...      Filtra por nome/glob ('*-api', 'my-*'); --fase não é obrigatório"
  echo ""
  echo "Compose: docker-compose.hml.yml + .env.hml + project delpi-hml (rede delpi-hml-network)"
  echo "Sempre: up -d --no-deps + COMPOSE_PARALLEL_LIMIT=1"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build) BUILD=true; shift ;;
    --no-cache) NO_CACHE=true; shift ;;
    --pull) GIT_PULL=true; shift ;;
    --fase) FASE="${2:?}"; shift 2 ;;
    --list) FASE="list"; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --skip-provision) SKIP_PROVISION=true; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; EXTRA_SERVICES+=("$@"); break ;;
    -*) echo "Opção desconhecida: $1" >&2; usage >&2; exit 1 ;;
    *) EXTRA_SERVICES+=("$1"); shift ;;
  esac
done

cd "$COMPOSE_DIR"

compose_profiles_for() {
  local svc="$1"
  case "$svc" in
    postgres-core|keycloak-db|postgres-plugins) echo databases ;;
    delpi-redis) echo redis ;;
    keycloak) echo keycloak ;;
    core-api) echo core-api ;;
    api-delpi) echo api-delpi ;;
    portal) echo portal ;;
    plugin-ui) echo plugin-ui ;;
    production-control-api) echo production-control-api ;;
    production-control) echo production-control-ui ;;
    requests-api) echo requests-api ;;
    my-requests) echo my-requests ;;
    engineering-api) echo engineering-api ;;
    engineering) echo engineering ;;
    gateway) echo gateway ;;
    *)
      echo "Serviço HML sem profile mapeado: $svc" >&2
      exit 1
      ;;
  esac
}

hml_container_name() {
  local svc="$1"
  case "$svc" in
    delpi-redis) echo delpi-hml-redis ;;
    *) echo "delpi-hml-${svc}" ;;
  esac
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
    core) append_filtered_phase FASE_CORE plan ;;
    remote) append_filtered_phase FASE_REMOTE plan ;;
    mfe) append_filtered_phase FASE_MFE plan ;;
    api) append_filtered_phase FASE_API plan ;;
    tudo|auto)
      if [[ ${#EXTRA_SERVICES[@]} -gt 0 ]]; then
        COMPOSE_FILTER_ALLOW_EMPTY=1
        append_filtered_phase FASE_CORE plan
        append_filtered_phase FASE_REMOTE plan
        append_filtered_phase FASE_MFE plan
        append_filtered_phase FASE_API plan
        unset COMPOSE_FILTER_ALLOW_EMPTY
        if [[ ${#plan[@]} -eq 0 ]]; then
          echo "Nenhum serviço HML bate com: ${EXTRA_SERVICES[*]}" >&2
          echo "Dica: use aspas nos padrões glob (ex.: '*-api', 'my-*')." >&2
          echo "Serviços atuais: ${HML_ALL_SERVICES[*]}" >&2
          exit 1
        fi
      else
        if [[ "$FASE" == "auto" ]]; then
          echo "Fase auto exige nome ou glob de serviço (ex.: --build '*-api')." >&2
          exit 1
        fi
        plan+=("${HML_ALL_SERVICES[@]}")
      fi
      ;;
    *)
      echo "Fase inválida: $FASE (use core|remote|mfe|api|tudo)" >&2
      exit 1
      ;;
  esac
  compose_dedupe_services "${plan[@]}"
}

assert_hml_identity() {
  local name_line
  name_line="$(grep -E '^name:[[:space:]]*' "$COMPOSE_DIR/$COMPOSE_FILE" | head -n 1)"
  if [[ "$name_line" != "name: ${PROJECT}" ]]; then
    echo "[ERRO] Compose HML sem name: ${PROJECT}. Abortado." >&2
    exit 1
  fi
  if [[ ! -f "$COMPOSE_DIR/$ENV_FILE" ]]; then
    if [[ "$DRY_RUN" == true && -f "$COMPOSE_DIR/env.hml.example" ]]; then
      ENV_FILE="env.hml.example"
      echo "[AVISO] .env.hml ausente — dry-run usando env.hml.example" >&2
    else
      echo "[ERRO] $COMPOSE_DIR/$ENV_FILE ausente. Copie infra/env.hml.example → infra/.env.hml" >&2
      exit 1
    fi
  fi
  if grep -Eiq 'minhadelpi\.com\.br' "$COMPOSE_DIR/$ENV_FILE"; then
    echo "[ERRO] $ENV_FILE referencia domínio produtivo. STOP." >&2
    exit 1
  fi
}

# Garante que fases cobrem exatamente os serviços do compose HML (drift = falha).
assert_catalog_matches_compose() {
  local -a compose_svcs=()
  local line svc missing extra
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    compose_svcs+=("$line")
  done < <(
    awk '
      /^services:[[:space:]]*$/ { in_svc=1; next }
      in_svc && /^[^[:space:]#]/ { exit }
      in_svc && /^  [a-zA-Z0-9_-]+:[[:space:]]*$/ {
        name=$1; sub(/:$/, "", name); print name
      }
    ' "$COMPOSE_DIR/$COMPOSE_FILE"
  )

  declare -A known=()
  for svc in "${HML_ALL_SERVICES[@]}"; do
    known["$svc"]=1
  done

  missing=""
  for svc in "${compose_svcs[@]}"; do
    if [[ -z "${known[$svc]:-}" ]]; then
      missing+="$svc"$'\n'
    fi
  done
  if [[ -n "$missing" ]]; then
    echo "[ERRO] docker-compose.hml.yml tem serviços fora de up-hml-sequential.sh:" >&2
    printf '%s' "$missing" >&2
    echo "Atualize FASE_* em infra/scripts/up-hml-sequential.sh." >&2
    exit 1
  fi

  declare -A in_compose=()
  for svc in "${compose_svcs[@]}"; do
    in_compose["$svc"]=1
  done
  extra=""
  for svc in "${HML_ALL_SERVICES[@]}"; do
    if [[ -z "${in_compose[$svc]:-}" ]]; then
      extra+="$svc"$'\n'
    fi
  done
  if [[ -n "$extra" ]]; then
    echo "[ERRO] up-hml-sequential.sh lista serviços ausentes no compose HML:" >&2
    printf '%s' "$extra" >&2
    exit 1
  fi
}

ensure_hml_data_dirs() {
  local -a dirs=("$@")
  local d need_docker=false
  mkdir -p "${dirs[@]}" 2>/dev/null || true
  for d in "${dirs[@]}"; do
    if [[ ! -d "$d" ]]; then
      need_docker=true
      break
    fi
  done
  if [[ "$need_docker" == true ]]; then
    docker run --rm -v "$COMPOSE_DIR/hml-data:/data" alpine:3.20 \
      sh -c 'mkdir -p /data/my-requests-attachments /data/my-requests-artifacts /data/prc-attachments /data/ocr-models && chmod 777 /data/my-requests-attachments /data/my-requests-artifacts /data/prc-attachments /data/ocr-models' \
      >/dev/null
  fi
}

assert_hml_tls_certs() {
  local crt="$COMPOSE_DIR/hml-certs/hml-gateway.crt"
  local key="$COMPOSE_DIR/hml-certs/hml-gateway.key"
  if [[ ! -f "$crt" || ! -f "$key" ]]; then
    echo "[ERRO] certs TLS HML ausentes. Rode ./infra/scripts/hml-tls-prepare.sh" >&2
    exit 1
  fi
}

pre_up_hooks() {
  local svc="$1"
  [[ "$SKIP_PROVISION" == true ]] && return 0
  case "$svc" in
    gateway)
      assert_hml_tls_certs
      ;;
    requests-api)
      ensure_hml_data_dirs \
        "$COMPOSE_DIR/hml-data/my-requests-attachments" \
        "$COMPOSE_DIR/hml-data/my-requests-artifacts"
      ;;
    engineering-api)
      ensure_hml_data_dirs \
        "$COMPOSE_DIR/hml-data/prc-attachments" \
        "$COMPOSE_DIR/hml-data/ocr-models"
      if [[ "$DRY_RUN" == true ]]; then
        echo "  [dry-run] bash $SCRIPT_DIR/hml-provision-eng-prc.sh $COMPOSE_DIR/$ENV_FILE"
      else
        bash "$SCRIPT_DIR/hml-provision-eng-prc.sh" "$COMPOSE_DIR/$ENV_FILE"
      fi
      ;;
  esac
}

compose_cmd_base() {
  local profile="$1"
  printf '%s\n' docker compose \
    --project-name "$PROJECT" \
    --project-directory "$COMPOSE_DIR" \
    -f "$COMPOSE_FILE" \
    --env-file "$ENV_FILE" \
    --profile "$profile"
}

run_compose_up() {
  local svc="$1"
  local profile
  profile="$(compose_profiles_for "$svc")"
  mapfile -t base < <(compose_cmd_base "$profile")
  local -a cmd=("${base[@]}")

  pre_up_hooks "$svc"

  if [[ "$BUILD" == true ]]; then
    local -a build_cmd=("${cmd[@]}" build "$svc")
    if [[ "$NO_CACHE" == true ]]; then
      build_cmd+=(--no-cache)
    fi
    if [[ "$DRY_RUN" == true ]]; then
      echo "  [dry-run] ${build_cmd[*]}"
    else
      (
        cd "$COMPOSE_DIR"
        env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME "${build_cmd[@]}"
      )
    fi
  fi

  cmd+=(up -d --no-deps "$svc")
  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] ${cmd[*]}"
    return 0
  fi
  (
    cd "$COMPOSE_DIR"
    env -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME "${cmd[@]}"
  )
}

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

wait_healthy_optional() {
  local svc="$1"
  local cname
  cname="$(hml_container_name "$svc")"
  local has_health
  has_health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$cname" 2>/dev/null || true)"
  [[ -z "$has_health" ]] && return 0
  echo "  Aguardando health de $cname (timeout ${HEALTH_TIMEOUT_SEC}s)..."
  local deadline=$((SECONDS + HEALTH_TIMEOUT_SEC))
  local st
  while (( SECONDS < deadline )); do
    st="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cname" 2>/dev/null || echo missing)"
    if [[ "$st" == "healthy" ]]; then
      echo "  HEALTH=$svc:healthy"
      return 0
    fi
    if [[ "$st" == "none" ]]; then
      return 0
    fi
    sleep 2
  done
  echo "Timeout aguardando health de $cname (último=$st)" >&2
  exit 1
}

if [[ "$FASE" == "list" ]]; then
  assert_catalog_matches_compose
  echo "=== HML fase core ==="
  printf '  %s\n' "${FASE_CORE[@]}"
  echo "=== HML fase remote ==="
  printf '  %s\n' "${FASE_REMOTE[@]}"
  echo "=== HML fase mfe ==="
  printf '  %s\n' "${FASE_MFE[@]}"
  echo "=== HML fase api ==="
  printf '  %s\n' "${FASE_API[@]}"
  echo "=== total ${#HML_ALL_SERVICES[@]} serviços (docker-compose.hml.yml) ==="
  exit 0
fi

if [[ ${#EXTRA_SERVICES[@]} -gt 0 && "$FASE" == "tudo" ]]; then
  FASE="auto"
fi

assert_hml_identity
assert_catalog_matches_compose

if [[ "$GIT_PULL" == true ]]; then
  echo "=== git pull --ff-only ($REPO_ROOT) ==="
  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] git -C $REPO_ROOT pull --ff-only"
  else
    git -C "$REPO_ROOT" pull --ff-only
  fi
  echo ""
fi

export COMPOSE_PARALLEL_LIMIT=1
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export SOURCE_REVISION="${SOURCE_REVISION:-$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo hml)}"

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

echo "=== DELPI HML sequencial — $TOTAL serviço(s) ==="
echo "project=$PROJECT compose=$COMPOSE_FILE env=$ENV_FILE"
echo "build=$BUILD fase=$FASE skip_provision=$SKIP_PROVISION"
echo "COMPOSE_PARALLEL_LIMIT=$COMPOSE_PARALLEL_LIMIT"
echo ""

idx=0
for svc in "${PLAN[@]}"; do
  idx=$((idx + 1))
  echo ">>> [$idx/$TOTAL] $svc (profile=$(compose_profiles_for "$svc"))"
  run_compose_up "$svc"

  if [[ "$DRY_RUN" == true ]]; then
    continue
  fi

  case "$svc" in
    postgres-core) wait_pg delpi-hml-postgres-core "${POSTGRES_CORE_USER:-delpi}" "${POSTGRES_CORE_DB:-delpi_core}" ;;
    keycloak-db) wait_pg delpi-hml-keycloak-db "${POSTGRES_KC_USER:-keycloak}" "${POSTGRES_KC_DB:-keycloak}" ;;
    postgres-plugins) wait_pg delpi-hml-postgres-plugins "${PLUGINS_DB_USER:-plugins_user}" "${PLUGINS_DB_NAME:-plugins_hub}" ;;
    *) wait_healthy_optional "$svc" ;;
  esac

  if [[ "$BUILD" == true ]]; then
    sleep 2
  fi
done

echo ""
echo "=== Concluído (HML) ==="
PUBLIC_ORIGIN="$(grep -E '^DELPI_HML_PUBLIC_ORIGIN=' "$ENV_FILE" | head -1 | cut -d= -f2- || true)"
PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-https://192.168.1.237:18443}"
echo "Portal HML: ${PUBLIC_ORIGIN}/"
if [[ "$DRY_RUN" == true ]]; then
  echo "(dry-run — containers não alterados)"
  exit 0
fi
echo "Containers delpi-hml-*:"
docker ps --filter name=delpi-hml --format 'table {{.Names}}\t{{.Status}}' || true
echo "total=$(docker ps --filter name=delpi-hml -q | wc -l)"
