#!/usr/bin/env bash
# Manutenção DELPI — limpa caches regeneráveis sem apagar dados sensíveis.
#
# Uso (da raiz do repositório):
#   ./infra/scripts/maintenance-clean-cache.sh --list
#   ./infra/scripts/maintenance-clean-cache.sh --dry-run
#   ./infra/scripts/maintenance-clean-cache.sh --tier standard
#   ./infra/scripts/maintenance-clean-cache.sh --tier light --yes
#   ./infra/scripts/maintenance-clean-cache.sh --tier docker-deep --yes
#   ./infra/scripts/maintenance-clean-cache.sh --only drawing-library,query-cache
#
# Tiers:
#   light    — build cache Docker + imagens dangling + containers órfãos parados
#   standard — light + drawing-library-cache + rotação de logs api-delpi + restart query-cache
#   docker-deep — standard + imagens não usadas + builder prune completo
#
# Nunca toca: Postgres, Keycloak, Ollama (modelos), uploads/evidências em DELPI_DATA_HOST_DIR.
#
# Doc: infra/README-ambiente.md § Manutenção de cache

set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=maintenance-cache-manifest.sh
source "$SCRIPT_DIR/maintenance-cache-manifest.sh"

TIER="standard"
DRY_RUN=false
ASSUME_YES=false
ONLY_TARGETS=()
LOG_RETENTION_DAYS="${LOG_RETENTION_DAYS:-30}"
INCLUDE_VLLM_CACHE=false
API_DELPI_CONTAINER="${API_DELPI_CONTAINER:-delpi-api-delpi}"

usage() {
  sed -n '2,20p' "$0"
  echo ""
  echo "Opções:"
  echo "  --list              Mostra proteções e alvos por tier"
  echo "  --dry-run           Só imprime o que faria (sem alterar nada)"
  echo "  --tier TIER         light | standard (padrão) | docker-deep"
  echo "  --only A,B,C        Só estes alvos (ver --list)"
  echo "  --yes               Não pedir confirmação interativa"
  echo "  --include-vllm-cache  Inclui limpeza do volume vllm_cache (re-download HF)"
  echo "  --log-retention N   Dias de logs api-delpi a manter (padrão: ${LOG_RETENTION_DAYS})"
  echo ""
  echo "Alvos (--only): builder, dangling-images, unused-images, stopped-orphans,"
  echo "                drawing-library, query-cache, api-delpi-logs, vllm-huggingface"
}

log_info() { echo "[INFO] $*"; }
log_ok() { echo "[OK] $*"; }
log_warn() { echo "[AVISO] $*" >&2; }
log_skip() { echo "[SKIP] $*"; }

run_cmd() {
  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] $*"
  else
    log_info "$*"
    eval "$@"
  fi
}

human_dir_size() {
  local path="$1"
  if [[ -d "$path" ]]; then
    du -sh "$path" 2>/dev/null | awk '{print $1}'
  else
    echo "0"
  fi
}

confirm_or_exit() {
  local prompt="$1"
  if [[ "$ASSUME_YES" == true ]]; then
    return 0
  fi
  echo ""
  read -r -p "${prompt} [s/N] " reply
  case "${reply,,}" in
    s|sim|y|yes) return 0 ;;
    *) log_warn "Cancelado pelo operador."; exit 0 ;;
  esac
}

tier_includes() {
  local target="$1"
  if [[ ${#ONLY_TARGETS[@]} -gt 0 ]]; then
    local t
    for t in "${ONLY_TARGETS[@]}"; do
      [[ "$t" == "$target" ]] && return 0
    done
    return 1
  fi
  case "$TIER" in
    light)
      case "$target" in
        builder|dangling-images|stopped-orphans) return 0 ;;
      esac
      ;;
    standard)
      case "$target" in
        builder|dangling-images|stopped-orphans|drawing-library|query-cache|api-delpi-logs) return 0 ;;
      esac
      ;;
    docker-deep)
      case "$target" in
        builder|dangling-images|unused-images|stopped-orphans|drawing-library|query-cache|api-delpi-logs) return 0 ;;
      esac
      ;;
  esac
  if [[ "$target" == "vllm-huggingface" && "$INCLUDE_VLLM_CACHE" == true ]]; then
    return 0
  fi
  return 1
}

