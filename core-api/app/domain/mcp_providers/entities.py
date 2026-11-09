"""Domain entity for governed MCP provider registrations (Core-owned)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class McpProviderRecord:
    provider_ref: str
    display_name: str
    protocol: str
    endpoint_ref: str
    owner_ref: str
    auth_strategy_ref: str
    approval_status: str
    enabled: bool
    version: int
    resource_client_id: str | None = None
    audience_scope: str | None = None
    resource_audience: str | None = None
    risk_tier: str | None = None
    policy_ref: str | None = None
    approved_by_user_id: UUID | None = None
    approved_at: datetime | None = None
    last_validated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def provider_record_to_dict(row: McpProviderRecord) -> dict:
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


def eligible_record_to_dict(row: McpProviderRecord) -> dict:
    """S2S projection — provider approval only, never user/org AuthZ."""
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
        # R1-RW05: explicit non-grant — callers must not treat this as
        # user/org connection or domain permission.
        "authorizationScope": "provider_approval_only",
    }
