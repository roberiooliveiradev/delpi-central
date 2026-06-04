from datetime import datetime, timezone
from uuid import UUID

from app.extensions.db import db
from app.infrastructure.db.models.vocabulary_term_model import AiVocabularyTermModel

# Tipos de termo aplicáveis como regra de normalização aprendida.
_NORMALIZATION_TYPES = ("typo", "abbreviation", "phrase")


class PostgresVocabularyTermRepository:
    def upsert_term(
        self,
        *,
        term: str,
        normalized_term: str,
        meaning: str | None = None,
        type: str = "typo",
        scope: str = "global",
        project_id: UUID | None = None,
        source: str = "promotion",
        confidence: float | None = None,
        approved: bool = False,
        active: bool = True,
        created_by: UUID | None = None,
    ) -> dict:
        query = AiVocabularyTermModel.query.filter(
            AiVocabularyTermModel.normalized_term == normalized_term,
            AiVocabularyTermModel.scope == scope,
        )

        if project_id is None:
            query = query.filter(AiVocabularyTermModel.project_id.is_(None))
        else:
            query = query.filter(AiVocabularyTermModel.project_id == project_id)

        row = query.first()
        now = datetime.now(timezone.utc)

        if row:
            row.term = term
            row.meaning = meaning
            row.type = type
            row.source = source
            row.confidence = confidence
            row.approved = approved
            row.active = active
            row.evidence_count = int(row.evidence_count or 0) + 1
            row.updated_at = now
        else:
            row = AiVocabularyTermModel(
                term=term,
                normalized_term=normalized_term,
                meaning=meaning,
                type=type,
                scope=scope,
                project_id=project_id,
                source=source,
                confidence=confidence,
                approved=approved,
                active=active,
                evidence_count=1,
                created_by=created_by,
                created_at=now,
                updated_at=now,
            )
            db.session.add(row)

        db.session.flush()
        return self._to_dict(row)

    def list_terms(
        self,
        *,
        scope: str | None = None,
        approved: bool | None = None,
        type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        query = AiVocabularyTermModel.query

        if scope:
            query = query.filter(AiVocabularyTermModel.scope == scope)

        if approved is not None:
            query = query.filter(AiVocabularyTermModel.approved.is_(approved))

        if type:
            query = query.filter(AiVocabularyTermModel.type == type)

        total = query.count()
        rows = (
            query.order_by(AiVocabularyTermModel.updated_at.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 200)))
            .all()
        )

        return [self._to_dict(row) for row in rows], total

    def list_active_normalization_rules(
        self,
        *,
        scopes: tuple[str, ...] = ("global",),
        max_rules: int = 500,
    ) -> list[dict]:
        rows = (
            AiVocabularyTermModel.query.filter(
                AiVocabularyTermModel.approved.is_(True),
                AiVocabularyTermModel.active.is_(True),
                AiVocabularyTermModel.scope.in_(scopes),
                AiVocabularyTermModel.type.in_(_NORMALIZATION_TYPES),
            )
            .order_by(AiVocabularyTermModel.updated_at.desc())
            .limit(max(1, min(max_rules, 2000)))
            .all()
        )

        return [
            {
                "term": str(row.term),
                "normalizedTerm": str(row.normalized_term),
                "type": str(row.type),
            }
            for row in rows
        ]

    def get(self, term_id: int) -> dict | None:
        row = AiVocabularyTermModel.query.filter_by(id=term_id).first()
        return self._to_dict(row) if row else None

    def set_active(self, term_id: int, *, active: bool) -> dict | None:
        row = AiVocabularyTermModel.query.filter_by(id=term_id).first()

        if not row:
            return None

        row.active = active
        row.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return self._to_dict(row)

    def _to_dict(self, row: AiVocabularyTermModel) -> dict:
        return {
            "id": int(row.id),
            "term": str(row.term),
            "normalizedTerm": str(row.normalized_term),
            "meaning": row.meaning,
            "type": str(row.type),
            "scope": str(row.scope),
            "projectId": str(row.project_id) if row.project_id else None,
            "source": str(row.source),
            "confidence": float(row.confidence) if row.confidence is not None else None,
            "evidenceCount": int(row.evidence_count or 0),
            "approved": bool(row.approved),
            "active": bool(row.active),
            "createdBy": str(row.created_by) if row.created_by else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }
