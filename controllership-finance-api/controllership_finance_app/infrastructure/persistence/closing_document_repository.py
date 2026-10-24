"""Adapter PostgreSQL das evidências documentais (P2-Upload SLICE-1).

Idempotência D-U7=A — padrão supplies-api: `UNIQUE(competence_id,
idempotency_key)` + `request_hash` + registros persistentes (sem TTL).
Concorrência resolve no banco (`ON CONFLICT DO NOTHING` + re-leitura do
vencedor): replay idêntico retorna o documento original, payload
divergente levanta `idempotency_conflict` (409). Toda mutação registra
`closing_audit_event` na mesma transação — metadado e auditoria são
inseparáveis.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    CompetenceNotOpened,
    DocumentNotFound,
    IdempotencyConflict,
    ItemNotFound,
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


class ClosingDocumentRepository:
    """Repository/port — evidências de fechamento (SLICE-1: U1–U4)."""

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

    # -- competência / item ----------------------------------------------------

    def get_competence_id(self, period: str) -> str:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT competence_id FROM {_q('monthly_competence')}
                 WHERE period = %s
                """,
                (period,),
            )
            row = cur.fetchone()
        if row is None:
            raise CompetenceNotOpened(
                "Competência ainda não foi aberta."
            )
        return str(row["competence_id"])

    def get_snapshot_item_id(
        self, competence_id: str, snapshot_item_id: str
    ) -> str:
        """Item deve pertencer à competência do path (D-U6=A) — cross-
        competence nunca é autorizado nem revelado (404)."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT snapshot_item_id
                  FROM {_q('competence_checklist_item')}
                 WHERE competence_id = %s AND snapshot_item_id = %s
                """,
                (competence_id, snapshot_item_id),
            )
            row = cur.fetchone()
        if row is None:
            raise ItemNotFound("Item do checklist não encontrado.")
        return str(row["snapshot_item_id"])

    # -- idempotência ------------------------------------------------------------

    def find_document_by_idempotency(
        self, competence_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT d.document_id, d.competence_id, d.snapshot_item_id,
                       d.link_kind, d.title, d.attachment_role, d.state,
                       d.current_version_no, d.revision, d.request_hash,
                       d.uploaded_by, d.created_at
                  FROM {_q('closing_document')} d
                 WHERE d.competence_id = %s AND d.idempotency_key = %s
                """,
                (competence_id, idempotency_key),
            )
            return cur.fetchone()

    # -- criação U1 (transação única) ---------------------------------------------

    def create_document(
        self,
        *,
        competence_id: str,
        snapshot_item_id: str | None,
        link_kind: str,
        title: str | None,
        attachment_role: str,
        idempotency_key: str,
        request_hash: str,
        storage_key: str,
        original_name: str,
        stored_name: str,
        mime_type: str,
        extension: str,
        size_bytes: int,
        checksum_sha256: str,
        actor: str,
    ) -> tuple[dict[str, Any], bool]:
        """document_file + closing_document + document_version(v1) + audit.

        `ON CONFLICT (competence_id, idempotency_key) DO NOTHING`:
        corrida perdida aborta a transação — o vencedor é re-lido fora
        e comparado pelo `request_hash` (replay ⇒ existente; divergente
        ⇒ `idempotency_conflict`). Retorna ``(documento, created)``.
        """
        inserted = None
        with self._conn() as conn:
            try:
                with conn.transaction():
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('document_file')}
                                (storage_key, original_name, stored_name,
                                 mime_type, extension, size_bytes,
                                 checksum_sha256, created_by)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                            RETURNING file_id
                            """,
                            (
                                storage_key,
                                original_name,
                                stored_name,
                                mime_type,
                                extension,
                                size_bytes,
                                checksum_sha256,
                                actor,
                            ),
                        )
                        file_id = cur.fetchone()["file_id"]
                        cur.execute(
                            f"""
                            INSERT INTO {_q('closing_document')}
                                (competence_id, snapshot_item_id, link_kind,
                                 title, attachment_role, state,
                                 current_version_no, idempotency_key,
                                 request_hash, uploaded_by)
                            VALUES (%s,%s,%s,%s,%s,'ATTACHED',1,%s,%s,%s)
                            ON CONFLICT (competence_id, idempotency_key)
                                DO NOTHING
                            RETURNING document_id
                            """,
                            (
                                competence_id,
                                snapshot_item_id,
                                link_kind,
                                title,
                                attachment_role,
                                idempotency_key,
                                request_hash,
                                actor,
                            ),
                        )
                        inserted = cur.fetchone()
                        if inserted is None:
                            raise _IdempotencyRaceLost()
                        document_id = inserted["document_id"]
                        cur.execute(
                            f"""
                            INSERT INTO {_q('document_version')}
                                (document_id, version_no, file_id, state,
                                 uploaded_by)
                            VALUES (%s, 1, %s, 'ATTACHED', %s)
                            """,
                            (document_id, file_id, actor),
                        )
                        self._audit(
                            cur,
                            entity_type="closing_document",
                            entity_id=document_id,
                            competence_id=competence_id,
                            event_type="DOCUMENT_UPLOADED",
                            actor=actor,
                            detail={
                                "link_kind": link_kind,
                                "snapshot_item_id": snapshot_item_id,
                                "attachment_role": attachment_role,
                                "original_name": original_name,
                                "size_bytes": size_bytes,
                                "checksum_sha256": checksum_sha256,
                            },
                        )
            except _IdempotencyRaceLost:
                pass
        if inserted is not None:
            return (
                self.get_document_by_id(competence_id, str(document_id)),
                True,
            )
        winner = self.find_document_by_idempotency(
            competence_id, idempotency_key
        )
        if winner is None:
            raise PersistenceUnavailable(
                "Falha ao recuperar documento idempotente."
            )
        if winner["request_hash"] != request_hash:
            raise IdempotencyConflict(
                "Chave de idempotência já utilizada com payload divergente."
            )
        return self.get_document_by_id(
            competence_id, str(winner["document_id"])
        ), False

    # -- leitura U2/U3/U4 ---------------------------------------------------------

    def get_document_by_id(
        self, competence_id: str, document_id: str
    ) -> dict[str, Any]:
        """Documento só existe dentro da competência do path — cross-
        competence é 404 (existência nunca vaza)."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT d.document_id, d.competence_id, d.snapshot_item_id,
                       i.item_key AS snapshot_item_key,
                       d.link_kind, d.title, d.attachment_role, d.state,
                       d.current_version_no, d.revision, d.uploaded_by,
                       d.created_at, d.updated_at,
                       f.original_name, f.mime_type, f.size_bytes,
                       f.checksum_sha256
                  FROM {_q('closing_document')} d
                  LEFT JOIN {_q('competence_checklist_item')} i
                    ON i.snapshot_item_id = d.snapshot_item_id
                  JOIN {_q('document_version')} v
                    ON v.document_id = d.document_id
                   AND v.version_no = d.current_version_no
                  JOIN {_q('document_file')} f
                    ON f.file_id = v.file_id
                 WHERE d.competence_id = %s AND d.document_id = %s
                """,
                (competence_id, document_id),
            )
            row = cur.fetchone()
        if row is None:
            raise DocumentNotFound("Documento não encontrado.")
        return row

    def list_documents(
        self,
        competence_id: str,
        *,
        snapshot_item_id: str | None = None,
        link_kind: str | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        clauses = ["d.competence_id = %s"]
        params: list[Any] = [competence_id]
        if snapshot_item_id:
            clauses.append("d.snapshot_item_id = %s")
            params.append(snapshot_item_id)
        if link_kind:
            clauses.append("d.link_kind = %s")
            params.append(link_kind)
        if state:
            clauses.append("d.state = %s")
            params.append(state)
        where = " AND ".join(clauses)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT count(*) AS total
                  FROM {_q('closing_document')} d
                 WHERE {where}
                """,
                params,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"""
                SELECT d.document_id, d.competence_id, d.snapshot_item_id,
                       i.item_key AS snapshot_item_key,
                       d.link_kind, d.title, d.attachment_role, d.state,
                       d.current_version_no, d.uploaded_by, d.created_at,
                       f.original_name, f.mime_type, f.size_bytes,
                       f.checksum_sha256
                  FROM {_q('closing_document')} d
                  JOIN {_q('document_version')} v
                    ON v.document_id = d.document_id
                   AND v.version_no = d.current_version_no
                  JOIN {_q('document_file')} f
                    ON f.file_id = v.file_id
                  LEFT JOIN {_q('competence_checklist_item')} i
                    ON i.snapshot_item_id = d.snapshot_item_id
                 WHERE {where}
                 ORDER BY d.created_at DESC, d.document_id
                 LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            items = cur.fetchall()
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def get_version_file(
        self, competence_id: str, document_id: str, version_no: int
    ) -> dict[str, Any]:
        """Versão + metadado do arquivo — download nunca vaza storage_key."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT v.document_version_id, v.version_no, v.state,
                       v.uploaded_by, v.created_at,
                       f.file_id, f.storage_key, f.original_name,
                       f.mime_type, f.size_bytes, f.checksum_sha256
                  FROM {_q('closing_document')} d
                  JOIN {_q('document_version')} v
                    ON v.document_id = d.document_id
                  JOIN {_q('document_file')} f
                    ON f.file_id = v.file_id
                 WHERE d.competence_id = %s AND d.document_id = %s
                   AND v.version_no = %s
                """,
                (competence_id, document_id, version_no),
            )
            row = cur.fetchone()
        if row is None:
            raise DocumentNotFound("Documento não encontrado.")
        return row

    def audit_download(
        self,
        *,
        competence_id: str,
        document_id: str,
        version_no: int,
        actor: str,
        result: str,
    ) -> None:
        """`DOCUMENT_DOWNLOADED` — D-U3=A: autorização efetivada, sem
        bytes/tokens; a linha distingue o resultado (AUTHORIZED agora;
        DENIED/FAILED são reservados para fluxos que os produzam)."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    self._audit(
                        cur,
                        entity_type="closing_document",
                        entity_id=document_id,
                        competence_id=competence_id,
                        event_type="DOCUMENT_DOWNLOADED",
                        actor=actor,
                        detail={"version_no": version_no, "result": result},
                    )

    # -- internals --------------------------------------------------------------

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
        import json

        cur.execute(
            f"""
            INSERT INTO {_q('closing_audit_event')}
                (entity_type, entity_id, competence_id, event_type,
                 actor_subject, detail)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                entity_type,
                str(entity_id),
                competence_id,
                event_type,
                actor,
                json.dumps(detail),
            ),
        )


class _IdempotencyRaceLost(Exception):
    """Sinal interno: `ON CONFLICT DO NOTHING` indica vencedor concorrente."""
