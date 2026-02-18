# app/interfaces/http/rbac_admin_controller.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy.exc import IntegrityError

from app.extensions.db import db

from app.domain.services.permission_resolver import resolve_user_permissions
from app.extensions.permission_cache import invalidate_user_permissions
from app.domain.services.audit_log_service import log_audit

from app.infrastructure.db.models import (
    User,
    Role,
    Group,
    Permission,
    UserPermission,
)


rbac_admin_bp = Blueprint("rbac_admin", __name__, url_prefix="/core-api/admin/rbac")


# =========================================================
# Helpers
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


def _json_role(role: Role):
    return {
        "id": str(role.id),
        "name": role.name,
        "description": getattr(role, "description", None),
        "permissions": [{"id": str(p.id), "code": p.code, "name": p.name} for p in role.permissions],
    }


def _json_permission(p: Permission):
    return {
        "id": str(p.id),
        "code": p.code,
        "name": p.name,
        "description": getattr(p, "description", None),
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
    # Diretos
    for user in role.users:
        invalidate_user_permissions(user.id)

    # Via grupos
    for group in role.groups:
        for user in group.users:
            invalidate_user_permissions(user.id)

# =========================================================
# Permissions (CRUD)
# =========================================================
@rbac_admin_bp.get("/permissions")
def list_permissions():
    rows = Permission.query.order_by(Permission.code.asc()).all()
    return jsonify([_json_permission(p) for p in rows])


@rbac_admin_bp.post("/permissions")
def create_permission():
    data = request.get_json(force=True) or {}
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or None)

    if not code or not name:
        return jsonify({"error": "code and name are required"}), 400

    p = Permission(code=code, name=name, description=description)
    db.session.add(p)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "permission code already exists"}), 409

    log_audit(
        action="permissions.create",
        entity_type="permission",
        entity_id=p.id,
        payload={"payload": data}
    )
    
    return jsonify(_json_permission(p)), 201


@rbac_admin_bp.put("/permissions/<permission_id>")
def update_permission(permission_id: str):
    p = Permission.query.get(permission_id)
    if not p:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    if "code" in data:
        p.code = (data.get("code") or "").strip()
    if "name" in data:
        p.name = (data.get("name") or "").strip()
    if "description" in data:
        p.description = data.get("description")

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "permission code already exists"}), 409

    log_audit(
        action="permissions.update",
        entity_type="permission",
        entity_id=permission_id,
        payload={"payload": data}
    )

    return jsonify(_json_permission(p))


@rbac_admin_bp.delete("/permissions/<permission_id>")
def delete_permission(permission_id: str):
    p = Permission.query.get(permission_id)
    if not p:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok": True})


# =========================================================
# Roles (CRUD + bind permissions)
# =========================================================
@rbac_admin_bp.get("/roles")
def list_roles():
    rows = Role.query.order_by(Role.name.asc()).all()
    return jsonify([_json_role(r) for r in rows])


@rbac_admin_bp.post("/roles")
def create_role():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    description = data.get("description")

    if not name:
        return jsonify({"error": "name is required"}), 400

    role = Role(name=name, description=description)
    db.session.add(role)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "role name already exists"}), 409

    log_audit(
        action="roles.create",
        entity_type="role",
        entity_id=role.id,
        payload={"payload": data}
    )

    return jsonify(_json_role(role)), 201


@rbac_admin_bp.put("/roles/<role_id>")
def update_role(role_id: str):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    if "name" in data:
        role.name = (data.get("name") or "").strip()
    if "description" in data:
        role.description = data.get("description")

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "role name already exists"}), 409

    log_audit(
        action="roles.update",
        entity_type="role",
        entity_id=role_id,
        payload={"payload": data}
    )

    return jsonify(_json_role(role))


@rbac_admin_bp.delete("/roles/<role_id>")
def delete_role(role_id: str):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(role)
    db.session.commit()
    return jsonify({"ok": True})


@rbac_admin_bp.put("/roles/<role_id>/permissions")
def set_role_permissions(role_id: str):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    ids = data.get("permissionIds") or []
    if not isinstance(ids, list):
        return jsonify({"error": "permissionIds must be a list"}), 400

    perms = Permission.query.filter(Permission.id.in_(ids)).all() if ids else []
    role.permissions = perms
    db.session.commit()

    invalidate_role_users(role)

    return jsonify(_json_role(role))


