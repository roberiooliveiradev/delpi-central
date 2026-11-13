"""G1-DOM: regras puras do inventario, sem rede, banco ou acesso remoto."""

import pytest

from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.workstations import (
    WORKSTATION_FIELD_NAMES,
    WorkstationFields,
    build_workstation_fields,
    format_workstation_code,
)


def payload(**overrides):
    data = {
        "name": "PC Engenharia",
        "hostname": "PC-ENG-01.DELPI.LOCAL.",
        "ip_address": "192.0.2.14",
        "unit_code": "01",
        "device_kind": "desktop",
        "department": "Engenharia",
        "location": "Predio principal",
        "responsible": "TI",
        "operating_system": "Windows 11 Pro",
        "administrative_status": "in_operation",
        "description": "Estacao de teste, sem dados pessoais.",
    }
    data.update(overrides)
    return data


def test_normalizes_workstation_and_keeps_remote_access_out_of_domain():
    value = build_workstation_fields(payload())
    assert isinstance(value, WorkstationFields)
    assert value.hostname == "pc-eng-01.delpi.local"
    assert value.ip_address == "192.0.2.14"
    assert value.unit_code == "01"
    assert value.device_kind == "desktop"
    assert value.responsible_user_id is None
    assert "remote_access_enabled" not in WORKSTATION_FIELD_NAMES
    assert "password" not in WORKSTATION_FIELD_NAMES
    assert value.as_dict()["description"] == "Estacao de teste, sem dados pessoais."


@pytest.mark.parametrize("kind", ["desktop", "notebook", "mini_pc", "workstation"])
def test_accepts_supported_device_kinds(kind):
    assert build_workstation_fields(payload(device_kind=kind)).device_kind == kind


@pytest.mark.parametrize("field,value", [
    ("name", ""),
    ("hostname", "host@invalido"),
    ("ip_address", "999.1.1.1"),
    ("unit_code", "03"),
    ("device_kind", "server"),
    ("administrative_status", "unknown"),
    ("department", "d" * 121),
])
def test_invalid_fields_fail_closed(field, value):
    with pytest.raises(ValidationError) as exc:
        build_workstation_fields(payload(**{field: value}))
    assert field in exc.value.details["fields"]


@pytest.mark.parametrize("field", ["name", "operating_system", "department", "location", "responsible", "description"])
def test_never_stores_labelled_credentials(field):
    with pytest.raises(ValidationError) as exc:
        build_workstation_fields(payload(**{field: "token=supersecretvalue"}))
    assert exc.value.code == "secret_not_allowed"


def test_empty_optional_fields_and_code():
    value = build_workstation_fields(payload(ip_address="", department="", description=""))
    assert value.ip_address is None
    assert value.department is None
    assert value.description is None
    assert format_workstation_code(1) == "PC-0001"
    assert format_workstation_code(10001) == "PC-10001"
    with pytest.raises(ValueError):
        format_workstation_code(0)
    with pytest.raises(ValueError):
        format_workstation_code(True)
