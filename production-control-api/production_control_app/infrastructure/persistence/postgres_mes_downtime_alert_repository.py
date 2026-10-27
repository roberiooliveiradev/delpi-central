"""Persistência do avaliador de alertas MES (Etapa 6).

Leituras de avaliação sobre os fatos canônicos (downtime_events /
mes_downtime_treatments) + claim atômico de dedup em
mes_downtime_alert_dispatches — INSERT/UPDATE condicional por assinatura
garante que dois avaliadores concorrentes não disparam o mesmo alerta.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
    PC_SCHEMA_NAME,
    get_connection,
)

_DOWNTIMES = f"{PC_SCHEMA_NAME}.downtime_events"
_TREATMENTS = f"{PC_SCHEMA_NAME}.mes_downtime_treatments"
_DISPATCHES = f"{PC_SCHEMA_NAME}.mes_downtime_alert_dispatches"


class PostgresMesDowntimeAlertRepository:
    """Consultas do avaliador + dedup atômico — owner dos fatos MES."""

    def list_open_downtimes_older_than(
        self, *, branch: str, reference_before: datetime
    ) -> list[dict[str, Any]]:
        """Paradas abertas cujo início antecede o corte (parada prolongada)."""
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT d.id::text AS id, d.work_center, d.started_at,
                       d.source, d.reason_code, d.confirmed,
                       reason.label AS reason_label
                  FROM {_DOWNTIMES} d
             LEFT JOIN {PC_SCHEMA_NAME}.downtime_reason_catalog reason
                    ON reason.code = d.reason_code
                 WHERE d.branch = %s
                   AND d.ended_at IS NULL
                   AND d.started_at <= %s
              ORDER BY d.started_at ASC
                """,
                [branch, reference_before],
            )
            return [dict(row) for row in cur.fetchall()]

    def count_unclassified_downtimes(self, *, branch: str) -> int:
        """Ocorrências sem classificação confirmada (backlog gerencial)."""
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                  FROM {_DOWNTIMES} d
                 WHERE d.branch = %s
                   AND d.confirmed IS NOT TRUE
                """,
                [branch],
            )
            return int(cur.fetchone()["total"])

    def list_overdue_open_treatments(
        self, *, branch: str, reference_before: datetime
    ) -> list[dict[str, Any]]:
        """Tratamentos abertos (pending|referred) criados antes do corte —
        ações corretivas vencidas pelo parâmetro governado."""
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT t.downtime_id::text AS downtime_id, t.status,
                       t.created_at, t.updated_at,
                       d.work_center, d.reason_code
                  FROM {_TREATMENTS} t
                  JOIN {_DOWNTIMES} d ON d.id = t.downtime_id
                 WHERE t.branch = %s
                   AND t.status IN ('pending', 'referred')
                   AND t.created_at <= %s
              ORDER BY t.created_at ASC
                """,
                [branch, reference_before],
            )
            return [dict(row) for row in cur.fetchall()]

    def claim_if_signature_changed(
        self,
        *,
        alert_key: str,
        branch: str,
        rule: str,
        subject_key: str,
        signature: str,
        now: datetime,
    ) -> bool:
        """Dedup atômico: retorna True (pode despachar) somente quando a
        assinatura difere da última notificada para a mesma chave —
        primeira ocorrência insere; recorrência atualiza apenas se o
        estado relevante mudou (RQ-6.7)."""
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_DISPATCHES} (
                    alert_key, branch, rule, subject_key, signature,
                    first_seen_at, last_dispatched_at, dispatch_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                ON CONFLICT (alert_key) DO UPDATE SET
                    signature = EXCLUDED.signature,
                    last_dispatched_at = EXCLUDED.last_dispatched_at,
                    dispatch_count =
                        {PC_SCHEMA_NAME}.mes_downtime_alert_dispatches.dispatch_count + 1,
                    updated_at = now()
                WHERE
                    {PC_SCHEMA_NAME}.mes_downtime_alert_dispatches.signature
                    <> EXCLUDED.signature
                RETURNING alert_key
                """,
                [alert_key, branch, rule, subject_key, signature, now, now],
            )
            claimed = cur.fetchone() is not None
            conn.commit()
            return claimed
