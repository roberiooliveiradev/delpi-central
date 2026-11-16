"""ATLAS P2.2h.2d: strictly read-only PostgreSQL journal queries.

The caller is the Portal TI BFF and MUST authorize a fresh human Core RBAC
identity before invoking. No MCP tool, approval operation or migration here.
The feature is OFF by default and tables exist only in the CI draft schema.
Never leak challenges, attestation credentials or database error details.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from it_portal_app.domain.errors import NotFoundError, PersistenceUnavailableError
from it_portal_app.infrastructure.persistence.db import (
    atlas_journal_read_connect, atlas_journal_read_db_configured,
)

logger = logging.getLogger(__name__)

# Hardcoded, non-user-controlled target. JOIN requires all immutable OCI
# identity columns and never exposes legacy unbound proposals.
_FROM = """ FROM it_portal.atlas_deploy_proposals AS p
JOIN it_portal.atlas_deploy_oci_bindings AS b
  ON b.proposal_id = p.id
 AND b.requester_subject = p.requester_subject
 AND b.request_id = p.request_id
 AND b.environment = p.environment
 AND b.service_id = p.service_id
 AND b.target_sha = p.target_sha
 AND b.base_sha = p.base_sha
 AND b.sealed_binding_sha256 = p.proposal_hash
 AND b.issued_at = p.created_at
 AND b.expires_at = p.expires_at
WHERE p.service_id = 'public-hub'
  AND b.base_image_id <> b.release_image_id
  AND b.rollback_image_id = b.base_image_id
"""

_SELECT = """SELECT
  p.id, p.requester_subject, p.request_id, p.environment, p.service_id,
  p.status, p.target_sha, p.base_sha, p.created_at, p.expires_at,
  (p.expires_at <= clock_timestamp()) AS expired,
  p.approved_by, p.approved_at, p.revision,
  b.signed_manifest_digest, b.release_image_id, b.base_image_id,
  b.rollback_image_id, b.sealed_binding_sha256
"""

_LIST_FILTER = """ AND (%(environment)s::text IS NULL OR p.environment = %(environment)s)
 AND (%(status)s::text IS NULL OR p.status = %(status)s)
"""
# Static SQL; values remain separate parameters. No secret challenge data.
_SQL_COUNT = "SELECT count(*) AS total" + _FROM + _LIST_FILTER
_SQL_LIST = (
    _SELECT + _FROM + _LIST_FILTER
    + " ORDER BY p.created_at DESC, p.id DESC LIMIT %(page_size)s OFFSET %(offset)s"
)
_SQL_DETAIL = _SELECT + _FROM + " AND p.id = %(proposal_id)s"
_SQL_EVENTS = """SELECT e.event_seq, e.event_type, e.actor_subject, e.occurred_at
  FROM it_portal.atlas_deploy_events AS e
  WHERE e.proposal_id = %s
  ORDER BY e.event_seq ASC
  LIMIT 100
"""
_SQL_SCHEMA = """SELECT
 to_regclass('it_portal.atlas_deploy_proposals') IS NOT NULL AS proposals,
 to_regclass('it_portal.atlas_deploy_oci_bindings') IS NOT NULL AS oci_bindings,
 to_regclass('it_portal.atlas_deploy_events') IS NOT NULL AS audit_events"""


class PostgresAtlasDeployReadRepository:
    """Reads only. Uses a dedicated PostgreSQL SELECT role, never the API write role."""

    def __init__(
        self,
        *,
        connect: Callable[[], Any] = atlas_journal_read_connect,
        configured: Callable[[], bool] = atlas_journal_read_db_configured,
    ):
        self._connect = connect
        self._configured = configured

    def _open_readonly(self):
        if not self._configured():
            raise PersistenceUnavailableError(
                "atlas_journal_unavailable", "Consulta de implantações indisponível."
            )
        try:
            return self._connect()
        except Exception as exc:
            logger.error("atlas_journal_connection_unavailable error_class=%s", type(exc).__name__)
            raise PersistenceUnavailableError(
                "atlas_journal_unavailable", "Consulta de implantações indisponível."
            ) from None

    @staticmethod
    def _require_schema(conn: Any) -> None:
        result = conn.execute(_SQL_SCHEMA).fetchone()
        if not result or not all(result.values()):
            raise PersistenceUnavailableError(
                "atlas_journal_schema_pending",
                "Consulta de implantações ainda não configurada.",
            )

    @staticmethod
    def _entry(row: dict) -> dict:
        # Carefully bounded fields. NEVER return challenge_digest,
        # ci_statement_sha256, host_challenge_sha256 or preview_hash.
        return {
            "id": str(row["id"]),
            "requester_subject": str(row["requester_subject"]),
            "request_id": str(row["request_id"]),
            "environment": row["environment"],
            "service_id": row["service_id"],
            "status": row["status"],
            "target_commit_sha": row["target_sha"],
            "base_commit_sha": row["base_sha"],
            "manifest_digest": row["signed_manifest_digest"],
            "previous_image_id": row["base_image_id"],
            "target_image_id": row["release_image_id"],
            "rollback_image_id": row["rollback_image_id"],
            "binding_sha256": row["sealed_binding_sha256"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "expired": row["expired"],
            "approved_by": str(row["approved_by"]) if row["approved_by"] else None,
            "approved_at": row["approved_at"],
            "revision": row["revision"],
            "can_approve": False,
            "can_execute": False,
        }

    def list_proposals(
        self, *,
        environment: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        if page < 1 or page_size < 1 or page_size > 50 or page > 1000:
            raise ValueError("invalid pagination")
        params = {
            "environment": environment, "status": status,
            "page_size": page_size, "offset": (page - 1) * page_size,
        }
        conn = self._open_readonly()
        try:
            with conn.transaction():
                # First statement sets transaction isolation, protects against
                # data changes between count, rows and detail reads.
                conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                self._require_schema(conn)
                total = conn.execute(_SQL_COUNT, params).fetchone()["total"]
                rows = conn.execute(_SQL_LIST, params).fetchall()
                return {
                    "items": [self._entry(row) for row in rows],
                    "total": int(total),
                    "page": page,
                    "page_size": page_size,
                }
        except PersistenceUnavailableError:
            raise
        except Exception as exc:
            logger.error("atlas_journal_read_failed error_class=%s", type(exc).__name__)
            raise PersistenceUnavailableError(
                "atlas_journal_unavailable", "Consulta de implantações indisponível."
            ) from None
        finally:
            conn.close()

    def get_proposal(self, proposal_id: str) -> dict:
        conn = self._open_readonly()
        try:
            with conn.transaction():
                conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                self._require_schema(conn)
                row = conn.execute(_SQL_DETAIL, {"proposal_id": proposal_id}).fetchone()
                if row is None:
                    raise NotFoundError(
                        "atlas_proposal_not_found", "Solicitação de implantação não encontrada."
                    )
                events = conn.execute(_SQL_EVENTS, (proposal_id,)).fetchall()
                item = self._entry(row)
                item["events"] = [{
                    "sequence": int(e["event_seq"]),
                    "event_type": e["event_type"],
                    "actor_subject": str(e["actor_subject"]) if e["actor_subject"] else None,
                    "occurred_at": e["occurred_at"],
                } for e in events]
                return item
        except (PersistenceUnavailableError, NotFoundError):
            raise
        except Exception as exc:
            logger.error("atlas_journal_detail_failed error_class=%s", type(exc).__name__)
            raise PersistenceUnavailableError(
                "atlas_journal_unavailable", "Consulta de implantações indisponível."
            ) from None
        finally:
            conn.close()
