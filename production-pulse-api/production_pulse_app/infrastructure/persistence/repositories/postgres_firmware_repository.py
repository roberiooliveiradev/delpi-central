from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import psycopg.errors
from psycopg.types.json import Json

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)


class FirmwareConflictError(Exception):
    pass


class FirmwareNotFoundError(Exception):
    pass


_FIRMWARE_COLUMNS = """
    id, firmware_key, driver_key, version, display_name, source_text, artifact_path,
    artifact_sha256, artifact_size_bytes, release_notes, min_compatible_version,
    published_at, created_by, created_at, archived_at
"""


class PostgresFirmwareRepository:
    def list_firmwares(
        self,
        *,
        firmware_key: str | None = None,
        driver_key: str | None = None,
        published_only: bool = False,
        include_archived: bool = True,
    ) -> list[dict[str, Any]]:
        clauses = ["1=1"]
        params: list[Any] = []
        if firmware_key:
            clauses.append("firmware_key = %s")
            params.append(firmware_key)
        if driver_key:
            clauses.append("driver_key = %s")
            params.append(driver_key)
        if published_only:
            clauses.append("published_at IS NOT NULL")
        if not include_archived:
            clauses.append("archived_at IS NULL")
        where_sql = " AND ".join(clauses)
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_FIRMWARE_COLUMNS}
                    FROM production_pulse.firmwares
                    WHERE {where_sql}
                    ORDER BY firmware_key, published_at DESC NULLS LAST, created_at DESC
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]

    def get_by_id(self, firmware_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_FIRMWARE_COLUMNS}
                    FROM production_pulse.firmwares
                    WHERE id = %s
                    """,
                    (firmware_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def get_by_key_version(
        self,
        *,
        firmware_key: str,
        version: str,
    ) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_FIRMWARE_COLUMNS}
                    FROM production_pulse.firmwares
                    WHERE firmware_key = %s AND version = %s
                    ORDER BY published_at DESC NULLS LAST, created_at DESC
                    LIMIT 1
                    """,
                    (firmware_key, version),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def create(
        self,
        *,
        firmware_key: str,
        driver_key: str,
        version: str,
        display_name: str,
        source_text: str | None = None,
        artifact_path: str | None = None,
        artifact_sha256: str | None = None,
        artifact_size_bytes: int | None = None,
        release_notes: str | None,
        min_compatible_version: str | None,
        publish: bool,
        actor_sub: str | None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO production_pulse.firmwares (
                            firmware_key, driver_key, version, display_name, source_text,
                            artifact_path, artifact_sha256, artifact_size_bytes,
                            release_notes, min_compatible_version, published_at, created_by
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            CASE WHEN %s THEN NOW() ELSE NULL END, %s
                        )
                        RETURNING {_FIRMWARE_COLUMNS}
                        """,
                        (
                            firmware_key,
                            driver_key,
                            version,
                            display_name,
                            source_text,
                            artifact_path,
                            artifact_sha256,
                            artifact_size_bytes,
                            release_notes,
                            min_compatible_version,
                            publish,
                            actor_sub,
                        ),
                    )
                    row = cur.fetchone()
                conn.commit()
                return dict(row)
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                raise FirmwareConflictError(str(exc)) from exc

    def update_source(self, firmware_id: UUID, *, source_text: str | None) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmwares
                    SET source_text = %s
                    WHERE id = %s
                      AND published_at IS NULL
                      AND archived_at IS NULL
                    RETURNING {_FIRMWARE_COLUMNS}
                    """,
                    (source_text, firmware_id),
                )
                row = cur.fetchone()
            conn.commit()
            if row is None:
                existing = self.get_by_id(firmware_id)
                if existing is None:
                    raise FirmwareNotFoundError(str(firmware_id))
                raise FirmwareConflictError("firmware_not_editable")
            return dict(row)

    def attach_artifact(
        self,
        firmware_id: UUID,
        *,
        artifact_path: str,
        artifact_sha256: str,
        artifact_size_bytes: int,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmwares
                    SET artifact_path = %s,
                        artifact_sha256 = %s,
                        artifact_size_bytes = %s
                    WHERE id = %s
                      AND published_at IS NULL
                      AND archived_at IS NULL
                    RETURNING {_FIRMWARE_COLUMNS}
                    """,
                    (
                        artifact_path,
                        artifact_sha256,
                        artifact_size_bytes,
                        firmware_id,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            if row is None:
                existing = self.get_by_id(firmware_id)
                if existing is None:
                    raise FirmwareNotFoundError(str(firmware_id))
                raise FirmwareConflictError("firmware_not_editable")
            return dict(row)

    def publish_version(self, firmware_id: UUID) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmwares
                    SET published_at = NOW()
                    WHERE id = %s
                      AND published_at IS NULL
                      AND archived_at IS NULL
                      AND artifact_path IS NOT NULL
                      AND artifact_sha256 IS NOT NULL
                      AND artifact_size_bytes IS NOT NULL
                    RETURNING {_FIRMWARE_COLUMNS}
                    """,
                    (firmware_id,),
                )
                row = cur.fetchone()
            conn.commit()
            if row is None:
                existing = self.get_by_id(firmware_id)
                if existing is None:
                    raise FirmwareNotFoundError(str(firmware_id))
                if existing.get("archived_at") is not None:
                    raise FirmwareConflictError("firmware_archived")
                if existing.get("published_at") is not None:
                    raise FirmwareConflictError("firmware_already_published")
                raise FirmwareConflictError("firmware_missing_artifact")
            return dict(row)

    def update_metadata(
        self,
        firmware_id: UUID,
        *,
        display_name: str | None = None,
        release_notes: str | None = None,
    ) -> dict[str, Any]:
        sets: list[str] = []
        params: list[Any] = []
        if display_name is not None:
            sets.append("display_name = %s")
            params.append(display_name)
        if release_notes is not None:
            sets.append("release_notes = %s")
            params.append(release_notes)
        if not sets:
            row = self.get_by_id(firmware_id)
            if row is None:
                raise FirmwareNotFoundError(str(firmware_id))
            return row
        params.append(firmware_id)
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmwares
                    SET {", ".join(sets)}
                    WHERE id = %s
                      AND archived_at IS NULL
                    RETURNING {_FIRMWARE_COLUMNS}
                    """,
                    params,
                )
                row = cur.fetchone()
            conn.commit()
            if row is None:
                existing = self.get_by_id(firmware_id)
                if existing is None:
                    raise FirmwareNotFoundError(str(firmware_id))
                raise FirmwareConflictError("firmware_archived")
            return dict(row)

    def archive(self, firmware_id: UUID) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmwares
                    SET archived_at = COALESCE(archived_at, NOW())
                    WHERE id = %s
                    RETURNING {_FIRMWARE_COLUMNS}
                    """,
                    (firmware_id,),
                )
                row = cur.fetchone()
            conn.commit()
            if row is None:
                raise FirmwareNotFoundError(str(firmware_id))
            return dict(row)


