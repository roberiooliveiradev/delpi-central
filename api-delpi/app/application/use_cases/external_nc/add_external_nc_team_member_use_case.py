# app/application/use_cases/external_nc/add_external_nc_team_member_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.external_nc.add_external_nc_team_member_request import (
    AddExternalNcTeamMemberRequest,
)
from app.domain.entities.external_nc.external_nc_team_member import (
    ExternalNcTeamMember,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.external_nc.external_nc_team_member_repository import (
    ExternalNcTeamMemberRepositoryPort,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)


class AddExternalNcTeamMemberUseCase:
    def __init__(
        self,
        nonconformity_repository: ExternalNonconformityRepositoryPort,
        team_member_repository: ExternalNcTeamMemberRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._team_member_repository = team_member_repository
        self._audit_event_repository = audit_event_repository

    def execute(
        self,
        request: AddExternalNcTeamMemberRequest,
    ) -> ExternalNcTeamMember:
        self._validate_request(request)

        nc = self._nonconformity_repository.get_by_id(request.nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade externa não encontrada.")

        existing = self._team_member_repository.get_by_nonconformity_and_role(
            nc.id,
            request.user_id.strip(),
            request.role_in_case.strip(),
        )
        if existing is not None:
            raise ValueError("Membro já vinculado com esse papel no caso.")

        member = ExternalNcTeamMember(
            id=str(uuid4()),
            nonconformity_id=nc.id,
            user_id=request.user_id.strip(),
            role_in_case=request.role_in_case.strip(),
            joined_at=datetime.now(timezone.utc),
        )

        created = self._team_member_repository.create(member)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="external_nonconformity",
                entity_id=nc.id,
                event_type="team_member_added",
                actor_user_id=request.actor_user_id.strip(),
                payload_json={
                    "member_id": created.id,
                    "user_id": created.user_id,
                    "role_in_case": created.role_in_case,
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        return created

    def _validate_request(self, request: AddExternalNcTeamMemberRequest) -> None:
        if not request.nonconformity_id or not request.nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")
        if not request.user_id or not request.user_id.strip():
            raise ValueError("user_id é obrigatório.")
        if not request.role_in_case or not request.role_in_case.strip():
            raise ValueError("role_in_case é obrigatório.")
        if not request.actor_user_id or not request.actor_user_id.strip():
            raise ValueError("actor_user_id é obrigatório.")