#!/usr/bin/env python3
"""Validação Fase 0 — view dbo.VW_PD3_BENEF_RETORNOS (TOTVS)."""
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

from app.domain.totvs.protheus_third_party_materials import (  # noqa: E402
    CONTROL_DIFFERENCE_TOLERANCE,
    VIEW_NAME,
)
from app.infrastructure.persistence.totvs.base_repository import (  # noqa: E402
    BaseRepository,
)

ACCEPTANCE_BRANCH = "01"
ACCEPTANCE_PRODUCT = "10211413"
EXPECTED_SHIPMENTS = 43
EXPECTED_RETURNS = 397
EXPECTED_WITH_BALANCE = 3
EXPECTED_PENDING_BALANCE = Decimal("11419")


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
    params = (ACCEPTANCE_BRANCH, ACCEPTANCE_PRODUCT)
    shipments = repo.run_one(
        f"""
        SELECT COUNT(DISTINCT RECNO_REMESSA) AS total_remessas
        FROM {VIEW_NAME}
        WHERE FILIAL = ? AND PRODUTO = ?
        """,
        params,
    ) or {}
    returns = repo.run_one(
        f"""
        SELECT COUNT(RECNO_RETORNO) AS total_retornos
        FROM {VIEW_NAME}
        WHERE FILIAL = ? AND PRODUTO = ? AND RECNO_RETORNO IS NOT NULL
        """,
        params,
    ) or {}
    open_rows = repo.run(
        f"""
        SELECT DISTINCT
            RECNO_REMESSA,
            NF_RECEBIMENTO,
            QTD_RECEBIDA,
            QTD_DEVOLVIDA_TOTAL,
            SALDO_A_ENTREGAR,
            STATUS_REMESSA
        FROM {VIEW_NAME}
        WHERE FILIAL = ? AND PRODUTO = ? AND POSSUI_SALDO = 'S'
        ORDER BY NF_RECEBIMENTO
        """,
        params,
    )
    pending = repo.run_one(
        f"""
        SELECT CAST(ISNULL(SUM(SALDO_A_ENTREGAR), 0) AS decimal(28, 8)) AS saldo_pendente
        FROM (
            SELECT DISTINCT RECNO_REMESSA, SALDO_A_ENTREGAR
            FROM {VIEW_NAME}
            WHERE FILIAL = ? AND PRODUTO = ?
        ) T
        """,
        params,
    ) or {}
    audit = repo.run_one(
        f"""
        SELECT COUNT(*) AS divergencias
        FROM (
            SELECT DISTINCT RECNO_REMESSA, DIFERENCA_CONTROLE
            FROM {VIEW_NAME}
            WHERE FILIAL = ? AND PRODUTO = ?
              AND ABS(DIFERENCA_CONTROLE) > ?
        ) T
        """,
        (*params, CONTROL_DIFFERENCE_TOLERANCE),
    ) or {}
    sample = repo.run(
        f"""
        SELECT TOP 5
            RECNO_REMESSA, NF_RECEBIMENTO, STATUS_REMESSA, SALDO_A_ENTREGAR, NF_RETORNO
        FROM {VIEW_NAME}
        WHERE FILIAL = ? AND PRODUTO = ?
        ORDER BY EMISSAO_RECEBIMENTO DESC, RECNO_REMESSA, RECNO_RETORNO
        """,
        params,
    )

    total_shipments = int(shipments.get("total_remessas") or 0)
    total_returns = int(returns.get("total_retornos") or 0)
    pending_balance = Decimal(str(pending.get("saldo_pendente") or 0))
    divergences = int(audit.get("divergencias") or 0)
    ready = (
        total_shipments == EXPECTED_SHIPMENTS
        and total_returns == EXPECTED_RETURNS
        and len(open_rows) == EXPECTED_WITH_BALANCE
        and abs(pending_balance - EXPECTED_PENDING_BALANCE) <= Decimal(str(CONTROL_DIFFERENCE_TOLERANCE))
        and divergences == 0
    )
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "view": VIEW_NAME,
        "acceptance": {
            "branch": ACCEPTANCE_BRANCH,
            "product": ACCEPTANCE_PRODUCT,
            "expected_shipments": EXPECTED_SHIPMENTS,
            "expected_returns": EXPECTED_RETURNS,
            "expected_with_balance": EXPECTED_WITH_BALANCE,
            "expected_pending_balance": float(EXPECTED_PENDING_BALANCE),
        },
        "observed": {
            "shipments": total_shipments,
            "returns": total_returns,
            "with_balance": len(open_rows),
            "pending_balance": float(pending_balance),
            "control_difference_rows": divergences,
            "open_shipments": open_rows,
        },
        "ready_for_phase_1": ready,
        "sample": sample,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default))
    if args.json:
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
    return 0 if report["ready_for_phase_1"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
