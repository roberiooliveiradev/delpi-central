from unittest.mock import MagicMock

import pytest

from si_app.application.services.strategic_indicators.admin_config_bundle_service import (
    AdminConfigBundleService,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


def _bundle(**overrides):
    payload = {
        "schema_version": 1,
        "departments": [
            {"department_id": "quality", "department_name": "Qualidade"},
        ],
        "department_indicators": [
            {
                "indicator_id": "quality-ppm",
                "department_id": "quality",
                "indicator_name": "PPM",
            }
        ],
        "indicator_goals": [
            {
                "indicator_id": "quality-ppm",
                "goal_year": 2026,
                "goal_label": "PPM",
                "goal_value": 10,
                "goal_periodicity": "monthly",
                "is_active": True,
                "goal_scope_branch": "",
            }
        ],
        "module_settings": {"parameters": {"items": []}, "governance": {"items": []}},
    }
    payload.update(overrides)
    return payload


def _repo_mock(**counts):
    repo = MagicMock()
    repo.count_catalog.return_value = {
        "departments": counts.get("departments", 7),
        "department_indicators": counts.get("department_indicators", 42),
        "indicator_goals": counts.get("indicator_goals", 42),
    }
    repo.list_department_ids.return_value = set()
    repo.list_indicator_ids.return_value = set()
    repo.list_active_goal_keys.return_value = set()
    return repo


def test_preview_replace_plans_deletes():
    repo = _repo_mock()
    service = AdminConfigBundleService(repo)
    result = service.preview(bundle=_bundle(), mode="replace")

    assert result["valid"] is True
    assert result["errors"] == []
    assert result["planned"]["departments"]["insert"] == 1
    assert result["planned"]["departments"]["delete"] == 7
    assert result["planned"]["department_indicators"]["delete"] == 42
    assert result["planned"]["indicator_goals"]["delete"] == 42
    assert result["planned"]["indicator_goals"]["insert"] == 1
    repo.import_bundle.assert_not_called()


def test_preview_invalid_indicator_without_department():
    repo = _repo_mock()
    service = AdminConfigBundleService(repo)
    result = service.preview(
        bundle=_bundle(
            department_indicators=[
                {"indicator_id": "quality-x", "department_id": "missing"}
            ]
        ),
        mode="replace",
    )
    assert result["valid"] is False
    assert any("quality-x" in item for item in result["errors"])
    repo.import_bundle.assert_not_called()


def test_preview_schema_version_raises():
    repo = _repo_mock()
    service = AdminConfigBundleService(repo)
    with pytest.raises(ValueError, match="schema_version"):
        service.preview(bundle=_bundle(schema_version=2), mode="replace")


def test_apply_invalid_does_not_import():
    repo = _repo_mock()
    service = AdminConfigBundleService(repo)
    with pytest.raises(ValueError):
        service.apply(
            bundle=_bundle(
                department_indicators=[
                    {"indicator_id": "quality-x", "department_id": "missing"}
                ]
            ),
            actor_user_id="user-1",
            mode="replace",
        )
    repo.import_bundle.assert_not_called()


def test_preview_merge_skips_existing_goal():
    repo = _repo_mock(departments=1, department_indicators=1, indicator_goals=1)
    repo.list_department_ids.return_value = {"quality"}
    repo.list_indicator_ids.return_value = {"quality-ppm"}
    repo.list_active_goal_keys.return_value = {("quality-ppm", 2026, "")}
    service = AdminConfigBundleService(repo)
    result = service.preview(bundle=_bundle(), mode="merge")
    assert result["valid"] is True
    assert result["planned"]["departments"]["update"] == 1
    assert result["planned"]["indicator_goals"]["skip"] == 1
    assert result["planned"]["indicator_goals"]["insert"] == 0
    assert result["planned"]["departments"]["delete"] == 0


def test_apply_replace_ignores_include_goals_false():
    repo = _repo_mock()
    repo.import_bundle.return_value = {"mode": "replace", "goals_created": 1}
    service = AdminConfigBundleService(repo)
    service.apply(
        bundle=_bundle(),
        actor_user_id="user-1",
        mode="replace",
        include_goals=False,
    )
    kwargs = repo.import_bundle.call_args.kwargs
    assert kwargs["include_goals"] is True
    assert kwargs["mode"] == "replace"


def test_injected_connection_execute_does_not_auto_commit():
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    repo = PluginBaseRepository(connection=connection)
    repo.execute("SELECT 1")
    connection.commit.assert_not_called()
    cursor.execute.assert_called_once()
