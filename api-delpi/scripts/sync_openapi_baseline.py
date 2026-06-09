#!/usr/bin/env python3
"""Gera/atualiza app/content/openapi_baseline.json a partir do OpenAPI da aplicação."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domain.services.openapi_baseline_service import save_openapi_baseline  # noqa: E402
from app.main import app  # noqa: E402


def main() -> int:
    target = save_openapi_baseline(app.openapi())
    print(f"Baseline OpenAPI atualizado: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
