"""Job assíncrono de import OpenAPI — Playbook 16 Sprint B."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import requests
from flask import Flask

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.extensions.db import db
from app.infrastructure.config.settings import Settings
from app.infrastructure.db.models.external_action_import_job_model import (
    ExternalActionImportJobModel,
)

logger = logging.getLogger(__name__)


class ExternalActionImportJobService:
    @classmethod
    def start(
        cls,
        app: Flask,
        *,
        provider_key: str,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        job = ExternalActionImportJobModel(
            provider_key=str(provider_key).strip(),
            user_id=UUID(user_id) if user_id else None,
            agent_id=UUID(agent_id) if agent_id else None,
            status="queued",
            phase="queued",
            progress_done=0,
            progress_total=0,
        )
        db.session.add(job)
        db.session.flush()

        job_id = str(job.id)
        db.session.commit()

        thread = threading.Thread(
            target=cls._run,
            kwargs={
                "app": app,
                "job_id": job_id,
                "provider_key": provider_key,
            },
            daemon=True,
            name=f"external-action-import-{job_id[:8]}",
        )
        thread.start()

        return cls.to_dict(job)

    @classmethod
    def get(cls, *, provider_key: str, job_id: str) -> dict[str, Any] | None:
        job = cls._load_job(provider_key=provider_key, job_id=job_id)

        if not job:
            return None

        return cls.to_dict(job)

    @classmethod
    def get_latest(cls, *, provider_key: str) -> dict[str, Any] | None:
        job = (
            ExternalActionImportJobModel.query.filter_by(
                provider_key=str(provider_key).strip(),
            )
            .order_by(ExternalActionImportJobModel.started_at.desc())
            .first()
        )

        if not job:
            return None

        return cls.to_dict(job)

    @classmethod
    def run_to_completion(
        cls,
        app: Flask,
        *,
        provider_key: str,
        schema_json: dict | None = None,
        source_type: str = "url",
        source_url: str | None = None,
        skip_embeddings: bool = False,
    ) -> dict[str, Any]:
        job = ExternalActionImportJobModel(
            provider_key=str(provider_key).strip(),
            status="queued",
            phase="queued",
            progress_done=0,
            progress_total=0,
        )
        db.session.add(job)
        db.session.flush()

        job_id = str(job.id)
        db.session.commit()

        with app.app_context():
            cls._execute_job(
                job_id=job_id,
                provider_key=provider_key,
                schema_json=schema_json,
                source_type=source_type,
                source_url=source_url,
                skip_embeddings=skip_embeddings,
            )
            db.session.commit()

        finished = cls._load_job(provider_key=provider_key, job_id=job_id)

        if not finished:
            raise RuntimeError(f"Import job not found after completion: {job_id}")

        return cls.to_dict(finished)

    @classmethod
    def to_dict(cls, job: ExternalActionImportJobModel) -> dict[str, Any]:
        phase = str(job.phase or "")
        status = str(job.status or "")

        return {
            "jobId": str(job.id),
            "providerKey": job.provider_key,
            "status": status,
            "phase": phase,
            "phaseLabel": ExternalActionResponseContentService.get(
                "importJob",
                "phaseLabels",
                phase,
                default=phase,
            ),
            "progress": {
                "done": int(job.progress_done or 0),
                "total": int(job.progress_total or 0),
                "unit": "actions",
            },
            "result": job.result if isinstance(job.result, dict) else None,
            "error": job.error,
            "startedAt": job.started_at.isoformat() if job.started_at else None,
            "updatedAt": job.updated_at.isoformat() if job.updated_at else None,
            "pollUrl": f"/chat/providers/{job.provider_key}/import/jobs/{job.id}",
        }

    @classmethod
    def _load_job(
        cls,
        *,
        provider_key: str,
        job_id: str,
    ) -> ExternalActionImportJobModel | None:
        try:
            job_uuid = UUID(str(job_id))
        except ValueError:
            return None

        return ExternalActionImportJobModel.query.filter_by(
            id=job_uuid,
            provider_key=str(provider_key).strip(),
        ).first()

    @classmethod
    def _run(cls, app: Flask, *, job_id: str, provider_key: str) -> None:
        with app.app_context():
            try:
                cls._execute_job(job_id=job_id, provider_key=provider_key)
                db.session.commit()
            except Exception as exc:
                logger.exception(
                    "external_action_import_job_failed",
                    extra={"job_id": job_id, "provider_key": provider_key},
                )

                try:
                    db.session.rollback()
                except Exception:
                    pass

                cls._mark_failed(job_id=job_id, provider_key=provider_key, error=str(exc))

    @classmethod
    def _execute_job(
        cls,
        *,
        job_id: str,
        provider_key: str,
        schema_json: dict | None = None,
        source_type: str = "url",
        source_url: str | None = None,
        skip_embeddings: bool = False,
    ) -> None:
        from app.composition.external_action_composer import (
            make_postgres_external_action_repository,
        )

        job = cls._load_job(provider_key=provider_key, job_id=job_id)

        if not job:
            return

        repository = make_postgres_external_action_repository()
        provider = repository.get_provider_by_key(provider_key)

        if not provider:
            raise ValueError(f"Provider not found: {provider_key}")

        resolved_schema = schema_json
        resolved_source_type = source_type
        resolved_source_url = source_url

        if resolved_schema is None:
            if not provider.openapi_url:
                raise ValueError("openApiUrl is required")

            cls._update_job(
                job,
                status="running",
                phase="fetch_schema",
                progress_done=0,
                progress_total=0,
            )
            db.session.commit()

            response = requests.get(provider.openapi_url, timeout=20)
            response.raise_for_status()
            resolved_schema = response.json()
            resolved_source_type = "url"
            resolved_source_url = provider.openapi_url

        if not isinstance(resolved_schema, dict):
            raise ValueError("OpenAPI response must be a JSON object")

        cls._update_job(
            job,
            status="running",
            phase="import_actions",
            progress_done=0,
            progress_total=0,
        )
        db.session.commit()

        import_result = repository.import_schema_from_json(
            provider_key=provider_key,
            schema_json=resolved_schema,
            source_type=resolved_source_type,
            source_url=resolved_source_url,
            embed_on_import=False,
        )

        actions_imported = int(import_result.get("actionsImported") or 0)

        cls._update_job(
            job,
            phase="import_actions",
            progress_done=actions_imported,
            progress_total=actions_imported,
            result={
                "actionsImported": actions_imported,
                "schemaHash": import_result.get("schemaHash"),
                "embeddingsUpdated": 0,
            },
        )
        db.session.commit()

        if skip_embeddings or not repository.embedding_service:
            cls._update_job(
                job,
                status="completed",
                phase="done",
                result={
                    **(job.result or {}),
                    "embeddingsUpdated": 0,
                    "embeddingsSkipped": True,
                },
            )
            db.session.commit()
            return

        cls._update_job(
            job,
            phase="embed_actions",
            progress_done=0,
            progress_total=actions_imported,
        )
        db.session.commit()

        def on_progress(done: int, total: int) -> None:
            refreshed = cls._load_job(provider_key=provider_key, job_id=job_id)

            if not refreshed:
                return

            cls._update_job(
                refreshed,
                progress_done=done,
                progress_total=total,
            )

            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        embed_result = repository.backfill_action_embeddings(
            provider_key=provider_key,
            on_progress=on_progress,
            commit_batch_size=Settings.EXTERNAL_ACTION_IMPORT_EMBED_BATCH_SIZE,
        )

        cls._update_job(
            job,
            status="completed",
            phase="done",
            progress_done=int(embed_result.get("total") or actions_imported),
            progress_total=int(embed_result.get("total") or actions_imported),
            result={
                "actionsImported": actions_imported,
                "schemaHash": import_result.get("schemaHash"),
                "embeddingsUpdated": int(embed_result.get("updated") or 0),
                "embeddingsSkipped": int(embed_result.get("skipped") or 0),
            },
        )
        db.session.commit()

    @classmethod
    def _update_job(
        cls,
        job: ExternalActionImportJobModel,
        *,
        status: str | None = None,
        phase: str | None = None,
        progress_done: int | None = None,
        progress_total: int | None = None,
        result: dict | None = None,
        error: str | None = None,
    ) -> None:
        if status is not None:
            job.status = status

        if phase is not None:
            job.phase = phase

        if progress_done is not None:
            job.progress_done = progress_done

        if progress_total is not None:
            job.progress_total = progress_total

        if result is not None:
            job.result = result

        if error is not None:
            job.error = error

        job.updated_at = datetime.now(timezone.utc)
        db.session.add(job)

    @classmethod
    def _mark_failed(cls, *, job_id: str, provider_key: str, error: str) -> None:
        job = cls._load_job(provider_key=provider_key, job_id=job_id)

        if not job:
            return

        cls._update_job(
            job,
            status="failed",
            phase="failed",
            error=error,
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
