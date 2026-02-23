# app/interfaces/http/rbac_admin_controller.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from app.extensions.db import db
from app.domain.services.permission_resolver import resolve_user_permissions
from app.extensions.permission_cache import invalidate_user_permissions
from app.domain.services.audit_log_service import log_audit
from app.interfaces.http.utils.pagination import paginate_query

from app.infrastructure.db.models import (
    User,
    Role,
    Group,
    Permission,
    UserPermission,
)

rbac_admin_bp = Blueprint(
    "rbac_admin",
    __name__,
    url_prefix="/core-api/admin/rbac"
)

# =========================================================
# Auth
# =========================================================

def _is_authorized():
    user = getattr(g, "current_user", None)
    if not user:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    perms = set(resolve_user_permissions(user))
    return "rbac.manage" in perms


@rbac_admin_bp.before_request
def guard():
    if not _is_authorized():
        return jsonify({"error": "Forbidden"}), 403


# =========================================================
# Serializers
# =========================================================

def _json_permission(p: Permission):
    return {
        "id": str(p.id),
        "code": p.code,
        "name": p.name,
        "description": getattr(p, "description", None),
    }


def _json_role(role: Role):
    return {
        "id": str(role.id),
        "name": role.name,
        "description": getattr(role, "description", None),
        "permissions": [
            {"id": str(p.id), "code": p.code, "name": p.name}
            for p in role.permissions
        ],
    }


def _json_group(group: Group):
    return {
        "id": str(group.id),
        "name": group.name,
        "description": getattr(group, "description", None),
        "roles": [{"id": str(r.id), "name": r.name} for r in group.roles],
    }


def _json_user(user: User):
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "is_superadmin": getattr(user, "is_superadmin", False),
        "roles": [{"id": str(r.id), "name": r.name} for r in user.roles],
        "groups": [{"id": str(gr.id), "name": gr.name} for gr in user.groups],
    }


def invalidate_role_users(role):
    for user in role.users:
        invalidate_user_permissions(user.id)

    for group in role.groups:
        for user in group.users:
            invalidate_user_permissions(user.id)


# =========================================================
# Permissions
# =========================================================

@rbac_admin_bp.get("/permissions")
def list_permissions():
    q = (request.args.get("q") or "").strip().lower()
    query = Permission.query
    if q:
        query = query.filter(
            or_(
                Permission.code.ilike(f"%{q}%"),
                Permission.name.ilike(f"%{q}%")
            )
        )

    return paginate_query(
        query,
        _json_permission,
        Permission,
        allowed_sort_fields=["code", "name"],
        default_sort="code",
    )


@rbac_admin_bp.post("/permissions")
def create_permission():
    data = request.get_json(force=True) or {}
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()

    if not code or not name:
        return jsonify({"error": "code and name are required"}), 400

    p = Permission(code=code, name=name, description=data.get("description"))
    db.session.add(p)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "permission code already exists"}), 409

    log_audit("permissions.create", "permission", p.id, {"payload": data})
    return jsonify(_json_permission(p)), 201


@rbac_admin_bp.put("/permissions/<permission_id>")
def update_permission(permission_id: str):
    p = Permission.query.get(permission_id)
    if not p:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    for field in ["code", "name", "description"]:
        if field in data:
            setattr(p, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "permission code already exists"}), 409

    log_audit("permissions.update", "permission", permission_id, {"payload": data})
    return jsonify(_json_permission(p))


@rbac_admin_bp.delete("/permissions/<permission_id>")
def delete_permission(permission_id: str):
    p = Permission.query.get(permission_id)
    if not p:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(p)
    db.session.commit()

    log_audit("permissions.delete", "permission", permission_id, {})
    return jsonify({"ok": True})


@rbac_admin_bp.post("/permissions/bulk-delete")
def bulk_delete_permissions():
    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    rows = Permission.query.filter(Permission.id.in_(ids)).all()
    for r in rows:
        db.session.delete(r)

    db.session.commit()
    log_audit("permissions.bulk_delete", "permission", None, {"ids": ids})
    return jsonify({"ok": True, "deleted": len(rows)})


# =========================================================
# Roles
# =========================================================

