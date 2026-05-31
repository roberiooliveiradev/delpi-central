#!/usr/bin/env python3
"""Valida alinhamento entre identity.json e features_catalog.json (autoajuda Fase 1)."""

from __future__ import annotations

import sys

from app.infrastructure.content.content_service import ContentService


def main() -> int:
    errors: list[str] = []

    try:
        identity = ContentService.load_json("assistant/identity")
        catalog = ContentService.load_json("assistant/features_catalog")
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"FAIL conteúdo: {exc}", file=sys.stderr)
        return 1

    sync = identity.get("catalogSync")

    if not isinstance(sync, dict):
        errors.append("identity.json: catalogSync ausente")
    else:
        catalog_version = str(catalog.get("version") or "").strip()
        sync_version = str(sync.get("version") or "").strip()

        if not sync_version:
            errors.append("identity.catalogSync.version ausente")
        elif catalog_version and sync_version != catalog_version:
            errors.append(
                f"identity.catalogSync.version ({sync_version}) != features_catalog.version ({catalog_version})"
            )

        declared_ids = sync.get("featureIds")

        if not isinstance(declared_ids, list) or not declared_ids:
            errors.append("identity.catalogSync.featureIds vazio ou inválido")
        else:
            catalog_ids = {
                str(item.get("id") or "").strip()
                for item in (catalog.get("features") or [])
                if isinstance(item, dict) and str(item.get("id") or "").strip()
            }
            declared_set = {str(item).strip() for item in declared_ids if str(item).strip()}

            missing_in_identity = sorted(catalog_ids - declared_set)
            extra_in_identity = sorted(declared_set - catalog_ids)

            if missing_in_identity:
                errors.append(
                    "featureIds em identity.json faltando no catálogo: "
                    + ", ".join(missing_in_identity[:12])
                )

            if extra_in_identity:
                errors.append(
                    "featureIds em identity.json sem entrada no catálogo: "
                    + ", ".join(extra_in_identity[:12])
                )

    if errors:
        for line in errors:
            print(f"FAIL {line}", file=sys.stderr)
        return 1

    print("OK identity.json alinhado ao features_catalog.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
