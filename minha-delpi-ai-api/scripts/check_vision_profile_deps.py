#!/usr/bin/env python3
"""Verifica dependências de visão/OCR no container."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def _check_import(label: str, import_fn) -> bool:
    try:
        import_fn()
        print(f"OK {label}")
        return True
    except ImportError:
        print(f"SKIP {label} (não instalado)")
        return False


def _check_easyocr_models() -> bool:
    model_dir = os.environ.get("CHAT_EASYOCR_MODEL_DIR", "").strip()

    if not model_dir:
        print("SKIP easyocr models (CHAT_EASYOCR_MODEL_DIR não definido)")
        return True

    path = Path(model_dir)

    if not path.is_dir():
        print(f"SKIP easyocr models (diretório ausente: {model_dir})")
        return False

    artifacts = [item for item in path.rglob("*") if item.is_file()]

    if not artifacts:
        print(f"SKIP easyocr models (diretório vazio: {model_dir})")
        return False

    print(f"OK easyocr models ({len(artifacts)} arquivo(s) em {model_dir})")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica extras de visão/OCR.")
    parser.add_argument(
        "--require-easyocr",
        action="store_true",
        help="Falha (exit 1) se easyocr não estiver importável — uso no build Docker.",
    )
    parser.add_argument(
        "--require-easyocr-models",
        action="store_true",
        help="Falha se CHAT_EASYOCR_MODEL_DIR estiver definido mas vazio.",
    )
    args = parser.parse_args()

    tesseract = bool(shutil.which("tesseract"))
    print("OK tesseract" if tesseract else "SKIP tesseract (binário ausente)")

    easyocr = _check_import("easyocr", lambda: __import__("easyocr"))
    docling = _check_import("docling", lambda: __import__("docling"))
    paddle = _check_import("paddleocr", lambda: __import__("paddleocr"))
    easyocr_models = _check_easyocr_models() if easyocr else False

    try:
        import pytesseract  # noqa: F401

        print("OK pytesseract")
    except ImportError:
        print("SKIP pytesseract (não instalado)")

    if not easyocr:
        print(
            "Dica: rebuild da imagem com INSTALL_VISION_EXTRAS=true "
            "ou scripts/docker_install_vision_extras.sh no Dockerfile."
        )

    if not docling and not paddle:
        print(
            "Backends docling/paddleocr opcionais — descomente em requirements-vision.txt "
            "ou use CHAT_DOCUMENT_VISION_BACKEND=tesseract|auto."
        )

    if args.require_easyocr and not easyocr:
        return 1

    if args.require_easyocr_models and easyocr and not easyocr_models:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
