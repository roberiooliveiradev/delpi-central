"""Ingestão e consulta de observações automáticas de servidor (E4.S1)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

from it_portal_app.application.ports import ItPortalRepository, ObservationRepository
from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError
from it_portal_app.domain.observations import (
    OBSERVATION_RETENTION_DEFAULT,
    STALE_AFTER_HOURS_DEFAULT,
    ObservationIngest,
    build_observation_ingest,
    compute_divergences,
)
from it_portal_app.domain.servers import normalize_hostname

HISTORY_LIMIT = 50


def _allowlist_server_ids() -> frozenset[str]:
    raw = (os.environ.get("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST") or "").strip()
    return frozenset(item.strip() for item in raw.split(",") if item.strip())


def _windows_collector_bindings() -> dict[str, frozenset[str]]:
    """E4.S3: vínculo explícito client_id -> servidor(es); vazio nega Windows.

    Sintaxe: client-1=uuid-1;client-2=uuid-2 (um cliente por host recomendado).
    Múltiplos UUIDs para o mesmo cliente podem ser separados por vírgula.
    """
    raw = (os.environ.get("IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS") or "").strip()
    parsed: dict[str, set[str]] = {}
    for entry in raw.split(";"):
        if not entry.strip() or "=" not in entry:
            continue
        client, server_ids = entry.split("=", 1)
        client = client.strip()
        if not client:
            continue
        ids = set()
        for candidate in server_ids.split(","):
            try:
                ids.add(str(uuid.UUID(candidate.strip())))
            except (ValueError, AttributeError):
                continue
        if ids:
            parsed.setdefault(client, set()).update(ids)
    return {client: frozenset(ids) for client, ids in parsed.items()}


def _retention() -> int:
    raw = (os.environ.get("IT_PORTAL_OBSERVATION_RETENTION") or "").strip()
    if not raw:
        return OBSERVATION_RETENTION_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        return OBSERVATION_RETENTION_DEFAULT
    return max(1, min(value, 200))


def _stale_after_hours() -> int:
    raw = (os.environ.get("IT_PORTAL_OBSERVATION_STALE_HOURS") or "").strip()
    if not raw:
        return STALE_AFTER_HOURS_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        return STALE_AFTER_HOURS_DEFAULT
    return max(1, min(value, 24 * 30))


def presentation_status(observation: dict | None, *, now: datetime | None = None) -> str:
    """Status exibido na UI: available | partial | stale | unavailable."""
    if observation is None:
        return "unavailable"
    status = observation.get("status")
    if status == "failed":
        return "unavailable"
    observed_at = observation.get("observed_at")
    if isinstance(observed_at, datetime):
        clock = now or datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if clock - observed_at.astimezone(timezone.utc) > timedelta(hours=_stale_after_hours()):
            return "stale"
    if status == "partial":
        return "partial"
    return "available"


class ObservationService:
    def __init__(self, observations: ObservationRepository, servers: ItPortalRepository):
        self._observations = observations
        self._servers = servers

    def ingest(
        self,
        server_id: str,
        raw: dict,
        *,
        collector_client_id: str,
    ) -> dict:
        allowlist = _allowlist_server_ids()
        if not allowlist:
            raise ConflictError(
                "collector_allowlist_empty",
                "Nenhum servidor autorizado para ingestão automática neste ambiente.",
            )
        if server_id not in allowlist:
            raise ConflictError(
                "collector_server_forbidden",
                "Este coletor não está autorizado a enviar observações para o servidor informado.",
            )

        server = self._servers.get_server(server_id)
        if server is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        if server.get("archived"):
            raise ConflictError(
                "server_archived",
                "Servidor arquivado: restaure o cadastro antes de receber observações.",
            )

        ingest = build_observation_ingest(raw)
        if ingest.source == "windows_host_collector":
            permitted = _windows_collector_bindings().get(collector_client_id, frozenset())
            if server_id not in permitted:
                raise ConflictError(
                    "windows_collector_binding_forbidden",
                    "Cliente Windows não autorizado para este servidor.",
                )
        registered_hostname = normalize_hostname(server.get("hostname"))
        if ingest.host_identity.hostname != registered_hostname:
            raise ValidationError(
                "hostname_mismatch",
                "O hostname observado não confere com o cadastro do servidor.",
                {
                    "fields": {
                        "host_identity.hostname": (
                            f"Esperado {registered_hostname}; observado "
                            f"{ingest.host_identity.hostname}."
                        )
                    }
                },
            )

        existing = self._observations.get_by_run_id(ingest.run_id)
        if existing is not None:
            if existing["server_id"] != server_id:
                raise ConflictError(
                    "observation_run_id_conflict",
                    "Este run_id já foi registrado para outro servidor.",
                )
            return existing

        divergences = compute_divergences(server, ingest)
        observation_id = str(uuid.uuid4())
        return self._observations.insert_observation(
            observation_id,
            server_id,
            ingest,
            collector_client_id=collector_client_id,
            divergences=divergences,
            retention=_retention(),
        )

    def latest(self, server_id: str) -> dict | None:
        self._require_server(server_id)
        observation = self._observations.get_latest_for_server(server_id)
        if observation is None:
            return None
        return {**observation, "presentation_status": presentation_status(observation)}

    def list_history(self, server_id: str, *, limit: int = HISTORY_LIMIT) -> list[dict]:
        self._require_server(server_id)
        capped = max(1, min(limit, HISTORY_LIMIT))
        items = self._observations.list_for_server(server_id, limit=capped)
        return [
            {**item, "presentation_status": presentation_status(item)} for item in items
        ]

    def _require_server(self, server_id: str) -> dict:
        server = self._servers.get_server(server_id)
        if server is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        return server