# =========================================================
# Groups (CRUD + bind roles)
# =========================================================
@rbac_admin_bp.get("/groups")
def list_groups():
    rows = Group.query.order_by(Group.name.asc()).all()
    return jsonify([_json_group(gr) for gr in rows])


@rbac_admin_bp.post("/groups")
def create_group():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    description = data.get("description")

    if not name:
        return jsonify({"error": "name is required"}), 400

    gr = Group(name=name, description=description)
    db.session.add(gr)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "group name already exists"}), 409


    log_audit(
        action="groups.create",
        entity_type="group",
        entity_id=gr.id,
        payload={"payload": data}
    )

    return jsonify(_json_group(gr)), 201


@rbac_admin_bp.put("/groups/<group_id>")
def update_group(group_id: str):
    gr = Group.query.get(group_id)
    if not gr:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    if "name" in data:
        gr.name = (data.get("name") or "").strip()
    if "description" in data:
        gr.description = data.get("description")

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "group name already exists"}), 409

    log_audit(
        action="groups.update",
        entity_type="group",
        entity_id=group_id,
        payload={"payload": data}
    )

    return jsonify(_json_group(gr))


@rbac_admin_bp.delete("/groups/<group_id>")
def delete_group(group_id: str):
    gr = Group.query.get(group_id)
    if not gr:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(gr)
    db.session.commit()
    return jsonify({"ok": True})


@rbac_admin_bp.put("/groups/<group_id>/roles")
def set_group_roles(group_id: str):
    gr = Group.query.get(group_id)
    if not gr:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    ids = data.get("roleIds") or []
    if not isinstance(ids, list):
        return jsonify({"error": "roleIds must be a list"}), 400

    roles = Role.query.filter(Role.id.in_(ids)).all() if ids else []
    gr.roles = roles
    db.session.commit()
    return jsonify(_json_group(gr))


# =========================================================
# Users (list + bind roles/groups + overrides)
# =========================================================
@rbac_admin_bp.get("/users")
def list_users():
    q = (request.args.get("q") or "").strip().lower()
    query = User.query

    if q:
        query = query.filter(
            (User.email.ilike(f"%{q}%")) | (User.name.ilike(f"%{q}%"))
        )

    rows = query.order_by(User.email.asc()).limit(200).all()
    return jsonify([_json_user(u) for u in rows])


@rbac_admin_bp.get("/users/<user_id>")
def get_user(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_json_user(user))


@rbac_admin_bp.put("/users/<user_id>/roles")
def set_user_roles(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    ids = data.get("roleIds") or []

    roles = Role.query.filter(Role.id.in_(ids)).all() if ids else []
    user.roles = roles
    db.session.commit()

    invalidate_user_permissions(user.id)  

    return jsonify(_json_user(user))


@rbac_admin_bp.put("/users/<user_id>/groups")
def set_user_groups(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    ids = data.get("groupIds") or []
    if not isinstance(ids, list):
        return jsonify({"error": "groupIds must be a list"}), 400

    groups = Group.query.filter(Group.id.in_(ids)).all() if ids else []
    user.groups = groups
    db.session.commit()

    invalidate_user_permissions(user.id) 

    return jsonify(_json_user(user))


@rbac_admin_bp.get("/users/<user_id>/overrides")
def list_user_overrides(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404

    rows = UserPermission.query.filter_by(user_id=user.id).all()

    resp = []
    for up in rows:
        p = Permission.query.get(up.permission_id)
        if not p:
            continue
        resp.append({
            "id": str(up.id),
            "permission": _json_permission(p),
            "granted": bool(up.granted),
        })

    return jsonify(resp)


@rbac_admin_bp.put("/users/<user_id>/overrides")
def set_user_overrides(user_id: str):
    """
    Body:
    {
      "overrides": [
        {"permissionId": "...", "granted": true},
        {"permissionId": "...", "granted": false}
      ]
    }
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    overrides = data.get("overrides") or []
    if not isinstance(overrides, list):
        return jsonify({"error": "overrides must be a list"}), 400

    # apaga e recria (simples e consistente)
    UserPermission.query.filter_by(user_id=user.id).delete(synchronize_session=False)

    for item in overrides:
        pid = item.get("permissionId")
        granted = bool(item.get("granted"))
        if not pid:
            continue
        db.session.add(UserPermission(user_id=user.id, permission_id=pid, granted=granted))

    db.session.commit()

    invalidate_user_permissions(user.id)

    return jsonify({"ok": True})
