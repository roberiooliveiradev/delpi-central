# app/domain/plugins/manifest_rules.py

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")  # MAJOR.MINOR.PATCH
PLUGIN_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")  # lowercase, hífen, sem espaços
PERMISSION_CODE_RE = re.compile(r"^[a-z][a-z0-9]*\.[a-z0-9]+(?:\.[a-z0-9]+)*$")  # module.resource.action...
PATH_RE = re.compile(r"^/[-a-z0-9/]*$")

@dataclass(frozen=True)
class ManifestError:
    code: str
    message: str
    path: str  # JSONPath simplificado, ex: "$.routes[0].path"

def validate_manifest_rules(manifest: Dict[str, Any]) -> List[ManifestError]:
    errors: List[ManifestError] = []

    plugin_id = manifest.get("id", "")
    version = manifest.get("version", "")
    base_path = manifest.get("basePath", "")

    # id: único e padrão (unicidade vs DB é na Fase do Register; aqui validamos formato)
    if not PLUGIN_ID_RE.match(plugin_id):
        errors.append(ManifestError(
            code="invalid_plugin_id",
            message="Campo 'id' deve ser lowercase, sem espaços, usando hífen quando necessário (ex: 'crm', 'gpt-api').",
            path="$.id",
        ))

    # version: SemVer
    if not SEMVER_RE.match(version):
        errors.append(ManifestError(
            code="invalid_version",
            message="Campo 'version' deve seguir SemVer MAJOR.MINOR.PATCH (ex: 2.1.0).",
            path="$.version",
        ))

    # basePath: padrão e consistência
    if not PATH_RE.match(base_path) or base_path == "/":
        errors.append(ManifestError(
            code="invalid_base_path",
            message="Campo 'basePath' deve começar com '/', conter apenas [-a-z0-9/] e não pode ser '/'.",
            path="$.basePath",
        ))

    # permissions: formato + unicidade interna
    seen_perm_codes: Set[str] = set()
    for i, perm in enumerate(manifest.get("permissions", []) or []):
        code = (perm or {}).get("code", "")
        module = (perm or {}).get("module", "")
        name = (perm or {}).get("name", "")

        if not PERMISSION_CODE_RE.match(code):
            errors.append(ManifestError(
                code="invalid_permission_code",
                message="Permission code deve seguir padrão 'module.resource.action' (ex: crm.leads.read).",
                path=f"$.permissions[{i}].code",
            ))

        if code in seen_perm_codes:
            errors.append(ManifestError(
                code="duplicate_permission_code_in_manifest",
                message=f"Permission code duplicada no manifesto: '{code}'.",
                path=f"$.permissions[{i}].code",
            ))
        seen_perm_codes.add(code)

        # regra opcional forte: module do permission deve bater com id do plugin
        if module and plugin_id and module != plugin_id:
            errors.append(ManifestError(
                code="permission_module_mismatch",
                message=f"permissions[{i}].module ('{module}') deve ser igual ao plugin id ('{plugin_id}').",
                path=f"$.permissions[{i}].module",
            ))
            
        if not name:
            errors.append(ManifestError(
                code="permission_name_required",
                message="Permission name é obrigatório.",
                path=f"$.permissions[{i}].name",
            ))
    # routes: path inicia com basePath + permission referencia existente
    perm_lookup = set((p or {}).get("code") for p in (manifest.get("permissions", []) or []) if (p or {}).get("code"))
    seen_routes: Set[str] = set()

    for i, route in enumerate(manifest.get("routes", []) or []):
        path = (route or {}).get("path", "")
        permission = (route or {}).get("permission", "")

        if not PATH_RE.match(path):
            errors.append(ManifestError(
                code="invalid_route_path",
                message="Route path deve começar com '/' e conter apenas [-a-z0-9/].",
                path=f"$.routes[{i}].path",
            ))

        if base_path and not path.startswith(base_path):
            errors.append(ManifestError(
                code="route_outside_base_path",
                message=f"Route path '{path}' deve iniciar com basePath '{base_path}'.",
                path=f"$.routes[{i}].path",
            ))

        if path in seen_routes:
            errors.append(ManifestError(
                code="duplicate_route_path_in_manifest",
                message=f"Route path duplicada no manifesto: '{path}'.",
                path=f"$.routes[{i}].path",
            ))
        seen_routes.add(path)

        if permission and permission not in perm_lookup:
            errors.append(ManifestError(
                code="route_permission_not_declared",
                message=f"Route permission '{permission}' não existe em permissions[].code.",
                path=f"$.routes[{i}].permission",
            ))

    # type/backend constraints (mínimo)
    plugin_type = manifest.get("type")
    backend = manifest.get("backend")
    if backend is not None:
        issuer = (backend or {}).get("issuer", "")
        audience = (backend or {}).get("audience", "")
        if not issuer:
            errors.append(ManifestError("backend_missing_issuer", "backend.issuer é obrigatório quando backend existe.", "$.backend.issuer"))
        if not audience:
            errors.append(ManifestError("backend_missing_audience", "backend.audience é obrigatório quando backend existe.", "$.backend.audience"))

    # backend-only: deve ter pelo menos uma permission de acesso? (recomendado)
    if plugin_type == "backend-only":
        # não obrigatório, mas bem útil para governança:
        if f"{plugin_id}.access" not in perm_lookup:
            errors.append(ManifestError(
                code="missing_access_permission",
                message=f"Recomendado declarar permission '{plugin_id}.access' para plugins backend-only.",
                path="$.permissions",
            ))

    return errors