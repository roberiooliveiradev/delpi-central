"""CLARA — base de conhecimento própria (V011).

Ingestão governada + recuperação com citação. Nada aqui é sistema de
registro: todo item carrega proveniência (fonte, versão, hash,
autoridade) e `citation_locator` verificável. Recuperação respeita
`access_scope` — `INTERNAL_ONLY` nunca sai para usuário do Portal.

Classificações honestas (`evidence_classification`):
PROVEN_SCREENSHOT/PROVEN_CODE/PROVEN_TEST = comprovado por artefato;
OWNER_REPORTED_VIA_PO = declaração do responsável; TO_INVENTORY =
inventariado sem confirmação; TARGET = desejado, não implementado;
APPROVED_RULE = decisão de produto aprovada; CURRENT_IMPLEMENTATION =
comportamento vigente no HEAD.
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


class KnowledgeSourceConflict(ChecklistDomainError):
    code = "knowledge_source_conflict"
    status = 409


class KnowledgeNotFound(ChecklistDomainError):
    code = "knowledge_not_found"
    status = 404


SOURCE_TYPES = frozenset(
    {
        "DOCUMENT",
        "VIDEO_OBSERVATION",
        "VIDEO_TRANSCRIPT",
        "MATRIX",
        "INVENTORY",
        "REPORT_SAMPLE",
        "CONTRACT",
        "CODE_EVIDENCE",
        "TEST_EVIDENCE",
    }
)

EVIDENCE_CLASSIFICATIONS = frozenset(
    {
        "PROVEN_SCREENSHOT",
        "PROVEN_CODE",
        "PROVEN_TEST",
        "OWNER_REPORTED_VIA_PO",
        "TO_INVENTORY",
        "TARGET",
        "APPROVED_RULE",
        "CURRENT_IMPLEMENTATION",
    }
)

ACCESS_SCOPES = frozenset(
    {"PORTAL_ACCESS", "PORTAL_MANAGE", "INTERNAL_ONLY"}
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ClaraKnowledgeRepository:
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

    # -- ingestão ----------------------------------------------------------

    def register_source(
        self,
        *,
        source_id: str,
        source_type: str,
        name: str,
        source_version: str | None = None,
        source_hash: str | None = None,
        origin_authority: str = "TO_INVENTORY",
        description: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Registra/atualiza fonte autorizada (upsert por source_id)."""
        if source_type not in SOURCE_TYPES:
            raise ChecklistDomainError(
                f"source_type inválido: {source_type}."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {_q('clara_knowledge_source')}
                            (source_id, source_type, name, source_version,
                             source_hash, origin_authority, description,
                             metadata)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                        ON CONFLICT (source_id) DO UPDATE SET
                            source_type = EXCLUDED.source_type,
                            name = EXCLUDED.name,
                            source_version = EXCLUDED.source_version,
                            source_hash = EXCLUDED.source_hash,
                            origin_authority = EXCLUDED.origin_authority,
                            description = EXCLUDED.description,
                            metadata = EXCLUDED.metadata
                        RETURNING *
                        """,
                        (
                            source_id,
                            source_type,
                            name,
                            source_version,
                            source_hash,
                            origin_authority,
                            description,
                            json.dumps(metadata or {}),
                        ),
                    )
                    return cur.fetchone()

    def ingest_item(
        self,
        *,
        source_id: str,
        topic: str,
        title: str,
        content: str,
        business_step: str | None = None,
        related_report_ids: list[str] | None = None,
        origin_authority: str = "TO_INVENTORY",
        evidence_classification: str = "OWNER_REPORTED_VIA_PO",
        citation_locator: dict | None = None,
        access_scope: str = "PORTAL_ACCESS",
        valid_from: str | None = None,
        supersedes: str | None = None,
    ) -> dict:
        """Insere segmento de conhecimento. Deduplica por (source_id,
        locator, content_hash) — reingestão idêntica não duplica."""
        if evidence_classification not in EVIDENCE_CLASSIFICATIONS:
            raise ChecklistDomainError(
                "evidence_classification inválida."
            )
        if access_scope not in ACCESS_SCOPES:
            raise ChecklistDomainError("access_scope inválido.")
        content_hash = _sha256(content)
        locator = citation_locator or {}
        locator_key = locator.get("key")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    # Dedup/supersede por locator estável (doc+heading) —
                    # line_range muda quando o doc evolui e não deve
                    # quebrar a deduplicação nem a trilha de supersede.
                    cur.execute(
                        f"""
                        SELECT knowledge_id, status, content_hash
                          FROM {_q('clara_knowledge_item')}
                         WHERE source_id = %s
                           AND citation_locator->>'key' = %s
                         ORDER BY indexed_at DESC
                        """,
                        (source_id, locator_key or ""),
                    )
                    existing = cur.fetchall()
                    for row in existing:
                        if row["content_hash"] == content_hash:
                            cur.execute(
                                f"""
                                UPDATE {_q('clara_knowledge_item')}
                                   SET last_verified_at = now(),
                                       status = 'PUBLISHED',
                                       citation_locator = %s::jsonb
                                 WHERE knowledge_id = %s
                                RETURNING *
                                """,
                                (
                                    json.dumps(locator),
                                    row["knowledge_id"],
                                ),
                            )
                            updated = cur.fetchone()
                            updated["_deduplicated"] = True
                            return updated
                    previous_id = None
                    if existing:
                        previous_id = existing[0]["knowledge_id"]
                        cur.execute(
                            f"""
                            UPDATE {_q('clara_knowledge_item')}
                               SET status = 'SUPERSEDED'
                             WHERE knowledge_id = %s
                            """,
                            (previous_id,),
                        )
                    supersedes = supersedes or (
                        str(previous_id) if previous_id else None
                    )
                    if supersedes and not previous_id:
                        cur.execute(
                            f"""
                            UPDATE {_q('clara_knowledge_item')}
                               SET status = 'SUPERSEDED'
                             WHERE knowledge_id = %s
                            """,
                            (supersedes,),
                        )
                    cur.execute(
                        f"""
                        INSERT INTO {_q('clara_knowledge_item')}
                            (source_id, topic, business_step,
                             related_report_ids, origin_authority,
                             evidence_classification, valid_from,
                             access_scope, citation_locator, supersedes,
                             title, content, content_hash)
                        VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s::jsonb,
                                %s,%s,%s,%s)
                        RETURNING knowledge_id, topic, business_step,
                                  title, evidence_classification,
                                  access_scope, citation_locator, status
                        """,
                        (
                            source_id,
                            topic,
                            business_step,
                            json.dumps(related_report_ids or []),
                            origin_authority,
                            evidence_classification,
                            valid_from,
                            access_scope,
                            json.dumps(locator),
                            supersedes,
                            title,
                            content,
                            content_hash,
                        ),
                    )
                    row = cur.fetchone()
                    if previous_id:
                        row["_superseded"] = True
                    return row

    def publish_corpus_version(
        self, *, actor: str, manifest: dict | None = None
    ) -> dict:
        """Fecha uma versão do corpus: contagem + manifest de fontes."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT COUNT(*) AS items,
                               COUNT(DISTINCT source_id) AS sources
                          FROM {_q('clara_knowledge_item')}
                         WHERE status = 'PUBLISHED'
                        """
                    )
                    counts = cur.fetchone()
                    cur.execute(
                        f"""
                        INSERT INTO {_q('clara_corpus_version')}
                            (published_by, item_count, source_count,
                             manifest)
                        VALUES (%s,%s,%s,%s::jsonb)
                        RETURNING *
                        """,
                        (
                            actor,
                            counts["items"],
                            counts["sources"],
                            json.dumps(manifest or {}),
                        ),
                    )
                    return cur.fetchone()

    # -- recuperação ---------------------------------------------------------

    def current_corpus_version(self) -> dict | None:
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q('clara_corpus_version')}
                     WHERE status = 'PUBLISHED'
                     ORDER BY published_at DESC LIMIT 1
                    """
                )
                return cur.fetchone()

    def list_sources(self, *, access_scope: str = "PORTAL_ACCESS") -> list[dict]:
        scope_filter = "AND k.access_scope <> 'INTERNAL_ONLY'"
        if access_scope == "INTERNAL_ONLY":
            scope_filter = ""
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT s.*, COUNT(k.knowledge_id) AS item_count
                      FROM {_q('clara_knowledge_source')} s
                      JOIN {_q('clara_knowledge_item')} k
                        ON k.source_id = s.source_id
                       AND k.status = 'PUBLISHED' {scope_filter}
                     GROUP BY s.source_id
                     ORDER BY s.source_id
                    """
                )
                return cur.fetchall()

    def search(
        self,
        *,
        query: str | None = None,
        topic: str | None = None,
        business_step: str | None = None,
        report_id: str | None = None,
        access_scope: str = "PORTAL_ACCESS",
        limit: int = 8,
    ) -> list[dict]:
        """Recuperação com citação — FTS português + filtros estruturados.

        `INTERNAL_ONLY` nunca alcança escopo de Portal; `PORTAL_MANAGE`
        só sai para manage efetivo (o caller decide o scope do ator).
        """
        clauses = ["k.status = 'PUBLISHED'"]
        where_params: list[Any] = []
        if access_scope == "PORTAL_ACCESS":
            clauses.append("k.access_scope = 'PORTAL_ACCESS'")
        elif access_scope == "PORTAL_MANAGE":
            clauses.append("k.access_scope IN ('PORTAL_ACCESS','PORTAL_MANAGE')")
        if topic:
            clauses.append("k.topic ILIKE %s")
            where_params.append(f"%{topic}%")
        if business_step:
            clauses.append("k.business_step ILIKE %s")
            where_params.append(f"%{business_step}%")
        if report_id:
            clauses.append("k.related_report_ids @> %s::jsonb")
            where_params.append(json.dumps([report_id]))
        rank = "0.0"
        rank_params: list[Any] = []
        if query:
            clauses.append(
                "k.content_tsv @@ plainto_tsquery('portuguese', %s)"
            )
            where_params.append(query)
            rank = (
                "ts_rank(k.content_tsv, "
                "plainto_tsquery('portuguese', %s))"
            )
            rank_params.append(query)
        # O placeholder do rank fica no SELECT — antes dos filtros.
        params = (*rank_params, *where_params)
        limit = max(1, min(int(limit), 50))
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT k.knowledge_id, k.source_id, k.topic,
                           k.business_step, k.related_report_ids,
                           k.origin_authority, k.evidence_classification,
                           k.access_scope, k.citation_locator,
                           k.last_verified_at, k.title, k.content,
                           {rank} AS rank
                      FROM {_q('clara_knowledge_item')} k
                     WHERE {' AND '.join(clauses)}
                     ORDER BY rank DESC, k.indexed_at DESC
                     LIMIT %s
                    """,
                    (*params, limit),
                )
                return cur.fetchall()

    def get_item(
        self, knowledge_id: str, *, access_scope: str = "PORTAL_ACCESS"
    ) -> dict:
        with self._conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT k.*, s.name AS source_name,
                           s.source_type, s.source_version,
                           s.source_hash
                      FROM {_q('clara_knowledge_item')} k
                      JOIN {_q('clara_knowledge_source')} s
                        ON s.source_id = k.source_id
                     WHERE k.knowledge_id = %s
                    """,
                    (knowledge_id,),
                )
                row = cur.fetchone()
        if row is None:
            raise KnowledgeNotFound("Conhecimento não encontrado.")
        scope = row["access_scope"]
        if scope == "INTERNAL_ONLY" or (
            scope == "PORTAL_MANAGE" and access_scope == "PORTAL_ACCESS"
        ):
            raise KnowledgeNotFound("Conhecimento não encontrado.")
        return row
