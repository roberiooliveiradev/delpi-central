#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import time

from si_app.application.dto.strategic_indicators.get_executive_summary_real_request import (
    GetExecutiveSummaryRealRequest,
)
from si_app.application.dto.strategic_indicators.get_trends_real_request import (
    GetStrategicIndicatorsTrendsRealRequest,
)
from si_app.application.use_cases.strategic_indicators.get_department_details_real_use_case import (
    GetStrategicIndicatorsDepartmentDetailsRealRequest,
)
from si_app.composition.strategic_indicators_composer import (
    build_get_strategic_indicators_department_details_use_case,
    build_get_strategic_indicators_executive_summary_use_case,
    build_get_strategic_indicators_trends_use_case,
)


def _bench(label: str, fn) -> float:
    started = time.perf_counter()
    fn()
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(f"{label:28} {elapsed_ms:8.0f} ms")
    return elapsed_ms


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark rotas SI (in-process).")
    parser.add_argument("--competence", default="2026-05")
    parser.add_argument("--department-id", default="commercial")
    parser.add_argument("--months", type=int, default=6)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    print(f"competence={args.competence} department_id={args.department_id} months={args.months}")
    print("-" * 40)

    _bench(
        "executive-summary",
        lambda: build_get_strategic_indicators_executive_summary_use_case().execute(
            GetExecutiveSummaryRealRequest(competence=args.competence)
        ),
    )
    _bench(
        f"departments/{args.department_id}",
        lambda: build_get_strategic_indicators_department_details_use_case().execute(
            GetStrategicIndicatorsDepartmentDetailsRealRequest(
                department_id=args.department_id,
                competence=args.competence,
            )
        ),
    )
    _bench(
        f"trends-{args.months}m",
        lambda: build_get_strategic_indicators_trends_use_case().execute(
            GetStrategicIndicatorsTrendsRealRequest(
                competence=args.competence,
                months=args.months,
            )
        ),
    )


if __name__ == "__main__":
    main()
