from __future__ import annotations

from datetime import date

from app.domain.services.kaizen import kaizen_revision_service as svc


def test_changed_trigger_fields_detects_status():
    current = {"status": "recebido", "notes": "a"}
    updated = {"status": "implantado", "notes": "b"}
    changed = svc.changed_trigger_fields(current, updated)
    assert changed == ["status"]


def test_changed_trigger_fields_ignores_non_trigger():
    current = {"status": "recebido", "notes": "a", "accountable": "Ana"}
    updated = {"notes": "b", "accountable": "Bruno"}
    assert svc.changed_trigger_fields(current, updated) == []


def test_changed_trigger_fields_normalizes_numbers():
    current = {"fixed_daily_savings": 10}
    updated = {"fixed_daily_savings": 10.0}
    assert svc.changed_trigger_fields(current, updated) == []


def test_resolve_change_type_creation_baseline():
    assert svc.resolve_change_type(None, {"status": "recebido"}, is_creation=True) == "baseline"


def test_resolve_change_type_creation_implanted():
    assert svc.resolve_change_type(None, {"status": "implantado"}, is_creation=True) == "implantacao"


def test_resolve_change_type_to_implanted():
    current = {"status": "recebido"}
    merged = {"status": "implantado"}
    assert svc.resolve_change_type(current, merged, is_creation=False) == "implantacao"


def test_resolve_change_type_to_discontinued():
    current = {"status": "implantado"}
    merged = {"status": "descontinuado"}
    assert svc.resolve_change_type(current, merged, is_creation=False) == "descontinuacao"


def test_resolve_change_type_savings_change_is_melhoria():
    current = {"status": "implantado", "fixed_daily_savings": 5}
    merged = {"status": "implantado", "fixed_daily_savings": 10}
    assert svc.resolve_change_type(current, merged, is_creation=False) == "melhoria"


def test_build_change_summary_status():
    current = {"status": "recebido"}
    merged = {"status": "implantado"}
    summary = svc.build_change_summary(current, merged, ["status"])
    assert summary == "status: Recebido → Implantado"


def test_build_snapshot_contains_business_fields():
    record = {
        "branch_code": "01",
        "title": "Kaizen X",
        "status": "implantado",
        "daily_savings": 12.5,
        "id": "ignored",
        "created_at": "2026-01-01",
    }
    snapshot = svc.build_snapshot(record)
    assert snapshot["branch_code"] == "01"
    assert snapshot["title"] == "Kaizen X"
    assert snapshot["status"] == "implantado"
    assert snapshot["daily_savings"] == 12.5
    assert "id" not in snapshot
    assert "created_at" not in snapshot


def test_resolve_effective_from_uses_provided_when_no_implantation_date():
    assert svc.resolve_effective_from({}, provided="2026-05-01") == "2026-05-01"


def test_resolve_parent_revision_id_prefers_explicit():
    assert (
        svc.resolve_parent_revision_id(
            explicit="  parent-1  ",
            active_version={"id": "active-9"},
        )
        == "parent-1"
    )


def test_resolve_parent_revision_id_falls_back_to_active():
    assert (
        svc.resolve_parent_revision_id(
            explicit=None,
            active_version={"id": "active-9"},
        )
        == "active-9"
    )


def test_resolve_parent_revision_id_none_without_active():
    assert svc.resolve_parent_revision_id(explicit="  ", active_version=None) is None


def test_resolve_effective_from_prefers_date_implemented_over_provided():
    assert (
        svc.resolve_effective_from({"date_implemented": "2026-03-03"}, provided="2026-05-01")
        == "2026-03-03"
    )


def test_resolve_effective_from_falls_back_to_date_implemented():
    assert svc.resolve_effective_from({"date_implemented": "2026-03-03"}) == "2026-03-03"


def test_ensure_implantation_date_is_passthrough_without_auto_fill():
    result = svc.ensure_implantation_date({"status": "implantado"})
    assert "date_implemented" not in result


def test_ensure_implantation_date_keeps_existing():
    result = svc.ensure_implantation_date(
        {"status": "implantado", "date_implemented": "2026-01-15"}
    )
    assert result["date_implemented"] == "2026-01-15"
