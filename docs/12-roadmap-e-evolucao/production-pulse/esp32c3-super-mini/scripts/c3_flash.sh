#!/usr/bin/env bash
# Flash / compile helper — ESP32-C3 Super Mini (Production Pulse)
# Requires: arduino-cli + esp32:esp32@3.3.11 in PATH (see evidence E1).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../../.." && pwd)"
SKETCH="$ROOT/docs/12-roadmap-e-evolucao/production-pulse/firmware/esp32c3_counter_v1"
OUT="${PP_C3_BUILD_DIR:-/tmp/esp32c3_counter_v1_build}"
FQBN="${PP_C3_FQBN:-esp32:esp32:esp32c3:UploadSpeed=115200,CPUFreq=160,FlashFreq=80,FlashMode=qio,FlashSize=4M,PartitionScheme=min_spiffs}"

export PATH="${HOME}/bin:${PATH}"

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli não encontrado. Instale em ~/bin (ver evidence E1)." >&2
  exit 1
fi

cmd="${1:-compile}"
shift || true

case "$cmd" in
  compile)
    mkdir -p "$OUT"
    echo "FQBN=$FQBN"
    arduino-cli compile --fqbn "$FQBN" --output-dir "$OUT" --warnings all "$SKETCH"
    ls -lh "$OUT"/esp32c3_counter_v1.ino.bin
    ;;
  list)
    arduino-cli board list
    ;;
  upload)
    port="${1:-}"
    if [[ -z "$port" ]]; then
      echo "Uso: $0 upload /dev/ttyACM0" >&2
      echo "Dica WSL2: usbipd attach --wsl --busid <BUSID> no Windows, depois $0 list" >&2
      exit 1
    fi
    mkdir -p "$OUT"
    arduino-cli compile --fqbn "$FQBN" --output-dir "$OUT" "$SKETCH"
    arduino-cli upload -p "$port" --fqbn "$FQBN" --input-dir "$OUT" "$SKETCH"
    echo "Upload OK. Serial: arduino-cli monitor -p $port -c baudrate=115200"
    ;;
  monitor)
    port="${1:-}"
    if [[ -z "$port" ]]; then
      echo "Uso: $0 monitor /dev/ttyACM0" >&2
      exit 1
    fi
    arduino-cli monitor -p "$port" -c baudrate=115200
    ;;
  *)
    echo "Uso: $0 {compile|list|upload <port>|monitor <port>}" >&2
    exit 1
    ;;
esac
