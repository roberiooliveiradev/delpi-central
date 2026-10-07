#!/usr/bin/env python3
"""
Investigação DAVI-INVENTORY-ADJUSTMENT-REPORT — reverse engineering do
relatório Protheus de ajustes de inventário.

Uso:
  docker exec -w /app delpi-api-delpi env PYTHONPATH=/app \\
    python scripts/investigate_inventory_adjustment_report.py

Saída:
  docs/roadmaps/evidencias/inventory-adjustment-report-investigacao.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.infrastructure.persistence.totvs.base_repository import BaseRepository

_SCRIPT_DIR = Path(__file__).resolve().parent
_SQL_PATH = _SCRIPT_DIR / "sql" / "investigate_inventory_adjustment_report.sql"
_EVIDENCE_DIR = _SCRIPT_DIR.parent / "docs" / "roadmaps" / "evidencias"

RESULTSET_NAMES = (
    "sx3_sd3_cost_fields",
    "sx3_sb_cost_fields",
    "tmcf_distribution",
    "seqcalc_distribution",
    "window_movements",
    "sample_unit_costs",
    "sb2_current",
    "sb9_closures_f02",
    "sb9_for_products",
    "sf5_tm_lookup",
    "estorno_check",
)


def main() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    with BaseRepository() as repo:
        resultsets = repo.execute_query_multiple(sql, ())

    named = {}
    for i, rs in enumerate(resultsets):
        name = RESULTSET_NAMES[i] if i < len(RESULTSET_NAMES) else f"resultset_{i}"
        named[name] = rs["data"]

    _EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = _EVIDENCE_DIR / "inventory-adjustment-report-investigacao.json"
    out.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "window": {
                    "branch": "02",
                    "start": "2026-09-04",
                    "end_exclusive": "2026-09-30",
                    "warehouses": ["01", "99"],
                    "doc": "INVENT",
                },
                "resultsets": named,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    for name, data in named.items():
        print(f"{name}: {len(data)} rows")
    print(f"written: {out}")


if __name__ == "__main__":
    main()
