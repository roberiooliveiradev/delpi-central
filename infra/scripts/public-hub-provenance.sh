#!/usr/bin/env bash
# Source this helper from the canonical HML/PROD sequential deploy scripts.
# The label is an informational pointer, never build attestation/authorization.

atlas_public_hub_revision() {
  local repo_root="${1:?repo_root required}"
  local revision dirty ignored pattern
  local ignore_file="$repo_root/plugins/.dockerignore"
  local -a build_inputs=(
    plugins/.dockerignore
    plugins/public-hub
    plugins/tv-dashboard-presentation
    plugins/transformometro-meeting-minutes-presentation
    plugins/cipa-meeting-minutes-presentation
    plugins/vite
    plugins/plugin-ui/src/components/signature
    plugins/plugin-ui/src/overlayLayers.ts
  )
  if ! revision="$(git -C "$repo_root" rev-parse --verify HEAD 2>/dev/null)"; then
    echo "[ERRO] Public Hub: Git HEAD nao disponivel; build bloqueado." >&2
    return 1
  fi
  if [[ ! "$revision" =~ ^[0-9a-f]{40}$ ]]; then
    echo "[ERRO] Public Hub: SOURCE_REVISION exige SHA Git completo (40 hex)." >&2
    return 1
  fi

  # Dockerfile-specific policies override the context policy. Do not infer
  # exclusion safety from Git ignore rules or accept an unreviewed override.
  if [[ ! -f "$ignore_file" || -L "$ignore_file" ||
        -e "$repo_root/plugins/public-hub/Dockerfile.dockerignore" ||
        -L "$repo_root/plugins/public-hub/Dockerfile.dockerignore" ]]; then
    echo "[ERRO] Public Hub: politica Docker de exclusao ausente ou substituida; build bloqueado." >&2
    return 1
  fi
  # Only this reviewed subset is supported. In particular, a negation could
  # reintroduce local node_modules/dist that the Git checks below omit.
  while IFS= read -r pattern || [[ -n "$pattern" ]]; do
    case "$pattern" in
      ''|\#*|'**/node_modules'|'**/dist'|'**/.git') ;;
      *)
        echo "[ERRO] Public Hub: politica Docker alterada; revisar exclusoes antes do build." >&2
        return 1
        ;;
    esac
  done < "$ignore_file"
  for pattern in '**/node_modules' '**/dist' '**/.git'; do
    if ! grep -Fxq "$pattern" "$ignore_file"; then
      echo "[ERRO] Public Hub: exclusao Docker obrigatoria ausente; build bloqueado." >&2
      return 1
    fi
  done

  # These paths cover COPY inputs AND the policy controlling their contents.
  # Fail closed on tracked edits OR untracked assets affecting the image.
  if ! dirty="$(git -C "$repo_root" status --porcelain --untracked-files=normal -- \
    "${build_inputs[@]}")"; then
    echo "[ERRO] Public Hub: impossivel verificar a arvore de trabalho." >&2
    return 1
  fi
  if [[ -n "$dirty" ]]; then
    echo "[ERRO] Public Hub: arquivos do build modificados ou nao versionados. Publique primeiro um commit limpo." >&2
    return 1
  fi

  # Git-clean alone omits .env.local, logs and other locally ignored inputs
  # that Docker still copies. Exempt only the directories proven excluded by
  # the checked Docker policy; never print names or contents of local files.
  if ! ignored="$(git -C "$repo_root" ls-files --others --ignored --exclude-standard -- \
    "${build_inputs[@]}" \
    ':(glob,exclude)**/node_modules' ':(glob,exclude)**/node_modules/**' \
    ':(glob,exclude)**/dist' ':(glob,exclude)**/dist/**' \
    ':(glob,exclude)**/.git' ':(glob,exclude)**/.git/**')"; then
    echo "[ERRO] Public Hub: impossivel verificar arquivos ignorados pelo Git." >&2
    return 1
  fi
  if [[ -n "$ignored" ]]; then
    echo "[ERRO] Public Hub: arquivos locais ignorados pelo Git podem entrar na imagem; build bloqueado." >&2
    return 1
  fi
  printf '%s\n' "$revision"
}
