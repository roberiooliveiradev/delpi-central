from pathlib import Path

import pytest

from app.domain.services.chat_presentation_coverage_service import (
    ChatPresentationCoverageService,
)
from tests.fixtures.chat_presentation_regression_cases import (
    PRESENTATION_COVERAGE_EXPECTATIONS,
    PRESENTATION_DOMAIN_SAMPLES,
    PRESENTATION_FORMAT_ALIASES,
    PRESENTATION_SESSION_FORMAT_CASES,
)


def test_default_openapi_baseline_exists() -> None:
    path = ChatPresentationCoverageService.default_openapi_baseline_path()

    assert path.is_file()
    assert path.name == "openapi_baseline.json"


def test_build_matrix_has_expected_operation_count() -> None:
    rows = ChatPresentationCoverageService.build_matrix()

    assert len(rows) >= PRESENTATION_COVERAGE_EXPECTATIONS["min_operation_count"]


def test_summarize_tier_distribution() -> None:
    rows = ChatPresentationCoverageService.build_matrix()
    summary = ChatPresentationCoverageService.summarize(rows)

    assert summary["tierCounts"]["A"] >= PRESENTATION_COVERAGE_EXPECTATIONS["min_tier_a"]
    assert summary["tierCounts"]["B"] >= PRESENTATION_COVERAGE_EXPECTATIONS["min_tier_b"]
    assert summary["entityRoutedCount"] >= PRESENTATION_COVERAGE_EXPECTATIONS["min_entity_routed"]


@pytest.mark.parametrize(
    "sample",
    PRESENTATION_DOMAIN_SAMPLES,
    ids=[item["domain"] for item in PRESENTATION_DOMAIN_SAMPLES],
)
def test_domain_samples_resolve_entity(sample: dict[str, str]) -> None:
    entity, routed_by = ChatPresentationCoverageService.resolve_entity_for_path(sample["path"])

    assert entity == sample["entity"]
    assert routed_by in {"meta.entity", "path"}


def test_classify_tier_for_sql_and_product_structure() -> None:
    assert (
        ChatPresentationCoverageService.classify_tier(
            entity="sql_result",
            path="/data/sql",
        )
        == "D"
    )
    assert (
        ChatPresentationCoverageService.classify_tier(
            entity="product_structure",
            path="/products/90269001/structure",
        )
        == "A"
    )
    assert (
        ChatPresentationCoverageService.classify_tier(
            entity="supplies_cpv",
            path="/supplies/cpv",
        )
        == "B"
    )


def test_rows_to_csv_header() -> None:
    rows = ChatPresentationCoverageService.build_matrix()[:1]
    csv_text = ChatPresentationCoverageService.rows_to_csv(rows)

    assert "data_shape" in csv_text.splitlines()[0]
    assert "humanized_gaps" in csv_text.splitlines()[0]


def test_validate_for_ci_passes_on_current_matrix() -> None:
    validation = ChatPresentationCoverageService.validate_for_ci()

    assert validation["ok"] is True
    assert not validation["profileGaps"]
    assert not validation["entitySetProfileGaps"]


def test_find_entity_set_profile_gaps_is_empty() -> None:
    gaps = ChatPresentationCoverageService.find_entity_set_profile_gaps()

    assert gaps == []


def test_regression_fixture_domains_are_unique_enough() -> None:
    domains = {item["domain"] for item in PRESENTATION_DOMAIN_SAMPLES}

    assert domains >= {"product", "supplies", "hr", "quality", "commercial", "sql"}


def test_session_format_cases_have_required_keys() -> None:
    for case in PRESENTATION_SESSION_FORMAT_CASES:
        assert case["session_format"] in PRESENTATION_FORMAT_ALIASES or case["session_format"] in {
            "text",
            "table",
            "tree",
            "chart",
        }
        assert "expected_selected" in case


def test_build_report_writes_serializable_rows() -> None:
    report = ChatPresentationCoverageService.build_report()

    assert isinstance(report["summary"], dict)
    assert isinstance(report["rows"], list)
    assert report["rows"]


def test_validate_table_roles_for_ci_passes_on_tier_a_fixtures() -> None:
    from tests.fixtures.presentation_table_role_gate import validate_table_roles_for_ci

    validation = validate_table_roles_for_ci()

    assert validation["ok"] is True
    assert not validation["tableRoleGaps"]


def test_find_visual_builder_warnings_has_no_tier_a_gaps() -> None:
    warnings = ChatPresentationCoverageService.find_visual_builder_warnings()

    assert warnings == []
