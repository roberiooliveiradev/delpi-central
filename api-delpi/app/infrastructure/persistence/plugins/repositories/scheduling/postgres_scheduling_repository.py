from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from psycopg.errors import ExclusionViolation

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)


class BookingConflictError(PluginsRepositoryError):
    """Reserva conflita com outro agendamento confirmado."""


class PostgresSchedulingRepository(PluginBaseRepository):
    def list_resources(
        self,
        branch_code: str,
        *,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT id,
                   branch_code,
                   name,
                   resource_type,
                   description,
                   capacity,
                   metadata,
                   active,
                   created_by_user_id,
                   created_at,
                   updated_at
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
            """
            SELECT id,
                   branch_code,
                   name,
                   resource_type,
                   description,
                   capacity,
                   metadata,
                   active,
                   created_by_user_id,
                   created_at,
                   updated_at
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
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO scheduling.resources (
                branch_code,
                name,
                resource_type,
                description,
                capacity,
                metadata,
                created_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
            RETURNING id,
                      branch_code,
                      name,
                      resource_type,
                      description,
                      capacity,
                      metadata,
                      active,
                      created_by_user_id,
                      created_at,
                      updated_at
            """,
            (
                branch_code,
                name.strip(),
                resource_type,
                description,
                capacity,
                json.dumps(metadata or {}),
                created_by_user_id,
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

        if not fields:
            return self.get_resource(resource_id)

        fields.append("updated_at = NOW()")
        params.append(resource_id)

        return self.execute_returning_one(
            f"""
            UPDATE scheduling.resources
               SET {", ".join(fields)}
             WHERE id = %s
            RETURNING id,
                      branch_code,
                      name,
                      resource_type,
                      description,
                      capacity,
                      metadata,
                      active,
                      created_by_user_id,
                      created_at,
                      updated_at
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
        include_cancelled: bool = False,
    ) -> list[dict[str, Any]]:
        query = """
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
                   b.created_at,
                   b.updated_at,
                   r.name AS resource_name,
                   r.resource_type
              FROM scheduling.bookings b
              JOIN scheduling.resources r ON r.id = b.resource_id
             WHERE b.branch_code = %s
               AND b.start_at < %s
               AND b.end_at > %s
        """
        params: list[Any] = [branch_code, to_at, from_at]
        if resource_id:
            query += " AND b.resource_id = %s"
            params.append(resource_id)
        if not include_cancelled:
            query += " AND b.status = 'confirmed'"
        query += " ORDER BY b.start_at ASC"
        return self.fetch_all(query, tuple(params))

    def get_booking(self, booking_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
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
                   b.created_at,
                   b.updated_at,
                   r.name AS resource_name,
                   r.resource_type
              FROM scheduling.bookings b
              JOIN scheduling.resources r ON r.id = b.resource_id
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
               AND status = 'confirmed'
               AND start_at < %s
               AND end_at > %s
        """
        params: list[Any] = [resource_id, end_at, start_at]
        if exclude_booking_id:
            query += " AND id <> %s"
            params.append(exclude_booking_id)
        query += " LIMIT 1"
        return self.fetch_one(query, tuple(params)) is not None

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
    ) -> dict[str, Any]:
        if self.has_booking_conflict(resource_id, start_at, end_at):
            raise BookingConflictError("Recurso já reservado neste horário.")

        try:
            row = self.execute_returning_one(
                """
                INSERT INTO scheduling.bookings (
                    resource_id,
                    branch_code,
                    title,
                    notes,
                    start_at,
                    end_at,
                    booked_by_user_id,
                    booked_by_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id,
                          resource_id,
                          branch_code,
                          title,
                          notes,
                          start_at,
                          end_at,
                          booked_by_user_id,
                          booked_by_name,
                          status,
                          created_at,
                          updated_at
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
        resource = self.get_resource(resource_id)
        if resource:
            row["resource_name"] = resource["name"]
            row["resource_type"] = resource["resource_type"]
        return row

    def cancel_booking(self, booking_id: str) -> dict[str, Any] | None:
        return self.execute_returning_one(
            """
            UPDATE scheduling.bookings
               SET status = 'cancelled',
                   updated_at = NOW()
             WHERE id = %s
               AND status = 'confirmed'
            RETURNING id,
                      resource_id,
                      branch_code,
                      title,
                      notes,
                      start_at,
                      end_at,
                      booked_by_user_id,
                      booked_by_name,
                      status,
                      created_at,
                      updated_at
            """,
            (booking_id,),
        )
