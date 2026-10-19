from __future__ import annotations

import logging
from typing import Any

from purchase_requests_app.infrastructure.gateways.core_protheus_identity_gateway import (
    CoreProtheusIdentityGateway,
    CoreProtheusIdentityUnavailableError,
    protheus_identity_owner,
)
from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

logger = logging.getLogger(__name__)


class UserProtheusMappingRepository:
    """Facade: Core is authoritative when PROTHEUS_IDENTITY_OWNER=core."""

    def __init__(
        self,
        *,
        core_gateway: CoreProtheusIdentityGateway | None = None,
    ) -> None:
        self._core = core_gateway or CoreProtheusIdentityGateway()

    def get_mapping(self, user_id: str) -> dict[str, Any] | None:
        if protheus_identity_owner() == "core":
            try:
                return self._core.get_by_user_id(user_id)
            except CoreProtheusIdentityUnavailableError:
                logger.exception("core_protheus_identity_read_failed user_id=%s", user_id)
                raise
        return self._get_mapping_local(user_id)

    def upsert_mapping(
        self,
        *,
        user_id: str,
        protheus_user_id: str | None,
        protheus_user_code: str | None,
        mapping_status: str,
        mapping_source: str | None,
        verified: bool,
    ) -> dict[str, Any]:
        if protheus_identity_owner() == "core":
            try:
                return self._core.upsert(
                    user_id=user_id,
                    protheus_user_id=protheus_user_id,
                    protheus_user_code=protheus_user_code,
                    mapping_status=mapping_status,
                    mapping_source=mapping_source,
                    verified=verified,
                )
            except CoreProtheusIdentityUnavailableError:
                logger.exception("core_protheus_identity_write_failed user_id=%s", user_id)
                raise
        return self._upsert_mapping_local(
            user_id=user_id,
            protheus_user_id=protheus_user_id,
            protheus_user_code=protheus_user_code,
            mapping_status=mapping_status,
            mapping_source=mapping_source,
            verified=verified,
        )

    def get_mapping_by_protheus_user_id(
        self,
        protheus_user_id: str,
    ) -> dict[str, Any] | None:
        normalized = (protheus_user_id or "").strip()
        if not normalized:
            return None
        if protheus_identity_owner() == "core":
            try:
                return self._core.get_by_protheus_user_id(normalized)
            except CoreProtheusIdentityUnavailableError:
                logger.exception(
                    "core_protheus_identity_reverse_lookup_failed protheus_user_id=%s",
                    normalized,
                )
                raise
        return self._get_mapping_by_protheus_user_id_local(normalized)

    def list_mappings(self) -> list[dict[str, Any]]:
        # Admin list remains local during transition; Core has no unrestricted list.
        if protheus_identity_owner() == "core":
            logger.warning(
                "list_mappings_not_supported_on_core_owner — returning local snapshot if any"
            )
        return self._list_mappings_local()

    def _get_mapping_local(self, user_id: str) -> dict[str, Any] | None:
        sql = """
        SELECT user_id, protheus_user_id, protheus_user_code, mapping_status,
               mapping_source, verified, created_at, updated_at
        FROM purchase_requests.user_protheus_mappings
        WHERE user_id = %s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def _upsert_mapping_local(
        self,
        *,
        user_id: str,
        protheus_user_id: str | None,
        protheus_user_code: str | None,
        mapping_status: str,
        mapping_source: str | None,
        verified: bool,
    ) -> dict[str, Any]:
        sql = """
        INSERT INTO purchase_requests.user_protheus_mappings
            (user_id, protheus_user_id, protheus_user_code, mapping_status, mapping_source, verified)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            protheus_user_id = EXCLUDED.protheus_user_id,
            protheus_user_code = EXCLUDED.protheus_user_code,
            mapping_status = EXCLUDED.mapping_status,
            mapping_source = EXCLUDED.mapping_source,
            verified = EXCLUDED.verified,
            updated_at = NOW()
        RETURNING user_id, protheus_user_id, protheus_user_code, mapping_status,
                  mapping_source, verified, created_at, updated_at
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        user_id,
                        protheus_user_id,
                        protheus_user_code,
                        mapping_status,
                        mapping_source,
                        verified,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row)

    def _get_mapping_by_protheus_user_id_local(
        self,
        protheus_user_id: str,
    ) -> dict[str, Any] | None:
        sql = """
        SELECT user_id, protheus_user_id, protheus_user_code, mapping_status,
               mapping_source, verified, created_at, updated_at
        FROM purchase_requests.user_protheus_mappings
        WHERE mapping_status = 'mapped'
          AND BTRIM(protheus_user_id) = %s
        LIMIT 1
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (protheus_user_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def _list_mappings_local(self) -> list[dict[str, Any]]:
        sql = """
        SELECT user_id, protheus_user_id, protheus_user_code, mapping_status,
               mapping_source, verified, created_at, updated_at
        FROM purchase_requests.user_protheus_mappings
        ORDER BY updated_at DESC
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return [dict(row) for row in rows]
