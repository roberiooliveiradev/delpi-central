from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from psycopg.errors import ExclusionViolation

from app.domain.services.scheduling_recurrence_service import (
    RecurrenceValidationError,
    expand_recurrence_slots,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

CancelScope = Literal["occurrence", "future", "all"]
BookingDecision = Literal["confirmed", "rejected", "expired", "cancelled"]

_RESOURCE_RETURNING = """
    id,
    branch_code,
    name,
    resource_type,
    description,
    capacity,
    metadata,
    active,
    requires_approval,
    created_by_user_id,
    created_at,
    updated_at
"""

_BOOKING_SELECT = """
    SELECT b.id,
           b.resource_id,
           b.branch_code,
           b.title,
           b.notes,
           b.start_at,
           b.end_at,
           b.booked_by_user_id,
           b.booked_by_name,
           b.status,
           b.recurrence_series_id,
           b.decided_by_user_id,
           b.decided_by_name,
           b.decided_at,
           b.decision_reason,
           b.expires_at,
           b.created_at,
           b.updated_at,
           r.name AS resource_name,
           r.resource_type,
           r.requires_approval,
           rs.frequency AS recurrence_frequency
"""

_BOOKING_RETURNING = """
    id,
    resource_id,
    branch_code,
    title,
    notes,
    start_at,
    end_at,
    booked_by_user_id,
    booked_by_name,
    status,
    recurrence_series_id,
    decided_by_user_id,
    decided_by_name,
    decided_at,
    decision_reason,
    expires_at,
    created_at,
    updated_at
"""


class BookingConflictError(PluginsRepositoryError):
    """Reserva conflita com outro agendamento confirmado ou pendente."""


class PostgresSchedulingRepository(PluginBaseRepository):
    def list_resources(
        self,
        branch_code: str,
        *,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT {_RESOURCE_RETURNING}
              FROM scheduling.resources
             WHERE branch_code = %s
        """
        params: list[Any] = [branch_code]
        if active_only:
            query += " AND active = TRUE"
        query += " ORDER BY lower(name)"
        return self.fetch_all(query, tuple(params))

    def get_resource(self, resource_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            SELECT {_RESOURCE_RETURNING}
              FROM scheduling.resources
             WHERE id = %s
            """,
            (resource_id,),
        )

    def create_resource(
        self,
        *,
        branch_code: str,
        name: str,
        resource_type: str,
        description: str | None,
        capacity: int | None,
        metadata: dict[str, Any] | None,
        created_by_user_id: str | None,
        requires_approval: bool = False,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO scheduling.resources (
                branch_code,
                name,
                resource_type,
                description,
                capacity,
                metadata,
                created_by_user_id,
                requires_approval
            ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            RETURNING {_RESOURCE_RETURNING}
            """,
            (
                branch_code,
                name.strip(),
                resource_type,
                description,
                capacity,
                json.dumps(metadata or {}),
                created_by_user_id,
                requires_approval,
            ),
        )
        if not row:
            raise PluginsRepositoryError("Falha ao cadastrar recurso.")
        return row

    def update_resource(
        self,
        resource_id: str,
        *,
        name: str | None = None,
        resource_type: str | None = None,
        description: str | None = None,
        capacity: int | None = None,
        metadata: dict[str, Any] | None = None,
        active: bool | None = None,
        requires_approval: bool | None = None,
    ) -> dict[str, Any] | None:
        fields: list[str] = []
        params: list[Any] = []

        if name is not None:
            fields.append("name = %s")
            params.append(name.strip())
        if resource_type is not None:
            fields.append("resource_type = %s")
            params.append(resource_type)
        if description is not None:
            fields.append("description = %s")
            params.append(description)
        if capacity is not None:
            fields.append("capacity = %s")
            params.append(capacity)
        if metadata is not None:
            fields.append("metadata = %s::jsonb")
            params.append(json.dumps(metadata))
        if active is not None:
            fields.append("active = %s")
            params.append(active)
        if requires_approval is not None:
            fields.append("requires_approval = %s")
            params.append(requires_approval)

        if not fields:
            return self.get_resource(resource_id)

        fields.append("updated_at = NOW()")
        params.append(resource_id)

        return self.execute_returning_one(
            f"""
            UPDATE scheduling.resources
               SET {", ".join(fields)}
             WHERE id = %s
            RETURNING {_RESOURCE_RETURNING}
            """,
            tuple(params),
        )

    def list_bookings(
        self,
        branch_code: str,
        *,
        from_at: datetime,
        to_at: datetime,
        resource_id: str | None = None,
        statuses: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        query = f"""
            {_BOOKING_SELECT}
              FROM scheduling.bookings b
              JOIN scheduling.resources r ON r.id = b.resource_id
              LEFT JOIN scheduling.recurrence_series rs ON rs.id = b.recurrence_series_id
             WHERE b.branch_code = %s
               AND b.start_at < %s
               AND b.end_at > %s
        """
        params: list[Any] = [branch_code, to_at, from_at]
        if resource_id:
            query += " AND b.resource_id = %s"
            params.append(resource_id)
        active_statuses = statuses or ["confirmed", "pending"]
        query += " AND b.status = ANY(%s)"
        params.append(active_statuses)
        query += " ORDER BY b.start_at ASC"
        return self.fetch_all(query, tuple(params))

    def list_pending_bookings(
        self,
        branch_code: str,
        *,
        booked_by_user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = f"""
            {_BOOKING_SELECT}
              FROM scheduling.bookings b
              JOIN scheduling.resources r ON r.id = b.resource_id
              LEFT JOIN scheduling.recurrence_series rs ON rs.id = b.recurrence_series_id
             WHERE b.branch_code = %s
               AND b.status = 'pending'
        """
        params: list[Any] = [branch_code]
        if booked_by_user_id:
            query += " AND b.booked_by_user_id = %s"
            params.append(booked_by_user_id)
        query += " ORDER BY b.start_at ASC"
        return self.fetch_all(query, tuple(params))

    def get_booking(self, booking_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            {_BOOKING_SELECT}
              FROM scheduling.bookings b
              JOIN scheduling.resources r ON r.id = b.resource_id
              LEFT JOIN scheduling.recurrence_series rs ON rs.id = b.recurrence_series_id
             WHERE b.id = %s
            """,
            (booking_id,),
        )

    def has_booking_conflict(
        self,
        resource_id: str,
        start_at: datetime,
        end_at: datetime,
        *,
        exclude_booking_id: str | None = None,
    ) -> bool:
        query = """
            SELECT 1
              FROM scheduling.bookings
             WHERE resource_id = %s
               AND status IN ('confirmed', 'pending')
               AND start_at < %s
               AND end_at > %s
        """
        params: list[Any] = [resource_id, end_at, start_at]
        if exclude_booking_id:
            query += " AND id <> %s"
            params.append(exclude_booking_id)
        query += " LIMIT 1"
        return self.fetch_one(query, tuple(params)) is not None

    def expire_overdue_pending_bookings(
        self,
        *,
        branch_code: str | None = None,
    ) -> list[dict[str, Any]]:
        query = f"""
            {_BOOKING_SELECT}
              FROM scheduling.bookings b
              JOIN scheduling.resources r ON r.id = b.resource_id
              LEFT JOIN scheduling.recurrence_series rs ON rs.id = b.recurrence_series_id
             WHERE b.status = 'pending'
               AND b.expires_at IS NOT NULL
               AND b.expires_at < NOW()
        """
        params: list[Any] = []
        if branch_code:
            query += " AND b.branch_code = %s"
            params.append(branch_code)

        overdue = self.fetch_all(query, tuple(params))
        if not overdue:
            return []

        expired_ids = [str(row["id"]) for row in overdue]
        self.execute(
            """
            UPDATE scheduling.bookings
               SET status = 'expired',
                   decided_at = NOW(),
                   decision_reason = COALESCE(decision_reason, 'Prazo de aprovação expirado.'),
                   updated_at = NOW()
             WHERE id = ANY(%s)
               AND status = 'pending'
            """,
            (expired_ids,),
        )
        result: list[dict[str, Any]] = []
        for booking_id, previous in zip(expired_ids, overdue, strict=False):
            current = self.get_booking(booking_id)
            if current:
                result.append(current)
            else:
                previous = dict(previous)
                previous["status"] = "expired"
                result.append(previous)
        return result

    def create_booking(
        self,
        *,
        resource_id: str,
        branch_code: str,
        title: str,
        notes: str | None,
        start_at: datetime,
        end_at: datetime,
        booked_by_user_id: str,
        booked_by_name: str,
        status: str = "confirmed",
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        if self.has_booking_conflict(resource_id, start_at, end_at):
            raise BookingConflictError("Recurso já reservado neste horário.")

        try:
            row = self.execute_returning_one(
                f"""
                INSERT INTO scheduling.bookings (
                    resource_id,
                    branch_code,
                    title,
                    notes,
                    start_at,
                    end_at,
                    booked_by_user_id,
                    booked_by_name,
                    status,
                    expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING {_BOOKING_RETURNING}
                """,
                (
                    resource_id,
                    branch_code,
                    title.strip(),
                    notes,
                    start_at,
                    end_at,
                    booked_by_user_id,
                    booked_by_name,
                    status,
                    expires_at,
                ),
                auto_commit=False,
            )
            self.commit()
        except ExclusionViolation as exc:
            self.rollback()
            raise BookingConflictError("Recurso já reservado neste horário.") from exc
        except Exception:
            self.rollback()
            raise

        if not row:
            raise PluginsRepositoryError("Falha ao criar reserva.")
        return self.get_booking(str(row["id"])) or row

    def create_recurring_bookings(
        self,
        *,
        resource_id: str,
        branch_code: str,
        title: str,
        notes: str | None,
        start_at: datetime,
        end_at: datetime,
        booked_by_user_id: str,
        booked_by_name: str,
        frequency: str,
        until: datetime,
        interval: int = 1,
    ) -> dict[str, Any]:
        try:
            slots = expand_recurrence_slots(
                start_at=start_at,
                end_at=end_at,
                frequency=frequency,  # type: ignore[arg-type]
                until=until,
                interval=interval,
            )
        except RecurrenceValidationError as exc:
            raise PluginsRepositoryError(str(exc)) from exc

        resource = self.get_resource(resource_id)
        if not resource:
            raise PluginsRepositoryError("Recurso não encontrado.")

        created: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []

        try:
            series_row = self.execute_returning_one(
                """
                INSERT INTO scheduling.recurrence_series (
                    branch_code,
                    resource_id,
                    frequency,
                    interval_count,
                    series_start,
                    series_end,
                    title,
                    notes,
                    booked_by_user_id,
                    booked_by_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id,
                          branch_code,
                          resource_id,
                          frequency,
                          interval_count,
                          series_start,
                          series_end,
                          title,
                          notes,
                          booked_by_user_id,
                          booked_by_name,
                          created_at,
                          updated_at
                """,
                (
                    branch_code,
                    resource_id,
                    frequency,
                    interval,
                    start_at,
                    until,
                    title.strip(),
                    notes,
                    booked_by_user_id,
                    booked_by_name,
                ),
                auto_commit=False,
            )
            if not series_row:
                raise PluginsRepositoryError("Falha ao criar série recorrente.")

            series_id = str(series_row["id"])

            for slot_start, slot_end in slots:
                if self.has_booking_conflict(resource_id, slot_start, slot_end):
                    skipped.append(
                        {
                            "start_at": slot_start.isoformat(),
                            "end_at": slot_end.isoformat(),
                            "reason": "Recurso já reservado neste horário.",
                        }
                    )
                    continue

                try:
                    row = self.execute_returning_one(
                        f"""
                        INSERT INTO scheduling.bookings (
                            resource_id,
                            branch_code,
                            title,
                            notes,
                            start_at,
                            end_at,
                            booked_by_user_id,
                            booked_by_name,
                            recurrence_series_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING {_BOOKING_RETURNING}
                        """,
                        (
                            resource_id,
                            branch_code,
                            title.strip(),
                            notes,
                            slot_start,
                            slot_end,
                            booked_by_user_id,
                            booked_by_name,
                            series_id,
                        ),
                        auto_commit=False,
                    )
                except ExclusionViolation:
                    skipped.append(
                        {
                            "start_at": slot_start.isoformat(),
                            "end_at": slot_end.isoformat(),
                            "reason": "Recurso já reservado neste horário.",
                        }
                    )
                    continue

                if row:
                    full = self.get_booking(str(row["id"]))
                    created.append(full or row)

            if not created:
                self.rollback()
                raise BookingConflictError(
                    "Nenhuma ocorrência pôde ser reservada. Todos os horários estão ocupados."
                )

            self.commit()
        except BookingConflictError:
            self.rollback()
            raise
        except Exception:
            self.rollback()
            raise

        return {
            "series_id": series_id,
            "frequency": frequency,
            "created": created,
            "skipped": skipped,
            "total_created": len(created),
            "total_skipped": len(skipped),
        }

    def decide_booking(
        self,
        booking_id: str,
        *,
        status: BookingDecision,
        decided_by_user_id: str | None,
        decided_by_name: str | None,
        decision_reason: str | None = None,
    ) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            f"""
            UPDATE scheduling.bookings
               SET status = %s,
                   decided_by_user_id = %s,
                   decided_by_name = %s,
                   decided_at = NOW(),
                   decision_reason = %s,
                   expires_at = CASE WHEN %s = 'confirmed' THEN NULL ELSE expires_at END,
                   updated_at = NOW()
             WHERE id = %s
               AND status = 'pending'
            RETURNING {_BOOKING_RETURNING}
            """,
            (
                status,
                decided_by_user_id,
                decided_by_name,
                decision_reason,
                status,
                booking_id,
            ),
        )
        if not row:
            return None
        return self.get_booking(booking_id)

    def cancel_booking(
        self,
        booking_id: str,
        *,
        scope: CancelScope = "occurrence",
    ) -> dict[str, Any]:
        booking = self.get_booking(booking_id)
        if not booking:
            raise PluginsRepositoryError("Reserva não encontrada.")
        if booking.get("status") in {"cancelled", "rejected", "expired"}:
            raise PluginsRepositoryError("Reserva não pode ser cancelada neste status.")

        series_id = booking.get("recurrence_series_id")
        if not series_id or scope == "occurrence":
            row = self._cancel_single_booking(booking_id)
            if not row:
                raise PluginsRepositoryError("Não foi possível cancelar a reserva.")
            full = self.get_booking(booking_id) or row
            full["cancelled_count"] = 1
            return full

        if scope == "future":
            rows = self.fetch_all(
                """
                UPDATE scheduling.bookings
                   SET status = 'cancelled',
                       updated_at = NOW()
                 WHERE recurrence_series_id = %s
                   AND status IN ('confirmed', 'pending')
                   AND start_at >= %s
                RETURNING id
                """,
                (series_id, booking["start_at"]),
            )
        else:
            rows = self.fetch_all(
                """
                UPDATE scheduling.bookings
                   SET status = 'cancelled',
                       updated_at = NOW()
                 WHERE recurrence_series_id = %s
                   AND status IN ('confirmed', 'pending')
                RETURNING id
                """,
                (series_id,),
            )

        if not rows:
            raise PluginsRepositoryError("Não foi possível cancelar as reservas da série.")

        cancelled_count = len(rows)
        row = self.get_booking(booking_id) or booking
        row["cancelled_count"] = cancelled_count
        return row

    def _cancel_single_booking(self, booking_id: str) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""
            UPDATE scheduling.bookings
               SET status = 'cancelled',
                   updated_at = NOW()
             WHERE id = %s
               AND status IN ('confirmed', 'pending')
            RETURNING {_BOOKING_RETURNING}
            """,
            (booking_id,),
        )
