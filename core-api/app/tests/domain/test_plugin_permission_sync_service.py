# app/tests/domain/test_plugin_permission_sync_service.py

from app.domain.services.plugin_permission_sync_service import PluginPermissionSyncService


def test_normalize_desired_forces_module_and_dedupes():
    desired = PluginPermissionSyncService.normalize_desired(
        "crm",
        [
            {"code": "crm.view", "name": "View", "module": "other"},
            {"code": "crm.view", "name": "Dup"},
            {"code": "  ", "name": "Empty"},
            {"code": "crm.edit", "name": None, "description": "x"},
        ],
    )

    assert desired == [
        {
            "code": "crm.view",
            "name": "View",
            "description": None,
            "module": "crm",
        },
        {
            "code": "crm.edit",
            "name": "crm.edit",
            "description": "x",
            "module": "crm",
        },
    ]


def test_normalize_desired_empty():
    assert PluginPermissionSyncService.normalize_desired("crm", None) == []
    assert PluginPermissionSyncService.normalize_desired("crm", []) == []
