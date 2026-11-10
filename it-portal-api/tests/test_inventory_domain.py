"""Regras de domínio de serviços, instâncias de banco e vínculos (E2A)."""

import pytest

from it_portal_app.domain.database_instances import build_database_fields, format_database_code
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.inventory_links import build_consumer_fields, build_hosting_fields
from it_portal_app.domain.it_services import build_service_fields, format_service_code

from tests.conftest import database_payload, service_payload

SERVER_ID = "4b6f1c1e-2f8a-4c3b-9d7e-0a1b2c3d4e5f"
SERVICE_ID = "7c1d2e3f-4a5b-4c6d-8e9f-0a1b2c3d4e5f"


def _fields_error(exc: pytest.ExceptionInfo) -> dict:
    return exc.value.details["fields"]


def test_codes_are_stable_and_padded():
    assert format_service_code(7) == "SVC-0007"
    assert format_database_code(12) == "DB-0012"


def test_service_fields_are_normalized():
    fields = build_service_fields(service_payload(name="  Portal Interno  ", port="8443", technology=""))
    assert fields.name == "Portal Interno"
    assert fields.port == 8443
    assert fields.technology is None


def test_service_requires_responsible_and_criticality_and_reports_all_fields():
    with pytest.raises(ValidationError) as exc:
        build_service_fields(service_payload(responsible=" ", criticality="extreme", service_kind="container"))
    assert set(_fields_error(exc)) == {"responsible", "criticality", "service_kind"}


@pytest.mark.parametrize("port", [0, 65536, "abc", True, -1])
def test_service_rejects_invalid_ports(port):
    with pytest.raises(ValidationError) as exc:
        build_service_fields(service_payload(port=port))
    assert "port" in _fields_error(exc)


def test_service_port_is_optional():
    assert build_service_fields(service_payload(port=None)).port is None
    assert build_service_fields(service_payload(port="")).port is None


def test_service_description_blocks_credentials_but_allows_mentions():
    with pytest.raises(ValidationError) as exc:
        build_service_fields(service_payload(description="admin password: Sup3rS3cret"))
    assert exc.value.code == "secret_not_allowed"
    fields = build_service_fields(service_payload(description="A senha fica no cofre corporativo."))
    assert fields.description == "A senha fica no cofre corporativo."


def test_database_fields_are_validated():
    fields = build_database_fields(database_payload(SERVER_ID.upper(), port="1433"))
    assert fields.server_id == SERVER_ID
    assert fields.port == 1433
    with pytest.raises(ValidationError) as exc:
        build_database_fields(database_payload("not-a-uuid", dbms="excel", responsible=""))
    assert set(_fields_error(exc)) == {"server_id", "dbms", "responsible"}


@pytest.mark.parametrize(
    "notes",
    [
        "postgresql://app:Sup3rS3cret@db01:5432/erp",
        "Server=db01;User Id=sa;Password=Sup3rS3cret;",
        "token = abcdEFGH1234",
    ],
)
def test_database_rejects_connection_secrets(notes):
    with pytest.raises(ValidationError) as exc:
        build_database_fields(database_payload(SERVER_ID, technical_notes=notes))
    assert exc.value.code == "secret_not_allowed"


def test_database_accepts_connection_target_without_secret():
    fields = build_database_fields(
        database_payload(SERVER_ID, technical_notes="Acesso via db01.delpi.local:1433; login no cofre.")
    )
    assert "cofre" in fields.technical_notes


def test_hosting_fields_require_existing_runtime_catalog():
    fields = build_hosting_fields(
        {"service_id": SERVICE_ID, "server_id": SERVER_ID, "runtime": "container", "instance_name": "api-1"}
    )
    assert fields.runtime == "container"
    with pytest.raises(ValidationError) as exc:
        build_hosting_fields({"service_id": "x", "server_id": SERVER_ID, "runtime": "kubernetes"})
    assert set(_fields_error(exc)) == {"service_id", "runtime"}


def test_consumer_fields_validate_references_and_secrets():
    fields = build_consumer_fields({"database_instance_id": SERVER_ID, "service_id": SERVICE_ID})
    assert fields.notes is None
    with pytest.raises(ValidationError):
        build_consumer_fields({"database_instance_id": SERVER_ID, "service_id": ""})
    with pytest.raises(ValidationError) as exc:
        build_consumer_fields(
            {"database_instance_id": SERVER_ID, "service_id": SERVICE_ID, "notes": "pwd=abcd1234"}
        )
    assert exc.value.code == "secret_not_allowed"
