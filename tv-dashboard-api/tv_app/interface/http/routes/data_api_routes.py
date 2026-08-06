from __future__ import annotations

import logging
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
from tv_app.core.security import TV_MANAGE, TV_READ, TV_WRITE, assert_permission
from tv_app.interface.http.auth_http import resolve_user
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access

logger = logging.getLogger(__name__)

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
    # Estado live do editor (dataDefaults) — prevalece sobre o valor persistido.
    playlistDefaults: dict[str, Any] | None = None
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


class SuggestDataRoutesBody(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class BuilderTurnBody(BaseModel):
    message: str | None = None
    action: dict[str, Any] | None = None


@router.post("/builder/sessions")
def create_data_builder_session(request: Request):
    """Inicia sessão do assistente conversacional de dados."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.data.tv_data_builder_service import TvDataBuilderService

    session = TvDataBuilderService(_catalog).create_session()
    return ok(session, message="Sessão do assistente de dados iniciada.")


@router.get("/builder/sessions/{session_id}")
def get_data_builder_session(request: Request, session_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.data.tv_data_builder_service import TvDataBuilderService

    session = TvDataBuilderService(_catalog).get_session(session_id)
    if not session:
        return fail("Sessão do assistente não encontrada ou expirada.", 404)
    return ok(session)


@router.post("/builder/sessions/{session_id}/turn")
def data_builder_turn(request: Request, session_id: str, body: BuilderTurnBody):
    """Deprecated: turno NL do Builder. Preferir Copilot + POST /data/copilot/suggest-ops;
    materialize tipado via POST .../to-copilot-ops (mesmo catálogo)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not (body.message and str(body.message).strip()) and not body.action:
        return fail("Informe message ou action.", 400)
    from tv_app.application.services.data.tv_data_builder_service import TvDataBuilderService

    session = TvDataBuilderService(_catalog).turn(
        session_id,
        message=body.message,
        action=body.action,
        authorization=request.headers.get("Authorization"),
        user=user,
    )
    if not session:
        return fail("Sessão do assistente não encontrada ou expirada.", 404)
    return ok(session, message="Turno aplicado.")


@router.post("/builder/sessions/{session_id}/materialize")
def data_builder_materialize(request: Request, session_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.data.tv_data_builder_service import TvDataBuilderService

    result = TvDataBuilderService(_catalog).materialize(session_id)
    if result is None:
        return fail("Sessão do assistente não encontrada ou expirada.", 404)
    if not result.get("ok"):
        return fail(str(result.get("message") or "Rascunho vazio."), 400, data=result)
    return ok(result, message="Modelo pronto para o slide.")


@router.post("/builder/sessions/{session_id}/to-copilot-ops")
def data_builder_to_copilot_ops(request: Request, session_id: str):
    """Fachada A0: rascunho do builder → ops TvCopilotPatch (mesmo materialize, sem segundo pipeline)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.data.tv_copilot_builder_facade import (
        materialize_session_to_copilot_ops,
    )

    result = materialize_session_to_copilot_ops(session_id, catalog=_catalog)
    if result.get("message") == "session_not_found":
        return fail("Sessão do assistente não encontrada ou expirada.", 404)
    if not result.get("ok"):
        return fail(str(result.get("message") or "Rascunho vazio."), 400, data=result)
    return ok(result, message="Ops do copiloto geradas a partir do rascunho.")


@router.post("/builder/sessions/{session_id}/preview")
def data_builder_preview(request: Request, session_id: str):
    """Força prévia tabular do rascunho (sob demanda)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.data.tv_data_builder_service import TvDataBuilderService

    result = TvDataBuilderService(_catalog).preview(
        session_id,
        authorization=request.headers.get("Authorization"),
        user=user,
    )
    if result is None:
        return fail("Sessão do assistente não encontrada ou expirada.", 404)
    if not result.get("ok"):
        return fail(str(result.get("message") or "Prévia indisponível."), 400, data=result)
    return ok(result, message="Prévia atualizada.")


@router.get("/routes")
def list_data_routes_v2(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items = [_validation.enrich_route_for_api(route) for route in _catalog.list_routes()]
    return ok({"items": items, "total": len(items)})


@router.post("/routes/suggest")
def suggest_data_routes(request: Request, body: SuggestDataRoutesBody):
    """NL → fontes do catálogo TV (ranking via chat base; intersect allowlist)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)

    from tv_app.application.services.data.tv_data_route_suggest_service import (
        TvDataRouteSuggestService,
    )

    result = TvDataRouteSuggestService(_catalog).suggest(
        query=body.query,
        limit=body.limit,
    )
    suggestions = [
        {
            **_validation.enrich_route_for_api(item),
            "reason": item.get("reason") or "",
            "score": item.get("score"),
        }
        for item in (result.get("suggestions") or [])
    ]
    return ok(
        {
            "query": result.get("query") or body.query,
            "suggestions": suggestions,
            "total": len(suggestions),
            "degraded": bool(result.get("degraded")),
        },
        message="Sugestões de fontes.",
    )


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
    """Rotas GET da api-delpi — curadoria (candidates) vs allowlist já sincronizada."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items = _openapi.list_candidates(include_allowlisted=include_catalog)
    return ok({"items": items, "total": len(items), "httpMethod": "GET"})


@router.post("/openapi/sync")
def sync_openapi_catalog(request: Request):
    """Reimporta OpenAPI live da api-delpi e regenera tv_data_routes.json."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.tv_openapi_catalog_sync_service import (
        TvOpenApiCatalogSyncService,
    )

    try:
        report = TvOpenApiCatalogSyncService().sync_from_live_api()
    except Exception as exc:  # noqa: BLE001
        return fail(f"Falha ao sincronizar OpenAPI: {exc}", 502)
    return ok(report)


@router.post("/preview-block")
def preview_data_block_v2(request: Request, body: PreviewDataBlockBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)

    # Sentinels do editor de template (ex.: "template-library") não são UUID —
    # preview segue sem dataDefaults da programação (mesmo efeito de omitir playlistId).
    # Body.playlistDefaults (estado live do editor) prevalece sobre o valor só no banco.
    playlist_defaults: dict[str, Any] | None = None
    playlist_uuid: UUID | None = None
    if body.playlistId:
        try:
            playlist_uuid = UUID(body.playlistId)
        except ValueError:
            playlist_uuid = None
        if playlist_uuid is not None:
            guarded = require_playlist_access(request, playlist_uuid, need="read")
            if is_access_error(guarded):
                return guarded
            _, access = guarded
            if isinstance(body.playlistDefaults, dict):
                playlist_defaults = body.playlistDefaults
            else:
                playlist = access.playlist or {}
                defaults = playlist.get("dataDefaults")
                playlist_defaults = defaults if isinstance(defaults, dict) else {}
    elif isinstance(body.playlistDefaults, dict):
        playlist_defaults = body.playlistDefaults

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


class CopilotPatchBody(BaseModel):
    """Envelope TvCopilotPatchV1."""

    target: dict[str, Any] = Field(default_factory=dict)
    ops: list[dict[str, Any]] = Field(default_factory=list)
    includeFingerprint: bool = True


class SuggestOpsBody(BaseModel):
    message: str = ""
    hostContext: dict[str, Any] = Field(default_factory=dict)


def _copilot_actor(user: Any) -> str | None:
    from tv_app.application.services.playlist_access_service import PlaylistAccessService

    return PlaylistAccessService.actor_id(user)


def _copilot_unexpected_failure(kind: str, ops: list[dict[str, Any]] | None):
    """Falha não prevista no patch: log com as ops + motivo factual ao chamador.

    Sem isso o copiloto da IA recebia 500 com «Internal server error» e o usuário
    via só «não foi possível aplicar», sem saber qual operação quebrou.
    """
    from tv_app.application.services.data.tv_copilot_content_service import (
        TvCopilotContentService,
    )

    op_names = [
        str(op.get("op") or "?") for op in (ops or []) if isinstance(op, dict)
    ] or ["?"]
    logger.exception("copilot_patch_unexpected_error kind=%s ops=%s", kind, op_names)
    return fail(
        TvCopilotContentService.message("patchUnexpectedError", ops=", ".join(op_names)),
        500,
    )


@router.get("/copilot/capabilities")
def copilot_capabilities(request: Request):
    """Catálogo versionado de ops tipadas (fonte de verdade para a AI / host)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.data.tv_copilot_content_service import (
        TvCopilotContentService,
    )

    return ok(TvCopilotContentService.capability_catalog_document())


@router.post("/copilot/suggest-ops")
def copilot_suggest_ops(request: Request, body: SuggestOpsBody):
    """NL + hostContext → ops tipadas (determinístico no BFF; sem LLM)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.data.tv_copilot_command_planner_service import (
        TvCopilotCommandPlannerService,
    )

    authorization = request.headers.get("authorization") or request.headers.get(
        "Authorization"
    )
    plan = TvCopilotCommandPlannerService.plan(
        message=body.message,
        host_context=body.hostContext,
        authorization=authorization,
        user=user,
    )
    result = TvCopilotCommandPlannerService.to_suggest_payload(plan)
    return ok(result, message=str(result.get("reason") or "Sugestão gerada."))


@router.post("/copilot/preview-patch")
def copilot_preview_patch(request: Request, body: CopilotPatchBody):
    """Dry-run do patch tipado (sem persistir; opcional fingerprint via SlideDataResolution)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)

    playlist_id = str((body.target or {}).get("playlistId") or "").strip()
    if playlist_id:
        try:
            guarded = require_playlist_access(request, UUID(playlist_id), need="edit")
        except ValueError:
            return fail("playlistId inválido.", 422)
        if is_access_error(guarded):
            return guarded

    from tv_app.application.services.data.tv_copilot_patch_service import (
        TvCopilotPatchError,
        TvCopilotPatchService,
    )

    try:
        result = TvCopilotPatchService(catalog=_catalog).preview(
            {"target": body.target, "ops": body.ops},
            user=user,
            authorization=request.headers.get("Authorization"),
            include_fingerprint=bool(body.includeFingerprint),
        )
    except TvCopilotPatchError as exc:
        return fail(str(exc), 422)
    except Exception:
        return _copilot_unexpected_failure("preview", body.ops)
    return ok(result, message=str(result.get("message") or "Prévia gerada."))


@router.post("/copilot/apply-patch")
def copilot_apply_patch(request: Request, body: CopilotPatchBody):
    """Aplica patch tipado: persiste native_config / playlist + notify (cache + WS)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)

    actor = _copilot_actor(user)
    if not actor:
        return fail("Usuário não identificado.", 401)

    playlist_id = str((body.target or {}).get("playlistId") or "").strip()
    ops = body.ops or []
    creating_playlist = any(
        isinstance(op, dict) and str(op.get("op") or "") == "create_playlist" for op in ops
    )
    if playlist_id:
        try:
            guarded = require_playlist_access(request, UUID(playlist_id), need="edit")
        except ValueError:
            return fail("playlistId inválido.", 422)
        if is_access_error(guarded):
            return guarded
    elif not creating_playlist:
        return fail("Informe playlistId no target.", 422)

    from tv_app.application.services.data.tv_copilot_patch_service import (
        TvCopilotPatchError,
        TvCopilotPatchService,
    )

    try:
        result = TvCopilotPatchService(catalog=_catalog).apply(
            {"target": body.target, "ops": body.ops},
            user=user,
            authorization=request.headers.get("Authorization"),
            actor_user_id=actor,
        )
    except TvCopilotPatchError as exc:
        return fail(str(exc), 422)
    except Exception:
        return _copilot_unexpected_failure("apply", body.ops)
    return ok(result, message=str(result.get("message") or "Patch aplicado."))


@router.get("/copilot/telemetry")
def copilot_telemetry(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    from tv_app.application.services.data.tv_copilot_telemetry import (
        copilot_telemetry_snapshot,
    )

    return ok(copilot_telemetry_snapshot())
