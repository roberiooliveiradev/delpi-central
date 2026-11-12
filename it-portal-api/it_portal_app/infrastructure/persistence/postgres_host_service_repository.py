"""Persistence for complete, individually addressable Windows SCM inventory."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from psycopg.types.json import Jsonb

from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.host_services import HostServiceBatch
from it_portal_app.infrastructure.persistence.postgres_base import PostgresRepositoryBase

_S = "it_portal"


def _payload_hash(services: tuple[dict, ...]) -> str:
    encoded = json.dumps(services, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class PostgresHostServiceRepository(PostgresRepositoryBase):
    def ingest_batch(self, server_id: str, collector_client_id: str, batch: HostServiceBatch) -> dict:
        digest = _payload_hash(batch.services)
        with self._tx() as conn:
            # Serialize overlapping inventory runs for one server, including completion.
            server = conn.execute(
                f"SELECT archived_at FROM {_S}.servers WHERE id=%s FOR UPDATE", (server_id,)
            ).fetchone()
            if server is None or server["archived_at"] is not None:
                raise ConflictError("server_unavailable", "Servidor indisponível para coleta.")
            run = conn.execute(
                f"SELECT * FROM {_S}.host_service_runs WHERE run_id=%s FOR UPDATE", (batch.run_id,)
            ).fetchone()
            if run is None:
                conn.execute(
                    f"""INSERT INTO {_S}.host_service_runs
                    (run_id, server_id, collector_client_id, observed_at, batch_count)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (batch.run_id, server_id, collector_client_id,
                     batch.observed_at, batch.batch_count),
                )
            elif (str(run["server_id"]) != server_id
                  or run["collector_client_id"] != collector_client_id
                  or run["observed_at"] != batch.observed_at
                  or run["batch_count"] != batch.batch_count):
                raise ConflictError("run_conflict", "Identidade ou metadados da execução divergentes.")
            old = conn.execute(
                f"""SELECT payload_sha256 FROM {_S}.host_service_batches
                    WHERE run_id=%s AND batch_index=%s""",
                (batch.run_id, batch.batch_index),
            ).fetchone()
            if old is not None and old["payload_sha256"] != digest:
                raise ConflictError("batch_conflict", "Lote já recebido com conteúdo diferente.")
            if old is None:
                if run is not None and run["status"] == "complete":
                    raise ConflictError("run_complete", "Execução já concluída.")
                conn.execute(
                    f"""INSERT INTO {_S}.host_service_batches
                        (run_id, batch_index, payload_sha256, services)
                        VALUES (%s, %s, %s, %s)""",
                    (batch.run_id, batch.batch_index, digest, Jsonb(list(batch.services))),
                )
            batches = conn.execute(
                f"""SELECT batch_index, services FROM {_S}.host_service_batches
                    WHERE run_id=%s ORDER BY batch_index""", (batch.run_id,)
            ).fetchall()
            complete = len(batches) == batch.batch_count
            applied = bool(run and run["applied"])
            count = run["service_count"] if run else 0
            if complete and (run is None or run["status"] != "complete"):
                if [r["batch_index"] for r in batches] != list(range(batch.batch_count)):
                    raise ConflictError("batch_gap", "Índices de lote incompletos.")
                flattened = [item for b in batches for item in b["services"]]
                keys = [item["service_key"] for item in flattened]
                if len(set(keys)) != len(keys):
                    raise ConflictError("duplicate_service", "Serviço repetido entre lotes.")
                count = len(flattened)
                previous = conn.execute(
                    f"SELECT observed_at FROM {_S}.host_service_current WHERE server_id=%s FOR UPDATE",
                    (server_id,),
                ).fetchone()
                # Never replace newer/equal observed data with delayed deliveries.
                applied = previous is None or batch.observed_at > previous["observed_at"]
                if applied:
                    for svc in flattened:
                        conn.execute(
                            f"""INSERT INTO {_S}.host_services
                                (server_id, service_key, name, display_name, description,
                                 state, start_mode, can_stop, is_present, observed_at, last_run_id)
                                VALUES (%(server_id)s, %(service_key)s, %(name)s, %(display_name)s,
                                        %(description)s, %(state)s, %(start_mode)s, %(can_stop)s,
                                        true, %(observed_at)s, %(run_id)s)
                                ON CONFLICT (server_id, service_key) DO UPDATE SET
                                  name=EXCLUDED.name, display_name=EXCLUDED.display_name,
                                  description=EXCLUDED.description, state=EXCLUDED.state,
                                  start_mode=EXCLUDED.start_mode, can_stop=EXCLUDED.can_stop,
                                  is_present=true, observed_at=EXCLUDED.observed_at,
                                  last_run_id=EXCLUDED.last_run_id, updated_at=now()""",
                            {**svc, "server_id": server_id,
                             "observed_at": batch.observed_at, "run_id": batch.run_id},
                        )
                    conn.execute(
                        f"""UPDATE {_S}.host_services SET is_present=false, updated_at=now()
                            WHERE server_id=%s AND last_run_id<>%s AND is_present=true""",
                        (server_id, batch.run_id),
                    )
                    conn.execute(
                        f"""INSERT INTO {_S}.host_service_current
                            (server_id, run_id, observed_at, service_count)
                            VALUES (%s,%s,%s,%s)
                            ON CONFLICT(server_id) DO UPDATE SET
                            run_id=EXCLUDED.run_id, observed_at=EXCLUDED.observed_at,
                            service_count=EXCLUDED.service_count, received_at=now()""",
                        (server_id, batch.run_id, batch.observed_at, count),
                    )
                conn.execute(
                    f"""UPDATE {_S}.host_service_runs SET status='complete', applied=%s,
                        service_count=%s, completed_at=now() WHERE run_id=%s""",
                    (applied, count, batch.run_id),
                )
                # Completed batches retain hashes for replay, not full duplicate payloads.
                conn.execute(
                    f"UPDATE {_S}.host_service_batches SET services=NULL WHERE run_id=%s",
                    (batch.run_id,),
                )
            else:
                # Completed replays carry a stable result.
                if run and run["status"] == "complete":
                    complete = True
                    applied = run["applied"]
                    count = run["service_count"]
            return {
                "run_id": batch.run_id, "server_id": server_id,
                "batch_index": batch.batch_index, "received_batches": len(batches),
                "batch_count": batch.batch_count,
                "status": "complete" if complete else "collecting",
                "applied": bool(applied), "service_count": count,
            }

    def list_services(self, server_id: str, *, q: str | None, state: str | None,
                      start_mode: str | None, present: str, page: int, page_size: int):
        where = ["server_id = %(sid)s"]
        args: dict = {"sid": server_id, "limit": page_size, "offset": (page - 1) * page_size}
        if present != "all":
            where.append("is_present = %(present)s")
            args["present"] = present == "yes"
        if state:
            where.append("state = %(state)s")
            args["state"] = state
        if start_mode:
            where.append("start_mode = %(start_mode)s")
            args["start_mode"] = start_mode
        if q:
            where.append("(name ILIKE %(q)s OR display_name ILIKE %(q)s)")
            args["q"] = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        clause = " AND ".join(where)
        with self._tx() as conn:
            total = conn.execute(
                f"SELECT count(*) AS total FROM {_S}.host_services WHERE {clause}", args
            ).fetchone()["total"]
            rows = conn.execute(
                f"""SELECT name, display_name, description, state, start_mode, can_stop,
                           is_present, observed_at, updated_at
                    FROM {_S}.host_services WHERE {clause}
                    ORDER BY display_name COLLATE "C", service_key COLLATE "C"
                    LIMIT %(limit)s OFFSET %(offset)s""", args,
            ).fetchall()
            current = conn.execute(
                f"""SELECT run_id, observed_at, received_at, service_count
                    FROM {_S}.host_service_current WHERE server_id=%s""", (server_id,)
            ).fetchone()
        if current:
            current = {**current, "run_id": str(current["run_id"])}
        return [dict(row) for row in rows], total, current
