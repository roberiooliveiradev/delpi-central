#!/usr/bin/env python3
"""Idempotent DEV seed of the seven DELPI MCP specialists into Core.

Does NOT enable CAIO/CLARA/SURI/EVA by default (compose parity).
Does NOT write production. Safe to re-run.

Usage (from core-api with app context / DATABASE_URL):

    python scripts/seed_mcp_providers_dev.py
"""

from __future__ import annotations

import os
import sys

# Seven specialists — identity aligned with DÉLIA _SPECIALIST_IDENTITY
# and infra/scripts/delia_mcp_keycloak_state.py SPECIALISTS.
# enabled=True only for davi/teo/vista (compose defaults).
DEV_SPECIALISTS = (
    {
        "provider_ref": "davi",
        "display_name": "DAVI",
        "owner_ref": "api-delpi",
        "endpoint_ref": os.getenv(
            "SEED_MCP_DAVI_ENDPOINT",
            "http://delpi-api-delpi:8000/mcp",
        ),
        "resource_client_id": "mcp-api-delpi",
        "audience_scope": "mcp-audience-api-delpi",
        "resource_audience": "https://minhadelpi.com.br/apps/api-delpi/mcp",
        "enable": True,
    },
    {
        "provider_ref": "teo",
        "display_name": "TÉO",
        "owner_ref": "transformometro-api",
        "endpoint_ref": os.getenv(
            "SEED_MCP_TEO_ENDPOINT",
            "http://transformometro-api:8000/mcp",
        ),
        "resource_client_id": "mcp-transformometro",
        "audience_scope": "mcp-audience-transformometro",
        "resource_audience": "https://minhadelpi.com.br/apps/transformometro-api/mcp",
        "enable": True,
    },
    {
        "provider_ref": "vista",
        "display_name": "VISTA",
        "owner_ref": "tv-dashboard-api",
        "endpoint_ref": os.getenv(
            "SEED_MCP_VISTA_ENDPOINT",
            "http://tv-dashboard-api:8000/mcp",
        ),
        "resource_client_id": "mcp-tv-dashboard",
        "audience_scope": "mcp-audience-tv-dashboard",
        "resource_audience": "https://minhadelpi.com.br/apps/tv-dashboard-api/mcp",
        "enable": True,
    },
    {
        "provider_ref": "caio",
        "display_name": "CAIO",
        "owner_ref": "commercial-api",
        "endpoint_ref": os.getenv(
            "SEED_MCP_CAIO_ENDPOINT",
            "http://commercial-api:8000/mcp",
        ),
        "resource_client_id": "mcp-commercial",
        "audience_scope": "mcp-audience-caio",
        "resource_audience": "https://minhadelpi.com.br/apps/commercial-api/mcp",
        "enable": False,
    },
    {
        "provider_ref": "clara",
        "display_name": "CLARA",
        "owner_ref": "controllership-finance-api",
        "endpoint_ref": os.getenv(
            "SEED_MCP_CLARA_ENDPOINT",
            "http://controllership-finance-api:8000/mcp",
        ),
        "resource_client_id": "mcp-controllership-finance",
        "audience_scope": "mcp-audience-clara",
        "resource_audience": (
            "https://minhadelpi.com.br/apps/controllership-finance-api/mcp"
        ),
        "enable": False,
    },
    {
        "provider_ref": "suri",
        "display_name": "SURI",
        "owner_ref": "supplies-mcp",
        "endpoint_ref": os.getenv(
            "SEED_MCP_SURI_ENDPOINT",
            "http://supplies-api:8000/mcp",
        ),
        "resource_client_id": "mcp-supplies",
        "audience_scope": "mcp-audience-suri",
        "resource_audience": "https://minhadelpi.com.br/apps/supplies-api/mcp",
        "enable": False,
    },
    {
        "provider_ref": "eva",
        "display_name": "EVA",
        "owner_ref": "engineering-api",
        "endpoint_ref": os.getenv(
            "SEED_MCP_EVA_ENDPOINT",
            "http://engineering-api:8000/mcp",
        ),
        "resource_client_id": "mcp-engineering",
        "audience_scope": "mcp-audience-eva",
        "resource_audience": "https://minhadelpi.com.br/apps/engineering-api/mcp",
        "enable": False,
    },
)


def seed(session) -> dict[str, int]:
    from app.application.use_cases.manage_mcp_providers_use_case import (
        ManageMcpProvidersUseCase,
    )
    from app.domain.mcp_providers.lifecycle import (
        STATUS_APPROVED,
        STATUS_DISCOVERED,
    )
    from app.infrastructure.db.models.mcp_provider import McpProvider

    def _get(pref: str):
        return session.query(McpProvider).filter_by(provider_ref=pref).one_or_none()

    uc = ManageMcpProvidersUseCase(session)
    created = updated = enabled = skipped = 0

    for spec in DEV_SPECIALISTS:
        pref = spec["provider_ref"]
        existing = _get(pref)
        if existing is None:
            uc.register_candidate(
                provider_ref=pref,
                display_name=spec["display_name"],
                endpoint_ref=spec["endpoint_ref"],
                owner_ref=spec["owner_ref"],
                auth_strategy_ref="KEYCLOAK_DELEGATED",
                resource_client_id=spec["resource_client_id"],
                audience_scope=spec["audience_scope"],
                resource_audience=spec["resource_audience"],
                risk_tier="internal",
                policy_ref="delpi-internal-mcp",
                idempotent=True,
            )
            row = _get(pref)
            assert row is not None
            if row.approval_status == STATUS_DISCOVERED:
                row.approval_status = STATUS_APPROVED
                row.version = int(row.version) + 1
            if spec["enable"]:
                row.approval_status = "ACTIVE"
                row.enabled = True
                enabled += 1
            created += 1
        else:
            existing.display_name = spec["display_name"]
            existing.endpoint_ref = spec["endpoint_ref"]
            existing.owner_ref = spec["owner_ref"]
            existing.resource_client_id = spec["resource_client_id"]
            existing.audience_scope = spec["audience_scope"]
            existing.resource_audience = spec["resource_audience"]
            if existing.approval_status in {STATUS_DISCOVERED}:
                existing.approval_status = STATUS_APPROVED
            if spec["enable"] and existing.approval_status not in {
                "REVOKED",
                "DEPRECATED",
                "REJECTED",
            }:
                if not existing.enabled:
                    existing.approval_status = "ACTIVE"
                    existing.enabled = True
                    enabled += 1
            elif not spec["enable"]:
                skipped += 1
            updated += 1

    session.commit()
    return {
        "created": created,
        "updated": updated,
        "enabled_ops": enabled,
        "skipped": skipped,
    }


def main() -> int:
    # Ensure package imports resolve when run as script.
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)

    from app.create_app import create_app
    from app.extensions.db import db

    app = create_app()
    with app.app_context():
        stats = seed(db.session)
        print(f"[SEED mcp_providers] {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
