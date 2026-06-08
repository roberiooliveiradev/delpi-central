from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func

from app.domain.ports.evaluation_case_repository_port import EvaluationCaseRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.evaluation_case_model import AiEvaluationCaseModel


class PostgresEvaluationCaseRepository(EvaluationCaseRepositoryPort):
    def create(
        self,
        *,
        category: str,
        input_text: str,
        expected_intent: str | None = None,
        expected_answer: str | None = None,
        expected_normalized: str | None = None,
        must_not_use_tools: bool = False,
        must_not_use_rag: bool = False,
        source_feedback_id: int | None = None,
        linked_candidate_id: int | None = None,
        created_by: UUID | None = None,
    ) -> dict:
        row = AiEvaluationCaseModel(
            category=str(category).strip()[:32],
            input=str(input_text).strip(),
            expected_intent=(str(expected_intent).strip()[:80] if expected_intent else None),
            expected_answer=(str(expected_answer).strip() if expected_answer else None),
            expected_normalized=(
                str(expected_normalized).strip()[:240] if expected_normalized else None
            ),
            must_not_use_tools=bool(must_not_use_tools),
            must_not_use_rag=bool(must_not_use_rag),
            source_feedback_id=source_feedback_id,
            linked_candidate_id=linked_candidate_id,
            status="active",
            created_by=created_by,
        )
        db.session.add(row)
        db.session.flush()
        return self._to_dict(row)

    def get(self, case_id: int) -> dict | None:
        row = AiEvaluationCaseModel.query.filter(AiEvaluationCaseModel.id == case_id).first()
        return self._to_dict(row) if row else None

    def list_cases(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        query = AiEvaluationCaseModel.query

        if category:
            query = query.filter(AiEvaluationCaseModel.category == category)

        if status:
            query = query.filter(AiEvaluationCaseModel.status == status)

        total = query.count()
        rows = (
            query.order_by(AiEvaluationCaseModel.updated_at.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 500)))
            .all()
        )
        return [self._to_dict(row) for row in rows], int(total)

    def list_active(self, *, categories: tuple[str, ...] | None = None) -> list[dict]:
        query = AiEvaluationCaseModel.query.filter(AiEvaluationCaseModel.status == "active")

        if categories:
            query = query.filter(AiEvaluationCaseModel.category.in_(categories))

        rows = query.order_by(AiEvaluationCaseModel.id.asc()).all()
        return [self._to_dict(row) for row in rows]

    def update_run_result(
        self,
        case_id: int,
        *,
        passed: bool,
        failure_reason: str | None = None,
    ) -> dict | None:
        row = AiEvaluationCaseModel.query.filter(AiEvaluationCaseModel.id == case_id).first()

        if not row:
            return None

        row.last_run_at = datetime.now(timezone.utc)
        row.last_passed = bool(passed)
        row.last_failure_reason = failure_reason if not passed else None
        row.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return self._to_dict(row)

    def set_status(self, case_id: int, *, status: str) -> dict | None:
        row = AiEvaluationCaseModel.query.filter(AiEvaluationCaseModel.id == case_id).first()

        if not row:
            return None

        row.status = str(status).strip()[:16] or "active"
        row.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return self._to_dict(row)

    def find_duplicate_input(self, *, input_text: str, category: str) -> dict | None:
        normalized = str(input_text or "").strip().lower()

        if not normalized:
            return None

        row = (
            AiEvaluationCaseModel.query.filter(
                AiEvaluationCaseModel.category == category,
                func.lower(AiEvaluationCaseModel.input) == normalized,
                AiEvaluationCaseModel.status == "active",
            )
            .first()
        )
        return self._to_dict(row) if row else None

    def summary(self) -> dict:
        model = AiEvaluationCaseModel
        by_category = dict(
            db.session.query(model.category, func.count()).group_by(model.category).all()
        )
        by_status = dict(
            db.session.query(model.status, func.count()).group_by(model.status).all()
        )
        total = sum(by_status.values())
        failing = model.query.filter(
            model.status == "active",
            model.last_passed.is_(False),
        ).count()
        never_run = model.query.filter(
            model.status == "active",
            model.last_run_at.is_(None),
        ).count()
        passing = model.query.filter(
            model.status == "active",
            model.last_passed.is_(True),
        ).count()

        return {
            "total": int(total),
            "active": int(by_status.get("active", 0)),
            "disabled": int(by_status.get("disabled", 0)),
            "failing": int(failing),
            "passing": int(passing),
            "neverRun": int(never_run),
            "byCategory": {str(k): int(v) for k, v in by_category.items()},
        }

    @staticmethod
    def _to_dict(row: AiEvaluationCaseModel) -> dict:
        return {
            "id": int(row.id),
            "category": str(row.category),
            "input": str(row.input),
            "expectedIntent": row.expected_intent,
            "expectedAnswer": row.expected_answer,
            "expectedNormalized": row.expected_normalized,
            "mustNotUseTools": bool(row.must_not_use_tools),
            "mustNotUseRag": bool(row.must_not_use_rag),
            "sourceFeedbackId": int(row.source_feedback_id) if row.source_feedback_id else None,
            "linkedCandidateId": int(row.linked_candidate_id) if row.linked_candidate_id else None,
            "status": str(row.status),
            "lastRunAt": row.last_run_at.isoformat() if row.last_run_at else None,
            "lastPassed": row.last_passed,
            "lastFailureReason": row.last_failure_reason,
            "createdBy": str(row.created_by) if row.created_by else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }
