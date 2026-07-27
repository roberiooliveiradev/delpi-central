"""Unit — diff de histórico de NC LMP."""

from app.domain.services.lmp.lmp_nonconformity_history_diff import (
    build_nc_history_changes,
)


def test_build_nc_history_changes_on_create_lists_initial_values() -> None:
    changes = build_nc_history_changes(
        None,
        {
            "status": "open",
            "sale_number": "123456",
            "lmp_number": "LMP-LEG",
            "customer_name": None,
            "problem_tags": ["Medida"],
            "products": [
                {"product_code": "90001234", "product_description": "Produto X"},
            ],
        },
    )
    fields = {item["field"]: item for item in changes["fields"]}
    assert fields["status"]["new"] == "open"
    assert fields["sale_number"]["new"] == "123456"
    assert fields["lmp_number"]["new"] == "LMP-LEG"
    assert fields["problem_tags"]["new"] == ["Medida"]
    assert fields["products"]["new"][0]["product_code"] == "90001234"
    assert "customer_name" not in fields


def test_build_nc_history_changes_on_update_only_diffs() -> None:
    before = {
        "status": "open",
        "sale_number": "123456",
        "customer_name": "Cliente A",
        "launch_date": "2026-01-01",
        "last_revision_date": None,
        "executed_by": "Eng. A",
        "released_by": None,
        "defect_description": "Texto",
        "corrective_actions": None,
        "technical_opinion": None,
        "problem_tags": ["Medida"],
        "products": [{"product_code": "90001234", "product_description": ""}],
    }
    after = {
        **before,
        "status": "done",
        "problem_tags": ["Medida", "Desenho"],
    }
    changes = build_nc_history_changes(before, after)
    fields = {item["field"]: item for item in changes["fields"]}
    assert set(fields) == {"status", "problem_tags"}
    assert fields["status"]["old"] == "open"
    assert fields["status"]["new"] == "done"
    assert fields["problem_tags"]["new"] == ["Medida", "Desenho"]


def test_build_nc_history_changes_empty_when_unchanged() -> None:
    snapshot = {
        "status": "open",
        "sale_number": "1",
        "customer_name": None,
        "launch_date": None,
        "last_revision_date": None,
        "executed_by": None,
        "released_by": None,
        "defect_description": None,
        "corrective_actions": None,
        "technical_opinion": None,
        "problem_tags": [],
        "products": [],
    }
    assert build_nc_history_changes(snapshot, snapshot)["fields"] == []
