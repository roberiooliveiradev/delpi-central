"""Redes lógicas e conectividade servidor ↔ rede (E2B).

Cadastro manual: o portal não varre a rede. O CIDR é validado e normalizado
no backend; o gateway e o IP de um servidor na rede precisam pertencer ao CIDR.
"""

from __future__ import annotations

import ipaddress
from dataclasses import asdict, dataclass

from it_portal_app.domain.catalogs import (
    CRITICALITIES,
    ENVIRONMENTS,
    NETWORK_SCOPES,
    UNIT_CODES,
)
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.field_rules import (
    choice,
    clean,
    optional_text,
    required_text,
    required_uuid,
)
from it_portal_app.domain.secret_guard import ensure_no_secret

NAME_MAX = 120
LOCATION_MAX = 160
PURPOSE_MAX = 160
ZONE_MAX = 80
RESPONSIBLE_MAX = 160
NOTES_MAX = 4000
INTERFACE_MAX = 60
LINK_NOTES_MAX = 500
VLAN_MIN = 1
VLAN_MAX = 4094

NETWORK_CODE_PREFIX = "NET-"


def format_network_code(seq: int) -> str:
    return f"{NETWORK_CODE_PREFIX}{seq:04d}"


IpNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network


def parse_cidr(value: object) -> tuple[IpNetwork | None, str | None]:
    """CIDR normalizado ou mensagem de erro. Exige prefixo e endereço de rede."""
    cleaned = clean(value)
    if not cleaned:
        return None, "Informe o endereço da rede em CIDR (ex.: 192.168.1.0/24)."
    if "/" not in cleaned:
        return None, "Inclua o prefixo da rede (ex.: 192.168.1.0/24)."
    try:
        return ipaddress.ip_network(cleaned, strict=True), None
    except ValueError:
        try:
            network = ipaddress.ip_network(cleaned, strict=False)
        except ValueError:
            return None, "CIDR inválido. Use o formato 192.168.1.0/24."
        return None, f"Use o endereço de rede do bloco: {network}."


def address_in_network(address: str, cidr: str) -> bool:
    try:
        return ipaddress.ip_address(address) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False


def _host_address_in(network: IpNetwork, raw: object, field: str, errors: dict) -> str | None:
    cleaned = clean(raw)
    if not cleaned:
        return None
    try:
        address = ipaddress.ip_address(cleaned)
    except ValueError:
        errors[field] = "Endereço IP inválido."
        return None
    if address.version != network.version or address not in network:
        errors[field] = f"O endereço precisa pertencer à rede {network}."
        return None
    reserved = {network.network_address}
    if network.version == 4 and network.prefixlen < 31:
        reserved.add(network.broadcast_address)
    if address in reserved:
        errors[field] = "Use um endereço de host (não o de rede nem o de broadcast)."
        return None
    return str(address)


def _optional_vlan(raw: dict, errors: dict) -> int | None:
    value = raw.get("vlan_id")
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        errors["vlan_id"] = "VLAN inválida."
        return None
    try:
        vlan = int(str(value).strip())
    except ValueError:
        errors["vlan_id"] = f"Informe uma VLAN entre {VLAN_MIN} e {VLAN_MAX}."
        return None
    if not VLAN_MIN <= vlan <= VLAN_MAX:
        errors["vlan_id"] = f"Informe uma VLAN entre {VLAN_MIN} e {VLAN_MAX}."
        return None
    return vlan


@dataclass(frozen=True)
class NetworkFields:
    name: str
    cidr: str
    vlan_id: int | None
    gateway: str | None
    unit_code: str
    location: str | None
    purpose: str | None
    environment: str
    zone: str | None
    network_scope: str
    criticality: str
    responsible: str
    notes: str | None

    def as_dict(self) -> dict:
        return asdict(self)


NETWORK_FIELD_NAMES = tuple(NetworkFields.__dataclass_fields__.keys())


