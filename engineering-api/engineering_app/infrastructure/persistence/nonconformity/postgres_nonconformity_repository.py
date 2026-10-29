"""Adapter Postgres do contexto NC — principal dedicado.

Conecta APENAS via ``ENG_NC_DB_*`` (DSN própria do bounded context).
Jamais usa ``PLUGINS_DB_*`` — a storage compartilhada continua sob a
api-delpi até a aprovação formal do ADR-NC-OWNERSHIP (doc 47 §7).

Proteções:
- ``delete_all_records`` exige ``allow_replace=True`` na construção
  (composição liga isso a ``ENG_NC_IMPORT_REPLACE_ENABLED=true``);
- ``update_record`` aceita ``expected_updated_at`` → optimistic locking;
- ``create_record`` com ``idempotency_key`` deduplica por chave natural.

Semântica SQL espelha o repositório legado (paridade T6).
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Iterator

from engineering_app.domain.nonconformity.errors import (
    NcConcurrencyError,
    NcRepositoryError,
    NcUnsafeOperationError,
    NcValidationError,
)

_DOMAIN_ERRORS = (
    NcRepositoryError,
    NcConcurrencyError,
    NcValidationError,
    NcUnsafeOperationError,
)
from engineering_app.domain.nonconformity.history_diff import (
    build_nc_history_changes,
)
from engineering_app.domain.nonconformity.models import NcActor
from engineering_app.domain.nonconformity.normalize import (
    normalize_problem_tag_labels,
    normalize_products,
)
from engineering_app.domain.nonconformity.sort import resolve_nc_sort

logger = logging.getLogger(__name__)

_STATUS_VALUES = frozenset({"open", "in_progress", "done"})

_SORT_SQL: dict[str, str] = {
    "registered_at": "n.registered_at",
    "occurrence_date": "n.occurrence_date",
    "sale_number": "n.sale_number",
    "lmp_number": "n.lmp_number",
    "customer_name": "n.customer_name",
    "launch_date": "n.launch_date",
    "last_revision_date": "n.last_revision_date",
    "executed_by": "n.executed_by",
    "released_by": "n.released_by",
    "status": "n.status",
    "defect_description": "n.defect_description",
    "problem_tags": (
        "(SELECT COALESCE(string_agg(t.label, ', ' ORDER BY t.label), '')"
        " FROM engineering.lmp_nonconformity_problem_tags npt"
        " JOIN engineering.lmp_problem_tags t ON t.id = npt.tag_id"
        " WHERE npt.nonconformity_id = n.id)"
    ),
    "products": (
        "(SELECT COALESCE(string_agg(p.product_code, ', ' ORDER BY p.product_code), '')"
        " FROM engineering.lmp_nonconformity_products p"
        " WHERE p.nonconformity_id = n.id)"
    ),
}

_NC_SELECT = """
    SELECT n.id,
           n.registered_at,
           n.occurrence_date,
           n.sale_number,
           n.lmp_number,
           n.customer_name,
           n.launch_date,
           n.last_revision_date,
           n.executed_by,
           n.released_by,
           n.status,
           n.defect_description,
           n.corrective_actions,
           n.technical_opinion,
           n.created_by,
           n.updated_by,
           n.created_at,
           n.updated_at
      FROM engineering.lmp_nonconformities n
