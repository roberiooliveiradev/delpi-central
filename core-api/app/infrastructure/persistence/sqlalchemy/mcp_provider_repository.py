"""SQLAlchemy persistence for Core MCP provider registry."""

from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy.orm import Session

from app.infrastructure.db.models.mcp_provider import McpProvider


class SqlAlchemyMcpProviderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, provider_ref: str) -> McpProvider | None:
        return self._session.get(McpProvider, provider_ref)

    def list_all(self, *, limit: int = 100, offset: int = 0) -> Sequence[McpProvider]:
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
        return (
            self._session.query(McpProvider)
            .order_by(McpProvider.provider_ref.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_eligible(self) -> Sequence[McpProvider]:
        from app.domain.mcp_providers.lifecycle import ELIGIBLE_STATUSES

        return (
            self._session.query(McpProvider)
            .filter(
                McpProvider.enabled.is_(True),
                McpProvider.approval_status.in_(tuple(ELIGIBLE_STATUSES)),
            )
            .order_by(McpProvider.provider_ref.asc())
            .all()
        )

    def add(self, row: McpProvider) -> McpProvider:
        self._session.add(row)
        return row

    def delete(self, row: McpProvider) -> None:
        self._session.delete(row)

    def flush(self) -> None:
        self._session.flush()


def provider_to_dict(row: McpProvider) -> dict[str, Any]:
    return {
        "providerRef": row.provider_ref,
        "displayName": row.display_name,
        "protocol": row.protocol,
        "endpointRef": row.endpoint_ref,
        "ownerRef": row.owner_ref,
        "authStrategyRef": row.auth_strategy_ref,
        "resourceClientId": row.resource_client_id,
        "audienceScope": row.audience_scope,
        "resourceAudience": row.resource_audience,
        "approvalStatus": row.approval_status,
        "enabled": bool(row.enabled),
        "riskTier": row.risk_tier,
        "policyRef": row.policy_ref,
        "version": int(row.version),
        "approvedByUserId": (
            str(row.approved_by_user_id) if row.approved_by_user_id else None
        ),
        "approvedAt": row.approved_at.isoformat() if row.approved_at else None,
        "lastValidatedAt": (
            row.last_validated_at.isoformat() if row.last_validated_at else None
        ),
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
    }


def eligible_to_dict(row: McpProvider) -> dict[str, Any]:
    """Consumer-facing projection — no admin-only fields beyond eligibility."""
    return {
        "providerRef": row.provider_ref,
        "displayName": row.display_name,
        "protocol": row.protocol,
        "endpointRef": row.endpoint_ref,
        "ownerRef": row.owner_ref,
        "authStrategyRef": row.auth_strategy_ref,
        "resourceClientId": row.resource_client_id,
        "audienceScope": row.audience_scope,
        "resourceAudience": row.resource_audience,
        "approvalStatus": row.approval_status,
        "enabled": bool(row.enabled),
        "version": int(row.version),
    }
