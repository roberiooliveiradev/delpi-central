"""DAVI discovery-quality benchmark machinery tests.

TASK: DAVI-MCP-DISCOVERY-QUALITY-001

Validates the benchmark itself (dataset integrity, catalog coverage,
determinism, no tokens/network) — does not assert retrieval quality, which is
baseline-measured in evidence/davi-mcp-discovery-quality-001.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_API_ROOT))
sys.path.insert(0, str(_API_ROOT / "scripts"))

import pytest

from evaluate_davi_discovery_quality import _load_fixture, evaluate

_FIXTURE = _API_ROOT / "tests" / "fixtures" / "davi_discovery_quality_v1.json"
_POSITIVE_TYPES = {"POSITIVE_PRECISE", "POSITIVE_PARAPHRASE", "QUARANTINE_CONFLICT"}
_REQUIRED_KEYS = {
    "id",
    "query",
    "language",
    "case_type",
    "family",
    "expected_action_ids",
    "top1_required",
    "notes",
}
_ALLOWED_TYPES = {
    "POSITIVE_PRECISE",
    "POSITIVE_PARAPHRASE",
    "AMBIGUOUS",
    "WRITE_NEGATIVE",
    "GENERIC_SQL_NEGATIVE",
    "UNSUPPORTED_NEGATIVE",
    "QUARANTINE_CONFLICT",
}


@pytest.fixture(scope="module")
def fixture() -> dict:
    return _load_fixture()


@pytest.fixture(scope="module")
def catalog_ops() -> set[str]:
    from app.application.external_capabilities.dynamic_information.eligibility import (
        is_dynamically_executable,
    )
    from evaluate_davi_discovery_quality import _live_actions

    return {
        a.operation_id
        for a in _live_actions()
        if is_dynamically_executable(a.davi_status)
    }


def test_fixture_schema_valid(fixture: dict) -> None:
    assert fixture["benchmark_version"] == "1"
    for case in fixture["cases"]:
        assert _REQUIRED_KEYS <= set(case), case["id"]
        assert case["case_type"] in _ALLOWED_TYPES, case["id"]
        assert case["language"] in {"pt-BR", "en"}, case["id"]


def test_case_ids_unique(fixture: dict) -> None:
    ids = [c["id"] for c in fixture["cases"]]
    assert len(ids) == len(set(ids))


def test_expected_actions_exist_in_governed_catalog(
    fixture: dict, catalog_ops: set[str]
) -> None:
    for case in fixture["cases"]:
        for op in case["expected_action_ids"]:
            assert op in catalog_ops, f"{case['id']}: {op} not executable"


def test_every_governed_action_has_positive_coverage(
    fixture: dict, catalog_ops: set[str]
) -> None:
    covered = {
        op
        for c in fixture["cases"]
        if c["case_type"] in _POSITIVE_TYPES
        for op in c["expected_action_ids"]
    }
    assert covered == catalog_ops


def test_hard_negatives_have_no_expected_target(fixture: dict) -> None:
    for case in fixture["cases"]:
        if case["case_type"] in {"WRITE_NEGATIVE", "GENERIC_SQL_NEGATIVE"}:
            assert case["expected_action_ids"] == [], case["id"]


def test_ambiguous_cases_have_acceptable_set(fixture: dict) -> None:
    for case in fixture["cases"]:
        if case["case_type"] == "AMBIGUOUS":
            assert len(case["expected_action_ids"]) >= 2, case["id"]


def test_known_live_residual_case_present(fixture: dict) -> None:
    case = next(c for c in fixture["cases"] if c["id"] == "DQ-STOCK-001")
    assert case["query"] == "estoque atual do produto 10080034"
    assert case["expected_action_ids"] == ["get_product_stock"]
    assert case["case_type"] == "POSITIVE_PRECISE"


def test_runner_deterministic() -> None:
    a, b = evaluate(), evaluate()
    assert a["metrics"] == b["metrics"]
    assert a["known_failures"] == b["known_failures"]


def test_metrics_raw_and_not_hidden() -> None:
    m = evaluate()["metrics"]
    for key in (
        "top1_accuracy",
        "top3_recall",
        "top5_recall",
        "mrr",
        "hard_negative_zero_candidate_rate",
        "family_metrics",
    ):
        assert key in m
    assert m["case_counts"]["total"] == len(_load_fixture()["cases"])


def test_no_candidate_tokens_in_report() -> None:
    text = json.dumps(evaluate())
    assert "candidate_token" not in text


def test_runner_has_no_network_or_provider_dependency() -> None:
    src = (_API_ROOT / "scripts" / "evaluate_davi_discovery_quality.py").read_text(
        encoding="utf-8"
    )
    import re

    lowered = src.lower()
    assert not re.search(r"\bopenai\b", lowered)  # app.openapi() is allowed
    for forbidden in ("import requests", "import httpx", "urllib", "socket"):
        assert forbidden not in lowered, forbidden
