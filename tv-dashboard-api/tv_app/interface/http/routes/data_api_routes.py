from __future__ import annotations

from typing import Any

from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tv_app.application.services.data.tv_data_config_validation_service import TvDataConfigValidationService
from tv_app.application.services.data.m_query.m_compiler import (
    MCompileRequest,
    MQueryCompiler,
)
from tv_app.application.services.data.m_query.m_function_registry import get_function_registry
from tv_app.application.services.data.m_query.m_mutation_service import (
    MMutationError,
    MQueryMutationService,
)
from tv_app.application.services.tv_dashboard_content_service import m_query_setting
from tv_app.application.services.data.tv_data_openapi_catalog_service import TvDataOpenApiCatalogService
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_MANAGE, TV_READ, assert_permission
from tv_app.interface.http.auth_http import resolve_user
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access

router = APIRouter(prefix="/data", tags=["TV Dados"])
_catalog = TvDataRouteCatalogService()
_validation = TvDataConfigValidationService(_catalog)
_preview = TvDataPreviewService(_catalog)
_openapi = TvDataOpenApiCatalogService(_catalog)
_m_compiler = MQueryCompiler()
_m_mutation = MQueryMutationService(_m_compiler)

class PreviewOptionsBody(BaseModel):
    maxRows: int | None = Field(default=None, ge=1)
    includeColumnProfile: bool = False
    deadlineMs: int | None = Field(default=None, ge=1)


class PreviewDataBlockBody(BaseModel):
    block: dict[str, Any]
    nativeConfig: dict[str, Any] = Field(default_factory=dict)
    playlistId: str | None = None
    forceRefresh: bool = False
    targetStepName: str | None = None
    previewOptions: PreviewOptionsBody = Field(default_factory=PreviewOptionsBody)


class ValidateDataConfigBody(BaseModel):
    nativeConfig: dict[str, Any] = Field(default_factory=dict)


class MSourceColumnBody(BaseModel):
    key: str
    type: str = "any"
    nullable: bool = True


class MQueryBindingBody(BaseModel):
    name: str
    sourceId: str


class MCompileBody(BaseModel):
    profile: str = "m-delpi-v1"
    script: str
    sourceSchema: list[MSourceColumnBody] = Field(default_factory=list)
    queryBindings: list[MQueryBindingBody] = Field(default_factory=list)
    targetStepName: str | None = None
    culture: str | None = None


class MMutationBody(MCompileBody):
    action: dict[str, Any]


def _model_dict(model: BaseModel) -> dict[str, Any]:
    dump = getattr(model, "model_dump", None)
    return dump() if callable(dump) else model.dict()


