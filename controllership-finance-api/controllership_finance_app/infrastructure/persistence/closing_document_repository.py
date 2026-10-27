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
    DocumentCancelled,
    DocumentNotAttached,
    DocumentNotFound,
    IdempotencyConflict,
    ItemLockedBySubmittedPackage,
    ItemNotFound,
    PersistenceUnavailable,
    StaleRevision,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    lock_competence_row,
    locked_item_keys_in,
)
from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
    recompute_item_state,
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

    @staticmethod
    def _assert_snapshot_unlocked(
        cur, competence_id: str, snapshot_item_id: str | None
    ) -> None:
        """R-105-04: revalida o congelamento de evidência DENTRO da
        mesma transação e sob o lock da competência — elimina a janela
        TOCTOU entre a checagem pré-mutação e o INSERT/UPDATE."""
        if not snapshot_item_id:
            return
        cur.execute(
            f"SELECT item_key FROM {_q('competence_checklist_item')}"
            " WHERE snapshot_item_id = %s AND competence_id = %s",
            (snapshot_item_id, competence_id),
        )
        row = cur.fetchone()
        if row and row["item_key"] in locked_item_keys_in(
            cur, competence_id
        ):
            raise ItemLockedBySubmittedPackage(
                f"Item {row['item_key']} integra pacote submetido — "
                "correção exige nova versão do pacote "
                "(reabrir/complementar)."
            )

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

    def get_snapshot_item(
        self, competence_id: str, snapshot_item_id: str
    ) -> dict[str, Any]:
        """Item deve pertencer à competência do path (D-U6=A) — cross-
        competence nunca é autorizado nem revelado (404). Retorna o
        `branch_scope` do item: o documento vinculado herda esse escopo
        (doc 103 §117)."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT snapshot_item_id, item_key, branch_scope
                  FROM {_q('competence_checklist_item')}
                 WHERE competence_id = %s AND snapshot_item_id = %s
                """,
                (competence_id, snapshot_item_id),
            )
            row = cur.fetchone()
        if row is None:
            raise ItemNotFound("Item do checklist não encontrado.")
        return row

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
                        # R-105-04: serializa contra submit_for_review —
                        # lock + revalidação na mesma transação.
                        lock_competence_row(cur, competence_id)
                        self._assert_snapshot_unlocked(
                            cur, competence_id, snapshot_item_id
                        )
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
                                (document_id, version_no, file_id,
                                 uploaded_by, idempotency_key,
                                 request_hash)
                            VALUES (%s, 1, %s, %s, %s, %s)
                            """,
                            (
                                document_id,
                                file_id,
                                actor,
                                idempotency_key,
                                request_hash,
                            ),
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
                       COALESCE(i.branch_scope, 'BOTH') AS branch_scope,
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
        branch_scope: str | None = None,
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
        else:
            # Listagem ativa: CANCELLED só aparece via filtro explícito —
            # o documento permanece consultável (U3/U6/U8), nunca some.
            clauses.append("d.state != 'CANCELLED'")
        if branch_scope and branch_scope != "BOTH":
            # Escopo herdado do item (competência = BOTH): o contexto
            # específico alcança o próprio escopo + recursos BOTH.
            clauses.append(
                "COALESCE(i.branch_scope, 'BOTH') IN ('BOTH', %s)"
            )
            params.append(branch_scope)
        where = " AND ".join(clauses)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT count(*) AS total
                  FROM {_q('closing_document')} d
                  LEFT JOIN {_q('competence_checklist_item')} i
                    ON i.snapshot_item_id = d.snapshot_item_id
                 WHERE {where}
                """,
                params,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"""
                SELECT d.document_id, d.competence_id, d.snapshot_item_id,
                       i.item_key AS snapshot_item_key,
                       COALESCE(i.branch_scope, 'BOTH') AS branch_scope,
                       d.link_kind, d.title, d.attachment_role, d.state,
                       d.current_version_no, d.revision, d.uploaded_by,
                       d.created_at,
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
                SELECT v.document_version_id, v.version_no,
                       CASE WHEN v.version_no = d.current_version_no
                            THEN 'ATTACHED' ELSE 'SUPERSEDED'
                       END AS state,
                       v.uploaded_by, v.created_at,
                       COALESCE(i.branch_scope, 'BOTH') AS branch_scope,
                       f.file_id, f.storage_key, f.original_name,
                       f.mime_type, f.size_bytes, f.checksum_sha256
                  FROM {_q('closing_document')} d
                  JOIN {_q('document_version')} v
                    ON v.document_id = d.document_id
                  JOIN {_q('document_file')} f
                    ON f.file_id = v.file_id
                  LEFT JOIN {_q('competence_checklist_item')} i
                    ON i.snapshot_item_id = d.snapshot_item_id
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
        """`DOCUMENT_DOWNLOADED` — D-U3=A: sem bytes/tokens.

        `result` distingue AUTHORIZED/DENIED/FAILED; `phase` classifica
        explicitamente a etapa registrada — decisão de autorização
        (AUTHORIZED/DENIED) versus falha de entrega (FAILED). O evento
        nunca reivindica transferência concluída: a infraestrutura
        (`FileResponse`) não prova que os bytes chegaram ao cliente."""
        phase = "delivery" if result == "FAILED" else "authorization"
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
                        detail={
                            "version_no": version_no,
                            "result": result,
                            "phase": phase,
                        },
                    )

    # -- mutações U5/U7 (SLICE-2) -------------------------------------------------

    def find_version_by_idempotency(
        self, document_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        """Registro de idempotência da mutação de versão (D-U7=A no
        aggregate `document_version` — nunca a key U1 reutilizada)."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT document_version_id, document_id, version_no,
                       idempotency_key, request_hash
                  FROM {_q('document_version')}
                 WHERE document_id = %s AND idempotency_key = %s
                """,
                (document_id, idempotency_key),
            )
            return cur.fetchone()

    def add_version(
        self,
        *,
        competence_id: str,
        document_id: str,
        expected_revision: int,
        storage_key: str,
        original_name: str,
        stored_name: str,
        mime_type: str,
        extension: str,
        size_bytes: int,
        checksum_sha256: str,
        idempotency_key: str,
        request_hash: str,
        actor: str,
    ) -> tuple[dict[str, Any], bool]:
        """U5 — versão N+1 + audit; retorna ``(documento, created)``.

        Ordem canônica sob `SELECT ... FOR UPDATE` na linha do documento:
        1. **idempotência** — key já registrada ⇒ replay idêntico
           deduplica (`created=False`, efeito já aplicado) e divergente
           aborta com `idempotency_conflict`; o replay não recria versão
           nem evento mesmo com `revision` já obsoleta;
        2. **OCC** — `revision` reavaliada sob lock ⇒ perdedor recebe
           `stale_revision` (409) e nenhuma versão se perde (AC-P2-UP-21);
        3. **mutação** — `document_version` é linha imutável (V004):
           nunca UPDATE; o estado documental é derivado de
           `current_version_no` (corrente `ATTACHED`, anteriores
           `SUPERSEDED`). `version_no` UNIQUE por documento garante
           unicidade fora da serialização esperada.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    lock_competence_row(cur, competence_id)
                    doc = self._lock_document_for_update(
                        cur,
                        competence_id=competence_id,
                        document_id=document_id,
                    )
                    self._assert_active_document(doc)
                    self._assert_snapshot_unlocked(
                        cur, competence_id, doc["snapshot_item_id"]
                    )
                    cur.execute(
                        f"""
                        SELECT version_no, request_hash
                          FROM {_q('document_version')}
                         WHERE document_id = %s
                           AND idempotency_key = %s
                        """,
                        (document_id, idempotency_key),
                    )
                    existing = cur.fetchone()
                    if existing is not None:
                        if existing["request_hash"] != request_hash:
                            raise IdempotencyConflict(
                                "Chave de idempotência já utilizada "
                                "com payload divergente."
                            )
                        return (
                            self.get_document_by_id(
                                competence_id, document_id
                            ),
                            False,
                        )
                    self._assert_revision(doc, expected_revision)
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
                    new_version_no = doc["current_version_no"] + 1
                    cur.execute(
                        f"""
                        INSERT INTO {_q('document_version')}
                            (document_id, version_no, file_id,
                             uploaded_by, idempotency_key, request_hash)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            document_id,
                            new_version_no,
                            file_id,
                            actor,
                            idempotency_key,
                            request_hash,
                        ),
                    )
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_document')}
                           SET current_version_no = %s,
                               revision = revision + 1,
                               updated_at = now()
                         WHERE document_id = %s
                        """,
                        (new_version_no, document_id),
                    )
                    revalidation = self._reopen_item_validation(
                        cur, doc["snapshot_item_id"]
                    )
                    self._audit(
                        cur,
                        entity_type="closing_document",
                        entity_id=document_id,
                        competence_id=competence_id,
                        event_type="VERSION_ADDED",
                        actor=actor,
                        detail={
                            "version_no": new_version_no,
                            "superseded_version_no": doc[
                                "current_version_no"
                            ],
                            "item_revalidation_required": revalidation,
                            "original_name": original_name,
                            "size_bytes": size_bytes,
                            "checksum_sha256": checksum_sha256,
                        },
                    )
        return self.get_document_by_id(competence_id, document_id), True

    def cancel_document(
        self,
        *,
        competence_id: str,
        document_id: str,
        expected_revision: int,
        actor: str,
    ) -> dict[str, Any]:
        """U7 — cancelamento lógico: `CANCELLED != DELETED`.

        Mesma disciplina de OCC do `add_version`: replay ou corrida
        obsoleta aborta com `stale_revision` antes de qualquer efeito —
        eventos nunca são duplicados indevidamente. Arquivos, versões e
        auditoria anteriores permanecem intactos.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    lock_competence_row(cur, competence_id)
                    doc = self._lock_document_for_update(
                        cur,
                        competence_id=competence_id,
                        document_id=document_id,
                    )
                    self._assert_active_document(doc)
                    self._assert_snapshot_unlocked(
                        cur, competence_id, doc["snapshot_item_id"]
                    )
                    self._assert_revision(doc, expected_revision)
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_document')}
                           SET state = 'CANCELLED',
                               revision = revision + 1,
                               updated_at = now()
                         WHERE document_id = %s
                        """,
                        (document_id,),
                    )
                    revalidation = self._reopen_item_validation(
                        cur, doc["snapshot_item_id"]
                    )
                    self._audit(
                        cur,
                        entity_type="closing_document",
                        entity_id=document_id,
                        competence_id=competence_id,
                        event_type="DOCUMENT_CANCELLED",
                        actor=actor,
                        detail={
                            "version_no": doc["current_version_no"],
                            "item_revalidation_required": revalidation,
                        },
                    )
        return self.get_document_by_id(competence_id, document_id)

    def _reopen_item_validation(
        self, cur, snapshot_item_id
    ) -> bool:
        """RQ-P2-05 — mutação da evidência exige nova validação.

        Recomputa o estado do item vinculado na mesma transação: item
        `ACCEPTED` cuja composição mudou (versão nova sem decisão ou
        conjunto alterado) volta a `EXPECTED`. Retorna True quando a
        revalidação foi efetivamente reaberta.
        """
        if snapshot_item_id is None:
            return False
        cur.execute(
            f"""
            SELECT state, validation_scope
              FROM {_q('competence_checklist_item')}
             WHERE snapshot_item_id = %s
             FOR UPDATE
            """,
            (snapshot_item_id,),
        )
        item = cur.fetchone()
        if item is None or item["state"] != "ACCEPTED":
            return False
        new_state = recompute_item_state(
            cur,
            snapshot_item_id=snapshot_item_id,
            validation_scope=item["validation_scope"],
            current_state=item["state"],
        )
        if new_state == item["state"]:
            return False
        cur.execute(
            f"""
            UPDATE {_q('competence_checklist_item')}
               SET state = %s
             WHERE snapshot_item_id = %s
            """,
            (new_state, snapshot_item_id),
        )
        return True

    # -- leituras U6/U8 (SLICE-2) ---------------------------------------------------

    def list_document_versions(
        self, competence_id: str, document_id: str
    ) -> list[dict[str, Any]]:
        """U6 — histórico completo; versões são linhas imutáveis
        (`SUPERSEDED != DELETED` — V004: estado derivado de
        `current_version_no`, nunca reescrito). Sem storage_key."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT v.document_version_id, v.document_id, v.version_no,
                       CASE WHEN v.version_no = d.current_version_no
                            THEN 'ATTACHED' ELSE 'SUPERSEDED'
                       END AS state,
                       v.uploaded_by, v.created_at,
                       f.original_name, f.mime_type, f.size_bytes,
                       f.checksum_sha256
                  FROM {_q('document_version')} v
                  JOIN {_q('document_file')} f
                    ON f.file_id = v.file_id
                  JOIN {_q('closing_document')} d
                    ON d.document_id = v.document_id
                 WHERE d.competence_id = %s AND v.document_id = %s
                 ORDER BY v.version_no DESC
                """,
                (competence_id, document_id),
            )
            return cur.fetchall()

    def list_document_events(
        self,
        competence_id: str,
        document_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """U8 — eventos de auditoria do documento (append-only).

        Somente os eventos documentais do contrato são expostos — o
        filtro impede vazamento de eventos internos de outros casos de
        uso sobre a mesma entidade."""
        clauses = [
            "entity_type = 'closing_document'",
            "entity_id = %s",
            "competence_id = %s",
            "event_type IN (%s, %s, %s, %s, %s, %s, %s)",
        ]
        params: list[Any] = [
            document_id,
            competence_id,
            "DOCUMENT_UPLOADED",
            "DOCUMENT_DOWNLOADED",
            "VERSION_ADDED",
            "DOCUMENT_CANCELLED",
            "EVIDENCE_ACCEPTED",
            "EVIDENCE_REJECTED",
            "DOCUMENT_MESSAGE_POSTED",
        ]
        where = " AND ".join(clauses)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT count(*) AS total
                  FROM {_q('closing_audit_event')}
                 WHERE {where}
                """,
                params,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"""
                SELECT event_id, event_type, actor_subject, detail,
                       created_at
                  FROM {_q('closing_audit_event')}
                 WHERE {where}
                 ORDER BY created_at DESC, event_id
                 LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            items = cur.fetchall()
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    # -- U9 — conversa documental (SLICE-3) ---------------------------------------

    def list_document_messages(
        self,
        competence_id: str,
        document_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Mensagens do documento da competência — ordem cronológica
        ASC (conversa) com `created_at`/`message_id` como desempate
        estável. Escopo duplo (documento+competência) impede leitura
        cruzada mesmo que o caller falhe em validar a associação."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT count(*) AS total
                  FROM {_q('document_message')}
                 WHERE document_id = %s AND competence_id = %s
                """,
                (document_id, competence_id),
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"""
                SELECT message_id, document_id, competence_id,
                       version_no, audience, body, author_subject,
                       author_name, created_at
                  FROM {_q('document_message')}
                 WHERE document_id = %s AND competence_id = %s
                 ORDER BY created_at ASC, message_id ASC
                 LIMIT %s OFFSET %s
                """,
                (document_id, competence_id, limit, offset),
            )
            items = cur.fetchall()
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def find_message_by_idempotency(
        self, document_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        """Registro de idempotência da mensagem (D-U9=A — key nunca é
        reutilizada entre documentos: o unique é por documento)."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT message_id, document_id, competence_id,
                       version_no, audience, body, author_subject,
                       author_name, created_at, request_hash
                  FROM {_q('document_message')}
                 WHERE document_id = %s AND idempotency_key = %s
                """,
                (document_id, idempotency_key),
            )
            return cur.fetchone()

    def create_document_message(
        self,
        *,
        competence_id: str,
        document_id: str,
        version_no: int | None,
        audience: str,
        body: str,
        author_subject: str,
        author_name: str | None,
        idempotency_key: str,
        request_hash: str,
    ) -> tuple[dict[str, Any], bool]:
        """document_message + `DOCUMENT_MESSAGE_POSTED` numa transação
        — mensagem e auditoria são inseparáveis.

        `ON CONFLICT (document_id, idempotency_key) DO NOTHING`:
        corrida perdida aborta a transação — o vencedor é re-lido fora
        e comparado pelo `request_hash` (replay ⇒ existente;
        divergente ⇒ `idempotency_conflict`). Retorna
        ``(mensagem, created)``."""
        inserted = None
        with self._conn() as conn:
            try:
                with conn.transaction():
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('document_message')}
                                (document_id, competence_id, version_no,
                                 audience, body, author_subject,
                                 author_name, idempotency_key,
                                 request_hash)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT (document_id, idempotency_key)
                                DO NOTHING
                            RETURNING message_id
                            """,
                            (
                                document_id,
                                competence_id,
                                version_no,
                                audience,
                                body,
                                author_subject,
                                author_name,
                                idempotency_key,
                                request_hash,
                            ),
                        )
                        inserted = cur.fetchone()
                        if inserted is None:
                            raise _IdempotencyRaceLost()
                        message_id = str(inserted["message_id"])
                        self._audit(
                            cur,
                            entity_type="closing_document",
                            entity_id=document_id,
                            competence_id=competence_id,
                            event_type="DOCUMENT_MESSAGE_POSTED",
                            actor=author_subject,
                            detail={
                                "message_id": message_id,
                                "version_no": version_no,
                            },
                        )
            except _IdempotencyRaceLost:
                pass
        if inserted is not None:
            with self._conn() as conn, conn.cursor(
                row_factory=dict_row
            ) as cur:
                cur.execute(
                    f"""
                    SELECT message_id, document_id, competence_id,
                           version_no, audience, body, author_subject,
                           author_name, created_at
                      FROM {_q('document_message')}
                     WHERE message_id = %s
                    """,
                    (message_id,),
                )
                return cur.fetchone(), True
        winner = self.find_message_by_idempotency(
            document_id, idempotency_key
        )
        if winner is None:
            raise PersistenceUnavailable(
                "Falha ao recuperar mensagem idempotente."
            )
        if winner["request_hash"] != request_hash:
            raise IdempotencyConflict(
                "Chave de idempotência já utilizada com payload "
                "divergente."
            )
        return winner, False

    def list_document_participant_ids(
        self, document_id: str
    ) -> list[str]:
        """Participantes vinculados ao documento (RW01 — Plano 113
        §23.6): autores de mensagens U9 + atores de eventos U8 +
        uploader do documento. É a única prova de vínculo aceita —
        identificador vindo só do frontend nunca basta."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT DISTINCT actor AS participant_id FROM (
                    SELECT author_subject AS actor
                      FROM {_q('document_message')}
                     WHERE document_id = %s
                    UNION
                    SELECT actor_subject AS actor
                      FROM {_q('closing_audit_event')}
                     WHERE entity_type = 'closing_document'
                       AND entity_id = %s
                    UNION
                    SELECT uploaded_by AS actor
                      FROM {_q('closing_document')}
                     WHERE document_id = %s
                ) bound
                WHERE actor IS NOT NULL
                """,
                (document_id, document_id, document_id),
            )
            return [str(row["participant_id"]) for row in cur.fetchall()]

    # -- internals --------------------------------------------------------------

    def _lock_document_for_update(
        self,
        cur,
        *,
        competence_id: str,
        document_id: str,
    ) -> dict[str, Any]:
        """Linha do documento sob lock — escopo da competência do path
        reavaliado na transação (cross-competence = 404)."""
        cur.execute(
            f"""
            SELECT document_id, state, revision, current_version_no,
                   uploaded_by, snapshot_item_id
              FROM {_q('closing_document')}
             WHERE competence_id = %s AND document_id = %s
             FOR UPDATE
            """,
            (competence_id, document_id),
        )
        row = cur.fetchone()
        if row is None:
            raise DocumentNotFound("Documento não encontrado.")
        return row

    @staticmethod
    def _assert_active_document(doc: dict[str, Any]) -> None:
        """Mutações exigem estado `ATTACHED`; `CANCELLED` é terminal."""
        if doc["state"] == "CANCELLED":
            raise DocumentCancelled(
                "Documento cancelado não pode ser alterado."
            )
        if doc["state"] != "ATTACHED":
            raise DocumentNotAttached(
                "Documento não está em estado que permita alteração."
            )

    @staticmethod
    def _assert_revision(
        doc: dict[str, Any], expected_revision: int
    ) -> None:
        if doc["revision"] != expected_revision:
            raise StaleRevision(
                "O documento foi alterado. Atualize e tente novamente."
            )

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
