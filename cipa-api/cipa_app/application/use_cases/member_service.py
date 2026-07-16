from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from cipa_app.application.security import cipa_permissions as perms
from cipa_app.core.serialize import row_to_json, rows_to_json
from cipa_app.infrastructure.persistence.repositories.member_repository import (
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
            raise ValueError("Cargo inválido para membro da CIPA.")
        return normalized

    def _to_payload(self, row: dict[str, Any] | None) -> dict[str, Any] | None:
        return row_to_json(row)

    def list_members(
        self,
        user,
        *,
        unit_code: str,
        active_on: str | None = None,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        code = perms.normalize_unit_code(unit_code)
        if not code:
            raise ValueError("Unidade inválida.")
        perms.assert_unit_action(user, "view", code)
        on_date = None
        if active_on:
            on_date = self._parse_date(active_on, field="a data de vigência")
        rows = self.repo.list_members(
            unit_code=code,
            active_on=on_date,
            include_inactive=include_inactive,
        )
        return rows_to_json(rows)

    def create_member(self, user, payload: dict[str, Any]) -> dict[str, Any]:
        actor = self._actor_id(user)
        code = perms.normalize_unit_code(str(payload.get("unit_code") or ""))
        if not code:
            raise ValueError("Unidade inválida.")
        perms.assert_unit_action(user, "create", code)

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

        conflict_user = self.repo.find_active_by_user(unit_code=code, user_id=user_id)
        if conflict_user:
            raise ValueError(
                "Já existe um membro ativo com este usuário nesta filial. "
                "Encerre o mandato atual antes de cadastrar novamente."
            )

        if role in LEADERSHIP_ROLES:
            conflict_role = self.repo.find_active_leadership(unit_code=code, role=role)
            if conflict_role:
                label = conflict_role.get("display_name") or "outro membro"
                raise ValueError(
                    f"Já existe um ocupante ativo para este cargo ({label}). "
                    "Encerre o mandato atual antes de atribuir o cargo."
                )

        row = self.repo.create_member(
            unit_code=code,
            user_id=user_id,
            display_name=display_name,
            role=role,
            mandate_start=mandate_start or date.today().isoformat(),
            mandate_end=mandate_end,
            sort_order=sort_order,
            actor_user_id=actor,
        )
        return self._to_payload(row) or {}

    def update_member(self, user, member_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        actor = self._actor_id(user)
        mid = self._parse_uuid(member_id, field="id do membro")
        current = self.repo.get_member(mid)
        if not current:
            raise LookupError("Membro não encontrado.")

        unit_code = str(current.get("unit_code") or "")
        perms.assert_unit_action(user, "edit", unit_code)

        fields: dict[str, Any] = {}
        if "display_name" in payload and payload.get("display_name") is not None:
            name = str(payload.get("display_name") or "").strip()
            if not name:
                raise ValueError("Informe o nome do membro.")
            if len(name) > 200:
                raise ValueError("Nome do membro excede 200 caracteres.")
            fields["display_name"] = name

        role = str(current.get("role") or "")
        if "role" in payload and payload.get("role") is not None:
            role = self._validate_role(str(payload.get("role") or ""))
            fields["role"] = role

        start = current.get("mandate_start")
        end = current.get("mandate_end")
        if "mandate_start" in payload and payload.get("mandate_start") is not None:
            start = self._parse_date(
                str(payload.get("mandate_start") or ""), field="o início do mandato"
            )
            fields["mandate_start"] = start
        if "mandate_end" in payload:
            end = self._parse_date(
                payload.get("mandate_end"),
                field="o fim do mandato",
                required=False,
            )
            fields["mandate_end"] = end

        start_s = start.isoformat() if isinstance(start, date) else str(start or "")
        end_s = end.isoformat() if isinstance(end, date) else (str(end) if end else None)
        if start_s:
            self._validate_period(start_s, end_s)

        if "is_active" in payload and payload.get("is_active") is not None:
            fields["is_active"] = bool(payload.get("is_active"))

        if "sort_order" in payload and payload.get("sort_order") is not None:
            sort_order = int(payload.get("sort_order"))
            if sort_order < 0:
                raise ValueError("Ordem inválida.")
            fields["sort_order"] = sort_order

        becoming_active = fields.get("is_active", current.get("is_active"))
        if becoming_active:
            conflict_user = self.repo.find_active_by_user(
                unit_code=unit_code,
                user_id=str(current.get("user_id")),
                exclude_id=mid,
            )
            if conflict_user:
                raise ValueError(
                    "Já existe outro membro ativo com este usuário nesta filial."
                )
            if role in LEADERSHIP_ROLES:
                conflict_role = self.repo.find_active_leadership(
                    unit_code=unit_code,
                    role=role,
                    exclude_id=mid,
                )
                if conflict_role:
                    label = conflict_role.get("display_name") or "outro membro"
                    raise ValueError(
                        f"Já existe um ocupante ativo para este cargo ({label})."
                    )

        row = self.repo.update_member(
            member_id=mid,
            fields=fields,
            actor_user_id=actor,
        )
        return self._to_payload(row) or {}

    def end_membership(
        self,
        user,
        member_id: str,
        *,
        mandate_end: str | None = None,
    ) -> dict[str, Any]:
        """Encerra participação (is_active=false) mantendo histórico."""
        end = mandate_end or date.today().isoformat()
        return self.update_member(
            user,
            member_id,
            {
                "is_active": False,
                "mandate_end": end,
            },
        )

    def soft_delete(self, user, member_id: str) -> dict[str, Any]:
        actor = self._actor_id(user)
        mid = self._parse_uuid(member_id, field="id do membro")
        current = self.repo.get_member(mid)
        if not current:
            raise LookupError("Membro não encontrado.")
        perms.assert_unit_action(user, "delete", str(current.get("unit_code") or ""))
        row = self.repo.soft_delete(member_id=mid, actor_user_id=actor)
        return self._to_payload(row) or {}
