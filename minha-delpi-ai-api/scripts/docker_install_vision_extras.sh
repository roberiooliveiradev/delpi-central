#!/usr/bin/env bash
# Instala extras de visão durante o BUILD da imagem Docker (não usar no entrypoint).
#
# Variáveis:
#   INSTALL_VISION_EXTRAS   true|false — prod usa false por padrão; dev usa true
#   CHAT_EASYOCR_MODEL_DIR  destino dos pesos EasyOCR (prefetch no build)

set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
REQ_FILE="${APP_ROOT}/requirements-vision.txt"
INSTALL_VISION_EXTRAS="${INSTALL_VISION_EXTRAS:-true}"

if [ "$INSTALL_VISION_EXTRAS" != "true" ]; then
  echo "⏭️  INSTALL_VISION_EXTRAS=false — extras de visão omitidos no build."
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

echo "📦 [build] Instalando requirements-vision.txt…"
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r "$REQ_FILE"

echo "📥 [build] Prefetch de modelos EasyOCR…"
python3 "${APP_ROOT}/scripts/prefetch_vision_models.py"

echo "🔍 [build] Verificando extras de visão…"
python3 "${APP_ROOT}/scripts/check_vision_profile_deps.py" --require-easyocr

echo "✅ Extras de visão instalados na imagem."
