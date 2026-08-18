from pathlib import Path
from unittest.mock import MagicMock

import pytest

from si_app.application.services.strategic_indicators.admin_config_bundle_service import (
    AdminConfigBundleService,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_audit_repository import (
    PostgresStrategicIndicatorsSettingsAuditRepository,
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


def test_preview_merge_inserts_new_department():
    repo = _repo_mock(departments=1, department_indicators=0, indicator_goals=0)
    repo.list_department_ids.return_value = {"existing"}
    service = AdminConfigBundleService(repo)
    result = service.preview(bundle=_bundle(), mode="merge")
    assert result["planned"]["departments"]["insert"] == 1
    assert result["planned"]["departments"]["update"] == 0
    assert result["planned"]["department_indicators"]["insert"] == 1


def test_preview_merge_include_goals_false_skips_goals():
    repo = _repo_mock()
    service = AdminConfigBundleService(repo)
    result = service.preview(
        bundle=_bundle(),
        mode="merge",
        include_goals=False,
    )
    assert result["planned"]["indicator_goals"]["insert"] == 0
    assert result["planned"]["indicator_goals"]["skip"] == 1


def test_apply_merge_keeps_include_goals_false():
    repo = _repo_mock()
    repo.list_department_ids.return_value = {"quality"}
    repo.list_indicator_ids.return_value = {"quality-ppm"}
    repo.import_bundle.return_value = {"mode": "merge", "goals_created": 0}
    service = AdminConfigBundleService(repo)
    service.apply(
        bundle=_bundle(),
        actor_user_id="user-1",
        mode="merge",
        include_goals=False,
    )
    assert repo.import_bundle.call_args.kwargs["include_goals"] is False


def test_delete_catalog_for_replace_uses_fk_order():
    from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_config_bundle_repository import (
        PostgresStrategicIndicatorsAdminConfigBundleRepository,
    )

    repo = PostgresStrategicIndicatorsAdminConfigBundleRepository(connection=MagicMock())
    repo.count_catalog = MagicMock(
        return_value={
            "departments": 7,
            "department_indicators": 42,
            "indicator_goals": 42,
        }
    )
    repo.execute = MagicMock()
    deleted = repo.delete_catalog_for_replace()
    sqls = [call.args[0] for call in repo.execute.call_args_list]
    assert "indicator_goals" in sqls[0]
    assert "department_indicators" in sqls[1]
    assert "departments" in sqls[2]
    assert deleted == {
        "goals_deleted": 42,
        "indicators_deleted": 42,
        "departments_deleted": 7,
    }


def test_apply_replace_wipe_insert_rolls_back_when_import_fails():
    repo = _repo_mock()
    repo.import_bundle.side_effect = RuntimeError("falha persistência")
    service = AdminConfigBundleService(repo)
    with pytest.raises(RuntimeError, match="falha persistência"):
        service.apply(bundle=_bundle(), actor_user_id="user-1", mode="replace")
    assert repo.import_bundle.call_count == 1


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


def test_apply_writes_config_imported_audit():
    repo = _repo_mock()
    repo.import_bundle.return_value = {"mode": "replace", "departments_upserted": 1}
    audit = MagicMock()
    service = AdminConfigBundleService(repo, audit_repository=audit)
    service.apply(bundle=_bundle(), actor_user_id="user-1", mode="replace")
    audit.insert_audit_event.assert_called_once()
    kwargs = audit.insert_audit_event.call_args.kwargs
    assert kwargs["event_type"] == "config.imported"
    assert kwargs["payload_after"]["mode"] == "replace"
    assert kwargs["payload_after"]["stats"]["departments_upserted"] == 1


def test_preview_does_not_write_audit():
    repo = _repo_mock()
    audit = MagicMock()
    service = AdminConfigBundleService(repo, audit_repository=audit)
    service.preview(bundle=_bundle(), mode="replace")
    audit.insert_audit_event.assert_not_called()


def test_export_writes_config_exported_audit():
    repo = _repo_mock()
    repo.export_bundle.return_value = _bundle()
    audit = MagicMock()
    service = AdminConfigBundleService(repo, audit_repository=audit)
    service.export(actor_user_id="user-1")
    kwargs = audit.insert_audit_event.call_args.kwargs
    assert kwargs["event_type"] == "config.exported"
    assert kwargs["payload_after"]["departments"] == 1


def test_insert_audit_event_uses_provided_event_type():
    repo = PostgresStrategicIndicatorsSettingsAuditRepository(connection=MagicMock())
    repo.execute = MagicMock()
    repo.insert_audit_event(
        entity_key="admin.config",
        payload_before=None,
        payload_after={"mode": "replace"},
        changed_by_user_id="user-1",
        event_type="config.imported",
    )
    params = repo.execute.call_args.args[1]
    assert params[0] == "config.imported"


def test_v033_allows_config_export_import_events():
    sql = Path("migrations/V033__settings_audit_config_import_events.sql").read_text(
        encoding="utf-8"
    )
    assert "config.exported" in sql
    assert "config.imported" in sql
    assert "ck_si_settings_audit_event_type" in sql
