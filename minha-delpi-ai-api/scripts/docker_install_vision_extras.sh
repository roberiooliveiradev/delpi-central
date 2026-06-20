#!/usr/bin/env bash
# Instala extras de visão na CAMADA da imagem Docker (permanente após build).
# Não usar no entrypoint — runtime pip quebra recreate e gera 502 no gateway.
#
# Variáveis:
#   INSTALL_VISION_EXTRAS   true (default dev) | false (prod mínimo)
#   CHAT_EASYOCR_MODEL_DIR    destino dos pesos EasyOCR (prefetch no build)

set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
REQ_FILE="${APP_ROOT}/requirements-vision.txt"
INSTALL_VISION_EXTRAS="${INSTALL_VISION_EXTRAS:-true}"

if [ "$INSTALL_VISION_EXTRAS" != "true" ]; then
  echo "⏭️  INSTALL_VISION_EXTRAS=false — extras de visão omitidos no build."
  exit 0
fi

if [ ! -f "$REQ_FILE" ]; then
  echo "❌ ${REQ_FILE} ausente — build de visão abortado." >&2
  exit 1
fi

if ! grep -v '^[[:space:]]*#' "$REQ_FILE" | grep -q '[a-zA-Z0-9]'; then
  echo "❌ requirements-vision.txt sem pacotes ativos — build de visão abortado." >&2
  exit 1
fi

echo "📦 [build] Extras de visão permanentes — PyTorch CPU + requirements-vision…"
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir -r "$REQ_FILE"

echo "📥 [build] Prefetch de modelos EasyOCR (camada da imagem)…"
python3 "${APP_ROOT}/scripts/prefetch_vision_models.py"

echo "🔍 [build] Verificando extras de visão na imagem…"
python3 "${APP_ROOT}/scripts/check_vision_profile_deps.py" --require-easyocr --require-easyocr-models

echo "✅ Extras de visão instalados permanentemente na imagem."
