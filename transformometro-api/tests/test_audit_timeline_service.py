from __future__ import annotations

from tm_app.application.services.audit_timeline_service import enrich_timeline_actor_names


def test_enrich_timeline_actor_names_fills_missing_from_lookup(monkeypatch):
    items = [
        {"user_id": "u1", "user_email": "a@example.com"},
        {"user_id": "u2", "user_name": "Maria"},
    ]

    def fake_lookup(user_ids, authorization):
        assert authorization == "Bearer token"
        assert user_ids == ["u1"]
        return {"u1": "João Silva"}

    monkeypatch.setattr(
        "tm_app.application.services.audit_timeline_service.lookup_user_names_by_ids",
        fake_lookup,
    )

    enriched = enrich_timeline_actor_names(items, authorization="Bearer token")

    assert enriched[0]["user_name"] == "João Silva"
    assert enriched[1]["user_name"] == "Maria"


def test_enrich_timeline_actor_names_skips_when_all_named():
    items = [{"user_id": "u1", "user_name": "Ana"}]
    enriched = enrich_timeline_actor_names(items, authorization="Bearer token")
    assert enriched == items
