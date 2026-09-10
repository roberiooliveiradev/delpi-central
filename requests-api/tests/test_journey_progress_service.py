from __future__ import annotations

from requests_app.domain.services.content_loader import load_workflow_definition
from requests_app.domain.services.journey_progress_service import resolve_journey_progress


def test_missing_journey_returns_null():
    assert resolve_journey_progress({"initialStatus": "submitted"}, status="submitted") is None


def test_invoice_submitted():
    workflow = load_workflow_definition("invoice_issuance")
    progress = resolve_journey_progress(workflow, status="submitted")
    assert progress is not None
    assert progress["percentage"] == 33
    assert progress["current_stage_id"] == "intake"
    assert progress["outcome"] == "in_progress"
    assert progress["summary"] is None
    assert [s["state"] for s in progress["stages"]] == ["current", "upcoming", "upcoming"]


def test_invoice_in_progress():
    workflow = load_workflow_definition("invoice_issuance")
    progress = resolve_journey_progress(workflow, status="in_progress")
    assert progress["percentage"] == 66
    assert progress["current_stage_id"] == "service"
    assert [s["state"] for s in progress["stages"]] == ["complete", "current", "upcoming"]


def test_invoice_needs_information_waiting_requester():
    workflow = load_workflow_definition("invoice_issuance")
    progress = resolve_journey_progress(workflow, status="needs_information")
    assert progress["percentage"] == 66
    assert progress["outcome"] == "waiting_requester"
    assert "Aguardando" in (progress["summary"] or "")
    assert progress["stages"][1]["state"] == "current"


def test_invoice_completed_succeeded_100():
    workflow = load_workflow_definition("invoice_issuance")
    progress = resolve_journey_progress(workflow, status="completed")
    assert progress["percentage"] == 100
    assert progress["outcome"] == "succeeded"
    assert [s["state"] for s in progress["stages"]] == ["complete", "complete", "current"]


def test_invoice_cancelled_not_succeeded():
    workflow = load_workflow_definition("invoice_issuance")
    progress = resolve_journey_progress(workflow, status="cancelled")
    assert progress["outcome"] == "cancelled"
    assert progress["percentage"] != 100 or progress["outcome"] != "succeeded"
    assert progress["stages"][1]["state"] == "error"
    assert progress["percentage"] == 66


def test_raw_material_rejected():
    workflow = load_workflow_definition("raw_material_creation")
    progress = resolve_journey_progress(workflow, status="rejected")
    assert progress is not None
    assert progress["outcome"] == "rejected"
    assert progress["stages"][1]["state"] == "error"


def test_unmapped_status_returns_null():
    workflow = load_workflow_definition("invoice_issuance")
    assert resolve_journey_progress(workflow, status="unknown_status") is None
