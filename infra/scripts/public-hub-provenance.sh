#!/usr/bin/env bash
# Source this helper from the canonical HML/PROD sequential deploy scripts.
# The label is an informational pointer, never build attestation/authorization.

atlas_public_hub_revision() {
  local repo_root="${1:?repo_root required}"
  local revision dirty
  if ! revision="$(git -C "$repo_root" rev-parse --verify HEAD 2>/dev/null)"; then
    echo "[ERRO] Public Hub: Git HEAD nao disponivel; build bloqueado." >&2
    return 1
  fi
  if [[ ! "$revision" =~ ^[0-9a-f]{40}$ ]]; then
    echo "[ERRO] Public Hub: SOURCE_REVISION exige SHA Git completo (40 hex)." >&2
    return 1
  fi

  # The Dockerfile copies these exact build inputs from the plugins context.
  # Fail closed on tracked edits OR untracked assets affecting the image.
  if ! dirty="$(git -C "$repo_root" status --porcelain --untracked-files=normal -- \
    plugins/public-hub \
    plugins/tv-dashboard-presentation \
    plugins/transformometro-meeting-minutes-presentation \
    plugins/cipa-meeting-minutes-presentation \
    plugins/vite \
    plugins/plugin-ui/src/components/signature \
    plugins/plugin-ui/src/overlayLayers.ts)"; then
    echo "[ERRO] Public Hub: impossivel verificar a arvore de trabalho." >&2
    return 1
  fi
  if [[ -n "$dirty" ]]; then
    echo "[ERRO] Public Hub: arquivos do build modificados ou nao versionados. Publique primeiro um commit limpo." >&2
    return 1
  fi
  printf '%s\n' "$revision"
}
