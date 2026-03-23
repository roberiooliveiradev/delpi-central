# app/application/use_cases/internal_nc/remove_internal_nc_team_member_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.internal_nc.remove_internal_nc_team_member_request import (
    RemoveInternalNcTeamMemberRequest,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.internal_nc.internal_nc_team_member_repository import (
    InternalNcTeamMemberRepositoryPort,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)


class RemoveInternalNcTeamMemberUseCase:
    def __init__(
        self,
        nonconformity_repository: InternalNonconformityRepositoryPort,
        team_member_repository: InternalNcTeamMemberRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._team_member_repository = team_member_repository
        self._audit_event_repository = audit_event_repository

    def execute(self, request: RemoveInternalNcTeamMemberRequest) -> None:
        if not request.nonconformity_id or not request.nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")
        if not request.member_id or not request.member_id.strip():
            raise ValueError("member_id é obrigatório.")
        if not request.actor_user_id or not request.actor_user_id.strip():
            raise ValueError("actor_user_id é obrigatório.")

        nc = self._nonconformity_repository.get_by_id(request.nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade interna não encontrada.")

        members = self._team_member_repository.list_by_nonconformity_id(nc.id)
        member = next((m for m in members if m.id == request.member_id.strip()), None)
        if member is None:
            raise ValueError("Membro da análise não encontrado.")

        self._team_member_repository.delete(member.id)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="internal_nonconformity",
                entity_id=nc.id,
                event_type="team_member_removed",
                actor_user_id=request.actor_user_id.strip(),
                payload_json={
                    "member_id": member.id,
                    "user_id": member.user_id,
                    "role_in_case": member.role_in_case,
                },
                created_at=datetime.now(timezone.utc),
            )
        )