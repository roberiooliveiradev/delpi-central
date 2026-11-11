"""Repositório em memória de observações — exclusivo de testes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.observations import ObservationIngest


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class InMemoryObservationRepository:
    observations: dict[str, dict] = field(default_factory=dict)
    by_run_id: dict[str, str] = field(default_factory=dict)
    servers: object | None = None

    def get_by_run_id(self, run_id: str) -> dict | None:
        observation_id = self.by_run_id.get(run_id)
        return None if observation_id is None else dict(self.observations[observation_id])

    def get_latest_for_server(self, server_id: str) -> dict | None:
        items = self.list_for_server(server_id, limit=1)
        return items[0] if items else None

    def list_for_server(self, server_id: str, *, limit: int) -> list[dict]:
        rows = [row for row in self.observations.values() if row["server_id"] == server_id]
        rows.sort(key=lambda row: (row["observed_at"], row["created_at"]), reverse=True)
        return [dict(row) for row in rows[:limit]]

    def insert_observation(
        self,
        observation_id: str,
        server_id: str,
        ingest: ObservationIngest,
        *,
        collector_client_id: str,
        divergences: list[dict],
        retention: int,
    ) -> dict:
        if self.servers is not None:
            server = self.servers.get_server(server_id)
            if server is None or server.get("archived"):
                raise ConflictError(
                    "server_archived",
                    "Servidor arquivado: restaure o cadastro antes de receber observações.",
                )
        if ingest.run_id in self.by_run_id:
            return self.get_by_run_id(ingest.run_id)
        row = {
            "id": observation_id,
            "server_id": server_id,
            "run_id": ingest.run_id,
            "source": ingest.source,
            "collector_client_id": collector_client_id,
            "observed_at": ingest.observed_at,
            "received_at": _now(),
            "schema_version": ingest.schema_version,
            "status": ingest.status,
            "summary": dict(ingest.summary),
            "sections_status": dict(ingest.sections_status),
            "divergences": list(divergences),
            "created_at": _now(),
        }
        self.observations[observation_id] = row
        self.by_run_id[ingest.run_id] = observation_id
        # retenção
        kept = self.list_for_server(server_id, limit=retention)
        keep_ids = {item["id"] for item in kept}
        for oid, item in list(self.observations.items()):
            if item["server_id"] == server_id and oid not in keep_ids:
                del self.observations[oid]
                self.by_run_id.pop(item["run_id"], None)
        return dict(self.observations[observation_id])
