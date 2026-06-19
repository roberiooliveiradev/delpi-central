#!/usr/bin/env python3
"""Baixa pesos EasyOCR para diretório fixo — executar no BUILD da imagem Docker."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _model_dir() -> Path:
    raw = os.environ.get("CHAT_EASYOCR_MODEL_DIR", "/opt/delpi-vision/easyocr").strip()
    return Path(raw or "/opt/delpi-vision/easyocr")


def main() -> int:
    model_dir = _model_dir()
    model_dir.mkdir(parents=True, exist_ok=True)

    try:
        import easyocr
    except ImportError:
        print("SKIP prefetch EasyOCR — pacote não instalado.")
        return 0

    languages = ["pt", "en"]
    print(f"Prefetch EasyOCR → {model_dir} ({', '.join(languages)})")

    easyocr.Reader(
        languages,
        gpu=False,
        verbose=False,
        model_storage_directory=str(model_dir),
    )

    artifacts = list(model_dir.glob("**/*"))
    if not artifacts:
        print("ERRO: prefetch EasyOCR não gerou arquivos.", file=sys.stderr)
        return 1

    print(f"OK EasyOCR prefetch ({len(artifacts)} artefato(s) em {model_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
