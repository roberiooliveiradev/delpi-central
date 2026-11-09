"""SQLAlchemy adapter for Core MCP provider registry."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.domain.mcp_providers.entities import McpProviderRecord
from app.domain.mcp_providers.lifecycle import ELIGIBLE_STATUSES
from app.infrastructure.db.models.mcp_provider import McpProvider


def _to_entity(row: McpProvider) -> McpProviderRecord:
    return McpProviderRecord(
        provider_ref=row.provider_ref,
        display_name=row.display_name,
        protocol=row.protocol,
        endpoint_ref=row.endpoint_ref,
        owner_ref=row.owner_ref,
        auth_strategy_ref=row.auth_strategy_ref,
        approval_status=row.approval_status,
        enabled=bool(row.enabled),
        version=int(row.version),
        resource_client_id=row.resource_client_id,
        audience_scope=row.audience_scope,
        resource_audience=row.resource_audience,
        risk_tier=row.risk_tier,
        policy_ref=row.policy_ref,
        approved_by_user_id=row.approved_by_user_id,
        approved_at=row.approved_at,
        last_validated_at=row.last_validated_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _apply(row: McpProvider, record: McpProviderRecord) -> None:
    row.display_name = record.display_name
    row.protocol = record.protocol
    row.endpoint_ref = record.endpoint_ref
    row.owner_ref = record.owner_ref
    row.auth_strategy_ref = record.auth_strategy_ref
    row.resource_client_id = record.resource_client_id
    row.audience_scope = record.audience_scope
    row.resource_audience = record.resource_audience
    row.approval_status = record.approval_status
    row.enabled = bool(record.enabled)
    row.risk_tier = record.risk_tier
    row.policy_ref = record.policy_ref
    row.version = int(record.version)
    row.approved_by_user_id = record.approved_by_user_id
    row.approved_at = record.approved_at
    row.last_validated_at = record.last_validated_at


class SqlAlchemyMcpProviderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, provider_ref: str) -> McpProviderRecord | None:
        row = (
            self._session.query(McpProvider)
            .filter_by(provider_ref=provider_ref)
            .one_or_none()
        )
        return _to_entity(row) if row is not None else None

    def list_all(
        self, *, limit: int = 100, offset: int = 0
    ) -> Sequence[McpProviderRecord]:
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
        rows = (
            self._session.query(McpProvider)
            .order_by(McpProvider.provider_ref.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_to_entity(r) for r in rows]

    def list_eligible(self) -> Sequence[McpProviderRecord]:
        rows = (
            self._session.query(McpProvider)
            .filter(
                McpProvider.enabled.is_(True),
                McpProvider.approval_status.in_(tuple(ELIGIBLE_STATUSES)),
            )
            .order_by(McpProvider.provider_ref.asc())
            .all()
        )
        return [_to_entity(r) for r in rows]

    def save(self, record: McpProviderRecord) -> McpProviderRecord:
        row = (
            self._session.query(McpProvider)
            .filter_by(provider_ref=record.provider_ref)
            .one_or_none()
        )
        if row is None:
            row = McpProvider(provider_ref=record.provider_ref)
            self._session.add(row)
        _apply(row, record)
        self._session.flush()
        return _to_entity(row)

    def flush(self) -> None:
        self._session.flush()
