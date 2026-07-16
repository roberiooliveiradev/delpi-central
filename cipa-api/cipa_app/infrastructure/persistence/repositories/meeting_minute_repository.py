from __future__ import annotations

import json
import os
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def get_connection():
    host = os.getenv("PLUGINS_DB_HOST", "").strip()
    port = os.getenv("PLUGINS_DB_PORT", "5432").strip()
    database = os.getenv("PLUGINS_DB_NAME", "").strip()
    user = os.getenv("PLUGINS_DB_USER", "").strip()
    password = os.getenv("PLUGINS_DB_PASSWORD", "").strip()
    connect_timeout = os.getenv("PLUGINS_DB_CONNECT_TIMEOUT", "5").strip() or "5"
    sslmode = os.getenv("PLUGINS_DB_SSLMODE", "prefer").strip() or "prefer"
    if not all([host, database, user, password]):
        raise RuntimeError("Variáveis PLUGINS_DB_* incompletas.")
    dsn = (
        f"host={host} port={port} dbname={database} user={user} "
        f"password={password} connect_timeout={connect_timeout} sslmode={sslmode}"
    )
    return psycopg.connect(conninfo=dsn, row_factory=dict_row, autocommit=False)


def _uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    return value if isinstance(value, UUID) else UUID(str(value))


