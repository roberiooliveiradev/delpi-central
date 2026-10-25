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
