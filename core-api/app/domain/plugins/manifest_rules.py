# app/domain/plugins/manifest_rules.py

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set

# SemVer básico (MAJOR.MINOR.PATCH)
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

# id do plugin: lowercase, hífen, sem espaços
PLUGIN_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# permission code: module.resource.action...
PERMISSION_CODE_RE = re.compile(r"^[a-z][a-z0-9]*\.[a-z0-9]+(?:\.[a-z0-9]+)*$")

# paths do app: /crm, /crm/leads (somente [-a-z0-9/])
PATH_RE = re.compile(r"^/[-a-z0-9/]*$")


@dataclass(frozen=True)
class ManifestError:
    code: str
    message: str
    path: str  # JSONPath simplificado (ex: "$.routes[0].path")


def validate_manifest_rules(manifest: Dict[str, Any]) -> List[ManifestError]:
    """
    Regras de negócio além do JSON Schema.
    Importante: schema valida tipos/required; aqui validamos coerência.
    """
    errors: List[ManifestError] = []

    plugin_id = str(manifest.get("id") or "").strip()
    version = str(manifest.get("version") or "").strip()
    base_path = str(manifest.get("basePath") or "").strip()

    # id
    if not PLUGIN_ID_RE.match(plugin_id):
        errors.append(
            ManifestError(
                code="invalid_plugin_id",
                message="Campo 'id' deve ser lowercase, sem espaços, usando hífen quando necessário (ex: 'crm', 'gpt-api').",
                path="$.id",
            )
        )

    # version
    if not SEMVER_RE.match(version):
        errors.append(
            ManifestError(
                code="invalid_version",
                message="Campo 'version' deve seguir SemVer MAJOR.MINOR.PATCH (ex: 2.1.0).",
                path="$.version",
            )
        )

    # basePath
    if not PATH_RE.match(base_path) or base_path == "/":
        errors.append(
            ManifestError(
                code="invalid_base_path",
                message="Campo 'basePath' deve começar com '/', conter apenas [-a-z0-9/] e não pode ser '/'.",
                path="$.basePath",
            )
        )

    # permissions: formato + unicidade + module coerente + name obrigatório
    seen_perm_codes: Set[str] = set()
    perms = manifest.get("permissions") or []
    for i, perm in enumerate(perms):
        perm = perm or {}
        code = str(perm.get("code") or "").strip()
        module = str(perm.get("module") or "").strip()
        name = str(perm.get("name") or "").strip()

        if not PERMISSION_CODE_RE.match(code):
            errors.append(
                ManifestError(
                    code="invalid_permission_code",
                    message="Permission code deve seguir padrão 'module.resource.action' (ex: crm.leads.read).",
                    path=f"$.permissions[{i}].code",
                )
            )

        if code and code in seen_perm_codes:
            errors.append(
                ManifestError(
                    code="duplicate_permission_code_in_manifest",
                    message=f"Permission code duplicada no manifesto: '{code}'.",
                    path=f"$.permissions[{i}].code",
                )
            )
        if code:
            seen_perm_codes.add(code)

        if not name:
            errors.append(
                ManifestError(
                    code="permission_name_required",
                    message="Permission name é obrigatório.",
                    path=f"$.permissions[{i}].name",
                )
            )

        # regra forte: module deve bater com o id do plugin
        if module and plugin_id and module != plugin_id:
            errors.append(
                ManifestError(
                    code="permission_module_mismatch",
                    message=f"permissions[{i}].module ('{module}') deve ser igual ao plugin id ('{plugin_id}').",
                    path=f"$.permissions[{i}].module",
                )
            )

    # routes: path dentro do basePath + unicidade + permission existente
    perm_lookup = {
        str((p or {}).get("code") or "").strip()
        for p in perms
        if str((p or {}).get("code") or "").strip()
    }

    seen_routes: Set[str] = set()
    routes = manifest.get("routes") or []
    for i, route in enumerate(routes):
        route = route or {}
        path = str(route.get("path") or "").strip()
        permission = str(route.get("permission") or "").strip()

        if not PATH_RE.match(path):
            errors.append(
                ManifestError(
                    code="invalid_route_path",
                    message="Route path deve começar com '/' e conter apenas [-a-z0-9/].",
                    path=f"$.routes[{i}].path",
                )
            )

        if base_path and path and not path.startswith(base_path):
            errors.append(
                ManifestError(
                    code="route_outside_base_path",
                    message=f"Route path '{path}' deve iniciar com basePath '{base_path}'.",
                    path=f"$.routes[{i}].path",
                )
            )

        if path and path in seen_routes:
            errors.append(
                ManifestError(
                    code="duplicate_route_path_in_manifest",
                    message=f"Route path duplicada no manifesto: '{path}'.",
                    path=f"$.routes[{i}].path",
                )
            )
        if path:
            seen_routes.add(path)

        if permission and permission not in perm_lookup:
            errors.append(
                ManifestError(
                    code="route_permission_not_declared",
                    message=f"Route permission '{permission}' não existe em permissions[].code.",
                    path=f"$.routes[{i}].permission",
                )
            )

    # backend constraints (se backend existe, issuer/audience obrigatórios)
    backend = manifest.get("backend")
    if backend is not None:
        backend = backend or {}
        issuer = str(backend.get("issuer") or "").strip()
        audience = str(backend.get("audience") or "").strip()
        required = backend.get("required", None)

        if required is True:
            if not issuer:
                errors.append(
                    ManifestError(
                        code="backend_missing_issuer",
                        message="backend.issuer é obrigatório quando backend.required=true.",
                        path="$.backend.issuer",
                    )
                )
            if not audience:
                errors.append(
                    ManifestError(
                        code="backend_missing_audience",
                        message="backend.audience é obrigatório quando backend.required=true.",
                        path="$.backend.audience",
                    )
                )

    # recomendação para backend-only: ter {id}.access
    plugin_type = str(manifest.get("type") or "").strip()
    if plugin_type == "backend-only" and plugin_id:
        if f"{plugin_id}.access" not in perm_lookup:
            errors.append(
                ManifestError(
                    code="missing_access_permission",
                    message=f"Recomendado declarar permission '{plugin_id}.access' para plugins backend-only.",
                    path="$.permissions",
                )
            )

    return errors