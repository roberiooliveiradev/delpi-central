"""TvPresentationPatchV1 — typed presentation mutation reducer (canonical).

Dry-run builds in-memory state; persistence goes through
``TvPresentationWriteService`` / CRUD.
"""

from __future__ import annotations

import contextvars
import copy
import time
import uuid
from typing import Any
from uuid import UUID

from tv_app.application.services.comunicado_config_validation_service import (
    sanitize_and_hydrate_comunicado_config,
    validate_comunicado_native_config,
)
from tv_app.application.services.data.slide_data_resolution_service import (
    SlideDataResolutionService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)
from tv_app.application.services.data.data_transform_contract import (
    sanitize_data_transform_for_persistence,
)
from tv_app.application.services.data.m_query.m_legacy_adapter import (
    normalize_legacy_transform,
)
from tv_app.application.services.data.tv_data_transform_service import (
    STRUCTURAL_TRANSFORM_OPS,
    normalize_data_transform,
    project_transform_output_columns,
)
from tv_app.application.services.data.presentation_mutation.execution_context import (
    ExecutionContext,
    is_synthetic_id,
    mint_synthetic_id,
)
from tv_app.application.services.data.presentation_mutation.merge import (
    deep_merge_dicts,
    merge_block_patch,
    merge_data_binding,
    merge_native_config_key,
)
from tv_app.application.services.data.presentation_nested_contract import (
    NestedContractError,
    patch_native_keys,
    validate_operation_payload,
)
from tv_app.application.services.data.tv_data_binding_hydrate_service import (
    _KEEP_WITHOUT_SCHEMA,
    _PARAM_KEY_REMAP,
    _remap_param_keys,
)
from tv_app.application.services.tv_date_range_preset_service import (
    merge_period_params_layer,
)
from tv_app.application.services.data.presentation_mutation.plan_compiler import (
    PlanCompileError,
    compile_presentation_plan,
)
from tv_app.application.services.data.presentation_http_command_planner_service import (
    PresentationHttpCommandPlannerService,
)
from tv_app.application.services.data.presentation_mutation_telemetry import record_presentation_mutation_event
from tv_app.application.services.presentation_change_notifier import (
    notify_presentation_changed,
)
from tv_app.application.services.slide_preset_service import (
    SlidePresetNotFoundError,
    resolve_preset_slide,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    MainSectionProtectedError,
    PlaylistNotFoundError,
    PlaylistRepository,
    SectionNotFoundError,
    SlideNotFoundError,
)

_PATCH_NATIVE_KEYS = patch_native_keys()

_VISUAL_PROJECTION_DEFAULTS = {
    "kpi_view": "kpiProjection",
    "chart_view": "chartProjection",
    "table_view": "tableProjection",
}


_CURRENT_PATCH_OP: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "vista_current_patch_op",
    default=None,
)


class PresentationPatchError(ValueError):
    """Erro de validação do envelope / ops (PresentationMutation)."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        merged = dict(details or {})
        current = _CURRENT_PATCH_OP.get()
        if isinstance(current, dict):
            if "opIndex" not in merged and current.get("opIndex") is not None:
                merged["opIndex"] = current["opIndex"]
            operation = current.get("operation")
            if "operation" not in merged and operation and operation != "?":
                merged["operation"] = operation
        self.details = merged


def _new_block_id() -> str:
    return f"blk_{uuid.uuid4().hex[:10]}"


def _blocks_of(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    raw = cfg.get("blocks")
    if not isinstance(raw, list):
        cfg["blocks"] = []
        return cfg["blocks"]
    return [b for b in raw if isinstance(b, dict)]


def _find_block(blocks: list[dict[str, Any]], block_id: str) -> dict[str, Any] | None:
    for block in blocks:
        if str(block.get("id") or "") == block_id:
            return block
    return None


# Nested keys materialized from blockDefaults on create (PRESENTATION-001).
_BLOCK_DEFAULT_NESTED_KEYS = frozenset(
    {
        "style",
        "frame",
        "kpiParts",
        "chartParts",
        "tableParts",
        "kpiOptions",
        "chartOptions",
        "tableOptions",
        "input",
        "inputParts",
        "imageCrop",
        "efficiencyPin",
    }
)


def _with_block_defaults(block: dict[str, Any]) -> dict[str, Any]:
    """Bloco novo recebe geometria/estilo/options canônicos do catálogo.

    Sem frame o bloco existe no native_config mas não aparece no slide.
    Options/parts (kpi/chart/table/input) também materializam no create para
    que o MFE pinte sem ``DEFAULT_*`` locais (TV-DASHBOARD-PRESENTATION-001).
    """
    defaults = PresentationOpsContentService.block_defaults(str(block.get("type") or ""))
    out = dict(block)
    for key, value in defaults.items():
        if key == "frame":
            if not isinstance(out.get("frame"), dict) and isinstance(value, dict):
                out["frame"] = dict(value)
            continue
        if key in _BLOCK_DEFAULT_NESTED_KEYS and isinstance(value, dict):
            current = out.get(key) if isinstance(out.get(key), dict) else {}
            # Defaults under authored keys (author wins).
            out[key] = {**value, **current} if key == "style" else deep_merge_dicts(value, current)
            continue
        if key not in out:
            out[key] = copy.deepcopy(value)
    return out


# Types that may be created with an informed id even without an authored frame
# (defaults inject geometry). Textual labels are the common ghost-create path.
_UPSERT_CREATE_FRIENDLY_TYPES = frozenset(
    {
        "image",
        "video",
        "icon",
        "chart_view",
        "table_view",
        "kpi_view",
        "canvas_table",
        "input",
        "data_source",
        "data_kpi",
        "data_chart",
        "data_table",
        "data_metric",
    }
)


def _upsert_block_has_authored_frame(block: dict[str, Any]) -> bool:
    frame = block.get("frame")
    return isinstance(frame, dict) and bool(frame)


def _upsert_block_allows_create(
    cleaned: dict[str, Any],
    op: dict[str, Any],
    *,
    root_block_id: str,
) -> bool:
    """Whether missing target may CREATE instead of failing ALTER_EXISTING.

    - createIfMissing:true → always allow
    - root blockId (VISTA alter contract) → never allow unless createIfMissing
    - authored frame → allow (positioned new visual)
    - chart/table/kpi/media types → allow (common recipe creates)
    - text/heading/shape without frame → refuse (ghost labels)
    """
    if op.get("createIfMissing") is True:
        return True
    if root_block_id:
        return False
    if _upsert_block_has_authored_frame(cleaned):
        return True
    btype = str(cleaned.get("type") or "").strip()
    return btype in _UPSERT_CREATE_FRIENDLY_TYPES


def _fingerprint_from_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Assinatura estável de campos críticos (sem payloads enormes)."""
    out: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        resolved = block.get("resolved")
        binding = block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else {}
        item: dict[str, Any] = {
            "id": block.get("id"),
            "type": block.get("type"),
            "operationId": binding.get("operationId"),
        }
        if isinstance(resolved, dict):
            for key in ("idd", "score", "si", "value", "summary", "items", "rows"):
                if key in resolved:
                    val = resolved[key]
                    if isinstance(val, (str, int, float, bool)) or val is None:
                        item[key] = val
                    elif isinstance(val, list):
                        item[f"{key}Count"] = len(val)
                    elif isinstance(val, dict):
                        item[f"{key}Keys"] = sorted(str(k) for k in val.keys())[:20]
        out.append(item)
    return out


def _diff_blocks(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> dict[str, Any]:
    before_ids = {str(b.get("id") or "") for b in before}
    after_ids = {str(b.get("id") or "") for b in after}
    return {
        "addedBlockIds": sorted(after_ids - before_ids),
        "removedBlockIds": sorted(before_ids - after_ids),
        "blockCountBefore": len(before),
        "blockCountAfter": len(after),
    }


def _field_present(op: dict[str, Any], field: str) -> bool:
    """Campo requerido presente: chave existe; null explícito ok; string vazia não."""
    if field not in op:
        return False
    value = op[field]
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, dict)) and not value:
        return False
    return True


def _validate_op_required_fields(op_name: str, raw_op: dict[str, Any]) -> None:
    spec = PresentationOpsContentService.operation_spec(op_name)
    schema = spec.get("inputSchema") if isinstance(spec, dict) else None
    if not isinstance(schema, dict):
        cap = PresentationOpsContentService.capability_by_op(op_name)
        schema = cap.get("inputSchema") if isinstance(cap, dict) else None
    if not isinstance(schema, dict):
        return
    required = schema.get("required")
    if not isinstance(required, list):
        return
    for field in required:
        key = str(field or "").strip()
        if not key or key == "op":
            continue
        if not _field_present(raw_op, key):
            raise PresentationPatchError(
                PresentationOpsContentService.message("opMissingField", op=op_name, field=key)
            )


def _validate_target_for_ops(
    ops: list[Any],
    *,
    playlist_id: str | None,
    slide_id: str | None,
) -> None:
    """Valida target mínimo respeitando produces do próprio plano (pós compile)."""
    typed = [op for op in ops if isinstance(op, dict)]
    requirements = PresentationOpsContentService.plan_resource_requirements(
        typed,
        {
            "playlistId": playlist_id or "",
            "slideId": slide_id or "",
        },
    )
    if requirements["requiresPlaylist"] and not playlist_id:
        raise PresentationPatchError(PresentationOpsContentService.message("missingPlaylist"))
    if requirements["requiresSlide"] and not slide_id:
        if requirements["requiresPlaylist"] and not playlist_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        raise PresentationPatchError(PresentationOpsContentService.message("missingSlide"))


_NATIVE_OP_NAMES = frozenset(
    {
        "upsert_data_source",
        "patch_data_source_params",
        "set_data_transform",
        "upsert_block",
        "set_display_format",
        "delete_block",
        "bind_visual",
        "patch_native_config",
        "ensure_brand_logo_on_slide",
        "apply_published_slide_template",
        # Mutates slide nativeConfig / dataFilters; must preload like other native ops.
        # Without this, preview raises misleading missingTarget even with valid target IDs.
        "re_layer_playlist_filters",
        # PRESENTATION-001 — geometry / identity ops on nativeConfig.
        "create_block",
        "align_blocks",
        "reorder_block_z",
        "duplicate_blocks",
        "transform_text_case",
        "bump_font_size",
    }
)


def _op_name_of(raw: dict[str, Any]) -> str:
    return str(raw.get("op") or "").strip()

