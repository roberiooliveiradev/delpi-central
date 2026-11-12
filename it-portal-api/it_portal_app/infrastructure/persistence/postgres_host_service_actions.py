"""#1585. Durable command queue with at-most-once dispatch and audited outcomes."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid

from it_portal_app.application.ports import Actor, AuditEvent
from it_portal_app.domain.errors import ConflictError, NotFoundError
from it_portal_app.infrastructure.persistence.postgres_base import PostgresRepositoryBase

_S = "it_portal"
_TERMINAL = frozenset({"succeeded", "failed", "timeout"})
# Queue TTL 30s. Agent has 75s to report, then result is unknown/no retry.
_JOB_COLUMNS = (
    "id, server_id, service_key, service_name, action, state_before, status, "
    "state_after, error_code, requested_at, claimed_at, finished_at, requested_by_name"
)


def _public(row: dict) -> dict:
    return {key: (str(value) if isinstance(value, uuid.UUID) else value)
            for key, value in row.items()}


class PostgresHostServiceActions(PostgresRepositoryBase):
    @staticmethod
    def _expire(conn, server_id: str) -> None:
        # No automatic retry: a claimed Windows command could already have executed.
        conn.execute(
            f"""UPDATE {_S}.host_service_actions
                SET status='timeout', finished_at=now(), error_code='timeout'
                WHERE server_id=%s AND (
                    (status='queued' AND requested_at < now()-interval '30 seconds')
                    OR (status='running' AND claimed_at < now()-interval '75 seconds')
                )""",
            (server_id,),
        )

    def enqueue(self, server_id: str, service_key: str, action: str,
                request_id: str, actor: Actor) -> dict:
        with self._tx() as conn:
            # Serialize dispatch with snapshot updates and other operators.
            server = conn.execute(
                f"SELECT archived_at FROM {_S}.servers WHERE id=%s FOR UPDATE",
                (server_id,),
            ).fetchone()
            if server is None or server["archived_at"] is not None:
                raise ConflictError("server_unavailable", "Servidor indisponível.")
            self._expire(conn, server_id)
            prior = conn.execute(
                f"""SELECT {_JOB_COLUMNS} FROM {_S}.host_service_actions
                    WHERE server_id=%s AND requested_by_id=%s AND request_id=%s""",
                (server_id, actor.id, request_id),
            ).fetchone()
            if prior:
                if prior["service_key"] != service_key or prior["action"] != action:
                    raise ConflictError("control_request_conflict", "Solicitação duplicada com dados diferentes.")
                return _public(prior)
            svc = conn.execute(
                f"""SELECT name, state, start_mode, can_stop, is_present,
                           observed_at FROM {_S}.host_services
                    WHERE server_id=%s AND service_key=%s FOR UPDATE""",
                (server_id, service_key),
            ).fetchone()
            if svc is None or not svc["is_present"]:
                raise NotFoundError("control_service_unavailable", "Serviço não encontrado na coleta atual.")
            if conn.execute(
                f"""SELECT 1 FROM {_S}.host_service_actions WHERE server_id=%s
                    AND service_key=%s AND status IN ('queued','running')""",
                (server_id, service_key),
            ).fetchone():
                raise ConflictError("control_action_in_progress", "Já existe uma ação em andamento para este serviço.")
            # Always recheck actual state in the Windows agent before execution.
            if (action == "start" and (svc["state"] != "stopped" or svc["start_mode"] == "disabled")) or (
                action in {"stop", "restart"} and
                (svc["state"] != "running" or not svc["can_stop"])
            ):
                raise ConflictError("control_state_conflict", "Estado do serviço não permite esta ação.")
            if conn.execute(
                "SELECT %s::timestamptz < now()-interval '12 minutes' AS stale",
                (svc["observed_at"],),
            ).fetchone()["stale"]:
                raise ConflictError("control_inventory_stale", "Inventário desatualizado; aguarde uma nova coleta.")
            job_id = str(uuid.uuid4())
            conn.execute(
                f"""INSERT INTO {_S}.host_service_actions (
                    id, request_id, server_id, service_key, service_name, action,
                    state_before, requested_by_id, requested_by_name
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (job_id, request_id, server_id, service_key, svc["name"], action,
                 svc["state"], actor.id, actor.name),
            )
            self._audit(conn, AuditEvent(
                entity_type="host_service_action", entity_id=job_id,
                server_id=server_id, event_type="host_service_action_requested",
                changes={"service": svc["name"], "action": action, "state_before": svc["state"]},
            ), actor)
            row = conn.execute(
                f"SELECT {_JOB_COLUMNS} FROM {_S}.host_service_actions WHERE id=%s",
                (job_id,),
            ).fetchone()
            return _public(row)

    def status(self, server_id: str, action_id: str) -> dict | None:
        with self._tx() as conn:
            self._expire(conn, server_id)
            row = conn.execute(
                f"SELECT {_JOB_COLUMNS} FROM {_S}.host_service_actions WHERE server_id=%s AND id=%s",
                (server_id, action_id),
            ).fetchone()
            return _public(row) if row else None

    def claim(self, server_id: str, client_id: str) -> dict | None:
        with self._tx() as conn:
            self._expire(conn, server_id)
            # No retry and no duplicate claim, even with concurrent agent sessions.
            row = conn.execute(
                f"""SELECT id, service_name, service_key, action, state_before
                    FROM {_S}.host_service_actions
                    WHERE server_id=%s AND status='queued'
                    ORDER BY requested_at, id
                    LIMIT 1 FOR UPDATE SKIP LOCKED""",
                (server_id,),
            ).fetchone()
            if not row:
                return None
            lease = secrets.token_urlsafe(32)
            conn.execute(
                f"""UPDATE {_S}.host_service_actions
                    SET status='running', claimed_by=%s, claimed_at=now(),
                        lease_sha256=%s WHERE id=%s""",
                (client_id, hashlib.sha256(lease.encode()).hexdigest(), row["id"]),
            )
            return {**_public(row), "lease": lease}

    def finish(self, server_id: str, action_id: str, client_id: str, lease: str,
               *, status: str, state_after: str | None, error_code: str | None) -> dict:
        if not isinstance(lease, str) or not 24 <= len(lease) <= 128:
            raise ConflictError("control_lease_invalid", "Comprovação da execução inválida.")
        with self._tx() as conn:
            self._expire(conn, server_id)
            row = conn.execute(
                f"""SELECT * FROM {_S}.host_service_actions WHERE id=%s
                    AND server_id=%s FOR UPDATE""",
                (action_id, server_id),
            ).fetchone()
            if row is None:
                raise NotFoundError("control_action_not_found", "Solicitação não encontrada.")
            if row["claimed_by"] != client_id or not row["lease_sha256"] or not hmac.compare_digest(
                row["lease_sha256"], hashlib.sha256(lease.encode()).hexdigest()
            ):
                raise ConflictError("control_lease_denied", "Resposta do agente não autorizada.")
            if row["status"] in _TERMINAL:
                if row["status"] == status and row["state_after"] == state_after and row["error_code"] == error_code:
                    return _public({key: row[key] for key in _JOB_COLUMNS.split(", ")})
                raise ConflictError("control_action_expired", "Ação já finalizada; resultado não pode ser sobrescrito.")
            if row["status"] != "running":
                raise ConflictError("control_action_not_claimed", "Ação não está em execução.")
            expected = "stopped" if row["action"] == "stop" else "running"
            if status == "succeeded" and state_after != expected:
                raise ConflictError("control_result_mismatch", "Agente não confirmou o estado esperado.")
            conn.execute(
                f"""UPDATE {_S}.host_service_actions SET status=%s, state_after=%s,
                    error_code=%s, finished_at=now() WHERE id=%s""",
                (status, state_after, error_code, action_id),
            )
            if status == "succeeded":
                # Observacao operacional imediata, confirmada pelo SCM e independente da coleta 5min.
                conn.execute(
                    f"""UPDATE {_S}.host_services SET state=%s, observed_at=now(),
                        updated_at=now() WHERE server_id=%s AND service_key=%s""",
                    (state_after, server_id, row["service_key"]),
                )
            actor = Actor(id=str(row["requested_by_id"]), name=row["requested_by_name"])
            self._audit(conn, AuditEvent(
                entity_type="host_service_action", entity_id=action_id,
                server_id=server_id, event_type="host_service_action_finished",
                changes={"service": row["service_name"], "action": row["action"],
                         "status": status, "state_before": row["state_before"],
                         "state_after": state_after, "error_code": error_code,
                         "confirmed_by_agent": client_id},
            ), actor)
            result = conn.execute(
                f"SELECT {_JOB_COLUMNS} FROM {_S}.host_service_actions WHERE id=%s",
                (action_id,),
            ).fetchone()
            return _public(result)
