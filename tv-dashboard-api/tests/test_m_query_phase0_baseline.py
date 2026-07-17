import json
from pathlib import Path

from tv_app.application.services.branch_policy_service import validate_native_branch
from tv_app.application.services.comunicado_data_enrichment_service import (
    _build_data_cache_key,
)
from tv_app.application.services.data.tv_data_transform_service import (
    apply_data_transform_steps,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)
from tv_app.application.services.tv_dashboard_content_service import (
    _load_settings,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPOSITORY_ROOT / "fixtures" / "tv-dashboard" / "m-query"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def test_shared_v1_fixtures_cover_every_legacy_operation():
    payload = _load_fixture("v1-operations.json")
    operations = payload["operations"]
    names = {case["name"] for case in operations}

    assert names == {
        "rename",
        "select",
        "filter",
        "addColumn",
        "replace",
        "sort",
        "keepRows",
        "removeRows",
        "changeType",
        "fillDown",
        "firstRowAsHeader",
        "groupBy",
        "pivot",
        "unpivot",
        "merge",
    }

    for case in operations:
        actual = apply_data_transform_steps(
            case["input"],
            case["legacySteps"],
            sibling_tables=case.get("siblingTables"),
        )
        assert actual == case["expected"], case["name"]


def test_preview_by_step_uses_the_same_executor_with_step_prefixes():
    preview = _load_fixture("v1-operations.json")["previewByStep"]

    for index, expected in enumerate(preview["expectedStages"]):
        actual = apply_data_transform_steps(
            preview["input"],
            preview["legacySteps"][: index + 1],
        )
        assert actual == expected


def test_m_corpus_freezes_required_security_and_language_categories():
    corpus = _load_fixture("corpus.json")
    valid_tags = {tag for case in corpus["valid"] for tag in case["tags"]}
    invalid_tags = {tag for case in corpus["invalid"] for tag in case["tags"]}
    invalid_codes = {case["expectedCode"] for case in corpus["invalid"]}

    assert {"unicode", "comments", "v1-functions", "merge"} <= valid_tags
    assert {"forbidden", "adversarial", "io", "database", "recursion"} <= invalid_tags
    assert {
        "m.syntax_error",
        "m.function_not_allowed",
        "m.limit_expression_depth",
        "m.limit_script_bytes",
    } <= invalid_codes


def test_m_query_settings_expose_the_controlled_pilot_rollout():
    settings = _load_settings()["mQuery"]

    assert settings["profile"] == "m-delpi-v1"
    assert settings["defaultCulture"] == "pt-BR"
    assert settings["enabled"] is True
    assert settings["writeV2Enabled"] is True
    assert settings["advancedEditorEnabled"] is True
    assert settings["profilingEnabled"] is False
    assert settings["explainPlanEnabled"] is False
    assert settings["compileCacheEnabled"] is False
    assert settings["previewCacheEnabled"] is False
    assert settings["phase7TelemetryEnabled"] is True
    assert settings["maxScriptBytes"] == 65536
    assert settings["maxAstNodes"] == 5000
    assert settings["executionTimeoutMs"] == 2000


def test_lark_parser_dependency_is_pinned_without_runtime_integration():
    requirements = (REPOSITORY_ROOT / "tv-dashboard-api" / "requirements.txt").read_text(
        encoding="utf-8"
    )
    assert "lark==1.3.1" in requirements.splitlines()

    application_files = (
        REPOSITORY_ROOT / "tv-dashboard-api" / "tv_app" / "application"
    ).rglob("*.py")
    assert all("import lark" not in path.read_text(encoding="utf-8") for path in application_files)


def test_baseline_catalog_has_232_unique_allowlisted_get_operations():
    routes = TvDataRouteCatalogService().list_routes()
    operation_ids = [route["operationId"] for route in routes]

    assert len(operation_ids) == 232
    assert len(set(operation_ids)) == 232


def test_cache_key_isolated_between_distinct_authenticated_users_after_phase1():
    params = {"branch": "01", "periodDays": 7}

    user_a = _build_data_cache_key(
        operation_id="get_production_oee_series",
        params=params,
        authorization="Bearer user-a",
    )
    user_b = _build_data_cache_key(
        operation_id="get_production_oee_series",
        params=params,
        authorization="Bearer user-b",
    )

    assert user_a != user_b
    assert "Bearer user-a" not in user_a
    assert json.loads(user_a)["authorizationFingerprint"].startswith("sha256:")


def test_baseline_empty_static_branch_policy_remains_permissive():
    """Caracterização do baseline; RBAC granular continua em BranchAccessScopeService."""
    assert _load_settings()["branchPolicy"]["allowedBranches"] == []
    validate_native_branch({"branch": "99"})
