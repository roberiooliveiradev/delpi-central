# app/interfaces/http/rbac_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from app.application.use_cases.create_role_use_case import CreateRoleUseCase
from app.application.use_cases.update_role_use_case import UpdateRoleUseCase
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

from app.application.use_cases.list_group_users_use_case import ListGroupUsersUseCase
from app.application.use_cases.list_role_users_use_case import ListRoleUsersUseCase

from app.application.use_cases.admin.list_users_use_case import ListUsersUseCase
from app.application.use_cases.admin.list_roles_use_case import ListRolesUseCase
from app.application.use_cases.admin.list_groups_use_case import ListGroupsUseCase
from app.application.use_cases.admin.list_permissions_use_case import ListPermissionsUseCase
from app.application.use_cases.list_permission_usage_use_case import ListPermissionUsageUseCase

from app.application.use_cases.admin.delete_user_use_case import DeleteUserUseCase
from app.application.use_cases.admin.bulk_delete_users_use_case import BulkDeleteUsersUseCase
from app.application.use_cases.admin.update_user_admin_use_case import UpdateUserAdminUseCase

from app.application.use_cases.admin.create_group_use_case import CreateGroupUseCase
from app.application.use_cases.admin.update_group_use_case import UpdateGroupUseCase
from app.application.use_cases.admin.delete_group_use_case import DeleteGroupUseCase
from app.application.use_cases.admin.bulk_delete_groups_use_case import BulkDeleteGroupsUseCase

from app.application.use_cases.admin.delete_role_use_case import DeleteRoleUseCase
from app.application.use_cases.admin.bulk_delete_roles_use_case import BulkDeleteRolesUseCase

from app.interfaces.http.serializers.user_serializer import serialize_user_dto
from app.interfaces.http.utils.errors import api_error, server_error
from app.interfaces.http.security.authorization import (
    require_permission,
    require_all_permissions,
    require_superadmin,
)

rbac_bp = Blueprint("rbac", __name__)


# ==========================================================
# ROLES
# ==========================================================