list_tiers() {
  maintenance_print_protection_summary
  echo "Tiers e alvos:"
  echo "  light:     builder, dangling-images, stopped-orphans"
  echo "  standard:  light + drawing-library, query-cache, api-delpi-logs"
  echo "  docker-deep: standard + unused-images + builder prune --all"
  echo ""
  echo "Opcional: --include-vllm-cache → vllm-huggingface (volume HuggingFace; re-download)"
  echo ""
  local data_root
  data_root="$(maintenance_default_data_host_dir)"
  echo "DELPI_DATA_HOST_DIR efetivo: ${data_root}"
  echo "  drawing-library-cache: $(human_dir_size "${data_root}/chat-attachments/drawing-library-cache")"
  echo "  api-delpi-logs:        $(human_dir_size "${data_root}/api-delpi-logs")"
  echo ""
  docker system df 2>/dev/null || log_warn "docker system df indisponível"
}

clean_builder() {
  tier_includes builder || return 0
  if [[ "$TIER" == "docker-deep" ]]; then
    run_cmd "docker builder prune -af"
  else
    # Mantém camadas recentes (até 7 dias) — suficiente para dev sem rebuild total.
    run_cmd "docker builder prune -af --filter until=168h"
  fi
}

clean_dangling_images() {
  tier_includes dangling-images || return 0
  run_cmd "docker image prune -f"
}

clean_unused_images() {
  tier_includes unused-images || return 0
  log_warn "Remove imagens não referenciadas por container (rebuild pode demorar)."
  confirm_or_exit "Remover imagens Docker não usadas?"
  run_cmd "docker image prune -af"
}