def _collect_side_effect_hints(applied: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for op_name in applied:
        for hint in PresentationOpsContentService.side_effect_hints_for_op(op_name):
            if hint not in seen:
                seen.add(hint)
                ordered.append(hint)
    return ordered


class PresentationPatchService:
    """Aplica envelope TvPresentationPatchV1 sobre native_config / playlist."""

    def __init__(
        self,
        *,
        catalog: TvDataRouteCatalogService | None = None,
        repo: PlaylistRepository | None = None,
        resolution: SlideDataResolutionService | None = None,
    ) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()
        self._repo = repo or PlaylistRepository()
        self._resolution = resolution or SlideDataResolutionService(catalog=self._catalog)

    def preview(
        self,
        envelope: dict[str, Any],
        *,
        user: Any,
        authorization: str | None = None,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            # Sempre dry-run: o redutor não persiste; httpCommands são a saída.
            result = self._run(envelope, user=user, persist=False, authorization=authorization)
            # Gate executável: mudanças que tocam fontes de dados precisam
            # resolver o closure afetado no candidate state antes de virar
            # proposal elegível (commit_now incluso).
            self._assert_candidate_data_execution(
                result,
                envelope.get("ops"),
                user=user,
                authorization=authorization,
            )
            if include_fingerprint and result.get("nativeConfig"):
                result["fingerprint"] = self._resolve_fingerprint(
                    result["nativeConfig"],
                    user=user,
                    authorization=authorization,
                    playlist_defaults=result.get("playlistDefaults"),
                )
            record_presentation_mutation_event(
                kind="preview",
                ok=True,
                ops_count=len(result.get("appliedOps") or []),
                elapsed_ms=(time.perf_counter() - started) * 1000,
            )
            result["message"] = PresentationOpsContentService.message(
                "previewOk",
                ops=len(result.get("appliedOps") or []),
            )
            return result
        except PresentationPatchError as exc:
            record_presentation_mutation_event(
                kind="preview",
                ok=False,
                rejected_op=str(exc)[:120],
                elapsed_ms=(time.perf_counter() - started) * 1000,
            )
            raise

    def apply(
        self,
        envelope: dict[str, Any],
        *,
        user: Any,
        authorization: str | None = None,
        actor_user_id: str,
    ) -> dict[str, Any]:
        """Plano de apply via CRUD — não persiste no BFF.

        Mantido por compatibilidade de rota; a AI deve executar ``httpCommands``
        nas rotas ``/playlists/**``. ``actor_user_id`` é ignorado (a identidade
        vem do JWT nas rotas CRUD).
        """
        del actor_user_id  # identidade = JWT nas rotas CRUD
        started = time.perf_counter()
        try:
            result = self._run(
                envelope,
                user=user,
                persist=False,
                authorization=authorization,
            )
            record_presentation_mutation_event(
                kind="apply",
                ok=True,
                ops_count=len(result.get("appliedOps") or []),
                elapsed_ms=(time.perf_counter() - started) * 1000,
            )
            result["message"] = PresentationOpsContentService.message(
                "planReady",
                ops=len(result.get("httpCommands") or []),
            )
            result["persisted"] = False
            result["executionMode"] = "crud_http"
            return result
        except PresentationPatchError as exc:
            record_presentation_mutation_event(
                kind="apply",
                ok=False,
                rejected_op=str(exc)[:120],
                elapsed_ms=(time.perf_counter() - started) * 1000,
            )
            raise

    def _run(
        self,
        envelope: dict[str, Any],
        *,
        user: Any,
        persist: bool,
        authorization: str | None = None,
        actor_user_id: str | None = None,
    ) -> dict[str, Any]:
        # Redutor puro: nunca persiste. Persistência = rotas CRUD via httpCommands.
        persist = False
        actor_user_id = None

        if not isinstance(envelope, dict):
            raise PresentationPatchError(PresentationOpsContentService.message("invalidEnvelope"))

        ops = envelope.get("ops")
        if not isinstance(ops, list) or not ops:
            raise PresentationPatchError(PresentationOpsContentService.message("noOps"))

        max_ops = PresentationOpsContentService.setting_int("maxOpsPerPatch", 80)
        if len(ops) > max_ops:
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "tooManyOps",
                    count=len(ops),
                    max=max_ops,
                ),
                code="BATCH_TOO_LARGE",
                details={
                    "opCount": len(ops),
                    "maxOpsPerPatch": max_ops,
                    "suggestedCorrection": "split_by_slide_or_reduce_ops",
                },
            )

        target = envelope.get("target") if isinstance(envelope.get("target"), dict) else {}
        try:
            compiled = compile_presentation_plan(ops=ops, target=target)
        except PlanCompileError as exc:
            details: dict[str, Any] = {}
            if getattr(exc, "op_index", None) is not None:
                details["opIndex"] = exc.op_index
            if getattr(exc, "operation", None):
                details["operation"] = exc.operation
            raise PresentationPatchError(str(exc), code=exc.code, details=details or None) from exc
        ops = compiled.ordered_ops

        allowed = PresentationOpsContentService.allowed_ops()
        applied: list[str] = []
        side_effects: dict[str, Any] = {}
        removed_block_ids: list[str] = []
        informed_frame_ids: set[str] = set()
        playlist_mutated = False

        ctx = ExecutionContext.from_target(target)
        playlist_id = ctx.playlist_id
        slide_id = ctx.slide_id
        _validate_target_for_ops(
            ops,
            playlist_id=playlist_id,
            slide_id=slide_id,
        )
        native_config: dict[str, Any] | None = None
        playlist_defaults: dict[str, Any] | None = None
        before_blocks: list[dict[str, Any]] = []

        needs_native = any(
            isinstance(op, dict) and _op_name_of(op) in _NATIVE_OP_NAMES for op in ops
        )
        creates_slide = any(
            isinstance(op, dict)
            and _op_name_of(op) in {"add_blank_slide", "add_slide_from_preset"}
            for op in ops
        )

        if needs_native and playlist_id and slide_id and not (
            is_synthetic_id(playlist_id) or is_synthetic_id(slide_id)
        ):
            slide = self._load_slide(playlist_id or "", slide_id or "")
            native_config = copy.deepcopy(slide.get("nativeConfig") or {})
            if not isinstance(native_config, dict):
                native_config = {}
            if "version" not in native_config:
                native_config["version"] = 5
            before_blocks = copy.deepcopy(_blocks_of(native_config))
            playlist_defaults = self._playlist_defaults(playlist_id)
            ctx.native_config = native_config
            ctx.native_by_slide[str(slide_id)] = native_config
        elif needs_native and not creates_slide:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))

        for op_index, raw_op in enumerate(ops):
            _CURRENT_PATCH_OP.set({"opIndex": op_index})
            if not isinstance(raw_op, dict):
                raise PresentationPatchError(PresentationOpsContentService.message("unknownOp", op="?"))
            op_name = str(raw_op.get("op") or "").strip()
            _CURRENT_PATCH_OP.set({"opIndex": op_index, "operation": op_name or "?"})
            if op_name not in allowed:
                record_presentation_mutation_event(kind="preview", ok=False, rejected_op=op_name)
                raise PresentationPatchError(
                    PresentationOpsContentService.message("unknownOp", op=op_name or "?")
                )
            _validate_op_required_fields(op_name, raw_op)
            try:
                validate_operation_payload(op_name, raw_op)
            except NestedContractError as exc:
                raise PresentationPatchError(str(exc)) from exc

            playlist_id = ctx.resolve_playlist_id(raw_op) or ctx.playlist_id
            slide_id = ctx.resolve_slide_id(raw_op) or ctx.slide_id

            if op_name in _NATIVE_OP_NAMES:
                native_config = self._ensure_native_for_slide(
                    ctx,
                    playlist_id=playlist_id,
                    slide_id=slide_id,
                )
                if playlist_defaults is None and playlist_id:
                    playlist_defaults = self._playlist_defaults(playlist_id)
                slide_id = ctx.slide_id

            if op_name == "create_playlist":
                created = self._op_create_playlist(
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                if not created.get("id"):
                    created["id"] = mint_synthetic_id("playlist")
                ctx.set_playlist(str(created["id"]), op=raw_op)
                playlist_id = ctx.playlist_id
                side_effects["playlist"] = created
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "patch_playlist_data_defaults":
                if not playlist_id:
                    raise PresentationPatchError(
                        PresentationOpsContentService.message("missingPlaylist")
                    )
                patched_playlist = self._op_patch_playlist_data_defaults(
                    playlist_id,
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                side_effects["playlist"] = patched_playlist
                if isinstance(patched_playlist.get("dataDefaults"), dict):
                    playlist_defaults = dict(patched_playlist["dataDefaults"])
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "re_layer_playlist_filters":
                if not playlist_id or not slide_id or native_config is None:
                    details: dict[str, Any] = {
                        "operation": op_name,
                        "received": {
                            "playlistId": playlist_id,
                            "slideId": slide_id,
                        },
                    }
                    if playlist_id and slide_id and native_config is None:
                        details["validationPath"] = "nativeConfig"
                        details["internalReason"] = "native_config_not_loaded"
                        details["expected"] = "preloaded slide nativeConfig"
                    else:
                        details["validationPath"] = (
                            "target.slideId" if playlist_id and not slide_id else "target.playlistId"
                        )
                        details["internalReason"] = "target_ids_missing"
                    raise PresentationPatchError(
                        PresentationOpsContentService.message("missingTarget"),
                        details=details,
                    )
                playlist_defaults = self._op_re_layer_playlist_filters(
                    native_config,
                    raw_op,
                    playlist_id=playlist_id,
                    playlist_defaults=playlist_defaults,
                    side_effects=side_effects,
                )
                applied.append(op_name)
                continue

            if op_name == "add_slide_from_preset":
                if not playlist_id:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingPlaylist"))
                created_slide = self._op_add_slide_from_preset(
                    playlist_id,
                    raw_op,
                    user=user,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                if not created_slide.get("id"):
                    created_slide["id"] = mint_synthetic_id("slide")
                    created_slide["nativeConfig"] = copy.deepcopy(
                        created_slide.get("nativeConfig")
                        or {"version": 5, "headline": "", "subtitle": "", "blocks": []}
                    )
                ctx.set_slide(
                    str(created_slide["id"]),
                    op=raw_op,
                    native_config=created_slide.get("nativeConfig")
                    if isinstance(created_slide.get("nativeConfig"), dict)
                    else None,
                )
                slide_id = ctx.slide_id
                if ctx.native_config is not None:
                    native_config = ctx.native_config
                    if not before_blocks:
                        before_blocks = copy.deepcopy(_blocks_of(native_config))
                side_effects.setdefault("slides", []).append(created_slide)
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "add_blank_slide":
                if not playlist_id:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingPlaylist"))
                created_slide = self._op_add_blank_slide(
                    playlist_id,
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                if not created_slide.get("id"):
                    created_slide["id"] = mint_synthetic_id("slide")
                blank_native = created_slide.get("nativeConfig")
                if not isinstance(blank_native, dict):
                    blank_native = {
                        "version": 5,
                        "headline": "",
                        "subtitle": "",
                        "blocks": [],
                    }
                    created_slide["nativeConfig"] = blank_native
                ctx.set_slide(
                    str(created_slide["id"]),
                    op=raw_op,
                    native_config=blank_native,
                )
                slide_id = ctx.slide_id
                native_config = ctx.native_config
                if not before_blocks and native_config is not None:
                    before_blocks = copy.deepcopy(_blocks_of(native_config))
                side_effects.setdefault("slides", []).append(created_slide)
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "update_slide":
                updated = self._op_update_slide(
                    playlist_id,
                    slide_id,
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                side_effects.setdefault("slides", []).append(updated)
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "reorder_slides":
                if not playlist_id:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingPlaylist"))
                reordered = self._op_reorder_slides(
                    playlist_id,
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                side_effects["reorder"] = reordered
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "delete_slide":
                if not playlist_id or not slide_id:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
                deleted = self._op_delete_slide(
                    playlist_id,
                    slide_id,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                side_effects.setdefault("deletedSlides", []).append(deleted)
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "upsert_section":
                if not playlist_id:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingPlaylist"))
                section = self._op_upsert_section(
                    playlist_id,
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                if not section.get("id"):
                    section["id"] = mint_synthetic_id("section")
                ctx.set_section(str(section["id"]), op=raw_op)
                side_effects.setdefault("sections", []).append(section)
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "delete_section":
                if not playlist_id:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingPlaylist"))
                deleted = self._op_delete_section(
                    playlist_id,
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                side_effects.setdefault("deletedSections", []).append(deleted)
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if op_name == "move_slide_to_section":
                if not playlist_id or not slide_id:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
                moved = self._op_move_slide_to_section(
                    playlist_id,
                    slide_id,
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                side_effects.setdefault("slides", []).append(moved)
                applied.append(op_name)
                playlist_mutated = playlist_mutated or bool(persist)
                continue

            if native_config is None:
                if creates_slide or ctx.native_config is not None:
                    native_config = ctx.ensure_native_config()
                else:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))

            if op_name == "upsert_data_source":
                self._op_upsert_data_source(
                    native_config, raw_op, playlist_defaults=playlist_defaults
                )
            elif op_name == "patch_data_source_params":
                self._op_patch_data_source_params(
                    native_config, raw_op, side_effects=side_effects
                )
            elif op_name == "set_data_transform":
                self._op_set_data_transform(native_config, raw_op)
            elif op_name == "upsert_block":
                block_id, frame_informed = self._op_upsert_block(native_config, raw_op)
                if frame_informed and block_id:
                    informed_frame_ids.add(block_id)
            elif op_name == "set_display_format":
                self._op_set_display_format(native_config, raw_op)
            elif op_name == "create_block":
                block_id, frame_informed = self._op_create_block(native_config, raw_op)
                if frame_informed and block_id:
                    informed_frame_ids.add(block_id)
            elif op_name == "align_blocks":
                self._op_align_blocks(native_config, raw_op)
            elif op_name == "reorder_block_z":
                self._op_reorder_block_z(native_config, raw_op)
            elif op_name == "duplicate_blocks":
                self._op_duplicate_blocks(native_config, raw_op)
            elif op_name == "transform_text_case":
                self._op_transform_text_case(native_config, raw_op)
            elif op_name == "bump_font_size":
                self._op_bump_font_size(native_config, raw_op)
            elif op_name == "delete_block":
                removed = self._op_delete_block(native_config, raw_op)
                if removed:
                    removed_block_ids.append(removed)
            elif op_name == "bind_visual":
                self._op_bind_visual(native_config, raw_op)
            elif op_name == "patch_native_config":
                self._op_patch_native_config(native_config, raw_op)
            elif op_name == "ensure_brand_logo_on_slide":
                if not playlist_id:
                    raise PresentationPatchError(PresentationOpsContentService.message("missingPlaylist"))
                self._op_ensure_brand_logo_on_slide(
                    native_config,
                    raw_op,
                    playlist_id=playlist_id,
                    actor_user_id=actor_user_id,
                    persist=persist,
                )
            elif op_name == "apply_published_slide_template":
                self._op_apply_published_slide_template(native_config, raw_op)
            else:
                raise PresentationPatchError(
                    PresentationOpsContentService.message("unknownOp", op=op_name or "?")
                )
            ctx.native_config = native_config
            active_sid = str(ctx.slide_id or slide_id or "").strip()
            if active_sid:
                ctx.native_by_slide[active_sid] = native_config
                ctx.mark_native_touched(active_sid)
            applied.append(op_name)

        if native_config is not None or ctx.touched_native_slides:
            from tv_app.application.services.data.slide_auto_layout_service import (
                SlideAutoLayoutService,
            )
            from tv_app.application.services.data.slide_part_chrome_service import (
                SlidePartChromeService,
            )

            ctx.stash_native()
            cleaned_by_slide: dict[str, dict[str, Any]] = {}
            slide_ids = (
                set(ctx.touched_native_slides)
                if ctx.touched_native_slides
                else set(ctx.native_by_slide.keys())
            )
            for sid in slide_ids:
                cfg = ctx.native_by_slide.get(str(sid))
                if not isinstance(cfg, dict):
                    continue
                SlideAutoLayoutService.apply_post_create_layout(
                    cfg,
                    informed_block_ids=informed_frame_ids,
                )
                SlidePartChromeService.apply_missing_defaults(
                    cfg,
                    informed_block_ids=informed_frame_ids,
                )
                cleaned = sanitize_and_hydrate_comunicado_config(cfg, catalog=self._catalog)
                try:
                    validate_comunicado_native_config(
                        cleaned, user=user, catalog=self._catalog
                    )
                except ValueError as exc:
                    raise PresentationPatchError(str(exc)) from exc
                cleaned_by_slide[str(sid)] = cleaned
                ctx.native_by_slide[str(sid)] = cleaned
            if cleaned_by_slide:
                focus_id = str(
                    (target.get("slideId") if isinstance(target, dict) else None)
                    or ""
                ).strip()
                if focus_id and focus_id in cleaned_by_slide:
                    native_config = cleaned_by_slide[focus_id]
                    ctx.slide_id = focus_id
                elif len(cleaned_by_slide) == 1:
                    only_id, only_cfg = next(iter(cleaned_by_slide.items()))
                    native_config = only_cfg
                    ctx.slide_id = only_id
                else:
                    # Multi-slide: nativeConfig stays focus snapshot only if present;
                    # persistence uses nativeConfigsBySlide.
                    fallback_id = str(ctx.slide_id or next(iter(cleaned_by_slide)))
                    native_config = cleaned_by_slide.get(fallback_id) or next(
                        iter(cleaned_by_slide.values())
                    )
                ctx.native_config = native_config

        hints = _collect_side_effect_hints(applied)
        if removed_block_ids:
            side_effects["removedBlockIds"] = list(removed_block_ids)

        playlist_id = ctx.playlist_id
        slide_id = ctx.slide_id
        result: dict[str, Any] = {
            "ok": True,
            "version": "TvPresentationPatchV1",
            "catalogVersion": PresentationOpsContentService.catalog_version(),
            "appliedOps": applied,
            "target": {"playlistId": playlist_id, "slideId": slide_id},
            "sideEffects": side_effects,
            "sideEffectHints": hints,
            "playlistDefaults": playlist_defaults,
            "persisted": False,
            "executionMode": "crud_http",
            "orderedOps": ops,
            "dependencyOrder": compiled.dependency_order,
            "aliasMap": ctx.alias_map_public(),
            "compileDigest": compiled.compile_digest,
        }

        if ctx.touched_native_slides:
            result["nativeConfigsBySlide"] = {
                sid: cfg
                for sid, cfg in ctx.native_by_slide.items()
                if sid in ctx.touched_native_slides
                and isinstance(cfg, dict)
                and not is_synthetic_id(sid)
            }
        if native_config is not None:
            after_blocks = _blocks_of(native_config)
            result["nativeConfig"] = native_config
            result["diff"] = _diff_blocks(before_blocks, after_blocks)

        base_revision = self._playlist_revision(playlist_id)
        result["baseRevision"] = base_revision
        try:
            # Synthetic ids are preview placeholders (new playlist/slide). The HTTP
            # planner emits POST/PATCH with {playlistId}/{slideId} tokens — do not
            # wipe commands just because ctx now holds syn:* after create ops.
            plan_target = {
                "playlistId": None if is_synthetic_id(playlist_id) else playlist_id,
                "slideId": None if is_synthetic_id(slide_id) else slide_id,
            }
            # PATCH /playlists/{id} replaces dataDefaults JSON — send merged blob.
            plan_ops = copy.deepcopy(ops)
            playlist_preview = side_effects.get("playlist")
            if isinstance(playlist_preview, dict) and isinstance(
                playlist_preview.get("dataDefaults"), dict
            ):
                has_patch = any(
                    isinstance(plan_op, dict)
                    and _op_name_of(plan_op) == "patch_playlist_data_defaults"
                    for plan_op in plan_ops
                )
                if not has_patch and any(
                    isinstance(plan_op, dict)
                    and _op_name_of(plan_op) == "re_layer_playlist_filters"
                    for plan_op in plan_ops
                ):
                    plan_ops = [
                        {
                            "op": "patch_playlist_data_defaults",
                            "dataDefaults": copy.deepcopy(playlist_preview["dataDefaults"]),
                        },
                        *plan_ops,
                    ]
                for plan_op in plan_ops:
                    if (
                        isinstance(plan_op, dict)
                        and _op_name_of(plan_op) == "patch_playlist_data_defaults"
                    ):
                        plan_op["dataDefaults"] = copy.deepcopy(
                            playlist_preview["dataDefaults"]
                        )
            result["httpCommands"] = PresentationHttpCommandPlannerService.build(
                ops=plan_ops,
                target=plan_target,
                native_config=result.get("nativeConfig"),
                native_configs_by_slide=result.get("nativeConfigsBySlide"),
                alias_map=result.get("aliasMap")
                if isinstance(result.get("aliasMap"), dict)
                else None,
                base_revision=base_revision,
            )
        except ValueError as exc:
            raise PresentationPatchError(str(exc)) from exc

        return result

    def _ensure_native_for_slide(
        self,
        ctx: ExecutionContext,
        *,
        playlist_id: str | None,
        slide_id: str | None,
    ) -> dict[str, Any]:
        """Load or switch the active nativeConfig when ops target another existing slide."""
        if not playlist_id or not slide_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        sid = str(slide_id)
        if (
            str(ctx.slide_id or "") == sid
            and isinstance(ctx.native_config, dict)
        ):
            return ctx.native_config
        cached = ctx.native_by_slide.get(sid)
        if isinstance(cached, dict):
            return ctx.activate_native(sid, cached)
        if is_synthetic_id(sid) or is_synthetic_id(playlist_id):
            blank = ctx.ensure_native_config()
            return ctx.activate_native(sid, blank)
        slide = self._load_slide(playlist_id, sid)
        cfg = copy.deepcopy(slide.get("nativeConfig") or {})
        if not isinstance(cfg, dict):
            cfg = {}
        if "version" not in cfg:
            cfg["version"] = 5
        return ctx.activate_native(sid, cfg)

    def _playlist_revision(self, playlist_id: str | None) -> int | None:
        if not playlist_id or playlist_id.startswith("{") or is_synthetic_id(playlist_id):
            return None
        try:
            playlist = self._repo.get_by_id(UUID(str(playlist_id)))
        except (PlaylistNotFoundError, ValueError):
            return None
        if not isinstance(playlist, dict):
            return None
        try:
            return int(playlist.get("revision") or 0)
        except (TypeError, ValueError):
            return None

    def _playlist_defaults(self, playlist_id: str | None) -> dict[str, Any] | None:
        """dataDefaults da programação — contexto opcional, nunca quebra o patch."""
        if not playlist_id or is_synthetic_id(playlist_id):
            return None
        try:
            playlist = self._repo.get_by_id(UUID(str(playlist_id)))
        except (PlaylistNotFoundError, ValueError):
            return None
        if not isinstance(playlist, dict):
            return None
        defaults = playlist.get("dataDefaults")
        return dict(defaults) if isinstance(defaults, dict) else None

    def _load_slide(self, playlist_id: str, slide_id: str) -> dict[str, Any]:
        try:
            return self._repo.get_slide(UUID(slide_id), playlist_id=UUID(playlist_id))
        except (SlideNotFoundError, ValueError) as exc:
            raise PresentationPatchError(PresentationOpsContentService.message("slideNotFound")) from exc
        except PlaylistNotFoundError as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message("playlistNotFound")
            ) from exc

    def _resolve_fingerprint(
        self,
        native_config: dict[str, Any],
        *,
        user: Any,
        authorization: str | None,
        playlist_defaults: dict[str, Any] | None,
    ) -> list[dict[str, Any]] | None:
        blocks = [
            b
            for b in _blocks_of(native_config)
            if str(b.get("type") or "") == "data_source"
        ]
        if not blocks:
            return None
        cap = PresentationOpsContentService.setting_int("fingerprintMaxBlocks", 12)
        try:
            resolved = self._resolution.resolve_blocks(
                blocks[:cap],
                cfg=native_config,
                authorization=authorization,
                playlist_defaults=playlist_defaults,
                user=user,
                force_refresh=False,
            )
            return _fingerprint_from_blocks(resolved)
        except Exception:  # noqa: BLE001 — fingerprint é best-effort no preview
            return None

    _DATA_EXECUTION_OPS = frozenset(
        {
            "upsert_data_source",
            "patch_data_source_params",
            "set_data_transform",
            # Mudança estrutural no conjunto de fontes: closure exata exigiria o
            # grafo pré-op — validar todas as fontes do candidate é o seguro.
            "delete_block",
            "duplicate_blocks",
            # Ops sem alvo de bloco que podem alterar params/estado de dados.
            "patch_native_config",
            "patch_playlist_data_defaults",
            "re_layer_playlist_filters",
            "add_slide_from_preset",
            "apply_published_slide_template",
        }
    )

    def _assert_candidate_data_execution(
        self,
        result: dict[str, Any],
        ops: Any,
        *,
        user: Any,
        authorization: str | None,
    ) -> None:
        """Executa o closure de dados afetado no candidate nativeConfig.

        Só roda quando alguma op toca fontes de dados; erros tipados de
        execução (merge/calc/fetch) impedem o candidate de virar proposal.
        """
        op_list = [op for op in ops or [] if isinstance(op, dict)]
        touching = [
            op
            for op in op_list
            if str(op.get("op") or "").strip() in self._DATA_EXECUTION_OPS
        ]
        if not touching:
            return
        cfgs: list[dict[str, Any]] = []
        by_slide = result.get("nativeConfigsBySlide")
        if isinstance(by_slide, dict):
            cfgs.extend(c for c in by_slide.values() if isinstance(c, dict))
        primary = result.get("nativeConfig")
        if isinstance(primary, dict) and not any(c is primary for c in cfgs):
            cfgs.append(primary)
        playlist_defaults = (
            result.get("playlistDefaults")
            if isinstance(result.get("playlistDefaults"), dict)
            else None
        )
        for cfg in cfgs:
            self._validate_candidate_cfg_data(
                cfg, touching, user=user, authorization=authorization,
                playlist_defaults=playlist_defaults,
            )

    def _validate_candidate_cfg_data(
        self,
        cfg: dict[str, Any],
        touching_ops: list[dict[str, Any]],
        *,
        user: Any,
        authorization: str | None,
        playlist_defaults: dict[str, Any] | None,
    ) -> None:
        from tv_app.application.services.data.m_query.m_query_dependency_service import (
            MQueryDependencyService,
        )

        cfg_blocks = _blocks_of(cfg)
        ds_ids = {
            str(b.get("id") or "").strip()
            for b in cfg_blocks
            if isinstance(b, dict) and str(b.get("type") or "") == "data_source"
        }
        if not ds_ids:
            return
        touched: set[str] = set()
        validate_all = False
        for op in touching_ops:
            name = str(op.get("op") or "").strip()
            if name in {"delete_block", "duplicate_blocks"}:
                # Conjunto de fontes mudou estruturalmente: dependents de um id
                # removido/duplicado não aparecem no grafo pós-op → validar tudo.
                validate_all = True
                continue
            ids = [str(op.get("blockId") or "").strip()]
            raw_ids = op.get("blockIds")
            if isinstance(raw_ids, list):
                ids.extend(str(i).strip() for i in raw_ids)
            ids = [i for i in ids if i]
            if not ids:
                # Op cria fonte sem id informado → não dá para mapear → validar tudo.
                validate_all = True
                continue
            touched.update(ids)
        if not validate_all and not (touched & ds_ids):
            return  # ops de dados apontam para outros slides
        scope = ds_ids if validate_all else touched
        graph = MQueryDependencyService().resolve(cfg_blocks)
        deps = {
            node.source_id: set(node.dependencies) for node in graph.nodes
        }
        needed = set(scope)
        # upstream: dependências das fontes tocadas
        stack = list(scope)
        while stack:
            sid = stack.pop()
            for dep in deps.get(sid, ()):
                if dep not in needed:
                    needed.add(dep)
                    stack.append(dep)
        # downstream: fontes que dependem (transitivamente) das tocadas
        changed = True
        while changed:
            changed = False
            for sid, dep_set in deps.items():
                if sid not in needed and dep_set & needed:
                    needed.add(sid)
                    changed = True
        blocks = [
            b
            for b in cfg_blocks
            if isinstance(b, dict)
            and str(b.get("type") or "") == "data_source"
            and str(b.get("id") or "") in needed
        ]
        if not blocks:
            return
        try:
            enriched = self._resolution.resolve_blocks(
                blocks,
                cfg=cfg,
                authorization=authorization,
                playlist_defaults=playlist_defaults,
                user=user,
            )
        except Exception as exc:  # noqa: BLE001 — propaga como erro de gate
            raise PresentationPatchError(
                str(exc) or "Execução de dados do candidate falhou.",
                code="DATA_EXECUTION_FAILED",
                details={"stage": "data_execution"},
            ) from exc
        failures: list[tuple[dict[str, Any], dict[str, Any] | None, str]] = []
        for block in enriched:
            if not isinstance(block, dict):
                continue
            resolved = block.get("resolved")
            block_id = str(block.get("id") or "")
            if not isinstance(resolved, dict):
                raise PresentationPatchError(
                    f'A fonte "{block_id}" não foi resolvida no candidate state.',
                    code="DATA_EXECUTION_FAILED",
                    details={
                        "stage": "data_execution",
                        "blockId": block_id,
                    },
                )
            transform_error = (
                resolved.get("transformError")
                if isinstance(resolved.get("transformError"), dict)
                else None
            )
            error_msg = str(resolved.get("error") or "").strip()
            if transform_error or error_msg:
                failures.append((block, transform_error, error_msg))
        if failures:
            # Erros de modelo/transform (m.*) nomeiam a dependência quebrada e a
            # causa raiz na mensagem — priorizar sobre o erro bruto da fonte
            # upstream (ex.: fetch falhou na dependência).
            block, transform_error, error_msg = next(
                (
                    item
                    for item in failures
                    if str((item[1] or {}).get("code") or "").startswith("m.")
                ),
                failures[0],
            )
            block_id = str(block.get("id") or "")
            code = str((transform_error or {}).get("code") or "data.fetch_failed")
            details: dict[str, Any] = {
                "stage": "data_execution",
                "blockId": block_id,
                "errorCode": code,
            }
            dep_id = self._merge_dependency_ref(block)
            if dep_id:
                details["dependencySourceId"] = dep_id
            raise PresentationPatchError(
                str(
                    (transform_error or {}).get("message")
                    or error_msg
                    or "Execução de dados do candidate falhou."
                ),
                code=code,
                details=details,
            )

    @staticmethod
    def _merge_dependency_ref(block: dict[str, Any]) -> str | None:
        transform = block.get("dataTransform")
        steps = transform.get("steps") if isinstance(transform, dict) else None
        if not isinstance(steps, list):
            return None
        for step in steps:
            if isinstance(step, dict) and str(step.get("op") or "") == "merge":
                ref = str(step.get("sourceId") or "").strip()
                if ref:
                    return ref
        return None

    def _op_upsert_data_source(
        self,
        cfg: dict[str, Any],
        op: dict[str, Any],
        *,
        playlist_defaults: dict[str, Any] | None = None,
    ) -> None:
        operation_id = str(op.get("operationId") or "").strip()
        block_id = str(op.get("blockId") or "").strip()
        blocks = _blocks_of(cfg)
        existing = _find_block(blocks, block_id) if block_id else None

        # Label-only metadata patch: keep operationId/params/transforms/bindings intact.
        if self._is_data_source_label_only_patch(op, existing):
            assert existing is not None
            prior_binding = (
                existing.get("dataBinding")
                if isinstance(existing.get("dataBinding"), dict)
                else {}
            )
            label = str(op.get("label") or "").strip()
            existing["type"] = "data_source"
            existing["dataBinding"] = merge_data_binding(
                prior_binding, {"label": label}
            )
            # Do not clear resolved — label is display metadata only.
            if isinstance(op.get("fieldLabels"), dict):
                existing["fieldLabels"] = {
                    str(k): str(v)
                    for k, v in op["fieldLabels"].items()
                    if str(k).strip() and str(v).strip()
                }
            return

        if not operation_id:
            raise PresentationPatchError(
                PresentationOpsContentService.message("operationNotInCatalog", operationId="")
            )
        route = self._catalog.get_route(operation_id)
        if not route:
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "operationNotInCatalog", operationId=operation_id
                )
            )
        if not block_id:
            block_id = _new_block_id()
            existing = None
        params = op.get("params") if isinstance(op.get("params"), dict) else {}
        from tv_app.application.services.data.ready_slide_quality_service import (
            ReadySlideQualityService,
        )

        params = ReadySlideQualityService.enrich_data_source_params(
            route, params, playlist_defaults=playlist_defaults
        )
        slide_filters = (
            cfg.get("dataFilters") if isinstance(cfg.get("dataFilters"), dict) else None
        )
        try:
            ReadySlideQualityService.assert_data_source_params_ready(
                route,
                params,
                playlist_defaults=playlist_defaults,
                slide_filters=slide_filters,
            )
        except ValueError as exc:
            raise PresentationPatchError(str(exc)) from exc
        label = op.get("label") or route.get("label") or operation_id
        binding = {
            "operationId": operation_id,
            "params": dict(params),
            "displayMode": str(op.get("displayMode") or "auto"),
            "label": label,
        }
        if existing is not None:
            existing["type"] = "data_source"
            prior_binding = (
                existing.get("dataBinding")
                if isinstance(existing.get("dataBinding"), dict)
                else {}
            )
            existing["dataBinding"] = merge_data_binding(prior_binding, binding)
            existing.pop("resolved", None)
            if isinstance(op.get("dataTransform"), dict):
                existing["dataTransform"] = self._sanitize_vista_data_transform(
                    op["dataTransform"]
                )
                self._assert_transform_no_authoritative_shadow(
                    existing,
                    existing["dataTransform"].get("steps") or [],
                )
                self._assert_transform_preserves_consumers(cfg, existing)
            if isinstance(op.get("fieldLabels"), dict):
                existing["fieldLabels"] = {
                    str(k): str(v)
                    for k, v in op["fieldLabels"].items()
                    if str(k).strip() and str(v).strip()
                }
            return
        block: dict[str, Any] = _with_block_defaults(
            {
                "id": block_id,
                "type": "data_source",
                "dataBinding": binding,
            }
        )
        if isinstance(op.get("dataTransform"), dict):
            block["dataTransform"] = self._sanitize_vista_data_transform(
                op["dataTransform"]
            )
            self._assert_transform_no_authoritative_shadow(
                block, block["dataTransform"].get("steps") or []
            )
        if isinstance(op.get("fieldLabels"), dict):
            block["fieldLabels"] = {
                str(k): str(v)
                for k, v in op["fieldLabels"].items()
                if str(k).strip() and str(v).strip()
            }
        blocks.append(block)
        cfg["blocks"] = blocks

    def _op_patch_data_source_params(
        self,
        cfg: dict[str, Any],
        op: dict[str, Any],
        *,
        side_effects: dict[str, Any] | None = None,
    ) -> None:
        """Patch atomico de `dataBinding.params`: set/unset com allowlist da rota.

        Preserva operationId/transforms/bindings/layout/label/displayMode do
        bloco. Período mergeia como intenção atômica via
        ``merge_period_params_layer`` — `set` com preset dinâmico remove datas
        stale mesmo sem `unset` explícito.
        """
        block_id = str(op.get("blockId") or "").strip()
        blocks = _blocks_of(cfg)
        existing = _find_block(blocks, block_id) if block_id else None
        if existing is None or str(existing.get("type") or "") != "data_source":
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "blockNotFound", blockId=block_id or "?"
                )
            )
        binding = (
            existing.get("dataBinding")
            if isinstance(existing.get("dataBinding"), dict)
            else {}
        )
        operation_id = str(binding.get("operationId") or "").strip()
        route = self._catalog.get_route(operation_id) if operation_id else None
        if not isinstance(route, dict):
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "operationNotInCatalog", operationId=operation_id
                )
            )

        raw_set = op.get("set") if isinstance(op.get("set"), dict) else {}
        raw_unset = op.get("unset") if isinstance(op.get("unset"), list) else []

        set_patch: dict[str, Any] = {}
        unset_keys: set[str] = set()
        for key, value in raw_set.items():
            key_str = str(key).strip()
            if not key_str:
                continue
            if value is None or value == "":
                unset_keys.add(key_str)
                continue
            if not isinstance(value, (str, int, float, bool)):
                raise PresentationPatchError(
                    PresentationOpsContentService.message("paramsInvalid")
                )
            set_patch[key_str] = value
        for item in raw_unset:
            key_str = str(item or "").strip()
            if key_str:
                unset_keys.add(key_str)
        unset_keys.difference_update(set_patch)

        schema = (
            route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
        )
        schema_keys = set(schema.keys())
        allowed = schema_keys | _KEEP_WITHOUT_SCHEMA | set(_PARAM_KEY_REMAP)
        current = binding.get("params") if isinstance(binding.get("params"), dict) else {}

        rejected = sorted(key for key in set_patch if key not in allowed) + sorted(
            key for key in unset_keys if key not in allowed and key not in current
        )
        if rejected:
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "dataSourceParamNotAllowed",
                    blockId=block_id,
                    keys=", ".join(rejected),
                )
            )

        set_patch, _ = _remap_param_keys(set_patch, schema_keys)
        base = {key: value for key, value in current.items() if key not in unset_keys}
        next_params = merge_period_params_layer(base, set_patch)

        removed = sorted(key for key in current if key not in next_params)
        changed_set = {
            key: next_params[key]
            for key in set_patch
            if key in next_params and current.get(key) != next_params[key]
        }
        next_binding = dict(binding)
        next_binding["params"] = next_params
        existing["dataBinding"] = next_binding
        existing.pop("resolved", None)
        if side_effects is not None:
            side_effects.setdefault("dataSourceParamPatches", []).append(
                {
                    "blockId": block_id,
                    "changed": {"set": changed_set, "unset": removed},
                }
            )

    @staticmethod
    def _is_data_source_label_only_patch(
        op: dict[str, Any], existing: dict[str, Any] | None
    ) -> bool:
        """True when op only renames an existing source (no route/params rewrite)."""
        if existing is None or str(existing.get("type") or "") != "data_source":
            return False
        label = str(op.get("label") or "").strip()
        if not label:
            return False
        # Explicit params/transform/displayMode ⇒ full upsert path.
        if isinstance(op.get("params"), dict) and op["params"]:
            return False
        if isinstance(op.get("dataTransform"), dict):
            return False
        if op.get("displayMode") not in (None, ""):
            return False
        op_id = str(op.get("operationId") or "").strip()
        if not op_id:
            return True
        prior = (
            existing.get("dataBinding")
            if isinstance(existing.get("dataBinding"), dict)
            else {}
        )
        prior_op = str(prior.get("operationId") or "").strip()
        # Same route + label only (optional operationId echo) still label-only.
        return bool(prior_op) and prior_op == op_id

    def _sanitize_vista_data_transform(self, raw: dict[str, Any]) -> dict[str, Any]:
        if (
            raw.get("script") is not None
            or raw.get("language") is not None
            or raw.get("version") == 2
        ):
            raise PresentationPatchError(PresentationOpsContentService.message("mForbidden"))
        raw_steps = raw.get("steps")
        if isinstance(raw_steps, list):
            for index, step in enumerate(raw_steps):
                # Um step malformado não pode sumir em silêncio: o modelo
                # persistido divergiria da intenção declarada.
                if not isinstance(step, dict) or (
                    normalize_legacy_transform({"steps": [step]}) is None
                ):
                    raise PresentationPatchError(
                        "Etapa de transformação inválida.",
                        code="DATA_TRANSFORM_INVALID_STEP",
                        details={
                            "stepIndex": index,
                            "op": str(step.get("op") or "") if isinstance(step, dict) else None,
                        },
                    )
        sanitized = sanitize_data_transform_for_persistence(raw)
        if sanitized is None:
            return {"steps": []}
        if sanitized.get("script") is not None or sanitized.get("version") == 2:
            raise PresentationPatchError(PresentationOpsContentService.message("mForbidden"))
        return sanitized

    def _route_result_field_names(self, block: dict[str, Any]) -> set[str] | None:
        """Campos declarados da rota do binding (schema autoritativo de entrada)."""
        binding = (
            block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else {}
        )
        operation_id = str(binding.get("operationId") or "").strip()
        route = (
            self._catalog.get_route(operation_id)
            if operation_id and self._catalog is not None
            else None
        )
        if not isinstance(route, dict):
            return None
        names: set[str] = set()
        for item in route.get("projectableFields") or []:
            if isinstance(item, dict) and item.get("projectable", True):
                name = str(item.get("name") or "").strip()
                if name:
                    names.add(name)
        for raw in route.get("valueFields") or []:
            name = str(raw or "").strip()
            if name:
                names.add(name)
        return names or None

    def _projected_source_output_columns(
        self,
        cfg: dict[str, Any],
        block: dict[str, Any],
        _visited: frozenset[str] = frozenset(),
    ) -> set[str] | None:
        """Schema de saída da fonte após dataTransform (estático, sem executar)."""
        block_id = str(block.get("id") or "")
        if block_id in _visited:
            return None  # ciclo de merges — indeterminável
        visited = _visited | {block_id}
        normalized = normalize_data_transform(block.get("dataTransform"))
        steps = normalized.get("steps") if normalized else []
        input_columns = self._route_result_field_names(block)
        if not steps:
            return input_columns

        def sibling_columns(source_id: str) -> set[str] | None:
            sibling = _find_block(_blocks_of(cfg), source_id)
            if sibling is None:
                return None
            return self._projected_source_output_columns(cfg, sibling, visited)

        return project_transform_output_columns(
            input_columns,
            steps,
            sibling_columns=sibling_columns,
        )

    def _assert_transform_preserves_consumers(
        self,
        cfg: dict[str, Any],
        source_block: dict[str, Any],
    ) -> None:
        """Fonte compartilhada: transform estrutural não pode remover campo
        ligado por consumer existente (kpi/chart/table/text/canvas)."""
        from tv_app.application.services.data.projection_fields_contract import (
            collect_source_consumer_field_refs,
        )

        source_id = str(source_block.get("id") or "").strip()
        consumers = collect_source_consumer_field_refs(_blocks_of(cfg), source_id)
        if not consumers:
            return
        normalized = normalize_data_transform(source_block.get("dataTransform"))
        steps = normalized.get("steps") if normalized else []
        if not steps:
            return
        projected = self._projected_source_output_columns(cfg, source_block)
        if projected is None:
            structural = any(
                isinstance(step, dict)
                and str(step.get("op") or "") in STRUCTURAL_TRANSFORM_OPS
                for step in steps
            )
            if structural:
                raise PresentationPatchError(
                    "Transform estrutural em fonte compartilhada: schema de saída "
                    "indeterminável e a fonte possui consumers. Use uma fonte "
                    "auxiliar ou declare colunas explícitas.",
                    code="DATA_TRANSFORM_SCHEMA_UNKNOWN",
                    details={
                        "blockId": source_id,
                        "consumers": {k: v for k, v in consumers.items()},
                    },
                )
            return
        missing = {
            block_id: [
                field
                for field in refs
                if field not in projected and not field.startswith("filter.")
            ]
            for block_id, refs in consumers.items()
        }
        missing = {key: value for key, value in missing.items() if value}
        if missing:
            raise PresentationPatchError(
                "O transform remove campos ligados por consumers da fonte: "
                + ", ".join(sorted({f for fields in missing.values() for f in fields})),
                code="DATA_BINDING_FIELD_MISSING",
                details={
                    "blockId": source_id,
                    "consumers": missing,
                    "outputColumns": sorted(projected),
                },
            )

    def _assert_transform_no_authoritative_shadow(
        self,
        block: dict[str, Any],
        steps: list[dict[str, Any]],
    ) -> None:
        """AUTHORITATIVE ROUTE FIELD > DERIVED TV CALCULATION.

        addColumn cujo nome coincide com campo que a rota já retorna é shadow
        de campo autoritativo → rejeita; o binding deve usar o campo da rota.
        """
        route_fields = self._route_result_field_names(block)
        if not route_fields:
            return
        for index, step in enumerate(steps):
            if not isinstance(step, dict) or str(step.get("op") or "") != "addColumn":
                continue
            name = str(step.get("name") or "").strip()
            if name and name in route_fields:
                raise PresentationPatchError(
                    f'A coluna derivada "{name}" sombreia um campo que a rota já '
                    "fornece; vincule o campo autoritativo diretamente.",
                    code="DATA_FIELD_AUTHORITATIVE",
                    details={
                        "blockId": str(block.get("id") or ""),
                        "stepIndex": index,
                        "field": name,
                        "routeFields": sorted(route_fields),
                    },
                )

    def _op_set_data_transform(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        if (
            op.get("script") is not None
            or op.get("language") is not None
            or op.get("version") == 2
            or (
                isinstance(op.get("dataTransform"), dict)
                and (
                    op["dataTransform"].get("script") is not None
                    or op["dataTransform"].get("language") is not None
                    or op["dataTransform"].get("version") == 2
                )
            )
        ):
            raise PresentationPatchError(PresentationOpsContentService.message("mForbidden"))
        block_id = str(op.get("blockId") or "").strip()
        blocks = _blocks_of(cfg)
        block = _find_block(blocks, block_id) if block_id else None
        if block is None:
            for candidate in blocks:
                if str(candidate.get("type") or "") == "data_source":
                    block = candidate
                    break
        if block is None:
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockNotFound", blockId=block_id or "?")
            )
        steps = op.get("steps")
        if steps is None and isinstance(op.get("dataTransform"), dict):
            transform = self._sanitize_vista_data_transform(op["dataTransform"])
        else:
            transform = self._sanitize_vista_data_transform(
                {"steps": list(steps) if isinstance(steps, list) else []}
            )
        block["dataTransform"] = transform
        self._assert_transform_no_authoritative_shadow(
            block, transform.get("steps") or []
        )
        self._assert_transform_preserves_consumers(cfg, block)
        block.pop("resolved", None)

    def _op_set_display_format(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        from tv_app.application.services.data.display_format_service import DisplayFormatService

        block_id = str(op.get("blockId") or "").strip()
        block = _find_block(_blocks_of(cfg), block_id)
        if block is None:
            raise PresentationPatchError(
                f"Bloco {block_id!r} não encontrado.",
                code="DISPLAY_FORMAT_TARGET_NOT_FOUND",
                details={"blockId": block_id},
            )
        target = op.get("target") or {}
        owner = target.get("owner")
        field = str(target.get("field") or "").strip()
        try:
            spec = DisplayFormatService.validate_write_spec(op.get("displayFormat"))
        except ValueError as exc:
            raise PresentationPatchError(str(exc), code="DISPLAY_FORMAT_INVALID") from exc
        if owner == "contentRunDataRef":
            if str(block.get("type") or "") not in {"text", "heading", "shape"}:
                raise PresentationPatchError("Tipo de bloco não suporta contentRuns.", code="DISPLAY_FORMAT_UNSUPPORTED_TARGET")
            runs = block.get("contentRuns")
            candidates = [
                run.get("dataRef") for run in (runs if isinstance(runs, list) else [])
                if isinstance(run, dict) and isinstance(run.get("dataRef"), dict)
                and str(run["dataRef"].get("field") or "") == field
            ]
            if not candidates:
                raise PresentationPatchError("Binding não encontrado.", code="DISPLAY_FORMAT_TARGET_NOT_FOUND")
            occurrence = target.get("occurrence")
            if occurrence is None and len(candidates) > 1:
                raise PresentationPatchError(
                    "Binding ambíguo; informe occurrence.",
                    code="DISPLAY_FORMAT_TARGET_AMBIGUOUS",
                    details={"candidates": [
                        {"owner": owner, "field": field, "occurrence": i}
                        for i in range(len(candidates))
                    ]},
                )
            index = occurrence if occurrence is not None else 0
            if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(candidates):
                raise PresentationPatchError("Occurrence não encontrado.", code="DISPLAY_FORMAT_TARGET_NOT_FOUND")
            candidates[index]["displayFormat"] = copy.deepcopy(spec)
        elif owner == "textProjection":
            if str(block.get("type") or "") not in {"text", "heading", "shape"}:
                raise PresentationPatchError("Tipo de bloco não suporta textProjection.", code="DISPLAY_FORMAT_UNSUPPORTED_TARGET")
            projection = block.get("textProjection")
            if not isinstance(projection, dict) or str(projection.get("field") or "") != field:
                raise PresentationPatchError("Binding não encontrado.", code="DISPLAY_FORMAT_TARGET_NOT_FOUND")
            runs = block.get("contentRuns")
            if any(isinstance(run, dict) and isinstance(run.get("dataRef"), dict) and run["dataRef"].get("field") for run in (runs if isinstance(runs, list) else [])):
                raise PresentationPatchError("textProjection não é owner ativo.", code="DISPLAY_FORMAT_UNSUPPORTED_TARGET")
            projection["displayFormat"] = copy.deepcopy(spec)
        else:
            raise PresentationPatchError("Owner de formato não suportado.", code="DISPLAY_FORMAT_UNSUPPORTED_TARGET")
        block.pop("resolved", None)

    def _op_upsert_block(self, cfg: dict[str, Any], op: dict[str, Any]) -> tuple[str, bool]:
        block = op.get("block")
        if not isinstance(block, dict):
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockNotFound", blockId="?")
            )
        frame_informed = isinstance(block.get("frame"), dict) and bool(block.get("frame"))
        # Anti-padrão: nunca aceitar resolved / url solta / M script.
        # assetId é permitido (mídia via asset da TV).
        cleaned = dict(block)
        cleaned.pop("resolved", None)
        cleaned.pop("url", None)
        cleaned.pop("mScript", None)
        cleaned.pop("powerQueryM", None)
        if block.get("mScript") or block.get("powerQueryM"):
            raise PresentationPatchError(PresentationOpsContentService.message("mForbidden"))
        raw_transform = cleaned.get("dataTransform")
        if isinstance(raw_transform, dict) and (
            raw_transform.get("script") is not None
            or raw_transform.get("language") is not None
            or raw_transform.get("version") == 2
        ):
            raise PresentationPatchError(PresentationOpsContentService.message("mForbidden"))
        if isinstance(raw_transform, dict):
            sanitized = sanitize_data_transform_for_persistence(raw_transform)
            if sanitized is None:
                cleaned.pop("dataTransform", None)
            else:
                cleaned["dataTransform"] = sanitized
        from tv_app.application.services.data.table_view_projection_authority import (
            has_explicit_table_columns,
            normalize_block_table_projection,
            validate_table_parts,
        )

        part_errors = validate_table_parts(cleaned.get("tableParts"))
        if part_errors:
            raise PresentationPatchError(
                "tableParts inválido/não suportado: "
                + ", ".join(part_errors[:6])
                + ". Use frame|title|header|headerCell|row|cell|rowEven|rowOdd; "
                "banding via tablePreset=banded / tableParts.rowEven|rowOdd."
            )
        if str(cleaned.get("type") or "").strip() in {"table_view", "data_table"}:
            normalize_block_table_projection(cleaned)

        from tv_app.application.services.data.display_format_hints_service import (
            DisplayFormatHintsService,
        )

        format_errors = DisplayFormatHintsService.validate_projection_formats(cleaned)
        if format_errors:
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "displayFormatInvalid",
                    field=", ".join(format_errors[:4]),
                )
            )

        from tv_app.application.services.data.projection_fields_contract import (
            validate_block_projection_fields,
        )

        projection_route: dict[str, Any] | None = None
        projected_fields: list[dict[str, Any]] | None = None
        source_id = str(cleaned.get("dataSourceId") or "").strip()
        if source_id:
            source_block = _find_block(_blocks_of(cfg), source_id)
            binding = (
                source_block.get("dataBinding")
                if isinstance(source_block, dict) and isinstance(source_block.get("dataBinding"), dict)
                else None
            )
            operation_id = str((binding or {}).get("operationId") or "").strip()
            if operation_id and self._catalog is not None:
                projection_route = self._catalog.get_route(operation_id)
            # Fonte com transform: refs validam contra o schema de SAÍDA, não
            # contra os campos da rota (campo renomeado/removido não pode virar
            # binding inválido silencioso).
            if isinstance(source_block, dict) and isinstance(
                source_block.get("dataTransform"), dict
            ):
                projected = self._projected_source_output_columns(cfg, source_block)
                if projected is not None:
                    projected_fields = [
                        {"name": name, "projectable": True}
                        for name in sorted(projected)
                    ]
        # Fonte embutida (data_* com binding próprio).
        if projection_route is None and isinstance(cleaned.get("dataBinding"), dict):
            operation_id = str(cleaned["dataBinding"].get("operationId") or "").strip()
            if operation_id and self._catalog is not None:
                projection_route = self._catalog.get_route(operation_id)

        field_error = validate_block_projection_fields(
            cleaned,
            route=projection_route if projected_fields is None else None,
            fields=projected_fields,
        )
        if field_error:
            raise PresentationPatchError(
                str(field_error.get("message") or "Campo de projeção inválido"),
                code=str(field_error.get("code") or "INVALID_PROJECTION_FIELD"),
                details={
                    "invalidFields": field_error.get("invalidFields") or [],
                    "allowedFields": field_error.get("allowedFields") or [],
                },
            )

        # Identity: block.id or root blockId (VISTA ALTER_EXISTING alias).
        root_block_id = str(op.get("blockId") or "").strip()
        nested_id = str(cleaned.get("id") or "").strip()
        if root_block_id and nested_id and root_block_id != nested_id:
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "upsertBlockIdConflict",
                    blockId=nested_id,
                    rootBlockId=root_block_id,
                )
            )
        block_id = nested_id or root_block_id
        projection_informed = has_explicit_table_columns(cleaned)
        blocks = _blocks_of(cfg)
        existing = _find_block(blocks, block_id) if block_id else None
        from tv_app.application.services.data.display_format_service import (
            DisplayFormatService,
        )

        if existing is not None:
            cleaned["id"] = str(existing.get("id") or block_id)
            # Partial patch: deep-merge nested style/frame/… so siblings survive.
            merged = merge_block_patch(existing, cleaned)
            if str(merged.get("type") or "").strip() in {"table_view", "data_table"}:
                normalize_block_table_projection(merged)
            # Campo / textProjection write must not leave dual-bind (G15).
            merged = DisplayFormatService.sanitize_contradictory_text_binding(merged)
            from tv_app.application.services.data.text_typography_service import (
                normalize_block_text_style,
                normalize_run_style,
            )

            if isinstance(merged.get("style"), dict):
                merged["style"] = normalize_block_text_style(merged["style"]) or {}
            runs = merged.get("contentRuns")
            if isinstance(runs, list):
                normalized_runs: list[Any] = []
                for raw in runs:
                    if not isinstance(raw, dict):
                        continue
                    run = dict(raw)
                    if isinstance(run.get("style"), dict):
                        ns = normalize_run_style(run["style"])
                        if ns:
                            run["style"] = ns
                        else:
                            run.pop("style", None)
                    normalized_runs.append(run)
                merged["contentRuns"] = normalized_runs
            existing.clear()
            existing.update(merged)
            cfg["blocks"] = blocks
            return str(existing.get("id") or block_id), frame_informed or projection_informed

        if not _upsert_block_allows_create(
            cleaned, op, root_block_id=root_block_id
        ):
            if block_id:
                raise PresentationPatchError(
                    PresentationOpsContentService.message(
                        "blockNotFound", blockId=block_id
                    ),
                    details={
                        "reason": "TARGET_BLOCK_NOT_FOUND",
                        "requestedBlockId": block_id,
                        "refetchRequired": True,
                        "resolutionHint": (
                            "Call gpt_get_playlist_context (scope=editorFocus) and "
                            "resolve blockId from blockIndex/objectMatches; never invent IDs."
                        ),
                    },
                )
            raise PresentationPatchError(
                PresentationOpsContentService.message("upsertBlockTargetRequired")
            )

        if not block_id:
            block_id = _new_block_id()
        cleaned["id"] = block_id
        blocks.append(
            DisplayFormatService.sanitize_contradictory_text_binding(
                _with_block_defaults(cleaned)
            )
        )
        cfg["blocks"] = blocks
        return block_id, frame_informed or projection_informed

    def _op_create_block(self, cfg: dict[str, Any], op: dict[str, Any]) -> tuple[str, bool]:
        """Typed create — type (+ optional chartType/shape/icon) → canonical block."""
        btype = str(op.get("type") or "").strip()
        if not btype:
            raise PresentationPatchError(
                PresentationOpsContentService.message("createBlockTypeRequired")
            )
        block: dict[str, Any] = {"type": btype}
        informed_id = str(op.get("blockId") or "").strip()
        if informed_id:
            block["id"] = informed_id
        for key in (
            "chartType",
            "shape",
            "iconName",
            "content",
            "tablePreset",
            "frame",
            "style",
            "dataBinding",
            "kpiOptions",
            "chartOptions",
            "tableOptions",
            "input",
        ):
            if key in op and op[key] is not None:
                block[key] = op[key]
        # Shape/icon convenience: map content → iconName when type=icon.
        if btype == "icon" and "iconName" not in block and isinstance(op.get("content"), str):
            block["iconName"] = op["content"]
        if btype == "shape" and "shape" not in block:
            block["shape"] = "rectangle"
        return self._op_upsert_block(
            cfg,
            {"op": "upsert_block", "block": block, "createIfMissing": True},
        )

    def _op_align_blocks(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        from tv_app.application.services.data.block_layout_service import align_blocks

        raw_ids = op.get("blockIds")
        if not isinstance(raw_ids, list) or not raw_ids:
            raise PresentationPatchError(
                PresentationOpsContentService.message("layoutNeedBlockIds")
            )
        command = str(op.get("command") or "").strip()
        try:
            align_blocks(_blocks_of(cfg), [str(i) for i in raw_ids], command)
        except ValueError as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "layoutCommandInvalid", command=command or "?"
                )
            ) from exc

    def _op_reorder_block_z(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        from tv_app.application.services.data.block_layout_service import reorder_block_z

        raw_ids = op.get("blockIds")
        if not isinstance(raw_ids, list) or not raw_ids:
            raise PresentationPatchError(
                PresentationOpsContentService.message("layoutNeedBlockIds")
            )
        command = str(op.get("command") or "").strip()
        try:
            reorder_block_z(_blocks_of(cfg), [str(i) for i in raw_ids], command)
        except ValueError as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message(
                    "layoutCommandInvalid", command=command or "?"
                )
            ) from exc

    def _op_duplicate_blocks(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        from tv_app.application.services.data.block_layout_service import duplicate_blocks

        raw_ids = op.get("blockIds")
        if not isinstance(raw_ids, list) or not raw_ids:
            raise PresentationPatchError(
                PresentationOpsContentService.message("layoutNeedBlockIds")
            )
        try:
            ox = float(op.get("offsetX", 2) if op.get("offsetX") is not None else 2)
            oy = float(op.get("offsetY", 2) if op.get("offsetY") is not None else 2)
        except (TypeError, ValueError):
            ox, oy = 2.0, 2.0
        blocks = _blocks_of(cfg)
        clones = duplicate_blocks(
            blocks,
            [str(i) for i in raw_ids],
            offset_x=ox,
            offset_y=oy,
            new_id_fn=_new_block_id,
        )
        for clone in clones:
            blocks.append(_with_block_defaults(clone))
        cfg["blocks"] = blocks

    def _op_transform_text_case(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        from tv_app.application.services.data.text_typography_service import (
            plain_from_runs,
            transform_content_runs_case,
            transform_text_case,
        )

        block_id = str(op.get("blockId") or "").strip()
        mode = str(op.get("mode") or "").strip().lower()
        if not block_id:
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockIdRequired")
            )
        if mode not in {"sentence", "lower", "upper", "title", "toggle"}:
            raise PresentationPatchError(
                PresentationOpsContentService.message("unknownOp", op="transform_text_case")
            )
        blocks = _blocks_of(cfg)
        block = _find_block(blocks, block_id)
        if block is None:
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockNotFound", blockId=block_id)
            )
        runs = block.get("contentRuns")
        start = op.get("start")
        end = op.get("end")
        range_start: int | None = None
        range_end: int | None = None
        try:
            if start is not None and end is not None:
                range_start = int(start)
                range_end = int(end)
        except (TypeError, ValueError):
            range_start = None
            range_end = None
        if isinstance(runs, list) and runs:
            next_runs = transform_content_runs_case(
                runs, mode, start=range_start, end=range_end
            )
            block["contentRuns"] = next_runs
            block["content"] = plain_from_runs(next_runs)
        else:
            content = block.get("content")
            if isinstance(content, str):
                if (
                    range_start is not None
                    and range_end is not None
                    and 0 <= range_start < range_end <= len(content)
                ):
                    before = content[:range_start]
                    mid = transform_text_case(content[range_start:range_end], mode)
                    after = content[range_end:]
                    block["content"] = f"{before}{mid}{after}"
                else:
                    block["content"] = transform_text_case(content, mode)
        cfg["blocks"] = blocks

    def _op_bump_font_size(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        from tv_app.application.services.data.text_typography_service import bump_font_size

        block_id = str(op.get("blockId") or "").strip()
        if not block_id:
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockIdRequired")
            )
        try:
            delta = int(op.get("deltaSteps"))
        except (TypeError, ValueError) as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message("unknownOp", op="bump_font_size")
            ) from exc
        blocks = _blocks_of(cfg)
        block = _find_block(blocks, block_id)
        if block is None:
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockNotFound", blockId=block_id)
            )
        style = block.get("style") if isinstance(block.get("style"), dict) else {}
        next_style = dict(style)
        next_style["fontSize"] = bump_font_size(style.get("fontSize"), delta)
        block["style"] = next_style
        # Also bump run fontSizes when present so partial rich text stays coherent.
        runs = block.get("contentRuns")
        if isinstance(runs, list):
            next_runs: list[Any] = []
            for raw in runs:
                if not isinstance(raw, dict):
                    continue
                run = dict(raw)
                run_style = run.get("style") if isinstance(run.get("style"), dict) else None
                if run_style and run_style.get("fontSize") is not None:
                    rs = dict(run_style)
                    rs["fontSize"] = bump_font_size(rs.get("fontSize"), delta)
                    run["style"] = rs
                next_runs.append(run)
            block["contentRuns"] = next_runs
        cfg["blocks"] = blocks

    def _op_delete_block(self, cfg: dict[str, Any], op: dict[str, Any]) -> str | None:
        block_id = str(op.get("blockId") or "").strip()
        if not block_id:
            raise PresentationPatchError(PresentationOpsContentService.message("blockIdRequired"))
        blocks = _blocks_of(cfg)
        kept = [b for b in blocks if str(b.get("id") or "") != block_id]
        if len(kept) == len(blocks):
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockNotFound", blockId=block_id)
            )
        cfg["blocks"] = kept
        return block_id

    def _op_bind_visual(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        visual_id = str(op.get("visualId") or "").strip()
        data_source_id = str(op.get("dataSourceId") or "").strip()
        if not visual_id or not data_source_id:
            raise PresentationPatchError(PresentationOpsContentService.message("bindNeedIds"))
        blocks = _blocks_of(cfg)
        visual = _find_block(blocks, visual_id)
        source = _find_block(blocks, data_source_id)
        if visual is None:
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockNotFound", blockId=visual_id)
            )
        if source is None:
            raise PresentationPatchError(
                PresentationOpsContentService.message("blockNotFound", blockId=data_source_id)
            )
        visual["dataSourceId"] = data_source_id
        visual.pop("resolved", None)
        binding = (
            source.get("dataBinding")
            if isinstance(source.get("dataBinding"), dict)
            else {}
        )
        operation_id = str(binding.get("operationId") or "").strip()
        route = self._catalog.get_route(operation_id) if operation_id else None
        from tv_app.application.services.data.ready_slide_quality_service import (
            ReadySlideQualityService,
        )
        from tv_app.application.services.data.visual_projection_service import (
            VisualProjectionService,
        )

        if ReadySlideQualityService.projection_is_empty(visual):
            patched = VisualProjectionService.apply_to_block(dict(visual), route)
            visual.update(patched)
        block_type = str(visual.get("type") or "").strip()
        projection_key = _VISUAL_PROJECTION_DEFAULTS.get(block_type)
        if projection_key and not isinstance(visual.get(projection_key), dict):
            # Fallback mínimo se a rota não tiver valueFields.
            visual[projection_key] = visual.get(projection_key) or {}

    def _op_patch_native_config(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        patch = op.get("patch")
        if not isinstance(patch, dict) or not patch:
            raise PresentationPatchError(PresentationOpsContentService.message("patchRequired"))
        unknown = [key for key in patch.keys() if str(key) not in _PATCH_NATIVE_KEYS]
        if unknown:
            raise PresentationPatchError(PresentationOpsContentService.message("patchKeysInvalid"))
        for key in _PATCH_NATIVE_KEYS:
            if key in patch:
                merge_native_config_key(cfg, str(key), patch[key])

    def _op_ensure_brand_logo_on_slide(
        self,
        cfg: dict[str, Any],
        op: dict[str, Any],
        *,
        playlist_id: str,
        actor_user_id: str | None,
        persist: bool,
    ) -> None:
        from tv_app.application.services.data.brand_logo_media_service import (
            BRAND_LOGO_FRAME,
            BRAND_LOGO_ROLE,
            BrandLogoMediaService,
        )

        service = BrandLogoMediaService()
        if service.theme_provides_logo(cfg):
            return
        if service.find_brand_logo_block(cfg):
            return

        variant_raw = str(op.get("variant") or "auto").strip() or "auto"
        variant = (
            service.resolve_variant_for_native(cfg)
            if variant_raw == "auto"
            else variant_raw
        )
        if variant not in ("onDark", "onLight"):
            variant = service.resolve_variant_for_native(cfg)

        # Preview without DB: skip binary seed; still mark intent via placeholder skip.
        if not persist:
            assets = service.list_brand_assets(playlist_id)
            asset = assets.get(variant)
            if not asset:
                # Synthetic preview id — commit path will seed real assetId.
                asset = {"id": f"preview-brand-{variant}"}
        else:
            assets = service.ensure_playlist_assets(
                playlist_id,
                created_by=actor_user_id,
            )
            asset = assets.get(variant)
        if not asset or not asset.get("id"):
            raise PresentationPatchError(
                "Logo Delpi indisponível na biblioteca da programação."
            )

        block_id = f"brand-logo-{variant}"
        blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
        logo_block = {
            "id": block_id,
            "type": "image",
            "role": BRAND_LOGO_ROLE,
            "brandLogoVariant": variant,
            "assetId": str(asset["id"]),
            "frame": dict(BRAND_LOGO_FRAME),
            "style": {"zIndex": 1, "opacity": 0.92},
        }
        next_blocks = [b for b in blocks if isinstance(b, dict) and str(b.get("id")) != block_id]
        next_blocks.append(logo_block)
        cfg["blocks"] = next_blocks

    def _op_add_blank_slide(
        self,
        playlist_id: str,
        op: dict[str, Any],
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        title = str(op.get("title") or "").strip() or "Slide personalizado"
        native_config_payload: dict[str, Any] = {
            "version": 5,
            "headline": "",
            "subtitle": "",
            "blocks": [],
        }
        if isinstance(op.get("background"), dict):
            native_config_payload["background"] = copy.deepcopy(op["background"])
        duration_sec = op.get("durationSec")
        try:
            duration = int(duration_sec) if duration_sec is not None else 30
        except (TypeError, ValueError):
            duration = 30
        payload = {
            "slideType": "native",
            "title": title,
            "nativeScreenKey": "custom_message",
            "nativeConfig": native_config_payload,
            "durationSec": duration,
        }
        if not persist:
            return {
                "id": None,
                "preview": True,
                **payload,
            }
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        slide = self._repo.add_slide(
            UUID(playlist_id),
            payload,
            actor_user_id=actor_user_id,
            reason="presentation_blank_slide",
        )
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="presentation_blank_slide",
        )
        return slide

    def _op_update_slide(
        self,
        playlist_id: str,
        slide_id: str,
        op: dict[str, Any],
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if "title" in op and op["title"] is not None:
            payload["title"] = str(op["title"]).strip()
        if "durationSec" in op:
            payload["durationSec"] = op["durationSec"]
        if "isActive" in op and op["isActive"] is not None:
            payload["isActive"] = bool(op["isActive"])
        if not payload:
            return {"id": slide_id, "preview": not persist, "unchanged": True}
        if not persist:
            return {"id": slide_id, "preview": True, **payload}
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        try:
            slide = self._repo.update_slide(
                UUID(playlist_id),
                UUID(slide_id),
                payload,
                actor_user_id=actor_user_id,
                reason="presentation_update_slide",
            )
        except (SlideNotFoundError, ValueError) as exc:
            raise PresentationPatchError(PresentationOpsContentService.message("slideNotFound")) from exc
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="presentation_update_slide",
        )
        return slide

    def _op_reorder_slides(
        self,
        playlist_id: str,
        op: dict[str, Any],
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        items = op.get("items")
        if not isinstance(items, list) or not items:
            raise PresentationPatchError(PresentationOpsContentService.message("reorderItemsRequired"))
        normalized: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                raise PresentationPatchError(PresentationOpsContentService.message("reorderItemsRequired"))
            item_id = str(item.get("id") or "").strip()
            if not item_id or "sortOrder" not in item:
                raise PresentationPatchError(PresentationOpsContentService.message("reorderItemsRequired"))
            try:
                sort_order = int(item["sortOrder"])
            except (TypeError, ValueError) as exc:
                raise PresentationPatchError(
                    PresentationOpsContentService.message("reorderItemsRequired")
                ) from exc
            normalized.append({"id": item_id, "sortOrder": sort_order})
        if not persist:
            return {"preview": True, "items": normalized}
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        slides = self._repo.reorder_slides(
            UUID(playlist_id),
            normalized,
            actor_user_id=actor_user_id,
            reason="presentation_reorder_slides",
        )
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="presentation_reorder_slides",
        )
        return {"items": normalized, "slides": slides}

    def _op_delete_slide(
        self,
        playlist_id: str,
        slide_id: str,
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        if not persist:
            return {"id": slide_id, "preview": True, "deleted": True}
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        try:
            self._repo.delete_slide(
                UUID(playlist_id),
                UUID(slide_id),
                actor_user_id=actor_user_id,
                reason="presentation_delete_slide",
            )
        except (SlideNotFoundError, ValueError) as exc:
            raise PresentationPatchError(PresentationOpsContentService.message("slideNotFound")) from exc
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="presentation_delete_slide",
        )
        return {"id": slide_id, "deleted": True}

    def _op_upsert_section(
        self,
        playlist_id: str,
        op: dict[str, Any],
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        name = str(op.get("name") or "").strip()
        if not name:
            raise PresentationPatchError(PresentationOpsContentService.message("sectionNameRequired"))
        section_id = str(op.get("sectionId") or "").strip() or None
        if not persist:
            return {
                "id": section_id,
                "preview": True,
                "name": name,
                "updated": bool(section_id),
            }
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        try:
            if section_id:
                section = self._repo.update_section(
                    UUID(playlist_id),
                    UUID(section_id),
                    {"name": name},
                    actor_user_id=actor_user_id,
                    reason="presentation_upsert_section",
                )
            else:
                section = self._repo.add_section(
                    UUID(playlist_id),
                    {"name": name},
                    actor_user_id=actor_user_id,
                    reason="presentation_upsert_section",
                )
        except (SectionNotFoundError, ValueError) as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message("sectionNotFound")
            ) from exc
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="presentation_upsert_section",
        )
        return section

    def _op_delete_section(
        self,
        playlist_id: str,
        op: dict[str, Any],
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        section_id = str(op.get("sectionId") or "").strip()
        if not section_id:
            raise PresentationPatchError(PresentationOpsContentService.message("sectionIdRequired"))
        if not persist:
            return {"id": section_id, "preview": True, "deleted": True}
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        try:
            self._repo.delete_section(
                UUID(playlist_id),
                UUID(section_id),
                actor_user_id=actor_user_id,
                reason="presentation_delete_section",
            )
        except SectionNotFoundError as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message("sectionNotFound")
            ) from exc
        except MainSectionProtectedError as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message("sectionProtected")
            ) from exc
        except ValueError as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message("sectionNotFound")
            ) from exc
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="presentation_delete_section",
        )
        return {"id": section_id, "deleted": True}

    def _op_move_slide_to_section(
        self,
        playlist_id: str,
        slide_id: str,
        op: dict[str, Any],
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        if "sectionId" not in op:
            raise PresentationPatchError(
                PresentationOpsContentService.message("opMissingField", op="move_slide_to_section", field="sectionId")
            )
        section_raw = op.get("sectionId")
        section_id = None if section_raw is None else str(section_raw).strip() or None
        payload = {"sectionId": section_id}
        if not persist:
            return {"id": slide_id, "preview": True, **payload}
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        try:
            slide = self._repo.update_slide(
                UUID(playlist_id),
                UUID(slide_id),
                payload,
                actor_user_id=actor_user_id,
                reason="presentation_move_slide_section",
            )
        except (SlideNotFoundError, ValueError) as exc:
            raise PresentationPatchError(PresentationOpsContentService.message("slideNotFound")) from exc
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="presentation_move_slide_section",
        )
        return slide

    def _op_add_slide_from_preset(
        self,
        playlist_id: str,
        op: dict[str, Any],
        *,
        user: Any,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        preset_key = str(op.get("presetKey") or "").strip()
        if not preset_key:
            raise PresentationPatchError(PresentationOpsContentService.message("presetRequired"))
        try:
            payload = resolve_preset_slide(preset_key)
        except SlidePresetNotFoundError as exc:
            raise PresentationPatchError(
                PresentationOpsContentService.message("presetRequired")
            ) from exc
        branch = str(op.get("branch") or "").strip()
        if branch and payload.get("slideType") == "native":
            native = dict(payload.get("nativeConfig") or {})
            native["branch"] = branch
            payload["nativeConfig"] = native
        if payload.get("slideType") == "native" and payload.get("nativeConfig"):
            cleaned = sanitize_and_hydrate_comunicado_config(
                payload["nativeConfig"], catalog=self._catalog
            )
            validate_comunicado_native_config(cleaned, user=user, catalog=self._catalog)
            payload["nativeConfig"] = cleaned
        if not persist:
            return {
                "id": None,
                "preview": True,
                "presetKey": preset_key,
                "title": payload.get("title"),
                "nativeConfig": payload.get("nativeConfig"),
                "slideType": payload.get("slideType"),
            }
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        slide = self._repo.add_slide(
            UUID(playlist_id),
            payload,
            actor_user_id=actor_user_id,
            reason="presentation_slide_from_preset",
        )
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="presentation_slide_from_preset",
        )
        return slide

    def _op_create_playlist(
        self,
        op: dict[str, Any],
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        name = str(op.get("name") or "").strip()
        if not name:
            raise PresentationPatchError(PresentationOpsContentService.message("playlistNameRequired"))
        description = op.get("description")
        if not persist:
            return {
                "id": None,
                "preview": True,
                "name": name,
                "description": description,
            }
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        playlist = self._repo.create(
            name=name,
            description=str(description) if description is not None else None,
            created_by=actor_user_id,
        )
        notify_presentation_changed(
            playlist_id=str(playlist.get("id") or ""),
            reason="presentation_playlist_created",
        )
        from tv_app.application.services.presentation_change_notifier import (
            notify_playlist_library_changed,
        )

        if actor_user_id and playlist.get("id"):
            notify_playlist_library_changed(
                user_ids=[actor_user_id],
                reason="created",
                playlist_id=str(playlist["id"]),
            )
        seed_presets = op.get("seedPresetKeys")
        seeded: list[dict[str, Any]] = []
        if isinstance(seed_presets, list) and playlist.get("id"):
            for key in seed_presets:
                key_s = str(key or "").strip()
                if not key_s:
                    continue
                try:
                    payload = resolve_preset_slide(key_s)
                    slide = self._repo.add_slide(
                        UUID(str(playlist["id"])),
                        payload,
                        actor_user_id=actor_user_id,
                        reason="presentation_playlist_seed",
                    )
                    seeded.append({"id": slide.get("id"), "presetKey": key_s})
                except SlidePresetNotFoundError:
                    continue
            if seeded:
                notify_presentation_changed(
                    playlist_id=str(playlist["id"]),
                    reason="presentation_playlist_seed",
                )
        playlist["seededSlides"] = seeded
        return playlist

    def _op_re_layer_playlist_filters(
        self,
        native_config: dict[str, Any],
        op: dict[str, Any],
        *,
        playlist_id: str,
        playlist_defaults: dict[str, Any] | None,
        side_effects: dict[str, Any],
    ) -> dict[str, Any] | None:
        from tv_app.application.services.data.filter_relayer_service import apply_relayer

        scope = str(op.get("scope") or "slide").strip().lower()
        if scope not in {"playlist", "slide"}:
            raise PresentationPatchError("re_layer_playlist_filters.scope must be playlist or slide.")
        keys_raw = op.get("keys")
        keys = [str(k) for k in keys_raw] if isinstance(keys_raw, list) else None
        _, next_defaults, promoted = apply_relayer(
            native_config,
            scope=scope,
            keys=keys,
            playlist_defaults=playlist_defaults,
        )
        if not promoted:
            return next_defaults
        if scope == "playlist" and isinstance(next_defaults, dict):
            side_effects["playlist"] = {
                "id": playlist_id,
                "preview": True,
                "dataDefaults": dict(next_defaults),
            }
        return next_defaults

    def _op_apply_published_slide_template(
        self,
        native_config: dict[str, Any],
        op: dict[str, Any],
    ) -> None:
        from uuid import UUID

        from tv_app.application.services.slide_template_library_service import (
            SlideTemplateLibraryService,
            SlideTemplateNotFoundError,
        )

        template_id = str(op.get("templateId") or "").strip()
        template_key = str(op.get("templateKey") or op.get("slug") or "").strip()
        item: dict[str, Any] | None = None
        library = SlideTemplateLibraryService()
        if template_id:
            try:
                item = library.get(UUID(template_id))
            except (ValueError, SlideTemplateNotFoundError) as exc:
                raise PresentationPatchError("Template não encontrado.") from exc
        elif template_key:
            item = library.get_by_key(template_key)
        if not item or str(item.get("status") or "") != "published":
            raise PresentationPatchError("Template publicado não encontrado.")
        tpl_native = item.get("nativeConfig")
        if not isinstance(tpl_native, dict):
            raise PresentationPatchError("Template sem nativeConfig.")
        merged = copy.deepcopy(tpl_native)
        merged.pop("resolved", None)
        native_config.clear()
        native_config.update(merged)
        if "version" not in native_config:
            native_config["version"] = 5

    def _op_patch_playlist_data_defaults(
        self,
        playlist_id: str,
        op: dict[str, Any],
        *,
        persist: bool,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        raw_defaults = op.get("dataDefaults")
        if not isinstance(raw_defaults, dict):
            raise PresentationPatchError(
                PresentationOpsContentService.message("playlistDefaultsRequired")
            )
        replace = bool(op.get("replace"))
        if not persist:
            from tv_app.application.services.tv_date_range_preset_service import (
                merge_period_params_layer,
                normalize_period_params_for_persistence,
            )

            existing = self._playlist_defaults(playlist_id) or {}
            merged = (
                normalize_period_params_for_persistence(raw_defaults)
                if replace
                else merge_period_params_layer(existing, raw_defaults)
            )
            return {
                "id": playlist_id,
                "preview": True,
                "dataDefaults": merged,
            }
        if not actor_user_id:
            raise PresentationPatchError(PresentationOpsContentService.message("missingTarget"))
        from tv_app.application.services.tv_presentation_write_service import (
            PresentationWriteError,
            TvPresentationWriteService,
        )

        writes = TvPresentationWriteService(self._repo)
        try:
            return writes.patch_playlist_data_defaults(
                UUID(playlist_id),
                data_defaults=raw_defaults,
                actor_user_id=actor_user_id,
                replace=replace,
            )
        except PresentationWriteError as exc:
            raise PresentationPatchError(str(exc)) from exc
