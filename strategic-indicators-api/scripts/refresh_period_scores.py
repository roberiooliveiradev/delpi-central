#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import time

from si_app.application.services.strategic_indicators.period_scores_refresh_service import (
    refresh_period_scores_materialized,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materializa period_scores no Postgres (mesmo job do scheduler).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Nível de log (DEBUG, INFO, ...)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print(
        "si_refresh_start (consulta TOTVS/Sheets/RH; pode levar 1–3 min em produção)...",
        flush=True,
    )
    started = time.perf_counter()
    upserted = refresh_period_scores_materialized()
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(f"refresh_ok periods={upserted} {elapsed_ms:.0f} ms", flush=True)


if __name__ == "__main__":
    main()
