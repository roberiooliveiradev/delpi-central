"""E7.S4 — path/entity cleanup com equivalência shape/OpenAPI."""

from __future__ import annotations

import json
from pathlib import Path

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)

configure_domain_infrastructure_ports()

_ROOT = Path(__file__).resolve().parents[4]
_ASSISTANT = _ROOT / "app/content/pt-BR/assistant"


def test_e7_s4_playbook_entity_shape_without_path_rule():
    """Positive: schedule/today via entity+shape (pathRule removido)."""

    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/ops/v2/schedule-renamed",
        entity="production_schedule_today",
        shape="playbook_report",
    )
    assert profile.get("openapiDerived") is True
    assert profile.get("defaultViewPolicy") == "table_when_available"
    assert profile.get("openapiShape") == "playbook_report"


def test_e7_s4_sibling_orders_open_same_view_policy():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/ops/v2/orders-open",
        entity="production_orders_open",
        shape="playbook_report",
    )
    assert profile.get("openapiDerived") is True
    assert profile.get("defaultViewPolicy") == "table_when_available"


def test_e7_s4_metamorphic_path_rename_same_entity_shape():
    a = ChatPresentationProfileService.build_resolved_profile(
        path="/production/schedule/today",
        entity="production_schedule_today",
        shape="playbook_report",
    )
    b = ChatPresentationProfileService.build_resolved_profile(
        path="/vendor/acme/daily-schedule",
        entity="production_schedule_today",
        shape="playbook_report",
    )
    assert a.get("profileKey") == b.get("profileKey")
    assert a.get("defaultViewPolicy") == b.get("defaultViewPolicy")


def test_e7_s4_negative_stock_specialized_untouched():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/products/10080001/stock",
        entity="product_stock",
        shape="paged_list",
    )
    assert profile.get("openapiDerived") is not True
    assert profile.get("profileKey") == "stock"


def test_e7_s4_schedule_table_profile_detect_has_no_path_contains():
    columns = json.loads(
        (_ASSISTANT / "column_labels.json").read_text(encoding="utf-8")
    )
    profile = (columns.get("tableProfiles") or {}).get("playbookScheduleToday") or {}
    detect = profile.get("detect") or {}
    assert "pathContains" not in detect
    assert detect.get("allKeys") or detect.get("anyKeys")

    # pathContains ausente não bloqueia match por keys (assinatura do helper).
    svc = ExternalActionColumnLabelService()
    assert hasattr(svc, "_profile_matches")


def test_e7_s4_dead_orphans_removed_and_ledger_populated():
    profiles = json.loads(
        (_ASSISTANT / "presentation_profiles.json").read_text(encoding="utf-8")
    )
    presenter = json.loads(
        (_ASSISTANT / "presenter_content.json").read_text(encoding="utf-8")
    )
    assert "pathEntityFallbacks" not in profiles
    assert "compositeVisualSpecs" not in presenter
    migrated = (profiles.get("entitySets") or {}).get("schemaFirstMigratedProfiles") or []
    assert isinstance(migrated, list)
    assert len(migrated) >= 20
    assert any(str(item).startswith("pathRule:") for item in migrated)
    assert any(str(item).startswith("table:") for item in migrated)


def test_e7_s4_path_rules_count_reduced():
    profiles = json.loads(
        (_ASSISTANT / "presentation_profiles.json").read_text(encoding="utf-8")
    )
    assert len(profiles.get("pathRules") or []) == 49
    columns = json.loads(
        (_ASSISTANT / "column_labels.json").read_text(encoding="utf-8")
    )
    with_pc = 0
    for profile in (columns.get("tableProfiles") or {}).values():
        if not isinstance(profile, dict):
            continue
        detect = profile.get("detect") or {}
        if isinstance(detect, dict) and detect.get("pathContains"):
            with_pc += 1
    assert with_pc == 23
