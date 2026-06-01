#!/usr/bin/env python3
"""Cron/local — gera relatório semanal de qualidade e issues automáticas."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-issues",
        action="store_true",
        help="Não criar issues automáticas a partir dos alertas.",
    )
    args = parser.parse_args()

    from app.application.use_cases.generate_weekly_quality_report_use_case import (
        GenerateWeeklyQualityReportUseCase,
    )
    from app.composition.root_composer import create_application
    from app.extensions.db import db

    app = create_application()

    with app.app_context():
        result = GenerateWeeklyQualityReportUseCase().execute(
            create_issues=not args.no_issues,
        )
        db.session.commit()

    report = result.get("report") or {}
    issues = result.get("issuesCreated") or []

    print(f"Relatório #{report.get('id')} gerado.")
    print(f"Issues criadas: {len(issues)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
