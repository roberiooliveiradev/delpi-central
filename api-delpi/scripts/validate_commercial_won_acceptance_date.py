#!/usr/bin/env python3
"""Valida listagem de propostas ganhas por data de aceite (AD1_DTASSI).

Uso:
  docker exec delpi-api-delpi python scripts/validate_commercial_won_acceptance_date.py \\
    --start 2026-05-01 --end 2026-05-31
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
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_proposals_repository import (
    CommercialProposalsRepository,
)

# OVs reportadas pelo comercial como ausentes no filtro de maio/2026 (ganhas).
REQUIRED_WON_MAY_2026 = {
    ("02", "000090"): "2026-05-06",
    ("02", "000084"): "2026-05-14",
    ("02", "000054"): "2026-05-20",
    ("01", "003551"): "2026-05-19",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida ganhas por AD1_DTASSI")
    parser.add_argument("--start", default="2026-05-01")
    parser.add_argument("--end", default="2026-05-31")
    args = parser.parse_args()

    repo = CommercialProposalsRepository()
    page = repo.list_proposals(
        ListCommercialProposalsRequest(
            start_date=args.start,
            end_date=args.end,
            status="won",
            page=1,
            page_size=200,
        )
    )

    by_key = {(item.branch, item.proposal_number): item for item in page.items}
    missing = []
    wrong_end_date = []

    for (branch, number), expected_end in REQUIRED_WON_MAY_2026.items():
        item = by_key.get((branch, number))
        if item is None:
            missing.append(f"{branch}/{number}")
            continue
        if item.end_date != expected_end:
            wrong_end_date.append(
                {
                    "proposal": f"{branch}/{number}",
                    "expected_end_date": expected_end,
                    "actual_end_date": item.end_date,
                }
            )

    report = {
        "period": {"start": args.start, "end": args.end},
        "total": page.total,
        "missing_required": missing,
        "wrong_end_date": wrong_end_date,
        "sample": [
            {
                "branch": item.branch,
                "proposal_number": item.proposal_number,
                "proposal_date": item.proposal_date,
                "end_date": item.end_date,
            }
            for item in page.items[:15]
        ],
        "ok": not missing and not wrong_end_date and page.total >= len(REQUIRED_WON_MAY_2026),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
