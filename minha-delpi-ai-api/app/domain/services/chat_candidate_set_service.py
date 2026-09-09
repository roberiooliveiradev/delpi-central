"""Identidade estável do candidate set do turno — membership sem segundo catálogo."""

from __future__ import annotations

import hashlib
from typing import Any

from app.domain.models.action_descriptor import ActionCandidate


class ChatCandidateSetService:
    @classmethod
    def action_ids(
        cls,
        candidates: list[ActionCandidate] | list[dict[str, Any]] | None,
    ) -> list[str]:
        action_ids: list[str] = []
        for item in candidates or []:
            action_id = ""
            if isinstance(item, ActionCandidate):
                action_id = item.action_id
            elif isinstance(item, dict):
                action_id = str(item.get("actionId") or item.get("action_id") or "").strip()
            if action_id:
                action_ids.append(action_id)
        return action_ids

    @classmethod
    def contains(
        cls,
        action_id: str,
        *,
        candidate_action_ids: list[str] | set[str] | tuple[str, ...] | None,
        allowed_action_ids: list[str] | set[str] | tuple[str, ...] | None = None,
    ) -> bool:
        target = str(action_id or "").strip()
        if not target:
            return False
        candidate_set = {
            str(item).strip() for item in (candidate_action_ids or []) if str(item).strip()
        }
        if candidate_set and target not in candidate_set:
            return False
        if allowed_action_ids is not None:
            allowed = {
                str(item).strip() for item in allowed_action_ids if str(item).strip()
            }
            if allowed and target not in allowed:
                return False
        return True

    @classmethod
    def build_id(
        cls,
        candidates: list[ActionCandidate] | list[dict[str, Any]],
        *,
        queries: list[str] | None = None,
        allowed_action_ids: list[str] | None = None,
    ) -> str:
        action_ids = cls.action_ids(candidates)
        allowed = sorted({str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()})
        query_key = "|".join(q.strip().lower() for q in (queries or []) if str(q).strip())
        payload = "\n".join(
            [
                ",".join(sorted(set(action_ids))),
                query_key,
                ",".join(allowed),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def slim_summaries(cls, candidates: list[ActionCandidate]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in candidates:
            descriptor = item.descriptor
            rows.append(
                {
                    "actionId": item.action_id,
                    "summary": descriptor.summary or descriptor.description or "",
                    "score": round(float(item.score), 4),
                    "method": descriptor.method,
                    "path": descriptor.path,
                    "tags": list(descriptor.tags),
                }
            )
        return rows
