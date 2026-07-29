#!/usr/bin/env bash
# Catálogo canônico: o que é cache regenerável vs. dado sensível DELPI.
# Fonte única consumida por maintenance-clean-cache.sh
#
# Doc: infra/README-ambiente.md § Manutenção de cache

# Volumes nomeados Compose (prefixo típico: infra_*). NUNCA prune/remover.
readonly DELPI_PROTECTED_VOLUME_PATTERNS=(
  '*postgres*'
  '*keycloak*'
  '*ollama*'
)

# Subpastas de DELPI_DATA_HOST_DIR que contêm uploads/evidências do usuário.
# drawing-library-cache fica DENTRO de chat-attachments e é exceção (cache).
readonly DELPI_PROTECTED_DATA_SUBDIRS=(
  chat-attachments
  chat-sources
  pac-evidences
  kaizen-evidences
  guias-procedimentos
  audit-5s-nc
  audit-5s-responses
  quality-labels
  reports-runs
  revisao-evidencias
  processo-arquivos
  transformometro
  cipa
  customer-experience
  tv-dashboard
  api-delpi-logs
)

# Caches regeneráveis no host (paths relativos a DELPI_DATA_HOST_DIR).
readonly DELPI_REGENERABLE_HOST_CACHES=(
  chat-attachments/drawing-library-cache
)

# Containers DELPI — nunca remover em manutenção de órfãos.
readonly DELPI_CONTAINER_PREFIX=delpi-

# Volume opcional (modelos HuggingFace — re-download demorado).
readonly DELPI_OPTIONAL_HEAVY_VOLUME_PATTERN='*vllm*'

maintenance_default_data_host_dir() {
  if [[ -f "${COMPOSE_DIR:-}/.env" ]]; then
    # shellcheck disable=SC1090
    set -a
    # shellcheck source=/dev/null
    source <(grep -E '^DELPI_DATA_HOST_DIR=' "${COMPOSE_DIR}/.env" 2>/dev/null || true)
    set +a
  fi
  echo "${DELPI_DATA_HOST_DIR:-${HOME}/.delpi}"
}

maintenance_is_protected_volume() {
  local name="$1"
  local pattern
  for pattern in "${DELPI_PROTECTED_VOLUME_PATTERNS[@]}"; do
    case "$name" in
      $pattern) return 0 ;;
    esac
  done
  return 1
}

maintenance_is_vllm_volume() {
  local name="$1"
  case "$name" in
    $DELPI_OPTIONAL_HEAVY_VOLUME_PATTERN) return 0 ;;
  esac
  return 1
}

maintenance_print_protection_summary() {
  echo "Volumes protegidos (padrões): ${DELPI_PROTECTED_VOLUME_PATTERNS[*]}"
  echo "Dados persistentes em DELPI_DATA_HOST_DIR (não apagar):"
  local sub
  for sub in "${DELPI_PROTECTED_DATA_SUBDIRS[@]}"; do
    echo "  - .../${sub}/"
  done
  echo "Caches regeneráveis no host:"
  local cache
  for cache in "${DELPI_REGENERABLE_HOST_CACHES[@]}"; do
    echo "  - .../${cache}/"
  done
  echo ""
  echo "Operações proibidas neste fluxo: docker volume prune, docker system prune --volumes,"
  echo "rm -rf em pastas de upload/evidência fora dos caches listados."
}
