"""D2 — coverage recommendationQueries vs presentation profiles."""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)

_ROOT = Path(__file__).resolve().parents[4]
_PROFILES = (
    _ROOT
    / "app/content/pt-BR/assistant/presentation_profiles.json"
)


def test_all_presentation_commentary_keys_have_recommendation_queries():
    payload = json.loads(_PROFILES.read_text(encoding="utf-8"))
    profiles = payload.get("profiles") or {}
    missing: list[tuple[str, str]] = []

    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        key = str(profile.get("commentaryProfileKey") or "").strip()
        if not key:
            continue
        queries = ChatHumanizedDataResponseContentService.recommendation_queries(key)
        if not queries:
            missing.append((name, key))

    assert not missing, f"profiles without recommendationQueries: {missing}"


def test_unknown_profile_has_no_recommendation_queries():
    assert (
        ChatHumanizedDataResponseContentService.recommendation_queries(
            "profile_that_does_not_exist"
        )
        == []
    )


def test_static_recommendations_catalog_removed():
    node = ChatHumanizedDataResponseContentService.get_node("recommendations")
    assert node in (None, {}, [])
