# app/interfaces/http/plugins_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from app.application.use_cases.register_plugin_use_case import RegisterPluginUseCase
from app.application.use_cases.update_plugin_manifest_use_case import UpdatePluginManifestUseCase
from app.application.use_cases.rollback_plugin_version_use_case import RollbackPluginVersionUseCase
from app.application.use_cases.unregister_plugin_use_case import UnregisterPluginUseCase
from app.application.use_cases.get_plugin_manifest_use_case import GetPluginManifestUseCase
from app.application.use_cases.list_plugin_versions_use_case import ListPluginVersionsUseCase

from app.application.use_cases.set_plugin_active_use_case import SetPluginActiveUseCase
from app.application.use_cases.bulk_set_plugins_active_use_case import BulkSetPluginsActiveUseCase
from app.application.use_cases.bulk_unregister_plugins_use_case import BulkUnregisterPluginsUseCase

from app.application.validators.manifest_validator import ManifestValidator

from app.interfaces.http.utils.errors import unauthorized, forbidden, bad_request, not_found


admin_plugins_bp = Blueprint(
    "admin_plugins",
    __name__,
    url_prefix="/admin/plugins",
)


def require_admin():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    if getattr(user, "is_superadmin", False):
        return None

    return forbidden("Forbidden")


# ==========================================================
# GET MANIFEST
# ==========================================================

@admin_plugins_bp.get("/<plugin_id>/manifest")
def get_manifest(plugin_id: str):
    guard = require_admin()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = GetPluginManifestUseCase(uow)
    result = uc.execute(plugin_id)

    if not result.success:
        return not_found("Manifest not found")

    return jsonify(result.manifest), 200


# ==========================================================
# REGISTER
# ==========================================================

@admin_plugins_bp.post("/register")
def register_plugin():
    guard = require_admin()
    if guard:
        return guard

    manifest = request.get_json(silent=True)
    if not isinstance(manifest, dict):
        return bad_request(
            "Body must be valid JSON",
            code="validation_error",
            path="_global"
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            validator = ManifestValidator()
            uc = RegisterPluginUseCase(uow, validator)
            result = uc.execute(manifest)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 201

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# UPDATE MANIFEST
# ==========================================================

@admin_plugins_bp.put("/<plugin_id>/manifest")
def update_manifest(plugin_id: str):
    guard = require_admin()
    if guard:
        return guard

    manifest = request.get_json(silent=True)
    if not isinstance(manifest, dict):
        return bad_request(
            "Body must be valid JSON",
            code="validation_error",
            path="_global"
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            validator = ManifestValidator()
            uc = UpdatePluginManifestUseCase(uow, validator)
            result = uc.execute(plugin_id, manifest)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# LIST VERSIONS
# ==========================================================

@admin_plugins_bp.get("/<plugin_id>/versions")
def list_versions(plugin_id: str):
    guard = require_admin()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = ListPluginVersionsUseCase(uow)
    result = uc.execute(plugin_id)

    if not result.success:
        return jsonify({"errors": result.errors}), 404

    return jsonify(result.versions), 200


# ==========================================================
# ROLLBACK
# ==========================================================

@admin_plugins_bp.post("/<plugin_id>/rollback")
def rollback(plugin_id: str):
    guard = require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    version = data.get("version")

    if not version:
        return bad_request(
            "version is required",
            code="validation_error",
            path="version"
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = RollbackPluginVersionUseCase(uow)
            result = uc.execute(plugin_id, version)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# UNREGISTER
# ==========================================================

@admin_plugins_bp.delete("/<plugin_id>")
def unregister(plugin_id: str):
    guard = require_admin()
    if guard:
        return guard

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = UnregisterPluginUseCase(uow)
            result = uc.execute(plugin_id)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return bad_request(str(e))


@admin_plugins_bp.post("/<plugin_id>/active")
def set_plugin_active(plugin_id: str):
    guard = require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    active = bool(data.get("active", True))

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = SetPluginActiveUseCase(uow)
            result = uc.execute(plugin_id, active)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return bad_request(str(e))
    

@admin_plugins_bp.post("/bulk-activate")
def bulk_activate_plugins():
    guard = require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    active = bool(data.get("active", True))

    if not isinstance(ids, list):
        return bad_request(
            "ids must be a list",
            code="validation_error",
            path="ids"
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = BulkSetPluginsActiveUseCase(uow)
            result = uc.execute(ids, active)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True, "updated": result.updated}), 200

    except Exception as e:
        return bad_request(str(e))


@admin_plugins_bp.post("/bulk-unregister")
def bulk_unregister():
    guard = require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])

    if not isinstance(ids, list):
        return bad_request(
            "ids must be a list",
            code="validation_error",
            path="ids"
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = BulkUnregisterPluginsUseCase(uow)
            result = uc.execute(ids)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True, "deleted": result.deleted}), 200

    except Exception as e:
        return bad_request(str(e))