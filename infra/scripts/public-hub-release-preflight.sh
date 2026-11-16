#!/usr/bin/env bash
# ATLAS P2.2h: read-only candidate for signed Public Hub promotion.
# No Docker writes, deploy, registry pull, approval or PREPARE/ACT invocation.
set -euo pipefail

REPO='roberiooliveiradev/delpi-central'
IMAGE='ghcr.io/roberiooliveiradev/delpi-public-hub'
WORKFLOW='roberiooliveiradev/delpi-central/.github/workflows/atlas-public-hub-oci.yml'

fail() { printf '[BLOCKED] Public Hub P2.2h: %s\n' "$1" >&2; exit 1; }

# An explicit apply request is NEVER interpreted as consent. The future
# executor must validate a sealed approval and journal outside ChatGPT.
[[ "${1:-}" != '--apply' ]] || fail 'ativacao bloqueada: approval Core/journal/executor ainda indisponiveis'
[[ $# -eq 5 && "$1" == '--plan' ]] || \
  fail 'uso: public-hub-release-preflight.sh --plan <prod|hml> <commit-sha-40> <manifest-sha256> <current-ImageID>'

environment="$2"
revision="$3"
digest="$4"
expected_current="$5"
[[ "$revision" =~ ^[0-9a-f]{40}$ ]] || fail 'commit SHA invalido'
[[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]] || fail 'digest OCI invalido'
[[ "$expected_current" =~ ^sha256:[0-9a-f]{64}$ ]] || fail 'ImageID atual esperado invalido'
case "$environment" in
  prod) container='delpi-public-hub' ;;
  hml) container='delpi-hml-public-hub' ;;
  *) fail 'ambiente fora da allowlist' ;;
esac
command -v gh >/dev/null 2>&1 || fail 'GitHub CLI indisponivel'
command -v docker >/dev/null 2>&1 || fail 'Docker CLI indisponivel'
command -v sha256sum >/dev/null 2>&1 || fail 'sha256sum indisponivel'

# The signed subject is the manifest digest; OCI labels are never credentials.
# Deny if GitHub/Sigstore cannot validate issuer, workflow, ref and source SHA.
if ! gh attestation verify "oci://${IMAGE}@${digest}" \
  --repo "$REPO" \
  --signer-workflow "$WORKFLOW" \
  --source-ref 'refs/heads/main' \
  --source-digest "$revision" \
  --predicate-type 'https://slsa.dev/provenance/v1' \
  --cert-oidc-issuer 'https://token.actions.githubusercontent.com' \
  --deny-self-hosted-runners >/dev/null; then
  fail 'atestado assinado nao verificado'
fi

# Read the actual container, not the local Git HEAD or the downloaded cache.
actual_id="$(docker container inspect --format '{{.Image}}' "$container" 2>/dev/null)" || \
  fail 'container esperado nao localizado'
[[ "$actual_id" == "$expected_current" ]] || fail 'drift do ImageID atual desde o readback'
status="$(docker container inspect --format '{{.State.Status}}' "$container" 2>/dev/null)" || \
  fail 'estado Docker indisponivel'
[[ "$status" == running ]] || fail 'container nao esta em execucao'
service="$(docker container inspect --format '{{index .Config.Labels "com.docker.compose.service"}}' "$container" 2>/dev/null)" || \
  fail 'Compose service indisponivel'
[[ "$service" == public-hub ]] || fail 'servico Compose divergente'
project="$(docker container inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' "$container" 2>/dev/null)" || \
  fail 'Compose project indisponivel'
[[ -n "$project" && "$project" != '<no value>' ]] || fail 'projeto Compose nao verificavel'
if [[ "$environment" == hml ]]; then
  [[ "$project" == delpi-hml ]] || fail 'projeto HML divergente'
else
  [[ "$project" != delpi-hml ]] || fail 'container HML nao pode passar por PROD'
fi
current_revision="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$actual_id" 2>/dev/null)" || \
  fail 'revisao da imagem instalada indisponivel'
[[ "$current_revision" =~ ^[0-9a-f]{40}$ ]] || fail 'revisao da imagem instalada invalida'

# The plan hash is only a tamper-evident diagnostic. It is NOT an approval,
# a trust token, a journal record, or an authorization to execute anything.
seal="$(printf '%s\n' 'ATLAS-P22H-PLAN-V1' "$environment" "$revision" "$digest" "$actual_id" "$project" "$current_revision" | sha256sum)"
seal="${seal%% *}"
printf '[PLAN_OK_NO_DEPLOY] release assinada e revisao atual lidas sem alterar host\n'
printf 'environment=%s container=%s project=%s current_ImageID=%s current_revision=%s\n' \
  "$environment" "$container" "$project" "$actual_id" "$current_revision"
printf 'signed_commit=%s signed_manifest=%s plan_sha256=%s\n' "$revision" "$digest" "$seal"
printf 'promotion=BLOCKED approval=NOT_IMPLEMENTED readiness=NOT_VERIFIED rollback=NOT_VERIFIED\n'
