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
    id, firmware_key, driver_key, version, display_name, artifact_path, artifact_sha256,
    artifact_size_bytes, release_notes, min_compatible_version, published_at,
    created_by, created_at
"""


class PostgresFirmwareRepository:
    def list_firmwares(
        self,
        *,
        firmware_key: str | None = None,
        driver_key: str | None = None,
        published_only: bool = False,
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

    def create(
        self,
        *,
        firmware_key: str,
        driver_key: str,
        version: str,
        display_name: str,
        artifact_path: str,
        artifact_sha256: str,
        artifact_size_bytes: int,
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
                            firmware_key, driver_key, version, display_name, artifact_path,
                            artifact_sha256, artifact_size_bytes, release_notes,
                            min_compatible_version, published_at, created_by
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CASE WHEN %s THEN NOW() ELSE NULL END, %s)
                        RETURNING {_FIRMWARE_COLUMNS}
                        """,
                        (
                            firmware_key,
                            driver_key,
                            version,
                            display_name,
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
                    SET status = 'cancelled', finished_at = NOW(), updated_at = NOW()
                    WHERE job_id = %s
                      AND status IN ('pending', 'authorized', 'downloading', 'applying')
                    """,
                    (job_id,),
                )
            conn.commit()
            return dict(job)

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
    ) -> dict[str, Any]:
        sets = ["updated_at = NOW()"]
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
