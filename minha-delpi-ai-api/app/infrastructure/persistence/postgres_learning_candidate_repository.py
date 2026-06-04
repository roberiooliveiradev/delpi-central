from datetime import datetime, timezone
from uuid import UUID

from app.extensions.db import db
from app.infrastructure.db.models.learning_candidate_model import (
    AiLearningCandidateModel,
)

_ACTIVE_STATUSES = ("pending", "auto_approved")


class PostgresLearningCandidateRepository:
    def find_active_duplicate(
        self,
        *,
        candidate_type: str,
        term: str,
        scope: str,
        project_id: UUID | None = None,
    ) -> dict | None:
        query = AiLearningCandidateModel.query.filter(
            AiLearningCandidateModel.candidate_type == candidate_type,
            AiLearningCandidateModel.term == term,
            AiLearningCandidateModel.scope == scope,
            AiLearningCandidateModel.status.in_(_ACTIVE_STATUSES),
        )

        if project_id is None:
            query = query.filter(AiLearningCandidateModel.project_id.is_(None))
        else:
            query = query.filter(AiLearningCandidateModel.project_id == project_id)

        row = query.order_by(AiLearningCandidateModel.created_at.desc()).first()
        return self._to_dict(row) if row else None

    def create(
        self,
        *,
        candidate_type: str,
        input_text: str,
        term: str | None = None,
        proposed_rule: str | None = None,
        proposed_meaning: str | None = None,
        evidence: dict | None = None,
        confidence: float | None = None,
        evidence_count: int = 1,
        risk_level: str = "low",
        scope: str = "global",
        project_id: UUID | None = None,
        status: str = "pending",
        source: str = "auto",
        created_by: UUID | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        row = AiLearningCandidateModel(
            candidate_type=candidate_type,
            input_text=input_text,
            term=term,
            proposed_rule=proposed_rule,
            proposed_meaning=proposed_meaning,
            evidence_json=evidence,
            confidence=confidence,
            evidence_count=max(1, evidence_count),
            risk_level=risk_level,
            scope=scope,
            project_id=project_id,
            status=status,
            source=source,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        db.session.add(row)
        db.session.flush()
        return self._to_dict(row)

    def bump_evidence(
        self,
        candidate_id: int,
        *,
        confidence: float | None = None,
        example: str | None = None,
    ) -> dict | None:
        row = AiLearningCandidateModel.query.filter_by(id=candidate_id).first()

        if not row:
            return None

        row.evidence_count = int(row.evidence_count or 0) + 1

        if confidence is not None:
            row.confidence = confidence

        if example:
            evidence = dict(row.evidence_json or {})
            examples = list(evidence.get("examples") or [])

            if example not in examples:
                examples.append(example)

            evidence["examples"] = examples[-20:]
            row.evidence_json = evidence

        row.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return self._to_dict(row)

    def list_candidates(
        self,
        *,
        status: str | None = None,
        candidate_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        query = AiLearningCandidateModel.query

        if status:
            query = query.filter(AiLearningCandidateModel.status == status)

        if candidate_type:
            query = query.filter(AiLearningCandidateModel.candidate_type == candidate_type)

        total = query.count()
        rows = (
            query.order_by(
                AiLearningCandidateModel.evidence_count.desc(),
                AiLearningCandidateModel.created_at.desc(),
            )
            .offset(max(0, offset))
            .limit(max(1, min(limit, 200)))
            .all()
        )

        return [self._to_dict(row) for row in rows], total

    def get(self, candidate_id: int) -> dict | None:
        row = AiLearningCandidateModel.query.filter_by(id=candidate_id).first()
        return self._to_dict(row) if row else None

    def update_status(
        self,
        candidate_id: int,
        *,
        status: str,
        reviewer_id: UUID | None = None,
        promoted_term_id: int | None = None,
    ) -> dict | None:
        row = AiLearningCandidateModel.query.filter_by(id=candidate_id).first()

        if not row:
            return None

        now = datetime.now(timezone.utc)
        row.status = status
        row.updated_at = now

        if reviewer_id is not None:
            row.reviewer_id = reviewer_id

        if status in {"approved", "rejected", "promoted"}:
            row.reviewed_at = now

        if promoted_term_id is not None:
            row.promoted_term_id = promoted_term_id

        db.session.flush()
        return self._to_dict(row)

    def _to_dict(self, row: AiLearningCandidateModel) -> dict:
        payload = {
            "id": int(row.id),
            "candidateType": str(row.candidate_type),
            "inputText": str(row.input_text),
            "term": row.term,
            "proposedRule": row.proposed_rule,
            "proposedMeaning": row.proposed_meaning,
            "confidence": float(row.confidence) if row.confidence is not None else None,
            "evidenceCount": int(row.evidence_count or 0),
            "riskLevel": str(row.risk_level),
            "scope": str(row.scope),
            "projectId": str(row.project_id) if row.project_id else None,
            "status": str(row.status),
            "source": str(row.source),
            "createdBy": str(row.created_by) if row.created_by else None,
            "reviewerId": str(row.reviewer_id) if row.reviewer_id else None,
            "promotedTermId": int(row.promoted_term_id) if row.promoted_term_id else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
            "reviewedAt": row.reviewed_at.isoformat() if row.reviewed_at else None,
        }

        if isinstance(row.evidence_json, dict):
            payload["evidence"] = dict(row.evidence_json)

        return payload
