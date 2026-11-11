"""Contrato e validação de observações automáticas de servidor (E4.S1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.field_rules import clean, choice, optional_text, required_text
from it_portal_app.domain.secret_guard import ensure_no_secret
from it_portal_app.domain.servers import normalize_hostname, normalize_ip

OBSERVATION_SOURCES = ("linux_host_collector",)
OBSERVATION_STATUSES = ("complete", "partial", "failed")
SECTION_STATUSES = ("ok", "partial", "unavailable", "failed")
SCHEMA_VERSION_V1 = "1"

RUN_ID_MIN = 8
RUN_ID_MAX = 64
HOSTNAME_MAX = 253
MACHINE_ID_MAX = 64
OS_NAME_MAX = 120
OS_VERSION_MAX = 80
KERNEL_MAX = 120
ARCH_MAX = 40
VIRT_MAX = 80
HW_MAX = 160
INTERFACE_MAX = 40
ADDRESS_MAX = 64
SERVICE_NAME_MAX = 120
VOLUME_MOUNT_MAX = 120
SUMMARY_JSON_MAX_BYTES = 48_000
MAX_VOLUMES = 32
MAX_NICS = 32
MAX_SERVICES = 40
MAX_CONTAINER_SAMPLE = 20

# Interfaces de runtime Docker / bridge — não são rede corporativa.
DOCKER_NIC_PREFIXES = ("docker", "br-", "veth", "cni", "flannel", "cali", "tunl", "virbr")

OBSERVATION_RETENTION_DEFAULT = 50
STALE_AFTER_HOURS_DEFAULT = 36


@dataclass(frozen=True)
class HostIdentity:
    hostname: str
    machine_id: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ObservationIngest:
    run_id: str
    source: str
    schema_version: str
    status: str
    observed_at: datetime
    host_identity: HostIdentity
    summary: dict
    sections_status: dict[str, str]

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "source": self.source,
            "schema_version": self.schema_version,
            "status": self.status,
            "observed_at": self.observed_at,
            "host_identity": self.host_identity.as_dict(),
            "summary": self.summary,
            "sections_status": dict(self.sections_status),
        }


def _parse_observed_at(raw: object, errors: dict) -> datetime:
    value = clean(raw)
    if not value:
        errors["observed_at"] = "Informe o horário da observação (ISO-8601)."
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors["observed_at"] = "Informe o horário da observação em ISO-8601."
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _validate_sections_status(raw: object, errors: dict) -> dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        errors["sections_status"] = "sections_status deve ser um objeto."
        return {}
    out: dict[str, str] = {}
    for key, value in list(raw.items())[:40]:
        name = clean(key)
        status = clean(value)
        if not name or len(name) > 40:
            errors["sections_status"] = "Nome de seção inválido."
            continue
        if status not in SECTION_STATUSES:
            errors["sections_status"] = (
                f"Status de seção inválido: use {', '.join(SECTION_STATUSES)}."
            )
            continue
        out[name] = status
    return out


def _trim_list(items: list, limit: int) -> list:
    return items[:limit]


def _sanitize_summary(raw: object, errors: dict) -> dict:
    if not isinstance(raw, dict):
        errors["summary"] = "summary deve ser um objeto."
        return {}
    # Cópia rasa controlada — remove chaves sensíveis conhecidas.
    forbidden = {
        "env",
        "environment",
        "environ",
        "secrets",
        "password",
        "token",
        "argv",
        "cmdline",
        "command_line",
        "mounts",
        "bind_mounts",
    }
    summary = {str(k): v for k, v in raw.items() if str(k).lower() not in forbidden}

    os_info = summary.get("os")
    if isinstance(os_info, dict):
        for field in ("name", "version", "kernel", "architecture"):
            if field in os_info:
                text = clean(os_info.get(field))
                if text:
                    ensure_no_secret(f"summary.os.{field}", text)
                os_info[field] = text or None
        summary["os"] = os_info

    virt = summary.get("virtualization")
    if isinstance(virt, dict):
        for field in ("type", "hardware_model"):
            if field in virt:
                text = clean(virt.get(field))
                if text:
                    ensure_no_secret(f"summary.virtualization.{field}", text)
                virt[field] = text or None
        summary["virtualization"] = virt

    nics = summary.get("host_nics")
    if isinstance(nics, list):
        cleaned_nics = []
        for nic in _trim_list(nics, MAX_NICS):
            if not isinstance(nic, dict):
                continue
            name = clean(nic.get("name"))[:INTERFACE_MAX]
            if not name or name.lower().startswith(DOCKER_NIC_PREFIXES):
                continue
            addresses = []
            for addr in nic.get("addresses") or []:
                text = clean(addr)[:ADDRESS_MAX]
                if text:
                    addresses.append(text)
            cleaned_nics.append(
                {
                    "name": name,
                    "addresses": addresses[:8],
                    "state": clean(nic.get("state"))[:20] or None,
                }
            )
        summary["host_nics"] = cleaned_nics
    elif nics is not None:
        errors["summary"] = "host_nics deve ser uma lista."

    volumes = summary.get("volumes")
    if isinstance(volumes, list):
        cleaned_volumes = []
        for vol in _trim_list(volumes, MAX_VOLUMES):
            if not isinstance(vol, dict):
                continue
            mount = clean(vol.get("mount_point") or vol.get("mount"))[:VOLUME_MOUNT_MAX]
            if not mount:
                continue
            cleaned_volumes.append(
                {
                    "mount_point": mount,
                    "filesystem": clean(vol.get("filesystem"))[:40] or None,
                    "size_bytes": _optional_nonneg_int(vol.get("size_bytes")),
                    "used_bytes": _optional_nonneg_int(vol.get("used_bytes")),
                    "available_bytes": _optional_nonneg_int(vol.get("available_bytes")),
                    "used_percent": _optional_percent(vol.get("used_percent")),
                }
            )
        summary["volumes"] = cleaned_volumes
    elif volumes is not None:
        errors["summary"] = "volumes deve ser uma lista."

    services = summary.get("systemd_services")
    if isinstance(services, list):
        cleaned_services = []
        for svc in _trim_list(services, MAX_SERVICES):
            if not isinstance(svc, dict):
                continue
            name = clean(svc.get("name"))[:SERVICE_NAME_MAX]
            if not name:
                continue
            cleaned_services.append(
                {
                    "name": name,
                    "active_state": clean(svc.get("active_state"))[:40] or None,
                    "sub_state": clean(svc.get("sub_state"))[:40] or None,
                    "unit_file_state": clean(svc.get("unit_file_state"))[:40] or None,
                }
            )
        summary["systemd_services"] = cleaned_services
    elif services is not None:
        errors["summary"] = "systemd_services deve ser uma lista."

    docker = summary.get("docker_summary")
    if isinstance(docker, dict):
        sample = docker.get("container_names_sample")
        if isinstance(sample, list):
            docker["container_names_sample"] = [
                clean(item)[:120] for item in sample[:MAX_CONTAINER_SAMPLE] if clean(item)
            ]
        summary["docker_summary"] = {
            "available": bool(docker.get("available")),
            "server_version": clean(docker.get("server_version"))[:40] or None,
            "containers_total": _optional_nonneg_int(docker.get("containers_total")),
            "containers_running": _optional_nonneg_int(docker.get("containers_running")),
            "images": _optional_nonneg_int(docker.get("images")),
            "container_names_sample": docker.get("container_names_sample") or [],
            "unavailable_reason": clean(docker.get("unavailable_reason"))[:160] or None,
        }
    elif docker is not None:
        errors["summary"] = "docker_summary deve ser um objeto."

    encoded = str(summary)
    if len(encoded.encode("utf-8")) > SUMMARY_JSON_MAX_BYTES:
        errors["summary"] = "Resumo da observação excede o limite permitido."
    return summary


def _optional_nonneg_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _optional_percent(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0 or number > 100:
        return None
    return round(number, 2)


def build_observation_ingest(raw: dict) -> ObservationIngest:
    errors: dict[str, str] = {}
    run_id = required_text(
        raw, "run_id", RUN_ID_MAX, "Informe o identificador idempotente da execução.", errors
    )
    if run_id and len(run_id) < RUN_ID_MIN:
        errors["run_id"] = f"run_id deve ter pelo menos {RUN_ID_MIN} caracteres."
    source = choice(raw, "source", OBSERVATION_SOURCES, "Fonte de coleta inválida.", errors)
    schema_version = required_text(
        raw, "schema_version", 16, "Informe a versão do contrato da observação.", errors
    )
    if schema_version and schema_version != SCHEMA_VERSION_V1:
        errors["schema_version"] = f"Versão de contrato suportada: {SCHEMA_VERSION_V1}."
    status = choice(
        raw, "status", OBSERVATION_STATUSES, "Status da coleta inválido.", errors
    )
    observed_at = _parse_observed_at(raw.get("observed_at"), errors)

    host_raw = raw.get("host_identity")
    if not isinstance(host_raw, dict):
        errors["host_identity"] = "Informe a identidade do host."
        host_raw = {}
    hostname = normalize_hostname(host_raw.get("hostname"))
    if not hostname:
        errors["host_identity.hostname"] = "Informe o hostname observado."
    elif len(hostname) > HOSTNAME_MAX:
        errors["host_identity.hostname"] = f"Use no máximo {HOSTNAME_MAX} caracteres."
    machine_id = optional_text(host_raw, "machine_id", MACHINE_ID_MAX, errors)
    if machine_id:
        ensure_no_secret("host_identity.machine_id", machine_id)

    sections_status = _validate_sections_status(raw.get("sections_status"), errors)
    try:
        summary = _sanitize_summary(raw.get("summary"), errors)
    except ValidationError as exc:
        field = exc.details.get("field") or "summary"
        errors[str(field)] = exc.message
        summary = {}

    if errors:
        raise ValidationError(
            "invalid_observation",
            "Revise os campos destacados da observação.",
            {"fields": errors},
        )

    return ObservationIngest(
        run_id=run_id,
        source=source,
        schema_version=schema_version,
        status=status,
        observed_at=observed_at,
        host_identity=HostIdentity(hostname=hostname, machine_id=machine_id),
        summary=summary,
        sections_status=sections_status,
    )


def compute_divergences(server: dict, observation: ObservationIngest) -> list[dict[str, Any]]:
    """Compara observação com campos manuais do cadastro — não altera o servidor."""
    divergences: list[dict[str, Any]] = []
    observed_hostname = observation.host_identity.hostname
    registered_hostname = normalize_hostname(server.get("hostname"))
    if observed_hostname and registered_hostname and observed_hostname != registered_hostname:
        divergences.append(
            {
                "field": "hostname",
                "registered": registered_hostname,
                "observed": observed_hostname,
            }
        )

    os_info = observation.summary.get("os") if isinstance(observation.summary.get("os"), dict) else {}
    observed_os_parts = [
        clean(os_info.get("name")),
        clean(os_info.get("version")),
    ]
    observed_os = " ".join(part for part in observed_os_parts if part).strip() or None
    registered_os = clean(server.get("operating_system")) or None
    if observed_os and registered_os and observed_os.lower() != registered_os.lower():
        divergences.append(
            {
                "field": "operating_system",
                "registered": registered_os,
                "observed": observed_os,
            }
        )

    registered_ip = normalize_ip(server.get("ip_address"))
    observed_ips: list[str] = []
    for nic in observation.summary.get("host_nics") or []:
        if not isinstance(nic, dict):
            continue
        for addr in nic.get("addresses") or []:
            ip = normalize_ip(str(addr).split("/")[0])
            if ip:
                observed_ips.append(ip)
    if registered_ip and observed_ips and registered_ip not in observed_ips:
        divergences.append(
            {
                "field": "ip_address",
                "registered": registered_ip,
                "observed": observed_ips[0],
                "observed_all": observed_ips[:8],
            }
        )
    return divergences
