"""Use-case tests for Core MCP provider registry (sqlite in-memory)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.use_cases.manage_mcp_providers_use_case import (
    ManageMcpProvidersUseCase,
    McpProviderConflictError,
    McpProviderValidationError,
)
from app.infrastructure.db.models.mcp_provider import McpProvider


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _fk(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    McpProvider.__table__.create(bind=engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    try:
        yield sess
    finally:
        sess.close()
        engine.dispose()


def _register(uc: ManageMcpProvidersUseCase, ref: str = "davi"):
    return uc.register_candidate(
        provider_ref=ref,
        display_name=ref.upper(),
        endpoint_ref=f"http://{ref}-api:8000/mcp",
        owner_ref=f"{ref}-api",
        auth_strategy_ref="KEYCLOAK_DELEGATED",
        resource_client_id=f"mcp-{ref}",
        audience_scope=f"mcp-audience-{ref}",
        resource_audience=f"https://minhadelpi.com.br/apps/{ref}-api/mcp",
    )


def test_register_and_idempotent(session):
    uc = ManageMcpProvidersUseCase(session)
    first = _register(uc)
    assert first["approvalStatus"] == "DISCOVERED"
    assert first["enabled"] is False
    second = _register(uc)
    assert second["providerRef"] == "davi"
    assert second["version"] == 2
    session.commit()


def test_duplicate_non_idempotent_conflict(session):
    uc = ManageMcpProvidersUseCase(session)
    _register(uc)
    with pytest.raises(McpProviderConflictError):
        uc.register_candidate(
            provider_ref="davi",
            display_name="DAVI",
            endpoint_ref="http://delpi-api-delpi:8000/mcp",
            owner_ref="api-delpi",
            auth_strategy_ref="KEYCLOAK_DELEGATED",
            idempotent=False,
        )


def test_lifecycle_approve_enable_revoke_and_eligibility(session):
    uc = ManageMcpProvidersUseCase(session)
    _register(uc, "teo")
    actor = uuid4()
    approved = uc.approve("teo", actor_user_id=actor)
    assert approved["approvalStatus"] == "APPROVED"
    assert approved["enabled"] is False
    assert uc.list_eligible() == []

    enabled = uc.enable("teo", expected_version=approved["version"])
    assert enabled["approvalStatus"] == "ACTIVE"
    assert enabled["enabled"] is True
    eligible = uc.list_eligible()
    assert len(eligible) == 1
    assert eligible[0]["providerRef"] == "teo"

    revoked = uc.revoke("teo", expected_version=enabled["version"])
    assert revoked["approvalStatus"] == "REVOKED"
    assert revoked["enabled"] is False
    assert uc.list_eligible() == []


def test_version_conflict(session):
    uc = ManageMcpProvidersUseCase(session)
    row = _register(uc, "vista")
    uc.approve("vista")
    with pytest.raises(McpProviderConflictError) as exc:
        uc.enable("vista", expected_version=row["version"])
    assert exc.value.code == "mcp_provider.version_conflict"


def test_ssrf_endpoint_rejected(session):
    uc = ManageMcpProvidersUseCase(session)
    with pytest.raises(McpProviderValidationError) as exc:
        uc.register_candidate(
            provider_ref="evil",
            display_name="Evil",
            endpoint_ref="http://127.0.0.1/mcp",
            owner_ref="evil",
            auth_strategy_ref="KEYCLOAK_DELEGATED",
        )
    assert exc.value.code == "mcp_provider.endpoint_ssrf"


def test_illegal_enable_before_approve(session):
    uc = ManageMcpProvidersUseCase(session)
    _register(uc, "caio")
    with pytest.raises(McpProviderValidationError):
        uc.enable("caio")


def test_seed_seven_parity_helpers(session):
    """Mirrors DEV seed: three enabled, four approved-but-disabled."""
    import importlib.util
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2] / "scripts" / "seed_mcp_providers_dev.py"
    )
    spec = importlib.util.spec_from_file_location("seed_mcp_providers_dev", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    stats = mod.seed(session)
    assert stats["created"] == 7
    uc = ManageMcpProvidersUseCase(session)
    items = {i["providerRef"]: i for i in uc.list_providers(limit=20)}
    assert set(items) == {s["provider_ref"] for s in mod.DEV_SPECIALISTS}
    eligible_refs = {i["providerRef"] for i in uc.list_eligible()}
    assert eligible_refs == {"davi", "teo", "vista"}
    for ref in ("caio", "clara", "suri", "eva"):
        assert items[ref]["enabled"] is False
    stats2 = mod.seed(session)
    assert stats2["created"] == 0
    assert len(uc.list_eligible()) == 3
