import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

from tv_app.application.services.branch_policy_service import validate_data_route_branch
from tv_app.application.services.comunicado_data_enrichment_service import _build_data_cache_key
from tv_app.application.services.comunicado_native_config_sanitize import sanitize_comunicado_config
from tv_app.application.services.data.data_transform_contract import (
    DataTransformReadStatus,
    read_data_transform,
    sanitize_data_transform_for_persistence,
)
from tv_app.application.services.data.m_query.m_formatter import format_transform_plan_as_m
from tv_app.application.services.data.m_query.m_legacy_adapter import legacy_steps_to_plan
from tv_app.application.services.data.tv_data_config_validation_service import (
    TvDataConfigValidationService,
)
from tv_app.application.services.data.tv_data_transform_service import (
    apply_data_transform_steps,
    apply_transform_plan,
)
from tv_app.domain.data_query import (
    ColumnSchema,
    ColumnTypeSource,
    Diagnostic,
    DiagnosticSeverity,
    MType,
    MTypeKind,
    SourceRange,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPOSITORY_ROOT / "fixtures" / "tv-dashboard" / "m-query" / "v1-operations.json"


def _fixtures() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["operations"]


def test_domain_value_objects_are_typed_immutable_and_serializable():
    source_range = SourceRange(1, 1, 1, 4, 0, 3)
    diagnostic = Diagnostic(
        code="m.sample",
        severity=DiagnosticSeverity.WARNING,
        message="Aviso",
        source_range=source_range,
    )
    column = ColumnSchema(
        key="oee",
        label="OEE",
        m_type=MType(MTypeKind.NUMBER, nullable=True),
        type_source=ColumnTypeSource.DECLARED,
    )

    assert diagnostic.to_dict()["range"]["endColumn"] == 4
    assert column.to_dict() == {
        "key": "oee",
        "label": "OEE",
        "type": "number",
        "nullable": True,
        "typeSource": "declared",
    }
    with pytest.raises(FrozenInstanceError):
        column.label = "Outro"


@pytest.mark.parametrize("case", _fixtures(), ids=lambda case: case["name"])
def test_all_15_legacy_fixtures_have_plan_formatter_and_execution_parity(case):
    plan = legacy_steps_to_plan({"steps": case["legacySteps"]})

    assert plan is not None
    assert plan.steps
    assert plan.output == plan.steps[-1].name
    script = format_transform_plan_as_m(plan)
    assert script.startswith("let\n")
    assert "\nin\n    " in script
    assert "= RenameColumns(" not in script

    via_plan = apply_transform_plan(
        case["input"],
        plan,
        sibling_tables=case.get("siblingTables"),
    )
    via_legacy = apply_data_transform_steps(
        case["input"],
        case["legacySteps"],
        sibling_tables=case.get("siblingTables"),
    )
    assert via_plan == via_legacy == case["expected"]


def test_dual_reader_executes_v1_and_returns_safe_feature_disabled_for_v2():
    v1 = read_data_transform({"steps": [{"op": "select", "columns": ["a"]}]})
    v2 = read_data_transform(
        {
            "version": 2,
            "language": "m-delpi-v1",
            "script": "let\n    Fonte2 = Fonte\nin\n    Fonte2",
            "ast": {"must": "not persist"},
            "plan": {"must": "not persist"},
            "rows": [{"secret": 1}],
        }
    )

    assert v1.status == DataTransformReadStatus.READY
    assert v1.executable is True
    assert v2.status == DataTransformReadStatus.FEATURE_DISABLED
    assert v2.executable is False
    assert [item.code for item in v2.diagnostics] == ["m.execution_feature_disabled"]
    assert set(v2.normalized or {}) == {"version", "language", "script"}


def test_single_write_flag_keeps_v1_off_and_emits_only_v2_on():
    legacy = {"steps": [{"op": "rename", "from": "a", "to": "b"}]}

    assert sanitize_data_transform_for_persistence(
        legacy,
        write_v2_enabled=False,
    ) == legacy
    written = sanitize_data_transform_for_persistence(legacy, write_v2_enabled=True)
    assert written is not None
    assert set(written) == {"version", "language", "script"}
    assert written["version"] == 2
    assert "Table.RenameColumns" in written["script"]


def test_config_validation_rejects_new_v2_write_while_flag_is_disabled():
    service = TvDataConfigValidationService()
    result = service.validate(
        {
            "blocks": [
                {
                    "type": "data_source",
                    "dataBinding": {
                        "operationId": "get_overall_equipment_effectiveness_pct",
                        "params": {"periodDays": 7},
                        "displayMode": "auto",
                    },
                    "dataTransform": {
                        "version": 2,
                        "language": "m-delpi-v1",
                        "script": "let\n    X = Fonte\nin\n    X",
                    },
                }
            ]
        }
    )

    assert result["valid"] is False
    assert any(issue["field"].endswith(".dataTransform") for issue in result["issues"])


def test_config_sanitization_never_persists_runtime_plan_ast_or_rows():
    cleaned = sanitize_comunicado_config(
        {
            "blocks": [
                {
                    "id": "source",
                    "type": "data_source",
                    "resolved": {"table": {"rows": [{"secret": True}]}},
                    "dataTransform": {
                        "version": 2,
                        "language": "m-delpi-v1",
                        "script": "let\r\n    X = Fonte\r\nin\r\n    X",
                        "ast": {"node": "forbidden"},
                        "plan": {"steps": []},
                        "rows": [{"secret": True}],
                    },
                }
            ]
        }
    )

    block = cleaned["blocks"][0]
    assert "resolved" not in block
    assert block["dataTransform"] == {
        "version": 2,
        "language": "m-delpi-v1",
        "script": "let\n    X = Fonte\nin\n    X",
    }


def test_cache_isolates_two_users_and_service_context_without_raw_tokens():
    user_a = SimpleNamespace(sub="user-a", permissions=["tv-dashboard.view.filial-01"])
    user_b = SimpleNamespace(sub="user-b", permissions=["tv-dashboard.view.filial-01"])
    common = {
        "operation_id": "get_production_oee_series",
        "params": {"branch": "01"},
    }

    key_a = _build_data_cache_key(**common, authorization="Bearer token-a", user=user_a)
    key_b = _build_data_cache_key(**common, authorization="Bearer token-b", user=user_b)
    service_a = _build_data_cache_key(
        **common,
        authorization=None,
        service_context="public-presentation",
    )
    service_b = _build_data_cache_key(
        **common,
        authorization=None,
        service_context="admin-preview",
    )

    assert len({key_a, key_b, service_a, service_b}) == 4
    serialized = key_a + key_b
    assert "token-a" not in serialized and "token-b" not in serialized
    assert "authorizationFingerprint" in key_a


def test_branch_enforcement_uses_declarative_marker_and_canonical_aliases():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.view.filial-01"],
    )
    curated = {
        "tvConstraints": {
            "requiresBranchPermission": True,
            "branchParamAliases": ["filial"],
        }
    }

    validate_data_route_branch(curated, {"filial": "01"}, user=user)
    with pytest.raises(ValueError):
        validate_data_route_branch(curated, {"filial": "02"}, user=user)

    explicitly_public = {"tvConstraints": {"requiresBranchPermission": False}}
    validate_data_route_branch(explicitly_public, {"filial": "02"}, user=user)
