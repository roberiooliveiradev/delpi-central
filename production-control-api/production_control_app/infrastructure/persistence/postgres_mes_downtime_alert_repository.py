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

    def list_observer_states(self, *, branch: str) -> list[dict[str, Any]]:
        """Estado de telemetria Pulse por CT — a regra de parada
        prolongada não alerta quando a ausência de sinal é
        indistinguível da parada real (RQ-6.8)."""
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT work_center, device_online, degraded_reason,
                       last_seen_at
                  FROM {PC_SCHEMA_NAME}.work_center_pulse_observers
                 WHERE branch = %s
                """,
                [branch],
            )
            return [dict(row) for row in cur.fetchall()]

    def claim_pending(
        self,
        *,
        alert_key: str,
        branch: str,
        rule: str,
        subject_key: str,
        signature: str,
        now: datetime,
        lease_expiry: datetime,
    ) -> bool:
        """Reserva atômica do alerta para dispatch.

        Retorna True somente quando a assinatura difere da última
        ENTREGUE e nenhum claim vigente segura a chave (lease não
        expirado) — dois avaliadores concorrentes não despacham o
        mesmo alerta, e um avaliador que falha/cai libera a chave
        para retry após o lease.
        """
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_DISPATCHES} (
                    alert_key, branch, rule, subject_key, signature,
                    pending_signature, claimed_at,
                    first_seen_at, last_dispatched_at, dispatch_count
                ) VALUES (%s, %s, %s, %s, NULL, %s, %s, %s, NULL, 0)
                ON CONFLICT (alert_key) DO UPDATE SET
                    pending_signature = EXCLUDED.pending_signature,
                    claimed_at = EXCLUDED.claimed_at,
                    updated_at = now()
                WHERE
                    {PC_SCHEMA_NAME}.mes_downtime_alert_dispatches.signature
                        IS DISTINCT FROM EXCLUDED.pending_signature
                    AND (
                        {PC_SCHEMA_NAME}.mes_downtime_alert_dispatches.claimed_at
                            IS NULL
                        OR {PC_SCHEMA_NAME}.mes_downtime_alert_dispatches.claimed_at
                            < %s
                    )
                RETURNING alert_key
                """,
                [
                    alert_key, branch, rule, subject_key, signature,
                    now, now, lease_expiry,
                ],
            )
            claimed = cur.fetchone() is not None
            conn.commit()
            return claimed

    def confirm_dispatch(
        self, *, alert_key: str, signature: str, now: datetime
    ) -> None:
        """Marca a assinatura como entregue — somente após dispatch
        bem-sucedido e apenas se ainda somos o dono do claim
        (pending_signature casa)."""
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {_DISPATCHES} SET
                    signature = pending_signature,
                    pending_signature = NULL,
                    claimed_at = NULL,
                    last_dispatched_at = %s,
                    dispatch_count = dispatch_count + 1,
                    updated_at = now()
                WHERE alert_key = %s
                  AND pending_signature = %s
                """,
                [now, alert_key, signature],
            )
            conn.commit()

    def release_claim(self, *, alert_key: str, signature: str) -> None:
        """Libera a reserva após falha de dispatch — o próximo tick
        retenta (a assinatura entregue não mudou)."""
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {_DISPATCHES} SET
                    pending_signature = NULL,
                    claimed_at = NULL,
                    updated_at = now()
                WHERE alert_key = %s
                  AND pending_signature = %s
                """,
                [alert_key, signature],
            )
            conn.commit()