@router.post("/m/compile")
def compile_m_query(request: Request, body: MCompileBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    result = _m_compiler.compile(
        MCompileRequest(
            profile=body.profile,
            script=body.script,
            source_schema=tuple(_model_dict(item) for item in body.sourceSchema),
            query_bindings=tuple(_model_dict(item) for item in body.queryBindings),
            target_step_name=body.targetStepName,
            culture=body.culture or str(m_query_setting("defaultCulture", "pt-BR")),
        )
    )
    message = "Consulta M válida." if result.valid else "Consulta M contém diagnósticos."
    payload = result.to_dict()
    if not bool(m_query_setting("explainPlanEnabled", False)):
        payload["explainPlan"] = None
    return ok(payload, message=message)


@router.post("/m/explain")
def explain_m_query(request: Request, body: MCompileBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not bool(m_query_setting("explainPlanEnabled", False)):
        return fail("Explain plan M não está habilitado.", 404)
    result = _m_compiler.compile(
        MCompileRequest(
            profile=body.profile,
            script=body.script,
            source_schema=tuple(_model_dict(item) for item in body.sourceSchema),
            query_bindings=tuple(_model_dict(item) for item in body.queryBindings),
            target_step_name=body.targetStepName,
            culture=body.culture or str(m_query_setting("defaultCulture", "pt-BR")),
        )
    )
    return ok(
        {
            "profile": result.profile,
            "scriptHash": result.script_hash,
            "valid": result.valid,
            "diagnostics": [item.to_dict() for item in result.diagnostics],
            "explainPlan": dict(result.explain_plan or {}),
            "compileMetrics": {
                "durationMs": result.compile_ms,
                "cache": result.compile_cache,
            },
        }
    )


@router.get("/m/functions")
def list_m_functions(request: Request, profile: str = "m-delpi-v1"):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    registry = get_function_registry()
    if profile != registry.profile:
        return fail("Profile M não suportado.", 422)
    items = registry.catalog()
    return ok(
        {
            "profile": registry.profile,
            "registryVersion": registry.version,
            "items": items,
            "total": len(items),
        }
    )


@router.get("/m/capabilities")
def get_m_capabilities(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(
        {
            "enabled": bool(m_query_setting("enabled", False)),
            "writeV2Enabled": bool(m_query_setting("writeV2Enabled", False)),
            "advancedEditorEnabled": bool(
                m_query_setting("advancedEditorEnabled", False)
            ),
            "profilingEnabled": bool(m_query_setting("profilingEnabled", False)),
            "explainPlanEnabled": bool(
                m_query_setting("explainPlanEnabled", False)
            ),
            "compileCacheEnabled": bool(
                m_query_setting("compileCacheEnabled", False)
            ),
            "previewCacheEnabled": bool(
                m_query_setting("previewCacheEnabled", False)
            ),
            "phase7TelemetryEnabled": bool(
                m_query_setting("phase7TelemetryEnabled", False)
            ),
            "limits": {
                "previewRows": int(m_query_setting("maxPreviewRows", 200)),
                "profileSampleRows": int(
                    m_query_setting("profileSampleRows", 500)
                ),
                "profileTimeoutMs": int(m_query_setting("profileTimeoutMs", 750)),
                "previewDeadlineMaxMs": int(
                    m_query_setting("previewDeadlineMaxMs", 3000)
                ),
            },
            "profile": str(m_query_setting("profile", "m-delpi-v1")),
        }
    )


@router.post("/m/mutate")
def mutate_m_query(request: Request, body: MMutationBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    compile_request = MCompileRequest(
        profile=body.profile,
        script=body.script,
        source_schema=tuple(_model_dict(item) for item in body.sourceSchema),
        query_bindings=tuple(_model_dict(item) for item in body.queryBindings),
        target_step_name=body.targetStepName,
        culture=body.culture or str(m_query_setting("defaultCulture", "pt-BR")),
    )
    try:
        result = _m_mutation.mutate(compile_request, body.action)
    except (MMutationError, ValueError) as exc:
        return fail(str(exc), 422)
    if not result.valid:
        return ok(result.to_dict(), message="Mutação gerou diagnósticos.")
    return ok(result.to_dict(), message="Consulta M atualizada.")


@router.get("/routes")
def list_data_routes_v2(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items = [_validation.enrich_route_for_api(route) for route in _catalog.list_routes()]
    return ok({"items": items, "total": len(items)})


@router.get("/routes/{operation_id}")
def get_data_route(request: Request, operation_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    route = _catalog.get_route(operation_id)
    if not route:
        return fail("Fonte de dados não encontrada no catálogo.", 404)
    return ok(_validation.enrich_route_for_api(route))


@router.get("/openapi/candidates")
def list_openapi_get_candidates(request: Request, include_catalog: bool = False):
    """Rotas GET da api-delpi — curadoria para expandir o catálogo TV (não import automático)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items = _openapi.list_candidates(include_allowlisted=include_catalog)
    return ok({"items": items, "total": len(items), "httpMethod": "GET"})


@router.post("/preview-block")
def preview_data_block_v2(request: Request, body: PreviewDataBlockBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)

    playlist_defaults: dict[str, Any] | None = None
    if body.playlistId:
        try:
            playlist_uuid = UUID(body.playlistId)
        except ValueError:
            return fail("Programação inválida.", 422)
        guarded = require_playlist_access(request, playlist_uuid, need="read")
        if is_access_error(guarded):
            return guarded
        _, access = guarded
        playlist = access.playlist or {}
        defaults = playlist.get("dataDefaults")
        playlist_defaults = defaults if isinstance(defaults, dict) else {}

    auth = request.headers.get("Authorization")
    try:
        cfg = _validation.sanitize(body.nativeConfig)
        block = _preview.preview_block(
            body.block,
            native_config=cfg,
            authorization=auth,
            user=user,
            playlist_defaults=playlist_defaults,
            force_refresh=bool(body.forceRefresh),
            target_step_name=body.targetStepName,
            preview_options=_model_dict(body.previewOptions),
        )
    except ValueError as exc:
        return fail(str(exc), 422)
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), 502)
    resolved = block.get("resolved") if isinstance(block, dict) else None
    payload: dict[str, Any] = {"block": block}
    if isinstance(resolved, dict):
        if isinstance(resolved.get("query"), dict):
            payload["query"] = resolved["query"]
        if isinstance(resolved.get("preview"), dict):
            payload["preview"] = resolved["preview"]
    return ok(payload)


@router.post("/validate-config")
def validate_data_config(request: Request, body: ValidateDataConfigBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    cfg = _validation.sanitize(body.nativeConfig)
    result = _validation.validate(cfg, user=user)
    return ok(result)
