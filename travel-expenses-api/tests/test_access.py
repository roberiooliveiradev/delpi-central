from types import SimpleNamespace

from travel_expenses_app.application.security import travel_expenses_permissions as perms


def test_build_access_payload_write_unit():
    user = SimpleNamespace(
        permissions=["travel-expenses.write", "travel-expenses.unit.filial-02"],
        is_superadmin=False,
    )
    payload = perms.build_access_payload(user)
    assert payload["canWrite"] is True
    assert payload["canManage"] is False
    assert payload["units"] == [
        {
            "id": "02",
            "label": "Espírito Santo",
            "view": True,
            "write": True,
            "manage": False,
        }
    ]


def test_unit_codes_for_read_includes_write_only():
    user = SimpleNamespace(
        permissions=["travel-expenses.write", "travel-expenses.unit.filial-01"],
        is_superadmin=False,
    )
    assert perms.unit_codes_for_read(user) == ["01"]


def test_admin_sees_all_units():
    user = SimpleNamespace(permissions=["travel-expenses.admin"], is_superadmin=True)
    assert perms.unit_codes_for_read(user) == ["01", "02"]
    assert perms.build_access_payload(user)["admin"] is True
