#!/usr/bin/env bash
# Comprova o modelo de ownership do coletor Linux (falha se o serviço puder gravar código).
set -euo pipefail

INSTALL_ROOT="${IT_PORTAL_COLLECTOR_ROOT:-/opt/delpi/it-portal-collector}"
STATE_DIR="${IT_PORTAL_COLLECTOR_STATE_DIR:-/var/lib/it-portal-collector}"
ENV_FILE="${IT_PORTAL_COLLECTOR_ENV_FILE:-/etc/delpi/it-portal-linux-collector.env}"
SERVICE_USER="${IT_PORTAL_COLLECTOR_USER:-delpi-collector}"
SERVICE_GROUP="${IT_PORTAL_COLLECTOR_GROUP:-delpi-collector}"

die() { printf '[verify-collector-perms] ERRO: %s\n' "$*" >&2; exit 1; }
ok() { printf '[verify-collector-perms] OK %s\n' "$*"; }

[[ -d "${INSTALL_ROOT}" ]] || die "INSTALL_ROOT ausente: ${INSTALL_ROOT}"
[[ -d "${STATE_DIR}" ]] || die "STATE_DIR ausente: ${STATE_DIR}"
id -u "${SERVICE_USER}" >/dev/null 2>&1 || die "usuário ${SERVICE_USER} ausente"

owner_of() { stat -c '%U:%G' "$1"; }
mode_of() { stat -c '%a' "$1"; }

[[ "$(owner_of "${INSTALL_ROOT}")" == "root:root" ]] \
  || die "${INSTALL_ROOT} deve ser root:root (é $(owner_of "${INSTALL_ROOT}"))"

for path in \
  "${INSTALL_ROOT}/bin/run-collector" \
  "${INSTALL_ROOT}/collectors" \
  "${INSTALL_ROOT}/vendor" \
  "${INSTALL_ROOT}/venv"
do
  [[ -e "${path}" ]] || die "caminho obrigatório ausente: ${path}"
  [[ "$(owner_of "${path}")" == "root:root" ]] \
    || die "${path} deve ser root:root (é $(owner_of "${path}"))"
done

# Negativa: o usuário técnico não deve conseguir criar/modificar sob INSTALL_ROOT.
probe="${INSTALL_ROOT}/.write-probe.$$"
if sudo -u "${SERVICE_USER}" touch "${probe}" 2>/dev/null; then
  rm -f "${probe}" || true
  die "${SERVICE_USER} conseguiu escrever em ${INSTALL_ROOT}"
fi
ok "${SERVICE_USER} não escreve em ${INSTALL_ROOT}"

for path in \
  "${INSTALL_ROOT}/bin/run-collector" \
  "${INSTALL_ROOT}/collectors/linux_host/submit.py" \
  "${INSTALL_ROOT}/vendor/shared/pyproject.toml"
do
  if [[ -e "${path}" ]] && sudo -u "${SERVICE_USER}" sh -c "echo x >> '${path}'" 2>/dev/null; then
    die "${SERVICE_USER} conseguiu modificar ${path}"
  fi
done
ok "${SERVICE_USER} não modifica wrapper/código/vendor"

# Negativa adicional no venv (site-packages / bin), se já existir.
venv_probe_target=""
if [[ -d "${INSTALL_ROOT}/venv/lib" ]]; then
  venv_probe_target="$(find "${INSTALL_ROOT}/venv/lib" -type d -name site-packages 2>/dev/null | head -n 1 || true)"
fi
if [[ -n "${venv_probe_target}" ]]; then
  if sudo -u "${SERVICE_USER}" touch "${venv_probe_target}/.write-probe.$$" 2>/dev/null; then
    rm -f "${venv_probe_target}/.write-probe.$$" || true
    die "${SERVICE_USER} conseguiu escrever em ${venv_probe_target}"
  fi
  ok "${SERVICE_USER} não escreve em site-packages"
fi
if [[ -f "${INSTALL_ROOT}/venv/bin/python" ]]; then
  if sudo -u "${SERVICE_USER}" sh -c "echo x >> '${INSTALL_ROOT}/venv/bin/python'" 2>/dev/null; then
    die "${SERVICE_USER} conseguiu modificar venv/bin/python"
  fi
  ok "${SERVICE_USER} não modifica venv/bin"
fi

# Positiva: state gravável.
state_probe="${STATE_DIR}/.write-probe.$$"
sudo -u "${SERVICE_USER}" touch "${state_probe}" \
  || die "${SERVICE_USER} não conseguiu escrever em ${STATE_DIR}"
sudo -u "${SERVICE_USER}" rm -f "${state_probe}"
[[ "$(owner_of "${STATE_DIR}")" == "${SERVICE_USER}:${SERVICE_GROUP}" ]] \
  || die "${STATE_DIR} deve ser ${SERVICE_USER}:${SERVICE_GROUP}"
ok "${SERVICE_USER} grava em ${STATE_DIR}"

if [[ -f "${ENV_FILE}" ]]; then
  [[ "$(owner_of "${ENV_FILE}")" == "root:${SERVICE_GROUP}" ]] \
    || die "${ENV_FILE} deve ser root:${SERVICE_GROUP}"
  [[ "$(mode_of "${ENV_FILE}")" == "640" ]] \
    || die "${ENV_FILE} deve ser modo 640 (é $(mode_of "${ENV_FILE}"))"
  ok "env ${ENV_FILE} root:${SERVICE_GROUP} 0640"
fi

# Docker não deve ter sido concedido por este pacote (aviso se já existir).
if id -nG "${SERVICE_USER}" | tr ' ' '\n' | grep -qx docker; then
  printf '[verify-collector-perms] AVISO: %s já está no grupo docker (fora do instalador)\n' \
    "${SERVICE_USER}"
else
  ok "${SERVICE_USER} fora do grupo docker"
fi

ok "modelo de permissões válido"
