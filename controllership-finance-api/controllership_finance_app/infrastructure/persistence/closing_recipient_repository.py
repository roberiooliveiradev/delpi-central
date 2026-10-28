"""Adapter PostgreSQL da entrega documental a destinatários externos
(DRE-019 — doc 91 Opção B, Plano 113 §29, doc 112 §54).

Read-model restrito do destinatário (`access.dre` — única capability
DRE desde RW03):

- o vínculo é `closing_review_assignment` role='RECIPIENT' ativo,
  resolvido a `closing_package` (competência + recipient_area);
- a liberação é a versão SUBMITTED mais alta de cada pacote vinculado —
  o snapshot `content.items[].document_version_id` é o conjunto
  documental autorizado (D-DRE-RELEASE-01, alternativa A do gate 018);
- um ator pode ser destinatário de mais de uma área — a visão da
  competência é a UNIÃO dos conjuntos liberados dos pacotes
  vinculados; pacote de outro destinatário nunca entra (sibling = 404);
- o read-model NUNCA retorna `p3_reconciliation`, `p4_pendency_counts`,
  decisões, esclarecimentos ou required_areas do snapshot — projeção
  explícita, nunca o content bruto (boundary DRE).

Nenhuma regra de autorização vive fora do serviço — mas todo método
recebe o `subject` do ator e revalida a membership na query (defesa
em profundidade, fail-closed por construção).
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
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


class ClosingRecipientRepository:
    """Read-model da entrega documental ao destinatário externo."""

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

    # -- vínculo + entrega corrente ------------------------------------

    def list_deliveries(self, subject: str) -> list[dict[str, Any]]:
        """Entregas correntes ao destinatário: pacote com assignment
        RECIPIENT ativo + versão SUBMITTED mais alta (pode haver DRAFT
        mais novo em correção — a entrega anterior continua vigente).

        `document_count` conta itens do snapshot com evidência liberada
        (document_version_id não nulo) — sem materializar o content."""
        with self._conn() as conn, conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                f"""
                SELECT c.period,
                       p.package_id,
                       p.recipient_area,
                       v.package_version_id,
                       v.version_no,
                       v.submitted_at,
                       (
                         SELECT count(*)
                           FROM jsonb_array_elements(
                                v.content -> 'items') item
                          WHERE item ->> 'document_version_id' IS NOT NULL
                       ) AS document_count
                  FROM {_q('closing_review_assignment')} a
                  JOIN {_q('closing_package')} p
                       ON p.package_id = a.package_id
                  JOIN {_q('monthly_competence')} c
                       ON c.competence_id = p.competence_id
                  JOIN LATERAL (
                       SELECT v.package_version_id, v.version_no,
                              v.submitted_at, v.content
                         FROM {_q('closing_package_version')} v
                        WHERE v.package_id = p.package_id
                          AND v.status = 'SUBMITTED'
                        ORDER BY v.version_no DESC
                        LIMIT 1
                  ) v ON true
                 WHERE a.subject = %s
                   AND a.role = 'RECIPIENT'
                   AND a.active
                 ORDER BY c.period DESC, p.recipient_area
                """,
                (subject,),
            )
            return cur.fetchall()

    def bound_packages(
        self, period: str, subject: str
    ) -> list[dict[str, Any]]:
        """Pacotes vinculados ao destinatário na competência do path,
        cada um com sua versão SUBMITTED mais alta (entrega corrente).

        Lista vazia ⇒ sem vínculo OU nada submetido — o serviço mapeia
        para 404/visão vazia conforme o contrato; existência de pacote
        de terceiros nunca vaza."""
        with self._conn() as conn, conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                f"""
                SELECT c.competence_id, c.period,
                       p.package_id, p.recipient_area,
                       v.package_version_id, v.version_no,
                       v.submitted_at, v.content
                  FROM {_q('closing_review_assignment')} a
                  JOIN {_q('closing_package')} p
                       ON p.package_id = a.package_id
                  JOIN {_q('monthly_competence')} c
                       ON c.competence_id = p.competence_id
                  JOIN LATERAL (
                       SELECT v.package_version_id, v.version_no,
                              v.submitted_at, v.content
                         FROM {_q('closing_package_version')} v
                        WHERE v.package_id = p.package_id
                          AND v.status = 'SUBMITTED'
                        ORDER BY v.version_no DESC
                        LIMIT 1
                  ) v ON true
                 WHERE a.subject = %s
                   AND a.role = 'RECIPIENT'
                   AND a.active
                   AND c.period = %s
                 ORDER BY p.recipient_area
                """,
                (subject, period),
            )
            return cur.fetchall()

    # -- projeção documental --------------------------------------------

    @staticmethod
    def _released_version_ids(
        bound_packages: list[dict[str, Any]],
    ) -> dict[str, str]:
        """document_version_id → item_key, sobre o conjunto liberado
        da entrega corrente (união dos pacotes vinculados)."""
        mapping: dict[str, str] = {}
        for package in bound_packages:
            items = (package.get("content") or {}).get("items") or []
            for item in items:
                version_id = item.get("document_version_id")
                if version_id:
                    mapping[str(version_id)] = item.get("item_key")
        return mapping

    def released_documents(
        self, competence_id: str, bound_packages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Projeção documental da entrega corrente — SOMENTE os campos
        da experiência documental (sem p3/p4/decisões/metadados internos).

        Documento CANCELLED não é listado (CANCELLED != DELETED — sai da
        experiência ativa do destinatário, histórico interno preservado).
        `version_no` retornado é o PINNED no snapshot, que pode ser
        SUPERSEDED internamente — para o destinatário ela é a vigente."""
        version_items = self._released_version_ids(bound_packages)
        if not version_items:
            return []
        package_area = {
            str(vid): package["recipient_area"]
            for package in bound_packages
            for vid in [
                i.get("document_version_id")
                for i in (package.get("content") or {}).get("items") or []
            ]
            if vid
        }
        with self._conn() as conn, conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                f"""
                SELECT d.document_id, d.title, d.link_kind,
                       dv.document_version_id, dv.version_no,
                       f.original_name, f.mime_type, f.size_bytes,
                       dv.created_at AS released_at,
                       i.name AS item_name
                  FROM {_q('document_version')} dv
                  JOIN {_q('closing_document')} d
                       ON d.document_id = dv.document_id
                  JOIN {_q('document_file')} f
                       ON f.file_id = dv.file_id
                  LEFT JOIN {_q('competence_checklist_item')} i
                       ON i.competence_id = d.competence_id
                      AND i.snapshot_item_id = d.snapshot_item_id
                 WHERE dv.document_version_id = ANY(%s::uuid[])
                   AND d.competence_id = %s
                   AND d.state = 'ATTACHED'
                 ORDER BY i.name NULLS LAST, f.original_name
                """,
                (list(version_items), competence_id),
            )
            rows = cur.fetchall()
        for row in rows:
            key = str(row["document_version_id"])
            row["item_key"] = version_items.get(key)
            row["recipient_area"] = package_area.get(key)
        return rows

    def released_document(
        self,
        competence_id: str,
        bound_packages: list[dict[str, Any]],
        document_id: str,
    ) -> dict[str, Any] | None:
        """Documento da entrega corrente — `None` se não liberado
        (mesmo resultado de documento inexistente: existência nunca
        vaza fora do vínculo)."""
        released = self.released_documents(competence_id, bound_packages)
        for row in released:
            if str(row["document_id"]) == str(document_id):
                return row
        return None

    def released_versions(
        self, package_ids: list[str], document_id: str
    ) -> list[dict[str, Any]]:
        """Versões autorizadas do documento — todas pinadas em versões
        SUBMITTED dos pacotes vinculados (a v1 entregue continua
        consultável mesmo que v2 tenha substituído a entrega)."""
        if not package_ids:
            return []
        with self._conn() as conn, conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                f"""
                SELECT DISTINCT ON (dv.document_version_id)
                       dv.document_version_id, dv.document_id,
                       dv.version_no,
                       CASE WHEN dv.version_no = d.current_version_no
                            THEN 'ATTACHED' ELSE 'SUPERSEDED'
                       END AS state,
                       f.original_name,
                       f.mime_type, f.size_bytes, dv.created_at
                  FROM {_q('closing_package_version')} v,
                       jsonb_array_elements(v.content -> 'items') item
                  JOIN {_q('document_version')} dv
                       ON dv.document_version_id::text
                          = item ->> 'document_version_id'
                  JOIN {_q('closing_document')} d
                       ON d.document_id = dv.document_id
                  JOIN {_q('document_file')} f
                       ON f.file_id = dv.file_id
                 WHERE v.package_id = ANY(%s::uuid[])
                   AND v.status = 'SUBMITTED'
                   AND dv.document_id = %s
                 ORDER BY dv.document_version_id, v.version_no DESC
                """,
                (package_ids, document_id),
            )
            rows = cur.fetchall()
        rows.sort(key=lambda r: r["version_no"], reverse=True)
        return rows

    def version_file_if_released(
        self,
        competence_id: str,
        package_ids: list[str],
        document_id: str,
        version_no: int,
    ) -> dict[str, Any] | None:
        """Arquivo da versão SOMENTE se o document_version_id estiver
        pinado em alguma versão SUBMITTED dos pacotes vinculados — a
        autorização de download é por membership no conjunto liberado,
        nunca por conhecimento de ids."""
        if not package_ids:
            return None
        with self._conn() as conn, conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                f"""
                SELECT dv.document_version_id, dv.document_id,
                       dv.version_no,
                       f.storage_key, f.original_name, f.mime_type,
                       f.size_bytes, f.checksum_sha256
                  FROM {_q('document_version')} dv
                  JOIN {_q('document_file')} f
                       ON f.file_id = dv.file_id
                 WHERE dv.document_id = %s
                   AND dv.version_no = %s
                   AND EXISTS (
                       SELECT 1
                         FROM {_q('closing_package_version')} v,
                              jsonb_array_elements(
                                  v.content -> 'items') item
                        WHERE v.package_id = ANY(%s::uuid[])
                          AND v.status = 'SUBMITTED'
                          AND item ->> 'document_version_id'
                              = dv.document_version_id::text
                   )
                   AND EXISTS (
                       SELECT 1
                         FROM {_q('closing_document')} d
                        WHERE d.document_id = dv.document_id
                          AND d.competence_id = %s
                   )
                """,
                (
                    document_id,
                    version_no,
                    package_ids,
                    competence_id,
                ),
            )
            return cur.fetchone()
