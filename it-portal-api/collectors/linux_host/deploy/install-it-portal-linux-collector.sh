#!/usr/bin/env bash
# Instala/atualiza o coletor Linux do Portal de TI no host (idempotente).
# NÃO cria segredos, NÃO adiciona o usuário ao grupo docker e NÃO habilita o timer.
#
# Modelo de ownership (gate de segurança):
#   - /opt/delpi/it-portal-collector → root:root, leitura/execução para o serviço, sem escrita
#   - /var/lib/it-portal-collector   → delpi-collector (único gravável)
#   - /etc/delpi/*.env               → root:delpi-collector 0640
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
IT_PORTAL_API_DIR="${REPO_ROOT}/it-portal-api"
SHARED_DIR="${REPO_ROOT}/shared"
VENDOR_PYPROJECT="${SCRIPT_DIR}/vendor-delpi-auth-pyproject.toml"

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

harden_install_tree() {
  # Artefatos executáveis e dependências: só root escreve.
  chown -R root:root "${INSTALL_ROOT}"
  # Dirs: rwx para root, r-x para outros (serviço lê/executa).
  find "${INSTALL_ROOT}" -type d -exec chmod 0755 {} +
  # Arquivos: rw para root, r para outros; scripts/binários de venv precisam +x.
  find "${INSTALL_ROOT}" -type f -exec chmod 0644 {} +
  if [[ -d "${INSTALL_ROOT}/bin" ]]; then
    find "${INSTALL_ROOT}/bin" -type f -exec chmod 0755 {} +
  fi
  if [[ -d "${INSTALL_ROOT}/venv/bin" ]]; then
    find "${INSTALL_ROOT}/venv/bin" -type f -exec chmod 0755 {} +
  fi
  # shebang scripts / entrypoints
  if [[ -x "${INSTALL_ROOT}/bin/run-collector" ]]; then
    chmod 0755 "${INSTALL_ROOT}/bin/run-collector"
  fi
}

harden_state_and_env() {
  install -d -m 0750 -o "${SERVICE_USER}" -g "${SERVICE_GROUP}" "${STATE_DIR}"
  # Garante que o serviço não herda escrita em INSTALL_ROOT.
  chmod 0750 "${STATE_DIR}"
  chown "${SERVICE_USER}:${SERVICE_GROUP}" "${STATE_DIR}"

  install -d -m 0750 -o root -g "${SERVICE_GROUP}" "${ENV_DIR}"
  if [[ -f "${ENV_FILE}" ]]; then
    chown "root:${SERVICE_GROUP}" "${ENV_FILE}"
    chmod 0640 "${ENV_FILE}"
  fi
}

[[ "$(id -u)" -eq 0 ]] || die "execute como root (sudo)"
[[ -d "${IT_PORTAL_API_DIR}/collectors/linux_host" ]] || die "fonte do coletor ausente em ${IT_PORTAL_API_DIR}"
[[ -d "${SHARED_DIR}/delpi_auth" ]] || die "shared/delpi_auth ausente em ${SHARED_DIR}"
[[ -f "${VENDOR_PYPROJECT}" ]] || die "manifesto vendor ausente: ${VENDOR_PYPROJECT}"
command -v "${PYTHON_BIN}" >/dev/null || die "${PYTHON_BIN} não encontrado"
command -v rsync >/dev/null || die "rsync é obrigatório para instalação idempotente"
command -v flock >/dev/null || die "flock é obrigatório"

if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  log "criando usuário técnico ${SERVICE_USER} (sem login, sem docker)"
  useradd --system --home "${STATE_DIR}" --shell /usr/sbin/nologin \
    --user-group "${SERVICE_USER}"
else
  log "usuário ${SERVICE_USER} já existe — preservado (não altera grupos)"
fi

if id -nG "${SERVICE_USER}" 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
  log "AVISO: ${SERVICE_USER} já pertence ao grupo docker (decisão prévia). Coleta Docker pode funcionar; isso não foi concedido por este instalador."
else
  log "Docker: ${SERVICE_USER} fora do grupo docker — seção docker pode ficar partial/unavailable"
fi

install -d -m 0755 -o root -g root /opt/delpi
install -d -m 0755 -o root -g root "${INSTALL_ROOT}"
install -d -m 0755 -o root -g root "${INSTALL_ROOT}/bin"
install -d -m 0755 -o root -g root "${INSTALL_ROOT}/vendor"
harden_state_and_env

# Ownership root ANTES de qualquer pip privilegiado (evita pip sobre árvore editável pelo serviço).
harden_install_tree

