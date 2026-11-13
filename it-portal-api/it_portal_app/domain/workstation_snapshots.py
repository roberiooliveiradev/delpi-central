"""G2-S1: validate UNTRUSTED Windows workstation local snapshot v1.

No database writes or remote access. Validation is not authentication or device
identity: G2-S2 requires an independently enrolled, revocable principal.
"""
from __future__ import annotations

import ipaddress
import json
import re
import uuid
from datetime import datetime, timedelta, timezone

SCHEMA_VERSION = "1"
SOURCE = "windows_workstation_local_v1"
MAX_PAYLOAD_BYTES = 32_768
MAX_VOLUMES = 16
MAX_PRIVATE_IPS = 16
MAX_AGE = timedelta(days=1)
MAX_FUTURE = timedelta(minutes=5)
VALID_SECTION_STATES = {"ok", "partial", "unavailable"}
SECTIONS = ("hardware", "os", "volumes", "network")
PRIVATE_RANGES = tuple(ipaddress.ip_network(net) for net in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"
))
HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
MOUNT = re.compile(r"^[A-Z]:$")


class SnapshotValidationError(ValueError):
    """Field-safe error without including the sensitive value."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        super().__init__(f"{field}: {message}")


def _object(value: object, field: str, keys: set[str], *, nullable: bool = False) -> dict | None:
    if value is None and nullable:
        return None
    if not isinstance(value, dict):
        raise SnapshotValidationError(field, "must be an object")
    extra = set(value) - keys
    if extra:
        raise SnapshotValidationError(field, "unexpected key")
    return value


def _text(value: object, field: str, limit: int, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise SnapshotValidationError(field, "invalid text")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise SnapshotValidationError(field, "control character not allowed")
    return value.strip()


def _count(value: object, field: str, *, maximum: int, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or value < 0 or value > maximum:
        raise SnapshotValidationError(field, "invalid non-negative integer")
    return value


def _hostname(raw: object) -> str:
    value = _text(raw, "host.hostname", 253).lower().rstrip(".")
    if not value or any(not HOST_LABEL.fullmatch(part) for part in value.split(".")):
        raise SnapshotValidationError("host.hostname", "invalid hostname")
    return value


def _memory(raw: object, field: str) -> int | None:
    return _count(raw, field, maximum=1 << 54, nullable=True)


def validate_workstation_snapshot(raw: object, *, now: datetime | None = None) -> dict:
    """Strict/size-bounded sanitized structure for future, separately gated ingest.

    Produces no DB side effects, device enrollment or network requests.
    """
    body = _object(raw, "snapshot", {
        "source", "schema_version", "run_id", "observed_at", "status",
        "host", "hardware", "os", "volumes", "network", "sections_status",
    })
    if len(json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise SnapshotValidationError("snapshot", "payload too large")
    if body.get("source") != SOURCE or body.get("schema_version") != SCHEMA_VERSION:
        raise SnapshotValidationError("schema_version", "unsupported source or schema")
    run_id = _text(body.get("run_id"), "run_id", 36)
    try:
        parsed_run = uuid.UUID(run_id)
        if parsed_run.version != 4 or str(parsed_run) != run_id.lower():
            raise ValueError("not canonical UUID v4")
    except ValueError:
        raise SnapshotValidationError("run_id", "invalid UUID v4") from None

    timestamp = _text(body.get("observed_at"), "observed_at", 40)
    try:
        when = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        raise SnapshotValidationError("observed_at", "invalid ISO timestamp") from None
    if when.tzinfo is None:
        raise SnapshotValidationError("observed_at", "timezone required")
    when = when.astimezone(timezone.utc)
    clock = now if now is not None else datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError("now must have timezone")
    if when - clock > MAX_FUTURE or clock - when > MAX_AGE:
        raise SnapshotValidationError("observed_at", "observation outside allowed time window")

    host = _object(body.get("host"), "host", {"hostname"})
    host_name = _hostname(host.get("hostname"))

    sections = _object(body.get("sections_status"), "sections_status", set(SECTIONS))
    if set(sections) != set(SECTIONS) or any(v not in VALID_SECTION_STATES for v in sections.values()):
        raise SnapshotValidationError("sections_status", "invalid section status")
    expected = ("complete" if all(v == "ok" for v in sections.values()) else
                "failed" if all(v == "unavailable" for v in sections.values()) else "partial")
    if body.get("status") != expected:
        raise SnapshotValidationError("status", "inconsistent with sections_status")

    hardware = _object(body.get("hardware"), "hardware", {
        "manufacturer", "model", "cpu_name", "logical_processors", "memory_total_bytes"
    }, nullable=True)
    if hardware is not None:
        hardware = {
            "manufacturer": _text(hardware.get("manufacturer"), "hardware.manufacturer", 120, nullable=True),
            "model": _text(hardware.get("model"), "hardware.model", 120, nullable=True),
            "cpu_name": _text(hardware.get("cpu_name"), "hardware.cpu_name", 160, nullable=True),
            "logical_processors": _count(hardware.get("logical_processors"), "hardware.logical_processors", maximum=512, nullable=True),
            "memory_total_bytes": _memory(hardware.get("memory_total_bytes"), "hardware.memory_total_bytes"),
        }
    os_data = _object(body.get("os"), "os", {
        "name", "version", "build_number", "architecture", "uptime_seconds"
    }, nullable=True)
    if os_data is not None:
        os_data = {
            "name": _text(os_data.get("name"), "os.name", 120, nullable=True),
            "version": _text(os_data.get("version"), "os.version", 64, nullable=True),
            "build_number": _text(os_data.get("build_number"), "os.build_number", 40, nullable=True),
            "architecture": _text(os_data.get("architecture"), "os.architecture", 40, nullable=True),
            "uptime_seconds": _count(os_data.get("uptime_seconds"), "os.uptime_seconds", maximum=1 << 40, nullable=True),
        }
    if (sections["hardware"] == "ok") != (hardware is not None):
        if sections["hardware"] == "ok" or (hardware is None and sections["hardware"] == "partial"):
            raise SnapshotValidationError("hardware", "inconsistent section status")
    if (sections["os"] == "ok") != (os_data is not None):
        if sections["os"] == "ok" or (os_data is None and sections["os"] == "partial"):
            raise SnapshotValidationError("os", "inconsistent section status")

    volumes_raw = body.get("volumes")
    if not isinstance(volumes_raw, list) or len(volumes_raw) > MAX_VOLUMES:
        raise SnapshotValidationError("volumes", "invalid volume list")
    volumes = []
    mounts = set()
    for idx, entry in enumerate(volumes_raw):
        field = f"volumes[{idx}]"
        volume = _object(entry, field, {"mount_point", "filesystem", "capacity_bytes", "free_bytes"})
        mount = _text(volume.get("mount_point"), field + ".mount_point", 2).upper()
        if not MOUNT.fullmatch(mount) or mount in mounts:
            raise SnapshotValidationError(field + ".mount_point", "invalid or duplicate drive")
        mounts.add(mount)
        capacity = _count(volume.get("capacity_bytes"), field + ".capacity_bytes", maximum=1 << 54)
        free = _count(volume.get("free_bytes"), field + ".free_bytes", maximum=1 << 54)
        if capacity == 0 or free > capacity:
            raise SnapshotValidationError(field, "invalid disk size")
        volumes.append({
            "mount_point": mount,
            "filesystem": _text(volume.get("filesystem"), field + ".filesystem", 32, nullable=True),
            "capacity_bytes": capacity, "free_bytes": free,
        })
    if sections["volumes"] == "ok" and not volumes:
        raise SnapshotValidationError("volumes", "empty list marked ok")

    network = _object(body.get("network"), "network", {"private_ipv4"})
    addresses = network.get("private_ipv4")
    if not isinstance(addresses, list) or len(addresses) > MAX_PRIVATE_IPS:
        raise SnapshotValidationError("network.private_ipv4", "invalid address list")
    normalized_ips = []
    for value in addresses:
        if not isinstance(value, str):
            raise SnapshotValidationError("network.private_ipv4", "address must be IPv4")
        try:
            ip = ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError:
            raise SnapshotValidationError("network.private_ipv4", "invalid IPv4") from None
        if not any(ip in net for net in PRIVATE_RANGES):
            raise SnapshotValidationError("network.private_ipv4", "only RFC1918 IPv4 allowed")
        normalized_ips.append(str(ip))
    if len(set(normalized_ips)) != len(normalized_ips):
        raise SnapshotValidationError("network.private_ipv4", "duplicate IPv4")
    if sections["network"] == "ok" and not normalized_ips:
        raise SnapshotValidationError("network", "empty addresses marked ok")

    return {
        "source": SOURCE, "schema_version": SCHEMA_VERSION,
        "run_id": str(parsed_run), "observed_at": when.isoformat(),
        "status": expected, "host": {"hostname": host_name},
        "hardware": hardware, "os": os_data, "volumes": volumes,
        "network": {"private_ipv4": normalized_ips},
        "sections_status": dict(sections),
    }
