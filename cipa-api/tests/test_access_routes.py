from types import SimpleNamespace

from cipa_app.application.security import cipa_permissions as perms


def test_build_access_payload_manage_unit():
    user = SimpleNamespace(
        permissions=["cipa.manage", "cipa.unit.filial-02"],
        is_superadmin=False,
    )
    payload = perms.build_access_payload(user)
    assert payload["can_manage"] is True
    assert payload["can_view"] is False
    assert payload["units"] == [
        {
            "id": "02",
            "label": "Espírito Santo",
            "view": True,
            "manage": True,
            "sign": False,
        }
    ]


def test_unit_codes_for_read_includes_manage_only():
    user = SimpleNamespace(
        permissions=["cipa.manage", "cipa.unit.filial-01"],
        is_superadmin=False,
    )
    assert perms.unit_codes_for_read(user) == ["01"]
