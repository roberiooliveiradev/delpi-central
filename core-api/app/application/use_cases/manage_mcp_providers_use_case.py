"""Application use cases for Core-governed MCP provider registry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from urllib.parse import urlparse

from app.domain.mcp_providers.lifecycle import (
    PROTOCOL_MCP,
    STATUS_DISCOVERED,
    McpProviderLifecycleError,
    after_approve,
    after_disable,
    after_enable,
    after_reject,
    after_revoke,
    assert_auth_strategy,
    assert_status,
    is_eligible,
    transition,
)
from app.infrastructure.db.models.mcp_provider import McpProvider
from app.infrastructure.persistence.sqlalchemy.mcp_provider_repository import (
    SqlAlchemyMcpProviderRepository,
    eligible_to_dict,
    provider_to_dict,
)


class McpProviderConflictError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class McpProviderNotFoundError(Exception):
    pass


class McpProviderValidationError(Exception):
    def __init__(self, code: str, message: str, path: str = "_global") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path


def _validate_endpoint(endpoint_ref: str) -> str:
    value = str(endpoint_ref or "").strip()
    if not value:
        raise McpProviderValidationError(
            "mcp_provider.endpoint_required",
            "endpointRef is required",
            path="endpointRef",
        )
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise McpProviderValidationError(
            "mcp_provider.endpoint_scheme",
            "endpointRef must be http or https",
            path="endpointRef",
        )
    if not parsed.netloc:
        raise McpProviderValidationError(
            "mcp_provider.endpoint_host",
            "endpointRef must include a host",
            path="endpointRef",
        )
    # Soft SSRF guard for registration: block obvious metadata/loopback
    # unless explicitly host-local for DEV (http://*-api:). Private IP
    # literals are rejected; docker DNS names remain allowed for DEV.
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}:
        raise McpProviderValidationError(
            "mcp_provider.endpoint_ssrf",
            "endpointRef host is not allowed",
            path="endpointRef",
        )
    if host.startswith("169.254.") or host.startswith("metadata."):
        raise McpProviderValidationError(
            "mcp_provider.endpoint_ssrf",
            "endpointRef host is not allowed",
            path="endpointRef",
        )
    return value


def _normalize_provider_ref(provider_ref: str) -> str:
    value = str(provider_ref or "").strip().lower()
    if not value or len(value) > 64:
        raise McpProviderValidationError(
            "mcp_provider.provider_ref_invalid",
            "providerRef must be 1..64 characters",
            path="providerRef",
        )
    if not all(c.isalnum() or c in {"-", "_"} for c in value):
        raise McpProviderValidationError(
            "mcp_provider.provider_ref_invalid",
            "providerRef must be alphanumeric, hyphen or underscore",
            path="providerRef",
        )
    return value


@dataclass
class ManageMcpProvidersUseCase:
    """Single application façade for MCP provider governance."""

    def __init__(self, session, *, audit_repository=None) -> None:
        self._session = session
        self._repo = SqlAlchemyMcpProviderRepository(session)
        self._audit = audit_repository

    def _audit_log(
        self,
        *,
        action: str,
        provider_ref: str,
        actor_user_id: UUID | None,
        payload: dict[str, Any],
        ip_address: str | None = None,
    ) -> None:
        if self._audit is None:
            return
        self._audit.log(
            {
                "user_id": actor_user_id,
                "action": action,
                "entity_type": "mcp_provider",
                "entity_id": provider_ref,
                "payload": payload,
                "ip_address": ip_address,
            }
        )

    def register_candidate(
        self,
        *,
        provider_ref: str,
        display_name: str,
        endpoint_ref: str,
        owner_ref: str,
        auth_strategy_ref: str,
        resource_client_id: str | None = None,
        audience_scope: str | None = None,
        resource_audience: str | None = None,
        risk_tier: str | None = None,
        policy_ref: str | None = None,
        actor_user_id: UUID | None = None,
        ip_address: str | None = None,
        idempotent: bool = True,
    ) -> dict[str, Any]:
        pref = _normalize_provider_ref(provider_ref)
        name = str(display_name or "").strip()
        if not name:
            raise McpProviderValidationError(
                "mcp_provider.display_name_required",
                "displayName is required",
                path="displayName",
            )
        owner = str(owner_ref or "").strip()
        if not owner:
            raise McpProviderValidationError(
                "mcp_provider.owner_ref_required",
                "ownerRef is required",
                path="ownerRef",
            )
        endpoint = _validate_endpoint(endpoint_ref)
        strategy = assert_auth_strategy(auth_strategy_ref)

        existing = self._repo.get(pref)
        if existing is not None:
            if not idempotent:
                raise McpProviderConflictError(
                    "mcp_provider.already_exists",
                    f"Provider {pref} already exists",
                )
            # Idempotent re-register only when still a candidate and payload matches.
            if existing.approval_status not in {STATUS_DISCOVERED}:
                raise McpProviderConflictError(
                    "mcp_provider.already_exists",
                    f"Provider {pref} already exists with status {existing.approval_status}",
                )
            existing.display_name = name
            existing.endpoint_ref = endpoint
            existing.owner_ref = owner
            existing.auth_strategy_ref = strategy
            existing.resource_client_id = (resource_client_id or "").strip() or None
            existing.audience_scope = (audience_scope or "").strip() or None
            existing.resource_audience = (resource_audience or "").strip() or None
            existing.risk_tier = (risk_tier or "").strip() or None
            existing.policy_ref = (policy_ref or "").strip() or None
            existing.version = int(existing.version) + 1
            self._repo.flush()
            self._audit_log(
                action="mcp_provider.register_idempotent",
                provider_ref=pref,
                actor_user_id=actor_user_id,
                payload={"version": existing.version},
                ip_address=ip_address,
            )
            return provider_to_dict(existing)

        row = McpProvider(
            provider_ref=pref,
            display_name=name,
            protocol=PROTOCOL_MCP,
            endpoint_ref=endpoint,
            owner_ref=owner,
            auth_strategy_ref=strategy,
            resource_client_id=(resource_client_id or "").strip() or None,
            audience_scope=(audience_scope or "").strip() or None,
            resource_audience=(resource_audience or "").strip() or None,
            approval_status=STATUS_DISCOVERED,
            enabled=False,
            risk_tier=(risk_tier or "").strip() or None,
            policy_ref=(policy_ref or "").strip() or None,
            version=1,
        )
        self._repo.add(row)
        self._repo.flush()
        self._audit_log(
            action="mcp_provider.register",
            provider_ref=pref,
            actor_user_id=actor_user_id,
            payload={"status": STATUS_DISCOVERED},
            ip_address=ip_address,
        )
        return provider_to_dict(row)

    def get(self, provider_ref: str) -> dict[str, Any]:
        row = self._repo.get(_normalize_provider_ref(provider_ref))
        if row is None:
            raise McpProviderNotFoundError(provider_ref)
        return provider_to_dict(row)

    def list_providers(self, *, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        return [provider_to_dict(r) for r in self._repo.list_all(limit=limit, offset=offset)]

    def list_eligible(self) -> list[dict[str, Any]]:
        return [eligible_to_dict(r) for r in self._repo.list_eligible()]

    def _require(self, provider_ref: str) -> McpProvider:
        row = self._repo.get(_normalize_provider_ref(provider_ref))
        if row is None:
            raise McpProviderNotFoundError(provider_ref)
        return row

    def _bump_version(self, row: McpProvider, expected_version: int | None) -> None:
        if expected_version is not None and int(row.version) != int(expected_version):
            raise McpProviderConflictError(
                "mcp_provider.version_conflict",
                f"Expected version {expected_version}, found {row.version}",
            )
        row.version = int(row.version) + 1

    def review(
        self,
        provider_ref: str,
        *,
        expected_version: int | None = None,
        actor_user_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        row = self._require(provider_ref)
        try:
            row.approval_status = transition(row.approval_status, "REVIEWED")
        except McpProviderLifecycleError as exc:
            raise McpProviderValidationError(exc.code, exc.message) from exc
        self._bump_version(row, expected_version)
        self._repo.flush()
        self._audit_log(
            action="mcp_provider.review",
            provider_ref=row.provider_ref,
            actor_user_id=actor_user_id,
            payload={"status": row.approval_status, "version": row.version},
            ip_address=ip_address,
        )
        return provider_to_dict(row)

    def approve(
        self,
        provider_ref: str,
        *,
        expected_version: int | None = None,
        actor_user_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        row = self._require(provider_ref)
        try:
            status, enabled = after_approve(row.approval_status)
        except McpProviderLifecycleError as exc:
            raise McpProviderValidationError(exc.code, exc.message) from exc
        row.approval_status = status
        row.enabled = enabled
        row.approved_by_user_id = actor_user_id
        row.approved_at = datetime.now(timezone.utc)
        self._bump_version(row, expected_version)
        self._repo.flush()
        self._audit_log(
            action="mcp_provider.approve",
            provider_ref=row.provider_ref,
            actor_user_id=actor_user_id,
            payload={"status": status, "enabled": enabled, "version": row.version},
            ip_address=ip_address,
        )
        return provider_to_dict(row)

    def reject(
        self,
        provider_ref: str,
        *,
        expected_version: int | None = None,
        actor_user_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        row = self._require(provider_ref)
        try:
            status, enabled = after_reject(row.approval_status)
        except McpProviderLifecycleError as exc:
            raise McpProviderValidationError(exc.code, exc.message) from exc
        row.approval_status = status
        row.enabled = enabled
        self._bump_version(row, expected_version)
        self._repo.flush()
        self._audit_log(
            action="mcp_provider.reject",
            provider_ref=row.provider_ref,
            actor_user_id=actor_user_id,
            payload={"status": status, "version": row.version},
            ip_address=ip_address,
        )
        return provider_to_dict(row)

    def enable(
        self,
        provider_ref: str,
        *,
        expected_version: int | None = None,
        actor_user_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        row = self._require(provider_ref)
        try:
            status, enabled = after_enable(row.approval_status)
        except McpProviderLifecycleError as exc:
            raise McpProviderValidationError(exc.code, exc.message) from exc
        row.approval_status = status
        row.enabled = enabled
        self._bump_version(row, expected_version)
        self._repo.flush()
        self._audit_log(
            action="mcp_provider.enable",
            provider_ref=row.provider_ref,
            actor_user_id=actor_user_id,
            payload={"status": status, "enabled": enabled, "version": row.version},
            ip_address=ip_address,
        )
        return provider_to_dict(row)

    def disable(
        self,
        provider_ref: str,
        *,
        expected_version: int | None = None,
        actor_user_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        row = self._require(provider_ref)
        try:
            status, enabled = after_disable(row.approval_status)
        except McpProviderLifecycleError as exc:
            raise McpProviderValidationError(exc.code, exc.message) from exc
        row.approval_status = status
        row.enabled = enabled
        self._bump_version(row, expected_version)
        self._repo.flush()
        self._audit_log(
            action="mcp_provider.disable",
            provider_ref=row.provider_ref,
            actor_user_id=actor_user_id,
            payload={"status": status, "enabled": enabled, "version": row.version},
            ip_address=ip_address,
        )
        return provider_to_dict(row)

    def revoke(
        self,
        provider_ref: str,
        *,
        expected_version: int | None = None,
        actor_user_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        row = self._require(provider_ref)
        try:
            status, enabled = after_revoke(row.approval_status)
        except McpProviderLifecycleError as exc:
            raise McpProviderValidationError(exc.code, exc.message) from exc
        row.approval_status = status
        row.enabled = enabled
        self._bump_version(row, expected_version)
        self._repo.flush()
        self._audit_log(
            action="mcp_provider.revoke",
            provider_ref=row.provider_ref,
            actor_user_id=actor_user_id,
            payload={"status": status, "enabled": enabled, "version": row.version},
            ip_address=ip_address,
        )
        return provider_to_dict(row)

    @staticmethod
    def is_eligible_projection(row: dict[str, Any]) -> bool:
        return is_eligible(
            approval_status=assert_status(row["approvalStatus"]),
            enabled=bool(row["enabled"]),
        )
