"""Persistência PostgreSQL dos relatórios metalográficos (schema engineering)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from psycopg.errors import UniqueViolation
from psycopg.types.json import Json

from app.domain.engineering.metallographic_report import (
    BUSINESS_TIMEZONE,
    MEASUREMENT_KEYS,
    SAMPLE_FIELDS,
    SORT_VALUES,
    IdempotencyConflictError,
    ReportNotFoundError,
    ReportVersionConflictError,
    empty_measurements,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

_SORT_SQL = {
    "created_at_desc": "r.created_at DESC, r.id DESC",
    "created_at_asc": "r.created_at ASC, r.id ASC",
    "report_date_desc": "r.report_date DESC NULLS LAST, r.id DESC",
    "report_number_asc": "r.report_number ASC, r.id ASC",
}
_TEXT_COLUMNS = {
    "report_number": "r.report_number",
    **{field: f"r.{field}" for field in SAMPLE_FIELDS},
}


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _measurements(raw: Any) -> dict[str, Any]:
    base = empty_measurements()
    if isinstance(raw, dict):
        for key in MEASUREMENT_KEYS:
            pair = raw.get(key) or {}
            if isinstance(pair, dict):
                base[key] = {
                    "criterion": pair.get("criterion"),
                    "measured": pair.get("measured"),
                }
    return base


def _image_flag(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {"present": False, "content_type": None, "sha256": None}
    return {
        "present": True,
        "content_type": row.get("content_type"),
        "sha256": row.get("sha256"),
    }


def _public(row: dict[str, Any], images: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "report_number": row["report_number"],
        "report_date": _iso(row.get("report_date")),
        "revision": row["revision"],
        "sample": {field: row.get(field) for field in SAMPLE_FIELDS},
        "measurements": _measurements(row.get("measurements")),
        "conclusion": {
            "result": row.get("conclusion_result"),
            "notes": row.get("conclusion_notes"),
        },
        "analyst": {
            "name": row.get("analyst_name"),
            "user_id": row.get("analyst_user_id"),
        },
        "images": {
            "original": _image_flag(images.get("original")),
            "measured": _image_flag(images.get("measured")),
        },
        "status": row["status"],
        "version": int(row["version"]),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "created_by": row.get("created_by"),
        "updated_by": row.get("updated_by"),
    }


class PostgresMetallographicReportRepository(PluginBaseRepository):
    def create_report(
        self,
        *,
        actor: str,
        payload: dict[str, Any],
        idempotency_key: str,
        request_hash: str,
    ) -> dict[str, Any]:
        return self._insert_new(
            actor=actor,
            payload=payload,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            operation="create",
            source_id=None,
            images=[],
        )

    def copy_report(
        self,
        *,
        actor: str,
        source_id: str,
        report_id: str,
        payload: dict[str, Any],
        idempotency_key: str,
        request_hash: str,
        images: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return self._insert_new(
            actor=actor,
            payload=payload,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            operation="copy",
            source_id=source_id,
            report_id=report_id,
            images=images,
        )

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        with self.db():
            row = self._fetch_active(report_id)
            if row is None:
                return None
            images = self._fetch_images(report_id)
            return {"public": _public(row, images), "files": _files(images)}

    def list_reports(
        self,
        *,
        filters: dict[str, Any],
        page: int,
        page_size: int,
        sort: str,
    ) -> dict[str, Any]:
        if sort not in SORT_VALUES:
            sort = "created_at_desc"
        where, params = _where(filters)
        order = _SORT_SQL[sort]
        offset = (page - 1) * page_size
        with self.db():
            with self.connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) AS total FROM engineering.metallographic_reports r WHERE {where}",
                    params,
                )
                total = int(dict(cursor.fetchone())["total"])
                cursor.execute(
                    f"""
                    SELECT r.*,
                           io.content_type AS original_content_type,
                           io.sha256 AS original_sha256,
                           im.content_type AS measured_content_type,
                           im.sha256 AS measured_sha256
                      FROM engineering.metallographic_reports r
                      LEFT JOIN engineering.metallographic_report_images io
                        ON io.report_id = r.id AND io.slot = 'original'
                      LEFT JOIN engineering.metallographic_report_images im
                        ON im.report_id = r.id AND im.slot = 'measured'
                     WHERE {where}
                     ORDER BY {order}
                     LIMIT %s OFFSET %s
                    """,
                    (*params, page_size, offset),
                )
                rows = [dict(item) for item in cursor.fetchall()]
        items = []
        for row in rows:
            images = {
                "original": _joined_image(row, "original"),
                "measured": _joined_image(row, "measured"),
            }
            items.append(_public(row, images))
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": page * page_size < total,
        }

    def update_report(
        self,
        *,
        actor: str,
        report_id: str,
        expected_version: int,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        with self.db():
            row = self._lock_active(report_id)
            self._ensure_version(row, expected_version)
            merged = _apply_changes(row, changes)
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE engineering.metallographic_reports
                       SET report_date = %s,
                           revision = %s,
                           terminal_code = %s,
                           terminal_part_number = %s,
                           product_harness = %s,
                           cable = %s,
                           conductor_section = %s,
                           applicator_tool = %s,
                           press_equipment = %s,
                           batch_production_order = %s,
                           sample_identification = %s,
                           measurements = %s,
                           conclusion_result = %s,
                           conclusion_notes = %s,
                           analyst_name = %s,
                           status = %s,
                           version = version + 1,
                           updated_at = NOW(),
                           updated_by = %s
                     WHERE id = %s AND version = %s AND deleted_at IS NULL
                    RETURNING *
                    """,
                    (
                        merged["report_date"],
                        merged["revision"],
                        *(merged[field] for field in SAMPLE_FIELDS),
                        Json(merged["measurements"]),
                        merged["conclusion_result"],
                        merged["conclusion_notes"],
                        merged["analyst_name"],
                        merged["status"],
                        actor,
                        report_id,
                        expected_version,
                    ),
                )
                updated = cursor.fetchone()
                if updated is None:
                    raise ReportVersionConflictError(
                        "O relatório foi alterado por outra pessoa."
                    )
                self._audit(
                    cursor,
                    report_id,
                    "update",
                    actor,
                    {"fields": sorted(changes.keys())},
                )
            self.connection.commit()
            images = self._fetch_images(report_id)
            stored = dict(updated)
            return {"public": _public(stored, images), "files": _files(images)}

    def soft_delete(
        self,
        *,
        actor: str,
        report_id: str,
        expected_version: int,
    ) -> dict[str, Any]:
        with self.db():
            row = self._lock_active(report_id)
            self._ensure_version(row, expected_version)
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE engineering.metallographic_reports
                       SET deleted_at = NOW(),
                           deleted_by = %s,
                           updated_at = NOW(),
                           updated_by = %s,
                           version = version + 1
                     WHERE id = %s AND version = %s AND deleted_at IS NULL
                    RETURNING id, version
                    """,
                    (actor, actor, report_id, expected_version),
                )
                deleted = cursor.fetchone()
                if deleted is None:
                    raise ReportVersionConflictError(
                        "O relatório foi alterado por outra pessoa."
                    )
                self._audit(cursor, report_id, "delete", actor, {})
            self.connection.commit()
            return {"id": report_id, "deleted": True, "version": int(dict(deleted)["version"])}

    def put_image(
        self,
        *,
        actor: str,
        report_id: str,
        expected_version: int,
        image: dict[str, Any],
    ) -> dict[str, Any]:
        slot = image["slot"]
        with self.db():
            row = self._lock_active(report_id)
            self._ensure_version(row, expected_version)
            previous = self._fetch_images(report_id).get(slot)
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO engineering.metallographic_report_images (
                        report_id, slot, content_type, size_bytes, sha256,
                        stored_name, width, height
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (report_id, slot) DO UPDATE SET
                        content_type = EXCLUDED.content_type,
                        size_bytes = EXCLUDED.size_bytes,
                        sha256 = EXCLUDED.sha256,
                        stored_name = EXCLUDED.stored_name,
                        width = EXCLUDED.width,
                        height = EXCLUDED.height,
                        updated_at = NOW()
                    """,
                    (
                        report_id,
                        slot,
                        image["content_type"],
                        image["size_bytes"],
                        image["sha256"],
                        image["stored_name"],
                        image["width"],
                        image["height"],
                    ),
                )
                cursor.execute(
                    """
                    UPDATE engineering.metallographic_reports
                       SET version = version + 1, updated_at = NOW(), updated_by = %s
                     WHERE id = %s AND version = %s AND deleted_at IS NULL
                    RETURNING version, updated_at
                    """,
                    (actor, report_id, expected_version),
                )
                bumped = cursor.fetchone()
                if bumped is None:
                    raise ReportVersionConflictError(
                        "O relatório foi alterado por outra pessoa."
                    )
                self._audit(
                    cursor,
                    report_id,
                    "put_image",
                    actor,
                    {"slot": slot, "action": "replace" if previous else "create"},
                )
            self.connection.commit()
            bumped_row = dict(bumped)
            return {
                "previous_stored_name": None if previous is None else previous.get("stored_name"),
                "image": {
                    "slot": slot,
                    "content_type": image["content_type"],
                    "size_bytes": image["size_bytes"],
                    "sha256": image["sha256"],
                    "version": int(bumped_row["version"]),
                    "updated_at": _iso(bumped_row["updated_at"]),
                },
            }

    def delete_image(
        self,
        *,
        actor: str,
        report_id: str,
        slot: str,
        expected_version: int,
    ) -> dict[str, Any]:
        with self.db():
            row = self._lock_active(report_id)
            self._ensure_version(row, expected_version)
            current = self._fetch_images(report_id).get(slot)
            if current is None:
                raise ReportNotFoundError("Imagem não encontrada.")
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM engineering.metallographic_report_images
                     WHERE report_id = %s AND slot = %s
                    """,
                    (report_id, slot),
                )
                cursor.execute(
                    """
                    UPDATE engineering.metallographic_reports
                       SET version = version + 1, updated_at = NOW(), updated_by = %s
                     WHERE id = %s AND version = %s AND deleted_at IS NULL
                    RETURNING version
                    """,
                    (actor, report_id, expected_version),
                )
                bumped = cursor.fetchone()
                if bumped is None:
                    raise ReportVersionConflictError(
                        "O relatório foi alterado por outra pessoa."
                    )
                self._audit(cursor, report_id, "delete_image", actor, {"slot": slot})
            self.connection.commit()
            return {
                "stored_name": current.get("stored_name"),
                "version": int(dict(bumped)["version"]),
            }

    def referenced_stored_names(self, report_id: str) -> set[str]:
        with self.db():
            images = self._fetch_images(report_id)
        return {
            str(item["stored_name"])
            for item in images.values()
            if item.get("stored_name")
        }

    def record_export(self, *, actor: str, report_id: str) -> None:
        with self.db():
            row = self._fetch_active(report_id)
            if row is None:
                raise ReportNotFoundError("Relatório não encontrado.")
            with self.connection.cursor() as cursor:
                self._audit(cursor, report_id, "export_pdf", actor, {})
            self.connection.commit()

    def _insert_new(
        self,
        *,
        actor: str,
        payload: dict[str, Any],
        idempotency_key: str,
        request_hash: str,
        operation: str,
        source_id: str | None,
        images: list[dict[str, Any]],
        report_id: str | None = None,
    ) -> dict[str, Any]:
        created_id = report_id
        try:
            with self.db():
                replay = self._idempotency(actor, operation, idempotency_key, request_hash)
                if replay is not None:
                    return replay
                if operation == "copy":
                    source = self._fetch_active(str(source_id))
                    if source is None:
                        raise ReportNotFoundError("Relatório não encontrado.")
                created_id, number = self._insert_row(actor, payload, report_id=report_id)
                for image in images:
                    self._insert_image(created_id, image)
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO engineering.metallographic_report_idempotency (
                            actor_subject, operation, idempotency_key, request_hash, report_id
                        ) VALUES (%s, %s, %s, %s, %s)
                        """,
                        (actor, operation, idempotency_key, request_hash, created_id),
                    )
                    self._audit(
                        cursor,
                        created_id,
                        operation,
                        actor,
                        {"report_number": number, "source_id": source_id},
                    )
                self.connection.commit()
        except UniqueViolation as exc:
            self.rollback()
            constraint = getattr(getattr(exc, "diag", None), "constraint_name", "") or ""
            if constraint == "uq_metallographic_idempotency":
                replay = self._idempotency_committed(actor, operation, idempotency_key, request_hash)
                if replay is not None:
                    return replay
            raise PluginsRepositoryError("Falha ao gravar o relatório.") from exc
        stored = self.get_report(str(created_id))
        if stored is None:
            raise PluginsRepositoryError("Falha ao gravar o relatório.")
        return stored

    def _insert_row(
        self,
        actor: str,
        payload: dict[str, Any],
        *,
        report_id: str | None,
    ) -> tuple[str, str]:
        year = datetime.now(ZoneInfo(BUSINESS_TIMEZONE)).year
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO engineering.metallographic_report_counters (year, last_value)
                VALUES (%s, 1)
                ON CONFLICT (year) DO UPDATE
                SET last_value = engineering.metallographic_report_counters.last_value + 1
                RETURNING last_value
                """,
                (year,),
            )
            seq = int(dict(cursor.fetchone())["last_value"])
            number = f"MET-{year}-{seq:06d}"
            sample = payload["sample"]
            if report_id:
                cursor.execute(
                    """
                    INSERT INTO engineering.metallographic_reports (
                        id, report_number, report_date, revision,
                        terminal_code, terminal_part_number, product_harness, cable,
                        conductor_section, applicator_tool, press_equipment,
                        batch_production_order, sample_identification,
                        measurements, conclusion_result, conclusion_notes, analyst_name,
                        status, created_by, updated_by
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        report_id,
                        number,
                        payload.get("report_date"),
                        payload.get("revision") or "00",
                        *(sample.get(field) for field in SAMPLE_FIELDS),
                        Json(payload.get("measurements") or empty_measurements()),
                        payload.get("conclusion_result"),
                        payload.get("conclusion_notes"),
                        payload.get("analyst_name"),
                        payload.get("status") or "draft",
                        actor,
                        actor,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO engineering.metallographic_reports (
                        report_number, report_date, revision,
                    terminal_code, terminal_part_number, product_harness, cable,
                    conductor_section, applicator_tool, press_equipment,
                    batch_production_order, sample_identification,
                    measurements, conclusion_result, conclusion_notes, analyst_name,
                    status, created_by, updated_by
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
                RETURNING id
                """,
                (
                    number,
                    payload.get("report_date"),
                    payload.get("revision") or "00",
                    *(sample.get(field) for field in SAMPLE_FIELDS),
                    Json(payload.get("measurements") or empty_measurements()),
                    payload.get("conclusion_result"),
                    payload.get("conclusion_notes"),
                    payload.get("analyst_name"),
                    payload.get("status") or "draft",
                    actor,
                    actor,
                ),
            )
            report_id = str(dict(cursor.fetchone())["id"])
        return report_id, number

    def _insert_image(self, report_id: str, image: dict[str, Any]) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO engineering.metallographic_report_images (
                    report_id, slot, content_type, size_bytes, sha256,
                    stored_name, width, height
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    report_id,
                    image["slot"],
                    image["content_type"],
                    image["size_bytes"],
                    image["sha256"],
                    image["stored_name"],
                    image["width"],
                    image["height"],
                ),
            )

    def _idempotency(
        self,
        actor: str,
        operation: str,
        idempotency_key: str,
        request_hash: str,
    ) -> dict[str, Any] | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT report_id, request_hash
                  FROM engineering.metallographic_report_idempotency
                 WHERE actor_subject = %s AND operation = %s AND idempotency_key = %s
                 FOR UPDATE
                """,
                (actor, operation, idempotency_key),
            )
            found = cursor.fetchone()
        if found is None:
            return None
        row = dict(found)
        if row["request_hash"] != request_hash:
            raise IdempotencyConflictError(
                "A Idempotency-Key já foi usada com outro conteúdo."
            )
        stored = self._load_active(str(row["report_id"]))
        if stored is None:
            raise IdempotencyConflictError(
                "A Idempotency-Key já foi usada e o relatório não está mais disponível."
            )
        return stored

    def _idempotency_committed(
        self,
        actor: str,
        operation: str,
        idempotency_key: str,
        request_hash: str,
    ) -> dict[str, Any] | None:
        with self.db():
            return self._idempotency(actor, operation, idempotency_key, request_hash)

    def _load_active(self, report_id: str) -> dict[str, Any] | None:
        row = self._fetch_active(report_id)
        if row is None:
            return None
        images = self._fetch_images(report_id)
        return {"public": _public(row, images), "files": _files(images)}

    def _fetch_active(self, report_id: str) -> dict[str, Any] | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM engineering.metallographic_reports
                 WHERE id = %s AND deleted_at IS NULL
                """,
                (report_id,),
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    def _lock_active(self, report_id: str) -> dict[str, Any]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM engineering.metallographic_reports
                 WHERE id = %s AND deleted_at IS NULL
                 FOR UPDATE
                """,
                (report_id,),
            )
            row = cursor.fetchone()
        if row is None:
            raise ReportNotFoundError("Relatório não encontrado.")
        return dict(row)

    def _fetch_images(self, report_id: str) -> dict[str, dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT slot, content_type, size_bytes, sha256, stored_name, width, height, updated_at
                  FROM engineering.metallographic_report_images
                 WHERE report_id = %s
                """,
                (report_id,),
            )
            rows = [dict(item) for item in cursor.fetchall()]
        return {str(row["slot"]): row for row in rows}

    def _ensure_version(self, row: dict[str, Any], expected_version: int) -> None:
        if int(row["version"]) != int(expected_version):
            raise ReportVersionConflictError(
                "O relatório foi alterado por outra pessoa."
            )

    def _audit(
        self,
        cursor: Any,
        report_id: str,
        operation: str,
        actor: str,
        detail: dict[str, Any],
    ) -> None:
        cursor.execute(
            """
            INSERT INTO engineering.metallographic_report_audit (
                report_id, operation, actor_subject, outcome, detail
            ) VALUES (%s, %s, %s, 'ok', %s)
            """,
            (report_id, operation, actor, Json(detail)),
        )


def _files(images: dict[str, dict[str, Any]]) -> dict[str, str | None]:
    return {
        slot: None if images.get(slot) is None else images[slot].get("stored_name")
        for slot in ("original", "measured")
    }


def _joined_image(row: dict[str, Any], slot: str) -> dict[str, Any] | None:
    content_type = row.get(f"{slot}_content_type")
    if not content_type:
        return None
    return {"content_type": content_type, "sha256": row.get(f"{slot}_sha256")}


def _where(filters: dict[str, Any]) -> tuple[str, tuple[Any, ...]]:
    clauses = ["r.deleted_at IS NULL"]
    params: list[Any] = []
    date_from = filters.get("report_date_from")
    date_to = filters.get("report_date_to")
    if date_from:
        clauses.append(
            "COALESCE(r.report_date, (r.created_at AT TIME ZONE 'America/Sao_Paulo')::date) >= %s::date"
        )
        params.append(date_from)
    if date_to:
        clauses.append(
            "COALESCE(r.report_date, (r.created_at AT TIME ZONE 'America/Sao_Paulo')::date) <= %s::date"
        )
        params.append(date_to)
    for field, column in _TEXT_COLUMNS.items():
        value = filters.get(field)
        if value:
            clauses.append(f"{column} ILIKE %s ESCAPE '\\'")
            params.append(_like(str(value)))
    result = filters.get("conclusion_result")
    if result:
        clauses.append("r.conclusion_result = %s")
        params.append(result)
    return " AND ".join(clauses), tuple(params)


def _apply_changes(row: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "report_date": _iso(row.get("report_date")),
        "revision": row.get("revision"),
        "conclusion_result": row.get("conclusion_result"),
        "conclusion_notes": row.get("conclusion_notes"),
        "analyst_name": row.get("analyst_name"),
        "status": row.get("status") or "draft",
        "measurements": _measurements(row.get("measurements")),
    }
    for field in SAMPLE_FIELDS:
        merged[field] = row.get(field)
    if "sample" in changes:
        merged.update(changes["sample"])
    if "measurements" in changes:
        merged["measurements"] = {**merged["measurements"], **changes["measurements"]}
    for key in (
        "report_date",
        "revision",
        "conclusion_result",
        "conclusion_notes",
        "analyst_name",
        "status",
    ):
        if key in changes:
            merged[key] = changes[key]
    return merged
