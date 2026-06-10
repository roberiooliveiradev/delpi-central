from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func

from app.domain.ports.fine_tuning_repository_port import FineTuningRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.fine_tuning_dataset_model import AiFineTuningDatasetModel
from app.infrastructure.db.models.fine_tuning_run_model import AiFineTuningRunModel
from app.infrastructure.db.models.fine_tuning_sample_model import AiFineTuningSampleModel


class PostgresFineTuningRepository(FineTuningRepositoryPort):
    # --- datasets ---

    def create_dataset(
        self,
        *,
        name: str,
        description: str | None = None,
        target_model: str = "intent_classifier",
        metadata: dict | None = None,
        created_by: UUID | None = None,
    ) -> dict:
        row = AiFineTuningDatasetModel(
            name=str(name).strip()[:120],
            description=description,
            target_model=str(target_model).strip()[:64] or "intent_classifier",
            dataset_metadata=metadata,
            created_by=created_by,
        )
        db.session.add(row)
        db.session.flush()
        return self._dataset_to_dict(row)

    def get_dataset(self, dataset_id: int) -> dict | None:
        row = AiFineTuningDatasetModel.query.filter_by(id=dataset_id).first()
        return self._dataset_to_dict(row) if row else None

    def list_datasets(self, *, status: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
        query = AiFineTuningDatasetModel.query

        if status:
            query = query.filter(AiFineTuningDatasetModel.status == status)

        total = query.count()
        rows = (
            query.order_by(AiFineTuningDatasetModel.updated_at.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 200)))
            .all()
        )
        return [self._dataset_to_dict(row) for row in rows], int(total)

    def approve_dataset(self, dataset_id: int, *, approved_by: UUID | None = None) -> dict | None:
        row = AiFineTuningDatasetModel.query.filter_by(id=dataset_id).first()

        if not row:
            return None

        row.status = "approved"
        row.approved_by = approved_by
        row.approved_at = datetime.now(timezone.utc)
        row.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return self._dataset_to_dict(row)

    # --- samples ---

    def create_sample(
        self,
        *,
        messages_json: list,
        category: str = "routing",
        source: str,
        source_ref: str | None = None,
        intent_label: str | None = None,
        quality_score: float | None = None,
        anonymized: bool = False,
        risk_level: str | None = None,
        dataset_id: int | None = None,
        created_by: UUID | None = None,
    ) -> dict:
        row = AiFineTuningSampleModel(
            dataset_id=dataset_id,
            category=str(category).strip()[:32] or "routing",
            source=str(source).strip()[:48],
            source_ref=str(source_ref).strip()[:120] if source_ref else None,
            status="captured",
            messages_json=messages_json,
            intent_label=(str(intent_label).strip()[:80] if intent_label else None),
            quality_score=quality_score,
            anonymized=bool(anonymized),
            risk_level=risk_level,
            created_by=created_by,
        )
        db.session.add(row)
        db.session.flush()
        return self._sample_to_dict(row)

    def find_sample_by_source(self, *, source: str, source_ref: str) -> dict | None:
        row = AiFineTuningSampleModel.query.filter_by(
            source=source,
            source_ref=source_ref,
        ).first()
        return self._sample_to_dict(row) if row else None

    def get_sample(self, sample_id: int) -> dict | None:
        row = AiFineTuningSampleModel.query.filter_by(id=sample_id).first()
        return self._sample_to_dict(row) if row else None

    def list_samples(
        self,
        *,
        status: str | None = None,
        dataset_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        query = AiFineTuningSampleModel.query

        if status:
            query = query.filter(AiFineTuningSampleModel.status == status)

        if dataset_id is not None:
            query = query.filter(AiFineTuningSampleModel.dataset_id == dataset_id)

        total = query.count()
        rows = (
            query.order_by(AiFineTuningSampleModel.updated_at.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 500)))
            .all()
        )
        return [self._sample_to_dict(row) for row in rows], int(total)

    def list_approved_for_dataset(self, dataset_id: int) -> list[dict]:
        rows = (
            AiFineTuningSampleModel.query.filter(
                AiFineTuningSampleModel.dataset_id == dataset_id,
                AiFineTuningSampleModel.status == "approved",
            )
            .order_by(AiFineTuningSampleModel.id.asc())
            .all()
        )
        return [self._sample_to_dict(row) for row in rows]

    def update_sample_status(
        self,
        sample_id: int,
        *,
        status: str,
        reviewer_id: UUID | None = None,
        dataset_id: int | None = None,
    ) -> dict | None:
        row = AiFineTuningSampleModel.query.filter_by(id=sample_id).first()

        if not row:
            return None

        row.status = str(status).strip()[:24]
        row.reviewer_id = reviewer_id
        row.updated_at = datetime.now(timezone.utc)

        if dataset_id is not None:
            row.dataset_id = dataset_id

        db.session.flush()
        return self._sample_to_dict(row)

    def assign_samples_to_dataset(self, *, dataset_id: int, sample_ids: list[int]) -> int:
        if not sample_ids:
            return 0

        updated = (
            AiFineTuningSampleModel.query.filter(
                AiFineTuningSampleModel.id.in_(sample_ids),
                AiFineTuningSampleModel.status == "approved",
            )
            .update(
                {
                    AiFineTuningSampleModel.dataset_id: dataset_id,
                    AiFineTuningSampleModel.updated_at: datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        db.session.flush()
        return int(updated or 0)

    # --- runs ---

    def create_run(
        self,
        *,
        dataset_id: int,
        target_model: str,
        created_by: UUID | None = None,
    ) -> dict:
        row = AiFineTuningRunModel(
            dataset_id=dataset_id,
            status="pending",
            target_model=str(target_model).strip()[:64],
            created_by=created_by,
        )
        db.session.add(row)
        db.session.flush()
        return self._run_to_dict(row)

    def get_run(self, run_id: int) -> dict | None:
        row = AiFineTuningRunModel.query.filter_by(id=run_id).first()
        return self._run_to_dict(row) if row else None

    def update_run(
        self,
        run_id: int,
        *,
        status: str | None = None,
        export_stats: dict | None = None,
        metrics: dict | None = None,
        error_message: str | None = None,
        active_deploy: bool | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> dict | None:
        row = AiFineTuningRunModel.query.filter_by(id=run_id).first()

        if not row:
            return None

        if status is not None:
            row.status = status

        if export_stats is not None:
            row.export_stats = export_stats

        if metrics is not None:
            row.metrics = metrics

        if error_message is not None:
            row.error_message = error_message

        if active_deploy is not None:
            row.active_deploy = bool(active_deploy)

        if started_at is not None:
            row.started_at = started_at

        if completed_at is not None:
            row.completed_at = completed_at

        row.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return self._run_to_dict(row)

    def deactivate_deploys(self, *, target_model: str, except_run_id: int | None = None) -> None:
        query = AiFineTuningRunModel.query.filter(
            AiFineTuningRunModel.target_model == target_model,
            AiFineTuningRunModel.active_deploy.is_(True),
        )

        if except_run_id is not None:
            query = query.filter(AiFineTuningRunModel.id != except_run_id)

        query.update(
            {AiFineTuningRunModel.active_deploy: False},
            synchronize_session=False,
        )
        db.session.flush()

    def list_runs(self, *, dataset_id: int | None = None, limit: int = 20) -> list[dict]:
        query = AiFineTuningRunModel.query

        if dataset_id is not None:
            query = query.filter(AiFineTuningRunModel.dataset_id == dataset_id)

        rows = (
            query.order_by(AiFineTuningRunModel.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        return [self._run_to_dict(row) for row in rows]

    def get_active_deployed_ollama_model(self) -> str | None:
        row = (
            AiFineTuningRunModel.query.filter(
                AiFineTuningRunModel.active_deploy.is_(True),
                AiFineTuningRunModel.status.in_(("completed", "deployed")),
            )
            .order_by(AiFineTuningRunModel.updated_at.desc())
            .first()
        )

        if not row or not isinstance(row.metrics, dict):
            return None

        model_name = str(row.metrics.get("ollamaModelName") or "").strip()
        return model_name or None

    def summary(self) -> dict:
        sample_model = AiFineTuningSampleModel
        dataset_model = AiFineTuningDatasetModel
        run_model = AiFineTuningRunModel

        by_status = dict(
            db.session.query(sample_model.status, func.count()).group_by(sample_model.status).all()
        )
        datasets_approved = dataset_model.query.filter(dataset_model.status == "approved").count()
        active_deploy = run_model.query.filter(run_model.active_deploy.is_(True)).count()

        return {
            "samplesTotal": int(sum(by_status.values())),
            "samplesCaptured": int(by_status.get("captured", 0)),
            "samplesApproved": int(by_status.get("approved", 0)),
            "samplesRejected": int(by_status.get("rejected", 0)),
            "datasetsApproved": int(datasets_approved),
            "activeDeploys": int(active_deploy),
        }

    @staticmethod
    def _dataset_to_dict(row: AiFineTuningDatasetModel) -> dict:
        return {
            "id": int(row.id),
            "name": str(row.name),
            "description": row.description,
            "status": str(row.status),
            "targetModel": str(row.target_model),
            "metadata": row.dataset_metadata,
            "createdBy": str(row.created_by) if row.created_by else None,
            "approvedBy": str(row.approved_by) if row.approved_by else None,
            "approvedAt": row.approved_at.isoformat() if row.approved_at else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    @staticmethod
    def _sample_to_dict(row: AiFineTuningSampleModel) -> dict:
        return {
            "id": int(row.id),
            "datasetId": int(row.dataset_id) if row.dataset_id else None,
            "category": str(row.category),
            "source": str(row.source),
            "sourceRef": row.source_ref,
            "status": str(row.status),
            "messages": row.messages_json,
            "intentLabel": row.intent_label,
            "qualityScore": float(row.quality_score) if row.quality_score is not None else None,
            "anonymized": bool(row.anonymized),
            "riskLevel": row.risk_level,
            "reviewerId": str(row.reviewer_id) if row.reviewer_id else None,
            "createdBy": str(row.created_by) if row.created_by else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    @staticmethod
    def _run_to_dict(row: AiFineTuningRunModel) -> dict:
        return {
            "id": int(row.id),
            "datasetId": int(row.dataset_id),
            "status": str(row.status),
            "targetModel": str(row.target_model),
            "exportFormat": str(row.export_format),
            "exportStats": row.export_stats,
            "metrics": row.metrics,
            "errorMessage": row.error_message,
            "activeDeploy": bool(row.active_deploy),
            "createdBy": str(row.created_by) if row.created_by else None,
            "startedAt": row.started_at.isoformat() if row.started_at else None,
            "completedAt": row.completed_at.isoformat() if row.completed_at else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }
