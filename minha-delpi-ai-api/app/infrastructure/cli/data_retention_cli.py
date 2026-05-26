import logging
from datetime import datetime, timedelta, timezone

import click
from flask.cli import with_appcontext
from sqlalchemy import text

from app.extensions.db import db

logger = logging.getLogger("minha-delpi-ai-api.data_retention")

AUDIT_LOG_RETENTION_DAYS = 730
CHAT_MESSAGE_RETENTION_DAYS = 365


@click.group("data-retention")
def data_retention_cli():
    """Comandos de retenção de dados (LGPD) para minha-delpi-ai-api."""
    pass


@data_retention_cli.command("run")
@click.option("--dry-run", is_flag=True, help="Apenas exibir o que seria feito, sem alterar dados.")
@with_appcontext
def run_retention(dry_run: bool):
    """Executa limpeza periódica de dados que excederam prazo de retenção."""
    results = {}
    now = datetime.now(timezone.utc)

    results["audit_logs_anonymized"] = _anonymize_old_audit_logs(now, dry_run)
    results["chat_messages_deleted"] = _delete_old_chat_messages(now, dry_run)
    results["orphan_sessions_deleted"] = _delete_orphan_sessions(dry_run)

    if not dry_run:
        db.session.commit()

    prefix = "[DRY-RUN] " if dry_run else ""
    for key, value in results.items():
        click.echo(f"  {prefix}{key}: {value}")

    click.echo(f"{prefix}Retenção concluída.")


def _anonymize_old_audit_logs(now: datetime, dry_run: bool) -> int:
    cutoff = now - timedelta(days=AUDIT_LOG_RETENTION_DAYS)

    count_query = text(
        "SELECT count(*) FROM ai_audit_logs "
        "WHERE created_at < :cutoff AND user_id IS NOT NULL"
    )
    count = db.session.execute(count_query, {"cutoff": cutoff}).scalar() or 0

    if count == 0 or dry_run:
        return count

    update_query = text(
        "UPDATE ai_audit_logs "
        "SET user_id = NULL, "
        "    metadata = jsonb_set("
        "        COALESCE(metadata, '{}'::jsonb), "
        "        '{question_preview}', "
        "        '\"[REDACTED]\"'::jsonb"
        "    ) "
        "WHERE created_at < :cutoff AND user_id IS NOT NULL"
    )
    result = db.session.execute(update_query, {"cutoff": cutoff})
    logger.info("audit_logs_anonymized", extra={"count": result.rowcount})
    return result.rowcount


def _delete_old_chat_messages(now: datetime, dry_run: bool) -> int:
    cutoff = now - timedelta(days=CHAT_MESSAGE_RETENTION_DAYS)

    count_query = text(
        "SELECT count(*) FROM ai_chat_messages WHERE created_at < :cutoff"
    )
    count = db.session.execute(count_query, {"cutoff": cutoff}).scalar() or 0

    if count == 0 or dry_run:
        return count

    delete_query = text(
        "DELETE FROM ai_chat_messages WHERE created_at < :cutoff"
    )
    result = db.session.execute(delete_query, {"cutoff": cutoff})
    logger.info("chat_messages_deleted", extra={"count": result.rowcount})
    return result.rowcount


def _delete_orphan_sessions(dry_run: bool) -> int:
    count_query = text(
        "SELECT count(*) FROM ai_chat_sessions s "
        "WHERE NOT EXISTS ("
        "    SELECT 1 FROM ai_chat_messages m WHERE m.session_id = s.id"
        ")"
    )
    count = db.session.execute(count_query).scalar() or 0

    if count == 0 or dry_run:
        return count

    delete_query = text(
        "DELETE FROM ai_chat_sessions s "
        "WHERE NOT EXISTS ("
        "    SELECT 1 FROM ai_chat_messages m WHERE m.session_id = s.id"
        ")"
    )
    result = db.session.execute(delete_query)
    logger.info("orphan_sessions_deleted", extra={"count": result.rowcount})
    return result.rowcount