class MeetingMinuteRepository:
    def list_minutes(
        self,
        *,
        unit_codes: list[str],
        status: str | None = None,
        meeting_type: str | None = None,
        q: str | None = None,
        pending_for_user_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses = ["m.deleted_at IS NULL", "m.unit_code = ANY(%s)"]
        params: list[Any] = [unit_codes]
        if status:
            clauses.append("m.status = %s")
            params.append(status)
        if meeting_type:
            clauses.append("m.meeting_type = %s")
            params.append(meeting_type)
        if date_from:
            clauses.append("m.meeting_date >= %s")
            params.append(date_from)
        if date_to:
            clauses.append("m.meeting_date <= %s")
            params.append(date_to)
        if q:
            clauses.append("(m.title ILIKE %s OR m.minute_number ILIKE %s)")
            like = f"%{q}%"
            params.extend([like, like])
        if pending_for_user_id:
            clauses.append(
                """
                EXISTS (
                  SELECT 1 FROM cipa.meeting_minute_signers s
                  WHERE s.minute_id = m.id
                    AND s.user_id = %s
                    AND s.status IN ('pending', 'viewed')
                    AND s.version_id = m.current_version_id
                )
                """
            )
            params.append(_uuid(pending_for_user_id))

        where = " AND ".join(clauses)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) AS total FROM cipa.meeting_minutes m WHERE {where}",
                    params,
                )
                total = int(cur.fetchone()["total"])
                cur.execute(
                    f"""
                    SELECT m.*,
                      (
                        SELECT COUNT(*) FROM cipa.meeting_minute_signers s
                        WHERE s.minute_id = m.id
                          AND s.version_id = m.current_version_id
                          AND s.status = 'signed'
                      ) AS signatures_done,
                      (
                        SELECT COUNT(*) FROM cipa.meeting_minute_signers s
                        WHERE s.minute_id = m.id
                          AND s.version_id = m.current_version_id
                          AND s.status IN ('pending', 'viewed')
                      ) AS signatures_pending
                    FROM cipa.meeting_minutes m
                    WHERE {where}
                    ORDER BY m.meeting_date DESC, m.updated_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    [*params, limit, offset],
                )
                rows = cur.fetchall()
        return rows, total

    def get_minute(self, minute_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM cipa.meeting_minutes
                    WHERE id = %s AND deleted_at IS NULL
                    """,
                    (_uuid(minute_id),),
                )
                return cur.fetchone()

    def next_minute_number(self, conn, unit_code: str, year: int) -> str:
        prefix = f"{year}/"
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT minute_number FROM cipa.meeting_minutes
                WHERE unit_code = %s AND minute_number LIKE %s AND deleted_at IS NULL
                ORDER BY minute_number DESC
                LIMIT 1
                """,
                (unit_code, f"{prefix}%"),
            )
            row = cur.fetchone()
        if not row:
            return f"{prefix}001"
        try:
            seq = int(str(row["minute_number"]).split("/", 1)[1])
        except (IndexError, ValueError):
            seq = 0
        return f"{prefix}{seq + 1:03d}"

    def create_minute(
        self,
        *,
        unit_code: str,
        title: str,
        meeting_type: str,
        meeting_date: str,
        start_time: str | None,
        end_time: str | None,
        location: str | None,
        responsible_user_id: str | None,
        responsible_name: str | None,
        president_name: str | None,
        secretary_name: str | None,
        agenda_html: str,
        body_html: str,
        decisions_html: str,
        pending_html: str,
        observations_html: str,
        content_hash: str,
        created_by_user_id: str,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            year = int(str(meeting_date)[:4])
            minute_number = self.next_minute_number(conn, unit_code, year)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cipa.meeting_minutes (
                        unit_code, title, minute_number, meeting_type, meeting_date,
                        start_time, end_time, location, responsible_user_id, responsible_name,
                        president_name, secretary_name, status, created_by_user_id
                    ) VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft',%s
                    )
                    RETURNING *
                    """,
                    (
                        unit_code,
                        title,
                        minute_number,
                        meeting_type,
                        meeting_date,
                        start_time,
                        end_time,
                        location,
                        _uuid(responsible_user_id),
                        responsible_name,
                        president_name,
                        secretary_name,
                        _uuid(created_by_user_id),
                    ),
                )
                minute = cur.fetchone()
                cur.execute(
                    """
                    INSERT INTO cipa.meeting_minute_versions (
                        minute_id, unit_code, version_number, title, meeting_type, meeting_date,
                        start_time, end_time, location, agenda_html, body_html, decisions_html,
                        pending_html, observations_html, content_hash, change_reason, created_by_user_id
                    ) VALUES (
                        %s,%s,1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                    RETURNING *
                    """,
                    (
                        minute["id"],
                        unit_code,
                        title,
                        meeting_type,
                        meeting_date,
                        start_time,
                        end_time,
                        location,
                        agenda_html,
                        body_html,
                        decisions_html,
                        pending_html,
                        observations_html,
                        content_hash,
                        "Criação inicial",
                        _uuid(created_by_user_id),
                    ),
                )
                version = cur.fetchone()
                cur.execute(
                    """
                    UPDATE cipa.meeting_minutes
                    SET current_version_id = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (version["id"], minute["id"]),
                )
                minute = cur.fetchone()
                self._audit(
                    cur,
                    minute_id=minute["id"],
                    unit_code=unit_code,
                    entity_type="meeting_minute",
                    entity_id=minute["id"],
                    action="create",
                    actor_user_id=created_by_user_id,
                    before=None,
                    after=minute,
                )
            conn.commit()
            return minute

    def update_minute_draft(self, minute_id: str, fields: dict[str, Any], actor_user_id: str) -> dict[str, Any]:
        allowed = {
            "title",
            "meeting_type",
            "meeting_date",
            "start_time",
            "end_time",
            "location",
            "responsible_user_id",
            "responsible_name",
            "president_name",
            "secretary_name",
        }
        sets = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = %s")
            if key == "responsible_user_id":
                params.append(_uuid(value) if value else None)
            else:
                params.append(value)
        if not sets:
            minute = self.get_minute(minute_id)
            if not minute:
                raise LookupError("Ata não encontrada.")
            return minute
        sets.append("updated_at = NOW()")
        params.append(_uuid(minute_id))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM cipa.meeting_minutes WHERE id = %s AND deleted_at IS NULL FOR UPDATE",
                    (_uuid(minute_id),),
                )
                before = cur.fetchone()
                if not before:
                    raise LookupError("Ata não encontrada.")
                cur.execute(
                    f"UPDATE cipa.meeting_minutes SET {', '.join(sets)} WHERE id = %s RETURNING *",
                    params,
                )
                after = cur.fetchone()
                self._audit(
                    cur,
                    minute_id=after["id"],
                    unit_code=after["unit_code"],
                    entity_type="meeting_minute",
                    entity_id=after["id"],
                    action="edit",
                    actor_user_id=actor_user_id,
                    before=before,
                    after=after,
                )
            conn.commit()
            return after

    def update_current_version_content(
        self,
        *,
        minute_id: str,
        agenda_html: str,
        body_html: str,
        decisions_html: str,
        pending_html: str,
        observations_html: str,
        content_hash: str,
        actor_user_id: str,
        sync_header: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM cipa.meeting_minutes WHERE id = %s AND deleted_at IS NULL FOR UPDATE",
                    (_uuid(minute_id),),
                )
                minute = cur.fetchone()
                if not minute or not minute.get("current_version_id"):
                    raise LookupError("Ata não encontrada.")
                if sync_header:
                    cur.execute(
                        """
                        UPDATE cipa.meeting_minutes
                        SET title = COALESCE(%s, title),
                            meeting_type = COALESCE(%s, meeting_type),
                            meeting_date = COALESCE(%s, meeting_date),
                            start_time = COALESCE(%s, start_time),
                            end_time = COALESCE(%s, end_time),
                            location = COALESCE(%s, location),
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING *
                        """,
                        (
                            sync_header.get("title"),
                            sync_header.get("meeting_type"),
                            sync_header.get("meeting_date"),
                            sync_header.get("start_time"),
                            sync_header.get("end_time"),
                            sync_header.get("location"),
                            minute["id"],
                        ),
                    )
                    minute = cur.fetchone()
                cur.execute(
                    """
                    UPDATE cipa.meeting_minute_versions
                    SET title = %s,
                        meeting_type = %s,
                        meeting_date = %s,
                        start_time = %s,
                        end_time = %s,
                        location = %s,
                        agenda_html = %s,
                        body_html = %s,
                        decisions_html = %s,
                        pending_html = %s,
                        observations_html = %s,
                        content_hash = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (
                        minute["title"],
                        minute["meeting_type"],
                        minute["meeting_date"],
                        minute["start_time"],
                        minute["end_time"],
                        minute["location"],
                        agenda_html,
                        body_html,
                        decisions_html,
                        pending_html,
                        observations_html,
                        content_hash,
                        minute["current_version_id"],
                    ),
                )
                version = cur.fetchone()
                self._audit(
                    cur,
                    minute_id=minute["id"],
                    unit_code=minute["unit_code"],
                    entity_type="meeting_minute_version",
                    entity_id=version["id"],
                    action="edit_content",
                    actor_user_id=actor_user_id,
                    before=None,
                    after=version,
                )
            conn.commit()
            return version

    def create_new_version(
        self,
        *,
        minute_id: str,
        change_reason: str,
        agenda_html: str,
        body_html: str,
        decisions_html: str,
        pending_html: str,
        observations_html: str,
        content_hash: str,
        actor_user_id: str,
        reset_to_in_review: bool = True,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM cipa.meeting_minutes WHERE id = %s AND deleted_at IS NULL FOR UPDATE",
                    (_uuid(minute_id),),
                )
                minute = cur.fetchone()
                if not minute:
                    raise LookupError("Ata não encontrada.")
                cur.execute(
                    """
                    SELECT COALESCE(MAX(version_number), 0) AS max_v
                    FROM cipa.meeting_minute_versions WHERE minute_id = %s
                    """,
                    (minute["id"],),
                )
                next_v = int(cur.fetchone()["max_v"]) + 1
                cur.execute(
                    """
                    UPDATE cipa.meeting_minute_signers
                    SET status = 'invalidated', updated_at = NOW()
                    WHERE minute_id = %s AND version_id = %s AND status IN ('pending', 'viewed', 'signed')
                    """,
                    (minute["id"], minute["current_version_id"]),
                )
                cur.execute(
                    """
                    INSERT INTO cipa.meeting_minute_versions (
                        minute_id, unit_code, version_number, title, meeting_type, meeting_date,
                        start_time, end_time, location, agenda_html, body_html, decisions_html,
                        pending_html, observations_html, content_hash, change_reason, created_by_user_id
                    ) VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                    RETURNING *
                    """,
                    (
                        minute["id"],
                        minute["unit_code"],
                        next_v,
                        minute["title"],
                        minute["meeting_type"],
                        minute["meeting_date"],
                        minute["start_time"],
                        minute["end_time"],
                        minute["location"],
                        agenda_html,
                        body_html,
                        decisions_html,
                        pending_html,
                        observations_html,
                        content_hash,
                        change_reason,
                        _uuid(actor_user_id),
                    ),
                )
                version = cur.fetchone()
                new_status = "in_review" if reset_to_in_review else minute["status"]
                cur.execute(
                    """
                    UPDATE cipa.meeting_minutes
                    SET current_version_id = %s,
                        status = %s,
                        submitted_for_signature_at = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (version["id"], new_status, minute["id"]),
                )
                updated = cur.fetchone()
                self._audit(
                    cur,
                    minute_id=minute["id"],
                    unit_code=minute["unit_code"],
                    entity_type="meeting_minute_version",
                    entity_id=version["id"],
                    action="create_version",
                    actor_user_id=actor_user_id,
                    before={"status": minute["status"]},
                    after={"status": updated["status"], "version": version},
                )
            conn.commit()
            return {"minute": updated, "version": version}

    def get_version(self, minute_id: str, version_id: str | None = None) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if version_id:
                    cur.execute(
                        """
                        SELECT * FROM cipa.meeting_minute_versions
                        WHERE id = %s AND minute_id = %s
                        """,
                        (_uuid(version_id), _uuid(minute_id)),
                    )
                else:
                    cur.execute(
                        """
                        SELECT v.* FROM cipa.meeting_minute_versions v
                        JOIN cipa.meeting_minutes m ON m.current_version_id = v.id
                        WHERE m.id = %s
                        """,
                        (_uuid(minute_id),),
                    )
                return cur.fetchone()

    def list_versions(self, minute_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, minute_id, version_number, content_hash, change_reason,
                           created_by_user_id, created_at, title
                    FROM cipa.meeting_minute_versions
                    WHERE minute_id = %s
                    ORDER BY version_number DESC
                    """,
                    (_uuid(minute_id),),
                )
                return cur.fetchall()

    def replace_participants(
        self, minute_id: str, unit_code: str, participants: list[dict[str, Any]], actor_user_id: str
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM cipa.meeting_minute_participants WHERE minute_id = %s",
                    (_uuid(minute_id),),
                )
                rows = []
                for index, item in enumerate(participants):
                    cur.execute(
                        """
                        INSERT INTO cipa.meeting_minute_participants (
                            minute_id, unit_code, user_id, display_name, role_in_meeting,
                            presence, is_external, must_sign, sort_order
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING *
                        """,
                        (
                            _uuid(minute_id),
                            unit_code,
                            _uuid(item.get("user_id")) if item.get("user_id") else None,
                            item["display_name"],
                            item.get("role_in_meeting") or "other",
                            item.get("presence") or "present",
                            bool(item.get("is_external")),
                            bool(item.get("must_sign")),
                            item.get("sort_order", index),
                        ),
                    )
                    rows.append(cur.fetchone())
                self._audit(
                    cur,
                    minute_id=_uuid(minute_id),
                    unit_code=unit_code,
                    entity_type="meeting_minute_participants",
                    entity_id=_uuid(minute_id),
                    action="replace_participants",
                    actor_user_id=actor_user_id,
                    before=None,
                    after={"count": len(rows)},
                )
            conn.commit()
            return rows

    def list_participants(self, minute_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM cipa.meeting_minute_participants
                    WHERE minute_id = %s
                    ORDER BY sort_order ASC, created_at ASC
                    """,
                    (_uuid(minute_id),),
                )
                return cur.fetchall()

    def replace_signers(
        self,
        *,
        minute_id: str,
        version_id: str,
        unit_code: str,
        signers: list[dict[str, Any]],
        actor_user_id: str,
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM cipa.meeting_minute_signers
                    WHERE minute_id = %s AND version_id = %s
                    """,
                    (_uuid(minute_id), _uuid(version_id)),
                )
                rows = []
                for index, item in enumerate(signers):
                    cur.execute(
                        """
                        INSERT INTO cipa.meeting_minute_signers (
                            minute_id, version_id, unit_code, user_id, display_name, sign_order, status
                        ) VALUES (%s,%s,%s,%s,%s,%s,'pending')
                        RETURNING *
                        """,
                        (
                            _uuid(minute_id),
                            _uuid(version_id),
                            unit_code,
                            _uuid(item["user_id"]),
                            item["display_name"],
                            item.get("sign_order", index + 1),
                        ),
                    )
                    rows.append(cur.fetchone())
                self._audit(
                    cur,
                    minute_id=_uuid(minute_id),
                    unit_code=unit_code,
                    entity_type="meeting_minute_signers",
                    entity_id=_uuid(version_id),
                    action="replace_signers",
                    actor_user_id=actor_user_id,
                    before=None,
                    after={"count": len(rows)},
                )
            conn.commit()
            return rows

    def list_signers(self, minute_id: str, version_id: str | None = None) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if version_id:
                    cur.execute(
                        """
                        SELECT * FROM cipa.meeting_minute_signers
                        WHERE minute_id = %s AND version_id = %s
                        ORDER BY sign_order ASC
                        """,
                        (_uuid(minute_id), _uuid(version_id)),
                    )
                else:
                    cur.execute(
                        """
                        SELECT s.* FROM cipa.meeting_minute_signers s
                        JOIN cipa.meeting_minutes m ON m.id = s.minute_id
                        WHERE s.minute_id = %s AND s.version_id = m.current_version_id
                        ORDER BY s.sign_order ASC
                        """,
                        (_uuid(minute_id),),
                    )
                return cur.fetchall()

    def set_status(
        self,
        *,
        minute_id: str,
        status: str,
        actor_user_id: str,
        action: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        extra = extra or {}
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM cipa.meeting_minutes WHERE id = %s AND deleted_at IS NULL FOR UPDATE",
                    (_uuid(minute_id),),
                )
                before = cur.fetchone()
                if not before:
                    raise LookupError("Ata não encontrada.")
                sets = ["status = %s", "updated_at = NOW()"]
                params: list[Any] = [status]
                if status == "awaiting_signatures":
                    sets.append("submitted_for_signature_at = NOW()")
                if status == "finalized":
                    sets.append("finalized_at = NOW()")
                    sets.append("finalized_by_user_id = %s")
                    params.append(_uuid(actor_user_id))
                if status == "cancelled":
                    sets.append("cancelled_at = NOW()")
                    sets.append("cancelled_by_user_id = %s")
                    params.append(_uuid(actor_user_id))
                    sets.append("cancel_reason = %s")
                    params.append(extra.get("cancel_reason"))
                if extra.get("final_pdf_path"):
                    sets.append("final_pdf_path = %s")
                    params.append(extra["final_pdf_path"])
                if extra.get("final_content_hash"):
                    sets.append("final_content_hash = %s")
                    params.append(extra["final_content_hash"])
                if extra.get("validation_code"):
                    sets.append("validation_code = %s")
                    params.append(extra["validation_code"])
                params.append(_uuid(minute_id))
                cur.execute(
                    f"UPDATE cipa.meeting_minutes SET {', '.join(sets)} WHERE id = %s RETURNING *",
                    params,
                )
                after = cur.fetchone()
                self._audit(
                    cur,
                    minute_id=after["id"],
                    unit_code=after["unit_code"],
                    entity_type="meeting_minute",
                    entity_id=after["id"],
                    action=action,
                    actor_user_id=actor_user_id,
                    before=before,
                    after=after,
                )
            conn.commit()
            return after

    def mark_signer_viewed(self, signer_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE cipa.meeting_minute_signers
                    SET status = CASE WHEN status = 'pending' THEN 'viewed' ELSE status END,
                        viewed_at = COALESCE(viewed_at, NOW()),
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (_uuid(signer_id),),
                )
                row = cur.fetchone()
            conn.commit()
            return row

    def get_signer_for_user(self, minute_id: str, user_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.* FROM cipa.meeting_minute_signers s
                    JOIN cipa.meeting_minutes m ON m.id = s.minute_id
                    WHERE s.minute_id = %s
                      AND s.user_id = %s
                      AND s.version_id = m.current_version_id
                    """,
                    (_uuid(minute_id), _uuid(user_id)),
                )
                return cur.fetchone()

    def register_signature(
        self,
        *,
        minute_id: str,
        version_id: str,
        signer_id: str,
        unit_code: str,
        user_id: str,
        display_name_confirmed: str,
        content_hash: str,
        image_path: str,
        terms_accepted: bool,
        client_ip: str | None,
        user_agent: str | None,
        session_id: str | None,
        idempotency_key: str | None,
        actor_user_id: str,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if idempotency_key:
                    cur.execute(
                        """
                        SELECT * FROM cipa.meeting_minute_signatures
                        WHERE idempotency_key = %s
                        """,
                        (idempotency_key,),
                    )
                    existing = cur.fetchone()
                    if existing:
                        return {"signature": existing, "duplicate": True}

                cur.execute(
                    """
                    SELECT * FROM cipa.meeting_minute_signers
                    WHERE id = %s FOR UPDATE
                    """,
                    (_uuid(signer_id),),
                )
                signer = cur.fetchone()
                if not signer:
                    raise LookupError("Signatário não encontrado.")
                if signer["status"] == "signed":
                    raise ValueError("Assinatura já registrada para este signatário.")
                if signer["status"] in {"invalidated", "cancelled", "refused"}:
                    raise ValueError("Signatário não está elegível para assinar.")

                cur.execute(
                    """
                    INSERT INTO cipa.meeting_minute_signatures (
                        minute_id, version_id, signer_id, unit_code, user_id,
                        display_name_confirmed, content_hash, image_path, terms_accepted,
                        client_ip, user_agent, session_id, idempotency_key
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING *
                    """,
                    (
                        _uuid(minute_id),
                        _uuid(version_id),
                        _uuid(signer_id),
                        unit_code,
                        _uuid(user_id),
                        display_name_confirmed,
                        content_hash,
                        image_path,
                        terms_accepted,
                        client_ip,
                        user_agent,
                        session_id,
                        idempotency_key,
                    ),
                )
                signature = cur.fetchone()
                cur.execute(
                    """
                    UPDATE cipa.meeting_minute_signers
                    SET status = 'signed', signed_at = NOW(), updated_at = NOW()
                    WHERE id = %s
                    """,
                    (_uuid(signer_id),),
                )
                cur.execute(
                    """
                    SELECT
                      COUNT(*) FILTER (WHERE status = 'signed') AS signed_count,
                      COUNT(*) AS required_count
                    FROM cipa.meeting_minute_signers
                    WHERE minute_id = %s AND version_id = %s
                      AND status NOT IN ('invalidated', 'cancelled')
                    """,
                    (_uuid(minute_id), _uuid(version_id)),
                )
                progress = cur.fetchone()
                self._audit(
                    cur,
                    minute_id=_uuid(minute_id),
                    unit_code=unit_code,
                    entity_type="meeting_minute_signature",
                    entity_id=signature["id"],
                    action="sign",
                    actor_user_id=actor_user_id,
                    before=None,
                    after=signature,
                )
            conn.commit()
            return {
                "signature": signature,
                "duplicate": False,
                "signed_count": int(progress["signed_count"]),
                "required_count": int(progress["required_count"]),
            }

    def refuse_signature(
        self,
        *,
        minute_id: str,
        signer_id: str,
        reason: str,
        actor_user_id: str,
        unit_code: str,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE cipa.meeting_minute_signers
                    SET status = 'refused',
                        refuse_reason = %s,
                        refused_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s AND minute_id = %s
                    RETURNING *
                    """,
                    (reason, _uuid(signer_id), _uuid(minute_id)),
                )
                signer = cur.fetchone()
                if not signer:
                    raise LookupError("Signatário não encontrado.")
                self._audit(
                    cur,
                    minute_id=_uuid(minute_id),
                    unit_code=unit_code,
                    entity_type="meeting_minute_signer",
                    entity_id=signer["id"],
                    action="refuse_signature",
                    actor_user_id=actor_user_id,
                    before=None,
                    after=signer,
                )
            conn.commit()
            return signer

    def list_signatures(self, minute_id: str, version_id: str | None = None) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if version_id:
                    cur.execute(
                        """
                        SELECT * FROM cipa.meeting_minute_signatures
                        WHERE minute_id = %s AND version_id = %s
                        ORDER BY created_at ASC
                        """,
                        (_uuid(minute_id), _uuid(version_id)),
                    )
                else:
                    cur.execute(
                        """
                        SELECT sig.* FROM cipa.meeting_minute_signatures sig
                        JOIN cipa.meeting_minutes m ON m.id = sig.minute_id
                        WHERE sig.minute_id = %s AND sig.version_id = m.current_version_id
                        ORDER BY sig.created_at ASC
                        """,
                        (_uuid(minute_id),),
                    )
                return cur.fetchall()

    def get_signature(self, minute_id: str, signature_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT sig.* FROM cipa.meeting_minute_signatures sig
                    JOIN cipa.meeting_minutes m ON m.id = sig.minute_id
                    WHERE sig.id = %s
                      AND sig.minute_id = %s
                      AND sig.version_id = m.current_version_id
                    """,
                    (_uuid(signature_id), _uuid(minute_id)),
                )
                return cur.fetchone()

    def replace_action_items(
        self, minute_id: str, unit_code: str, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM cipa.meeting_minute_action_items WHERE minute_id = %s",
                    (_uuid(minute_id),),
                )
                rows = []
                for index, item in enumerate(items):
                    cur.execute(
                        """
                        INSERT INTO cipa.meeting_minute_action_items (
                            minute_id, unit_code, title, description, owner_user_id, owner_name,
                            due_date, priority, status, sort_order
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING *
                        """,
                        (
                            _uuid(minute_id),
                            unit_code,
                            item["title"],
                            item.get("description"),
                            _uuid(item.get("owner_user_id")) if item.get("owner_user_id") else None,
                            item.get("owner_name"),
                            item.get("due_date"),
                            item.get("priority") or "normal",
                            item.get("status") or "open",
                            item.get("sort_order", index),
                        ),
                    )
                    rows.append(cur.fetchone())
            conn.commit()
            return rows

    def list_action_items(self, minute_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM cipa.meeting_minute_action_items
                    WHERE minute_id = %s
                    ORDER BY sort_order ASC
                    """,
                    (_uuid(minute_id),),
                )
                return cur.fetchall()

    def soft_delete(self, minute_id: str, actor_user_id: str) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE cipa.meeting_minutes
                    SET deleted_at = NOW(), updated_at = NOW()
                    WHERE id = %s AND deleted_at IS NULL
                    RETURNING *
                    """,
                    (_uuid(minute_id),),
                )
                row = cur.fetchone()
                if not row:
                    raise LookupError("Ata não encontrada.")
                self._audit(
                    cur,
                    minute_id=row["id"],
                    unit_code=row["unit_code"],
                    entity_type="meeting_minute",
                    entity_id=row["id"],
                    action="soft_delete",
                    actor_user_id=actor_user_id,
                    before=None,
                    after={"deleted_at": row["deleted_at"]},
                )
            conn.commit()
            return row

    def list_audit(self, minute_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM cipa.meeting_minute_audit_logs
                    WHERE minute_id = %s
                    ORDER BY created_at DESC
                    LIMIT 200
                    """,
                    (_uuid(minute_id),),
                )
                return cur.fetchall()

    def add_attachment(
        self,
        *,
        minute_id: str,
        unit_code: str,
        file_name: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
        uploaded_by_user_id: str,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cipa.meeting_minute_attachments (
                        minute_id, unit_code, file_name, content_type, size_bytes,
                        storage_path, uploaded_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    RETURNING *
                    """,
                    (
                        _uuid(minute_id),
                        unit_code,
                        file_name,
                        content_type,
                        size_bytes,
                        storage_path,
                        _uuid(uploaded_by_user_id),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            return row

    def _audit(
        self,
        cur,
        *,
        minute_id,
        unit_code: str,
        entity_type: str,
        entity_id,
        action: str,
        actor_user_id: str | None,
        before: Any,
        after: Any,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        cur.execute(
            """
            INSERT INTO cipa.meeting_minute_audit_logs (
                minute_id, unit_code, entity_type, entity_id, action, actor_user_id,
                before_data, after_data, client_ip, user_agent
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                _uuid(str(minute_id)) if minute_id else None,
                unit_code,
                entity_type,
                _uuid(str(entity_id)) if entity_id else None,
                action,
                _uuid(actor_user_id) if actor_user_id else None,
                Jsonb(json.loads(json.dumps(before, default=str))) if before is not None else None,
                Jsonb(json.loads(json.dumps(after, default=str))) if after is not None else None,
                client_ip,
                user_agent,
            ),
        )
