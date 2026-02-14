# app/application/use_cases/register_plugin_use_case.py

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from app.extensions import db
from app.domain.services.plugin_manifest_validator import validate_manifest_v2
from app.infrastructure.db.models import App, Permission, AppRoute, AppManifest, AuditLog


class PluginRegistrationError(Exception):
    pass


def _semver_tuple(v: str) -> tuple[int, int, int]:
    major, minor, patch = v.split(".")
    return int(major), int(minor), int(patch)


@dataclass(frozen=True)
class RegisterPluginResult:
    app_id: str
    created: bool
    version: str


def register_plugin(manifest: dict, actor_user_id: str | None, ip_address: str | None) -> RegisterPluginResult:
    validate_manifest_v2(manifest)

    plugin_id = manifest["id"]
    new_version = manifest["version"]

    # checksum para integridade/auditoria
    checksum = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()

    # 1) Colisão de permission codes
    incoming_codes = [p["code"] for p in manifest["permissions"]]
    existing_perm = Permission.query.filter(Permission.code.in_(incoming_codes)).all()
    if existing_perm:
        codes = [p.code for p in existing_perm]
        raise PluginRegistrationError(f"Colisão de permissions: {codes}")

    # 2) Colisão de rotas (path global)
    incoming_paths = [r["path"] for r in manifest["routes"]]
    existing_routes = AppRoute.query.filter(AppRoute.path.in_(incoming_paths)).all()
    if existing_routes:
        paths = [r.path for r in existing_routes]
        raise PluginRegistrationError(f"Colisão de rotas: {paths}")

    # 3) Política de upgrade/versionamento
    app = App.query.get(plugin_id)
    created = False

    if app:
        old_version = app.version or "0.0.0"
        old_t = _semver_tuple(old_version)
        new_t = _semver_tuple(new_version)

        if new_t < old_t:
            raise PluginRegistrationError(f"Downgrade bloqueado: atual={old_version}, novo={new_version}")

        if new_t[0] > old_t[0]:
            # MAJOR upgrade: bloquear por enquanto (política do roadmap)
            raise PluginRegistrationError(
                f"Upgrade MAJOR bloqueado: atual={old_version}, novo={new_version}. Exige aprovação manual."
            )
    else:
        created = True
        app = App(
            id=plugin_id,
            name=manifest["name"],
            description=manifest.get("description"),
            base_path=manifest["basePath"],
            icon=manifest.get("icon"),
            type=manifest["type"],
            version=new_version,
            active=True,
        )
        db.session.add(app)

    # transação única (cria tudo ou nada)
    try:
        # Atualiza app em upgrades MINOR/PATCH
        app.name = manifest["name"]
        app.description = manifest.get("description")
        app.base_path = manifest["basePath"]
        app.icon = manifest.get("icon")
        app.type = manifest["type"]
        app.version = new_version
        app.active = True

        # 4) Criar permissões
        code_to_permission_id: dict[str, str] = {}
        for p in manifest["permissions"]:
            perm = Permission(code=p["code"], description=p["description"], module=p.get("module"))
            db.session.add(perm)
            db.session.flush()  # garante perm.id
            code_to_permission_id[p["code"]] = perm.id

        # 5) Criar rotas
        for r in manifest["routes"]:
            perm_code = r["permission"]
            perm_id = code_to_permission_id.get(perm_code)
            if not perm_id:
                raise PluginRegistrationError(f"Rota '{r['path']}' referencia permission inexistente '{perm_code}'")

            route = AppRoute(
                app_id=plugin_id,
                path=r["path"],
                label=r.get("label"),
                icon=r.get("icon"),
                permission_id=perm_id,
                show_in_menu=bool(r.get("showInMenu", True)),
                order_index=int(r.get("order", 0) or 0),
                active=True,
            )
            db.session.add(route)

        # 6) Salvar manifesto
        m = AppManifest.query.get(plugin_id)
        if not m:
            m = AppManifest(app_id=plugin_id, manifest=manifest, checksum=checksum)
            db.session.add(m)
        else:
            m.manifest = manifest
            m.checksum = checksum

        # 7) Auditoria
        audit = AuditLog(
            user_id=actor_user_id,
            action="plugin.register",
            resource_type="app",
            resource_id=plugin_id,
            metadata={
                "version": new_version,
                "checksum": checksum,
                "routes": incoming_paths,
                "permissions": incoming_codes,
                "schemaVersion": manifest.get("schemaVersion"),
            },
            ip_address=ip_address,
        )
        db.session.add(audit)

        db.session.commit()
        return RegisterPluginResult(app_id=plugin_id, created=created, version=new_version)

    except Exception:
        db.session.rollback()
        raise
