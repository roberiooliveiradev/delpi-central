"""G2-S4: armazenamento de vinculos de identidade sem segredos ou tokens.

Operacoes sao auditadas em tabela propria, com reserva unica antes da chamada
externa ao Keycloak para impedir concorrencia e adoção silenciosa de clients.
"""
from __future__ import annotations

import uuid

from it_portal_app.application.ports import Actor
from it_portal_app.domain.errors import ConflictError, NotFoundError
from it_portal_app.infrastructure.persistence.postgres_base import PostgresRepositoryBase

T = "it_portal.workstation_agent_identities"
E = "it_portal.workstation_agent_identity_events"


class PostgresWorkstationIdentityStore(PostgresRepositoryBase):
    @staticmethod
    def _row(row):
        return dict(row) if row else None

    def get(self, workstation_id: str) -> dict | None:
        with self._tx() as conn:
            row = conn.execute(
                f"SELECT workstation_id, client_id, state, updated_at, "
                "ingest_authorized, revocation_status "
                f"FROM {T} WHERE workstation_id = %s",
                (workstation_id,),
            ).fetchone()
            return self._row(row)

    @staticmethod
    def _event(conn, workstation_id: str, actor: Actor, event: str) -> None:
        conn.execute(
            f"INSERT INTO {E} "
            "(id, workstation_id, actor_id, actor_name, event_type) "
            "VALUES (%s, %s, %s, %s, %s)",
            (str(uuid.uuid4()), workstation_id, actor.id, actor.name, event),
        )

    def reserve(self, workstation_id: str, client_id: str, actor: Actor) -> dict:
        with self._tx() as conn:
            machine = conn.execute(
                "SELECT archived_at, administrative_status "
                "FROM it_portal.workstations WHERE id = %s FOR UPDATE",
                (workstation_id,),
            ).fetchone()
            if machine is None:
                raise NotFoundError("workstation_not_found", "Computador nao encontrado.")
            if machine["archived_at"] is not None or machine["administrative_status"] != "in_operation":
                raise ConflictError(
                    "workstation_not_eligible",
                    "Somente computadores ativos e em operacao podem preparar identidade.",
                )
            previous = conn.execute(
                f"SELECT state, client_id FROM {T} WHERE workstation_id = %s FOR UPDATE",
                (workstation_id,),
            ).fetchone()
            if previous:
                if previous["client_id"] != client_id:
                    raise ConflictError("workstation_identity_conflict", "Identidade divergente.")
                if previous["state"] == "prepared":
                    return dict(previous)
                raise ConflictError(
                    "workstation_identity_review_required",
                    "Preparacao anterior requer revisao manual; nao repetir criacao no Keycloak.",
                )
            conn.execute(
                f"INSERT INTO {T} "
                "(workstation_id, client_id, created_by_id, created_by_name) "
                "VALUES (%s, %s, %s, %s)",
                (workstation_id, client_id, actor.id, actor.name),
            )
            self._event(conn, workstation_id, actor, "identity_reserved")
            return {"client_id": client_id, "state": "preparing"}

    def prepared(self, workstation_id: str, keycloak_uuid: str, actor: Actor) -> dict:
        with self._tx() as conn:
            row = conn.execute(
                f"UPDATE {T} SET state = 'prepared', keycloak_client_uuid = %s, "
                "updated_at = now() WHERE workstation_id = %s AND state = 'preparing' "
                "RETURNING client_id, state, updated_at",
                (keycloak_uuid, workstation_id),
            ).fetchone()
            if not row:
                raise ConflictError("workstation_identity_state_conflict", "Reserva indisponivel.")
            self._event(conn, workstation_id, actor, "identity_prepared")
            return dict(row)

    def failed(self, workstation_id: str, actor: Actor) -> None:
        with self._tx() as conn:
            row = conn.execute(
                f"UPDATE {T} SET state = 'failed', updated_at = now() "
                "WHERE workstation_id = %s AND state = 'preparing' RETURNING workstation_id",
                (workstation_id,),
            ).fetchone()
            if row:
                self._event(conn, workstation_id, actor, "identity_prepare_failed")

    def request_revocation(self, workstation_id: str, actor: Actor) -> dict | None:
        """Deny DB ingestion BEFORE contacting Keycloak; never retry pending/failed."""
        with self._tx() as conn:
            row = conn.execute(
                f"SELECT client_id, keycloak_client_uuid, state, revocation_status "
                f"FROM {T} WHERE workstation_id = %s FOR UPDATE",
                (workstation_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError("workstation_identity_not_found", "Identidade nao encontrada.")
            if row["state"] == "revoked" and row["revocation_status"] == "confirmed":
                return None  # revogacao completa, idempotente
            if (row["state"] != "prepared" or row["revocation_status"] != "none"
                    or row["keycloak_client_uuid"] is None):
                raise ConflictError(
                    "workstation_identity_revocation_review_required",
                    "Revogacao anterior requer revisao manual pela TI.",
                )
            conn.execute(
                f"UPDATE {T} SET ingest_authorized = FALSE, "
                "revocation_status = 'pending', updated_at = now() "
                "WHERE workstation_id = %s",
                (workstation_id,),
            )
            self._event(conn, workstation_id, actor, "identity_revocation_requested")
            return {
                "client_id": row["client_id"],
                "keycloak_client_uuid": str(row["keycloak_client_uuid"]),
            }

    def complete_revocation(self, workstation_id: str, actor: Actor) -> None:
        with self._tx() as conn:
            row = conn.execute(
                f"UPDATE {T} SET state = 'revoked', revocation_status = 'confirmed', "
                "ingest_authorized = FALSE, revoked_at = now(), revoked_by_id = %s, "
                "updated_at = now() WHERE workstation_id = %s "
                "AND state = 'prepared' AND revocation_status = 'pending' "
                "RETURNING workstation_id",
                (actor.id, workstation_id),
            ).fetchone()
            if not row:
                raise ConflictError(
                    "workstation_identity_revocation_state_invalid",
                    "Revogacao precisa de conciliacao manual.",
                )
            self._event(conn, workstation_id, actor, "identity_revoked")

    def fail_revocation(self, workstation_id: str, actor: Actor) -> None:
        with self._tx() as conn:
            row = conn.execute(
                f"UPDATE {T} SET revocation_status = 'failed', "
                "ingest_authorized = FALSE, updated_at = now() "
                "WHERE workstation_id = %s AND revocation_status = 'pending' "
                "RETURNING workstation_id",
                (workstation_id,),
            ).fetchone()
            if row:
                self._event(conn, workstation_id, actor, "identity_revocation_failed")
