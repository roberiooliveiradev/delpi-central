#!/usr/bin/env python3
"""Lê a planilha de kaizens (Google Sheets), trata os dados e gera um JSON importável.

Modos de uso (rodar com o ambiente da api-delpi, ex.: dentro do container
``delpi-api-delpi`` ou com o ``.env`` da api-delpi carregado):

1. Só gerar o JSON tratado (não toca no banco):

    python scripts/kaizen_sheet_to_json.py --out scripts/out/kaizens.json

2. Aplicar no banco LOCAL (apaga os kaizens atuais e recarrega da planilha):

    python scripts/kaizen_sheet_to_json.py --apply

O arquivo gerado tem o mesmo formato do endpoint ``GET /quality/kaizens/records/export``
e pode ser enviado à produção pela tela "Importar JSON" ou pelo endpoint
``POST /quality/kaizens/records/import``.

ATENÇÃO: ``--apply`` é DESTRUTIVO e destinado ao ambiente local. Ele executa
``TRUNCATE`` nas tabelas de kaizen antes de reimportar.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.composition.quality_composer import _build_kaizen_repository  # noqa: E402
from app.domain.services.kaizen.kaizen_sheet_import_mapper import (  # noqa: E402
    sheet_detail_to_record_fields,
)
from app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_repository import (  # noqa: E402
    PostgresKaizenRepository,
)

EXPORT_VERSION = 1
VALID_BRANCHES = {"01", "02"}
IMPORT_ACTOR_ID = "sheet-import"
IMPORT_ACTOR_NAME = "Importação da planilha (script local)"

_KAIZEN_TABLES = (
    "quality.kaizen_audit_log",
    "quality.kaizen_history",
    "quality.kaizen_evidences",
    "quality.kaizen_participants",
    "quality.kaizen_revisions",
    "quality.kaizens",
)


def build_payload() -> tuple[dict, list[dict]]:
    repository = _build_kaizen_repository()
    details = repository.list_active_kaizen_details()

    items: list[dict] = []
    skipped: list[dict] = []
    for detail in details:
        fields = sheet_detail_to_record_fields(detail)
        branch = str(fields.get("branch_code") or "").strip()
        title = str(fields.get("title") or "").strip()
        if branch not in VALID_BRANCHES or not title:
            skipped.append(
                {
                    "sheet_id": detail.id,
                    "title": title,
                    "branch_code": branch,
                    "reason": "invalid_branch" if title else "missing_title",
                }
            )
            continue
        items.append(fields)

    payload = {
        "version": EXPORT_VERSION,
        "source": "google_sheets",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    return payload, skipped


def wipe_local_kaizens(repo: PostgresKaizenRepository) -> None:
    tables = ", ".join(_KAIZEN_TABLES)
    repo.execute(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")


def apply_local(items: list[dict], *, wipe: bool) -> tuple[int, list[tuple[str, str]]]:
    repo = PostgresKaizenRepository()
    if wipe:
        wipe_local_kaizens(repo)

    created = 0
    errors: list[tuple[str, str]] = []
    for item in items:
        try:
            repo.create_record(
                fields=dict(item),
                created_by_user_id=IMPORT_ACTOR_ID,
                actor_name=IMPORT_ACTOR_NAME,
            )
            created += 1
        except Exception as exc:  # noqa: BLE001 — reporta por item
            errors.append((str(item.get("title") or "?"), str(exc)))
    return created, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta kaizens da planilha para JSON tratado.")
    parser.add_argument(
        "--out",
        default=str(ROOT / "scripts" / "out" / "kaizens_from_sheet.json"),
        help="Caminho do arquivo JSON de saída.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica no banco LOCAL: apaga os kaizens atuais e recarrega da planilha.",
    )
    parser.add_argument(
        "--no-wipe",
        action="store_true",
        help="Com --apply, não apaga os dados atuais (apenas insere).",
    )
    args = parser.parse_args()

    payload, skipped = build_payload()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Kaizens tratados: {payload['count']}")
    if skipped:
        print(f"Ignorados: {len(skipped)}")
        for item in skipped:
            print(f"  - [{item['reason']}] {item.get('title') or item.get('sheet_id')}")
    print(f"Arquivo gerado: {out_path}")

    if args.apply:
        wipe = not args.no_wipe
        print(f"\nAplicando no banco local (wipe={'sim' if wipe else 'não'})…")
        created, errors = apply_local(payload["items"], wipe=wipe)
        print(f"Kaizens criados: {created}")
        if errors:
            print(f"Erros: {len(errors)}")
            for title, reason in errors:
                print(f"  - {title}: {reason}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
