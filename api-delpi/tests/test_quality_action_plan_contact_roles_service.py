from __future__ import annotations

from app.domain.services.quality_action_plans.quality_action_plan_contact_roles_service import (
    build_contact_roles_view,
    resolve_customer_contact_email,
    resolve_customer_contact_name,
    resolve_delpi_primary_contact_name,
)


def test_resolve_customer_and_delpi_contacts_from_explicit_plan_fields():
    plan = {
        "customer_contact": "Igor Sfalsin Zamperlini",
        "customer_contact_email": "wmo-rnc@weg.net",
        "delpi_contact_name": "Laercio Koch",
        "delpi_contact_area": "comercial",
        "delpi_quality_contact": "Carla Demeneck",
        "template_payload": {},
    }

    assert resolve_customer_contact_name(plan) == "Igor Sfalsin Zamperlini"
    assert resolve_customer_contact_email(plan) == "wmo-rnc@weg.net"
    assert resolve_delpi_primary_contact_name(plan) == "Laercio Koch"
    roles = build_contact_roles_view(plan)
    assert roles["delpi_quality_contact"] == "Carla Demeneck"
    assert roles["delpi_contact_area_label"] == "Comercial"


def test_legacy_inverted_contacts_use_attention_to_as_customer():
    plan = {
        "customer_contact": "Laercio Koch",
        "template_payload": {
            "attention_to": "Igor Sfalsin Zamperlini",
            "attention_email": "wmo-rnc@weg.net",
            "contact_phone": "47 3370 5502",
        },
    }

    assert resolve_customer_contact_name(plan) == "Igor Sfalsin Zamperlini"
    assert resolve_customer_contact_email(plan) == "wmo-rnc@weg.net"
    assert resolve_delpi_primary_contact_name(plan) == "Laercio Koch"
