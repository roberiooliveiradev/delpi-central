#!/usr/bin/env python3
"""Valida o catálogo canônico de notificações (`app/content/notification_catalog.json`)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.infrastructure.content.notification_catalog_loader import (  # noqa: E402
    default_catalog_path,
    load_notification_catalog,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Carrega o JSON e falha se inválido (uso em CI).",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Caminho alternativo do catálogo (testes).",
    )
    args = parser.parse_args()

    catalog_path = args.path or default_catalog_path()
    catalog = load_notification_catalog(catalog_path)

    app_sources = [
        category_id
        for category_id, spec in catalog.categories.items()
        if spec.kind == "app"
    ]

    print(f"notification_catalog ok: version={catalog.version} categories={len(catalog.categories)}")
    print(f"  app sources: {', '.join(sorted(app_sources)) or '(nenhum)'}")
    print(f"  mutable: {len(catalog.mutable_categories)} / immutable: {len(catalog.allowed_categories) - len(catalog.mutable_categories)}")

    if args.check:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
