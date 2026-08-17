#!/usr/bin/env python3
"""Valida o catálogo canônico de notificações (`app/content/notification_catalog.json`)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.infrastructure.content.notification_catalog_loader import (  # noqa: E402
    default_catalog_path,
    load_notification_catalog,
)


def _check_portal_fallback(catalog_ids: set[str]) -> list[str]:
    """Garante que o FALLBACK do portal declara notificationLabel para cada id."""
    portal_path = (
        REPO / "portal" / "src" / "utils" / "notificationCatalog.ts"
    )
    if not portal_path.is_file():
        return [f"portal fallback missing: {portal_path}"]

    text = portal_path.read_text(encoding="utf-8")
    errors: list[str] = []
    for category_id in sorted(catalog_ids):
        # Bloco mínimo: id + notificationLabel no mesmo objeto do FALLBACK.
        pattern = (
            rf'id:\s*"{re.escape(category_id)}"[^}}]*notificationLabel:\s*"[^"]+"'
        )
        if not re.search(pattern, text, flags=re.DOTALL):
            errors.append(
                f"portal FALLBACK missing notificationLabel for category '{category_id}'"
            )
    return errors


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

    missing_titles = [
        category_id
        for category_id, spec in catalog.categories.items()
        if not (spec.notification_label or "").strip()
    ]
    if missing_titles:
        print(
            "ERROR: notificationLabel obrigatório ausente: "
            + ", ".join(sorted(missing_titles)),
            file=sys.stderr,
        )
        return 1

    portal_errors = _check_portal_fallback(set(catalog.categories.keys()))
    if portal_errors:
        for err in portal_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    app_sources = [
        category_id
        for category_id, spec in catalog.categories.items()
        if spec.kind == "app"
    ]

    print(f"notification_catalog ok: version={catalog.version} categories={len(catalog.categories)}")
    print(f"  app sources: {', '.join(sorted(app_sources)) or '(nenhum)'}")
    print(
        f"  mutable: {len(catalog.mutable_categories)} / immutable: "
        f"{len(catalog.allowed_categories) - len(catalog.mutable_categories)}"
    )
    print("  preference pattern: notificationLabel → app → status (+ icon)")

    if args.check:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
