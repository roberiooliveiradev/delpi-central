from __future__ import annotations

import hashlib
import json
from typing import Any


class ContentHashService:
    @classmethod
    def hash_version_payload(cls, payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def build_version_payload(
        cls,
        *,
        title: str,
        meeting_type: str,
        meeting_date: str,
        start_time: str | None,
        end_time: str | None,
        location: str | None,
        agenda_html: str,
        body_html: str,
        decisions_html: str,
        pending_html: str,
        observations_html: str,
    ) -> dict[str, Any]:
        return {
            "title": title,
            "meeting_type": meeting_type,
            "meeting_date": meeting_date,
            "start_time": start_time,
            "end_time": end_time,
            "location": location or "",
            "agenda_html": agenda_html,
            "body_html": body_html,
            "decisions_html": decisions_html,
            "pending_html": pending_html,
            "observations_html": observations_html,
        }