def build_network_fields(raw: dict) -> NetworkFields:
    errors: dict[str, str] = {}
    name = required_text(raw, "name", NAME_MAX, "Informe o nome da rede.", errors)
    network, cidr_error = parse_cidr(raw.get("cidr"))
    if cidr_error:
        errors["cidr"] = cidr_error
    vlan_id = _optional_vlan(raw, errors)
    gateway = _host_address_in(network, raw.get("gateway"), "gateway", errors) if network else None
    unit_code = choice(raw, "unit_code", UNIT_CODES, "Selecione a unidade.", errors)
    location = optional_text(raw, "location", LOCATION_MAX, errors)
    purpose = optional_text(raw, "purpose", PURPOSE_MAX, errors)
    environment = choice(raw, "environment", ENVIRONMENTS, "Selecione o ambiente.", errors)
    zone = optional_text(raw, "zone", ZONE_MAX, errors)
    network_scope = choice(
        raw,
        "network_scope",
        NETWORK_SCOPES,
        "Classifique a rede: corporativa ou interna de containers.",
        errors,
    )
    criticality = choice(raw, "criticality", CRITICALITIES, "Selecione a criticidade.", errors)
    responsible = required_text(
        raw, "responsible", RESPONSIBLE_MAX, "Informe o responsável pela rede.", errors
    )
    notes = optional_text(raw, "notes", NOTES_MAX, errors)

    if errors:
        raise ValidationError(
            "invalid_network", "Revise os campos destacados da rede.", {"fields": errors}
        )

    for field, value in (
        ("name", name),
        ("location", location),
        ("purpose", purpose),
        ("zone", zone),
        ("notes", notes),
    ):
        ensure_no_secret(field, value)

    return NetworkFields(
        name=name,
        cidr=str(network),
        vlan_id=vlan_id,
        gateway=gateway,
        unit_code=unit_code,
        location=location,
        purpose=purpose,
        environment=environment,
        zone=zone,
        network_scope=network_scope,
        criticality=criticality,
        responsible=responsible,
        notes=notes,
    )


@dataclass(frozen=True)
class ServerNetworkLinkFields:
    server_id: str
    network_id: str
    ip_address: str | None
    interface_name: str | None
    notes: str | None


def build_server_network_link_fields(raw: dict) -> ServerNetworkLinkFields:
    """Campos do vínculo; a pertinência do IP ao CIDR exige a rede (ver
    `validate_link_address`)."""
    errors: dict[str, str] = {}
    server_id = required_uuid(raw, "server_id", "Selecione o servidor.", errors)
    network_id = required_uuid(raw, "network_id", "Selecione a rede.", errors)
    ip_raw = clean(raw.get("ip_address"))
    ip_address = None
    if ip_raw:
        try:
            ip_address = str(ipaddress.ip_address(ip_raw))
        except ValueError:
            errors["ip_address"] = "Endereço IP inválido."
    interface_name = optional_text(raw, "interface_name", INTERFACE_MAX, errors)
    notes = optional_text(raw, "notes", LINK_NOTES_MAX, errors)
    if errors:
        raise ValidationError(
            "invalid_server_network_link", "Revise os campos do vínculo.", {"fields": errors}
        )
    ensure_no_secret("interface_name", interface_name)
    ensure_no_secret("notes", notes)
    return ServerNetworkLinkFields(
        server_id=server_id,
        network_id=network_id,
        ip_address=ip_address,
        interface_name=interface_name,
        notes=notes,
    )


def validate_link_address(ip_address: str | None, cidr: str) -> None:
    if ip_address is None:
        return
    errors: dict[str, str] = {}
    _host_address_in(ipaddress.ip_network(cidr, strict=False), ip_address, "ip_address", errors)
    if errors:
        raise ValidationError(
            "invalid_server_network_link", "Revise os campos do vínculo.", {"fields": errors}
        )
