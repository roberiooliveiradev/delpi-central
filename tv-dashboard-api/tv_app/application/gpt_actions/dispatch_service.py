"""GPT Actions dispatch — thin orchestration over TV canonical services."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.gpt_actions.capability_surface import build_capability_surface
from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.proposal import create_proposal
from tv_app.application.gpt_actions.proposal_store import get_proposal_store
from tv_app.application.ports import PresentationRepositoryPort
from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.story_digest_service import StoryDigestService
from tv_app.application.services.data.presentation_command_planner_service import (
    PresentationCommandPlannerService,
)
from tv_app.application.services.data.presentation_ops_content_service import PresentationOpsContentService
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.tv_data_config_validation_service import (
    TvDataConfigValidationService,
)
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService
from tv_app.application.services.data.tv_data_route_suggest_service import (
    TvDataRouteSuggestService,
)
from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.presentation_payload_service import PresentationPayloadService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.services.tv_presentation_write_service import TvPresentationWriteService
from tv_app.core.security import TV_READ, TV_WRITE, assert_permission


def _typed_ops(ops: list[Any] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in ops or []:
        if isinstance(raw, dict) and str(raw.get("op") or "").strip():
            out.append(dict(raw))
    return out


class GptActionsDispatchService:
    def __init__(
        self,
        *,
        repo: PresentationRepositoryPort,
        writes: TvPresentationWriteService,
        commit: TvGptCommitService,
        access: PlaylistAccessService | None = None,
        patch: PresentationPatchService | None = None,
        catalog: TvDataRouteCatalogService | None = None,
        validation: TvDataConfigValidationService | None = None,
        preview: TvDataPreviewService | None = None,
        suggest: TvDataRouteSuggestService | None = None,
    ) -> None:
        self._repo = repo
        self._writes = writes
        self._access = access or PlaylistAccessService()
        self._patch = patch or PresentationPatchService()
        self._commit = commit
        self._catalog = catalog or TvDataRouteCatalogService()
        self._validation = validation or TvDataConfigValidationService()
        self._preview = preview or TvDataPreviewService()
        self._suggest = suggest or TvDataRouteSuggestService(self._catalog)
        self._present = PresentationPayloadService()

    def _actor(self, user: Any) -> str:
        actor = self._access.actor_id(user)
        if not actor:
            raise GptActionsError(
                "Usuário não identificado.",
                code="AUTHENTICATION_REQUIRED",
                status_code=401,
            )
        return actor

    def get_catalog(self, *, user: Any) -> dict[str, Any]:
        assert_permission(user, TV_WRITE)
        doc = PresentationOpsContentService.capability_catalog_document()
        from tv_app.application.services.data.display_format_service import DisplayFormatService

        doc["displayFormatCatalog"] = [
            {"formatId": entry["formatId"], "spec": entry["spec"]}
            for entry in DisplayFormatService.format_catalog_entries()
        ]
        doc["capability_surface"] = build_capability_surface()
        return doc

    def list_playlists(
        self,
        *,
        user: Any,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        from tv_app.application.gpt_actions.response_compact import (
            project_playlist_list_item,
        )
        from tv_app.application.services.editor_focus_store import editor_focus_store

        assert_permission(user, TV_READ)
        actor = self._actor(user)
        items = self._repo.list_playlists(
            limit=limit,
            offset=offset,
            user_id=actor,
            include_all=False,
        )
        projected: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if actor and item.get("ownerUserId") == actor:
                role = "owner"
            elif actor:
                share = self._repo.get_share_role(UUID(item["id"]), actor)
                role = share or "viewer"
            else:
                role = "viewer"
            projected.append(project_playlist_list_item(item, access_role=role))
        # editorFocus first — continuous_review / "esta programação" must not miss it
        # when the items array is long.
        out: dict[str, Any] = {"limit": limit, "offset": offset, "items": projected}
        focus = editor_focus_store.get_for_user(actor) if actor else None
        if focus:
            out = {"editorFocus": focus, **out}
        return out

    def get_playlist_context(
        self,
        *,
        user: Any,
        playlist_id: str,
        include_preview: bool = False,
        preview_slide_id: str | None = None,
        scope: str | None = None,
        object_query: str | None = None,
        object_types: str | None = None,
        block_cursor: str | int | None = None,
        block_limit: int | None = None,
    ) -> dict[str, Any]:
        from tv_app.application.gpt_actions.response_compact import (
            exceeds_actions_budget,
            iter_block_index_items,
            pick_focus_slide_id,
            project_block_index,
            project_data_sources_from_slide,
            project_editor_focus_context,
            project_media_inventory,
            project_object_matches,
            project_playlist_summary,
            project_slide_detail,
            project_slide_index_row,
            resolve_selected_data_source_id,
        )
        from tv_app.application.services.data.filter_digest_service import (
            FilterDigestService,
        )
        from tv_app.application.services.data.layout_digest_service import (
            LayoutDigestService,
        )
        from tv_app.application.services.data.slide_preview_render_service import (
            get_slide_preview_render_service,
        )
        from tv_app.application.services.editor_focus_store import editor_focus_store

        assert_permission(user, TV_READ)
        pid = UUID(str(playlist_id))
        access = self._access.resolve(pid, user)
        if not access.can_read:
            raise GptActionsError(
                "Programação não encontrada.",
                code="RESOURCE_NOT_FOUND",
                status_code=404,
            )
        playlist = access.playlist or self._writes.get_playlist(pid)
        slides = self._writes.list_slides(pid)
        sections = self._writes.list_sections(pid)
        revision = self._writes.get_revision(pid)
        actor = self._actor(user)
        scope_key = str(scope or "full").strip().lower()
        if scope_key not in {"full", "editorfocus", "editor_focus"}:
            scope_key = "full"
        focused_scope = scope_key in {"editorfocus", "editor_focus"}

        layout_digest = (
            None if focused_scope else LayoutDigestService.digest_slides(slides)
        )
        programming_defaults = (
            (playlist.get("dataDefaults") or {}) if isinstance(playlist, dict) else {}
        )
        filter_digest = (
            None
            if focused_scope
            else FilterDigestService.digest_playlist(
                programming_defaults=programming_defaults,
                slides=slides,
            )
        )

        editor_focus: dict[str, Any] | None = None
        if actor:
            focus = editor_focus_store.get_for_user_playlist(actor, str(pid))
            if focus:
                editor_focus = {
                    "slideId": focus.get("slideId"),
                    "selectedIds": focus.get("selectedIds") or [],
                    "updatedAt": focus.get("updatedAt"),
                    "stale": bool(focus.get("stale")),
                }

        focus_slide_id = pick_focus_slide_id(
            [s for s in slides if isinstance(s, dict)],
            editor_focus=editor_focus,
            preview_slide_id=preview_slide_id,
        )
        slide_index = [
            project_slide_index_row(s) for s in slides if isinstance(s, dict)
        ]
        detail_slide = next(
            (
                s
                for s in slides
                if isinstance(s, dict) and str(s.get("id") or "") == str(focus_slide_id or "")
            ),
            None,
        )
        if detail_slide is None and slides:
            detail_slide = slides[0] if isinstance(slides[0], dict) else None

        data_sources = project_data_sources_from_slide(
            detail_slide if isinstance(detail_slide, dict) else None
        )
        selected_ds = resolve_selected_data_source_id(
            editor_focus=editor_focus,
            data_sources=data_sources,
        )
        if editor_focus is not None and selected_ds:
            editor_focus = {**editor_focus, "selectedDataSourceId": selected_ds}

        native_for_index = (
            detail_slide.get("nativeConfig")
            if isinstance(detail_slide, dict)
            and isinstance(detail_slide.get("nativeConfig"), dict)
            else {}
        )
        focus_sid = (
            str(detail_slide.get("id"))
            if isinstance(detail_slide, dict) and detail_slide.get("id")
            else None
        )
        block_index = project_block_index(
            native_for_index,
            slide_id=focus_sid,
            revision=revision,
            cursor=block_cursor,
            limit=block_limit,
            object_types=object_types,
        )
        object_matches = project_object_matches(
            iter_block_index_items(native_for_index, object_types=object_types),
            object_query=object_query,
            object_types=object_types,
        )

        if focused_scope:
            return project_editor_focus_context(
                playlist=playlist if isinstance(playlist, dict) else {},
                slides_index=slide_index,
                detail_slide=detail_slide if isinstance(detail_slide, dict) else None,
                data_sources=data_sources,
                selected_data_source_id=selected_ds,
                sections=sections,
                access_role=access.level,
                revision=revision,
                editor_focus=editor_focus,
                block_index=block_index,
                object_matches=object_matches,
            )

        out: dict[str, Any] = {
            "scope": "full",
            "playlist": project_playlist_summary(playlist if isinstance(playlist, dict) else {}),
            "slides": slide_index,
            "focusedSlide": project_slide_detail(detail_slide)
            if isinstance(detail_slide, dict)
            else None,
            "focusedSlideId": str(detail_slide.get("id"))
            if isinstance(detail_slide, dict)
            else None,
            "dataSources": data_sources,
            "sections": sections,
            "accessRole": access.level,
            "currentRevision": revision,
            "layoutDigest": layout_digest,
            "filterDigest": filter_digest,
            "designAudit": DesignIntelligenceService.design_audit(
                detail_slide.get("nativeConfig") if isinstance(detail_slide, dict) else None
            ),
            "storyDigest": StoryDigestService.digest(slides),
            "localDraftCoordination": "unavailable_external",
            "note": (
                "slides[] is a compact index (no nativeConfig). "
                "focusedSlide has full nativeConfig for the editorFocus/preview/first slide. "
                "dataSources[] lists id/label/operationId/params for the focused slide. "
                "If this response is too large, the API auto-downgrades to scope=editorFocus "
                "and retains blockIndex + dataSources[] (no invented blockIds). "
                "Pass scope=editorFocus explicitly for compact addressability without nativeConfig."
            ),
        }
        if editor_focus:
            out = {"editorFocus": editor_focus, **out}

        try:
            from tv_app.application.services.data.brand_logo_media_service import (
                BrandLogoMediaService,
            )

            media_svc = BrandLogoMediaService()
            brand = media_svc.list_brand_assets(pid)
            brand_proj = {
                variant: {
                    "assetId": asset.get("id"),
                    "originalName": asset.get("originalName"),
                    "mimeType": asset.get("mimeType"),
                }
                for variant, asset in brand.items()
            }
            playlist_assets = [
                {
                    "assetId": item.get("id"),
                    "originalName": item.get("originalName"),
                    "mimeType": item.get("mimeType"),
                    "mediaKind": item.get("mediaKind"),
                }
                for item in media_svc.list_playlist_assets(pid)
                if isinstance(item, dict) and item.get("id")
            ]
            out["mediaInventory"] = project_media_inventory(
                brand_logos=brand_proj,
                assets=playlist_assets,
            )
        except Exception:
            out["mediaInventory"] = {
                "brandLogos": {},
                "assets": [],
                "assetsTotal": 0,
                "assetsTruncated": False,
                "note": "unavailable",
            }

        slide_preview: dict[str, Any] | None = None
        if include_preview:
            target_id = str(out.get("focusedSlideId") or "").strip()
            slide = detail_slide
            if not slide or str(slide.get("id")) != target_id:
                slide = next(
                    (
                        s
                        for s in slides
                        if isinstance(s, dict) and str(s.get("id")) == target_id
                    ),
                    None,
                )
            if not slide:
                raise GptActionsError(
                    "Slide não encontrado para prévia.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                )
            slide_preview = get_slide_preview_render_service().build_preview_payload(
                playlist_id=str(pid),
                slide_id=str(slide["id"]),
                revision=revision,
                native_config=slide.get("nativeConfig")
                if isinstance(slide.get("nativeConfig"), dict)
                else {},
                title=str(slide.get("title") or "") or None,
            )
            out["slidePreview"] = slide_preview

        # Custom GPT Actions rejects oversized tool responses (ResponseTooLargeError).
        # Auto-downgrade keeps dataSources[] + blockIndex so existing-object mutation can proceed.
        if exceeds_actions_budget(out):
            return project_editor_focus_context(
                playlist=playlist if isinstance(playlist, dict) else {},
                slides_index=slide_index,
                detail_slide=detail_slide if isinstance(detail_slide, dict) else None,
                data_sources=data_sources,
                selected_data_source_id=selected_ds,
                sections=sections,
                access_role=access.level,
                revision=revision,
                editor_focus=editor_focus,
                scope_downgraded=True,
                slide_preview=slide_preview,
                block_index=block_index,
                object_matches=object_matches,
            )
        return out

    def get_slide_preview_png(
        self,
        *,
        user: Any | None,
        token: str,
    ) -> tuple[bytes, dict[str, Any]]:
        """Serve cached schematic PNG. Signed token is AuthZ; Bearer optional + checked."""
        from tv_app.application.services.data.slide_preview_render_service import (
            get_slide_preview_render_service,
        )
        from tv_app.application.services.data.slide_preview_token import (
            parse_slide_preview_token,
        )

        try:
            claims = parse_slide_preview_token(token)
        except ValueError as exc:
            code = "PREVIEW_TOKEN_EXPIRED" if "expired" in str(exc) else "PREVIEW_TOKEN_INVALID"
            raise GptActionsError(
                "Prévia expirada ou inválida.",
                code=code,
                status_code=404,
            ) from exc

        pid = UUID(claims["playlistId"])
        if user is not None:
            assert_permission(user, TV_READ)
            access = self._access.resolve(pid, user)
            if not access.can_read:
                raise GptActionsError(
                    "Programação não encontrada.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                )

        slides = self._writes.list_slides(pid)
        slide = next(
            (s for s in slides if isinstance(s, dict) and str(s.get("id")) == claims["slideId"]),
            None,
        )
        if not slide:
            raise GptActionsError(
                "Slide não encontrado.",
                code="RESOURCE_NOT_FOUND",
                status_code=404,
            )
        cache_key = str(claims.get("cacheKey") or "").strip()
        if cache_key:
            png = get_slide_preview_render_service().read_if_cached(
                slide_id=str(slide["id"]),
                revision=cache_key,
            )
            if not png:
                raise GptActionsError(
                    "Prévia do candidato expirou. Refaça gpt_preview_change.",
                    code="PREVIEW_REVISION_STALE",
                    status_code=409,
                )
            return png, {
                "playlistId": claims["playlistId"],
                "slideId": claims["slideId"],
                "revision": cache_key,
                "candidate": True,
            }
        current_rev = str(self._writes.get_revision(pid) or "")
        token_rev = str(claims.get("revision") or "")
        if token_rev and current_rev and token_rev != current_rev:
            raise GptActionsError(
                "Prévia desatualizada (revision). Peça gpt_get_playlist_context com includePreview.",
                code="PREVIEW_REVISION_STALE",
                status_code=409,
            )
        png = get_slide_preview_render_service().get_or_render(
            slide_id=str(slide["id"]),
            revision=current_rev or token_rev,
            native_config=slide.get("nativeConfig")
            if isinstance(slide.get("nativeConfig"), dict)
            else {},
            title=str(slide.get("title") or "") or None,
        )
        return png, {
            "playlistId": claims["playlistId"],
            "slideId": claims["slideId"],
            "revision": current_rev or token_rev,
        }
    def search_data_routes(
        self,
        *,
        user: Any,
        query: str | None = None,
        limit: int = 8,
        category: str | None = None,
    ) -> dict[str, Any]:
        from tv_app.application.gpt_actions.data_route_gpt_support import project_route_for_gpt

        assert_permission(user, TV_READ)
        q = str(query or "").strip()
        if not q:
            raise GptActionsError(
                "Informe query com a intenção de negócio (ex.: otd comercial). "
                "Listagem completa de rotas não é suportada nesta Action.",
                code="QUERY_REQUIRED",
                status_code=422,
            )
        cap = max(1, min(int(limit or 8), 20))
        result = self._suggest.suggest(
            query=q,
            limit=cap,
            category=str(category or "").strip() or None,
        )
        raw_items = result.get("suggestions") if isinstance(result, dict) else []
        if not isinstance(raw_items, list):
            raw_items = []
        items = [
            project_route_for_gpt(item)
            for item in raw_items
            if isinstance(item, dict)
        ]
        return {
            "items": items,
            "query": q,
            "category": str(category or "").strip() or None,
            "total": len(items),
            "degraded": False,
            "searchMissDoesNotProveAbsence": True,
            "refineHints": [
                "Refine com domínio + indicador (ex.: otd comercial, rol por filial).",
                "Use apenas operationId retornado; miss não prova ausência.",
            ]
            if not items
            else [],
        }

    def preview_data_block(
        self,
        *,
        user: Any,
        body: dict[str, Any],
        authorization: str | None,
    ) -> dict[str, Any]:
        from tv_app.application.gpt_actions.data_route_gpt_support import (
            build_preview_block_from_route,
            validate_route_params,
        )

        assert_permission(user, TV_READ)
        playlist_id = str(body.get("playlistId") or "").strip()
        playlist_defaults = body.get("playlistDefaults")
        if playlist_id:
            try:
                pid = UUID(playlist_id)
            except ValueError as exc:
                raise GptActionsError(
                    "playlistId inválido.",
                    code="INVALID_CHANGE",
                    status_code=422,
                ) from exc
            access = self._access.resolve(pid, user)
            if not access.can_read:
                raise GptActionsError(
                    "Programação não encontrada.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                )
            if not isinstance(playlist_defaults, dict):
                defaults = (access.playlist or {}).get("dataDefaults")
                playlist_defaults = defaults if isinstance(defaults, dict) else {}

        operation_id = str(body.get("operationId") or "").strip()
        block_in = body.get("block") if isinstance(body.get("block"), dict) else None
        native_in = body.get("nativeConfig") if isinstance(body.get("nativeConfig"), dict) else None
        route: dict[str, Any] | None = None

        if operation_id:
            route = self._catalog.get_route(operation_id)
            if not route:
                raise GptActionsError(
                    f"operationId não está no catálogo TV allowlist: {operation_id}",
                    code="UNKNOWN_OPERATION",
                    status_code=422,
                )
            try:
                params = validate_route_params(
                    route,
                    body.get("params") if isinstance(body.get("params"), dict) else {},
                )
            except ValueError as exc:
                token = str(exc)
                if token.startswith("PARAM_REQUIRED:"):
                    parts = token.split(":")
                    raise GptActionsError(
                        f"Parâmetro obrigatório ausente: {parts[2] if len(parts) > 2 else parts[1]}",
                        code="PARAM_REQUIRED",
                        status_code=422,
                        details={"field": parts[1] if len(parts) > 1 else None},
                    ) from exc
                if token.startswith("PARAM_INVALID:"):
                    parts = token.split(":")
                    raise GptActionsError(
                        f"Parâmetro inválido: {parts[1] if len(parts) > 1 else token}",
                        code="PARAM_INVALID",
                        status_code=422,
                        details={"raw": token},
                    ) from exc
                raise GptActionsError(token, code="INVALID_CHANGE", status_code=422) from exc
            block = build_preview_block_from_route(route, params=params)
            native_config: dict[str, Any] = {"version": 1, "blocks": [block]}
        elif block_in is not None:
            block = block_in
            native_config = native_in or {"version": 1, "blocks": [block]}
        else:
            raise GptActionsError(
                "Informe operationId+params ou block+nativeConfig.",
                code="INVALID_CHANGE",
                status_code=422,
            )

        try:
            cfg = self._validation.sanitize(native_config)
            block = self._preview.preview_block(
                block,
                native_config=cfg,
                authorization=authorization,
                user=user,
                playlist_defaults=playlist_defaults if isinstance(playlist_defaults, dict) else None,
                force_refresh=bool(body.get("forceRefresh")),
                target_step_name=body.get("targetStepName"),
                preview_options=body.get("previewOptions")
                if isinstance(body.get("previewOptions"), dict)
                else None,
            )
        except ValueError as exc:
            raise GptActionsError(str(exc), code="INVALID_CHANGE", status_code=422) from exc
        except Exception as exc:  # noqa: BLE001
            raise GptActionsError(
                str(exc),
                code="UPSTREAM_FAILURE",
                status_code=502,
                retryable=True,
            ) from exc

        join_hints = self._join_hints_for_preview(block, body=body, route=route)
        format_hints = self._format_hints_for_route(route)
        rows = self._rows_from_preview_block(block)
        digest = DesignIntelligenceService.semantic_digest(
            rows,
            columns=self._columns_from_preview_block(block),
        )
        dominant = None
        if playlist_id:
            story = StoryDigestService.digest(self._writes.list_slides(pid))
            dominant = StoryDigestService.dominant_family(story)
        response = {
            "block": block,
            "persisted": False,
            "operationId": operation_id or None,
            "joinHints": join_hints,
            "formatHints": format_hints,
            "semanticDigest": digest,
            "visualRecommendation": DesignIntelligenceService.visual_recommendation(
                digest,
                dominant_visual_family=dominant,
            ),
        }
        # Transform/binding failure nunca é dataset vazio: erro tipado no topo do
        # payload para o caller não tratar preview quebrado como sucesso.
        resolved = block.get("resolved") if isinstance(block, dict) else None
        if isinstance(resolved, dict):
            transform_error = resolved.get("transformError")
            if isinstance(transform_error, dict):
                response["ok"] = False
                response["error"] = {
                    "code": transform_error.get("code") or "m.execution_error",
                    "message": str(resolved.get("error") or transform_error.get("message") or ""),
                    "blockId": str(block.get("id") or "") or None,
                    "stage": "transform",
                }
            elif resolved.get("error"):
                response["ok"] = False
                response["error"] = {
                    "code": "DATA_RESOLUTION_FAILED",
                    "message": str(resolved.get("error")),
                    "blockId": str(block.get("id") or "") or None,
                    "stage": "resolution",
                }
        return response

    @staticmethod
    def _columns_from_preview_block(block: dict[str, Any]) -> list[str]:
        resolved = block.get("resolved") if isinstance(block.get("resolved"), dict) else {}
        for key in ("columns", "schemaColumns", "fields"):
            raw = resolved.get(key) if resolved else None
            if isinstance(raw, list) and raw:
                return [str(item) for item in raw if str(item).strip()]
        rows = resolved.get("rows") if resolved else None
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return [str(k) for k in rows[0].keys()]
        return []

    @staticmethod
    def _rows_from_preview_block(block: dict[str, Any]) -> list[dict[str, Any]]:
        resolved = block.get("resolved") if isinstance(block.get("resolved"), dict) else {}
        rows = resolved.get("rows") if isinstance(resolved, dict) else None
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
        chart = resolved.get("chart") if isinstance(resolved, dict) else None
        if isinstance(chart, dict) and isinstance(chart.get("points"), list):
            return [row for row in chart["points"] if isinstance(row, dict)]
        return []

    def _join_hints_for_preview(
        self,
        block: dict[str, Any],
        *,
        body: dict[str, Any],
        route: dict[str, Any] | None,
    ) -> dict[str, Any]:
        from tv_app.application.services.data.join_plan_service import JoinPlanService

        left_cols = self._columns_from_preview_block(block)
        sibling = body.get("siblingColumns")
        right_cols = (
            [str(c) for c in sibling if str(c).strip()]
            if isinstance(sibling, list)
            else None
        )
        proposal = None
        if left_cols and right_cols:
            proposal = JoinPlanService.propose(
                left_columns=left_cols, right_columns=right_cols
            )
        candidates = JoinPlanService.candidate_keys_from_columns(left_cols)
        payload: dict[str, Any] = {
            "candidateKeys": candidates,
            "preferredKeyVocabulary": list(JoinPlanService.preferred_keys()),
        }
        if proposal is not None and proposal.is_usable:
            payload["proposal"] = proposal.to_dict()
        if route:
            payload["operationId"] = route.get("operationId")
        return payload

    @staticmethod
    def _format_hints_for_route(route: dict[str, Any] | None) -> list[dict[str, Any]]:
        from tv_app.application.services.data.display_format_hints_service import (
            DisplayFormatHintsService,
        )

        if not isinstance(route, dict):
            return []
        field_types = route.get("valueFieldTypes")
        if not isinstance(field_types, dict):
            return []
        out: list[dict[str, Any]] = []
        for field_key, field_type in field_types.items():
            hint = DisplayFormatHintsService.resolve(
                field_key=str(field_key),
                field_type=str(field_type or ""),
            )
            if hint is None:
                continue
            row = hint.to_dict()
            row["field"] = str(field_key)
            out.append(row)
        return out

    def suggest_change(
        self,
        *,
        user: Any,
        message: str,
        host_context: dict[str, Any] | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        assert_permission(user, TV_WRITE)
        plan = PresentationCommandPlannerService.plan(
            message=message,
            host_context=host_context if isinstance(host_context, dict) else {},
            user=user,
            authorization=authorization,
        )
        return PresentationCommandPlannerService.to_suggest_payload(plan)

    def _candidate_preview(
        self,
        *,
        playlist_id: str,
        slide_id: str,
        native_config: dict[str, Any] | None,
        revision: Any,
    ) -> dict[str, Any] | None:
        if not playlist_id or not slide_id or not isinstance(native_config, dict):
            return None
        before_cfg: dict[str, Any] | None = None
        try:
            slides = self._writes.list_slides(UUID(playlist_id))
        except Exception:
            slides = []
        for slide in slides:
            if isinstance(slide, dict) and str(slide.get("id") or "") == slide_id:
                raw = slide.get("nativeConfig")
                before_cfg = raw if isinstance(raw, dict) else None
                break
        before = DesignIntelligenceService.design_audit(before_cfg)
        after = DesignIntelligenceService.design_audit(native_config)
        before_ids = {str(item.get("id")) for item in before.get("issues") or []}
        after_issues = [item for item in after.get("issues") or [] if isinstance(item, dict)]
        after_ids = {str(item.get("id")) for item in after_issues}
        from tv_app.application.services.data.slide_preview_render_service import (
            get_slide_preview_render_service,
        )

        rendered = get_slide_preview_render_service().build_candidate_preview(
            playlist_id=playlist_id,
            slide_id=slide_id,
            revision=revision,
            native_config=native_config,
        )
        return {
            "previewUrl": rendered.get("previewUrl"),
            "designAudit": after,
            "fixedIssues": [
                item
                for item in before.get("issues") or []
                if isinstance(item, dict) and str(item.get("id")) not in after_ids
            ],
            "introducedIssues": [
                item for item in after_issues if str(item.get("id")) not in before_ids
            ],
            "remainingIssues": after_issues,
            "persisted": False,
        }

    def preview_change(
        self,
        *,
        user: Any,
        target: dict[str, Any] | None,
        ops: list[Any],
        catalog_version: str | None,
        authorization: str | None,
        commit_now: bool = False,
        confirmation: dict[str, Any] | bool | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        assert_permission(user, TV_WRITE)
        actor = self._actor(user)
        playlist_id = str((target or {}).get("playlistId") or "").strip()
        if playlist_id:
            access = self._access.resolve(UUID(playlist_id), user)
            if not access.can_edit:
                raise GptActionsError(
                    "Programação não encontrada.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                )
        typed_ops = _typed_ops(ops)
        envelope = {
            "target": target if isinstance(target, dict) else {},
            "ops": typed_ops,
            "catalogVersion": str(
                catalog_version or PresentationOpsContentService.catalog_version()
            ).strip(),
        }
        try:
            result = self._patch.preview(
                envelope,
                user=user,
                authorization=authorization,
                include_fingerprint=True,
            )
        except PresentationPatchError as exc:
            code = str(getattr(exc, "code", None) or "INVALID_CHANGE").strip() or "INVALID_CHANGE"
            raise GptActionsError(
                str(exc),
                code=code,
                status_code=422,
                details=getattr(exc, "details", None) or None,
            ) from exc

        # Prefer compiler-ordered ops for the proposal (source of truth for ACT).
        ordered_ops = result.get("orderedOps")
        stored_ops = (
            [op for op in ordered_ops if isinstance(op, dict)]
            if isinstance(ordered_ops, list) and ordered_ops
            else typed_ops
        )
        # appliedOps from patch service is list[str] — expose as operationNames only.
        applied_names = result.get("appliedOps") or []
        operation_names = [
            str(name) for name in applied_names if isinstance(name, str) and name.strip()
        ]
        base_revision = result.get("baseRevision")
        base_revision_int = int(base_revision) if base_revision is not None else None
        # Policy authority is the Copilot catalog — not patch-service echo.
        policy = PresentationOpsContentService.aggregate_ops_policy(stored_ops)
        confirmation_policy = str(policy["confirmationPolicy"] or "direct").strip().lower()
        proposal = create_proposal(
            actor_id=actor,
            target=envelope["target"],
            ops=stored_ops,
            operation_names=operation_names,
            catalog_version=envelope["catalogVersion"],
            base_revision=base_revision_int,
            risk=policy["risk"],
            confirmation_policy=confirmation_policy,
            side_effect_hints=list(policy["sideEffectHints"] or []),
            meta={
                "diff": result.get("diff"),
                "fingerprint": result.get("fingerprint"),
                "compileDigest": result.get("compileDigest"),
                "dependencyOrder": result.get("dependencyOrder"),
                "aliasKeys": sorted((result.get("aliasMap") or {}).keys())
                if isinstance(result.get("aliasMap"), dict)
                else [],
                "nativeConfig": result.get("nativeConfig"),
                "nativeConfigsBySlide": result.get("nativeConfigsBySlide")
                if isinstance(result.get("nativeConfigsBySlide"), dict)
                else None,
            },
        )
        proposal_handle = get_proposal_store().put(proposal)
        preview_payload = {
            "target": envelope["target"],
            "ops": stored_ops,
            "operationNames": operation_names,
            "catalogVersion": envelope["catalogVersion"],
            "baseRevision": base_revision,
            "risk": policy["risk"],
            "confirmationPolicy": policy["confirmationPolicy"],
            "sideEffectHints": policy["sideEffectHints"],
            "diff": result.get("diff"),
            "fingerprint": result.get("fingerprint"),
            "proposal_handle": proposal_handle,
            "proposal": proposal.to_public_dict(),
            "confirmation_requirement": proposal.confirmation_requirement,
            "canCommit": True,
            "persisted": False,
            "message": result.get("message"),
            "dependencyOrder": result.get("dependencyOrder"),
            "aliasMap": result.get("aliasMap"),
            "compileDigest": result.get("compileDigest"),
            "orderedOps": stored_ops,
        }
        candidate = self._candidate_preview(
            playlist_id=playlist_id,
            slide_id=str((envelope["target"] or {}).get("slideId") or ""),
            native_config=result.get("nativeConfig")
            if isinstance(result.get("nativeConfig"), dict)
            else None,
            revision=base_revision,
        )
        if candidate is not None:
            preview_payload["candidatePreview"] = candidate

        from tv_app.application.gpt_actions.response_compact import (
            project_mutation_actions_payload,
        )

        if not commit_now:
            return project_mutation_actions_payload(preview_payload)

        if confirmation_policy == "confirm":
            preview_payload["message"] = (
                "commit_now ignorado: confirmationPolicy=confirm exige "
                "confirmação explícita do usuário e gpt_commit_change com o "
                "proposal_handle exato deste preview."
            )
            preview_payload["commit_now_applied"] = False
            return project_mutation_actions_payload(preview_payload)

        if not TvGptCommitService._normalize_confirmation(confirmation):
            raise GptActionsError(
                "commit_now=true exige confirmation.confirmed=true "
                "(policy direct). Nada foi gravado.",
                code="CONFIRMATION_REQUIRED",
                status_code=400,
            )

        key = str(idempotency_key or "").strip()
        if not key:
            raise GptActionsError(
                "commit_now=true exige Idempotency-Key (header) ou "
                "idempotency_key no body.",
                code="INVALID_CHANGE",
                status_code=422,
            )

        outcome = self._commit.commit(
            user=user,
            actor_id=actor,
            proposal_handle=proposal_handle,
            confirmation=confirmation,
            idempotency_key=key,
            authorization=authorization,
        )
        return project_mutation_actions_payload(
            {
                **preview_payload,
                **outcome,
                "proposal_handle": proposal_handle,
                "commit_now_applied": True,
                "persisted": bool(outcome.get("persisted", True)),
            }
        )

    def commit_change(
        self,
        *,
        user: Any,
        proposal_handle: str,
        confirmation: dict[str, Any] | bool | None,
        idempotency_key: str,
        authorization: str | None,
    ) -> dict[str, Any]:
        assert_permission(user, TV_WRITE)
        actor = self._actor(user)
        from tv_app.application.gpt_actions.response_compact import (
            project_mutation_actions_payload,
        )

        return project_mutation_actions_payload(
            self._commit.commit(
                user=user,
                actor_id=actor,
                proposal_handle=proposal_handle,
                confirmation=confirmation,
                idempotency_key=idempotency_key,
                authorization=authorization,
            )
        )
