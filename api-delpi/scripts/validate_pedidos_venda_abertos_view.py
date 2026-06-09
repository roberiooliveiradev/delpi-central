#!/usr/bin/env python3
"""Validação Fase 0 — view dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES (TOTVS)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.infrastructure.persistence.totvs.base_repository import BaseRepository  # noqa: E402

VIEW = "dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES"


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


class _ValidationRepository(BaseRepository):
    def run(self, query: str, params: tuple = ()) -> list[dict]:
        with self:
            return self.execute_query(query, params)

    def run_one(self, query: str, params: tuple = ()) -> dict | None:
        with self:
            return self.execute_one(query, params)


def build_report() -> dict:
    repo = _ValidationRepository()
    sample = repo.run(
        f"SELECT TOP 10 nome_cliente, tipo_entidade, filial, pedido, saldo, data_despacho, data_entrega FROM {VIEW} ORDER BY data_entrega DESC"
    )
    volume = repo.run_one(f"SELECT COUNT(*) AS total_linhas FROM {VIEW}") or {}
    summary = repo.run_one(
        f"SELECT COUNT(*) AS total_linhas, ISNULL(SUM(valor_aberto),0) AS valor_total_aberto FROM {VIEW}"
    ) or {}
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "view": VIEW,
        "ready_for_phase_1": len(sample) > 0,
        "sample_count": len(sample),
        "volume": volume,
        "summary": summary,
        "sample": sample,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default))
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return 0 if report["ready_for_phase_1"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
