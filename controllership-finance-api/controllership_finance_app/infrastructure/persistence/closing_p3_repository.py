"""P3 — cutoff humano governado, revalidação e conciliação (doc 10/15.1).

Regras canônicas implementadas:

- cutoff é confirmação humana única por competência — nunca inferido
  de aparente estabilidade (RQ-P3-01);
- revalidação pós-cutoff é append-only (`closing_revalidation`) e vale
  apenas para a `input_fingerprint` vigente: qualquer input de source
  alterado depois invalida a prontidão → `REVALIDATION_REQUIRED`
  (RQ-P3-02/06);
- paridade monetária é exatamente `R$ 0,00` por domínio
  (`ENTRADAS_SAIDAS`/`P7`/`H02`): `R$ 0,01` ou `-R$ 0,01` bloqueia
  (RQ-P3-03, `numeric(19,2)` — comparação exata, sem float);
- zero pré-cutoff é resultado preliminar, nunca final (RQ-P3-04);
- source indisponível permanece `UNAVAILABLE`/`PARTIAL`/`ERROR` —
  nunca é convertida em zero nem libera readiness (RQ-P3-05);
- `READY_TO_CLOSE` exige simultaneamente: cutoff confirmado,
  revalidação válida, todas as sources `AVAILABLE`, divergência zero;
- `STOCK_CLOSED` somente reflete `closing_stock_state` sincronizada
  pelo owner — linha ausente = `UNAVAILABLE`, sem fallback manual
  (RQ-P3-08); estado canônico é terminal no Portal (RQ-P3-08A);
- nenhuma escrita TOTVS/ERP (RQ-P3-07).
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    OfficialDocumentRequired,
    ChecklistDomainError,
    CompetenceNotOpened,
    CutoffAlreadyConfirmed,
    CutoffNotConfirmed,
    InvalidReconciliationDomain,
    InvalidSourceState,
    PersistenceUnavailable,
    StaleRevision,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME

RECONCILIATION_DOMAINS = ("ENTRADAS_SAIDAS", "P7", "H02")

SOURCE_STATES = frozenset(
    {"AVAILABLE", "STALE", "UNAVAILABLE", "PARTIAL", "ERROR"}
)

ZERO = Decimal("0.00")


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


class ClosingP3Repository:
    """Repository/port implementation — psycopg connection-per-call."""

    def _conn(self) -> psycopg.Connection:
        if not plugins_db_configured():
            raise PersistenceUnavailable(
                "Persistência do workflow não configurada."
            )
        try:
            return plugins_db_connect()
        except psycopg.Error as exc:
            raise PersistenceUnavailable(
                "Persistência do workflow indisponível."
            ) from exc

    def _competence_id(self, cur, period: str) -> str:
        cur.execute(
            f"SELECT competence_id FROM {_q('monthly_competence')}"
            " WHERE period = %s",
            (period,),
        )
        row = cur.fetchone()
        if row is None:
            raise CompetenceNotOpened(
                f"Competência {period} não está aberta."
            )
        return row["competence_id"]

    def _audit(
        self,
        cur,
        *,
        entity_type: str,
        entity_id: Any,
        event_type: str,
        actor: str,
        detail: dict[str, Any],
        competence_id: Any = None,
    ) -> None:
        cur.execute(
            f"""
            INSERT INTO {_q('closing_audit_event')}
                (entity_type, entity_id, competence_id, event_type,
                 actor_subject, detail)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                entity_type,
                entity_id,
                competence_id,
                event_type,
                actor,
                json.dumps(detail, default=str),
            ),
        )

    # -- leituras base ----------------------------------------------------

    def _cutoff(self, cur, competence_id: str) -> dict | None:
        cur.execute(
            f"""
            SELECT cutoff_id, competence_id, confirmed_by, confirmed_at,
                   notes, revision
              FROM {_q('closing_cutoff')}
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        return cur.fetchone()

    def _reconciliations(self, cur, competence_id: str) -> dict[str, dict]:
        cur.execute(
            f"""
            SELECT reconciliation_id, domain, source_state,
                   expected_amount, reported_amount, fetched_at,
                   rule_version, provenance, provenance_kind,
                   official_document_id, input_fingerprint,
                   revision, updated_at
              FROM {_q('closing_reconciliation')}
             WHERE competence_id = %s
             ORDER BY domain
            """,
            (competence_id,),
        )
        return {r["domain"]: r for r in cur.fetchall()}

    def _last_revalidation(self, cur, competence_id: str) -> dict | None:
        cur.execute(
            f"""
            SELECT revalidation_id, validated_by, validated_at, result,
                   input_fingerprint, notes
              FROM {_q('closing_revalidation')}
             WHERE competence_id = %s
             ORDER BY validated_at DESC, revalidation_id DESC
             LIMIT 1
            """,
            (competence_id,),
        )
        return cur.fetchone()

    def _stock_state(self, cur, competence_id: str) -> dict | None:
        cur.execute(
            f"""
            SELECT canonical_state, source, fetched_at
              FROM {_q('closing_stock_state')}
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        return cur.fetchone()

    # -- derivação de estado --------------------------------------------

    @staticmethod
    def _fingerprint(recons: dict[str, dict]) -> str:
        """Identidade dos inputs conciliados — qualquer mudança de
        source/amount invalida a revalidação anterior."""
        payload = {
            d: {
                "source_state": (recons.get(d) or {}).get("source_state"),
                "expected": str((recons.get(d) or {}).get("expected_amount")),
                "reported": str(
                    (recons.get(d) or {}).get("reported_amount")
                ),
            }
            for d in RECONCILIATION_DOMAINS
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()

    @staticmethod
    def _divergence(row: dict | None) -> Decimal | None:
        if not row or row["source_state"] != "AVAILABLE":
            return None
        if row["expected_amount"] is None or row["reported_amount"] is None:
            return None
        return (row["reported_amount"] - row["expected_amount"]).quantize(
            Decimal("0.01")
        )

    def get_p3_state(self, period: str) -> dict[str, Any]:
        """Readiness derivada — nunca persistida como verdade única."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            cutoff = self._cutoff(cur, competence_id)
            recons = self._reconciliations(cur, competence_id)
            reval = self._last_revalidation(cur, competence_id)
            stock = self._stock_state(cur, competence_id)

            fingerprint = self._fingerprint(recons)
            divergences = {
                d: self._divergence(recons.get(d))
                for d in RECONCILIATION_DOMAINS
            }
            all_available = all(
                (recons.get(d) or {}).get("source_state") == "AVAILABLE"
                for d in RECONCILIATION_DOMAINS
            )
            zero_divergence = all(v == ZERO for v in divergences.values())
            revalidation_valid = (
                reval is not None
                and reval["result"] == "VALID"
                and reval["input_fingerprint"] == fingerprint
            )
            canonical = (
                stock["canonical_state"] if stock else "UNAVAILABLE"
            )

            blockers: list[str] = []
            if cutoff is None:
                blockers.append("cutoff_not_confirmed")
            if cutoff is not None and not revalidation_valid:
                blockers.append("revalidation_required")
            for d in RECONCILIATION_DOMAINS:
                state = (recons.get(d) or {}).get(
                    "source_state", "UNAVAILABLE"
                )
                if state != "AVAILABLE":
                    blockers.append(f"source_unavailable:{d}")
                elif divergences[d] != ZERO:
                    blockers.append(f"divergence:{d}")

            if canonical == "CLOSED":
                state = "STOCK_CLOSED"
            elif not blockers:
                state = "READY_TO_CLOSE"
            elif cutoff is None:
                state = "WAITING_FOR_CUTOFF"
            elif not revalidation_valid:
                state = "REVALIDATION_REQUIRED"
            else:
                state = "REVALIDATION_REQUIRED"

            return {
                "period": period,
                "state": state,
                "canonical_stock_state": canonical,
                "cutoff": cutoff,
                "reconciliations": [
                    {
                        **(recons.get(d) or {"domain": d,
                                             "source_state": "UNAVAILABLE"}),
                        "divergence": divergences[d],
                    }
                    for d in RECONCILIATION_DOMAINS
                ],
                "last_revalidation": reval,
                "revalidation_valid": revalidation_valid,
                "input_fingerprint": fingerprint,
                "blockers": blockers,
            }

    # -- mutações governadas --------------------------------------------

    def confirm_cutoff(
        self, period: str, *, actor: str, notes: str | None = None
    ) -> dict[str, Any]:
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    try:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('closing_cutoff')}
                                (competence_id, confirmed_by, notes)
                            VALUES (%s, %s, %s)
                            RETURNING cutoff_id, competence_id,
                                      confirmed_by, confirmed_at,
                                      notes, revision
                            """,
                            (competence_id, actor, notes),
                        )
                    except psycopg.errors.UniqueViolation:
                        raise CutoffAlreadyConfirmed(
                            "Cutoff já confirmado para esta competência."
                        )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_p3",
                        entity_id=row["cutoff_id"],
                        competence_id=competence_id,
                        event_type="CUTOFF_CONFIRMED",
                        actor=actor,
                        detail={"period": period, "notes": notes},
                    )
                    return row

    def upsert_reconciliation(
        self,
        period: str,
        domain: str,
        *,
        actor: str,
        source_state: str,
        expected_amount: Decimal | None = None,
        reported_amount: Decimal | None = None,
        rule_version: str | None = None,
        provenance: dict | None = None,
        provenance_kind: str = "DECLARED",
        official_document_id: str | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        if domain not in RECONCILIATION_DOMAINS:
            raise InvalidReconciliationDomain(
                f"domain deve ser um de {RECONCILIATION_DOMAINS}."
            )
        if source_state not in SOURCE_STATES:
            raise InvalidSourceState(
                f"source_state deve ser um de {sorted(SOURCE_STATES)}."
            )
        provenance_kind = (provenance_kind or "DECLARED").strip().upper()
        if provenance_kind not in ("DECLARED", "OFFICIAL"):
            raise InvalidSourceState(
                "provenance_kind deve ser DECLARED ou OFFICIAL."
            )
        if provenance_kind == "OFFICIAL" and not official_document_id:
            raise OfficialDocumentRequired(
                "provenance_kind OFFICIAL exige official_document_id "
                "de artefato oficial anexado na competencia."
            )
        if provenance_kind == "DECLARED":
            official_document_id = None
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    if official_document_id is not None:
                        cur.execute(
                            f"""
                            SELECT document_id
                              FROM {_q('closing_document')}
                             WHERE document_id = %s
                               AND competence_id = %s
                               AND state = 'ATTACHED'
                            """,
                            (official_document_id, competence_id),
                        )
                        if cur.fetchone() is None:
                            raise OfficialDocumentRequired(
                                "official_document_id nao corresponde a "
                                "documento anexado nesta competencia."
                            )
                    cur.execute(
                        f"""
                        SELECT reconciliation_id, revision
                          FROM {_q('closing_reconciliation')}
                         WHERE competence_id = %s AND domain = %s
                         FOR UPDATE
                        """,
                        (competence_id, domain),
                    )
                    existing = cur.fetchone()
                    if existing is not None:
                        if (
                            expected_revision is not None
                            and existing["revision"] != expected_revision
                        ):
                            raise StaleRevision(
                                "A conciliação foi alterada por outra "
                                "sessão."
                            )
                        cur.execute(
                            f"""
                            UPDATE {_q('closing_reconciliation')}
                               SET source_state = %s,
                                   expected_amount = %s,
                                   reported_amount = %s,
                                   fetched_at = now(),
                                   rule_version = %s,
                                   provenance = %s::jsonb,
                                   provenance_kind = %s,
                                   official_document_id = %s,
                                   revision = revision + 1,
                                   updated_at = now()
                             WHERE reconciliation_id = %s
                             RETURNING reconciliation_id, domain,
                                       source_state, expected_amount,
                                       reported_amount, fetched_at,
                                       rule_version, provenance,
                                       provenance_kind,
                                       official_document_id,
                                       revision, updated_at
                            """,
                            (
                                source_state,
                                expected_amount,
                                reported_amount,
                                rule_version,
                                json.dumps(provenance)
                                if provenance
                                else None,
                                provenance_kind,
                                official_document_id,
                                existing["reconciliation_id"],
                            ),
                        )
                        row = cur.fetchone()
                    else:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('closing_reconciliation')}
                                (competence_id, domain, source_state,
                                 expected_amount, reported_amount,
                                 fetched_at, rule_version, provenance,
                                 provenance_kind, official_document_id)
                            VALUES (%s, %s, %s, %s, %s, now(), %s,
                                    %s::jsonb, %s, %s)
                            RETURNING reconciliation_id, domain,
                                      source_state, expected_amount,
                                      reported_amount, fetched_at,
                                      rule_version, provenance,
                                      provenance_kind,
                                      official_document_id,
                                      revision, updated_at
                            """,
                            (
                                competence_id,
                                domain,
                                source_state,
                                expected_amount,
                                reported_amount,
                                rule_version,
                                json.dumps(provenance)
                                if provenance
                                else None,
                                provenance_kind,
                                official_document_id,
                            ),
                        )
                        row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_reconciliation",
                        entity_id=row["reconciliation_id"],
                        competence_id=competence_id,
                        event_type="RECONCILIATION_UPDATED",
                        actor=actor,
                        detail={
                            "domain": domain,
                            "source_state": source_state,
                            "provenance_kind": provenance_kind,
                            "official_document_id": (
                                str(official_document_id)
                                if official_document_id
                                else None
                            ),
                            "expected_amount": (
                                str(expected_amount)
                                if expected_amount is not None
                                else None
                            ),
                            "reported_amount": (
                                str(reported_amount)
                                if reported_amount is not None
                                else None
                            ),
                        },
                    )
                    return row

    def revalidate(
        self,
        period: str,
        *,
        actor: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Revalidação pós-cutoff dos inputs — append-only."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    cutoff = self._cutoff(cur, competence_id)
                    if cutoff is None:
                        raise CutoffNotConfirmed(
                            "Revalidação exige cutoff confirmado."
                        )
                    recons = self._reconciliations(cur, competence_id)
                    fingerprint = self._fingerprint(recons)
                    all_available = all(
                        (recons.get(d) or {}).get("source_state")
                        == "AVAILABLE"
                        for d in RECONCILIATION_DOMAINS
                    )
                    result = "VALID" if all_available else "STALE_INPUT"
                    cur.execute(
                        f"""
                        INSERT INTO {_q('closing_revalidation')}
                            (competence_id, validated_by, result,
                             input_fingerprint, notes)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING revalidation_id, validated_by,
                                  validated_at, result,
                                  input_fingerprint, notes
                        """,
                        (
                            competence_id,
                            actor,
                            result,
                            fingerprint,
                            notes,
                        ),
                    )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_p3",
                        entity_id=row["revalidation_id"],
                        competence_id=competence_id,
                        event_type="P3_REVALIDATED",
                        actor=actor,
                        detail={
                            "result": result,
                            "input_fingerprint": fingerprint,
                            "notes": notes,
                        },
                    )
                    return row

    def list_p3_events(
        self, period: str, *, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            cur.execute(
                f"""
                SELECT event_id, event_type, actor_subject, detail,
                       created_at
                  FROM {_q('closing_audit_event')}
                 WHERE competence_id = %s
                   AND entity_type IN ('closing_p3',
                                       'closing_reconciliation')
                 ORDER BY created_at DESC, event_id
                 LIMIT %s OFFSET %s
                """,
                (competence_id, limit, offset),
            )
            return {
                "items": cur.fetchall(),
                "limit": limit,
                "offset": offset,
            }
