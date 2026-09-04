"""SLA policies persistence (commercial.sla_policies)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

SLA_APPLIES_TO_VALUES = frozenset(
    {"task", "sample", "order_confirmation", "offer_stage"}
)

_COLUMNS = (
    "id, code, name, applies_to, duration_hours, calendar_code, active, "
    "created_at, updated_at"
)


class SlaPolicyValidationError(ValueError):
    """Invalid SLA policy payload."""


class SlaPolicyConflictError(ValueError):
    """Unique code conflict."""


class PostgresSlaPolicyRepository(PluginBaseRepository):
    def list_active(self) -> list[dict]:
        return self.list_policies(include_inactive=False)

    def list_policies(self, *, include_inactive: bool = False) -> list[dict]:
        if include_inactive:
            rows = self.fetch_all(
                f"""
                SELECT {_COLUMNS}
                  FROM commercial.sla_policies
                 ORDER BY active DESC, code ASC
                """,
            )
        else:
            rows = self.fetch_all(
                f"""
                SELECT {_COLUMNS}
                  FROM commercial.sla_policies
                 WHERE active = TRUE
                 ORDER BY code ASC
                """,
            )
        return [self._row_to_dict(row) for row in rows]

    def get_by_id(self, policy_id: str) -> dict | None:
        pid = self._normalize_uuid(policy_id)
        if not pid:
            return None
        row = self.fetch_one(
            f"""
            SELECT {_COLUMNS}
              FROM commercial.sla_policies
             WHERE id = %s
            """,
            (pid,),
        )
        return self._row_to_dict(row) if row else None

    def get_by_code(self, code: str) -> dict | None:
        normalized = (code or "").strip()
        if not normalized:
            return None
        row = self.fetch_one(
            f"""
            SELECT {_COLUMNS}
              FROM commercial.sla_policies
             WHERE code = %s
            """,
            (normalized,),
        )
        return self._row_to_dict(row) if row else None

    def create(
        self,
        *,
        code: str,
        name: str,
        applies_to: str,
        duration_hours: int,
        calendar_code: str | None = None,
        active: bool = True,
    ) -> dict:
        payload = self._validated_fields(
            code=code,
            name=name,
            applies_to=applies_to,
            duration_hours=duration_hours,
            calendar_code=calendar_code,
        )
        if self.get_by_code(payload["code"]) is not None:
            raise SlaPolicyConflictError(
                f"Já existe política de SLA com o código «{payload['code']}»."
            )
        try:
            row = self.execute_returning_one(
                f"""
                INSERT INTO commercial.sla_policies (
                    code, name, applies_to, duration_hours, calendar_code, active
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING {_COLUMNS}
                """,
                (
                    payload["code"],
                    payload["name"],
                    payload["applies_to"],
                    payload["duration_hours"],
                    payload["calendar_code"],
                    bool(active),
                ),
            )
        except PluginsRepositoryError as exc:
            if "sla_policies_code" in str(exc).lower() or "unique" in str(exc).lower():
                raise SlaPolicyConflictError(
                    f"Já existe política de SLA com o código «{payload['code']}»."
                ) from exc
            raise
        if row is None:
            raise PluginsRepositoryError("Falha ao criar política de SLA.")
        return self._row_to_dict(row)

    def update(
        self,
        policy_id: str,
        *,
        code: str | None = None,
        name: str | None = None,
        applies_to: str | None = None,
        duration_hours: int | None = None,
        calendar_code: str | None | object = ...,
        active: bool | None = None,
    ) -> dict | None:
        current = self.get_by_id(policy_id)
        if current is None:
            return None

        next_code = current["code"] if code is None else code
        next_name = current["name"] if name is None else name
        next_applies = current["appliesTo"] if applies_to is None else applies_to
        next_hours = (
            current["durationHours"] if duration_hours is None else duration_hours
        )
        if calendar_code is ...:
            next_calendar = current.get("calendarCode")
        else:
            next_calendar = calendar_code  # type: ignore[assignment]
        next_active = current["active"] if active is None else active

        payload = self._validated_fields(
            code=next_code,
            name=next_name,
            applies_to=next_applies,
            duration_hours=next_hours,
            calendar_code=next_calendar,
        )
        existing = self.get_by_code(payload["code"])
        if existing is not None and existing["id"] != current["id"]:
            raise SlaPolicyConflictError(
                f"Já existe política de SLA com o código «{payload['code']}»."
            )

        pid = self._normalize_uuid(policy_id)
        try:
            row = self.execute_returning_one(
                f"""
                UPDATE commercial.sla_policies
                   SET code = %s,
                       name = %s,
                       applies_to = %s,
                       duration_hours = %s,
                       calendar_code = %s,
                       active = %s,
                       updated_at = NOW()
                 WHERE id = %s
             RETURNING {_COLUMNS}
                """,
                (
                    payload["code"],
                    payload["name"],
                    payload["applies_to"],
                    payload["duration_hours"],
                    payload["calendar_code"],
                    bool(next_active),
                    pid,
                ),
            )
        except PluginsRepositoryError as exc:
            if "unique" in str(exc).lower():
                raise SlaPolicyConflictError(
                    f"Já existe política de SLA com o código «{payload['code']}»."
                ) from exc
            raise
        return self._row_to_dict(row) if row else None

    def deactivate(self, policy_id: str) -> dict | None:
        return self.update(policy_id, active=False)

    @staticmethod
    def _normalize_uuid(value: str | None) -> str | None:
        raw = (value or "").strip()
        if not raw:
            return None
        try:
            return str(UUID(raw))
        except ValueError:
            return None

    @staticmethod
    def _validated_fields(
        *,
        code: str,
        name: str,
        applies_to: str,
        duration_hours: int | float | str,
        calendar_code: str | None,
    ) -> dict[str, Any]:
        normalized_code = (code or "").strip()
        normalized_name = (name or "").strip()
        normalized_applies = (applies_to or "").strip().lower()
        if not normalized_code:
            raise SlaPolicyValidationError("Informe o código da política de SLA.")
        if not normalized_name:
            raise SlaPolicyValidationError("Informe o nome da política de SLA.")
        if normalized_applies not in SLA_APPLIES_TO_VALUES:
            raise SlaPolicyValidationError(
                "Aplica-se inválido. Use: task, sample, order_confirmation ou offer_stage."
            )
        try:
            hours = int(duration_hours)
        except (TypeError, ValueError) as exc:
            raise SlaPolicyValidationError(
                "Duração em horas deve ser um número inteiro positivo."
            ) from exc
        if hours <= 0:
            raise SlaPolicyValidationError(
                "Duração em horas deve ser um número inteiro positivo."
            )
        calendar = (calendar_code or "").strip() or None
        return {
            "code": normalized_code,
            "name": normalized_name,
            "applies_to": normalized_applies,
            "duration_hours": hours,
            "calendar_code": calendar,
        }

    @staticmethod
    def _row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "code": row["code"],
            "name": row["name"],
            "appliesTo": row["applies_to"],
            "durationHours": int(row["duration_hours"]),
            "calendarCode": row.get("calendar_code"),
            "active": bool(row["active"]),
        }