log "sincronizando artefatos versionados do coletor → ${INSTALL_ROOT}"
rsync -a --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.venv/' \
  --exclude '*.egg-info/' \
  --exclude '*Zone.Identifier*' \
  "${IT_PORTAL_API_DIR}/collectors/" "${INSTALL_ROOT}/collectors/"

log "sincronizando somente shared/delpi_auth (sem árvore shared completa)"
rm -rf "${INSTALL_ROOT}/vendor/shared"
install -d -m 0755 -o root -g root "${INSTALL_ROOT}/vendor/shared"
rsync -a --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '*.egg-info/' \
  --exclude '.venv/' \
  --exclude 'tests/' \
  --exclude '*Zone.Identifier*' \
  --exclude '.env' \
  --exclude '*.pem' \
  --exclude '*.key' \
  --exclude '*.secret' \
  "${SHARED_DIR}/delpi_auth/" "${INSTALL_ROOT}/vendor/shared/delpi_auth/"
install -m 0644 "${VENDOR_PYPROJECT}" "${INSTALL_ROOT}/vendor/shared/pyproject.toml"

install -m 0644 "${SCRIPT_DIR}/requirements-collector.txt" "${INSTALL_ROOT}/requirements-collector.txt"
install -m 0644 "${SCRIPT_DIR}/README.md" "${INSTALL_ROOT}/README.md"
install -m 0755 "${SCRIPT_DIR}/run-collector.sh" "${INSTALL_ROOT}/bin/run-collector"
install -m 0755 "${SCRIPT_DIR}/verify-collector-permissions.sh" \
  "${INSTALL_ROOT}/bin/verify-collector-permissions"

# Reafirma root ownership após rsync/install (antes do pip).
harden_install_tree

if [[ ! -x "${INSTALL_ROOT}/venv/bin/python" ]]; then
  log "criando venv root-owned em ${INSTALL_ROOT}/venv"
  "${PYTHON_BIN}" -m venv "${INSTALL_ROOT}/venv"
  harden_install_tree
fi

log "instalando dependências pinadas no venv (não-editable)"
"${INSTALL_ROOT}/venv/bin/pip" install --upgrade pip
"${INSTALL_ROOT}/venv/bin/pip" install -r "${INSTALL_ROOT}/requirements-collector.txt"
# Instalação não-editable: código vai para site-packages root-owned, não fica -e sobre vendor.
"${INSTALL_ROOT}/venv/bin/pip" install --no-deps "${INSTALL_ROOT}/vendor/shared"

SOURCE_SHA="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
printf '%s\n' "${SOURCE_SHA}" > "${INSTALL_ROOT}/SOURCE_SHA"

# Pós-pip / pós-reinstall: ownership e modos finais.
harden_install_tree
harden_state_and_env

if [[ ! -f "${ENV_FILE}" ]]; then
  install -m 0640 -o root -g "${SERVICE_GROUP}" "${ENV_EXAMPLE}" "${ENV_FILE}"
  log "criado ${ENV_FILE} a partir do exemplo — SUBSTITUA S2S_CLIENT_SECRET antes do submit"
else
  log "preservando ${ENV_FILE} existente (não sobrescrito)"
  chown "root:${SERVICE_GROUP}" "${ENV_FILE}"
  chmod 0640 "${ENV_FILE}"
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

log "verificando permissões (negativa de escrita no código / positiva no state)"
"${INSTALL_ROOT}/bin/verify-collector-permissions"

cat <<EOF

Instalação concluída (timer NÃO habilitado).

Ownership:
  ${INSTALL_ROOT}          → root:root (serviço: leitura/execução, sem escrita)
  ${STATE_DIR}             → ${SERVICE_USER}:${SERVICE_GROUP} (único gravável)
  ${ENV_FILE}              → root:${SERVICE_GROUP} 0640

Artefatos:
  source_sha=${SOURCE_SHA}
  user=${SERVICE_USER} (sem login; docker NÃO concedido por este script)
  vendor=somente delpi_auth + manifesto mínimo (sem shared/ completo)

Próximos passos no srv-api:
  1) Editar ${ENV_FILE} (secret S2S + SERVER_ID).
  2) sudo -u ${SERVICE_USER} ${INSTALL_ROOT}/bin/run-collector diagnose
  3) sudo systemctl start it-portal-linux-collector.service
  4) Somente após aceite operacional:
       sudo systemctl enable --now it-portal-linux-collector.timer

Desativar:
  sudo systemctl disable --now it-portal-linux-collector.timer

Rollback das units:
  sudo systemctl disable --now it-portal-linux-collector.timer || true
  sudo rm -f ${SYSTEMD_DIR}/it-portal-linux-collector.service \\
             ${SYSTEMD_DIR}/it-portal-linux-collector.timer
  sudo systemctl daemon-reload
EOF
