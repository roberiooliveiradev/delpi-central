"""POST /closing/analysis/report-comparison — governed cross-report
comparison (doc 126, IMPLEMENTATION-STAGE-03) + CLARA semantic parity.

Chain under test: middleware (JWT + RBAC snapshot) → principal guard →
``controllership-finance.access`` → typed request → per-subject governed
fetch (S2S + delegated Bearer, fail-closed) → semantic compatibility →
authorized normalizations only → honest PARTIAL/DIFFERENT results.

The engine never recalculates producer rules, never converts missing
data into zero and never reveals a restricted subject through a
partial result.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.infrastructure.api_delpi_gateway import (
    DelpiApiGatewayError,
)
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
TOKEN = "viewer-test-token"
ROUTE = "/closing/analysis/report-comparison"
GW = (
    "controllership_finance_app.application.report_comparison."
    "compare_use_case.ApiDelpiSettlementsGateway"
)

KARDEX_SUMMARY = "/financeiro/stock-kardex/summary"
ADJ_SUMMARY = "/financeiro/inventory-adjustments/summary"
CCE = "/financeiro/cost-center-expenses"
ROSTER = "/financeiro/billing-exclusion-roster"
CPV = "/financeiro/cpv"


def _claims(**overrides) -> dict:
    claims = {
        "sub": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "roles": [],
        "groups": [],
        "permissions": [ACCESS],
        "is_superadmin": False,
    }
    rbac.update(overrides)
    return rbac


async def _load_rbac_result(rbac: dict):
    return rbac


@pytest.fixture(autouse=True)
def _auth_pipeline(monkeypatch):
    rbac_holder = {"rbac": _rbac()}

    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token",
        lambda request: False,
    )
    monkeypatch.setattr(fa, "validate_token", lambda token: _claims())
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(
            rbac_holder["rbac"]
        ),
    )
    yield rbac_holder


def _kardex_payload(output: str, *, month_note: str = "") -> dict:
    return {
        "status": "available",
        "totals": {
            "entryValue": "50.00",
            "outputValue": output,
            "netValue": "0.00",
            "openingValue": "10.00",
            "closingValue": "60.00",
            "entryQuantity": "5",
            "outputQuantity": "8",
            "netQuantity": "-3",
            "movementCount": 42,
            "blockCount": 0,
        },
        "summariesByType": [
            {
                "productType": "PA",
                "outputValue": output,
                "entryValue": "50.00",
            }
        ],
        "summariesByWarehouse": [
            {"warehouse": "01", "outputValue": output}
        ],
        "parityStatus": "PENDING",
        "provenance": {"engine": "matr910", "asOfConvention": "ttat"},
        "dataAsOf": "2026-10-01",
    }


def _cce_payload(
    total: str,
    *,
    items: list | None = None,
    total_items: int = 0,
    by_cc: list | None = None,
) -> dict:
    return {
        "status": "available",
        "summary": {
            "totalValue": total,
            "lineCount": 353,
            "documentCount": 139,
            "costCenterCount": 46,
            "supplierCount": 30,
            "findingCount": 3,
            "unclassifiedCount": 2,
            "byCostCenter": by_cc
            if by_cc is not None
            else [
                {
                    "costCenter": "0404",
                    "totalValue": "50000.00",
                    "lineCount": 10,
                    "findingCount": 1,
                },
                {
                    "costCenter": "1010",
                    "totalValue": "25000.00",
                    "lineCount": 4,
                    "findingCount": 0,
                },
            ],
            "byProductType": [
                {"productType": "SV", "totalValue": total}
            ],
        },
        "items": items or [],
        "pagination": {"total_items": total_items},
        "parityStatus": "PENDING",
        "provenance": {"engine": "edapp-r10"},
    }


def _roster_payload(
    total: str,
    *,
    items: list | None = None,
    total_items: int = 0,
) -> dict:
    return {
        "status": "available",
        "summary": {
            "totalValue": total,
            "lineCount": 11,
            "documentCount": 11,
            "customerCount": 5,
            "zeroCostCount": 11,
            "missingStockSiblingDocumentCount": 3,
            "findingCount": 3,
            "candidateLineCount": 11,
            "outOfCriteriaLineCount": 0,
            "byTes": [{"tes": "594", "totalValue": total}],
            "byProductGroup": [
                {"productGroup": "9035", "totalValue": total}
            ],
        },
        "items": items or [],
        "pagination": {"total_items": total_items},
        "parityStatus": "PENDING",
        "provenance": {"engine": "roster-r11"},
    }


def _cpv_payload(total: str) -> dict:
    return {
        "status": "available",
        "summary": {
            "cpvTotal": total,
            "totalMovements": 5,
            "totalQuantity": "10",
        },
        "byCfop": [{"cfop": "5101", "cpvTotal": total}],
        "byTm": [{"tm": "594", "cpvTotal": total}],
        "officialR06": False,
        "parityStatus": "PENDING",
        "provenance": {
            "engine": "cpv-sd2",
            "asOfConvention": "live",
        },
    }


@pytest.fixture
def gateway(monkeypatch):
    """Per-endpoint/per-period stub — keys on the forwarded params so
    tests can assert verbatim forwarding of period/branch/filters."""
    responses: dict[tuple, dict | Exception] = {}
    calls: list[tuple] = []

    def _get(
        path,
        *,
        access_token=None,
        params=None,
        timeout_seconds=None,
    ):
        params = dict(params or {})
        calls.append((path, params))
        period = params.get("period")
        branch = params.get("branch")
        key = (path, period, branch)
        for candidate in (key, (path, period), (path,)):
            value = responses.get(candidate)
            if value is not None:
                if isinstance(value, Exception):
                    raise value
                return {"success": True, "data": value}
        raise AssertionError(
            f"unstubbed gateway call: {path} {params}"
        )

    fake = MagicMock()
    fake.get.side_effect = _get
    fake.calls = calls
    fake.responses = responses
    monkeypatch.setattr(GW, lambda *a, **k: fake)
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _post(client, payload, token: str = TOKEN):
    return client.post(
        ROUTE, json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )


def _subject(
    rid: str, period: str, branch: str = "01", **filters
) -> dict:
    subject: dict = {"reportId": rid, "period": period, "branch": branch}
    if filters:
        subject["filters"] = filters
    return subject


# --- authorization ----------------------------------------------------------


def test_comparison_requires_bearer():
    response = _client().post(ROUTE, json={})
    assert response.status_code == 401


def test_comparison_manage_only_forbidden(_auth_pipeline):
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
            ],
        },
    )
    assert response.status_code == 403


def test_comparison_denied_subject_never_leaks(_auth_pipeline, gateway):
    """Fail-closed: an upstream 403 marks the subject denied; its
    totals/existence never appear in the response."""
    gateway.responses[(KARDEX_SUMMARY, "2026-07")] = _kardex_payload(
        "100.00"
    )
    gateway.responses[(KARDEX_SUMMARY, "2026-08")] = (
        DelpiApiGatewayError(
            "denied", status_code=403, error_code="scope_unavailable"
        )
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    denied = data["subjects"][1]
    assert denied["status"] == "denied"
    assert "measureValue" not in denied
    assert data["status"] == "INSUFFICIENT_EVIDENCE"
    assert data["diffs"] == []
    assert data["missingData"][0]["status"] == "denied"


# --- validation -------------------------------------------------------------


def _valid_period_body(**overrides) -> dict:
    body = {
        "comparisonKind": "PERIOD",
        "measure": "outputValue",
        "subjects": [
            _subject("R06", "2026-07"),
            _subject("R06", "2026-08"),
        ],
    }
    body.update(overrides)
    return body


def test_validation_single_subject_rejected():
    response = _post(
        _client(),
        _valid_period_body(subjects=[_subject("R06", "2026-07")]),
    )
    assert response.status_code == 422


def test_validation_seven_subjects_rejected():
    response = _post(
        _client(),
        _valid_period_body(
            subjects=[_subject("R06", f"2026-0{i}") for i in range(1, 8)]
        ),
    )
    assert response.status_code == 422


def test_validation_bad_kind():
    response = _post(
        _client(), _valid_period_body(comparisonKind="EVERYTHING")
    )
    assert response.status_code == 400


def test_validation_bad_period_format():
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-13"),
                _subject("R06", "2026-08"),
            ],
        },
    )
    assert response.status_code == 422


def test_validation_period_requires_same_report():
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "totalValue",
            "subjects": [
                _subject("R10", "2026-08"),
                _subject("R11", "2026-08"),
            ],
        },
    )
    assert response.status_code == 400


def test_validation_period_requires_distinct_periods():
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-08"),
                _subject("R06", "2026-08"),
            ],
        },
    )
    assert response.status_code == 400
    assert response.json()["data"]["error"]["code"] == (
        "duplicate_subject"
    )


def test_validation_branch_requires_two_branches():
    response = _post(
        _client(),
        {
            "comparisonKind": "BRANCH",
            "measure": "outputValue",
            "subjects": [
                _subject("R07", "2026-09", "01"),
                _subject("R07", "2026-09", "01"),
            ],
        },
    )
    assert response.status_code == 400


def test_validation_baseline_out_of_range():
    response = _post(
        _client(), _valid_period_body(baselineIndex=9)
    )
    assert response.status_code == 422


def test_validation_diff_page_size_capped():
    response = _post(
        _client(), _valid_period_body(diffPageSize=501)
    )
    assert response.status_code == 422


def test_comparison_upstream_401_subject_denied(gateway):
    """Failed S2S/delegation (upstream 401) → denied subject, no leak."""
    gateway.responses[(KARDEX_SUMMARY, "2026-07")] = _kardex_payload(
        "100.00"
    )
    gateway.responses[(KARDEX_SUMMARY, "2026-08")] = (
        DelpiApiGatewayError("unauthorized", status_code=401)
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
            ],
        },
    )
    data = response.json()["data"]
    assert data["subjects"][1]["status"] == "denied"
    assert "measureValue" not in data["subjects"][1]
    assert data["security"]["subjectsDenied"] == 1


def test_diff_pagination_truncates(gateway):
    """Grain diffs respect page size and declare truncation."""
    many = [
        {"costCenter": f"CC{i:02d}", "totalValue": str(1000 + i)}
        for i in range(5)
    ]
    many2 = [
        {"costCenter": f"CC{i:02d}", "totalValue": str(2000 + i)}
        for i in range(5)
    ]
    gateway.responses[(CCE, "2026-08")] = _cce_payload(
        "5000.00", by_cc=many
    )
    gateway.responses[(CCE, "2026-09")] = _cce_payload(
        "10000.00", by_cc=many2
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "totalValue",
            "grain": "cost_center",
            "diffPageSize": 2,
            "subjects": [
                _subject("R10", "2026-08"),
                _subject("R10", "2026-09"),
            ],
        },
    )
    data = response.json()["data"]
    assert len(data["diffs"]) == 2
    assert data["diffCount"] == 5
    assert data["diffTruncated"] is True


# --- valid comparisons ------------------------------------------------------


def test_period_r06_three_months(gateway):
    for period, total in (
        ("2026-07", "100.00"),
        ("2026-08", "150.00"),
        ("2026-09", "200.00"),
    ):
        gateway.responses[(KARDEX_SUMMARY, period)] = (
            _kardex_payload(total)
        )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
                _subject("R06", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DIFFERENT"
    assert [s["status"] for s in data["subjects"]] == ["ok"] * 3
    by_target = {d["target"]["index"]: d for d in data["diffs"]}
    assert by_target[1]["delta"] == "50.00"
    assert by_target[1]["deltaPct"] == "50.00"
    assert by_target[2]["delta"] == "100.00"
    assert by_target[2]["deltaPct"] == "100.00"
    assert (
        data["compatibility"][0]["classification"] == "COMPARABLE"
    )
    # forwards verbatim — same branch/params for every subject
    for path, params in gateway.calls:
        assert path == KARDEX_SUMMARY
        assert params["branch"] == "01"


def test_period_r06_product_grain(gateway):
    for period, total in (
        ("2026-07", "100.00"),
        ("2026-08", "150.00"),
    ):
        gateway.responses[(KARDEX_SUMMARY, period)] = (
            _kardex_payload(total)
        )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "grain": "product_type",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DIFFERENT"
    assert data["diffs"][0]["grainKey"] == "PA"
    assert data["diffs"][0]["delta"] == "50.00"


def test_branch_r07_two_branches(gateway):
    gateway.responses[(ADJ_SUMMARY, "2026-09", "01")] = (
        _kardex_payload("70.00")
    )
    gateway.responses[(ADJ_SUMMARY, "2026-09", "02")] = (
        _kardex_payload("30.00")
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "BRANCH",
            "measure": "outputValue",
            "subjects": [
                _subject("R07", "2026-09", "01"),
                _subject("R07", "2026-09", "02"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DIFFERENT"
    assert data["diffs"][0]["delta"] == "-40.00"
    assert data["diffs"][0]["deltaPct"] == "-57.14"


def test_r10_universe_mismatch_rejected(gateway):
    gateway.responses[(CCE, "2026-08")] = _cce_payload("1000.00")
    gateway.responses[(CCE, "2026-09")] = _cce_payload("1200.00")
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "totalValue",
            "subjects": [
                _subject(
                    "R10", "2026-08", universe="calculation"
                ),
                _subject(
                    "R10", "2026-09", universe="investigation"
                ),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "INCOMPATIBLE"
    assert data["diffs"] == []
    assert (
        data["compatibility"][0]["reason"] == "r10_universe_mismatch"
    )


def test_r10_same_universe_comparable(gateway):
    gateway.responses[(CCE, "2026-08")] = _cce_payload(
        "1000.00",
        by_cc=[
            {"costCenter": "0404", "totalValue": "50000.00"},
            {"costCenter": "1010", "totalValue": "25000.00"},
        ],
    )
    gateway.responses[(CCE, "2026-09")] = _cce_payload(
        "1200.00",
        by_cc=[
            {"costCenter": "0404", "totalValue": "65000.00"},
            {"costCenter": "1010", "totalValue": "25000.00"},
        ],
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "totalValue",
            "grain": "cost_center",
            "subjects": [
                _subject("R10", "2026-08"),
                _subject("R10", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DIFFERENT"
    keys = {d["grainKey"] for d in data["diffs"]}
    assert keys == {"0404", "1010"}
    forwarded = {params["universe"] for _p, params in gateway.calls}
    assert forwarded == {"calculation"}  # default universe forwarded


def test_r11_period_candidates(gateway):
    gateway.responses[(ROSTER, "2026-08")] = _roster_payload(
        "90000.00"
    )
    gateway.responses[(ROSTER, "2026-09")] = _roster_payload(
        "97462.71"
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "totalValue",
            "subjects": [
                _subject("R11", "2026-08"),
                _subject("R11", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DIFFERENT"
    assert data["diffs"][0]["delta"] == "7462.71"
    for _path, params in gateway.calls:
        assert params["view"] == "candidates"


# --- related comparisons ----------------------------------------------------


def test_r06_x_cpv_related_not_equivalent(gateway):
    gateway.responses[(KARDEX_SUMMARY, "2026-09")] = (
        _kardex_payload("100.00")
    )
    gateway.responses[(CPV, "2026-09")] = _cpv_payload("80.00")
    response = _post(
        _client(),
        {
            "comparisonKind": "REPORT",
            "subjects": [
                _subject("R06", "2026-09"),
                _subject("CPV", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DIFFERENT"
    assert "relacionadas" in data["statusReason"]
    assert (
        data["compatibility"][0]["classification"]
        == "RELATED_REQUIRES_EXPLANATION"
    )
    assert data["compatibility"][0]["deltaSemantics"] == (
        "related_not_equivalent"
    )
    assert data["diffs"][0]["deltaSemantics"] == (
        "related_not_equivalent"
    )
    # each subject resolved its own default measure
    assert data["subjects"][0]["measure"] == "outputValue"
    assert data["subjects"][1]["measure"] == "cpvTotal"


def test_explain_r06_x_cpv(gateway):
    gateway.responses[(KARDEX_SUMMARY, "2026-09")] = (
        _kardex_payload("100.00")
    )
    gateway.responses[(CPV, "2026-09")] = _cpv_payload("80.00")
    response = _post(
        _client(),
        {
            "comparisonKind": "EXPLAIN",
            "subjects": [
                _subject("R06", "2026-09"),
                _subject("CPV", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DIFFERENT"
    assert data["diffs"] == []  # explanation only — no delta rows
    assert "CPV" in data["compatibility"][0]["explanation"]


# --- non-comparable ---------------------------------------------------------


def test_r12_x_r15_not_implemented():
    response = _post(
        _client(),
        {
            "comparisonKind": "REPORT",
            "subjects": [
                _subject("R12", "2026-09"),
                _subject("R15", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "INSUFFICIENT_EVIDENCE"
    assert {
        s["errorCode"] for s in data["subjects"]
    } == {"report_not_implemented"}
    assert data["diffs"] == []


def test_unknown_report_insufficient_evidence():
    response = _post(
        _client(),
        {
            "comparisonKind": "REPORT",
            "subjects": [
                _subject("R06", "2026-09"),
                _subject("R99", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "INSUFFICIENT_EVIDENCE"
    assert data["subjects"][1]["errorCode"] == "unknown_report"


def test_unsupported_filter_rejected():
    response = _post(
        _client(),
        {
            "comparisonKind": "REPORT",
            "subjects": [
                _subject("R10", "2026-09", sql_filter="1=1"),
                _subject("R10", "2026-08"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["subjects"][0]["errorCode"] == "unsupported_filter"


def test_measure_not_supported_marked(gateway):
    gateway.responses[(KARDEX_SUMMARY, "2026-07")] = (
        _kardex_payload("100.00")
    )
    gateway.responses[(CCE, "2026-08")] = _cce_payload("1000.00")
    response = _post(
        _client(),
        {
            "comparisonKind": "REPORT",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R10", "2026-08"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["measureNotes"][0]["index"] == 1
    # the R06×R10 pair has no curated verdict → INSUFFICIENT_EVIDENCE
    assert (
        data["compatibility"][0]["classification"]
        == "INSUFFICIENT_EVIDENCE"
    )
    assert data["diffs"] == []


# --- partial results --------------------------------------------------------


def test_unavailable_subject_partial(gateway):
    gateway.responses[(KARDEX_SUMMARY, "2026-07")] = (
        _kardex_payload("100.00")
    )
    gateway.responses[(KARDEX_SUMMARY, "2026-08")] = (
        DelpiApiGatewayError("down", status_code=503)
    )
    gateway.responses[(KARDEX_SUMMARY, "2026-09")] = (
        _kardex_payload("150.00")
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
                _subject("R06", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "PARTIAL"
    assert data["subjects"][1]["status"] == "unavailable"
    # deltas computed only across authorized/available subjects —
    # never an implicit zero for 2026-08
    assert {d["target"]["index"] for d in data["diffs"]} == {2}


def test_empty_subject_distinguished_from_zero(gateway):
    gateway.responses[(KARDEX_SUMMARY, "2026-07")] = {
        "status": "no_matching_items",
        "parityStatus": "PENDING",
    }
    gateway.responses[(KARDEX_SUMMARY, "2026-08")] = (
        _kardex_payload("0.00")
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["subjects"][0]["status"] == "empty"
    assert data["subjects"][0]["errorCode"] == "no_matching_items"
    # a real zero remains a value, not an absence
    assert data["subjects"][1]["measureValue"] == "0.00"
    assert data["status"] == "INSUFFICIENT_EVIDENCE"


def test_zero_baseline_no_percentage(gateway):
    gateway.responses[(KARDEX_SUMMARY, "2026-07")] = (
        _kardex_payload("0.00")
    )
    gateway.responses[(KARDEX_SUMMARY, "2026-08")] = (
        _kardex_payload("50.00")
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "PERIOD",
            "measure": "outputValue",
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
            ],
        },
    )
    assert response.status_code == 200
    diff = response.json()["data"]["diffs"][0]
    assert diff["delta"] == "50.00"
    assert diff["deltaPct"] is None
    assert diff["deltaPctReason"].startswith("zero_baseline")


# --- DOCUMENT kind — R10 × R11 ----------------------------------------------


def _r10_items() -> list[dict]:
    return [
        {
            "lineId": "l1",
            "branchCode": "01",
            "document": "103033",
            "series": "1",
            "productCode": "9001",
        },
        {
            "lineId": "l2",
            "branchCode": "01",
            "document": "103200",
            "series": "1",
            "productCode": "9002",
        },
        {  # incomplete key — never matches
            "lineId": "l3",
            "branchCode": "01",
            "document": "",
            "series": "",
            "productCode": "9003",
        },
    ]


def _r11_items() -> list[dict]:
    return [
        {
            "lineId": "r1",
            "branchCode": "01",
            "document": "103033",
            "series": "1",
            "productCode": "9001",
        },
        {
            "lineId": "r2",
            "branchCode": "01",
            "document": "103033",
            "series": "1",
            "productCode": "9050",
        },
        {
            "lineId": "r3",
            "branchCode": "01",
            "document": "103199",
            "series": "1",
            "productCode": "9077",
        },
    ]


def test_document_r10_x_r11_matches_by_full_key(gateway):
    gateway.responses[(CCE, "2026-09")] = _cce_payload(
        "1000.00", items=_r10_items(), total_items=3
    )
    gateway.responses[(ROSTER, "2026-09")] = _roster_payload(
        "90000.00", items=_r11_items(), total_items=3
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "DOCUMENT",
            "subjects": [
                _subject("R10", "2026-09"),
                _subject("R11", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    doc = data["documentAnalysis"]
    assert data["status"] == "DIFFERENT"
    assert doc["status"] == "OK"
    assert doc["matchCount"] == 1
    match = doc["matchedDocuments"][0]
    assert match["document"] == "103033"
    assert match["series"] == "1"
    assert match["productsCommon"] == ["9001"]
    assert match["productsOnlyB"] == ["9050"]
    # incomplete-key item declared, never matched
    assert doc["incompleteKeys"]["0"][0]["lineId"] == "l3"


def test_document_no_matches(gateway):
    gateway.responses[(CCE, "2026-09")] = _cce_payload(
        "1000.00",
        items=[_r10_items()[1]],
        total_items=1,
    )
    gateway.responses[(ROSTER, "2026-09")] = _roster_payload(
        "90000.00",
        items=[_r11_items()[2]],
        total_items=1,
    )
    response = _post(
        _client(),
        {
            "comparisonKind": "DOCUMENT",
            "subjects": [
                _subject("R10", "2026-09"),
                _subject("R11", "2026-09"),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["documentAnalysis"]["status"] == "NO_MATCHES"
    assert data["status"] == "EQUAL"


# --- CLARA semantic parity ---------------------------------------------------


def test_clara_analyze_action_registered():
    from controllership_finance_app.interface.mcp import (
        semantic_bridge as sb,
    )

    assert "report_comparison" in sb.ANALYZE_ACTIONS
    schema = sb._schema_for("closing", "report_comparison")
    assert schema["tool"] == "analyze"
    assert "subjects" in schema["required_params"]


def test_clara_dispatch_reuses_same_portal_route(monkeypatch):
    """analyze(report_comparison) must call the SAME route function
    the Portal calls — parity by construction via _call_route."""
    from controllership_finance_app.interface.mcp import tool_bridge
    from controllership_finance_app.interface.http.routes import (
        analysis_routes,
    )

    captured: dict = {}

    def fake_call_route(fn, request, **params):
        captured["fn"] = fn
        captured["params"] = params
        return tool_bridge._ok({"status": "DIFFERENT"})

    monkeypatch.setattr(tool_bridge, "_call_route", fake_call_route)
    monkeypatch.setattr(
        tool_bridge,
        "_user_and_access",
        lambda: (MagicMock(), SimpleNamespace(id="u-1")),
    )
    result = tool_bridge.tool_analyze_report_comparison(
        subjects=[
            _subject("R06", "2026-07"),
            _subject("R06", "2026-08"),
        ],
        comparison_kind="PERIOD",
        measure="outputValue",
    )
    assert result.is_error is False
    assert captured["fn"] is (
        analysis_routes.post_closing_analysis_report_comparison
    )
    body = captured["params"]["body"]
    assert body.comparison_kind == "PERIOD"
    assert body.subjects[0].report_id == "R06"
    assert body.measure == "outputValue"


def test_clara_semantic_tool_analyze_dispatch(monkeypatch):
    """tool_analyze('report_comparison', parameters={subjects…})
    flows through the registry validation to the handler."""
    from controllership_finance_app.interface.mcp import (
        semantic_bridge as sb,
    )
    from controllership_finance_app.interface.mcp import tool_bridge

    seen: dict = {}

    def fake_handler(**params):
        seen.update(params)
        return tool_bridge._ok({"status": "DIFFERENT"})

    monkeypatch.setitem(
        sb.ANALYZE_ACTIONS["report_comparison"],
        "handler",
        fake_handler,
    )
    res = sb.tool_analyze(
        "report_comparison",
        parameters={
            "subjects": [
                _subject("R06", "2026-07"),
                _subject("R06", "2026-08"),
            ],
            "comparison_kind": "PERIOD",
            "measure": "outputValue",
        },
    )
    assert res.is_error is False
    assert seen["comparison_kind"] == "PERIOD"
    payload = res.structured_content or {}
    assert payload["action"] == "report_comparison"


def test_clara_semantic_dispatch_rejects_unknown_param():
    from controllership_finance_app.interface.mcp import (
        semantic_bridge as sb,
    )

    res = sb.tool_analyze(
        "report_comparison",
        parameters={
            "subjects": [],
            "sql": "drop table",
        },
    )
    assert res.is_error is True
