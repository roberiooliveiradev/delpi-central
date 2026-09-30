from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Callable, Sequence, TypeVar

import psycopg

from bpmn_modeler.application.ports import (
    AggregateNotFoundError,
    ConcurrencyConflictError,
    ModelRepositoryPort,
    ModelSummaryRecord,
    RepositoryError,
)
from bpmn_modeler.domain.entities.model import Model
from bpmn_modeler.domain.entities.revision import Revision, RevisionOrigin
from bpmn_modeler.domain.entities.working_copy import WorkingCopy
from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)

from .connection import db_connection

logger = logging.getLogger(__name__)

T = TypeVar("T")

_SORT_MAP = {
    ("updated_at", "desc"): "updated_at DESC, id DESC",
    ("updated_at", "asc"): "updated_at ASC, id ASC",
    ("created_at", "desc"): "created_at DESC, id DESC",
    ("created_at", "asc"): "created_at ASC, id ASC",
    ("display_name", "desc"): "lower(display_name) DESC, id DESC",
    ("display_name", "asc"): "lower(display_name) ASC, id ASC",
}

_ARCHIVED_MAP = {
    "active": "archived_at IS NULL",
    "archived": "archived_at IS NOT NULL",
    "all": "TRUE",
}


def _like_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )


class PostgresModelRepository(ModelRepositoryPort):
    """psycopg adapter — aggregate CAS via SELECT ... FOR UPDATE."""

    def create_aggregate(self, model: Model) -> None:
        try:
            with db_connection() as conn:
                self._insert_model(conn, model)
                for revision in model.revisions:
                    self._insert_revision(conn, model.id, revision)
                conn.commit()
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to create model aggregate") from exc

    def get_aggregate(self, model_id: str) -> Model | None:
        try:
            with db_connection() as conn:
                model = self._load_model(conn, model_id, for_update=False)
                if model is None:
                    return None
                model.revisions = self._load_revisions(conn, model_id)
                return model
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to read model aggregate") from exc

    def list_summaries(
        self,
        *,
        query: str | None,
        archived: str,
        sort: str,
        direction: str,
        offset: int,
        limit: int,
    ) -> Sequence[ModelSummaryRecord]:
        order_by = _SORT_MAP[(sort, direction)]
        where = _ARCHIVED_MAP[archived]
        params: dict[str, object] = {"offset": offset, "limit": limit}

        query_clause = ""
        if query:
            normalized = query.strip()
            if normalized:
                query_clause = (
                    " AND (lower(display_name) LIKE %(query)s ESCAPE '\\'"
                )
                params["query"] = f"%{_like_escape(normalized.lower())}%"
                try:
                    params["query_uuid"] = uuid.UUID(normalized)
                    query_clause += " OR id = %(query_uuid)s"
                except ValueError:
                    pass
                query_clause += ")"

        sql = f"""
            SELECT id, display_name, archived_at, version, created_at, updated_at,
                   (SELECT MAX(r.revision_number) FROM public.revisions r
                    WHERE r.model_id = m.id) AS latest_revision_number
            FROM public.models m
            WHERE {where}{query_clause}
            ORDER BY {order_by}
            OFFSET %(offset)s LIMIT %(limit)s
        """
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list models") from exc
        return [
            ModelSummaryRecord(
                id=str(row["id"]),
                display_name=row["display_name"],
                archived_at=row["archived_at"],
                version=row["version"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                latest_revision_number=row["latest_revision_number"],
            )
            for row in rows
        ]

    def mutate(
        self,
        model_id: str,
        expected_version: int,
        mutation: Callable[[Model], T],
    ) -> tuple[Model, T]:
        try:
            with db_connection() as conn:
                model = self._load_model(conn, model_id, for_update=True)
                if model is None:
                    raise AggregateNotFoundError(model_id)
                if model.version != expected_version:
                    raise ConcurrencyConflictError(model_id, model.version)
                model.revisions = self._load_revisions(conn, model_id)
                outcome = mutation(model)
                self._persist_model(conn, model)
                conn.commit()
                return model, outcome
        except (AggregateNotFoundError, ConcurrencyConflictError):
            raise
        except psycopg.errors.LockNotAvailable as exc:
            raise ConcurrencyConflictError(model_id, expected_version) from exc
        except Exception as exc:
            raise RepositoryError("failed to mutate model aggregate") from exc

    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_model(conn, model_id: str, *, for_update: bool) -> Model | None:
        lock = " FOR UPDATE" if for_update else ""
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, display_name, working_copy_xml, version,
                       archived_at, created_at, updated_at, created_by, updated_by
                FROM public.models WHERE id = %(id)s{lock}
                """,
                {"id": model_id},
            )
            row = cur.fetchone()
        if row is None:
            return None
        return Model(
            id=str(row["id"]),
            working_copy=WorkingCopy(CanonicalBpmnArtifact(row["working_copy_xml"])),
            display_name=row["display_name"],
            version=row["version"],
            archived_at=row["archived_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
        )

    @staticmethod
    def _load_revisions(conn, model_id: str) -> list[Revision]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, revision_number, artifact_xml, artifact_sha256,
                       origin, created_at, created_by
                FROM public.revisions WHERE model_id = %(id)s
                ORDER BY revision_number ASC
                """,
                {"id": model_id},
            )
            rows = cur.fetchall()
        return [
            Revision(
                revision_id=str(row["id"]),
                revision_number=row["revision_number"],
                artifact=CanonicalBpmnArtifact(row["artifact_xml"]),
                checksum=row["artifact_sha256"],
                created_at=row["created_at"],
                created_by=row["created_by"],
                origin=RevisionOrigin(row["origin"]),
            )
            for row in rows
        ]

    def _persist_model(self, conn, model: Model) -> None:
        import hashlib

        sha = hashlib.sha256(
            model.working_copy.artifact.content.encode("utf-8")
        ).hexdigest()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.models
                SET display_name = %(name)s,
                    working_copy_xml = %(xml)s,
                    working_copy_sha256 = %(sha)s,
                    version = %(version)s,
                    updated_at = %(updated_at)s,
                    updated_by = %(updated_by)s,
                    archived_at = %(archived_at)s
                WHERE id = %(id)s
                """,
                {
                    "id": model.id,
                    "name": model.display_name,
                    "xml": model.working_copy.artifact.content,
                    "sha": sha,
                    "version": model.version,
                    "updated_at": model.updated_at,
                    "updated_by": model.updated_by,
                    "archived_at": model.archived_at,
                },
            )
            for revision in model.revisions:
                cur.execute(
                    """
                    INSERT INTO public.revisions
                        (id, model_id, revision_number, artifact_xml,
                         artifact_sha256, origin, created_at, created_by)
                    VALUES (%(id)s, %(model_id)s, %(num)s, %(xml)s,
                            %(sha)s, %(origin)s, %(created_at)s, %(created_by)s)
                    ON CONFLICT (model_id, revision_number) DO NOTHING
                    """,
                    {
                        "id": revision.revision_id,
                        "model_id": model.id,
                        "num": revision.revision_number,
                        "xml": revision.artifact.content,
                        "sha": revision.checksum,
                        "origin": revision.origin.value,
                        "created_at": revision.created_at,
                        "created_by": revision.created_by,
                    },
                )

    @staticmethod
    def _insert_model(conn, model: Model) -> None:
        import hashlib

        sha = hashlib.sha256(
            model.working_copy.artifact.content.encode("utf-8")
        ).hexdigest()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.models
                    (id, display_name, working_copy_xml, working_copy_sha256,
                     version, created_at, created_by, updated_at, updated_by,
                     archived_at)
                VALUES (%(id)s, %(name)s, %(xml)s, %(sha)s, %(version)s,
                        %(created_at)s, %(created_by)s, %(updated_at)s,
                        %(updated_by)s, %(archived_at)s)
                """,
                {
                    "id": model.id,
                    "name": model.display_name,
                    "xml": model.working_copy.artifact.content,
                    "sha": sha,
                    "version": model.version,
                    "created_at": model.created_at or datetime.now(),
                    "created_by": model.created_by,
                    "updated_at": model.updated_at or datetime.now(),
                    "updated_by": model.updated_by,
                    "archived_at": model.archived_at,
                },
            )

    @staticmethod
    def _insert_revision(conn, model_id: str, revision: Revision) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.revisions
                    (id, model_id, revision_number, artifact_xml,
                     artifact_sha256, origin, created_at, created_by)
                VALUES (%(id)s, %(model_id)s, %(num)s, %(xml)s,
                        %(sha)s, %(origin)s, %(created_at)s, %(created_by)s)
                """,
                {
                    "id": revision.revision_id,
                    "model_id": model_id,
                    "num": revision.revision_number,
                    "xml": revision.artifact.content,
                    "sha": revision.checksum,
                    "origin": revision.origin.value,
                    "created_at": revision.created_at,
                    "created_by": revision.created_by,
                },
            )
