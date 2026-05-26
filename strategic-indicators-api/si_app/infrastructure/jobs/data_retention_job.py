"""
Job de retenção de dados — LGPD (Strategic Indicators).

Responsabilidades:
- Anonimizar changed_by_email em settings_audit com mais de 730 dias.

Executar via:
    python -m si_app.infrastructure.jobs.data_retention_job
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from si_app.infrastructure.providers.database.plugins_postgres_connection import (
    get_plugins_connection,
)

logger = logging.getLogger(__name__)

AUDIT_ANONYMIZE_DAYS = 730


@dataclass
class RetentionResult:
    audit_anonymized: int


def run_data_retention(*, dry_run: bool = False) -> RetentionResult:
    """Executa a política de retenção de dados pessoais em settings_audit."""
    conn = get_plugins_connection()
    audit_anonymized = 0

    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE strategic_indicators.settings_audit
                SET changed_by_email = 'anonimizado@lgpd',
                    changed_by_user_id = NULL
                WHERE changed_by_email IS NOT NULL
                  AND changed_by_email != 'anonimizado@lgpd'
                  AND created_at < NOW() - INTERVAL '{AUDIT_ANONYMIZE_DAYS} days'
                """,
            )
            audit_anonymized = cur.rowcount or 0
            logger.info(
                "settings_audit anonimizados: %d registros%s",
                audit_anonymized,
                " (dry-run)" if dry_run else "",
            )

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    except Exception:
        conn.rollback()
        logger.exception("Erro durante job de retenção de dados (strategic-indicators).")
        raise

    return RetentionResult(audit_anonymized=audit_anonymized)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logger.info("Modo dry-run ativado — nenhuma alteração será persistida.")

    result = run_data_retention(dry_run=dry_run)

    print("\n=== Resultado da retenção de dados (Strategic Indicators) ===")
    print(f"  settings_audit anonimizados (>{AUDIT_ANONYMIZE_DAYS} dias): {result.audit_anonymized}")

    if dry_run:
        print("\n  [DRY-RUN] Nenhuma alteração foi persistida.")


if __name__ == "__main__":
    main()