@rbac_admin_bp.get("/roles")
def list_roles():
    q = (request.args.get("q") or "").strip().lower()
    query = Role.query
    if q:
        query = query.filter(
            or_(
                Role.name.ilike(f"%{q}%"),
                Role.description.ilike(f"%{q}%")
            )
        )

    return paginate_query(
        query,
        _json_role,
        Role,
        allowed_sort_fields=["name", "description"],
        default_sort="name",
    )


@rbac_admin_bp.post("/roles")
def create_role():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400

    role = Role(name=name, description=data.get("description"))
    db.session.add(role)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "role name already exists"}), 409

    log_audit("roles.create", "role", role.id, {"payload": data})
    return jsonify(_json_role(role)), 201


@rbac_admin_bp.put("/roles/<role_id>")
def update_role(role_id: str):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}

    if "name" in data:
        role.name = data["name"]

    if "description" in data:
        role.description = data["description"]

    db.session.commit()
    log_audit("roles.update", "role", role_id, {"payload": data})
    return jsonify(_json_role(role))


@rbac_admin_bp.delete("/roles/<role_id>")
def delete_role(role_id: str):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(role)
    db.session.commit()

    log_audit("roles.delete", "role", role_id, {})
    return jsonify({"ok": True})


@rbac_admin_bp.post("/roles/bulk-delete")
def bulk_delete_roles():
    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])

    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    roles = Role.query.filter(Role.id.in_(ids)).all()
    for role in roles:
        db.session.delete(role)

    db.session.commit()
    log_audit("roles.bulk_delete", "role", None, {"ids": ids})
    return jsonify({"ok": True, "deleted": len(roles)})


# =========================================================
# Groups
# =========================================================

@rbac_admin_bp.get("/groups")
def list_groups():
    q = (request.args.get("q") or "").strip().lower()
    query = Group.query
    if q:
        query = query.filter(
            or_(
                Group.name.ilike(f"%{q}%"),
                Group.description.ilike(f"%{q}%")
            )
        )

    return paginate_query(
        query,
        _json_group,
        Group,
        allowed_sort_fields=["name", "description"],
        default_sort="name",
    )


@rbac_admin_bp.post("/groups")
def create_group():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400

    group = Group(name=name, description=data.get("description"))
    db.session.add(group)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "group name already exists"}), 409

    log_audit("groups.create", "group", group.id, {"payload": data})
    return jsonify(_json_group(group)), 201


@rbac_admin_bp.put("/groups/<group_id>")
def update_group(group_id: str):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    for field in ["name", "description"]:
        if field in data:
            setattr(group, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "group name already exists"}), 409

    log_audit("groups.update", "group", group_id, {"payload": data})
    return jsonify(_json_group(group))


@rbac_admin_bp.delete("/groups/<group_id>")
def delete_group(group_id: str):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(group)
    db.session.commit()

    log_audit("groups.delete", "group", group_id, {})
    return jsonify({"ok": True})


@rbac_admin_bp.post("/groups/bulk-delete")
def bulk_delete_groups():
    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    rows = Group.query.filter(Group.id.in_(ids)).all()
    for r in rows:
        db.session.delete(r)

    db.session.commit()
    log_audit("groups.bulk_delete", "group", None, {"ids": ids})
    return jsonify({"ok": True, "deleted": len(rows)})


# =========================================================
# Users
# =========================================================

@rbac_admin_bp.get("/users")
def list_users():
    q = (request.args.get("q") or "").strip().lower()
    query = User.query

    if q:
        query = query.filter(
            or_(
                User.email.ilike(f"%{q}%"),
                User.name.ilike(f"%{q}%")
            )
        )

    return paginate_query(
        query,
        _json_user,
        User,
        allowed_sort_fields=["email", "name", "is_superadmin"],
        default_sort="email",
    )


@rbac_admin_bp.get("/users/<user_id>/overrides")
def list_user_overrides(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404

    query = UserPermission.query.filter_by(user_id=user.id)

    def serializer(up):
        p = Permission.query.get(up.permission_id)
        if not p:
            return None
        return {
            "id": str(up.id),
            "permission": _json_permission(p),
            "granted": bool(up.granted),
        }

    return paginate_query(query, serializer, UserPermission)