#!/usr/bin/env python3
"""Verifica dependências opcionais do profile Docker `vision` (Onda 13)."""

from __future__ import annotations

import sys


def _check(label: str, import_fn) -> bool:
    try:
        import_fn()
        print(f"OK {label}")
        return True
    except ImportError:
        print(f"SKIP {label} (não instalado)")
        return False


def main() -> int:
    docling = _check("docling", lambda: __import__("docling"))
    paddle = _check("paddleocr", lambda: __import__("paddleocr"))

    if not docling and not paddle:
        print(
            "Profile vision: use infra/docker-compose.vision.yml e "
            "descomente pacotes em requirements-vision.txt para backends neurais."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
