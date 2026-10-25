"""CLARA — store de lotes governados (PREPARE_BATCH → consent → ACT).

Estado por lote e por operação é durável em PostgreSQL — claim
atômico antes do efeito, retomada segura, reconciliação de outcome
desconhecido. Não é transação global: cada operação executa pelas
regras canônicas do próprio recurso.
"""

from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    PersistenceUnavailable,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    handle_hash,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


class BatchNotFound(ChecklistDomainError):
    code = "batch_not_found"
    status = 404


class BatchActorMismatch(ChecklistDomainError):
    code = "batch_actor_mismatch"
    status = 403


class BatchNotConfirmed(ChecklistDomainError):
    code = "batch_not_confirmed"
    status = 409


class BatchExpired(ChecklistDomainError):
    code = "batch_expired"
    status = 409


class BatchTerminal(ChecklistDomainError):
    code = "batch_terminal"
    status = 409


class ClaraBatchRepository:
    def _conn(self) -> psycopg.Connection:
        if not plugins_db_configured():
            raise PersistenceUnavailable(
                "Persistência do workflow não configurada."
            )
        try:
            return plugins_db_connect()
        except ChecklistDomainError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceUnavailable(
                "Persistência indisponível."
            ) from exc

    # -- PREPARE_BATCH --------------------------------------------------

    def create_batch(
        self,
        *,
        handle: str,
        actor_sub: str,
        plan: dict,
        plan_hash: str,
        operations: list[dict],
        ttl_seconds: int = 900,
        correlation_id: str | None = None,
    ) -> dict:
        """Persiste o lote PREPARED + operações num único commit.

        ``operations[i]`` = {seq, idempotency_key, capability,
        resource_type, resource_key, params, depends_on,
        proposal_handle}.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {_q('clara_batch')}
                            (handle_hash, actor_sub, plan, plan_hash,
                             correlation_id, expires_at)
                        VALUES (%s,%s,%s::jsonb,%s,%s,
                                now() + make_interval(secs => %s))
                        RETURNING batch_id, expires_at, created_at
                        """,
                        (
                            handle_hash(handle),
                            actor_sub,
                            json.dumps(plan, default=str),
                            plan_hash,
                            correlation_id,
                            ttl_seconds,
                        ),
                    )
                    batch = cur.fetchone()
                    batch_id = batch["batch_id"]
                    for op in operations:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('clara_batch_operation')}
                                (batch_id, seq, idempotency_key,
                                 capability, resource_type,
                                 resource_key, params, depends_on,
                                 proposal_id)
                            VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,
                                    %s::jsonb,
                                    (SELECT proposal_id
                                       FROM {_q('clara_proposal')}
                                      WHERE handle_hash = %s))
                            RETURNING operation_id
                            """,
                            (
                                batch_id,
                                op["seq"],
                                op["idempotency_key"],
                                op["capability"],
                                op["resource_type"],
                                op["resource_key"],
                                json.dumps(op["params"], default=str),
                                json.dumps(op["depends_on"]),
                                handle_hash(op["proposal_handle"]),
                            ),
                        )
                        op_id = cur.fetchone()["operation_id"]
                        cur.execute(
                            f"""
                            UPDATE {_q('clara_proposal')}
                               SET batch_operation_id = %s
                             WHERE handle_hash = %s
                            """,
                            (
                                str(op_id),
                                handle_hash(op["proposal_handle"]),
                            ),
                        )
                    batch["operations"] = len(operations)
                    return batch

    # -- consentimento ---------------------------------------------------

    def record_consent(
        self,
        *,
        handle: str,
        actor_sub: str,
        plan_hash: str,
        mode: str,
        consent_record: dict,
    ) -> dict:
        """Uma confirmação consolidada por lote — nunca por operação.

        O plano selado não pode divergir do apresentado: ``plan_hash``
        precisa ser idêntico, senão o consentimento é inválido.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_batch')}
                         WHERE handle_hash = %s
                         FOR UPDATE
                        """,
                        (handle_hash(handle),),
                    )
                    batch = cur.fetchone()
                    if batch is None:
                        raise BatchNotFound("Lote não encontrado.")
                    if batch["actor_sub"] != actor_sub:
                        raise BatchActorMismatch(
                            "Lote pertence a outro ator."
                        )
                    if batch["status"] != "PREPARED":
                        raise BatchTerminal(
                            f"Lote em estado {batch['status']} — "
                            "não aceita consentimento."
                        )
                    if batch["plan_hash"] != plan_hash:
                        raise ChecklistDomainError(
                            "Plano divergente do selado — reprepare o "
                            "lote."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_batch')}
                           SET consent_mode = %s,
                               consent_record = %s::jsonb,
                               status = 'CONFIRMED',
                               confirmed_at = now()
                         WHERE handle_hash = %s
                        RETURNING batch_id, status, confirmed_at
                        """,
                        (
                            mode,
                            json.dumps(consent_record, default=str),
                            handle_hash(handle),
                        ),
                    )
                    return cur.fetchone()

    def record_consent_by_id(
        self,
        *,
        batch_id: str,
        actor_sub: str,
        plan_hash: str,
        mode: str,
        consent_record: dict,
    ) -> dict:
        """Versão por PK do record_consent (superfície BFF step-up)."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_batch')}
                         WHERE batch_id = %s
                         FOR UPDATE
                        """,
                        (batch_id,),
                    )
                    batch = cur.fetchone()
                    if batch is None:
                        raise BatchNotFound("Lote não encontrado.")
                    if batch["actor_sub"] != actor_sub:
                        raise BatchActorMismatch(
                            "Lote pertence a outro ator."
                        )
                    if batch["status"] != "PREPARED":
                        raise BatchTerminal(
                            f"Lote em estado {batch['status']} — "
                            "não aceita consentimento."
                        )
                    if batch["plan_hash"] != plan_hash:
                        raise ChecklistDomainError(
                            "Plano divergente do selado — reprepare o "
                            "lote."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_batch')}
                           SET consent_mode = %s,
                               consent_record = %s::jsonb,
                               status = 'CONFIRMED',
                               confirmed_at = now()
                         WHERE batch_id = %s
                        RETURNING batch_id, status, confirmed_at
                        """,
                        (
                            mode,
                            json.dumps(consent_record, default=str),
                            batch_id,
                        ),
                    )
                    return cur.fetchone()

    # -- execução ----------------------------------------------------------

    def claim_batch_for_execution(
        self, *, handle: str, actor_sub: str, resume: bool = False
    ) -> dict:
        """Transição atômica CONFIRMED → EXECUTING (vencedor único)."""
        from datetime import datetime as _dt, timezone as _tz

        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_batch')}
                         WHERE handle_hash = %s
                         FOR UPDATE
                        """,
                        (handle_hash(handle),),
                    )
                    batch = cur.fetchone()
                    if batch is None:
                        raise BatchNotFound("Lote não encontrado.")
                    if batch["actor_sub"] != actor_sub:
                        raise BatchActorMismatch(
                            "Lote pertence a outro ator."
                        )
                    expires_at = batch["expires_at"]
                    if (
                        getattr(expires_at, "tzinfo", None) is None
                        and hasattr(expires_at, "replace")
                    ):
                        expires_at = expires_at.replace(tzinfo=_tz.utc)
                    if expires_at < _dt.now(_tz.utc):
                        cur.execute(
                            f"""
                            UPDATE {_q('clara_batch')}
                               SET status = 'EXPIRED'
                             WHERE batch_id = %s
                            """,
                            (batch["batch_id"],),
                        )
                        raise BatchExpired("Lote expirado.")
                    if batch["status"] == "PREPARED":
                        raise BatchNotConfirmed(
                            "Lote sem consentimento consolidado — "
                            "confirme o plano antes de executar."
                        )
                    if batch["status"] in (
                        "COMPLETED", "COMPLETED_WITH_FAILURES",
                        "BLOCKED",
                    ):
                        raise BatchTerminal(
                            f"Lote já encerrado ({batch['status']})."
                        )
                    if batch["status"] == "EXECUTING" and not resume:
                        raise BatchTerminal(
                            "Lote já em execução — aguarde o "
                            "término ou retome com resume=True."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_batch')}
                           SET status = 'EXECUTING'
                         WHERE batch_id = %s
                           AND status IN ('CONFIRMED', 'EXECUTING')
                        RETURNING batch_id, plan, plan_hash
                        """,
                        (batch["batch_id"],),
                    )
                    claimed = cur.fetchone()
                    # Consome o desafio de consentimento do lote no
                    # mesmo claim — autorização single-use (V014).
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_consent_challenge')}
                           SET status = 'CONSUMED', consumed_at = now()
                         WHERE batch_id = %s
                           AND status = 'APPROVED'
                        """,
                        (batch["batch_id"],),
                    )
                    return claimed

    def list_operations(self, *, batch_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT o.*, p.handle_hash AS proposal_handle_hash
                      FROM {_q('clara_batch_operation')} o
                      LEFT JOIN {_q('clara_proposal')} p
                        ON p.proposal_id = o.proposal_id
                     WHERE o.batch_id = %s
                     ORDER BY o.seq
                    """,
                    (batch_id,),
                )
                return cur.fetchall()

    def claim_operation(self, *, operation_id: str) -> dict:
        """Claim atômico por operação — exatamente um executor."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_batch_operation')}
                           SET state = 'CLAIMED', updated_at = now()
                         WHERE operation_id = %s
                           AND state = 'PREPARED'
                        RETURNING *
                        """,
                        (operation_id,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ChecklistDomainError(
                            "Operação já reivindicada ou fora de "
                            "PREPARED."
                        )
                    return row

    def set_operation_state(
        self,
        *,
        operation_id: str,
        state: str,
        result: dict | None = None,
        error_code: str | None = None,
    ) -> None:
        with self._conn() as conn:
            with conn.transaction():
                conn.execute(
                    f"""
                    UPDATE {_q('clara_batch_operation')}
                       SET state = %s,
                           result = %s::jsonb,
                           error_code = %s,
                           updated_at = now()
                     WHERE operation_id = %s
                    """,
                    (
                        state,
                        json.dumps(result or {}, default=str),
                        error_code,
                        operation_id,
                    ),
                )

    def finish_batch(self, *, batch_id: str, result: dict) -> dict:
        """Fecha o lote com o resumo honesto de outcomes."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT state FROM {_q('clara_batch_operation')}
                         WHERE batch_id = %s
                        """,
                        (batch_id,),
                    )
                    states = [r["state"] for r in cur.fetchall()]
                    if all(s == "VERIFIED" for s in states):
                        status = "COMPLETED"
                    elif all(
                        s in ("FAILED", "BLOCKED", "UNKNOWN")
                        for s in states
                    ):
                        status = "BLOCKED"
                    else:
                        status = "COMPLETED_WITH_FAILURES"
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_batch')}
                           SET status = %s, result = %s::jsonb
                         WHERE batch_id = %s
                        RETURNING batch_id, status
                        """,
                        (status, json.dumps(result, default=str),
                         batch_id),
                    )
                    return cur.fetchone()

    # -- leitura ------------------------------------------------------------

    def load_by_handle(self, *, handle: str) -> dict:
        """Leitura por handle sem lock (status/consent check)."""
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q('clara_batch')}
                     WHERE handle_hash = %s
                    """,
                    (handle_hash(handle),),
                )
                batch = cur.fetchone()
        if batch is None:
            raise BatchNotFound("Lote não encontrado.")
        return batch

    def get_batch(self, *, batch_id: str) -> dict:
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q('clara_batch')}
                     WHERE batch_id = %s
                    """,
                    (batch_id,),
                )
                batch = cur.fetchone()
        if batch is None:
            raise BatchNotFound("Lote não encontrado.")
        batch["operations"] = self.list_operations(
            batch_id=str(batch_id)
        )
        return batch
