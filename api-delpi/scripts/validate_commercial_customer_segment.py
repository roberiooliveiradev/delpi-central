#!/usr/bin/env python3
"""Valida filtro WEG vs novos negócios no dashboard comercial.

Compara totais consolidados (sem filtro) com weg + new_business e executa
amostra SQL em AD1010 para jun/2026.

Uso:
  docker exec delpi-api-delpi python scripts/validate_commercial_customer_segment.py \\
    --start 2026-06-01 --end 2026-06-30
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.application.dto.commercial.new_business_rol_pct_request import (
    NewBusinessRolPctRequest,
)
from app.application.dto.commercial.sales_conversion_rate_request import (
    SalesConversionRateRequest,
)
from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
)
from app.domain.services.commercial_proposal_status import WON_STATUS_CODE
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_proposals_repository import (
    CommercialProposalsRepository,
)
from app.infrastructure.persistence.totvs.commercial_repositories.new_business_rol_pct_repository import (
    NewBusinessRolPctRepository,
)
from app.infrastructure.persistence.totvs.commercial_repositories.sales_conversion_rate_repository import (
    SalesConversionRateRepository,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def _sql_ad1_segment_counts(start: str, end: str) -> tuple[str, tuple]:
    qb = QueryBuilder()
    qb.raw("AD1.D_E_L_E_T_ = ''")
    qb.date_range("AD1.AD1_DATA", start, end)
    where_clause, where_params = qb.build()

    is_weg = CommercialCustomerSegmentService.sql_is_weg_client_code("ovs.AD1_CODCLI")
    sql = f"""
        WITH ovs AS (
            SELECT DISTINCT
                AD1.AD1_FILIAL,
                AD1.AD1_NROPOR,
                AD1.AD1_REVISA,
                AD1.AD1_CODCLI
            FROM AD1010 AD1
            WHERE {where_clause}
        )
        SELECT
            COUNT(*) AS total_revisions,
            SUM(CASE WHEN {is_weg} THEN 1 ELSE 0 END) AS weg_revisions,
            SUM(CASE WHEN NOT ({is_weg}) THEN 1 ELSE 0 END) AS new_business_revisions
        FROM ovs
    """
    return sql, where_params


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida segmento WEG vs novos negócios")
    parser.add_argument("--start", default="2026-06-01")
    parser.add_argument("--end", default="2026-06-30")
    parser.add_argument("--branch", default=None)
    args = parser.parse_args()

    branch = (args.branch or "").strip() or None
    start = args.start
    end = args.end

    closing_repo = SalesConversionRateRepository()
    proposals_repo = CommercialProposalsRepository()
    rol_repo = NewBusinessRolPctRepository()

    closing_all = closing_repo.get_sales_conversion_rate(
        SalesConversionRateRequest(branch=branch, start_date=start, end_date=end)
    )
    closing_weg = closing_repo.get_sales_conversion_rate(
        SalesConversionRateRequest(
            branch=branch,
            start_date=start,
            end_date=end,
            customer_segment="weg",
        )
    )
    closing_nb = closing_repo.get_sales_conversion_rate(
        SalesConversionRateRequest(
            branch=branch,
            start_date=start,
            end_date=end,
            customer_segment="new_business",
        )
    )

    proposals_all = proposals_repo.list_proposals(
        ListCommercialProposalsRequest(
            branch=branch,
            start_date=start,
            end_date=end,
            page=1,
            page_size=1,
        )
    )
    proposals_weg = proposals_repo.list_proposals(
        ListCommercialProposalsRequest(
            branch=branch,
            start_date=start,
            end_date=end,
            customer_segment="weg",
            page=1,
            page_size=1,
        )
    )
    proposals_nb = proposals_repo.list_proposals(
        ListCommercialProposalsRequest(
            branch=branch,
            start_date=start,
            end_date=end,
            customer_segment="new_business",
            page=1,
            page_size=1,
        )
    )

    rol_all = rol_repo.get_new_business_rol_pct(
        NewBusinessRolPctRequest(branch=branch, start_date=start, end_date=end)
    )
    rol_weg = rol_repo.get_new_business_rol_pct(
        NewBusinessRolPctRequest(
            branch=branch,
            start_date=start,
            end_date=end,
            customer_segment="weg",
        )
    )
    rol_nb = rol_repo.get_new_business_rol_pct(
        NewBusinessRolPctRequest(
            branch=branch,
            start_date=start,
            end_date=end,
            customer_segment="new_business",
        )
    )

    sql, params = _sql_ad1_segment_counts(start, end)
    with closing_repo:
        sql_row = closing_repo.execute_one(sql, params) or {}

    report = {
        "period": {"start": start, "end": end, "branch": branch or "consolidated"},
        "closing_rate": {
            "all": {
                "qtd_proposals": closing_all.qtd_proposals,
                "qtd_won": closing_all.qtd_won,
                "pct": float(closing_all.sales_conversion_rate_pct or 0),
            },
            "weg": {
                "qtd_proposals": closing_weg.qtd_proposals,
                "qtd_won": closing_weg.qtd_won,
                "pct": float(closing_weg.sales_conversion_rate_pct or 0),
            },
            "new_business": {
                "qtd_proposals": closing_nb.qtd_proposals,
                "qtd_won": closing_nb.qtd_won,
                "pct": float(closing_nb.sales_conversion_rate_pct or 0),
            },
            "sum_weg_plus_nb_proposals": closing_weg.qtd_proposals
            + closing_nb.qtd_proposals,
            "partition_ok": (
                closing_weg.qtd_proposals + closing_nb.qtd_proposals
                == closing_all.qtd_proposals
            ),
        },
        "proposals_table": {
            "all": proposals_all.total,
            "weg": proposals_weg.total,
            "new_business": proposals_nb.total,
            "sum_weg_plus_nb": proposals_weg.total + proposals_nb.total,
            "partition_ok": proposals_weg.total + proposals_nb.total
            == proposals_all.total,
        },
        "new_business_rol_pct": {
            "all": {
                "total_rol": rol_all.total_rol,
                "weg_rol": rol_all.weg_rol,
                "new_business_rol": rol_all.new_business_rol,
                "pct": rol_all.new_business_rol_pct,
            },
            "weg_filter": {
                "total_rol": rol_weg.total_rol,
                "weg_rol": rol_weg.weg_rol,
                "new_business_rol": rol_weg.new_business_rol,
            },
            "new_business_filter": {
                "total_rol": rol_nb.total_rol,
                "weg_rol": rol_nb.weg_rol,
                "new_business_rol": rol_nb.new_business_rol,
            },
            "weg_plus_nb_equals_total": abs(
                (rol_all.weg_rol or 0) + (rol_all.new_business_rol or 0)
                - (rol_all.total_rol or 0)
            )
            < 0.01,
        },
        "sql_ad1_revisions": {
            "total": int(sql_row.get("total_revisions") or 0),
            "weg": int(sql_row.get("weg_revisions") or 0),
            "new_business": int(sql_row.get("new_business_revisions") or 0),
            "matches_closing_all": int(sql_row.get("total_revisions") or 0)
            == closing_all.qtd_proposals,
        },
        "won_status_code": WON_STATUS_CODE,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    checks = [
        report["closing_rate"]["partition_ok"],
        report["proposals_table"]["partition_ok"],
        report["new_business_rol_pct"]["weg_plus_nb_equals_total"],
        report["sql_ad1_revisions"]["matches_closing_all"],
    ]
    if not all(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
