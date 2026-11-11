#!/usr/bin/env bash
# Instala/atualiza o coletor Linux do Portal de TI no host (idempotente).
# NÃO cria segredos, NÃO adiciona o usuário ao grupo docker e NÃO habilita o timer.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
IT_PORTAL_API_DIR="${REPO_ROOT}/it-portal-api"
SHARED_DIR="${REPO_ROOT}/shared"

INSTALL_ROOT="${IT_PORTAL_COLLECTOR_ROOT:-/opt/delpi/it-portal-collector}"
STATE_DIR="${IT_PORTAL_COLLECTOR_STATE_DIR:-/var/lib/it-portal-collector}"
ENV_DIR="${IT_PORTAL_COLLECTOR_ENV_DIR:-/etc/delpi}"
ENV_FILE="${ENV_DIR}/it-portal-linux-collector.env"
ENV_EXAMPLE="${SCRIPT_DIR}/it-portal-linux-collector.env.example"
SYSTEMD_DIR="${SYSTEMD_UNIT_DIR:-/etc/systemd/system}"
SERVICE_USER="${IT_PORTAL_COLLECTOR_USER:-delpi-collector}"
SERVICE_GROUP="${IT_PORTAL_COLLECTOR_GROUP:-delpi-collector}"
PYTHON_BIN="${IT_PORTAL_COLLECTOR_PYTHON:-python3}"

log() { printf '[it-portal-collector] %s\n' "$*"; }
die() { printf '[it-portal-collector] ERRO: %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "execute como root (sudo)"
[[ -d "${IT_PORTAL_API_DIR}/collectors/linux_host" ]] || die "fonte do coletor ausente em ${IT_PORTAL_API_DIR}"
[[ -d "${SHARED_DIR}/delpi_auth" ]] || die "shared/delpi_auth ausente em ${SHARED_DIR}"
command -v "${PYTHON_BIN}" >/dev/null || die "${PYTHON_BIN} não encontrado"
command -v rsync >/dev/null || die "rsync é obrigatório para instalação idempotente"
command -v flock >/dev/null || die "flock é obrigatório"

if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  log "criando usuário técnico ${SERVICE_USER} (sem login, sem docker)"
  useradd --system --home "${INSTALL_ROOT}" --shell /usr/sbin/nologin \
    --user-group "${SERVICE_USER}"
else
  log "usuário ${SERVICE_USER} já existe — preservado (não altera grupos)"
fi

# Garantir que o instalador NÃO adiciona docker automaticamente.
if id -nG "${SERVICE_USER}" 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
  log "AVISO: ${SERVICE_USER} já pertence ao grupo docker (decisão prévia). Coleta Docker pode funcionar; isso não foi concedido por este instalador."
else
  log "Docker: ${SERVICE_USER} fora do grupo docker — seção docker pode ficar partial/unavailable"
fi

install -d -m 0755 -o root -g root /opt/delpi
install -d -m 0750 -o "${SERVICE_USER}" -g "${SERVICE_GROUP}" "${INSTALL_ROOT}"
install -d -m 0750 -o "${SERVICE_USER}" -g "${SERVICE_GROUP}" "${STATE_DIR}"
install -d -m 0750 -o root -g "${SERVICE_GROUP}" "${ENV_DIR}"
install -d -m 0750 -o "${SERVICE_USER}" -g "${SERVICE_GROUP}" "${INSTALL_ROOT}/bin"
install -d -m 0750 -o "${SERVICE_USER}" -g "${SERVICE_GROUP}" "${INSTALL_ROOT}/vendor"

log "sincronizando artefatos versionados → ${INSTALL_ROOT}"
rsync -a --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.venv/' \
  "${IT_PORTAL_API_DIR}/collectors/" "${INSTALL_ROOT}/collectors/"

rsync -a --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '*.egg-info/' \
  --exclude '.venv/' \
  "${SHARED_DIR}/" "${INSTALL_ROOT}/vendor/shared/"

install -m 0644 "${SCRIPT_DIR}/requirements-collector.txt" "${INSTALL_ROOT}/requirements-collector.txt"
install -m 0644 "${SCRIPT_DIR}/README.md" "${INSTALL_ROOT}/README.md"
install -m 0755 "${SCRIPT_DIR}/run-collector.sh" "${INSTALL_ROOT}/bin/run-collector"

if [[ ! -x "${INSTALL_ROOT}/venv/bin/python" ]]; then
  log "criando venv em ${INSTALL_ROOT}/venv"
  "${PYTHON_BIN}" -m venv "${INSTALL_ROOT}/venv"
fi

log "instalando dependências reproduzíveis no venv"
"${INSTALL_ROOT}/venv/bin/pip" install --upgrade pip
"${INSTALL_ROOT}/venv/bin/pip" install -r "${INSTALL_ROOT}/requirements-collector.txt"
"${INSTALL_ROOT}/venv/bin/pip" install -e "${INSTALL_ROOT}/vendor/shared"

chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_ROOT}"
chmod -R u=rwX,g=rX,o= "${INSTALL_ROOT}"
chmod 0750 "${INSTALL_ROOT}/bin/run-collector"
chmod 0750 "${INSTALL_ROOT}/venv/bin" || true

