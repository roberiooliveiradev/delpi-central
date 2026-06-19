#!/usr/bin/env python3
"""Verifica dependências de visão/OCR no container."""

from __future__ import annotations

import shutil
import sys


def _check_import(label: str, import_fn) -> bool:
    try:
        import_fn()
        print(f"OK {label}")
        return True
    except ImportError:
        print(f"SKIP {label} (não instalado)")
        return False


def main() -> int:
    tesseract = bool(shutil.which("tesseract"))
    print("OK tesseract" if tesseract else "SKIP tesseract (binário ausente)")

    easyocr = _check_import("easyocr", lambda: __import__("easyocr"))
    docling = _check_import("docling", lambda: __import__("docling"))
    paddle = _check_import("paddleocr", lambda: __import__("paddleocr"))

    try:
        import pytesseract  # noqa: F401

        print("OK pytesseract")
    except ImportError:
        print("SKIP pytesseract (não instalado)")

    if not easyocr:
        print(
            "Dica: rode scripts/install_vision_extras.sh ou rebuild da imagem "
            "com requirements-vision.txt (EasyOCR)."
        )

    if not docling and not paddle:
        print(
            "Backends docling/paddleocr opcionais — descomente em requirements-vision.txt "
            "ou use CHAT_DOCUMENT_VISION_BACKEND=tesseract|auto."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