clean_stopped_orphans() {
  tier_includes stopped-orphans || return 0
  local ids
  ids="$(docker ps -aq --filter status=exited 2>/dev/null || true)"
  if [[ -z "$ids" ]]; then
    log_skip "Nenhum container parado."
    return 0
  fi
  local id name remove_ids=()
  while read -r id; do
    [[ -z "$id" ]] && continue
    name="$(docker inspect -f '{{.Name}}' "$id" 2>/dev/null | sed 's|^/||')"
    if [[ "$name" == ${DELPI_CONTAINER_PREFIX}* ]]; then
      log_skip "Container DELPI parado preservado: $name"
      continue
    fi
    remove_ids+=("$id")
  done <<< "$ids"

  if [[ ${#remove_ids[@]} -eq 0 ]]; then
    log_skip "Nenhum container órfão (fora delpi-*) para remover."
    return 0
  fi
  run_cmd "docker rm ${remove_ids[*]}"
}

clean_drawing_library_cache() {
  tier_includes drawing-library || return 0
  local data_root rel path size_before
  data_root="$(maintenance_default_data_host_dir)"
  rel="chat-attachments/drawing-library-cache"
  path="${data_root}/${rel}"

  # Segurança: só remove subdir explícito de cache.
  case "$path" in
    */chat-attachments/drawing-library-cache) ;;
    *)
      log_warn "Path de cache inválido — abortando drawing-library: $path"
      return 1
      ;;
  esac

  if [[ ! -d "$path" ]]; then
    log_skip "drawing-library-cache ausente: $path"
    return 0
  fi

  size_before="$(human_dir_size "$path")"
  log_info "Limpando cache biblioteca de desenhos (${size_before}): $path"
  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] rm -rf ${path}/*"
  else
    find "$path" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    log_ok "drawing-library-cache limpo (era ${size_before})"
  fi
}

clean_query_cache() {
  tier_includes query-cache || return 0
  if ! docker inspect -f '{{.State.Running}}' "$API_DELPI_CONTAINER" 2>/dev/null | grep -q true; then
    log_skip "query-cache: ${API_DELPI_CONTAINER} não está em execução (cache em memória já vazio)."
    return 0
  fi
  log_info "Reiniciando ${API_DELPI_CONTAINER} para limpar query-cache em memória (QUERY_CACHE_BACKEND=memory)."
  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] docker restart ${API_DELPI_CONTAINER}"
  else
    docker restart "$API_DELPI_CONTAINER" >/dev/null
    log_ok "api-delpi reiniciada — query-cache em memória zerado."
    log_warn "Se QUERY_CACHE_BACKEND=redis no .env, reinicie também o Redis ou use FLUSHDB manualmente."
  fi
}

clean_api_delpi_logs() {
  tier_includes api-delpi-logs || return 0
  local data_root logs_dir
  data_root="$(maintenance_default_data_host_dir)"
  logs_dir="${data_root}/api-delpi-logs"

  if [[ ! -d "$logs_dir" ]]; then
    log_skip "api-delpi-logs ausente: $logs_dir"
    return 0
  fi

  log_info "Rotacionando logs em ${logs_dir} (manter ${LOG_RETENTION_DAYS} dias)"
  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] find ${logs_dir} -type f -name '*.log' -mtime +${LOG_RETENTION_DAYS} -print"
  else
    local count
    count="$(find "$logs_dir" -type f \( -name '*.log' -o -name '*.log.*' \) -mtime +"${LOG_RETENTION_DAYS}" 2>/dev/null | wc -l | tr -d ' ')"
    find "$logs_dir" -type f \( -name '*.log' -o -name '*.log.*' \) -mtime +"${LOG_RETENTION_DAYS}" -delete 2>/dev/null || true
    log_ok "Logs antigos removidos: ${count} arquivo(s)"
  fi
}

clean_vllm_huggingface_cache() {
  tier_includes vllm-huggingface || return 0
  local vol
  vol="$(docker volume ls -q 2>/dev/null | while read -r v; do
    maintenance_is_vllm_volume "$v" && echo "$v" && break
  done)"
  if [[ -z "$vol" ]]; then
    log_skip "Volume vllm_cache não encontrado."
    return 0
  fi
  log_warn "Volume ${vol}: modelos HuggingFace serão baixados novamente no próximo uso do vLLM."
  confirm_or_exit "Limpar conteúdo do volume ${vol}?"
  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] docker run --rm -v ${vol}:/cache alpine sh -c 'rm -rf /cache/*'"
  else
    docker run --rm -v "${vol}:/cache" alpine sh -c 'rm -rf /cache/*'
    log_ok "Volume ${vol} limpo."
  fi
}

assert_no_volume_prune() {
  log_info "Política: docker volume prune / system prune --volumes NÃO são executados neste script."
  local vol
  while read -r vol; do
    [[ -z "$vol" ]] && continue
    if maintenance_is_protected_volume "$vol"; then
      log_info "Volume protegido detectado: ${vol}"
    fi
  done < <(docker volume ls -q 2>/dev/null || true)
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list) list_tiers; exit 0 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --yes) ASSUME_YES=true; shift ;;
    --tier) TIER="${2:?}"; shift 2 ;;
    --only)
      IFS=',' read -ra ONLY_TARGETS <<< "${2:?}"
      shift 2
      ;;
    --include-vllm-cache) INCLUDE_VLLM_CACHE=true; shift ;;
    --log-retention) LOG_RETENTION_DAYS="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Opção desconhecida: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$TIER" in
  light|standard|docker-deep) ;;
  *)
    echo "Tier inválido: $TIER (use light, standard ou docker-deep)" >&2
    exit 1
    ;;
esac

echo "=== Manutenção DELPI — limpeza de cache (tier: ${TIER}) ==="
if [[ "$DRY_RUN" == true ]]; then
  log_warn "Modo dry-run — nenhuma alteração será aplicada."
fi

assert_no_volume_prune

if [[ "$TIER" == "docker-deep" && "$ASSUME_YES" != true && ${#ONLY_TARGETS[@]} -eq 0 ]]; then
  confirm_or_exit "Tier docker-deep remove imagens não usadas e todo build cache. Continuar?"
fi

if [[ "$INCLUDE_VLLM_CACHE" == true && "$ASSUME_YES" != true ]]; then
  confirm_or_exit "Inclui limpeza do cache HuggingFace (vLLM). Continuar?"
fi

clean_builder
clean_dangling_images
clean_unused_images
clean_stopped_orphans
clean_drawing_library_cache
clean_query_cache
clean_api_delpi_logs
clean_vllm_huggingface_cache

echo ""
log_ok "Manutenção concluída."
if [[ "$DRY_RUN" != true ]]; then
  docker system df 2>/dev/null || true
fi
