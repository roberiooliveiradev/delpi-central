from __future__ import annotations

from uuid import uuid4

from production_pulse_app.application.services.command_audit_actor_enrichment_service import (
    enrich_command_audit_actors,
)


def test_enrich_command_audit_actors_fills_name_and_email(monkeypatch):
    actor_id = str(uuid4())
    items = [{"issuedBy": actor_id, "commandKey": "reset"}]

    def fake_lookup(user_ids, authorization):
        assert authorization == "Bearer token"
        assert user_ids == [actor_id]
        return {
            actor_id: {
                "name": "João Silva",
                "email": "joao@delpi.com",
            }
        }

    monkeypatch.setattr(
        "production_pulse_app.application.services.command_audit_actor_enrichment_service.lookup_directory_users_by_ids",
        fake_lookup,
    )

    enriched = enrich_command_audit_actors(items, authorization="Bearer token")

    assert enriched[0]["issuedByName"] == "João Silva"
    assert enriched[0]["issuedByEmail"] == "joao@delpi.com"


def test_enrich_command_audit_actors_skips_non_uuid():
    items = [{"issuedBy": "unknown", "commandKey": "reset"}]
    enriched = enrich_command_audit_actors(items, authorization="Bearer token")
    assert enriched == items


def test_enrich_command_audit_actors_skips_without_authorization():
    actor_id = str(uuid4())
    items = [{"issuedBy": actor_id, "commandKey": "reset"}]
    enriched = enrich_command_audit_actors(items, authorization=None)
    assert enriched == items
