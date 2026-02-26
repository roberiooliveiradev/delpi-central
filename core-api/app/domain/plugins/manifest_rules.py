# app/domain/plugins/manifest_rules.py

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set


# ============================================================
# Regex & Constants
# ============================================================

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PLUGIN_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PERMISSION_CODE_RE = re.compile(
    r"^[a-z][a-z0-9-]*\.[a-z0-9-]+(?:\.[a-z0-9-]+)*$"
)
PATH_RE = re.compile(r"^/[-a-z0-9/]*$")


# ============================================================
# Error Model
# ============================================================

@dataclass(frozen=True)
class ManifestError:
    code: str
    message: str
    path: str  # JSONPath simplificado


# ============================================================
# Main Validator
# ============================================================

def validate_manifest_rules(manifest: Dict[str, Any]) -> List[ManifestError]:
    """
    Regras de negócio além do JSON Schema.
    Schema valida estrutura/tipos; aqui validamos coerência semântica.
    """

    errors: List[ManifestError] = []

    plugin_id = str(manifest.get("id") or "").strip()
    version = str(manifest.get("version") or "").strip()
    base_path = str(manifest.get("basePath") or "").strip()
    plugin_type = str(manifest.get("type") or "").strip()

    perms = manifest.get("permissions") or []
    routes = manifest.get("routes") or []
    backend = manifest.get("backend")

    # ========================================================
    # Core Fields
    # ========================================================

    if not PLUGIN_ID_RE.match(plugin_id):
        errors.append(
            ManifestError(
                code="invalid_plugin_id",
                message="Campo 'id' deve ser lowercase, sem espaços, usando hífen quando necessário (ex: 'crm', 'gpt-api').",
                path="$.id",
            )
        )

    if not SEMVER_RE.match(version):
        errors.append(
            ManifestError(
                code="invalid_version",
                message="Campo 'version' deve seguir SemVer MAJOR.MINOR.PATCH (ex: 2.1.0).",
                path="$.version",
            )
        )

    if not PATH_RE.match(base_path) or base_path == "/":
        errors.append(
            ManifestError(
                code="invalid_base_path",
                message="Campo 'basePath' deve começar com '/', conter apenas [-a-z0-9/] e não pode ser '/'.",
                path="$.basePath",
            )
        )

    # ========================================================
    # Permissions
    # ========================================================

    seen_perm_codes: Set[str] = set()

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

        if module and plugin_id and module != plugin_id:
            errors.append(
                ManifestError(
                    code="permission_module_mismatch",
                    message=f"permissions[{i}].module ('{module}') deve ser igual ao plugin id ('{plugin_id}').",
                    path=f"$.permissions[{i}].module",
                )
            )

    perm_lookup = {p.get("code") for p in perms if p.get("code")}

    # ========================================================
    # Type-Specific Rules
    # ========================================================

    # --------------------------------------------------------
    # MICROFRONTEND / IFRAME
    # --------------------------------------------------------

    if plugin_type in ("microfrontend", "iframe"):

        # entry obrigatório semanticamente
        entry = str(manifest.get("entry") or "").strip()
        if not entry:
            errors.append(
                ManifestError(
                    code="entry_required",
                    message=f"'entry' é obrigatório para plugins do tipo '{plugin_type}'.",
                    path="$.entry",
                )
            )

        # routes obrigatórias
        if not routes:
            errors.append(
                ManifestError(
                    code="routes_required",
                    message=f"Plugins do tipo '{plugin_type}' devem declarar ao menos uma route.",
                    path="$.routes",
                )
            )

        seen_routes: Set[str] = set()

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

    # --------------------------------------------------------
    # BACKEND-ONLY
    # --------------------------------------------------------

    if plugin_type == "backend-only":

        # routes não permitidas
        if routes:
            errors.append(
                ManifestError(
                    code="backend_only_cannot_have_routes",
                    message="Plugins backend-only não podem declarar routes.",
                    path="$.routes",
                )
            )

        # entry não permitido
        if manifest.get("entry") not in (None, "",):
            errors.append(
                ManifestError(
                    code="backend_only_entry_not_allowed",
                    message="Plugins backend-only não devem definir 'entry'.",
                    path="$.entry",
                )
            )

        # backend obrigatório
        if backend is None:
            errors.append(
                ManifestError(
                    code="backend_required",
                    message="Plugins backend-only devem declarar objeto 'backend'.",
                    path="$.backend",
                )
            )
        else:
            backend = backend or {}

            # required deve ser True
            if backend.get("required") is not True:
                errors.append(
                    ManifestError(
                        code="backend_required_must_be_true",
                        message="Para plugins backend-only, backend.required deve ser true.",
                        path="$.backend.required",
                    )
                )

            # JWT obrigatório se validateJwt=true
            if backend.get("validateJwt") is True:
                if not str(backend.get("issuer") or "").strip():
                    errors.append(
                        ManifestError(
                            code="backend_missing_issuer",
                            message="backend.issuer é obrigatório quando validateJwt=true.",
                            path="$.backend.issuer",
                        )
                    )
                if not str(backend.get("audience") or "").strip():
                    errors.append(
                        ManifestError(
                            code="backend_missing_audience",
                            message="backend.audience é obrigatório quando validateJwt=true.",
                            path="$.backend.audience",
                        )
                    )

        # recomendação forte: permission access
        if plugin_id and f"{plugin_id}.access" not in perm_lookup:
            errors.append(
                ManifestError(
                    code="missing_access_permission",
                    message=f"Recomendado declarar permission '{plugin_id}.access' para plugins backend-only.",
                    path="$.permissions",
                )
            )

    return errors