@rbac_bp.route("/admin/rbac/roles", methods=["POST"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def create_role():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return api_error(
            "validation_error",
            "Campo 'name' é obrigatório.",
            path="name",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = CreateRoleUseCase(uow)
            role_id = uc.execute(
                name=name,
                description=data.get("description"),
            )

        return jsonify({"id": str(role_id)}), 201

    except Exception as e:
        return api_error("create_role_failed", str(e))


@rbac_bp.route("/admin/rbac/roles", methods=["GET"])
@require_permission("rbac.manage")
def list_roles():
    try:
        q = request.args.get("q")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        sort = request.args.get("sort", "name")
        direction = request.args.get("direction", "asc")

        with SqlAlchemyUnitOfWork() as uow:
            uc = ListRolesUseCase(uow)
            result = uc.execute(
                q=q,
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )

        return jsonify({
            "data": [r.__dict__ for r in result.data],
            "pagination": result.pagination.__dict__,
        }), 200

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>", methods=["PUT"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def update_role(role_id: str):
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    description = data.get("description")

    if not name:
        return api_error(
            "validation_error",
            "Campo 'name' é obrigatório.",
            path="name",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = UpdateRoleUseCase(uow)
            result = uc.execute(
                role_id=role_id,
                name=name,
                description=description,
            )

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>", methods=["DELETE"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def delete_role(role_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = DeleteRoleUseCase(uow)
            result = uc.execute(role_id)

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/roles/bulk-delete", methods=["POST"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def bulk_delete_roles():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids")

    if not isinstance(ids, list):
        return api_error(
            "validation_error",
            "Campo 'ids' deve ser uma lista.",
            path="ids",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = BulkDeleteRolesUseCase(uow)
            result = uc.execute(ids)

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e), path="ids")

    except Exception as e:
        return server_error(str(e))


# ==========================================================
# ROLE PERMISSIONS
# ==========================================================

@rbac_bp.route("/admin/rbac/roles/<role_id>/permissions", methods=["GET"])
@require_permission("rbac.manage")
def list_role_permissions(role_id: str):
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ListRolePermissionsUseCase(uow)
            permissions = uc.execute(role_id)

        return jsonify({
            "data": permissions,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(permissions),
                "total_pages": 1,
            },
        }), 200

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>/permissions", methods=["PUT"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def replace_role_permissions(role_id: str):
    data = request.get_json(silent=True) or {}
    permission_ids = data.get("permissionIds")

    if not isinstance(permission_ids, list):
        return api_error(
            "validation_error",
            "Campo 'permissionIds' deve ser uma lista.",
            path="permissionIds",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ReplaceRolePermissionsUseCase(uow)
            result = uc.execute(role_id, permission_ids)

        return jsonify(result), 200

    except Exception as e:
        return api_error("replace_role_permissions_failed", str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>/permissions", methods=["POST"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def add_permission_to_role(role_id: str):
    data = request.get_json(silent=True) or {}
    permission_id = (data.get("id") or "").strip()

    if not permission_id:
        return api_error(
            "validation_error",
            "Campo 'id' é obrigatório.",
            path="id",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = AddPermissionToRoleUseCase(uow)
            result = uc.execute(role_id, permission_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("add_permission_to_role_failed", str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>/permissions/<permission_id>", methods=["DELETE"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def remove_permission_from_role(role_id: str, permission_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = RemovePermissionFromRoleUseCase(uow)
            result = uc.execute(role_id, permission_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("remove_permission_from_role_failed", str(e))


# ==========================================================
# ROLE USERS
# ==========================================================

@rbac_bp.route("/admin/rbac/roles/<role_id>/users", methods=["GET"])
@require_permission("rbac.manage")
def list_role_users(role_id: str):
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ListRoleUsersUseCase(uow)
            users = uc.execute(role_id)

        return jsonify({
            "data": users,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(users),
                "total_pages": 1,
            },
        }), 200

    except ValueError as e:
        return api_error("not_found", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>/users/<user_id>", methods=["POST"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def add_user_to_role(role_id: str, user_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = AddRoleToUserUseCase(uow)
            result = uc.execute(user_id, role_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("add_user_to_role_failed", str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>/users/<user_id>", methods=["DELETE"])
@require_all_permissions(["rbac.manage", "roles.manage"])
def remove_user_from_role(role_id: str, user_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = RemoveRoleFromUserUseCase(uow)
            result = uc.execute(user_id, role_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("remove_user_from_role_failed", str(e))


# ==========================================================
# GROUPS
# ==========================================================

@rbac_bp.route("/admin/rbac/groups", methods=["GET"])
@require_permission("rbac.manage")
def list_groups():
    try:
        q = request.args.get("q")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        sort = request.args.get("sort", "name")
        direction = request.args.get("direction", "asc")

        with SqlAlchemyUnitOfWork() as uow:
            uc = ListGroupsUseCase(uow)
            result = uc.execute(
                q=q,
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )

        return jsonify({
            "data": [g.__dict__ for g in result.data],
            "pagination": result.pagination.__dict__,
        }), 200

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/groups", methods=["POST"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def create_group():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    description = data.get("description")

    if not name:
        return api_error(
            "validation_error",
            "Campo 'name' é obrigatório.",
            path="name",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = CreateGroupUseCase(uow)
            result = uc.execute(
                name=name,
                description=description,
            )

        return jsonify(result), 201

    except ValueError as e:
        return api_error("validation_error", str(e), path="name")

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/groups/<group_id>", methods=["PUT"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def update_group(group_id: str):
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    description = data.get("description")

    if not name:
        return api_error(
            "validation_error",
            "Campo 'name' é obrigatório.",
            path="name",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = UpdateGroupUseCase(uow)
            result = uc.execute(
                group_id=group_id,
                name=name,
                description=description,
            )

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/groups/<group_id>", methods=["DELETE"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def delete_group(group_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = DeleteGroupUseCase(uow)
            result = uc.execute(group_id)

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/groups/bulk-delete", methods=["POST"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def bulk_delete_groups():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids")

    if not isinstance(ids, list):
        return api_error(
            "validation_error",
            "Campo 'ids' deve ser uma lista.",
            path="ids",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = BulkDeleteGroupsUseCase(uow)
            result = uc.execute(ids)

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e), path="ids")

    except Exception as e:
        return server_error(str(e))


# ==========================================================
# GROUP ROLES
# ==========================================================

@rbac_bp.route("/admin/rbac/groups/<group_id>/roles", methods=["GET"])
@require_permission("rbac.manage")
def list_group_roles(group_id: str):
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ListGroupRolesUseCase(uow)
            roles = uc.execute(group_id)

        return jsonify({
            "data": roles,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(roles),
                "total_pages": 1,
            },
        }), 200

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/groups/<group_id>/roles", methods=["PUT"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def replace_group_roles(group_id: str):
    data = request.get_json(silent=True) or {}
    role_ids = data.get("roleIds", [])

    if not isinstance(role_ids, list):
        return api_error(
            "validation_error",
            "Campo 'roleIds' deve ser uma lista.",
            path="roleIds",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ReplaceGroupRolesUseCase(uow)
            result = uc.execute(group_id, role_ids)

        return jsonify(result), 200

    except Exception as e:
        return api_error("replace_group_roles_failed", str(e))


@rbac_bp.route("/admin/rbac/groups/<group_id>/roles/<role_id>", methods=["POST"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def add_role_to_group(group_id: str, role_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = AddRoleToGroupUseCase(uow)
            result = uc.execute(group_id, role_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("add_role_to_group_failed", str(e))


@rbac_bp.route("/admin/rbac/groups/<group_id>/roles/<role_id>", methods=["DELETE"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def remove_role_from_group(group_id: str, role_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = RemoveRoleFromGroupUseCase(uow)
            result = uc.execute(group_id, role_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("remove_role_from_group_failed", str(e))


# ==========================================================
# GROUP USERS
# ==========================================================

@rbac_bp.route("/admin/rbac/groups/<group_id>/users", methods=["GET"])
@require_permission("rbac.manage")
def list_group_users(group_id: str):
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ListGroupUsersUseCase(uow)
            users = uc.execute(group_id)

        return jsonify({
            "data": users,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(users),
                "total_pages": 1,
            },
        }), 200

    except ValueError as e:
        return api_error("not_found", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/groups/<group_id>/users/<user_id>", methods=["POST"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def add_user_to_group(group_id: str, user_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = AddGroupToUserUseCase(uow)
            result = uc.execute(user_id, group_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("add_user_to_group_failed", str(e))


@rbac_bp.route("/admin/rbac/groups/<group_id>/users/<user_id>", methods=["DELETE"])
@require_all_permissions(["rbac.manage", "groups.manage"])
def remove_user_from_group(group_id: str, user_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = RemoveGroupFromUserUseCase(uow)
            result = uc.execute(user_id, group_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("remove_user_from_group_failed", str(e))


# ==========================================================
# USERS
# ==========================================================

@rbac_bp.route("/admin/rbac/users", methods=["GET"])
@require_all_permissions(["rbac.manage", "users.view"])
def list_users():
    try:
        q = request.args.get("q")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        sort = request.args.get("sort", "email")
        direction = request.args.get("direction", "asc")

        with SqlAlchemyUnitOfWork() as uow:
            use_case = ListUsersUseCase(uow)
            result = use_case.execute(
                q=q,
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )

        return jsonify({
            "data": [serialize_user_dto(u) for u in result.data],
            "pagination": result.pagination.__dict__,
        }), 200

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/users/<user_id>", methods=["PUT"])
@require_all_permissions(["rbac.manage", "users.manage"])
def _parse_birth_date(value):
    if value is None or value == "":
        return None, False

    from datetime import date

    if isinstance(value, date):
        return value, False

    try:
        return date.fromisoformat(str(value)[:10]), False
    except ValueError as exc:
        raise ValueError("birthDate must be YYYY-MM-DD") from exc


def update_user(user_id: str):
    data = request.get_json(silent=True) or {}

    try:
        actor = g.current_user
        birth_date = None
        clear_birth_date = False

        if "birthDate" in data or "birth_date" in data:
            raw = data.get("birthDate", data.get("birth_date"))
            if raw is None:
                clear_birth_date = True
            else:
                birth_date, _ = _parse_birth_date(raw)

        with SqlAlchemyUnitOfWork() as uow:
            uc = UpdateUserAdminUseCase(uow)
            result = uc.execute(
                actor_id=str(actor.id),
                actor_is_superadmin=actor.is_superadmin,
                target_user_id=user_id,
                role_ids=data.get("roleIds", None),
                group_ids=data.get("groupIds", None),
                is_superadmin=data.get("is_superadmin", None),
                birth_date=birth_date,
                clear_birth_date=clear_birth_date,
            )

        if isinstance(result, tuple):
            return result

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/users/<user_id>", methods=["DELETE"])
@require_superadmin()
def delete_user(user_id: str):
    try:
        actor = g.current_user

        with SqlAlchemyUnitOfWork() as uow:
            uc = DeleteUserUseCase(uow)
            result = uc.execute(
                user_id,
                actor_user_id=str(actor.id),
            )

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/users/bulk-delete", methods=["POST"])
@require_superadmin()
def bulk_delete_users():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids")

    if not isinstance(ids, list):
        return api_error(
            "validation_error",
            "Campo 'ids' deve ser uma lista.",
            path="ids",
        )

    try:
        actor = g.current_user

        with SqlAlchemyUnitOfWork() as uow:
            uc = BulkDeleteUsersUseCase(uow)
            result = uc.execute(
                ids,
                actor_user_id=str(actor.id),
            )

        return jsonify(result), 200

    except ValueError as e:
        return api_error("validation_error", str(e))

    except Exception as e:
        return server_error(str(e))


# ==========================================================
# USER ROLES
# ==========================================================

@rbac_bp.route("/admin/rbac/users/<user_id>/roles", methods=["GET"])
@require_permission("rbac.manage")
def list_user_roles(user_id: str):
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ListUserRolesUseCase(uow)
            roles = uc.execute(user_id)

        return jsonify({
            "data": roles,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(roles),
                "total_pages": 1,
            },
        }), 200

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/users/<user_id>/roles", methods=["PUT"])
@require_all_permissions(["rbac.manage", "users.manage"])
def replace_user_roles(user_id: str):
    data = request.get_json(silent=True) or {}
    role_ids = data.get("roleIds", [])

    if not isinstance(role_ids, list):
        return api_error(
            "validation_error",
            "Campo 'roleIds' deve ser uma lista.",
            path="roleIds",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ReplaceUserRolesUseCase(uow)
            result = uc.execute(user_id, role_ids)

        return jsonify(result), 200

    except Exception as e:
        return api_error("replace_user_roles_failed", str(e))


@rbac_bp.route("/admin/rbac/users/<user_id>/roles/<role_id>", methods=["POST"])
@require_all_permissions(["rbac.manage", "users.manage"])
def add_role_to_user(user_id: str, role_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = AddRoleToUserUseCase(uow)
            result = uc.execute(user_id, role_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("add_role_to_user_failed", str(e))


@rbac_bp.route("/admin/rbac/users/<user_id>/roles/<role_id>", methods=["DELETE"])
@require_all_permissions(["rbac.manage", "users.manage"])
def remove_role_from_user(user_id: str, role_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = RemoveRoleFromUserUseCase(uow)
            result = uc.execute(user_id, role_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("remove_role_from_user_failed", str(e))


# ==========================================================
# USER GROUPS
# ==========================================================

@rbac_bp.route("/admin/rbac/users/<user_id>/groups", methods=["GET"])
@require_all_permissions(["rbac.manage", "users.view"])
def list_user_groups(user_id: str):
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ListUserGroupsUseCase(uow)
            groups = uc.execute(user_id)

        return jsonify({
            "data": groups,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(groups),
                "total_pages": 1,
            },
        }), 200

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/users/<user_id>/groups", methods=["PUT"])
@require_all_permissions(["rbac.manage", "users.manage"])
def replace_user_groups(user_id: str):
    data = request.get_json(silent=True) or {}
    group_ids = data.get("groupIds", [])

    if not isinstance(group_ids, list):
        return api_error(
            "validation_error",
            "Campo 'groupIds' deve ser uma lista.",
            path="groupIds",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ReplaceUserGroupsUseCase(uow)
            result = uc.execute(user_id, group_ids)

        return jsonify(result), 200

    except Exception as e:
        return api_error("replace_user_groups_failed", str(e))


@rbac_bp.route("/admin/rbac/users/<user_id>/groups/<group_id>", methods=["POST"])
@require_all_permissions(["rbac.manage", "users.manage"])
def add_group_to_user(user_id: str, group_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = AddGroupToUserUseCase(uow)
            result = uc.execute(user_id, group_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("add_group_to_user_failed", str(e))


@rbac_bp.route("/admin/rbac/users/<user_id>/groups/<group_id>", methods=["DELETE"])
@require_all_permissions(["rbac.manage", "users.manage"])
def remove_group_from_user(user_id: str, group_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = RemoveGroupFromUserUseCase(uow)
            result = uc.execute(user_id, group_id)

        return jsonify(result), 200

    except Exception as e:
        return api_error("remove_group_from_user_failed", str(e))


# ==========================================================
# PERMISSIONS
# ==========================================================

@rbac_bp.route("/admin/rbac/permissions/<permission_id>/usage", methods=["GET"])
@require_permission("rbac.manage")
def get_permission_usage(permission_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = ListPermissionUsageUseCase(uow)
            result = uc.execute(permission_id)

        return jsonify(result), 200

    except ValueError as e:
        return api_error("not_found", str(e))

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/rbac/permissions", methods=["GET"])
@require_permission("rbac.manage")
def list_permissions():
    try:
        q = request.args.get("q")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        sort = request.args.get("sort", "code")
        direction = request.args.get("direction", "asc")

        with SqlAlchemyUnitOfWork() as uow:
            uc = ListPermissionsUseCase(uow)
            result = uc.execute(
                q=q,
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )

        return jsonify({
            "data": [p.__dict__ for p in result.data],
            "pagination": result.pagination.__dict__,
        }), 200

    except Exception as e:
        return server_error(str(e))