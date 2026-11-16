#!/usr/bin/env bash
# ATLAS P2.2g: read-only proof that a running Public Hub container uses the
# exact CI image whose manifest digest was signed by the trusted workflow.
# This is NOT a deploy, an approval, a healthcheck or a PREPARE/ACT endpoint.
set -euo pipefail

REPO='roberiooliveiradev/delpi-central'
IMAGE='ghcr.io/roberiooliveiradev/delpi-public-hub'
WORKFLOW='roberiooliveiradev/delpi-central/.github/workflows/atlas-public-hub-oci.yml'

fail() { printf '[BLOCKED] Public Hub release: %s\n' "$1" >&2; exit 1; }

if [[ $# -ne 3 ]]; then
  fail 'uso: verify-public-hub-release.sh <git-sha-40> <sha256:manifest-digest-64> <prod|hml>'
fi
revision="$1"
digest="$2"
environment="$3"

[[ "$revision" =~ ^[0-9a-f]{40}$ ]] || fail 'revisao Git invalida'
[[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]] || fail 'digest de manifesto OCI invalido'
case "$environment" in
  prod) container='delpi-public-hub' ;;
  hml) container='delpi-hml-public-hub' ;;
  *) fail 'ambiente nao autorizado' ;;
esac

command -v gh >/dev/null 2>&1 || fail 'GitHub CLI indisponivel'
command -v docker >/dev/null 2>&1 || fail 'Docker CLI indisponivel'
image_ref="${IMAGE}@${digest}"

# GitHub validates Sigstore signature, trusted source commit/ref, signing
# workflow, predicate and GitHub-hosted runner. Never trust OCI labels alone.
# The CLI may require authenticated read access to GHCR and GitHub.
if ! gh attestation verify "oci://${image_ref}" \
  --repo "$REPO" \
  --signer-workflow "$WORKFLOW" \
  --source-ref 'refs/heads/main' \
  --source-digest "$revision" \
  --predicate-type 'https://slsa.dev/provenance/v1' \
  --cert-oidc-issuer 'https://token.actions.githubusercontent.com' \
  --deny-self-hosted-runners >/dev/null; then
  fail 'assinatura/identidade/proveniencia do artefato nao verificadas'
fi

# The manifest digest is NOT the Docker image config ID. Resolve the
# *digest-pinned* locally available image and compare its config ID with the
# running container's actual ImageID. Never pull, rebuild or restart here.
image_id="$(docker image inspect --format '{{.Id}}' "$image_ref" 2>/dev/null)" || \
  fail 'imagem por digest nao instalada localmente'
[[ "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]] || fail 'ImageID local invalido'
installed_id="$(docker container inspect --format '{{.Image}}' "$container" 2>/dev/null)" || \
  fail 'container esperado indisponivel'
[[ "$installed_id" == "$image_id" ]] || fail 'container nao executa a imagem por digest aprovada'

source_revision="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_ref" 2>/dev/null)" || fail 'revisao OCI indisponivel'
source_repo="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.source"}}' "$image_ref" 2>/dev/null)" || fail 'origem OCI indisponivel'
[[ "$source_revision" == "$revision" ]] || fail 'revisao OCI diferente do commit assinado'
[[ "$source_repo" == "https://github.com/${REPO}" ]] || fail 'origem OCI nao canonica'

service="$(docker container inspect --format '{{index .Config.Labels "com.docker.compose.service"}}' "$container" 2>/dev/null)" || fail 'servico Compose indisponivel'
[[ "$service" == 'public-hub' ]] || fail 'container nao pertence ao servico Public Hub'
if [[ "$environment" == 'hml' ]]; then
  project="$(docker container inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' "$container" 2>/dev/null)" || fail 'projeto HML indisponivel'
  [[ "$project" == 'delpi-hml' ]] || fail 'projeto Compose HML divergente'
fi
status="$(docker container inspect --format '{{.State.Status}}' "$container" 2>/dev/null)" || fail 'estado runtime indisponivel'
[[ "$status" == 'running' ]] || fail 'container nao esta em execucao'

printf '[PASS] Public Hub %s: assinatura GitHub, commit, workflow, manifesto OCI e ImageID em execucao correspondem.\n' "$environment"
printf 'GitSHA=%s ManifestDigest=%s ImageID=%s\n' "$revision" "$digest" "$image_id"
