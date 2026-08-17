#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import time

from si_app.application.services.strategic_indicators.period_scores_refresh_service import (
    refresh_period_scores_materialized,
)
from si_app.config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materializa period_scores no Postgres (mesmo job do scheduler).",
    )
    parser.add_argument(
        "--competence",
        default=None,
        help="Competência de referência YYYY-MM (default: mês atual do servidor)",
    )
    parser.add_argument(
        "--trends-months",
        type=int,
        default=None,
        help=(
            "Meses de tendência a materializar (1–12). "
            "Default: YTD (início do ano até a competência), "
            "salvo override SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS no env."
        ),
    )
    parser.add_argument(
        "--branches",
        default=None,
        help=(
            "Escopos de filial CSV (ex.: consolidated, 01,02). "
            "Sobrescreve SI_PERIOD_SCORES_REFRESH_BRANCHES. "
            "Fase B noturna: --branches 01,02"
        ),
    )
    parser.add_argument(
        "--per-department",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Materializa também por departamento. "
            f"Default env: {settings.SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT}"
        ),
    )
    parser.add_argument(
        "--no-invalidate",
        action="store_true",
        help=(
            "Caminho feliz: não apaga period_scores antes (incremental). "
            "Wipe total: POST /cache/invalidate (admin), não este script sem a flag."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Nível de log (DEBUG, INFO, ...)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    competence_label = args.competence or "mês atual"
    trends_months_label = (
        args.trends_months
        if args.trends_months is not None
        else (
            settings.SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS
            if settings.SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS is not None
            else "ytd"
        )
    )
    branches_label = (
        args.branches
        if args.branches is not None
        else (settings.SI_PERIOD_SCORES_REFRESH_BRANCHES or "default")
    )
    per_department = (
        settings.SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT
        if args.per_department is None
        else args.per_department
    )

    print(
        (
            f"si_refresh_start competence={competence_label} "
            f"trends_months={trends_months_label} branches={branches_label} "
            f"per_department={per_department} "
            f"invalidate={not args.no_invalidate} "
            "(consulta TOTVS/Sheets/RH; pode levar vários minutos em produção)..."
        ),
        flush=True,
    )
    started = time.perf_counter()
    upserted = refresh_period_scores_materialized(
        reference_competence=args.competence,
        trends_months=args.trends_months,
        per_department=args.per_department,
        branches=args.branches,
        invalidate_cache=not args.no_invalidate,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(
        f"refresh_ok competence={competence_label} periods={upserted} {elapsed_ms:.0f} ms",
        flush=True,
    )


if __name__ == "__main__":
    main()
