# app/interfaces/http/rbac_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from app.application.use_cases.create_role_use_case import CreateRoleUseCase
from app.application.use_cases.list_role_permissions_use_case import ListRolePermissionsUseCase
from app.application.use_cases.replace_role_permissions_use_case import ReplaceRolePermissionsUseCase
from app.application.use_cases.add_permission_to_role_use_case import AddPermissionToRoleUseCase
from app.application.use_cases.remove_permission_from_role_use_case import RemovePermissionFromRoleUseCase

from app.application.use_cases.list_group_roles_use_case import ListGroupRolesUseCase
from app.application.use_cases.replace_group_roles_use_case import ReplaceGroupRolesUseCase
from app.application.use_cases.add_group_roles_use_case import AddRoleToGroupUseCase
from app.application.use_cases.remove_group_roles_use_case import RemoveRoleFromGroupUseCase

from app.application.use_cases.list_user_roles_use_case import ListUserRolesUseCase
from app.application.use_cases.replace_user_roles_use_case import ReplaceUserRolesUseCase
from app.application.use_cases.add_role_to_user_use_case import AddRoleToUserUseCase
from app.application.use_cases.remove_role_from_user_use_case import RemoveRoleFromUserUseCase

from app.application.use_cases.list_user_groups_use_case import ListUserGroupsUseCase
from app.application.use_cases.replace_user_groups_use_case import ReplaceUserGroupsUseCase
from app.application.use_cases.add_group_to_user_use_case import AddGroupToUserUseCase
from app.application.use_cases.remove_group_from_user_use_case import RemoveGroupFromUserUseCase

from app.interfaces.http.utils.errors import unauthorized, api_error


rbac_bp = Blueprint("rbac", __name__)


def require_auth():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()
    return None


# ==========================================================
# ROLES
# ==========================================================

@rbac_bp.route("/admin/roles", methods=["POST"])
def create_role():
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return api_error("validation_error", "Campo 'name' é obrigatório.", path="name")

    uow = SqlAlchemyUnitOfWork()
    uc = CreateRoleUseCase(uow)

    try:
        role_id = uc.execute(name=name, description=data.get("description"))
        return jsonify({"id": str(role_id)}), 201
    except Exception as e:
        uow.rollback()
        return api_error("create_role_failed", str(e))


@rbac_bp.route("/admin/roles/<role_id>/permissions", methods=["GET"])
def list_role_permissions(role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = ListRolePermissionsUseCase(uow)

    try:
        return jsonify(uc.execute(role_id)), 200
    except Exception as e:
        return api_error("list_role_permissions_failed", str(e), path="roleId")


@rbac_bp.route("/admin/roles/<role_id>/permissions", methods=["PUT"])
def replace_role_permissions(role_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    codes = data.get("codes")

    if not isinstance(codes, list):
        return api_error("validation_error", "Campo 'codes' deve ser uma lista.", path="codes")

    uow = SqlAlchemyUnitOfWork()
    uc = ReplaceRolePermissionsUseCase(uow)

    try:
        return jsonify(uc.execute(role_id, [str(c) for c in codes])), 200
    except Exception as e:
        uow.rollback()
        return api_error("replace_role_permissions_failed", str(e))


@rbac_bp.route("/admin/roles/<role_id>/permissions", methods=["POST"])
def add_permission_to_role(role_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()

    if not code:
        return api_error("validation_error", "Campo 'code' é obrigatório.", path="code")

    uow = SqlAlchemyUnitOfWork()
    uc = AddPermissionToRoleUseCase(uow)

    try:
        return jsonify(uc.execute(role_id, code)), 200
    except Exception as e:
        uow.rollback()
        return api_error("add_permission_to_role_failed", str(e))


@rbac_bp.route("/admin/roles/<role_id>/permissions/<permission_code>", methods=["DELETE"])
def remove_permission_from_role(role_id: str, permission_code: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = RemovePermissionFromRoleUseCase(uow)

    try:
        return jsonify(uc.execute(role_id, permission_code)), 200
    except Exception as e:
        uow.rollback()
        return api_error("remove_permission_from_role_failed", str(e))


# ==========================================================
# GROUPS
# ==========================================================

@rbac_bp.route("/admin/groups/<group_id>/roles", methods=["GET"])
def list_group_roles(group_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = ListGroupRolesUseCase(uow)
    return jsonify(uc.execute(group_id)), 200


@rbac_bp.route("/admin/groups/<group_id>/roles", methods=["PUT"])
def replace_group_roles(group_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    role_ids = data.get("roleIds", [])

    uow = SqlAlchemyUnitOfWork()
    uc = ReplaceGroupRolesUseCase(uow)

    try:
        return jsonify(uc.execute(group_id, role_ids)), 200
    except Exception as e:
        uow.rollback()
        return api_error("replace_group_roles_failed", str(e))


@rbac_bp.route("/admin/groups/<group_id>/roles/<role_id>", methods=["POST"])
def add_role_to_group(group_id: str, role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = AddRoleToGroupUseCase(uow)

    return jsonify(uc.execute(group_id, role_id)), 200


@rbac_bp.route("/admin/groups/<group_id>/roles/<role_id>", methods=["DELETE"])
def remove_role_from_group(group_id: str, role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = RemoveRoleFromGroupUseCase(uow)

    return jsonify(uc.execute(group_id, role_id)), 200


# ==========================================================
# USERS
# ==========================================================

@rbac_bp.route("/admin/users/<user_id>/roles", methods=["GET"])
def list_user_roles(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = ListUserRolesUseCase(uow)
    return jsonify(uc.execute(user_id)), 200


@rbac_bp.route("/admin/users/<user_id>/roles", methods=["PUT"])
def replace_user_roles(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    role_ids = data.get("roleIds", [])

    uow = SqlAlchemyUnitOfWork()
    uc = ReplaceUserRolesUseCase(uow)

    return jsonify(uc.execute(user_id, role_ids)), 200


@rbac_bp.route("/admin/users/<user_id>/roles/<role_id>", methods=["POST"])
def add_role_to_user(user_id: str, role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = AddRoleToUserUseCase(uow)

    return jsonify(uc.execute(user_id, role_id)), 200


@rbac_bp.route("/admin/users/<user_id>/roles/<role_id>", methods=["DELETE"])
def remove_role_from_user(user_id: str, role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = RemoveRoleFromUserUseCase(uow)

    return jsonify(uc.execute(user_id, role_id)), 200


@rbac_bp.route("/admin/users/<user_id>/groups", methods=["GET"])
def list_user_groups(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = ListUserGroupsUseCase(uow)
    return jsonify(uc.execute(user_id)), 200


@rbac_bp.route("/admin/users/<user_id>/groups", methods=["PUT"])
def replace_user_groups(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    group_ids = data.get("groupIds", [])

    uow = SqlAlchemyUnitOfWork()
    uc = ReplaceUserGroupsUseCase(uow)

    return jsonify(uc.execute(user_id, group_ids)), 200


@rbac_bp.route("/admin/users/<user_id>/groups/<group_id>", methods=["POST"])
def add_group_to_user(user_id: str, group_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = AddGroupToUserUseCase(uow)

    return jsonify(uc.execute(user_id, group_id)), 200


@rbac_bp.route("/admin/users/<user_id>/groups/<group_id>", methods=["DELETE"])
def remove_group_from_user(user_id: str, group_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = RemoveGroupFromUserUseCase(uow)

    return jsonify(uc.execute(user_id, group_id)), 200