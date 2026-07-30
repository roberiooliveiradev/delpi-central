from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from cec_app.application.security import cec_permissions as perms
from cec_app.core.serialize import row_to_json, rows_to_json
from cec_app.infrastructure.persistence.repositories.member_repository import (
    LEADERSHIP_ROLES,
    MEMBER_ROLES,
    MemberRepository,
)


class MemberService:
    def __init__(self) -> None:
        self.repo = MemberRepository()

    def _actor_id(self, user) -> str:
        user_id = str(getattr(user, "id", None) or getattr(user, "sub", None) or "")
        if not user_id:
            raise PermissionError("Usuário não identificado.")
        try:
            UUID(user_id)
        except ValueError as exc:
            raise PermissionError("Identificador de usuário inválido.") from exc
        return user_id

    def _parse_uuid(self, value: str, *, field: str) -> str:
        try:
            return str(UUID(str(value).strip()))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} inválido.") from exc

    def _parse_date(self, value: str | None, *, field: str, required: bool = True) -> str | None:
        raw = (value or "").strip()
        if not raw:
            if required:
                raise ValueError(f"Informe {field}.")
            return None
        try:
            return date.fromisoformat(raw).isoformat()
        except ValueError as exc:
            raise ValueError(f"{field} inválida. Use o formato AAAA-MM-DD.") from exc

    def _validate_period(self, start: str, end: str | None) -> None:
        if end and end < start:
            raise ValueError("A data de fim do mandato não pode ser anterior ao início.")

    def _validate_role(self, role: str) -> str:
        normalized = (role or "").strip()
        if normalized not in MEMBER_ROLES:
            raise ValueError("Cargo inválido para membro do Comitê.")
        return normalized

    def list_members(
        self,
        user,
        *,
        active_on: str | None = None,
        include_inactive: bool = False,
        unit_code: str | None = None,
    ) -> list[dict[str, Any]]:
        _ = unit_code
        perms.require_view(user)
        on_date = None
        if active_on:
            on_date = self._parse_date(active_on, field="a data de vigência")
        rows = self.repo.list_members(
            active_on=on_date,
            include_inactive=include_inactive,
        )
        return rows_to_json(rows)

    def create_member(self, user, payload: dict[str, Any]) -> dict[str, Any]:
        actor = self._actor_id(user)
        perms.require_manage(user)

        user_id = self._parse_uuid(str(payload.get("user_id") or ""), field="user_id")
        display_name = str(payload.get("display_name") or "").strip()
        if not display_name:
            raise ValueError("Informe o nome do membro.")
        if len(display_name) > 200:
            raise ValueError("Nome do membro excede 200 caracteres.")

        role = self._validate_role(str(payload.get("role") or ""))
        mandate_start = self._parse_date(
            str(payload.get("mandate_start") or ""), field="o início do mandato"
        )
        mandate_end = self._parse_date(
            payload.get("mandate_end"),
            field="o fim do mandato",
            required=False,
        )
        self._validate_period(mandate_start or "", mandate_end)

        sort_order = int(payload.get("sort_order") or 0)
        if sort_order < 0:
            raise ValueError("Ordem inválida.")

        if self.repo.find_active_by_user(user_id=user_id):
            raise ValueError(
                "Já existe um membro ativo com este usuário. "
                "Encerre o mandato atual antes de cadastrar novamente."
            )

        if role in LEADERSHIP_ROLES:
            conflict_role = self.repo.find_active_leadership(role=role)
            if conflict_role:
                raise ValueError(
                    f"Já existe um ocupante ativo para o cargo «{role}». "
                    "Encerre o mandato atual antes de indicar outro."
                )

        row = self.repo.create_member(
            user_id=user_id,
            display_name=display_name,
            role=role,
            mandate_start=mandate_start or "",
            mandate_end=mandate_end,
            sort_order=sort_order,
            actor_user_id=actor,
        )
        return row_to_json(row) or {}

    def update_member(self, user, member_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        actor = self._actor_id(user)
        perms.require_manage(user)
        current = self.repo.get_member(member_id)
        if not current:
            raise LookupError("Membro não encontrado.")

        fields: dict[str, Any] = {}
        if "display_name" in payload and payload["display_name"] is not None:
            name = str(payload["display_name"]).strip()
            if not name:
                raise ValueError("Informe o nome do membro.")
            fields["display_name"] = name
        if "role" in payload and payload["role"] is not None:
            fields["role"] = self._validate_role(str(payload["role"]))
        if "mandate_start" in payload and payload["mandate_start"] is not None:
            fields["mandate_start"] = self._parse_date(
                str(payload["mandate_start"]), field="o início do mandato"
            )
        if "mandate_end" in payload:
            fields["mandate_end"] = self._parse_date(
                payload.get("mandate_end"),
                field="o fim do mandato",
                required=False,
            )
        if "is_active" in payload and payload["is_active"] is not None:
            fields["is_active"] = bool(payload["is_active"])
        if "sort_order" in payload and payload["sort_order"] is not None:
            fields["sort_order"] = int(payload["sort_order"])

        start = str(fields.get("mandate_start") or current.get("mandate_start") or "")
        end = fields["mandate_end"] if "mandate_end" in fields else current.get("mandate_end")
        end_s = end.isoformat() if hasattr(end, "isoformat") else (str(end) if end else None)
        if start:
            self._validate_period(start[:10], end_s[:10] if end_s else None)

        role = str(fields.get("role") or current.get("role") or "")
        if role in LEADERSHIP_ROLES and fields.get("is_active", current.get("is_active")):
            conflict = self.repo.find_active_leadership(role=role, exclude_id=member_id)
            if conflict:
                raise ValueError(f"Já existe um ocupante ativo para o cargo «{role}».")

        if fields.get("is_active", current.get("is_active")):
            conflict_user = self.repo.find_active_by_user(
                user_id=str(current["user_id"]),
                exclude_id=member_id,
            )
            if conflict_user:
                raise ValueError("Já existe outro membro ativo com este usuário.")

        row = self.repo.update_member(
            member_id=member_id, fields=fields, actor_user_id=actor
        )
        return row_to_json(row) or {}

    def end_member(
        self, user, member_id: str, *, mandate_end: str | None = None
    ) -> dict[str, Any]:
        actor = self._actor_id(user)
        perms.require_manage(user)
        current = self.repo.get_member(member_id)
        if not current:
            raise LookupError("Membro não encontrado.")
        end = self._parse_date(mandate_end, field="o fim do mandato", required=False)
        if not end:
            end = date.today().isoformat()
        start = str(current.get("mandate_start") or "")[:10]
        self._validate_period(start, end)
        row = self.repo.update_member(
            member_id=member_id,
            fields={"is_active": False, "mandate_end": end},
            actor_user_id=actor,
        )
        return row_to_json(row) or {}

    def delete_member(self, user, member_id: str) -> dict[str, Any]:
        actor = self._actor_id(user)
        perms.require_manage(user)
        row = self.repo.soft_delete(member_id=member_id, actor_user_id=actor)
        return row_to_json(row) or {}
