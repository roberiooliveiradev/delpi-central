#!/usr/bin/env python3
"""
Migração Transforma+ (Google Sheets / CSV) → Postgres transformometro.

Uso:
  cd transformometro-api
  python scripts/migrate_transforma_mais_sheet.py --preview
  python scripts/migrate_transforma_mais_sheet.py --apply --replace
  python scripts/migrate_transforma_mais_sheet.py --apply --csv-dir ./exports

Requer PLUGINS_DB_* e TRANSFORMA_MAIS_* no ambiente (ou .env na raiz do monorepo).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tm_app.application.services.sheet_import_service import SheetImportService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa planilha Transforma+ para Postgres.")
    parser.add_argument("--preview", action="store_true", help="Somente validação e resumo.")
    parser.add_argument("--apply", action="store_true", help="Grava no banco.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Apaga cadastro existente antes de importar (CUIDADO).",
    )
    parser.add_argument("--no-recalc", action="store_true", help="Não dispara recálculo do dashboard.")
    parser.add_argument("--csv-dir", type=str, default=None, help="Pasta com CSVs exportados.")
    args = parser.parse_args()

    if not args.preview and not args.apply:
        parser.error("Informe --preview ou --apply.")

    csv_dir = Path(args.csv_dir).resolve() if args.csv_dir else None
    service = SheetImportService()

    if args.preview:
        result = service.preview(csv_dir=csv_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        ok = result.get("validation", {}).get("ok", False)
        return 0 if ok else 1

    result = service.apply(
        csv_dir=csv_dir,
        replace_existing=args.replace,
        recalc_dashboard=not args.no_recalc,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    diff = result.get("diff", {})
    return 0 if diff.get("all_match", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