if [[ ! -f "${ENV_FILE}" ]]; then
  install -m 0640 -o root -g "${SERVICE_GROUP}" "${ENV_EXAMPLE}" "${ENV_FILE}"
  log "criado ${ENV_FILE} a partir do exemplo — SUBSTITUA S2S_CLIENT_SECRET antes do submit"
else
  log "preservando ${ENV_FILE} existente (não sobrescrito)"
  chmod 0640 "${ENV_FILE}"
  chown "root:${SERVICE_GROUP}" "${ENV_FILE}"
fi

install -m 0644 "${SCRIPT_DIR}/it-portal-linux-collector.service" \
  "${SYSTEMD_DIR}/it-portal-linux-collector.service"
install -m 0644 "${SCRIPT_DIR}/it-portal-linux-collector.timer" \
  "${SYSTEMD_DIR}/it-portal-linux-collector.timer"

if command -v systemd-analyze >/dev/null; then
  log "systemd-analyze verify"
  systemd-analyze verify \
    "${SYSTEMD_DIR}/it-portal-linux-collector.service" \
    "${SYSTEMD_DIR}/it-portal-linux-collector.timer"
fi

systemctl daemon-reload

SOURCE_SHA="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
printf '%s\n' "${SOURCE_SHA}" > "${INSTALL_ROOT}/SOURCE_SHA"
chown "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_ROOT}/SOURCE_SHA"

cat <<EOF

Instalação concluída (timer NÃO habilitado).

Artefatos:
  root=${INSTALL_ROOT}
  env=${ENV_FILE}
  state=${STATE_DIR}
  source_sha=${SOURCE_SHA}
  user=${SERVICE_USER} (sem login; docker NÃO concedido por este script)

Próximos passos no srv-api:
  1) Editar ${ENV_FILE} (secret S2S + SERVER_ID). Permissão 0640 root:${SERVICE_GROUP}.
  2) Diagnóstico como usuário técnico:
       sudo -u ${SERVICE_USER} ${INSTALL_ROOT}/bin/run-collector diagnose
  3) Smoke manual do oneshot (após gates S2S/env):
       sudo systemctl start it-portal-linux-collector.service
       sudo systemctl status it-portal-linux-collector.service --no-pager
  4) Somente após AC-03 (run_id no Postgres + UI):
       sudo systemctl enable --now it-portal-linux-collector.timer
       systemctl is-enabled it-portal-linux-collector.timer
       systemctl is-active it-portal-linux-collector.timer
       systemctl list-timers it-portal-linux-collector.timer --no-pager

Desativar:
  sudo systemctl disable --now it-portal-linux-collector.timer

Rollback das units:
  sudo systemctl disable --now it-portal-linux-collector.timer || true
  sudo rm -f ${SYSTEMD_DIR}/it-portal-linux-collector.service \\
             ${SYSTEMD_DIR}/it-portal-linux-collector.timer
  sudo systemctl daemon-reload
EOF
