from __future__ import annotations

import re
from uuid import UUID

from app.extensions.db import db
from app.infrastructure.db.models.chat_skill_catalog_model import AiChatSkillCatalogModel


def _normalize_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return normalized[:80]


class PostgresChatSkillRepository:
    def list_all(self, *, include_inactive: bool = False) -> list[dict]:
        query = AiChatSkillCatalogModel.query

        if not include_inactive:
            query = query.filter(AiChatSkillCatalogModel.is_active.is_(True))

        rows = query.order_by(
            AiChatSkillCatalogModel.sort_order.asc(),
            AiChatSkillCatalogModel.label.asc(),
        ).all()

        return [self._to_dict(row) for row in rows]

    def list_active(self) -> list[dict]:
        return self.list_all(include_inactive=False)

    def get_by_id(self, skill_id: UUID) -> dict | None:
        row = db.session.get(AiChatSkillCatalogModel, skill_id)
        return self._to_dict(row) if row else None

    def get_by_key(self, skill_key: str) -> dict | None:
        normalized = _normalize_key(skill_key)
        if not normalized:
            return None

        row = AiChatSkillCatalogModel.query.filter_by(skill_key=normalized).first()
        return self._to_dict(row) if row else None

    def create(self, payload: dict) -> dict:
        skill_key = _normalize_key(payload.get("skillKey") or payload.get("skill_key") or "")

        if not skill_key:
            raise ValueError("skillKey is required")

        if AiChatSkillCatalogModel.query.filter_by(skill_key=skill_key).first():
            raise ValueError("skillKey already exists")

        row = AiChatSkillCatalogModel(
            skill_key=skill_key,
            label=str(payload.get("label") or skill_key).strip()[:160],
            description=str(payload.get("description") or "").strip(),
            policy_content=self._optional_text(payload.get("policyContent")),
            policy_file=self._optional_text(payload.get("policyFile"), max_len=120),
            metadata_flag=str(payload.get("metadataFlag") or "enabled").strip()[:80] or "enabled",
            legacy_metadata_flag=self._optional_text(payload.get("legacyMetadataFlag"), max_len=80),
            execution_path_hint=self._optional_text(payload.get("executionPathHint"), max_len=200),
            execution_derived_key=self._optional_text(payload.get("executionDerivedKey"), max_len=80),
            is_active=bool(payload.get("isActive", True)),
            sort_order=int(payload.get("sortOrder") or 0),
        )
        db.session.add(row)
        db.session.flush()
        return self._to_dict(row)

    def update(self, skill_id: UUID, payload: dict) -> dict | None:
        row = db.session.get(AiChatSkillCatalogModel, skill_id)

        if not row:
            return None

        if "label" in payload:
            row.label = str(payload.get("label") or row.label).strip()[:160]

        if "description" in payload:
            row.description = str(payload.get("description") or "").strip()

        if "policyContent" in payload:
            row.policy_content = self._optional_text(payload.get("policyContent"))

        if "policyFile" in payload:
            row.policy_file = self._optional_text(payload.get("policyFile"), max_len=120)

        if "metadataFlag" in payload:
            row.metadata_flag = str(payload.get("metadataFlag") or "enabled").strip()[:80] or "enabled"

        if "legacyMetadataFlag" in payload:
            row.legacy_metadata_flag = self._optional_text(payload.get("legacyMetadataFlag"), max_len=80)

        if "executionPathHint" in payload:
            row.execution_path_hint = self._optional_text(payload.get("executionPathHint"), max_len=200)

        if "executionDerivedKey" in payload:
            row.execution_derived_key = self._optional_text(payload.get("executionDerivedKey"), max_len=80)

        if "isActive" in payload:
            row.is_active = bool(payload.get("isActive"))

        if "sortOrder" in payload:
            row.sort_order = int(payload.get("sortOrder") or 0)

        db.session.flush()
        return self._to_dict(row)

    def deactivate(self, skill_id: UUID) -> bool:
        row = db.session.get(AiChatSkillCatalogModel, skill_id)

        if not row:
            return False

        row.is_active = False
        db.session.flush()
        return True

    @staticmethod
    def _optional_text(value: object, *, max_len: int | None = None) -> str | None:
        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        if max_len is not None:
            return text[:max_len]

        return text

    @staticmethod
    def _to_dict(row: AiChatSkillCatalogModel | None) -> dict | None:
        if not row:
            return None

        return {
            "id": str(row.id),
            "skillKey": row.skill_key,
            "label": row.label,
            "description": row.description or "",
            "policyContent": row.policy_content,
            "policyFile": row.policy_file,
            "metadataFlag": row.metadata_flag,
            "legacyMetadataFlag": row.legacy_metadata_flag,
            "executionPathHint": row.execution_path_hint,
            "executionDerivedKey": row.execution_derived_key,
            "isActive": bool(row.is_active),
            "sortOrder": int(row.sort_order or 0),
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }
