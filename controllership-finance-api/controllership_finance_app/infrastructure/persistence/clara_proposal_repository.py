"""CLARA — store de propostas governadas (PREPARE → ACT).

Padrão TÉO owner-local (CLARA-D04=A): handle opaco vinculado ao ator,
payload selado server-side, expiração, consumo atômico single-use.
A proposta nunca é autorização — o ACT revalida Core/escopo/regras no
momento da execução.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    PersistenceUnavailable,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


def handle_hash(handle: str) -> str:
    return hashlib.sha256(handle.encode("utf-8")).hexdigest()


class ProposalNotFound(ChecklistDomainError):
    code = "proposal_not_found"
    status = 404


class ProposalActorMismatch(ChecklistDomainError):
    code = "proposal_actor_mismatch"
    status = 403


class ProposalExpired(ChecklistDomainError):
    code = "proposal_expired"
    status = 409


class ProposalConsumed(ChecklistDomainError):
    code = "proposal_stale"
    status = 409


class ClaraProposalRepository:
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

    def create(
        self,
        *,
        handle: str,
        actor_sub: str,
        capability: str,
        resource_type: str,
        resource_key: str,
        payload: dict,
        expected_state: dict,
        ttl_seconds: int = 900,
    ) -> dict:
        """Sela a proposta server-side e devolve a projeção pública."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {_q('clara_proposal')}
                            (handle_hash, actor_sub, capability,
                             resource_type, resource_key, payload,
                             expected_state, expires_at)
                        VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,
                                now() + make_interval(secs => %s))
                        RETURNING proposal_id, capability, resource_type,
                                  resource_key, payload, expected_state,
                                  expires_at, created_at
                        """,
                        (
                            handle_hash(handle),
                            actor_sub,
                            capability,
                            resource_type,
                            resource_key,
                            json.dumps(payload, default=str),
                            json.dumps(expected_state, default=str),
                            ttl_seconds,
                        ),
                    )
                    return cur.fetchone()

    def load_for_actor(self, *, handle: str, actor_sub: str) -> dict:
        """Lê a proposta exigindo mesmo ator — mismatch é erro tipado."""
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q('clara_proposal')}
                     WHERE handle_hash = %s
                    """,
                    (handle_hash(handle),),
                )
                row = cur.fetchone()
        if row is None:
            raise ProposalNotFound("Proposta não encontrada.")
        if row["actor_sub"] != actor_sub:
            raise ProposalActorMismatch(
                "Proposta pertence a outro ator."
            )
        if row["consumed_at"] is not None:
            raise ProposalConsumed("Proposta já consumida.")
        return row

    def consume(self, *, handle: str, actor_sub: str, result: dict) -> dict:
        """Consumo atômico single-use — perdedor recebe `proposal_stale`."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_proposal')}
                           SET consumed_at = now(), result = %s::jsonb
                         WHERE handle_hash = %s
                           AND actor_sub = %s
                           AND consumed_at IS NULL
                        RETURNING *
                        """,
                        (
                            json.dumps(result, default=str),
                            handle_hash(handle),
                            actor_sub,
                        ),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ProposalConsumed(
                            "Proposta já consumida ou inexistente."
                        )
                    return row


    def claim(self, *, handle: str, actor_sub: str) -> dict:
        """Claim durável ANTES de qualquer efeito (S1).

        SELECT para diagnóstico tipado + UPDATE atômico — duas ACTs
        concorrentes sobre a mesma proposta têm exatamente um vencedor;
        a perdedora recebe `proposal_stale`. Não autoriza por si: as
        regras da BFF são reaplicadas na execução.
        """
        from datetime import datetime as _dt, timezone as _tz

        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_proposal')}
                         WHERE handle_hash = %s
                         FOR UPDATE
                        """,
                        (handle_hash(handle),),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ProposalNotFound(
                            "Proposta não encontrada."
                        )
                    if row["actor_sub"] != actor_sub:
                        raise ProposalActorMismatch(
                            "Proposta pertence a outro ator."
                        )
                    if row["claimed_at"] is not None or (
                        row["consumed_at"] is not None
                    ):
                        raise ProposalConsumed(
                            "Proposta já reivindicada ou consumida."
                        )
                    expires_at = row["expires_at"]
                    if (
                        getattr(expires_at, "tzinfo", None) is None
                        and hasattr(expires_at, "replace")
                    ):
                        expires_at = expires_at.replace(tzinfo=_tz.utc)
                    if expires_at < _dt.now(_tz.utc):
                        raise ProposalExpired("Proposta expirada.")
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_proposal')}
                           SET claimed_at = now(),
                               execution_state = 'CLAIMED'
                         WHERE handle_hash = %s
                           AND actor_sub = %s
                           AND claimed_at IS NULL
                           AND consumed_at IS NULL
                        RETURNING *
                        """,
                        (handle_hash(handle), actor_sub),
                    )
                    claimed = cur.fetchone()
                    if claimed is None:
                        raise ProposalConsumed(
                            "Proposta já reivindicada ou consumida."
                        )
                    return claimed

    def record_result(self, *, handle: str, result: dict) -> dict:
        """Grava o outcome verificado e fecha a proposta (terminal).

        Chamada somente após efeito+read-back — nunca antes. outcome:
        executed→VERIFIED, applied→APPLIED, failed→FAILED,
        unverified→UNKNOWN.
        """
        outcome = result.get("outcome", "failed")
        state = {
            "executed": "VERIFIED",
            "applied": "APPLIED",
            "failed": "FAILED",
            "unverified": "UNKNOWN",
        }.get(outcome, "FAILED")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_proposal')}
                           SET result = %s::jsonb,
                               execution_state = %s,
                               consumed_at = now()
                         WHERE handle_hash = %s
                           AND claimed_at IS NOT NULL
                        RETURNING proposal_id
                        """,
                        (
                            json.dumps(result, default=str),
                            state,
                            handle_hash(handle),
                        ),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ProposalConsumed(
                            "Resultado sem claim prévio — estado "
                            "inconsistente."
                        )
                    return row

    def link_batch_operation(
        self, *, handle: str, operation_id: str
    ) -> None:
        with self._conn() as conn:
            with conn.transaction():
                conn.execute(
                    f"""
                    UPDATE {_q('clara_proposal')}
                       SET batch_operation_id = %s
                     WHERE handle_hash = %s
                    """,
                    (operation_id, handle_hash(handle)),
                )


    def claim_by_id(self, *, proposal_id: str, actor_sub: str) -> dict:
        """Claim durável por PK (uso do orquestrador de lote)."""
        from datetime import datetime as _dt, timezone as _tz

        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_proposal')}
                         WHERE proposal_id = %s
                         FOR UPDATE
                        """,
                        (proposal_id,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ProposalNotFound(
                            "Proposta não encontrada."
                        )
                    if row["actor_sub"] != actor_sub:
                        raise ProposalActorMismatch(
                            "Proposta pertence a outro ator."
                        )
                    if row["claimed_at"] is not None or (
                        row["consumed_at"] is not None
                    ):
                        raise ProposalConsumed(
                            "Proposta já reivindicada ou consumida."
                        )
                    expires_at = row["expires_at"]
                    if (
                        getattr(expires_at, "tzinfo", None) is None
                        and hasattr(expires_at, "replace")
                    ):
                        expires_at = expires_at.replace(tzinfo=_tz.utc)
                    if expires_at < _dt.now(_tz.utc):
                        raise ProposalExpired("Proposta expirada.")
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_proposal')}
                           SET claimed_at = now(),
                               execution_state = 'CLAIMED'
                         WHERE proposal_id = %s
                           AND claimed_at IS NULL
                           AND consumed_at IS NULL
                        RETURNING *
                        """,
                        (proposal_id,),
                    )
                    claimed = cur.fetchone()
                    if claimed is None:
                        raise ProposalConsumed(
                            "Proposta já reivindicada ou consumida."
                        )
                    return claimed

    def record_result_by_id(
        self, *, proposal_id: str, result: dict
    ) -> dict:
        """Versão por PK do record_result (orquestrador de lote)."""
        outcome = result.get("outcome", "failed")
        state = {
            "executed": "VERIFIED",
            "applied": "APPLIED",
            "failed": "FAILED",
            "unverified": "UNKNOWN",
        }.get(outcome, "FAILED")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_proposal')}
                           SET result = %s::jsonb,
                               execution_state = %s,
                               consumed_at = now()
                         WHERE proposal_id = %s
                           AND claimed_at IS NOT NULL
                        RETURNING proposal_id
                        """,
                        (
                            json.dumps(result, default=str),
                            state,
                            proposal_id,
                        ),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ProposalConsumed(
                            "Resultado sem claim prévio — estado "
                            "inconsistente."
                        )
                    return row

    # -- leitura/consentimento (step-up consent, V013) -------------------

    def get_by_id(self, *, proposal_id: str) -> dict:
        """Leitura por PK sem lock — uso da superfície de consent."""
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q('clara_proposal')}
                     WHERE proposal_id = %s
                    """,
                    (proposal_id,),
                )
                row = cur.fetchone()
        if row is None:
            raise ProposalNotFound("Proposta não encontrada.")
        return row

    def load_any_for_actor(self, *, handle: str, actor_sub: str) -> dict:
        """Lê a proposta em qualquer estado (reconcile de UNKNOWN).

        Diferente de ``load_for_actor``, não rejeita proposta
        consumida — o caller decide como interpretar o estado.
        """
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q('clara_proposal')}
                     WHERE handle_hash = %s
                    """,
                    (handle_hash(handle),),
                )
                row = cur.fetchone()
        if row is None:
            raise ProposalNotFound("Proposta não encontrada.")
        if row["actor_sub"] != actor_sub:
            raise ProposalActorMismatch(
                "Proposta pertence a outro ator."
            )
        return row

    def record_consent(
        self,
        *,
        proposal_id: str,
        actor_sub: str,
        consent_record: dict,
    ) -> dict:
        """Consentimento step-up do Portal — só antes do claim.

        Escrita permitida apenas por superfície confiável (rota BFF
        com token fresco); a tool MCP nunca grava consent_record.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_proposal')}
                         WHERE proposal_id = %s
                         FOR UPDATE
                        """,
                        (proposal_id,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ProposalNotFound(
                            "Proposta não encontrada."
                        )
                    if row["actor_sub"] != actor_sub:
                        raise ProposalActorMismatch(
                            "Proposta pertence a outro ator."
                        )
                    if row["batch_operation_id"] is not None:
                        raise ChecklistDomainError(
                            "Proposta pertence a um lote — o "
                            "consentimento é consolidado pelo lote."
                        )
                    if row["claimed_at"] is not None or (
                        row["consumed_at"] is not None
                    ):
                        raise ProposalConsumed(
                            "Proposta já reivindicada ou consumida — "
                            "consentimento tardio não é aceito."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_proposal')}
                           SET consent_record = %s::jsonb,
                               consented_at = now()
                         WHERE proposal_id = %s
                           AND claimed_at IS NULL
                           AND consumed_at IS NULL
                        RETURNING proposal_id, consented_at
                        """,
                        (
                            json.dumps(consent_record, default=str),
                            proposal_id,
                        ),
                    )
                    updated = cur.fetchone()
                    if updated is None:
                        raise ProposalConsumed(
                            "Proposta já reivindicada ou consumida."
                        )
                    return updated
