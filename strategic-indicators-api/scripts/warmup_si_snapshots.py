#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import time

from si_app.application.services.strategic_indicators.snapshot_warmup_service import (
    warmup_strategic_indicators_snapshots,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pré-aquece cache de executive-summary e trends (in-process).",
    )
    parser.add_argument("--competence", default=None, help="YYYY-MM (default: mês atual)")
    parser.add_argument("--months", type=int, default=6, help="Meses em trends")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    started = time.perf_counter()
    warmup_strategic_indicators_snapshots(
        competence=args.competence,
        trends_months=args.months,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(f"warmup_ok {elapsed_ms:.0f} ms")


if __name__ == "__main__":
    main()
