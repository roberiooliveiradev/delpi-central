"""Regras de domínio E2B: CIDR, VLAN, gateway, IP do vínculo, pontas de integração."""

import uuid

import pytest

from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.integrations import (
    build_integration_fields,
    build_service_dependency_fields,
)
from it_portal_app.domain.networks import (
    build_network_fields,
    build_server_network_link_fields,
    validate_link_address,
)

from tests.conftest import integration_payload, network_payload

SVC_A = str(uuid.uuid4())
SVC_B = str(uuid.uuid4())


def _fields_error(exc: pytest.ExceptionInfo) -> dict:
    return exc.value.details["fields"]


@pytest.mark.parametrize(
    "cidr, expected",
    [
        ("192.168.1.0/24", "192.168.1.0/24"),
        (" 10.0.0.0/8 ", "10.0.0.0/8"),
        ("10.20.30.40/32", "10.20.30.40/32"),
        ("2001:DB8::/32", "2001:db8::/32"),
    ],
)
def test_valid_cidr_is_normalized(cidr, expected):
    fields = build_network_fields(network_payload(cidr=cidr, gateway=None))
    assert fields.cidr == expected


@pytest.mark.parametrize(
    "cidr, fragment",
    [
        ("", "CIDR"),
        ("192.168.1.0", "prefixo"),
        ("192.168.1.10/24", "192.168.1.0/24"),
        ("192.168.1.0/33", "inválido"),
        ("rede-lan", "prefixo"),
        ("300.1.1.0/24", "inválido"),
    ],
)
def test_invalid_cidr_is_rejected_with_guidance(cidr, fragment):
    with pytest.raises(ValidationError) as exc:
        build_network_fields(network_payload(cidr=cidr, gateway=None))
    assert fragment in _fields_error(exc)["cidr"]


@pytest.mark.parametrize("vlan", [0, 4095, "abc", True, -1])
def test_vlan_out_of_range_is_rejected(vlan):
    with pytest.raises(ValidationError) as exc:
        build_network_fields(network_payload(vlan_id=vlan))
    assert "vlan_id" in _fields_error(exc)


@pytest.mark.parametrize("vlan, expected", [(1, 1), ("4094", 4094), (None, None), ("", None)])
def test_vlan_bounds_and_empty(vlan, expected):
    assert build_network_fields(network_payload(vlan_id=vlan)).vlan_id == expected


@pytest.mark.parametrize(
    "gateway",
    ["192.168.2.1", "192.168.1.0", "192.168.1.255", "2001:db8::1", "gateway"],
)
def test_gateway_must_be_a_host_inside_the_network(gateway):
    with pytest.raises(ValidationError) as exc:
        build_network_fields(network_payload(gateway=gateway))
    assert "gateway" in _fields_error(exc)


def test_gateway_inside_network_is_accepted():
    assert build_network_fields(network_payload(gateway="192.168.1.254")).gateway == "192.168.1.254"


def test_point_to_point_network_accepts_both_addresses():
    fields = build_network_fields(network_payload(cidr="10.0.0.0/31", gateway="10.0.0.1"))
    assert fields.gateway == "10.0.0.1"


def test_scope_classification_is_mandatory():
    with pytest.raises(ValidationError) as exc:
        build_network_fields(network_payload(network_scope=None))
    assert "network_scope" in _fields_error(exc)
    container = build_network_fields(
        network_payload(cidr="172.17.0.0/16", gateway=None, network_scope="container_runtime")
    )
    assert container.network_scope == "container_runtime"


def test_network_requires_responsible_and_criticality():
    with pytest.raises(ValidationError) as exc:
        build_network_fields(network_payload(responsible=" ", criticality=None))
    assert {"responsible", "criticality"} <= set(_fields_error(exc))


def test_network_notes_reject_secrets():
    with pytest.raises(ValidationError) as exc:
        build_network_fields(network_payload(notes="switch core senha: Delpi@2026"))
    assert exc.value.code == "secret_not_allowed"


def test_link_address_must_belong_to_network():
    fields = build_server_network_link_fields(
        {"server_id": SVC_A, "network_id": SVC_B, "ip_address": "192.168.1.20"}
    )
    validate_link_address(fields.ip_address, "192.168.1.0/24")
    with pytest.raises(ValidationError):
        validate_link_address("10.0.0.5", "192.168.1.0/24")
    with pytest.raises(ValidationError):
        validate_link_address("192.168.1.0", "192.168.1.0/24")
    validate_link_address(None, "192.168.1.0/24")


def test_link_rejects_malformed_ip():
    with pytest.raises(ValidationError) as exc:
        build_server_network_link_fields(
            {"server_id": SVC_A, "network_id": SVC_B, "ip_address": "999.1.1.1"}
        )
    assert "ip_address" in _fields_error(exc)


def test_integration_between_two_services():
    fields = build_integration_fields(
        integration_payload(source_service_id=SVC_A, target_service_id=SVC_B)
    )
    assert fields.internal_service_ids() == (SVC_A, SVC_B)


def test_integration_with_explicit_external_destination():
    fields = build_integration_fields(
        integration_payload(source_service_id=SVC_A, target_external_name="SEFAZ — NF-e")
    )
    assert fields.target_service_id is None
    assert fields.target_external_name == "SEFAZ — NF-e"


@pytest.mark.parametrize(
    "endpoints, field",
    [
        ({"target_service_id": SVC_B}, "source_service_id"),
        ({"source_service_id": SVC_A}, "target_service_id"),
        (
            {"source_service_id": SVC_A, "source_external_name": "X", "target_service_id": SVC_B},
            "source_external_name",
        ),
        ({"source_external_name": "Banco", "target_external_name": "SEFAZ"}, "target_external_name"),
        ({"source_service_id": SVC_A, "target_service_id": SVC_A}, "target_service_id"),
        ({"source_service_id": "nao-uuid", "target_service_id": SVC_B}, "source_service_id"),
    ],
)
def test_integration_endpoint_rules(endpoints, field):
    with pytest.raises(ValidationError) as exc:
        build_integration_fields(integration_payload(**endpoints))
    assert field in _fields_error(exc)


def test_integration_rejects_credentials_in_external_reference():
    with pytest.raises(ValidationError) as exc:
        build_integration_fields(
            integration_payload(
                source_service_id=SVC_A,
                target_external_name="https://user:Segredo123@api.parceiro.com",
            )
        )
    assert exc.value.code == "secret_not_allowed"


def test_integration_closed_catalogs():
    with pytest.raises(ValidationError) as exc:
        build_integration_fields(
            integration_payload(
                source_service_id=SVC_A,
                target_service_id=SVC_B,
                protocol="carrier_pigeon",
                direction="sideways",
            )
        )
    assert {"protocol", "direction"} <= set(_fields_error(exc))


def test_dependency_rejects_self_relation():
    with pytest.raises(ValidationError) as exc:
        build_service_dependency_fields(
            {"dependent_service_id": SVC_A, "required_service_id": SVC_A}
        )
    assert "required_service_id" in _fields_error(exc)
    ok = build_service_dependency_fields(
        {"dependent_service_id": SVC_A, "required_service_id": SVC_B}
    )
    assert ok.required_service_id == SVC_B
