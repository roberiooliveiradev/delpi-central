"""CLARA — store de desafios de consentimento (R-CLARA-01, Doc 106).

A aprovação humana é um objeto de primeira classe emitido pelo
servidor no PREPARE e vinculado de forma verificável a ator, alvo
(lote ou proposta), plano selado (`plan_hash`/`plan_version`),
expiração, origem autorizada e correlação. A transição é única:

    PENDING → APPROVED → CONSUMED
                 ↘ EXPIRED | REVOKED

O método `approve_*` executa, em UMA transação, a aprovação do
desafio e a gravação do `consent_record` no alvo — nenhuma das duas
escritas existe isolada. A execução (claim do lote/proposta) consome
o desafio na mesma transação do claim.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
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


class ConsentChallengeNotFound(ChecklistDomainError):
    code = "consent_challenge_not_found"
    status = 404


class ConsentChallengeMismatch(ChecklistDomainError):
    code = "consent_challenge_mismatch"
    status = 403


class ConsentChallengeConsumed(ChecklistDomainError):
    code = "consent_challenge_consumed"
    status = 409


class ConsentChallengeExpired(ChecklistDomainError):
    code = "consent_challenge_expired"
    status = 409


class ClaraConsentChallengeRepository:
    """Owner da tabela `clara_consent_challenge` e da gravação de consent."""

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

    # -- emissão (PREPARE) ----------------------------------------------

    def _issue(
        self,
        *,
        kind: str,
        batch_id: str | None,
        proposal_id: str | None,
        actor_sub: str,
        plan_hash: str,
        expires_at: Any,
        correlation_id: str | None = None,
    ) -> dict:
        """Emite (ou devolve o pendente) desafio do alvo — idempotente."""
        target_col = "batch_id" if kind == "batch" else "proposal_id"
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {_q('clara_consent_challenge')}
                            (kind, batch_id, proposal_id, actor_sub,
                             plan_hash, expires_at, correlation_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT ({target_col})
                        WHERE status = 'PENDING'
                        DO NOTHING
                        RETURNING *
                        """,
                        (
                            kind,
                            batch_id,
                            proposal_id,
                            actor_sub,
                            plan_hash,
                            expires_at,
                            correlation_id,
                        ),
                    )
                    row = cur.fetchone()
                    if row is None:
                        col = "batch_id" if kind == "batch" else (
                            "proposal_id"
                        )
                        cur.execute(
                            f"""
                            SELECT * FROM {_q('clara_consent_challenge')}
                             WHERE {col} = %s AND status = 'PENDING'
                            """,
                            (batch_id or proposal_id,),
                        )
                        row = cur.fetchone()
                    return row

    def issue_for_batch(
        self,
        *,
        batch_id: str,
        actor_sub: str,
        plan_hash: str,
        expires_at: Any,
        correlation_id: str | None = None,
    ) -> dict:
        return self._issue(
            kind="batch",
            batch_id=batch_id,
            proposal_id=None,
            actor_sub=actor_sub,
            plan_hash=plan_hash,
            expires_at=expires_at,
            correlation_id=correlation_id,
        )

    def issue_for_proposal(
        self,
        *,
        proposal_id: str,
        actor_sub: str,
        plan_hash: str,
        expires_at: Any,
        correlation_id: str | None = None,
    ) -> dict:
        return self._issue(
            kind="proposal",
            batch_id=None,
            proposal_id=proposal_id,
            actor_sub=actor_sub,
            plan_hash=plan_hash,
            expires_at=expires_at,
            correlation_id=correlation_id,
        )

    # -- leitura ---------------------------------------------------------

    def get_by_id(self, *, challenge_id: str) -> dict:
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q('clara_consent_challenge')}
                     WHERE challenge_id = %s
                    """,
                    (challenge_id,),
                )
                row = cur.fetchone()
        if row is None:
            raise ConsentChallengeNotFound(
                "Desafio de consentimento não encontrado."
            )
        return row

    def latest_for_batch(self, *, batch_id: str) -> dict | None:
        return self._latest(column="batch_id", target_id=batch_id)

    def latest_for_proposal(self, *, proposal_id: str) -> dict | None:
        return self._latest(column="proposal_id", target_id=proposal_id)

    def _latest(self, *, column: str, target_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q('clara_consent_challenge')}
                     WHERE {column} = %s
                     ORDER BY created_at DESC
                     LIMIT 1
                    """,
                    (target_id,),
                )
                return cur.fetchone()

    # -- aprovação + gravação de consent (uma transação) -----------------

    def approve_for_batch(
        self,
        *,
        challenge_id: str,
        batch_id: str,
        actor_sub: str,
        plan_hash: str,
        consent_record: dict,
        token_jti: str | None,
        token_iat: Any,
    ) -> dict:
        """PENDING→APPROVED + consent_record do lote — atômico.

        Idempotente para repetição honesta do mesmo desafio: se o
        desafio já está APPROVED pelo mesmo ator e o lote CONFIRMED
        pelo mesmo registro, devolve o estado vigente em vez de erro.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_consent_challenge')}
                         WHERE challenge_id = %s
                         FOR UPDATE
                        """,
                        (challenge_id,),
                    )
                    challenge = cur.fetchone()
                    if challenge is None:
                        raise ConsentChallengeNotFound(
                            "Desafio de consentimento não encontrado."
                        )
                    self._assert_binding(
                        challenge,
                        kind="batch",
                        target_id=batch_id,
                        actor_sub=actor_sub,
                        plan_hash=plan_hash,
                    )
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
                        raise ConsentChallengeMismatch(
                            "Lote do desafio não existe."
                        )
                    if batch["actor_sub"] != actor_sub:
                        raise ConsentChallengeMismatch(
                            "Desafio pertence a outro ator."
                        )
                    if batch["plan_hash"] != plan_hash:
                        raise ConsentChallengeMismatch(
                            "Desafio não corresponde ao plano selado."
                        )
                    if challenge["status"] == "APPROVED" and (
                        batch["status"] == "CONFIRMED"
                    ):
                        existing = batch.get("consent_record") or {}
                        if isinstance(existing, str):
                            existing = json.loads(existing)
                        if existing.get("challenge_id") == challenge_id:
                            return {
                                "challenge": challenge,
                                "batch_id": batch["batch_id"],
                                "status": batch["status"],
                                "confirmed_at": batch["confirmed_at"],
                            }
                        raise ConsentChallengeConsumed(
                            "Desafio já aprovado para outro registro."
                        )
                    if challenge["status"] != "PENDING":
                        raise ConsentChallengeConsumed(
                            "Desafio já utilizado, expirado ou "
                            "revogado — reprepare a autorização."
                        )
                    self._assert_not_expired(challenge)
                    if batch["status"] != "PREPARED":
                        raise ConsentChallengeConsumed(
                            f"Lote em estado {batch['status']} — não "
                            "aceita consentimento."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_consent_challenge')}
                           SET status = 'APPROVED',
                               approved_at = now(),
                               approved_by = %s,
                               approved_token_jti = %s,
                               approved_token_iat = %s
                         WHERE challenge_id = %s
                        """,
                        (actor_sub, token_jti, token_iat, challenge_id),
                    )
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_batch')}
                           SET consent_mode = 'CONSOLIDATED',
                               consent_record = %s::jsonb,
                               status = 'CONFIRMED',
                               confirmed_at = now()
                         WHERE batch_id = %s
                        RETURNING batch_id, status, confirmed_at
                        """,
                        (json.dumps(consent_record, default=str),
                         batch_id),
                    )
                    updated = cur.fetchone()
                    return {
                        "challenge": challenge,
                        "batch_id": updated["batch_id"],
                        "status": updated["status"],
                        "confirmed_at": updated["confirmed_at"],
                    }

    def approve_for_proposal(
        self,
        *,
        challenge_id: str,
        proposal_id: str,
        actor_sub: str,
        plan_hash: str,
        consent_record: dict,
        token_jti: str | None,
        token_iat: Any,
    ) -> dict:
        """PENDING→APPROVED + consent_record da proposta — atômico."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_consent_challenge')}
                         WHERE challenge_id = %s
                         FOR UPDATE
                        """,
                        (challenge_id,),
                    )
                    challenge = cur.fetchone()
                    if challenge is None:
                        raise ConsentChallengeNotFound(
                            "Desafio de consentimento não encontrado."
                        )
                    self._assert_binding(
                        challenge,
                        kind="proposal",
                        target_id=proposal_id,
                        actor_sub=actor_sub,
                        plan_hash=plan_hash,
                    )
                    cur.execute(
                        f"""
                        SELECT * FROM {_q('clara_proposal')}
                         WHERE proposal_id = %s
                         FOR UPDATE
                        """,
                        (proposal_id,),
                    )
                    proposal = cur.fetchone()
                    if proposal is None:
                        raise ConsentChallengeMismatch(
                            "Proposta do desafio não existe."
                        )
                    if proposal["actor_sub"] != actor_sub:
                        raise ConsentChallengeMismatch(
                            "Desafio pertence a outro ator."
                        )
                    if proposal.get("batch_operation_id") is not None:
                        raise ConsentChallengeMismatch(
                            "Proposta pertence a um lote — o "
                            "consentimento é do lote."
                        )
                    if challenge["status"] == "APPROVED" and (
                        proposal.get("consented_at") is not None
                    ):
                        existing = proposal.get("consent_record") or {}
                        if isinstance(existing, str):
                            existing = json.loads(existing)
                        if existing.get("challenge_id") == challenge_id:
                            return {
                                "challenge": challenge,
                                "proposal_id": proposal["proposal_id"],
                                "consented_at": proposal["consented_at"],
                            }
                        raise ConsentChallengeConsumed(
                            "Desafio já aprovado para outro registro."
                        )
                    if challenge["status"] != "PENDING":
                        raise ConsentChallengeConsumed(
                            "Desafio já utilizado, expirado ou "
                            "revogado — reprepare a autorização."
                        )
                    self._assert_not_expired(challenge)
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_consent_challenge')}
                           SET status = 'APPROVED',
                               approved_at = now(),
                               approved_by = %s,
                               approved_token_jti = %s,
                               approved_token_iat = %s
                         WHERE challenge_id = %s
                        """,
                        (actor_sub, token_jti, token_iat, challenge_id),
                    )
                    cur.execute(
                        f"""
                        UPDATE {_q('clara_proposal')}
                           SET consent_record = %s::jsonb,
                               consented_at = now()
                         WHERE proposal_id = %s
                        RETURNING proposal_id, consented_at
                        """,
                        (json.dumps(consent_record, default=str),
                         proposal_id),
                    )
                    updated = cur.fetchone()
                    return {
                        "challenge": challenge,
                        "proposal_id": updated["proposal_id"],
                        "consented_at": updated["consented_at"],
                    }

    # -- consumo (chamado dentro da transação do claim) ------------------

    def consume_for_batch(self, *, batch_id: str) -> None:
        with self._conn() as conn:
            with conn.transaction():
                conn.execute(
                    f"""
                    UPDATE {_q('clara_consent_challenge')}
                       SET status = 'CONSUMED', consumed_at = now()
                     WHERE batch_id = %s AND status = 'APPROVED'
                    """,
                    (batch_id,),
                )

    def consume_for_proposal(self, *, proposal_id: str) -> None:
        with self._conn() as conn:
            with conn.transaction():
                conn.execute(
                    f"""
                    UPDATE {_q('clara_consent_challenge')}
                       SET status = 'CONSUMED', consumed_at = now()
                     WHERE proposal_id = %s AND status = 'APPROVED'
                    """,
                    (proposal_id,),
                )

    # -- verificação para execução ---------------------------------------

    def verify_batch_binding(
        self,
        *,
        challenge_id: str | None,
        batch_id: str,
        actor_sub: str,
        plan_hash: str,
    ) -> bool:
        """O challenge_id do consent_record prova a aprovação?"""
        if not challenge_id:
            return False
        try:
            challenge = self.get_by_id(challenge_id=str(challenge_id))
        except ConsentChallengeNotFound:
            return False
        return (
            challenge["kind"] == "batch"
            and str(challenge["batch_id"]) == str(batch_id)
            and challenge["actor_sub"] == actor_sub
            and challenge["plan_hash"] == plan_hash
            and challenge["origin"] == "portal"
            and challenge["status"] in ("APPROVED", "CONSUMED")
            and challenge["approved_by"] == actor_sub
        )

    def verify_proposal_binding(
        self,
        *,
        challenge_id: str | None,
        proposal_id: str,
        actor_sub: str,
        plan_hash: str,
    ) -> bool:
        if not challenge_id:
            return False
        try:
            challenge = self.get_by_id(challenge_id=str(challenge_id))
        except ConsentChallengeNotFound:
            return False
        return (
            challenge["kind"] == "proposal"
            and str(challenge["proposal_id"]) == str(proposal_id)
            and challenge["actor_sub"] == actor_sub
            and challenge["plan_hash"] == plan_hash
            and challenge["origin"] == "portal"
            and challenge["status"] in ("APPROVED", "CONSUMED")
            and challenge["approved_by"] == actor_sub
        )

    # -- validações internas ----------------------------------------------

    @staticmethod
    def _assert_binding(
        challenge: dict,
        *,
        kind: str,
        target_id: str,
        actor_sub: str,
        plan_hash: str,
    ) -> None:
        target = (
            challenge["batch_id"]
            if kind == "batch"
            else challenge["proposal_id"]
        )
        if challenge["kind"] != kind or str(target) != str(target_id):
            raise ConsentChallengeMismatch(
                "Desafio emitido para outro objeto — não autoriza "
                "este consentimento."
            )
        if challenge["actor_sub"] != actor_sub:
            raise ConsentChallengeMismatch(
                "Desafio emitido para outro usuário."
            )
        if challenge["plan_hash"] != plan_hash:
            raise ConsentChallengeMismatch(
                "Desafio emitido para outro plano — o plano selado "
                "não pode ser alterado após a emissão."
            )
        if challenge["origin"] != "portal":
            raise ConsentChallengeMismatch(
                "Origem do desafio não autorizada."
            )

    @staticmethod
    def _assert_not_expired(challenge: dict) -> None:
        expires = challenge["expires_at"]
        if getattr(expires, "tzinfo", None) is None and hasattr(
            expires, "replace"
        ):
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise ConsentChallengeExpired(
                "Desafio de consentimento expirado — reprepare a "
                "autorização."
            )
