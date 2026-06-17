"""Testes do builder generalista de metadados OpenAPI."""

from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder


def test_from_contract_commercial_rol_target() -> None:
    meta = OpenApiAgentMetadataBuilder.from_contract(
        "get_head_office_rol_target_pct",
        path="/commercial/head_office_rol_target_pct",
    )

    assert meta["operation_id"] == "get_head_office_rol_target_pct"
    assert "ROL" in meta["summary"] or "rol" in meta["summary"].lower()
    assert "Comercial" in meta["description"]
    assert meta["summary"]
    assert len(meta["description"]) > 40


def test_from_contract_hr_snapshot() -> None:
    meta = OpenApiAgentMetadataBuilder.from_contract(
        "get_hr_snapshot",
        path="/hr/snapshot",
    )

    assert meta["operation_id"] == "get_hr_snapshot"
    assert "RH" in meta["description"] or "rh" in meta["description"].lower()


def test_from_contract_unknown_operation_raises() -> None:
    try:
        OpenApiAgentMetadataBuilder.from_contract("unknown_operation_xyz")
    except KeyError as exc:
        assert "unknown_operation_xyz" in str(exc)
    else:
        raise AssertionError("expected KeyError")
