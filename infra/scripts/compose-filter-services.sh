#!/usr/bin/env bash
# Filtro de serviços por nome exato ou glob — usado por up-*-sequential.sh
#
# EXTRA_SERVICES deve estar definido no script chamador.
# Padrões glob: dashboard-*, *-production (use aspas se o shell expandir *).

compose_service_matches_filter() {
  local name="$1"
  local want="$2"
  # want sem aspas: match exato ou glob bash (* ? [...])
  [[ "$name" == $want ]]
}

compose_filter_phase_services() {
  local -a src=("$@")
  local -a out=()
  local name want matched

  if [[ ${#EXTRA_SERVICES[@]} -eq 0 ]]; then
    printf '%s\n' "${src[@]}"
    return 0
  fi

  for name in "${src[@]}"; do
    matched=false
    for want in "${EXTRA_SERVICES[@]}"; do
      if compose_service_matches_filter "$name" "$want"; then
        matched=true
        break
      fi
    done
    if [[ "$matched" == true ]]; then
      out+=("$name")
    fi
  done

  if [[ ${#out[@]} -eq 0 ]]; then
    # Quando o chamador varre várias fases (EXTRA_SERVICES sem --fase), fase vazia é ok.
    if [[ "${COMPOSE_FILTER_ALLOW_EMPTY:-0}" == "1" ]]; then
      return 0
    fi
    echo "Nenhum serviço da fase bate com: ${EXTRA_SERVICES[*]}" >&2
    echo "Dica: use aspas nos padrões glob (ex.: 'dashboard-*', '*-production')." >&2
    return 1
  fi

  printf '%s\n' "${out[@]}"
}
