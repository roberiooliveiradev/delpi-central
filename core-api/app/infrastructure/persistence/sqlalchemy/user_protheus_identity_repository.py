from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities.user_protheus_identity import (
    MAPPING_SOURCES,
    MAPPING_STATUSES,
    UserProtheusIdentity,
)
from app.domain.ports.user_protheus_identity_repository_port import (
    UserProtheusIdentityRepositoryPort,
)
from app.infrastructure.db.models.user_protheus_identity import (
    UserProtheusIdentity as UserProtheusIdentityModel,
)


class SqlAlchemyUserProtheusIdentityRepository(UserProtheusIdentityRepositoryPort):
    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_entity(row: UserProtheusIdentityModel) -> UserProtheusIdentity:
        return UserProtheusIdentity(
            user_id=row.user_id,
            protheus_user_id=row.protheus_user_id,
            protheus_user_code=row.protheus_user_code,
            mapping_status=row.mapping_status,
            mapping_source=row.mapping_source,
            verified=bool(row.verified),
            updated_by_user_id=row.updated_by_user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _normalize_protheus_user_id(value: str | None) -> str | None:
        if value is None:
            return None
        # Preserve leading zeros; only trim surrounding whitespace.
        normalized = str(value).strip()
        return normalized or None

    def get(self, user_id: UUID) -> UserProtheusIdentity | None:
        row = (
            self._session.query(UserProtheusIdentityModel)
            .filter_by(user_id=user_id)
            .first()
        )
        return self._to_entity(row) if row else None

    def get_by_protheus_user_id(
        self,
        protheus_user_id: str,
    ) -> UserProtheusIdentity | None:
        normalized = self._normalize_protheus_user_id(protheus_user_id)
        if not normalized:
            return None
        row = (
            self._session.query(UserProtheusIdentityModel)
            .filter(
                UserProtheusIdentityModel.mapping_status == "mapped",
                func.btrim(UserProtheusIdentityModel.protheus_user_id) == normalized,
            )
            .first()
        )
        return self._to_entity(row) if row else None

    def get_by_user_ids(
        self,
        user_ids: list[UUID],
    ) -> list[UserProtheusIdentity]:
        if not user_ids:
            return []
        rows = (
            self._session.query(UserProtheusIdentityModel)
            .filter(UserProtheusIdentityModel.user_id.in_(user_ids))
            .all()
        )
        return [self._to_entity(row) for row in rows]

    def upsert(
        self,
        *,
        user_id: UUID,
        protheus_user_id: str | None,
        protheus_user_code: str | None,
        mapping_status: str,
        mapping_source: str | None,
        verified: bool,
        updated_by_user_id: UUID | None,
    ) -> UserProtheusIdentity:
        status = (mapping_status or "").strip()
        if status not in MAPPING_STATUSES:
            raise ValueError(f"mapping_status inválido: {mapping_status}")

        source = (mapping_source or "").strip() or None
        if source is not None and source not in MAPPING_SOURCES:
            raise ValueError(f"mapping_source inválido: {mapping_source}")

        normalized_id = self._normalize_protheus_user_id(protheus_user_id)
        code = (
            str(protheus_user_code).strip()
            if protheus_user_code is not None and str(protheus_user_code).strip()
            else None
        )

        if status == "mapped" and normalized_id:
            conflict = (
                self._session.query(UserProtheusIdentityModel)
                .filter(
                    UserProtheusIdentityModel.mapping_status == "mapped",
                    func.btrim(UserProtheusIdentityModel.protheus_user_id)
                    == normalized_id,
                    UserProtheusIdentityModel.user_id != user_id,
                )
                .first()
            )
            if conflict:
                raise ValueError(
                    "protheus_user_id já associado a outro usuário Minha DELPI."
                )

        row = (
            self._session.query(UserProtheusIdentityModel)
            .filter_by(user_id=user_id)
            .first()
        )
        if row is None:
            row = UserProtheusIdentityModel(user_id=user_id)
            self._session.add(row)

        row.protheus_user_id = normalized_id
        row.protheus_user_code = code
        row.mapping_status = status
        row.mapping_source = source
        row.verified = bool(verified)
        row.updated_by_user_id = updated_by_user_id
        row.updated_at = datetime.now(timezone.utc)
        self._session.flush()
        return self._to_entity(row)

    def delete(self, user_id: UUID) -> None:
        self._session.query(UserProtheusIdentityModel).filter_by(
            user_id=user_id
        ).delete()
        self._session.flush()
