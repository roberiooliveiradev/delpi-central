"""Catálogos governados P6 (E01/E05/E06/T02/P5-H/T05-binding).

Modelo configurável aprovado (doc 17/105): códigos imutáveis, edição via
`revision` otimista, desativação prospectiva (nunca delete), auditoria
append-only em `closing_audit_event`. Semântica de seed não é inventada
aqui — catálogo vazio produz fallback explícito nos consumidores.
"""

from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    CatalogEntryNotFound,
    ChecklistDomainError,
    InvalidCatalogEntry,
    PersistenceUnavailable,
    StaleRevision,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


CATALOG_KEYS = (
    "BANK_ACCOUNT",
    "REJECTION_REASON",
    "ATTACHMENT_ROLE",
    "NOTIFICATION_TARGET",
    "PACKAGE_REQUIRED_AREA",
    "REVIEW_ELIGIBILITY",
)


class ClosingCatalogRepository:
    """CRUD governado de catálogos P6 — administração por `manage`."""

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

    def _audit(
        self,
        cur,
        *,
        entity_type: str,
        entity_id: str,
        event_type: str,
        actor: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        cur.execute(
            f"""
            INSERT INTO {_q('closing_audit_event')}
                (entity_type, entity_id, competence_id, event_type,
                 actor_subject, detail)
            VALUES (%s, %s, NULL, %s, %s, %s::jsonb)
            """,
            (
                entity_type,
                entity_id,
                event_type,
                actor,
                json.dumps(detail or {}),
            ),
        )

    # -- leitura ------------------------------------------------------------

    def list_entries(
        self,
        catalog_key: str | None = None,
        *,
        include_inactive: bool = True,
    ) -> list[dict[str, Any]]:
        if catalog_key is not None and catalog_key not in CATALOG_KEYS:
            raise InvalidCatalogEntry(
                f"catalog_key deve ser um de {list(CATALOG_KEYS)}."
            )
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            clauses: list[str] = []
            params: list[Any] = []
            if catalog_key is not None:
                clauses.append("catalog_key = %s")
                params.append(catalog_key)
            if not include_inactive:
                clauses.append("active")
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            cur.execute(
                f"""
                SELECT entry_id, catalog_key, code, label, attributes,
                       effective_from_period, active, revision,
                       created_by, created_at, updated_by, updated_at,
                       deactivated_by, deactivated_at
                  FROM {_q('closing_catalog_entry')}{where}
                 ORDER BY catalog_key, code
                """,
                params,
            )
            return cur.fetchall()

    def active_entries(self, catalog_key: str) -> list[dict[str, Any]]:
        """Visão do consumidor — somente entradas ativas."""
        return self.list_entries(catalog_key, include_inactive=False)

    # -- mutações governadas --------------------------------------------------

    def create_entry(
        self,
        catalog_key: str,
        *,
        code: str,
        label: str,
        attributes: dict[str, Any] | None = None,
        effective_from_period: str | None = None,
        actor: str,
    ) -> dict[str, Any]:
        if catalog_key not in CATALOG_KEYS:
            raise InvalidCatalogEntry(
                f"catalog_key deve ser um de {list(CATALOG_KEYS)}."
            )
        code = (code or "").strip()
        label = (label or "").strip()
        if not code or not label:
            raise InvalidCatalogEntry("code e label são obrigatórios.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    try:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('closing_catalog_entry')}
                                (catalog_key, code, label, attributes,
                                 effective_from_period, created_by)
                            VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                            RETURNING entry_id, catalog_key, code, label,
                                      attributes, effective_from_period,
                                      active, revision, created_by,
                                      created_at
                            """,
                            (
                                catalog_key,
                                code,
                                label,
                                json.dumps(attributes or {}),
                                effective_from_period,
                                actor,
                            ),
                        )
                    except psycopg.errors.UniqueViolation as exc:
                        raise InvalidCatalogEntry(
                            f"Entrada {catalog_key}/{code} já existe."
                        ) from exc
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_catalog_entry",
                        entity_id=str(row["entry_id"]),
                        event_type="CATALOG_ENTRY_CREATED",
                        actor=actor,
                        detail={
                            "catalog_key": catalog_key,
                            "code": code,
                            "label": label,
                            "attributes": attributes or {},
                            "effective_from_period": effective_from_period,
                        },
                    )
                    return row

    def update_entry(
        self,
        catalog_key: str,
        code: str,
        *,
        label: str | None = None,
        attributes: dict[str, Any] | None = None,
        expected_revision: int,
        actor: str,
    ) -> dict[str, Any]:
        """Edição prospectiva com OCC; `code`/`catalog_key` imutáveis."""
        sets: list[str] = ["revision = revision + 1",
                           "updated_by = %s", "updated_at = now()"]
        params: list[Any] = [actor]
        if label is not None:
            sets.append("label = %s")
            params.append(label)
        if attributes is not None:
            sets.append("attributes = %s::jsonb")
            params.append(json.dumps(attributes))
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_catalog_entry')}
                           SET {", ".join(sets)}
                         WHERE catalog_key = %s AND code = %s
                           AND revision = %s AND active
                        RETURNING entry_id, catalog_key, code, label,
                                  attributes, effective_from_period,
                                  active, revision
                        """,
                        (*params, catalog_key, code, expected_revision),
                    )
                    row = cur.fetchone()
                    if row is None:
                        cur.execute(
                            f"""
                            SELECT revision, active
                              FROM {_q('closing_catalog_entry')}
                             WHERE catalog_key = %s AND code = %s
                            """,
                            (catalog_key, code),
                        )
                        current = cur.fetchone()
                        if current is None or not current["active"]:
                            raise CatalogEntryNotFound(
                                f"Entrada {catalog_key}/{code} não "
                                "encontrada."
                            )
                        raise StaleRevision(
                            "Revisão desatualizada; recarregue a entrada."
                        )
                    self._audit(
                        cur,
                        entity_type="closing_catalog_entry",
                        entity_id=str(row["entry_id"]),
                        event_type="CATALOG_ENTRY_UPDATED",
                        actor=actor,
                        detail={
                            "catalog_key": catalog_key,
                            "code": code,
                            "label": label,
                            "attributes": attributes,
                        },
                    )
                    return row

    def deactivate_entry(
        self,
        catalog_key: str,
        code: str,
        *,
        expected_revision: int,
        actor: str,
    ) -> dict[str, Any]:
        """Desativação prospectiva — histórico permanece referenciável."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_catalog_entry')}
                           SET active = false,
                               deactivated_by = %s,
                               deactivated_at = now(),
                               revision = revision + 1
                         WHERE catalog_key = %s AND code = %s
                           AND revision = %s AND active
                        RETURNING entry_id, catalog_key, code, active,
                                  revision
                        """,
                        (actor, catalog_key, code, expected_revision),
                    )
                    row = cur.fetchone()
                    if row is None:
                        cur.execute(
                            f"""
                            SELECT revision, active
                              FROM {_q('closing_catalog_entry')}
                             WHERE catalog_key = %s AND code = %s
                            """,
                            (catalog_key, code),
                        )
                        current = cur.fetchone()
                        if current is None or not current["active"]:
                            raise CatalogEntryNotFound(
                                f"Entrada {catalog_key}/{code} não "
                                "encontrada."
                            )
                        raise StaleRevision(
                            "Revisão desatualizada; recarregue a entrada."
                        )
                    self._audit(
                        cur,
                        entity_type="closing_catalog_entry",
                        entity_id=str(row["entry_id"]),
                        event_type="CATALOG_ENTRY_DEACTIVATED",
                        actor=actor,
                        detail={"catalog_key": catalog_key, "code": code},
                    )
                    return row

    def reactivate_entry(
        self,
        catalog_key: str,
        code: str,
        *,
        actor: str,
    ) -> dict[str, Any]:
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_catalog_entry')}
                           SET active = true,
                               deactivated_by = NULL,
                               deactivated_at = NULL,
                               revision = revision + 1
                         WHERE catalog_key = %s AND code = %s
                           AND NOT active
                        RETURNING entry_id, catalog_key, code, active,
                                  revision
                        """,
                        (catalog_key, code),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise CatalogEntryNotFound(
                            f"Entrada {catalog_key}/{code} não encontrada "
                            "ou já ativa."
                        )
                    self._audit(
                        cur,
                        entity_type="closing_catalog_entry",
                        entity_id=str(row["entry_id"]),
                        event_type="CATALOG_ENTRY_REACTIVATED",
                        actor=actor,
                        detail={"catalog_key": catalog_key, "code": code},
                    )
                    return row

    # -- consumidores ---------------------------------------------------------

    def required_areas_for(self, package_type: str) -> list[str]:
        """P5-H: áreas obrigatórias versionadas por tipo de pacote.

        Retorna `[]` quando o catálogo não tem entrada para o tipo —
        o consumidor aplica o fallback monoárea explícito (doc 105);
        catálogo vazio nunca satisfaz obrigação silenciosamente.
        """
        entries = self.active_entries("PACKAGE_REQUIRED_AREA")
        areas = {
            (e["attributes"] or {}).get("required_area", "").strip()
            for e in entries
            if (e["attributes"] or {}).get("package_type") == package_type
        }
        areas.discard("")
        return sorted(areas)

    def eligibility_groups_for(self, area: str) -> set[str]:
        """T05-binding: grupos Core elegíveis configurados por área.

        `set()` vazio = sem binding configurado → consumidor decide o
        modo (assignment-only + flag de auditoria DECISION_REQUIRED).
        """
        entries = self.active_entries("REVIEW_ELIGIBILITY")
        return {
            (e["attributes"] or {}).get("core_group", "").strip()
            for e in entries
            if (e["attributes"] or {}).get("area") == area
            and (e["attributes"] or {}).get("core_group", "").strip()
        }
