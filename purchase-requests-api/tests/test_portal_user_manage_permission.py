from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_portal_user_manage,
)


def test_has_portal_user_manage_requires_both_permissions() -> None:
    actor = type(
        "User",
        (),
        {"is_superadmin": False, "permissions": ["rbac.manage"]},
    )()
    assert not has_portal_user_manage(actor)

    actor_ok = type(
        "User",
        (),
        {"is_superadmin": False, "permissions": ["rbac.manage", "users.manage"]},
    )()
    assert has_portal_user_manage(actor_ok)
