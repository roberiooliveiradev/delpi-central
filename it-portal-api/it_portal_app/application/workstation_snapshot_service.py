"""G2-S2: ingestao de inventario por identidade de dispositivo independente do usuario.

Feature flag e binding explicito sempre obrigatorios. Nenhum endpoint remoto.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Protocol

from it_portal_app.config import settings
from it_portal_app.application.workstation_identity_service import device_client_id
from it_portal_app.domain.errors import (
    ConflictError, NotFoundError, PersistenceUnavailableError, ValidationError,
)
from it_portal_app.domain.workstation_snapshots import (
    SnapshotValidationError, validate_workstation_snapshot,
)

INGEST_SCOPE = "it-portal.workstations.ingest"
_CLIENT_ID = re.compile(r"^[A-Za-z0-9_.-]{3,100}$")
_DEFAULT_RETENTION = 50
_MAX_RETENTION = 200
_STALE_AFTER = timedelta(hours=36)


class SnapshotRepository(Protocol):
    def save(
        self,
        workstation_id: str,
        payload: dict,
        *,
        client_id: str,
        digest: str,
        retention: int,
        enforce_dynamic_binding: bool = False,
    ) -> dict: ...

    def latest(self, workstation_id: str) -> dict | None: ...


def parse_workstation_bindings(raw: str) -> dict[str, str]:
    """Config privada: um client_id exclusivo para exatamente um workstation UUID.

    Ambiguidade ou configuracao parcial falham fechado. IDs nao sao secretos.
    """
    out: dict[str, str] = {}
    taken: set[str] = set()
    if not raw.strip():
        return out
    for entry in raw.split(";"):
        if entry.count("=") != 1:
            raise PersistenceUnavailableError(
                "workstation_ingest_config_invalid", "Vinculos S2S de computadores invalidos."
            )
        name, raw_id = (part.strip() for part in entry.split("=", 1))
        try:
            device_id = str(uuid.UUID(raw_id))
        except (ValueError, AttributeError):
            raise PersistenceUnavailableError(
                "workstation_ingest_config_invalid", "Vinculos S2S de computadores invalidos."
            ) from None
        if (not _CLIENT_ID.fullmatch(name) or name in out or
                device_id in taken or uuid.UUID(device_id).int == 0):
            raise PersistenceUnavailableError(
                "workstation_ingest_config_invalid", "Vinculos S2S de computadores invalidos."
            )
        out[name] = device_id
        taken.add(device_id)
    return out


def _retention_limit() -> int:
    try:
        value = int(settings.WORKSTATION_SNAPSHOT_RETENTION)
    except (ValueError, TypeError):
        return _DEFAULT_RETENTION
    return min(_MAX_RETENTION, max(1, value))


def _enabled() -> None:
    if not settings.WORKSTATION_INGEST_ENABLED:
        raise ConflictError(
            "workstation_ingest_disabled", "Ingestao automatica de computadores nao habilitada."
        )


class WorkstationSnapshotService:
    def __init__(self, repository: SnapshotRepository):
        self.repository = repository

    def ingest(self, workstation_id: str, raw: object, *, client_id: str) -> dict:
        _enabled()
        dynamic = settings.WORKSTATION_DB_BINDINGS_ENABLED
        if dynamic:
            # Client ID derivado do UUID, verificado contra JWT assinado na rota.
            # Permissao final e atomicamente checada no PostgreSQL com FOR SHARE.
            valid_binding = client_id == device_client_id(workstation_id)
        else:
            binding = parse_workstation_bindings(settings.WORKSTATION_COLLECTOR_BINDINGS)
            valid_binding = bool(binding) and binding.get(client_id) == workstation_id
        if not valid_binding:
            raise ConflictError(
                "workstation_collector_binding_forbidden",
                "Identidade do coletor nao autorizada para este computador.",
            )
        try:
            snapshot = validate_workstation_snapshot(raw)
        except SnapshotValidationError as exc:
            raise ValidationError(
                "invalid_workstation_snapshot",
                "Snapshot de inventario invalido.",
                {"fields": {exc.field: "Dado invalido ou nao permitido."}},
            ) from None

        # Canonicalizar para identificar replays adulterados usando o mesmo run_id.
        canonical = json.dumps(
            snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()

        return self.repository.save(
            workstation_id,
            snapshot,
            client_id=client_id,
            digest=digest,
            retention=_retention_limit(),
            enforce_dynamic_binding=dynamic,
        )

    def latest(self, workstation_id: str) -> dict | None:
        record = self.repository.latest(workstation_id)
        if record is None:
            return None
        observed_at = record["observed_at"]
        if isinstance(observed_at, str):
            observed_at = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if observed_at.tzinfo is None:
            raise PersistenceUnavailableError(
                "invalid_snapshot_timestamp", "Horario de inventario inconsistente."
            )
        elapsed = datetime.now(timezone.utc) - observed_at.astimezone(timezone.utc)
        return {
            "observed_at": record["observed_at"],
            "received_at": record["received_at"],
            "status": record["status"],
            "freshness": "stale" if elapsed > _STALE_AFTER else "recent",
            "snapshot": record["payload"],
        }
