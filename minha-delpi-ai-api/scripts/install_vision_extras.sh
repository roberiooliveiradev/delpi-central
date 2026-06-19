#!/usr/bin/env bash
# Instala dependências opcionais de visão/OCR — uso MANUAL ou CI, não no entrypoint.
# Idempotente: só instala quando os pacotes Python ainda não estão importáveis.
#
# Variáveis:
#   CHAT_VISION_EXTRAS_RUNTIME_INSTALL  true para permitir pip install (não usar na subida normal)
#   CHAT_VISION_EXTRAS_FORCE            true para forçar pip install -r requirements-vision.txt

set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
REQ_FILE="${APP_ROOT}/requirements-vision.txt"

if [ "${CHAT_VISION_EXTRAS_RUNTIME_INSTALL:-false}" != "true" ]; then
  echo "⏭️  Runtime install desligado — extras devem vir do build da imagem."
  echo "    Para instalar manualmente: CHAT_VISION_EXTRAS_RUNTIME_INSTALL=true $0"
  if [ -f "${APP_ROOT}/scripts/check_vision_profile_deps.py" ]; then
    python3 "${APP_ROOT}/scripts/check_vision_profile_deps.py" || true
  fi
  exit 0
fi

if [ ! -f "$REQ_FILE" ]; then
  echo "⚠️  ${REQ_FILE} ausente — extras de visão ignorados."
  exit 0
fi

if ! grep -v '^[[:space:]]*#' "$REQ_FILE" | grep -q '[a-zA-Z0-9]'; then
  echo "⏭️  requirements-vision.txt sem pacotes ativos."
  exit 0
fi

need_install=false

if [ "${CHAT_VISION_EXTRAS_FORCE:-false}" = "true" ]; then
  need_install=true
elif ! python3 -c "import easyocr" >/dev/null 2>&1; then
  need_install=true
fi

if [ "$need_install" = "true" ]; then
  echo "📦 Instalando extras de visão (requirements-vision.txt) — pode levar alguns minutos na primeira subida…"

  if command -v apt-get >/dev/null 2>&1; then
    if ! dpkg -s libgl1 >/dev/null 2>&1; then
      apt-get update
      DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        poppler-utils
      rm -rf /var/lib/apt/lists/*
    fi
  fi

  pip install --no-cache-dir -r "$REQ_FILE"
  python3 "${APP_ROOT}/scripts/prefetch_vision_models.py" || true
else
  echo "✅ Extras de visão já disponíveis (easyocr)."
fi

if [ -f "${APP_ROOT}/scripts/check_vision_profile_deps.py" ]; then
  python3 "${APP_ROOT}/scripts/check_vision_profile_deps.py" || true
fi
