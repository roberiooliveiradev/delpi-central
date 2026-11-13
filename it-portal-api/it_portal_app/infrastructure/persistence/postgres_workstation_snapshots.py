"""G2-S2: persistencia transacional, idempotente e separada do cadastro curado."""
from __future__ import annotations

import uuid

from psycopg.types.json import Jsonb

from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError
from it_portal_app.infrastructure.persistence.postgres_base import PostgresRepositoryBase

_TABLE = "it_portal.workstation_snapshots"


class PostgresWorkstationSnapshotRepository(PostgresRepositoryBase):
    def save(
        self, workstation_id: str, payload: dict, *,
        client_id: str, digest: str, retention: int,
    ) -> dict:
        # Lock compartilhado impede arquivamento/troca de hostname durante a escrita.
        with self._tx() as conn:
            workstation = conn.execute(
                "SELECT hostname, archived_at FROM it_portal.workstations "
                "WHERE id = %(id)s FOR SHARE",
                {"id": workstation_id},
            ).fetchone()
            if workstation is None:
                raise NotFoundError("workstation_not_found", "Computador nao encontrado.")
            if workstation["archived_at"] is not None:
                raise ConflictError(
                    "workstation_archived", "Computador arquivado nao recebe inventario."
                )
            if workstation["hostname"].lower().rstrip(".") != payload["host"]["hostname"]:
                raise ValidationError(
                    "workstation_hostname_mismatch",
                    "Hostname observado nao confere com o cadastro do computador.",
                )

            params = {
                "id": str(uuid.uuid4()), "workstation_id": workstation_id,
                "run_id": payload["run_id"], "client_id": client_id,
                "observed_at": payload["observed_at"], "status": payload["status"],
                "payload": Jsonb(payload), "digest": digest,
            }
            inserted = conn.execute(
                f"""INSERT INTO {_TABLE}
                    (id, workstation_id, run_id, collector_client_id, observed_at,
                     status, payload, payload_sha256)
                   VALUES (%(id)s, %(workstation_id)s, %(run_id)s, %(client_id)s,
                           %(observed_at)s, %(status)s, %(payload)s, %(digest)s)
                   ON CONFLICT (workstation_id, run_id) DO NOTHING
                   RETURNING id, received_at""",
                params,
            ).fetchone()
            if inserted is None:
                previous = conn.execute(
                    f"SELECT payload_sha256, collector_client_id, received_at "
                    f"FROM {_TABLE} WHERE workstation_id = %(workstation_id)s "
                    "AND run_id = %(run_id)s",
                    params,
                ).fetchone()
                if (previous is None or previous["payload_sha256"] != digest or
                        previous["collector_client_id"] != client_id):
                    raise ConflictError(
                        "workstation_snapshot_replay_conflict",
                        "Run ID ja utilizado para dados diferentes.",
                    )
                return {
                    "workstation_id": workstation_id,
                    "run_id": payload["run_id"], "observed_at": payload["observed_at"],
                    "received_at": previous["received_at"], "status": payload["status"],
                    "duplicate": True,
                }

            # Mantem as ultimas N observacoes por equipamento. Sem editar workstations.
            conn.execute(
                f"""DELETE FROM {_TABLE}
                    WHERE workstation_id = %(workstation_id)s AND id IN (
                        SELECT id FROM {_TABLE}
                        WHERE workstation_id = %(workstation_id)s
                        ORDER BY observed_at DESC, received_at DESC, id DESC
                        OFFSET %(retention)s
                    )""",
                {"workstation_id": workstation_id, "retention": retention},
            )
            return {
                "workstation_id": workstation_id,
                "run_id": payload["run_id"], "observed_at": payload["observed_at"],
                "received_at": inserted["received_at"], "status": payload["status"],
                "duplicate": False,
            }

    def latest(self, workstation_id: str) -> dict | None:
        with self._tx() as conn:
            row = conn.execute(
                f"""SELECT observed_at, received_at, status, payload FROM {_TABLE}
                    WHERE workstation_id = %(workstation_id)s
                    ORDER BY observed_at DESC, received_at DESC, id DESC LIMIT 1""",
                {"workstation_id": workstation_id},
            ).fetchone()
        return dict(row) if row else None