"""


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def _blank(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _order_sql(sort_by: str | None, sort_dir: str | None) -> tuple[str, str, str]:
    key, direction = resolve_nc_sort(sort_by, sort_dir)
    sql_dir = "ASC" if direction == "asc" else "DESC"
    nulls = "NULLS LAST" if direction == "asc" else "NULLS FIRST"
    return (
        key,
        direction,
        f"{_SORT_SQL[key]} {sql_dir} {nulls}, n.created_at DESC, n.id DESC",
    )


class PostgresNonconformityRepository:
    """Implementa ``NonconformityRepository`` sobre psycopg3."""

    def __init__(
        self,
        dsn: str,
        *,
        allow_replace: bool = False,
        connect_timeout: int = 5,
    ) -> None:
        if not dsn or not dsn.strip():
            raise NcRepositoryError("DSN do repositório NC ausente.")
        self._dsn = dsn.strip()
        self._allow_replace = allow_replace
        self._connect_timeout = connect_timeout

    @contextmanager
    def _db(self) -> Iterator[Any]:
        import psycopg
        from psycopg.rows import dict_row

        conn = None
        try:
            conn = psycopg.connect(
                self._dsn,
                row_factory=dict_row,
                connect_timeout=self._connect_timeout,
            )
            yield conn
        except _DOMAIN_ERRORS:
            if conn is not None:
                conn.rollback()
            raise
        except Exception as exc:
            if conn is not None:
                conn.rollback()
            logger.exception("nc_postgres_operation_failed")
            raise NcRepositoryError("Falha na persistência NC.") from exc
        finally:
            if conn is not None:
                conn.close()

    # ---------------------------------------------------------- reads

    def list_records(
        self,
        *,
        status: str | None = None,
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        product_code: str | None = None,
        problem_tag: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        filters = ["TRUE"]
        params: list[Any] = []

        if status:
            filters.append("n.status = %s")
            params.append(status)
        if sale_number:
            filters.append("n.sale_number ILIKE %s")
            params.append(f"%{sale_number.strip()}%")
        if lmp_number:
            filters.append("n.lmp_number ILIKE %s")
            params.append(f"%{lmp_number.strip()}%")
        if customer_name:
            filters.append("n.customer_name ILIKE %s")
            params.append(f"%{customer_name.strip()}%")
        if product_code:
            filters.append(
                """
                EXISTS (
                    SELECT 1
                      FROM engineering.lmp_nonconformity_products p
                     WHERE p.nonconformity_id = n.id
                       AND p.product_code ILIKE %s
                )
                """
            )
            params.append(f"%{product_code.strip()}%")
        if problem_tag:
            filters.append(
                """
                EXISTS (
                    SELECT 1
                      FROM engineering.lmp_nonconformity_problem_tags npt
                      JOIN engineering.lmp_problem_tags t ON t.id = npt.tag_id
                     WHERE npt.nonconformity_id = n.id
                       AND t.label ILIKE %s
                )
                """
            )
            params.append(f"%{problem_tag.strip()}%")
        if date_start:
            filters.append("n.occurrence_date >= %s::date")
            params.append(date_start)
        if date_end:
            filters.append("n.occurrence_date <= %s::date")
            params.append(date_end)

        where_sql = " AND ".join(filters)
        page = max(1, int(page))
        page_size = max(1, min(int(page_size), 200))
        offset = (page - 1) * page_size
        key, direction, order_sql = _order_sql(sort_by, sort_dir)

        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT COUNT(*) AS total
                      FROM engineering.lmp_nonconformities n
                     WHERE {where_sql}
                    """,
                    tuple(params),
                )
                total = int(cur.fetchone()["total"])

                cur.execute(
                    f"""
                    {_NC_SELECT}
                     WHERE {where_sql}
                     ORDER BY {order_sql}
                     LIMIT %s OFFSET %s
                    """,
                    tuple([*params, page_size, offset]),
                )
                rows = [dict(r) for r in cur.fetchall()]

        record_ids = [str(row["id"]) for row in rows]
        tags_by_id = self._list_problem_tags_for_ids(record_ids)
        items = [
            self._to_payload(
                row,
                include_products=True,
                problem_tags=tags_by_id.get(str(row["id"]), []),
            )
            for row in rows
        ]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "sort_by": key,
            "sort_dir": direction,
        }

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"{_NC_SELECT} WHERE n.id = %s", (record_id,))
                row = cur.fetchone()
        if row is None:
            return None
        row = dict(row)
        return self._to_payload(
            row,
            include_products=True,
            problem_tags=self._list_problem_tags(record_id),
        )

    def export_records(self) -> list[dict[str, Any]]:
        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    {_NC_SELECT}
                     ORDER BY n.registered_at ASC, n.id ASC
                    """,
                    (),
                )
                rows = [dict(r) for r in cur.fetchall()]
        if not rows:
            return []
        record_ids = [str(row["id"]) for row in rows]
        tags_by_id = self._list_problem_tags_for_ids(record_ids)
        return [
            self._to_payload(
                row,
                include_products=True,
                problem_tags=tags_by_id.get(str(row["id"]), []),
            )
            for row in rows
        ]

    def list_history(self, record_id: str) -> list[dict[str, Any]] | None:
        if self.get_record(record_id) is None:
            return None
        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id,
                           nonconformity_id,
                           event_type,
                           changes,
                           actor_user_id,
                           actor_email,
                           actor_name,
                           created_at
                      FROM engineering.lmp_nonconformity_history
                     WHERE nonconformity_id = %s
                     ORDER BY created_at DESC
                     LIMIT 200
                    """,
                    (record_id,),
                )
                rows = [dict(r) for r in cur.fetchall()]
        return [self._history_to_payload(row) for row in rows]

    def list_problem_tag_catalog(self) -> list[dict[str, Any]]:
        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.id,
                           t.label,
                           COUNT(npt.nonconformity_id)::int AS usage_count
                      FROM engineering.lmp_problem_tags t
                      LEFT JOIN engineering.lmp_nonconformity_problem_tags npt
                             ON npt.tag_id = t.id
                     GROUP BY t.id, t.label
                     ORDER BY t.label ASC
                    """,
                    (),
                )
                rows = [dict(r) for r in cur.fetchall()]
        return [
            {
                "id": str(row["id"]),
                "label": str(row["label"]),
                "usage_count": int(row.get("usage_count") or 0),
            }
            for row in rows
        ]

    def list_occurrence_dates(self) -> list[date]:
        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT occurrence_date
                      FROM engineering.lmp_nonconformities
                     ORDER BY occurrence_date ASC
                    """,
                    (),
                )
                rows = [dict(r) for r in cur.fetchall()]
        out: list[date] = []
        for row in rows:
            value = row.get("occurrence_date")
            if isinstance(value, date):
                out.append(value)
            elif value is not None:
                try:
                    out.append(date.fromisoformat(str(value)[:10]))
                except ValueError:
                    continue
        return out

    def find_import_duplicate(
        self,
        *,
        sale_number: str | None,
        defect_description: str | None,
        problem_tags: list[str] | None,
    ) -> dict[str, Any] | None:
        sale = (sale_number or "").strip()
        defect = (defect_description or "").strip()
        wanted = {
            str(tag).strip().casefold()
            for tag in (problem_tags or [])
            if str(tag).strip()
        }
        if not sale and not defect and not wanted:
            return None

        filters: list[str] = []
        params: list[Any] = []
        if sale:
            filters.append("COALESCE(n.sale_number, '') = %s")
            params.append(sale)
        else:
            filters.append("COALESCE(n.sale_number, '') = ''")
        if defect:
            filters.append("COALESCE(n.defect_description, '') = %s")
            params.append(defect)
        else:
            filters.append("COALESCE(n.defect_description, '') = ''")

        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    {_NC_SELECT}
                     WHERE {" AND ".join(filters)}
                     ORDER BY n.registered_at DESC
                     LIMIT 20
                    """,
                    tuple(params),
                )
                rows = [dict(r) for r in cur.fetchall()]
        for row in rows:
            record_id = str(row["id"])
            existing = {
                tag.casefold() for tag in self._list_problem_tags(record_id)
            }
            if existing == wanted:
                return self._to_payload(
                    row,
                    include_products=True,
                    problem_tags=self._list_problem_tags(record_id),
                )
        return None

    # --------------------------------------------------------- writes

    def create_record(
        self,
        *,
        status: str = "open",
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        occurrence_date: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        problem_tags: list[str] | None = None,
        registered_at: str | None = None,
        actor: NcActor,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        status_norm = (status or "open").strip().lower()
        if status_norm not in _STATUS_VALUES:
            raise NcValidationError(f"Status inválido: {status}")

        if idempotency_key:
            duplicate = self.find_import_duplicate(
                sale_number=sale_number,
                defect_description=defect_description,
                problem_tags=problem_tags,
            )
            if duplicate is not None:
                return duplicate

        lines = normalize_products(products)
        tags = normalize_problem_tag_labels(problem_tags)
        sale = _blank(sale_number)
        lmp = _blank(lmp_number)
        customer = _blank(customer_name)
        occurred = _blank(occurrence_date)
        launch = _blank(launch_date)
        revision = _blank(last_revision_date)
        executed = _blank(executed_by)
        released = _blank(released_by)
        defect = _blank(defect_description)
        corrective = _blank(corrective_actions)
        opinion = _blank(technical_opinion)
        registered = _blank(registered_at)

        with self._db() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO engineering.lmp_nonconformities (
                            registered_at, occurrence_date, sale_number, lmp_number,
                            customer_name, launch_date, last_revision_date,
                            executed_by, released_by, status,
                            defect_description, corrective_actions, technical_opinion,
                            created_by, updated_by
                        ) VALUES (
                            COALESCE(%s::timestamptz, NOW()),
                            COALESCE(%s::date, CURRENT_DATE),
                            %s, %s, %s, %s::date, %s::date,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s
                        )
                        RETURNING id
                        """,
                        (
                            registered,
                            occurred,
                            sale,
                            lmp,
                            customer,
                            launch,
                            revision,
                            executed,
                            released,
                            status_norm,
                            defect,
                            corrective,
                            opinion,
                            actor.label,
                            actor.label,
                        ),
                    )
                    record_id = str(cur.fetchone()["id"])
                    self._replace_products(cur, record_id, lines)
                    self._replace_problem_tags(
                        cur, record_id, tags, created_by=actor.label
                    )
                    after = _snapshot(
                        status=status_norm,
                        sale_number=sale,
                        lmp_number=lmp,
                        customer_name=customer,
                        occurrence_date=occurred,
                        launch_date=launch,
                        last_revision_date=revision,
                        executed_by=executed,
                        released_by=released,
                        defect_description=defect,
                        corrective_actions=corrective,
                        technical_opinion=opinion,
                        products=lines,
                        problem_tags=tags,
                    )
                    self._append_history(
                        cur,
                        record_id,
                        event_type="created",
                        changes=build_nc_history_changes(None, after),
                        actor=actor,
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        created = self.get_record(record_id)
        if created is None:
            raise NcRepositoryError("NC criada mas não encontrada após insert.")
        return created

    def update_record(
        self,
        *,
        record_id: str,
        status: str,
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        occurrence_date: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        problem_tags: list[str] | None = None,
        registered_at: str | None = None,
        actor: NcActor,
        expected_updated_at: str | None = None,
    ) -> dict[str, Any] | None:
        del registered_at  # update nunca altera o timestamp de registro
        before = self.get_record(record_id)
        if before is None:
            return None

        status_norm = (status or "").strip().lower()
        if status_norm not in _STATUS_VALUES:
            raise NcValidationError(f"Status inválido: {status}")
        occurred = _blank(occurrence_date)
        if occurred is None:
            raise NcValidationError("occurrence_date é obrigatória.")

        lines = normalize_products(products)
        tags = normalize_problem_tag_labels(problem_tags)
        sale = _blank(sale_number)
        lmp = _blank(lmp_number)
        customer = _blank(customer_name)
        launch = _blank(launch_date)
        revision = _blank(last_revision_date)
        executed = _blank(executed_by)
        released = _blank(released_by)
        defect = _blank(defect_description)
        corrective = _blank(corrective_actions)
        opinion = _blank(technical_opinion)

        with self._db() as conn:
            try:
                with conn.cursor() as cur:
                    if expected_updated_at is not None:
                        cur.execute(
                            """
                            UPDATE engineering.lmp_nonconformities
                               SET sale_number = %s,
                                   lmp_number = %s,
                                   customer_name = %s,
                                   occurrence_date = %s::date,
                                   launch_date = %s::date,
                                   last_revision_date = %s::date,
                                   executed_by = %s,
                                   released_by = %s,
                                   status = %s,
                                   defect_description = %s,
                                   corrective_actions = %s,
                                   technical_opinion = %s,
                                   updated_by = %s,
                                   updated_at = NOW()
                             WHERE id = %s AND updated_at = %s::timestamptz
                            """,
                            (
                                sale, lmp, customer, occurred, launch,
                                revision, executed, released, status_norm,
                                defect, corrective, opinion,
                                actor.label, record_id, expected_updated_at,
                            ),
                        )
                        if cur.rowcount == 0:
                            raise NcConcurrencyError(
                                "Registro alterado por outro processo "
                                "(updated_at divergente)."
                            )
                    else:
                        cur.execute(
                            """
                            UPDATE engineering.lmp_nonconformities
                               SET sale_number = %s,
                                   lmp_number = %s,
                                   customer_name = %s,
                                   occurrence_date = %s::date,
                                   launch_date = %s::date,
                                   last_revision_date = %s::date,
                                   executed_by = %s,
                                   released_by = %s,
                                   status = %s,
                                   defect_description = %s,
                                   corrective_actions = %s,
                                   technical_opinion = %s,
                                   updated_by = %s,
                                   updated_at = NOW()
                             WHERE id = %s
                            """,
                            (
                                sale, lmp, customer, occurred, launch,
                                revision, executed, released, status_norm,
                                defect, corrective, opinion,
                                actor.label, record_id,
                            ),
                        )
                    cur.execute(
                        """
                        DELETE FROM engineering.lmp_nonconformity_products
                         WHERE nonconformity_id = %s
                        """,
                        (record_id,),
                    )
                    self._replace_products(cur, record_id, lines)
                    self._replace_problem_tags(
                        cur, record_id, tags, created_by=actor.label
                    )
                    after = _snapshot(
                        status=status_norm,
                        sale_number=sale,
                        lmp_number=lmp,
                        customer_name=customer,
                        occurrence_date=occurred,
                        launch_date=launch,
                        last_revision_date=revision,
                        executed_by=executed,
                        released_by=released,
                        defect_description=defect,
                        corrective_actions=corrective,
                        technical_opinion=opinion,
                        products=lines,
                        problem_tags=tags,
                    )
                    changes = build_nc_history_changes(before, after)
                    if changes.get("fields"):
                        self._append_history(
                            cur,
                            record_id,
                            event_type="updated",
                            changes=changes,
                            actor=actor,
                        )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        return self.get_record(record_id)

    def delete_record(self, record_id: str) -> bool:
        """Exclui a NC; libera CASCADE do histórico via GUC (V008)."""
        with self._db() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT set_config('app.allow_lmp_nc_history_delete', 'true', true)"
                    )
                    cur.execute(
                        """
                        DELETE FROM engineering.lmp_nonconformities
                         WHERE id = %s
                     RETURNING id
                        """,
                        (record_id,),
                    )
                    row = cur.fetchone()
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return row is not None

    def delete_all_records(self) -> int:
        """Remove todas as NCs (substituição total na importação)."""
        if not self._allow_replace:
            raise NcUnsafeOperationError(
                "Substituição total de acervo bloqueada: "
                "ENG_NC_IMPORT_REPLACE_ENABLED não habilitado neste ambiente."
            )
        with self._db() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT set_config('app.allow_lmp_nc_history_delete', 'true', true)"
                    )
                    cur.execute(
                        """
                        DELETE FROM engineering.lmp_nonconformities
                     RETURNING id
                        """
                    )
                    rows = cur.fetchall()
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return len(rows or [])

    # -------------------------------------------------------- internal

    def _append_history(
        self,
        cursor: Any,
        record_id: str,
        *,
        event_type: str,
        changes: dict[str, Any],
        actor: NcActor,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO engineering.lmp_nonconformity_history (
                nonconformity_id, event_type, changes,
                actor_user_id, actor_email, actor_name
            ) VALUES (%s, %s, %s::jsonb, %s, %s, %s)
            """,
            (
                record_id,
                event_type,
                json.dumps(changes or {}, ensure_ascii=False),
                (actor.user_id or "unknown")[:100],
                actor.email,
                actor.name,
            ),
        )

    def _history_to_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        raw_changes = row.get("changes")
        if isinstance(raw_changes, str):
            try:
                changes = json.loads(raw_changes)
            except json.JSONDecodeError:
                changes = {"fields": []}
        elif isinstance(raw_changes, dict):
            changes = raw_changes
        else:
            changes = {"fields": []}
        return {
            "id": str(row["id"]),
            "nonconformity_id": str(row["nonconformity_id"]),
            "event_type": str(row["event_type"]),
            "changes": changes,
            "actor_user_id": str(row.get("actor_user_id") or ""),
            "actor_email": row.get("actor_email"),
            "actor_name": row.get("actor_name"),
            "created_at": _iso(row.get("created_at")),
        }

    @staticmethod
    def _replace_products(
        cursor: Any, record_id: str, lines: list[dict[str, str]]
    ) -> None:
        if not lines:
            return
        cursor.executemany(
            """
            INSERT INTO engineering.lmp_nonconformity_products (
                nonconformity_id, product_code, product_description
            ) VALUES (%s, %s, %s)
            """,
            [
                (
                    record_id,
                    line["product_code"],
                    _blank(line.get("product_description")),
                )
                for line in lines
            ],
        )

    def _replace_problem_tags(
        self,
        cursor: Any,
        record_id: str,
        labels: list[str],
        *,
        created_by: str | None,
    ) -> None:
        cursor.execute(
            """
            DELETE FROM engineering.lmp_nonconformity_problem_tags
             WHERE nonconformity_id = %s
            """,
            (record_id,),
        )
        if not labels:
            return
        tag_ids = self._ensure_problem_tag_ids(
            cursor, labels, created_by=created_by
        )
        cursor.executemany(
            """
            INSERT INTO engineering.lmp_nonconformity_problem_tags (
                nonconformity_id, tag_id
            ) VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            [(record_id, tag_id) for tag_id in tag_ids],
        )

    @staticmethod
    def _ensure_problem_tag_ids(
        cursor: Any,
        labels: list[str],
        *,
        created_by: str | None,
    ) -> list[str]:
        ids: list[str] = []
        for label in labels:
            cursor.execute(
                """
                SELECT id
                  FROM engineering.lmp_problem_tags
                 WHERE LOWER(TRIM(label)) = LOWER(TRIM(%s))
                 LIMIT 1
                """,
                (label,),
            )
            existing = cursor.fetchone()
            if existing is not None:
                ids.append(str(existing["id"]))
                continue
            cursor.execute(
                """
                INSERT INTO engineering.lmp_problem_tags (label, created_by)
                VALUES (%s, %s)
                RETURNING id
                """,
                (label, created_by),
            )
            inserted = cursor.fetchone()
            if inserted is None:
                raise NcRepositoryError(
                    f"Falha ao criar tag de problema: {label}"
                )
            ids.append(str(inserted["id"]))
        return ids

    def _list_products(self, record_id: str) -> list[dict[str, Any]]:
        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT product_code, product_description
                      FROM engineering.lmp_nonconformity_products
                     WHERE nonconformity_id = %s
                     ORDER BY product_code ASC
                    """,
                    (record_id,),
                )
                rows = [dict(r) for r in cur.fetchall()]
        return [
            {
                "product_code": str(r["product_code"]),
                "product_description": r.get("product_description"),
            }
            for r in rows
        ]

    def _list_problem_tags(self, record_id: str) -> list[str]:
        return self._list_problem_tags_for_ids([record_id]).get(record_id, [])

    def _list_problem_tags_for_ids(
        self, record_ids: list[str]
    ) -> dict[str, list[str]]:
        if not record_ids:
            return {}
        with self._db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT npt.nonconformity_id::text AS nonconformity_id,
                           t.label
                      FROM engineering.lmp_nonconformity_problem_tags npt
                      JOIN engineering.lmp_problem_tags t ON t.id = npt.tag_id
                     WHERE npt.nonconformity_id = ANY(%s::uuid[])
                     ORDER BY t.label ASC
                    """,
                    (record_ids,),
                )
                rows = [dict(r) for r in cur.fetchall()]
        out: dict[str, list[str]] = {rid: [] for rid in record_ids}
        for row in rows:
            rid = str(row["nonconformity_id"])
            out.setdefault(rid, []).append(str(row["label"]))
        return out

    def _to_payload(
        self,
        row: dict[str, Any],
        *,
        include_products: bool = False,
        problem_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        record_id = str(row["id"])
        payload: dict[str, Any] = {
            "id": record_id,
            "registered_at": _iso(row.get("registered_at")),
            "occurrence_date": _iso(row.get("occurrence_date")),
            "sale_number": row.get("sale_number"),
            "lmp_number": row.get("lmp_number"),
            "customer_name": row.get("customer_name"),
            "launch_date": _iso(row.get("launch_date")),
            "last_revision_date": _iso(row.get("last_revision_date")),
            "executed_by": row.get("executed_by"),
            "released_by": row.get("released_by"),
            "status": row.get("status"),
            "defect_description": row.get("defect_description"),
            "problem_tags": list(problem_tags or []),
            "corrective_actions": row.get("corrective_actions"),
            "technical_opinion": row.get("technical_opinion"),
            "created_by": row.get("created_by"),
            "updated_by": row.get("updated_by"),
            "created_at": _iso(row.get("created_at")),
            "updated_at": _iso(row.get("updated_at")),
        }
        if include_products:
            products = self._list_products(record_id)
            payload["products"] = products
            payload["product_codes"] = [p["product_code"] for p in products]
        return payload


def _snapshot(
    *,
    status: str,
    sale_number: str | None,
    lmp_number: str | None,
    customer_name: str | None,
    occurrence_date: str | None,
    launch_date: str | None,
    last_revision_date: str | None,
    executed_by: str | None,
    released_by: str | None,
    defect_description: str | None,
    corrective_actions: str | None,
    technical_opinion: str | None,
    products: list[dict[str, str]],
    problem_tags: list[str],
) -> dict[str, Any]:
    return {
        "status": status,
        "sale_number": sale_number,
        "lmp_number": lmp_number,
        "customer_name": customer_name,
        "occurrence_date": occurrence_date,
        "launch_date": launch_date,
        "last_revision_date": last_revision_date,
        "executed_by": executed_by,
        "released_by": released_by,
        "defect_description": defect_description,
        "corrective_actions": corrective_actions,
        "technical_opinion": technical_opinion,
        "products": list(products),
        "problem_tags": list(problem_tags),
    }
