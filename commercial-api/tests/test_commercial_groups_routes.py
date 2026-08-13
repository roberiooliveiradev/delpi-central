from pathlib import Path


ROUTES = (
    Path(__file__).resolve().parents[1]
    / "commercial_app"
    / "interface"
    / "http"
    / "routes"
    / "group_routes.py"
).read_text(encoding="utf-8")

MAIN = (
    Path(__file__).resolve().parents[1]
    / "commercial_app"
    / "main.py"
).read_text(encoding="utf-8")


def test_groups_router_prefix() -> None:
    assert 'prefix="/groups"' in ROUTES


def test_groups_operation_ids_registered() -> None:
    assert 'operation_id="list_commercial_groups"' in ROUTES
    assert 'operation_id="get_commercial_group"' in ROUTES
    assert 'operation_id="create_commercial_group"' in ROUTES
    assert 'operation_id="replace_commercial_group_members"' in ROUTES
    assert 'operation_id="add_commercial_group_member"' in ROUTES
    assert 'operation_id="remove_commercial_group_member"' in ROUTES


def test_groups_member_paths_exist() -> None:
    assert '"/{group_id}/members"' in ROUTES
    assert '"/{group_id}/members/{user_id}"' in ROUTES
    assert 'def list_commercial_groups(' in ROUTES
    assert 'def get_commercial_group(' in ROUTES
    assert 'def create_commercial_group(' in ROUTES


def test_groups_require_manage_permission() -> None:
    assert "COMMERCIAL_MANAGE_PERMISSIONS" in ROUTES
    assert ROUTES.count("@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)") == 6


def test_groups_mutations_pass_actor_user_id() -> None:
    assert "actor_user_id=_current_user_id(request)" in ROUTES
    assert "created_by_user_id=_current_user_id(request)" in ROUTES


def test_groups_router_mounted_in_main() -> None:
    assert "group_router" in MAIN
    assert "app.include_router(group_router)" in MAIN
