"""Contrato de inventário completo do Windows SCM, separado das observações v1."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.servers import is_valid_hostname, normalize_hostname

MAX_BATCH_SERVICES = 100
MAX_BATCHES = 50
VALID_STATES = frozenset({
    "running", "stopped", "paused", "start_pending", "stop_pending",
    "continue_pending", "pause_pending", "unknown",
})
VALID_START_MODES = frozenset({"auto", "manual", "disabled", "boot", "system", "unknown"})
_SECRET_PATTERN = re.compile(
    r"(?i)(?:bearer\s+[A-Za-z0-9._~+/-]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY|"
    r"(?:password|client_secret|access_token)\s*[:=])"
)


@dataclass(frozen=True)
class HostServiceBatch:
    run_id: str
    observed_at: datetime
    hostname: str
    batch_index: int
    batch_count: int
    services: tuple[dict, ...]


def build_host_service_batch(raw: dict) -> HostServiceBatch:
    """Falha fechado para campos desconhecidos, segredos e limites excedidos."""
    errors: dict[str, str] = {}
    allowed = {"run_id", "schema_version", "observed_at", "host_identity",
               "batch_index", "batch_count", "services"}
    if set(raw) - allowed:
        errors["body"] = "Campos não permitidos no contrato de inventário."

    try:
        run_id = str(uuid.UUID(str(raw.get("run_id"))))
    except (ValueError, AttributeError, TypeError):
        run_id = ""
        errors["run_id"] = "Informe um UUID válido para a coleta."
    if raw.get("schema_version") != "1":
        errors["schema_version"] = "Versão de contrato suportada: 1."
    try:
        observed_at = datetime.fromisoformat(str(raw.get("observed_at")).replace("Z", "+00:00"))
        if observed_at.tzinfo is None:
            raise ValueError("Timezone ausente")
        observed_at = observed_at.astimezone(timezone.utc)
        if observed_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError("Data futura")
    except (TypeError, ValueError, OverflowError):
        observed_at = datetime.now(timezone.utc)
        errors["observed_at"] = "Informe horário ISO-8601 UTC válido, não futuro."

    host = raw.get("host_identity")
    hostname = normalize_hostname(host.get("hostname")) if isinstance(host, dict) else ""
    if not is_valid_hostname(hostname) or (isinstance(host, dict) and set(host) != {"hostname"}):
        errors["host_identity"] = "Informe exclusivamente hostname válido."
    for field, maximum in (("batch_index", MAX_BATCHES - 1), ("batch_count", MAX_BATCHES)):
        value = raw.get(field)
        if type(value) is not int or value < (1 if field == "batch_count" else 0) or value > maximum:
            errors[field] = "Índice ou quantidade de lotes inválido."
    index, count = raw.get("batch_index"), raw.get("batch_count")
    if type(index) is int and type(count) is int and index >= count:
        errors["batch_index"] = "Índice deve ser menor que a quantidade de lotes."

    source = raw.get("services")
    if not isinstance(source, list) or not (1 <= len(source) <= MAX_BATCH_SERVICES):
        errors["services"] = f"Envie de 1 a {MAX_BATCH_SERVICES} serviços por lote."
        source = []
    services: list[dict] = []
    seen: set[str] = set()
    required = {"name", "display_name", "description", "state", "start_mode", "can_stop"}
    for i, item in enumerate(source):
        if not isinstance(item, dict) or set(item) != required:
            errors[f"services[{i}]"] = "Campos do serviço inválidos."
            continue
        name = item["name"]
        if (not isinstance(name, str) or not (1 <= len(name.strip()) <= 200)
                or any(ord(ch) < 32 or ch in "\\/" for ch in name)):
            errors[f"services[{i}].name"] = "Nome de serviço inválido."
            continue
        name = name.strip()
        key = name.casefold()
        if key in seen:
            errors[f"services[{i}].name"] = "Nome duplicado no lote."
            continue
        seen.add(key)
        display = item["display_name"]
        description = item["description"]
        if not isinstance(display, str) or not (1 <= len(display.strip()) <= 240):
            errors[f"services[{i}].display_name"] = "Descrição curta inválida."
            continue
        if description is not None and (
            not isinstance(description, str) or len(description) > 500 or
            bool(_SECRET_PATTERN.search(description))
        ):
            errors[f"services[{i}].description"] = "Descrição inválida ou sensível."
            continue
        if item["state"] not in VALID_STATES or item["start_mode"] not in VALID_START_MODES:
            errors[f"services[{i}].state"] = "Estado ou inicialização inválido."
            continue
        if type(item["can_stop"]) is not bool:
            errors[f"services[{i}].can_stop"] = "can_stop deve ser booleano."
            continue
        services.append({
            "service_key": key, "name": name, "display_name": display.strip(),
            "description": description.strip() if description else None,
            "state": item["state"], "start_mode": item["start_mode"],
            "can_stop": item["can_stop"],
        })
    if errors:
        raise ValidationError("invalid_host_service_batch", "Lote de serviços inválido.", {"fields": errors})
    return HostServiceBatch(run_id, observed_at, hostname, index, count, tuple(services))