_JOB_COLUMNS = """
    id, firmware_id, branch, trigger, scheduled_at, status, filter,
    created_by, created_at, updated_at
"""

_TARGET_COLUMNS = """
    id, job_id, device_id, status, from_version, to_version, error_code,
    artifact_token, artifact_token_expires_at, authorized_at, started_at, finished_at,
    created_at, updated_at, bytes_received, bytes_total, progress_percent
"""

_OPEN_TARGET_STATUSES = ("pending", "authorized", "downloading", "applying")


class FirmwareJobConflictError(Exception):
    pass


class FirmwareJobNotFoundError(Exception):
    pass


class PostgresFirmwareUpdateJobRepository:
    def get_job(self, job_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_JOB_COLUMNS} FROM production_pulse.firmware_update_jobs WHERE id = %s",
                    (job_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_jobs(self, *, branch: str | None = None) -> list[dict[str, Any]]:
        clauses = ["1=1"]
        params: list[Any] = []
        if branch:
            clauses.append("branch = %s")
            params.append(branch)
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_JOB_COLUMNS}
                    FROM production_pulse.firmware_update_jobs
                    WHERE {" AND ".join(clauses)}
                    ORDER BY created_at DESC
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]

    def create_job_with_targets(
        self,
        *,
        firmware_id: UUID,
        branch: str,
        trigger: str,
        scheduled_at: datetime | None,
        status: str,
        filter_payload: dict[str, Any],
        targets: list[dict[str, Any]],
        actor_sub: str | None,
        authorize_now: bool,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO production_pulse.firmware_update_jobs (
                            firmware_id, branch, trigger, scheduled_at, status, filter, created_by
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING {_JOB_COLUMNS}
                        """,
                        (
                            firmware_id,
                            branch,
                            trigger,
                            scheduled_at,
                            status,
                            Json(filter_payload),
                            actor_sub,
                        ),
                    )
                    job = dict(cur.fetchone())
                    job_id = job["id"]
                    for target in targets:
                        target_status = "authorized" if authorize_now else "pending"
                        authorized_at = datetime.now(timezone.utc) if authorize_now else None
                        cur.execute(
                            f"""
                            INSERT INTO production_pulse.firmware_update_targets (
                                job_id, device_id, status, from_version, to_version, authorized_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING {_TARGET_COLUMNS}
                            """,
                            (
                                job_id,
                                target["device_id"],
                                target_status,
                                target.get("from_version"),
                                target["to_version"],
                                authorized_at,
                            ),
                        )
                conn.commit()
                return job
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                raise FirmwareJobConflictError("open_target_exists") from exc

    def list_targets(self, job_id: UUID) -> list[dict[str, Any]]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_TARGET_COLUMNS}
                    FROM production_pulse.firmware_update_targets
                    WHERE job_id = %s
                    ORDER BY created_at
                    """,
                    (job_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def cancel_job(self, job_id: UUID) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_JOB_COLUMNS} FROM production_pulse.firmware_update_jobs WHERE id = %s",
                    (job_id,),
                )
                existing = cur.fetchone()
                if existing is None:
                    raise FirmwareJobNotFoundError(str(job_id))
                if existing["status"] not in {"draft", "scheduled", "running"}:
                    raise FirmwareJobConflictError("job_cannot_cancel")
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmware_update_jobs
                    SET status = 'cancelled', updated_at = NOW()
                    WHERE id = %s
                    RETURNING {_JOB_COLUMNS}
                    """,
                    (job_id,),
                )
                job = cur.fetchone()
                cur.execute(
                    """
                    UPDATE production_pulse.firmware_update_targets
                    SET status = 'cancelled',
                        finished_at = NOW(),
                        updated_at = NOW(),
                        artifact_token = NULL,
                        artifact_token_expires_at = NULL
                    WHERE job_id = %s
                      AND status IN ('pending', 'authorized', 'downloading', 'applying')
                    """,
                    (job_id,),
                )
            conn.commit()
            return dict(job)

    def transition_target(
        self,
        target_id: UUID,
        *,
        next_status: str,
        allowed_statuses: tuple[str, ...],
        error_code: str | None = None,
        clear_artifact_token: bool = False,
        touch_started: bool = False,
        touch_finished: bool = False,
        bytes_received: int | None = None,
        bytes_total: int | None = None,
        progress_percent: int | None = None,
    ) -> dict[str, Any] | None:
        """Atomic status transition; returns None if current status not allowed."""
        sets = ["status = %s", "updated_at = NOW()"]
        params: list[Any] = [next_status]
        if error_code is not None:
            sets.append("error_code = %s")
            params.append(error_code)
        if clear_artifact_token:
            sets.append("artifact_token = NULL")
            sets.append("artifact_token_expires_at = NULL")
        if touch_started:
            sets.append("started_at = COALESCE(started_at, NOW())")
        if touch_finished:
            sets.append("finished_at = NOW()")
        if bytes_received is not None:
            sets.append("bytes_received = %s")
            params.append(int(bytes_received))
        if bytes_total is not None:
            sets.append("bytes_total = %s")
            params.append(int(bytes_total))
        if progress_percent is not None:
            sets.append("progress_percent = %s")
            params.append(max(0, min(100, int(progress_percent))))
        params.extend([target_id, list(allowed_statuses)])
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmware_update_targets
                    SET {", ".join(sets)}
                    WHERE id = %s
                      AND status = ANY(%s)
                    RETURNING {_TARGET_COLUMNS}
                    """,
                    params,
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None

    def maybe_finish_job(self, job_id: UUID) -> dict[str, Any] | None:
        """If all targets are terminal and job is running, set completed or failed."""
        terminal = ("updated", "failed", "skipped", "cancelled")
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_JOB_COLUMNS}
                    FROM production_pulse.firmware_update_jobs
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (job_id,),
                )
                job = cur.fetchone()
                if job is None or job["status"] != "running":
                    conn.commit()
                    return dict(job) if job else None
                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status = ANY(%s)) AS terminal,
                        COUNT(*) FILTER (WHERE status = 'updated') AS updated,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed
                    FROM production_pulse.firmware_update_targets
                    WHERE job_id = %s
                    """,
                    (list(terminal), job_id),
                )
                counts = cur.fetchone()
                total = int(counts["total"] or 0)
                done = int(counts["terminal"] or 0)
                if total == 0 or done < total:
                    conn.commit()
                    return dict(job)
                updated_n = int(counts["updated"] or 0)
                next_status = "completed" if updated_n > 0 else "failed"
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmware_update_jobs
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s AND status = 'running'
                    RETURNING {_JOB_COLUMNS}
                    """,
                    (next_status, job_id),
                )
                finished = cur.fetchone()
            conn.commit()
            return dict(finished) if finished else dict(job)

    def authorize_due_scheduled_jobs(self, *, now: datetime | None = None) -> int:
        moment = now or datetime.now(timezone.utc)
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmware_update_jobs
                    SET status = 'running', updated_at = NOW()
                    WHERE status = 'scheduled'
                      AND scheduled_at IS NOT NULL
                      AND scheduled_at <= %s
                    RETURNING id
                    """,
                    (moment,),
                )
                job_ids = [row["id"] for row in cur.fetchall()]
                if job_ids:
                    cur.execute(
                        """
                        UPDATE production_pulse.firmware_update_targets
                        SET status = 'authorized',
                            authorized_at = COALESCE(authorized_at, NOW()),
                            updated_at = NOW()
                        WHERE job_id = ANY(%s)
                          AND status = 'pending'
                        """,
                        (job_ids,),
                    )
            conn.commit()
            return len(job_ids)

    def summary_counts(
        self,
        *,
        branch: str,
        firmware_key: str | None = None,
    ) -> dict[str, int]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM production_pulse.devices d
                    WHERE d.branch = %s
                      AND (
                        %s::text IS NULL
                        OR d.firmware_key = %s
                        OR d.driver_key = %s
                      )
                    """,
                    (branch, firmware_key, firmware_key, firmware_key),
                )
                total = int(cur.fetchone()["total"])

                cur.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (
                            WHERE t.status IN ('authorized', 'downloading', 'applying')
                        ) AS updating,
                        COUNT(*) FILTER (WHERE t.status = 'updated') AS updated,
                        COUNT(*) FILTER (WHERE t.status = 'failed') AS failed
                    FROM production_pulse.firmware_update_targets t
                    JOIN production_pulse.firmware_update_jobs j ON j.id = t.job_id
                    JOIN production_pulse.firmwares f ON f.id = j.firmware_id
                    WHERE j.branch = %s
                      AND j.status IN ('running', 'completed', 'scheduled')
                      AND (%s::text IS NULL OR f.firmware_key = %s)
                    """,
                    (branch, firmware_key, firmware_key),
                )
                row = cur.fetchone()
        return {
            "total": total,
            "updated": int(row["updated"] or 0),
            "updating": int(row["updating"] or 0),
            "failed": int(row["failed"] or 0),
        }

    def find_authorized_target_for_device(self, device_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT t.*,
                           f.version AS firmware_version,
                           f.artifact_path,
                           f.artifact_sha256,
                           f.artifact_size_bytes,
                           f.firmware_key,
                           f.driver_key,
                           f.id AS firmware_id
                    FROM production_pulse.firmware_update_targets t
                    JOIN production_pulse.firmware_update_jobs j ON j.id = t.job_id
                    JOIN production_pulse.firmwares f ON f.id = j.firmware_id
                    WHERE t.device_id = %s
                      AND t.status IN ('authorized', 'downloading', 'applying')
                      AND j.status = 'running'
                    ORDER BY t.authorized_at DESC NULLS LAST, t.created_at DESC
                    LIMIT 1
                    """,
                    (device_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def get_target_by_artifact_token(self, token: str) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT t.*,
                           f.artifact_path,
                           f.artifact_sha256,
                           f.artifact_size_bytes,
                           f.version AS firmware_version
                    FROM production_pulse.firmware_update_targets t
                    JOIN production_pulse.firmware_update_jobs j ON j.id = t.job_id
                    JOIN production_pulse.firmwares f ON f.id = j.firmware_id
                    WHERE t.artifact_token = %s
                    """,
                    (token,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def get_target_by_id_for_device(
        self, target_id: UUID, device_id: UUID
    ) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_TARGET_COLUMNS}
                    FROM production_pulse.firmware_update_targets
                    WHERE id = %s AND device_id = %s
                    """,
                    (target_id, device_id),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def update_target(
        self,
        target_id: UUID,
        *,
        status: str | None = None,
        error_code: str | None = None,
        artifact_token: str | None = None,
        artifact_token_expires_at: datetime | None = None,
        clear_artifact_token: bool = False,
        touch_started: bool = False,
        touch_finished: bool = False,
        bytes_received: int | None = None,
        bytes_total: int | None = None,
        progress_percent: int | None = None,
        clear_progress: bool = False,
        touch_activity: bool = True,
    ) -> dict[str, Any]:
        # Token-only OTA check must not renew the stale lease (touch_activity=False).
        sets: list[str] = ["updated_at = NOW()"] if touch_activity else []
        params: list[Any] = []
        if status is not None:
            sets.append("status = %s")
            params.append(status)
        if error_code is not None:
            sets.append("error_code = %s")
            params.append(error_code)
        if artifact_token is not None:
            sets.append("artifact_token = %s")
            params.append(artifact_token)
        if artifact_token_expires_at is not None:
            sets.append("artifact_token_expires_at = %s")
            params.append(artifact_token_expires_at)
        if clear_artifact_token:
            sets.append("artifact_token = NULL")
            sets.append("artifact_token_expires_at = NULL")
        if touch_started:
            sets.append("started_at = COALESCE(started_at, NOW())")
        if touch_finished:
            sets.append("finished_at = NOW()")
        if clear_progress:
            sets.append("bytes_received = NULL")
            sets.append("bytes_total = NULL")
            sets.append("progress_percent = NULL")
        else:
            if bytes_received is not None:
                sets.append("bytes_received = %s")
                params.append(int(bytes_received))
            if bytes_total is not None:
                sets.append("bytes_total = %s")
                params.append(int(bytes_total))
            if progress_percent is not None:
                sets.append("progress_percent = %s")
                params.append(max(0, min(100, int(progress_percent))))
        if not sets:
            # No-op update still returns current row (e.g. touch_activity=False with no fields).
            sets.append("id = id")
        params.append(target_id)
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.firmware_update_targets
                    SET {", ".join(sets)}
                    WHERE id = %s
                    RETURNING {_TARGET_COLUMNS}
                    """,
                    params,
                )
                row = cur.fetchone()
            conn.commit()
            if row is None:
                raise FirmwareJobNotFoundError(str(target_id))
            return dict(row)

    def find_status_target_for_device(self, device_id: UUID) -> dict[str, Any] | None:
        """Open target if any, else the most recently updated target for the device."""
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT t.*,
                           f.firmware_key,
                           f.version AS firmware_version,
                           j.status AS job_status
                    FROM production_pulse.firmware_update_targets t
                    JOIN production_pulse.firmware_update_jobs j ON j.id = t.job_id
                    JOIN production_pulse.firmwares f ON f.id = j.firmware_id
                    WHERE t.device_id = %s
                    ORDER BY
                      CASE WHEN t.status IN ('pending', 'authorized', 'downloading', 'applying')
                           THEN 0 ELSE 1 END,
                      t.updated_at DESC
                    LIMIT 1
                    """,
                    (device_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def find_open_target_for_device(self, device_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_TARGET_COLUMNS}
                    FROM production_pulse.firmware_update_targets
                    WHERE device_id = %s
                      AND status = ANY(%s)
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (device_id, list(_OPEN_TARGET_STATUSES)),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_stale_open_targets(self, stale_before: datetime) -> list[dict[str, Any]]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_TARGET_COLUMNS}
                    FROM production_pulse.firmware_update_targets
                    WHERE status = ANY(%s)
                      AND updated_at < %s
                    ORDER BY updated_at ASC
                    """,
                    (list(_OPEN_TARGET_STATUSES), stale_before),
                )
                return [dict(row) for row in cur.fetchall()]

    def list_open_targets_for_reconcile(self) -> list[dict[str, Any]]:
        """Open targets whose device already reports installed_firmware_version = to_version."""
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_TARGET_COLUMNS}
                    FROM production_pulse.firmware_update_targets t
                    JOIN production_pulse.devices d ON d.id = t.device_id
                    WHERE t.status = ANY(%s)
                      AND d.installed_firmware_version IS NOT NULL
                      AND d.installed_firmware_version = t.to_version
                    ORDER BY t.updated_at ASC
                    """,
                    (list(_OPEN_TARGET_STATUSES),),
                )
                return [dict(row) for row in cur.fetchall()]
