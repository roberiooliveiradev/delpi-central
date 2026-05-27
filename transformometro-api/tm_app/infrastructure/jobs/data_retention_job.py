"""
Job de retenção de dados — LGPD (Transformômetro).

Responsabilidades:
- Excluir permanentemente registros com deletado=TRUE há mais de 90 dias.
- Anonimizar user_email em audit_logs com mais de 730 dias.

Executar via:
    python -m tm_app.infrastructure.jobs.data_retention_job
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from tm_app.infrastructure.providers.database.plugins_postgres_connection import (
    get_plugins_connection,
)

logger = logging.getLogger(__name__)

SOFT_DELETE_RETENTION_DAYS = 90
AUDIT_ANONYMIZE_DAYS = 730

_TABLES_WITH_SOFT_DELETE = [
    "transformometro.revisao_recursos_compartilhados",
    "transformometro.investimentos",
    "transformometro.medicoes",
    "transformometro.revisoes",
    "transformometro.recurso_custos",
    "transformometro.recursos_compartilhados",
    "transformometro.processos",
]


@dataclass
class RetentionResult:
    purged: dict[str, int]
    audit_anonymized: int


def run_data_retention(*, dry_run: bool = False) -> RetentionResult:
    """Executa a política de retenção de dados pessoais."""
    conn = get_plugins_connection()
    purged: dict[str, int] = {}
    audit_anonymized = 0

    try:
        with conn.cursor() as cur:
            for table in _TABLES_WITH_SOFT_DELETE:
                cur.execute(
                    f"""
                    DELETE FROM {table}
                    WHERE deletado = TRUE
                      AND updated_at < NOW() - INTERVAL '{SOFT_DELETE_RETENTION_DAYS} days'
                    """,
                )
                purged[table] = cur.rowcount or 0
                logger.info(
                    "Purge %s: %d registros removidos%s",
                    table,
                    purged[table],
                    " (dry-run)" if dry_run else "",
                )

            cur.execute(
                f"""
                UPDATE transformometro.audit_logs
                SET user_email = 'anonimizado@lgpd',
                    user_id = NULL
                WHERE user_email IS NOT NULL
                  AND user_email != 'anonimizado@lgpd'
                  AND created_at < NOW() - INTERVAL '{AUDIT_ANONYMIZE_DAYS} days'
                """,
            )
            audit_anonymized = cur.rowcount or 0
            logger.info(
                "Audit logs anonimizados: %d registros%s",
                audit_anonymized,
                " (dry-run)" if dry_run else "",
            )

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    except Exception:
        conn.rollback()
        logger.exception("Erro durante job de retenção de dados (transformometro).")
        raise

    return RetentionResult(purged=purged, audit_anonymized=audit_anonymized)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logger.info("Modo dry-run ativado — nenhuma alteração será persistida.")

    result = run_data_retention(dry_run=dry_run)

    print("\n=== Resultado da retenção de dados (Transformômetro) ===")
    print(f"  Registros soft-deleted purgados (>{SOFT_DELETE_RETENTION_DAYS} dias):")
    for table, count in result.purged.items():
        print(f"    {table}: {count}")
    print(f"  Audit logs anonimizados (>{AUDIT_ANONYMIZE_DAYS} dias): {result.audit_anonymized}")

    if dry_run:
        print("\n  [DRY-RUN] Nenhuma alteração foi persistida.")


if __name__ == "__main__":
    main()
