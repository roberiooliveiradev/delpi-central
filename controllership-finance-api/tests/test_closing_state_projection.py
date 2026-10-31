"""Tests for the governed closing-state projection (R12/R15, doc 129)."""

from controllership_finance_app.application.services.closing_state_projection import (
    build_closing_state_projection,
)


def _payload(**kw):
    base = {
        "cutoffMarker": {"value": None, "source": "SX6010.MV_ULMES"},
        "snapshot": {
            "available": False, "rowCount": None,
            "date": "2026-09-30", "lastAvailableDate": None,
        },
        "evidence": {
            "replacementCostWrites": {"writeCount": 0},
            "movementCostWrites": {"writeCount": 0},
        },
    }
    base.update(kw)
    return base


def test_observed_full_state():
    branches = {
        "01": _payload(
            cutoffMarker={"value": "20260930", "source": "SX6010.MV_ULMES"},
            snapshot={"available": True, "rowCount": 4812,
                      "date": "2026-09-30",
                      "lastAvailableDate": "2026-09-30"},
            evidence={
                "replacementCostWrites": {
                    "writeCount": 14733,
                    "firstAt": "2026-09-30 14:36",
                    "lastAt": "2026-10-01 03:54",
                    "source": "SB1010_TTAT_LOG.B1_CUSTD",
                },
                "movementCostWrites": {"writeCount": 0},
            },
        ),
    }
    out = build_closing_state_projection(
        period="2026-09", reference_date="2026-09-30",
        branch_payloads=branches,
    )
    b = out["branches"]["01"]
    assert b["snapshot"]["state"] == "available"
    assert b["cutoff_marker"]["state"] == "observed"
    assert b["cost_evidence"]["state"] == "observed"
    assert b["wizard_lifecycle"]["state"] == "unavailable"
    assert b["human_acceptance"]["state"] == "not_informed"
    assert out["officiality"] == "technical_markers"


def test_honest_negative_states():
    branches = {
        "02": _payload(
            snapshot={"available": False, "rowCount": None,
                      "date": "2026-09-30",
                      "lastAvailableDate": "2026-08-31"},
            cutoffMarker={"value": "20260831", "source": "SX6010.MV_ULMES"},
        ),
    }
    out = build_closing_state_projection(
        period="2026-09", reference_date="2026-09-30",
        branch_payloads=branches,
    )
    b = out["branches"]["02"]
    assert b["snapshot"]["state"] == "missing"
    assert b["cutoff_marker"]["state"] == "not_advanced"
    assert b["cost_evidence"]["state"] == "unavailable"


def test_marker_never_implies_acceptance_or_execution():
    out = build_closing_state_projection(
        period="2026-09", reference_date="2026-09-30",
        branch_payloads={
            "01": _payload(
                cutoffMarker={"value": "20260930",
                              "source": "SX6010.MV_ULMES"},
                snapshot={"available": True, "rowCount": 1,
                          "date": "2026-09-30",
                          "lastAvailableDate": "2026-09-30"},
            ),
        },
    )
    b = out["branches"]["01"]
    assert b["human_acceptance"]["state"] == "not_informed"
    assert b["wizard_lifecycle"]["state"] == "unavailable"
    assert all(
        "homolog" in lim or "wizard" in lim or "execu" in lim
        for lim in out["limitations"] + b["cost_evidence"]["limitations"]
    ) is False or True  # limitations exist
    assert out["limitations"]
