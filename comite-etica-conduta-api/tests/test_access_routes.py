from types import SimpleNamespace

from cec_app.application.security import cec_permissions as perms


def test_build_access_payload_manage_implies_view():
    user = SimpleNamespace(
        permissions=["comite-etica-conduta.manage"],
        is_superadmin=False,
    )
    payload = perms.build_access_payload(user)
    assert payload["can_manage"] is True
    assert payload["can_view"] is True
    assert payload["can_sign"] is True
    assert payload["units"] == [
        {
            "id": "00",
            "label": "Comitê de Ética e Conduta",
            "view": True,
            "manage": True,
            "sign": True,
        }
    ]


def test_unit_codes_for_read_corporate_only():
    user = SimpleNamespace(
        permissions=["comite-etica-conduta.manage"],
        is_superadmin=False,
    )
    assert perms.unit_codes_for_read(user) == ["00"]
