"""GPT Actions dispatch — thin orchestration over TV canonical services."""

from __future__ import annotations

import copy
import hashlib
import json
import logging
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
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    TvPresentationWriteService,
)
import tv_app.core.security as core_security
from tv_app.core.security import (
    TV_TEMPLATES_MANAGE,
    TV_READ,
    TV_WRITE,
    GovernedWriteAuthzError,
    assert_permission,
    can,
)

logger = logging.getLogger(__name__)


def _typed_ops(ops: list[Any] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in ops or []:
        if isinstance(raw, dict) and str(raw.get("op") or "").strip():
            out.append(dict(raw))
    return out


# focused data_source inspection bounds — bounded observability, never a dump.
_INSPECT_MAX_COLUMNS = 40
_INSPECT_MAX_RESULT_ROWS = 10
_INSPECT_MAX_SAMPLE_FIELDS = 20


def _legacy_merge_source_refs(transform: Any) -> list[str]:
    """Raw `sourceId` refs of v1 merge steps (resolved or not)."""
    if not isinstance(transform, dict):
        return []
    steps = transform.get("steps")
    if not isinstance(steps, list):
        return []
    refs: list[str] = []
    for step in steps:
        if isinstance(step, dict) and str(step.get("op") or "") == "merge":
            ref = str(step.get("sourceId") or "").strip()
            if ref:
                refs.append(ref)
    return refs


def _merge_consumed_fields(
    transform: Any,
    source_id: str,
    ref_to_source: dict[str, str],
) -> list[str] | None:
    """Fields consumed from `source_id` by v1 merge steps — `rightKey` +
    declared `columns`. `None` when the contract takes all columns or the
    transform is v2 (field consumption not statically declared)."""
    if not isinstance(transform, dict):
        return None
    steps = transform.get("steps")
    if not isinstance(steps, list):
        return None
    fields: list[str] = []
    takes_all = False
    for step in steps:
        if not isinstance(step, dict) or str(step.get("op") or "") != "merge":
            continue
        ref = str(step.get("sourceId") or "").strip()
        if ref_to_source.get(ref) != source_id:
            continue
        key = str(step.get("rightKey") or "").strip()
        if key and key not in fields:
            fields.append(key)
        columns = step.get("columns")
        if isinstance(columns, list):
            for col in columns:
                col_str = str(col or "").strip()
                if col_str and col_str not in fields:
                    fields.append(col_str)
        else:
            takes_all = True
    if not fields and not takes_all:
        return []
    return None if takes_all else fields


def _expression_context_refs(params: dict[str, Any]) -> set[str]:
    """Context identifiers (`today`, `now`, `param.*`) referenced by expression
    params — static AST walk only, never evaluation."""
    refs: set[str] = set()

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("kind") == "identifier":
                value = str(node.get("value") or "").strip()
                if value:
                    refs.add(value)
            children = node.get("children")
            if isinstance(children, list):
                for child in children:
                    _walk(child)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    for value in params.values():
        if isinstance(value, dict) and isinstance(value.get("expression"), dict):
            spec = value["expression"]
            _walk(spec.get("expression") if isinstance(spec.get("expression"), dict) else spec)
    return refs


def _inspect_source_table(resolved: dict[str, Any]) -> dict[str, Any] | None:
    """Post-transform table de um bloco resolvido — `_queryTable` (tabela
    materializada da DAG quando sobrevive) com fallback para `resolved.table`
    (presentation bounded, mesma tabela transformada)."""
    dag_table = resolved.get("_queryTable")
    if isinstance(dag_table, dict) and isinstance(dag_table.get("rows"), list):
        return {
            "columns": [str(c) for c in (dag_table.get("columns") or [])],
            "rows": dag_table["rows"],
        }
    table = resolved.get("table")
    if isinstance(table, dict) and isinstance(table.get("rows"), list):
        return {
            "columns": [
                str(c.get("key") if isinstance(c, dict) else c)
                for c in (table.get("columns") or [])
            ],
            "rows": table["rows"],
        }
    return None


def _inspect_table_sample(
    table: Any,
    fields: list[str] | None,
) -> tuple[int, dict[str, Any] | None]:
    """(rowCount, first-row field sample) — only fields the transform consumes
    when declared; otherwise all columns bounded. `None` sample when no rows."""
    if not isinstance(table, dict):
        return 0, None
    rows = table.get("rows") or []
    row_count = len(rows)
    first = rows[0] if rows and isinstance(rows[0], dict) else None
    if first is None:
        return row_count, None
    columns = fields if isinstance(fields, list) and fields else [
        str(c) for c in (table.get("columns") or [])
    ]
    sample = {
        col: first.get(col)
        for col in columns[: _INSPECT_MAX_SAMPLE_FIELDS]
        if col in first
    }
    return row_count, sample


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
        solutions: Any | None = None,
        history: Any | None = None,
        consent: Any | None = None,
    ) -> None:
        self._repo = repo
        self._consent = consent
        self._writes = writes
        self._access = access or PlaylistAccessService()
        self._patch = patch or PresentationPatchService()
        self._commit = commit
        self._catalog = catalog or TvDataRouteCatalogService()
        self._validation = validation or TvDataConfigValidationService()
        self._preview = preview or TvDataPreviewService()
        self._suggest = suggest or TvDataRouteSuggestService(self._catalog)
        self._solutions = solutions
        self._history = history
        self._present = PresentationPayloadService()
        # (userId, slideId, revision) → last visual_capture_request send (mono).
        self._capture_request_last: dict[tuple[str, str, str], float] = {}

    def _actor(self, user: Any) -> str:
        actor = self._access.actor_id(user)
        if not actor:
            raise GptActionsError(
                "Usuário não identificado.",
                code="AUTHENTICATION_REQUIRED",
                status_code=401,
            )
        return actor

    def _governed_write_user(self, user: Any, authorization: str | None) -> Any:
        """Human-governed material write gate: end-user principal + fresh Core
        RBAC + TV_WRITE, fail-closed. Returns the freshly-authorized principal.
        Covers GPT Actions and MCP equally (both delegate here)."""
        try:
            return core_security.require_fresh_write_authorization(
                user,
                authorization=authorization,
                permission=TV_WRITE,
            )
        except GovernedWriteAuthzError as exc:
            raise GptActionsError(
                str(exc),
                code=exc.code,
                status_code=exc.status_code,
            ) from exc

    # ------------------------------------------------------------------
    # Semantic verbs surface (SEMANTIC_TOOLS_V1) — closed vocabulary
    # dispatch over the same canonical handlers. Adapter semantics only:
    # no second catalog, no second mutation engine, no AuthZ authority.
    # ------------------------------------------------------------------

    def semantic_get_context(
        self,
        *,
        user: Any,
        action: str | None = None,
        transport: str = "actions",
    ) -> dict[str, Any]:
        """``get_context`` — specialist context + effective capabilities.

        Effective capabilities are derived from real authorization
        (``can`` against Core-resolved permissions), never from the
        catalog — the catalog informs, AuthZ decides.
        """
        from tv_app.application.gpt_actions.capability_surface import (
            READ_ENTITY_ACTIONS,
            READ_ENTITY_STATUS,
            ANALYZE_ACTIONS,
            KNOWLEDGE_ACTIONS,
            EXECUTE_ENTITIES,
            EXECUTE_PHASES,
            EXECUTE_VERB_STATUS,
            DELETE_VERB_STATUS,
            DELETE_ENTITIES,
        )

        action_key = str(action or "context").strip().lower()
        if action_key == "catalog":
            return self.get_catalog(user=user, transport=transport)
        if action_key != "context":
            raise GptActionsError(
                f"Ação desconhecida para get_context: {action_key}.",
                code="UNKNOWN_ACTION",
                status_code=422,
            )
        assert_permission(user, TV_READ)
        can_read = True
        can_write = can(user, TV_WRITE)

        capabilities: list[dict[str, Any]] = []

        def _cap(name: str, *, verb: str, status: str, perm: str) -> None:
            capabilities.append(
                {
                    "capability": name,
                    "verb": verb,
                    "status": status,
                    "authorized": can_read if perm == "read" else can_write,
                }
            )

        for entity, actions in READ_ENTITY_ACTIONS.items():
            status = READ_ENTITY_STATUS.get(entity, "not_implemented")
            for act in actions:
                _cap(f"read.{entity}.{act}", verb="read", status=status, perm="read")
        for analysis, status in ANALYZE_ACTIONS.items():
            perm = "write" if analysis == "intent_materialization" else "read"
            _cap(f"analyze.{analysis}", verb="analyze", status=status, perm=perm)
        for act in KNOWLEDGE_ACTIONS:
            _cap(f"knowledge.{act}", verb="knowledge", status="proven", perm="read")
        for entity, actions in EXECUTE_ENTITIES.items():
            for act in actions:
                _cap(
                    f"execute.{entity}.{act}",
                    verb="execute",
                    status=EXECUTE_VERB_STATUS,
                    perm="write",
                )
        for entity in DELETE_ENTITIES:
            _cap(
                f"delete.{entity}",
                verb="delete",
                status=DELETE_VERB_STATUS,
                perm="write",
            )

        return {
            "assistant": {
                "id": "vista",
                "displayName": "VISTA",
                "characterId": "vista",
            },
            "principal": {
                "type": str(getattr(user, "principal_type", None) or "user"),
            },
            "catalogVersion": PresentationOpsContentService.catalog_version(),
            "effectiveCapabilities": capabilities,
            "confirmationModel": {
                "destructive": "consent_artifact_required",
                "target_check": "target_echo",
                "elicitation": "host_dependent",
                "fallback": "CONFIRMATION_UNAVAILABLE",
                "legacy_envelope": "confirmation_bool",
            },
            "phases": list(EXECUTE_PHASES),
            "notes": [
                "Catalog informs; backend authorizes. status/authorized are "
                "permission-level facts — resource scope (playlist/slide) is "
                "still enforced per call.",
                "confirm plans require a consent artifact minted by a "
                "verifiable human channel; target_echo alone proves nothing.",
            ],
        }

    @staticmethod

    # ------------------------------------------------------------------
    def _semantic_filters(
        filters: Any,
        *,
        allowed: set[str],
        context: str,
    ) -> dict[str, Any]:
        """Closed filter contract: undeclared keys are rejected (fail-closed),
        never silently dropped or treated as opaque."""
        raw = filters if isinstance(filters, dict) else {}
        unknown = sorted(str(k) for k in raw if k not in allowed)
        if unknown:
            raise GptActionsError(
                f"Filtro(s) não suportado(s) em {context}: {', '.join(unknown)}.",
                code="VALIDATION_ERROR",
                status_code=422,
                details={"rejectedFilters": unknown, "allowedFilters": sorted(allowed)},
            )
        return raw

    def semantic_read(
        self,
        *,
        user: Any,
        entity: str,
        action: str,
        ref: str | None = None,
        filters: dict[str, Any] | None = None,
        pagination: dict[str, Any] | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        """``read`` — closed (entity, action) vocabulary over READ handlers."""
        from tv_app.application.gpt_actions.capability_surface import (
            READ_ENTITY_ACTIONS,
            READ_ENTITY_STATUS,
        )

        entity_key = str(entity or "").strip()
        action_key = str(action or "").strip().lower()
        if entity_key not in READ_ENTITY_ACTIONS:
            raise GptActionsError(
                f"Entidade desconhecida para read: {entity_key!r}.",
                code="UNKNOWN_ENTITY",
                status_code=422,
            )
        if action_key not in READ_ENTITY_ACTIONS[entity_key]:
            raise GptActionsError(
                f"Ação desconhecida para read.{entity_key}: {action_key!r}.",
                code="UNKNOWN_ACTION",
                status_code=422,
            )
        if READ_ENTITY_STATUS.get(entity_key) != "proven":
            raise GptActionsError(
                f"read.{entity_key}.{action_key} ainda não possui handler "
                "canônico (capability planejada — B0/B1).",
                code="NOT_IMPLEMENTED",
                status_code=501,
            )
        page = pagination if isinstance(pagination, dict) else {}
        limit = page.get("limit")
        cursor = page.get("cursor")

        if entity_key == "playlist" and action_key == "list":
            self._semantic_filters(
                filters, allowed=set(), context="read.playlist.list"
            )
            return self.list_playlists(
                user=user,
                limit=min(max(int(limit or 50), 1), 100),
                offset=max(int(cursor or 0), 0),
            )
        if action_key == "export_mdd" and entity_key in (
            "playlist", "slide_template"
        ):
            self._semantic_filters(
                filters, allowed=set(), context="read.export_mdd"
            )
            from tv_app.core.security import assert_permission
            from uuid import UUID

            ref_raw = str(ref or "").strip()
            if not ref_raw:
                raise GptActionsError(
                    "export_mdd exige ref do recurso.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            try:
                rid = UUID(ref_raw)
            except ValueError as exc:
                raise GptActionsError(
                    "ref inválido.",
                    code="INVALID_CHANGE", status_code=422,
                ) from exc
            if entity_key == "playlist":
                assert_permission(user, TV_READ)
                from tv_app.application.services.tv_deck_package_service import (
                    TvDeckPackageService,
                )

                raw, filename = TvDeckPackageService().export_package(rid)
            else:
                assert_permission(user, TV_READ)
                from tv_app.application.services.slide_template_library_service import (
                    SlideTemplateLibraryService,
                )

                raw, filename = SlideTemplateLibraryService().export_mdd(
                    rid
                )
            import json as _json

            return {
                "filename": filename,
                "sizeBytes": len(raw),
                "mdd": _json.loads(raw.decode("utf-8")),
                "entity": entity_key,
            }
        if entity_key == "playlist" and action_key == "list_shares":
            self._semantic_filters(
                filters, allowed=set(), context="read.playlist.list_shares"
            )
            from uuid import UUID

            from tv_app.application.services.playlist_share_service import (
                list_shares,
            )

            pid_raw = str(ref or "").strip()
            if not pid_raw:
                raise GptActionsError(
                    "list_shares exige ref=playlistId.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            items = list_shares(UUID(pid_raw), user)
            return {"items": items, "count": len(items),
                    "entity": "playlist"}
        if entity_key == "playlist":
            flt = self._semantic_filters(
                filters,
                allowed={
                    "slideId",
                    "includePreview",
                    "scope",
                    "objectQuery",
                    "objectTypes",
                    "blockCursor",
                    "blockLimit",
                    "dataSourceId",
                    "includeRuntime",
                },
                context=f"read.playlist.{action_key}",
            )
            return self.get_playlist_context(
                user=user,
                playlist_id=str(ref or ""),
                include_preview=bool(flt.get("includePreview")),
                preview_slide_id=flt.get("slideId"),
                scope=flt.get("scope"),
                object_query=flt.get("objectQuery"),
                object_types=flt.get("objectTypes"),
                block_cursor=flt.get("blockCursor"),
                block_limit=flt.get("blockLimit"),
                data_source_id=flt.get("dataSourceId"),
                include_runtime=bool(flt.get("includeRuntime")),
                authorization=authorization,
            )
        if entity_key == "playlist_history":
            flt = self._semantic_filters(
                filters,
                allowed={"snapshotId", "page", "pageSize"},
                context="read.playlist_history.history",
            )
            return self.get_playlist_history(
                user=user,
                playlist_id=str(ref or ""),
                snapshot_id=flt.get("snapshotId"),
                page=int(flt.get("page") or 1),
                page_size=min(max(int(flt.get("pageSize") or 10), 1), 100),
            )
        if entity_key == "data_route":
            flt = self._semantic_filters(
                filters,
                allowed={"query", "limit", "category"},
                context="read.data_route.search",
            )
            return self.search_data_routes(
                user=user,
                query=str(flt.get("query") or ""),
                limit=int(flt.get("limit") or (limit or 8)),
                category=flt.get("category"),
                authorization=authorization,
            )
        if entity_key == "data_model":
            flt = self._semantic_filters(
                filters,
                allowed={"playlistId", "slideId", "includeRuntime"},
                context="read.data_model.inspect",
            )
            return self.inspect_data_model(
                user=user,
                playlist_id=str(flt.get("playlistId") or ""),
                slide_id=str(flt.get("slideId") or ""),
                model_id=str(ref or ""),
                authorization=authorization,
                include_runtime=bool(flt.get("includeRuntime", True)),
            )
        if entity_key == "display_format" and action_key == "list":
            self._semantic_filters(
                filters, allowed=set(), context="read.display_format.list"
            )
            return self.list_display_formats(user=user)
        if entity_key == "slide_preset" and action_key == "list":
            self._semantic_filters(
                filters, allowed=set(), context="read.slide_preset.list"
            )
            from tv_app.application.services.slide_preset_service import (
                list_slide_presets,
            )

            items = list_slide_presets()
            return {
                "items": items,
                "count": len(items),
                "entity": "slide_preset",
            }
        if entity_key == "media_asset" and action_key == "list":
            flt = self._semantic_filters(
                filters,
                allowed={"mediaKind"},
                context="read.media_asset.list",
            )
            from tv_app.application.services.media_query_service import (
                list_playlist_media,
            )
            from uuid import UUID

            playlist_ref = str(ref or flt.get("playlistId") or "").strip()
            if not playlist_ref:
                raise GptActionsError(
                    "read.media_asset.list exige ref=playlistId.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
            items = list_playlist_media(
                UUID(playlist_ref),
                media_kind=flt.get("mediaKind"),
            )
            return {
                "items": items,
                "count": len(items),
                "entity": "media_asset",
                "playlistId": playlist_ref,
            }
        if entity_key == "slide_template" and action_key == "list":
            flt = self._semantic_filters(
                filters,
                allowed={"status", "q", "isSystem"},
                context="read.slide_template.list",
            )
            from tv_app.application.services.slide_template_library_service import (
                SlideTemplateLibraryService,
            )
            from tv_app.core.security import assert_permission

            status_raw = str(flt.get("status") or "").strip().lower() or None
            svc = SlideTemplateLibraryService()
            if status_raw == "published":
                assert_permission(user, TV_READ)
                items = svc.list_published()
            else:
                assert_permission(user, TV_TEMPLATES_MANAGE)
                if status_raw and status_raw not in (
                    "draft", "published", "archived"
                ):
                    raise GptActionsError(
                        "status inválido.",
                        code="VALIDATION_ERROR", status_code=422,
                    )
                is_system = flt.get("isSystem")
                items = svc.list_library(
                    status=status_raw,
                    q=str(flt.get("q") or "").strip() or None,
                    is_system=is_system if isinstance(is_system, bool) else None,
                )
            return {"items": items, "count": len(items),
                    "entity": "slide_template"}
        if entity_key == "slide_template" and action_key == "get":
            self._semantic_filters(
                filters, allowed=set(), context="read.slide_template.get"
            )
            from tv_app.application.services.slide_template_library_service import (
                SlideTemplateLibraryService,
            )
            from tv_app.core.security import assert_permission
            from uuid import UUID

            tid = str(ref or "").strip()
            if not tid:
                raise GptActionsError(
                    "read.slide_template.get exige ref=templateId.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            item = SlideTemplateLibraryService().get(UUID(tid))
            if str(item.get("status") or "") == "published":
                assert_permission(user, TV_READ)
            else:
                assert_permission(user, TV_TEMPLATES_MANAGE)
            return {"item": item, "entity": "slide_template"}
        if entity_key == "product_guide":
            flt = self._semantic_filters(
                filters,
                allowed={"topic", "section"},
                context="read.product_guide.guide",
            )
            return self.get_product_guide(
                user=user,
                topic=str(ref or flt.get("topic") or "") or None,
                section=flt.get("section"),
            )
        # Defensive: vocabulary table and status table must agree.
        raise GptActionsError(  # pragma: no cover — contract table drift
            f"read.{entity_key}.{action_key} sem dispatch.",
            code="NOT_IMPLEMENTED",
            status_code=501,
        )

    def semantic_analyze(
        self,
        *,
        user: Any,
        analysis: str,
        subject_refs: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        """``analyze`` — closed analysis vocabulary over ANALYSIS handlers."""
        from tv_app.application.gpt_actions.capability_surface import (
            ANALYZE_ACTIONS,
        )

        analysis_key = str(analysis or "").strip()
        if analysis_key not in ANALYZE_ACTIONS:
            raise GptActionsError(
                f"Análise desconhecida: {analysis_key!r}.",
                code="UNKNOWN_ACTION",
                status_code=422,
            )
        if ANALYZE_ACTIONS[analysis_key] != "proven":
            raise GptActionsError(
                f"analyze.{analysis_key} não implementada.",
                code="NOT_IMPLEMENTED",
                status_code=501,
            )
        refs = subject_refs if isinstance(subject_refs, dict) else {}
        params = parameters if isinstance(parameters, dict) else {}

        if analysis_key == "intent_materialization":
            message = str(params.get("message") or "").strip()
            if not message:
                raise GptActionsError(
                    "parameters.message é obrigatório para intent_materialization.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
            out = self.suggest_change(
                user=user,
                message=message,
                host_context=refs,
                authorization=authorization,
            )
            out = dict(out)
            out["evidenceClass"] = "calculation"
            return out

        body = dict(refs)
        for key, value in params.items():
            body.setdefault(key, value)
        if analysis_key == "data_block_preview":
            out = self.preview_data_block(
                user=user, body=body, authorization=authorization
            )
            out = dict(out)
            out["evidenceClass"] = "preview"
            return out
        if analysis_key == "data_model_preview":
            out = self.preview_data_model(
                user=user, body=body, authorization=authorization
            )
            out = dict(out)
            out["evidenceClass"] = "preview"
            return out
        raise GptActionsError(  # pragma: no cover — contract table drift
            f"analyze.{analysis_key} sem dispatch.",
            code="NOT_IMPLEMENTED",
            status_code=501,
        )

    def semantic_knowledge(
        self,
        *,
        user: Any,
        action: str,
        topic: str | None = None,
        section: str | None = None,
        query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """``knowledge`` — canonical Product Guide registry projection.

        ``get`` returns one guide (or the topic index when topic is
        omitted). ``search`` is a deterministic bounded projection of the
        same registry filtered by query — no second knowledge base.
        """
        action_key = str(action or "").strip().lower()
        if action_key not in {"search", "get"}:
            raise GptActionsError(
                f"Ação desconhecida para knowledge: {action_key!r}.",
                code="UNKNOWN_ACTION",
                status_code=422,
            )
        if action_key == "get":
            return self.get_product_guide(user=user, topic=topic, section=section)

        assert_permission(user, TV_READ)
        from tv_app.application.product_guide.product_guide_registry import (
            get_product_guide_registry,
        )
        from tv_app.application.product_guide.product_guide_service import (
            guide_index_payload,
        )

        index = guide_index_payload(get_product_guide_registry())
        q = str(query or "").strip().lower()
        topics = list(index.get("topics") or [])
        if q:
            topics = [
                item
                for item in topics
                if isinstance(item, dict)
                and (
                    q in str(item.get("id") or "").lower()
                    or q in str(item.get("title") or "").lower()
                    or q in str(item.get("summary") or "").lower()
                )
            ]
        capped = max(1, min(int(limit or 20), 50))
        return {
            "topics": topics[:capped],
            "total": len(topics[:capped]),
            "query": str(query or "") or None,
            "evidenceClass": "fact",
            "source": "product_guide_registry",
        }

    def _semantic_commit(
        self,
        *,
        user: Any,
        proposal_handle: str,
        idempotency_key: str | None,
        consent_artifact: str | None,
        target_echo: str | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        """Commit phase shared by semantic write verbs — always
        ``consent_required=True``: the semantic surface has no
        ``confirmation`` boolean; only the consent artifact minted by
        the trusted channel proves human consent for confirm plans."""
        if not str(proposal_handle or "").strip():
            raise GptActionsError(
                "proposal_handle é obrigatório na fase commit.",
                code="INVALID_CHANGE",
                status_code=422,
            )
        confirmation: dict[str, Any] = {}
        if consent_artifact:
            confirmation["consent_artifact"] = consent_artifact
        if target_echo:
            confirmation["target_echo"] = target_echo
        return self.commit_change(
            user=user,
            proposal_handle=proposal_handle,
            confirmation=confirmation,
            idempotency_key=str(idempotency_key or "").strip(),
            authorization=authorization,
            consent_required=True,
        )

    @staticmethod
    def _semantic_operations(operations: list[Any] | None) -> list[dict[str, Any]]:
        """Normalize ``operations[]`` entries to canonical typed ops.

        Accepts the documented ``{"op", "args", "as"}`` envelope shape —
        ``args`` is flattened into the op — as well as flat op dicts.
        Transport translation only; vocabulary validation stays with the
        canonical catalog/PlanCompiler downstream.
        """
        out: list[dict[str, Any]] = []
        for raw in operations or []:
            if not isinstance(raw, dict):
                continue
            args = raw.get("args")
            op = {k: v for k, v in raw.items() if k != "args"}
            if isinstance(args, dict):
                op = {**args, **op}
            out.append(op)
        return out

    # B2 — slide_template commands (canonical SlideTemplateLibraryService)
    # ------------------------------------------------------------------

    def _template_service(self):
        from tv_app.application.services.slide_template_library_service import (
            SlideTemplateLibraryService,
        )

        return SlideTemplateLibraryService()

    # ------------------------------------------------------------------
    # B3 — playlist delete (sealed+consent) & history restore (CAS)
    # ------------------------------------------------------------------

    def _playlist_delete(
        self,
        *,
        user: Any,
        phase: str | None,
        target: dict[str, Any] | None,
        proposal_handle: str | None,
        consent_artifact: str | None,
        target_echo: str | None,
        idempotency_key: str | None,
        authorization: str | None,
        transport: str,
    ) -> dict[str, Any]:
        """Playlist delete — sealed proposal + A5 consent (B2 pattern)."""
        import hashlib
        import json as _json
        import time as _time
        import uuid as _uuid
        from uuid import UUID

        from tv_app.application.gpt_actions.proposal import VistaProposal
        from tv_app.application.gpt_actions.proposal_store import (
            load_valid_proposal,
            get_proposal_store,
        )
        from tv_app.application.gpt_actions.vista_consent_service import (
            challenge_view,
        )
        from tv_app.application.services.playlist_lifecycle_service import (
            delete_playlist,
        )

        user = self._governed_write_user(user, authorization)
        actor = self._actor(user)
        phase_key = str(phase or "prepare").strip().lower()
        if phase_key not in ("prepare", "commit"):
            raise GptActionsError(
                f"Fase desconhecida para delete: {phase_key!r}.",
                code="VALIDATION_ERROR", status_code=422,
            )

        if phase_key == "commit":
            if not proposal_handle:
                raise GptActionsError(
                    "commit exige proposal_handle.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            proposal = load_valid_proposal(
                proposal_handle=proposal_handle,
                actor_id=actor,
                expected_capability="delete.playlist",
            )
            pid_raw = str(
                (proposal.exact_change.get("target") or {}).get("playlistId")
                or ""
            ).strip()
            echo = str(target_echo or "").strip()
            if echo != pid_raw:
                raise GptActionsError(
                    "target_echo não corresponde ao alvo selado.",
                    code="CONFIRMATION_MISMATCH", status_code=409,
                )
            if self._consent is None:
                raise GptActionsError(
                    "Canal de consentimento indisponível.",
                    code="CONFIRMATION_UNAVAILABLE", status_code=503,
                )
            challenge = self._consent.verify_for_commit(
                proposal=proposal,
                actor_sub=actor,
                consent_artifact=consent_artifact,
                required=True,
            )
            try:
                delete_playlist(UUID(pid_raw))
            except Exception as exc:  # noqa: BLE001 — surface typed
                raise GptActionsError(
                    "Programação não encontrada.",
                    code="RESOURCE_NOT_FOUND", status_code=404,
                ) from exc
            self._consent.consume_for_commit(
                challenge=challenge,
                proposal_id=proposal.proposal_id,
                actor_sub=actor,
            )
            get_proposal_store().consume(proposal.proposal_id)
            return {
                "status": "VERIFIED",
                "operation": "delete_playlist",
                "deleted": {"id": pid_raw},
                "playlistId": pid_raw,
            }

        target_map = target if isinstance(target, dict) else {}
        pid_raw = str(target_map.get("playlistId") or "").strip()
        if not pid_raw:
            raise GptActionsError(
                "delete.playlist exige target.playlistId.",
                code="VALIDATION_ERROR", status_code=422,
            )
        try:
            pid = UUID(pid_raw)
        except ValueError as exc:
            raise GptActionsError(
                "playlistId inválido.",
                code="INVALID_CHANGE", status_code=422,
            ) from exc
        from tv_app.application.services.playlist_lifecycle_service import (
            get_playlist_state,
        )

        item = get_playlist_state(pid)
        if not item:
            raise GptActionsError(
                "Programação não encontrada.",
                code="RESOURCE_NOT_FOUND", status_code=404,
            )
        state_fp = hashlib.sha256(
            _json.dumps(item, sort_keys=True, default=str).encode()
        ).hexdigest()
        exact_change = {
            "target": {"playlistId": pid_raw},
            "ops": [{"op": "delete_playlist", "playlistId": pid_raw}],
        }
        now = _time.time()
        content_hash = hashlib.sha256(
            _json.dumps(
                {
                    "capability": "delete.playlist",
                    "actor_id": str(actor),
                    "resource_id": pid_raw,
                    "state": state_fp,
                    "exact_change": exact_change,
                },
                sort_keys=True, default=str,
            ).encode()
        ).hexdigest()
        proposal = VistaProposal(
            proposal_id=f"prop_{_uuid.uuid4().hex[:24]}",
            capability="delete.playlist",
            actor_id=str(actor),
            resource_type="playlist",
            resource_id=pid_raw,
            current_state_fingerprint=state_fp,
            exact_change=exact_change,
            confirmation_requirement={
                "explicit_user_confirmation": True,
                "confirmation_policy": "confirm",
                "destructive": True,
            },
            risk="destructive",
            confirmation_policy="confirm",
            catalog_version="",
            base_revision=None,
            created_at=now,
            expires_at=now + 600,
            content_hash=content_hash,
        )
        handle = get_proposal_store().put(proposal)
        if self._consent is None:
            raise GptActionsError(
                "Canal de consentimento indisponível.",
                code="CONFIRMATION_UNAVAILABLE", status_code=503,
            )
        consent_challenge = challenge_view(
            self._consent.issue_for_proposal(
                proposal=proposal,
                actor_sub=actor,
                origin=transport,
                correlation_id=None,
            )
        )
        return {
            "status": "consent_required",
            "phase": "prepare",
            "operation": "delete_playlist",
            "proposal_handle": handle,
            "consentChallenge": consent_challenge,
            "target": {"playlistId": pid_raw},
            "item": item,
        }

    def _playlist_history_restore(
        self,
        *,
        user: Any,
        target: dict[str, Any] | None,
        authorization: str | None,
        transport: str,
    ) -> dict[str, Any]:
        """Playlist history restore — CAS-guarded canonical workflow."""
        from uuid import UUID

        from tv_app.application.services.playlist_lifecycle_service import (
            PlaylistHistoryNotFoundError,
            PlaylistRevisionConflictError,
            restore_playlist_history,
        )

        user = self._governed_write_user(user, authorization)
        from tv_app.core.security import assert_permission
        assert_permission(user, TV_WRITE)
        actor = self._actor(user)
        tgt = target if isinstance(target, dict) else {}
        pid_raw = str(tgt.get("playlistId") or "").strip()
        hid_raw = str(tgt.get("historyId") or "").strip()
        if not pid_raw or not hid_raw:
            raise GptActionsError(
                "restore exige target.playlistId + target.historyId.",
                code="VALIDATION_ERROR", status_code=422,
            )
        expected = tgt.get("expectedRevision")
        try:
            pid, hid = UUID(pid_raw), UUID(hid_raw)
        except ValueError as exc:
            raise GptActionsError(
                "playlistId/historyId inválido.",
                code="INVALID_CHANGE", status_code=422,
            ) from exc
        try:
            result = restore_playlist_history(
                pid,
                hid,
                expected_revision=(
                    int(expected) if expected is not None else None
                ),
                actor_user_id=actor,
            )
            revision = result["revision"]
            playlist = result["playlist"]
        except PlaylistRevisionConflictError as exc:
            raise GptActionsError(
                "A programação foi alterada por outro usuário.",
                code="REVISION_CONFLICT",
                status_code=409,
                details={
                    "currentRevision": getattr(
                        exc, "current_revision", None
                    )
                },
            ) from exc
        except PlaylistHistoryNotFoundError as exc:
            raise GptActionsError(
                "Versão do histórico não encontrada.",
                code="RESOURCE_NOT_FOUND", status_code=404,
            ) from exc
        return {
            "status": "VERIFIED",
            "operation": "restore",
            "playlistId": pid_raw,
            "historyId": hid_raw,
            "revision": revision,
            "playlist": playlist,
        }

    # ------------------------------------------------------------------
    # B4 — MDD import/export via canonical services
    # ------------------------------------------------------------------

    _MAX_MDD_INLINE_BYTES = 512 * 1024

    def _mdd_payload(self, operations: list[Any] | None) -> bytes:
        import json as _json

        payload = (operations or [{}])[0]
        if not isinstance(payload, dict):
            raise GptActionsError(
                "operations[0] deve ser um objeto com o pacote MDD.",
                code="VALIDATION_ERROR", status_code=422,
            )
        mdd = payload.get("mdd")
        if mdd is None:
            raise GptActionsError(
                "operations[0].mdd é obrigatório (conteúdo JSON do pacote).",
                code="VALIDATION_ERROR", status_code=422,
            )
        if isinstance(mdd, str):
            raw = mdd.encode("utf-8")
        elif isinstance(mdd, dict):
            raw = _json.dumps(mdd).encode("utf-8")
        else:
            raise GptActionsError(
                "mdd deve ser objeto JSON ou string JSON.",
                code="VALIDATION_ERROR", status_code=422,
            )
        if len(raw) > self._MAX_MDD_INLINE_BYTES:
            raise GptActionsError(
                "Pacote MDD acima do limite inline "
                f"({self._MAX_MDD_INLINE_BYTES} bytes) — "
                "use o canal de upload canônico.",
                code="VALIDATION_ERROR", status_code=422,
            )
        return raw

    def _mdd_import(
        self,
        *,
        user: Any,
        entity: str,
        action: str,
        operations: list[Any] | None,
        authorization: str | None,
        transport: str,
    ) -> dict[str, Any]:
        """MDD import — preview (no persist) / apply (canonico, governed)."""
        from tv_app.core.security import assert_permission

        user = self._governed_write_user(user, authorization)
        actor = self._actor(user)
        payload = (operations or [{}])[0] if operations else {}
        if not isinstance(payload, dict):
            raise GptActionsError(
                "operations[0] deve ser um objeto.",
                code="VALIDATION_ERROR", status_code=422,
            )

        if entity == "playlist":
            assert_permission(user, TV_WRITE)
            from tv_app.application.services.tv_deck_package_service import (
                TvDeckPackageService,
                TvDeckPackageError,
            )

            svc = TvDeckPackageService()
            try:
                if action == "import_preview":
                    raw = self._mdd_payload(operations)
                    summary = svc.preview_import(raw)
                    return {
                        "status": "PREVIEW_ONLY",
                        "operation": "import_preview",
                        "summary": summary,
                        "persisted": False,
                    }
                token = str(payload.get("importToken") or "").strip()
                if not token:
                    raise GptActionsError(
                        "import_apply exige operations[0].importToken "
                        "emitido por import_preview.",
                        code="VALIDATION_ERROR", status_code=422,
                    )
                binding_policy = str(
                    payload.get("bindingPolicy") or "lenient"
                ).strip()
                if binding_policy not in ("lenient", "strict"):
                    raise GptActionsError(
                        "bindingPolicy deve ser lenient|strict.",
                        code="VALIDATION_ERROR", status_code=422,
                    )
                playlist = svc.apply_import(
                    import_token=token,
                    created_by=actor,
                    name_override=payload.get("nameOverride"),
                    activate_after_import=bool(
                        payload.get("activateAfterImport")
                    ),
                    binding_policy=binding_policy,
                )
            except TvDeckPackageError as exc:
                raise GptActionsError(
                    str(exc),
                    code="INVALID_CHANGE", status_code=422,
                ) from exc
            return {
                "status": "VERIFIED",
                "operation": "import_apply",
                "playlist": playlist,
            }

        assert_permission(user, TV_TEMPLATES_MANAGE)
        from tv_app.application.services.slide_template_library_service import (
            SlideTemplateLibraryService,
        )

        svc = SlideTemplateLibraryService()
        try:
            if action == "import_preview":
                raw = self._mdd_payload(operations)
                summary = svc.import_preview(raw)
                return {
                    "status": "PREVIEW_ONLY",
                    "operation": "import_preview",
                    "summary": summary,
                    "persisted": False,
                }
            raw = self._mdd_payload(operations)
            item = svc.import_apply(
                raw,
                publish_now=bool(payload.get("publishNow")),
                owner_user_id=actor,
                updated_by=actor,
            )
        except Exception as exc:  # noqa: BLE001 — surface typed
            raise GptActionsError(
                str(exc), code="INVALID_CHANGE", status_code=422
            ) from exc
        return {
            "status": "VERIFIED",
            "operation": "import_apply",
            "item": item,
        }

    # ------------------------------------------------------------------
    # B5 — playlist shares & edit invites (canon commands)
    # ------------------------------------------------------------------

    def _share_invite_command(
        self,
        *,
        user: Any,
        action: str,
        target: dict[str, Any] | None,
        operations: list[Any] | None,
        authorization: str | None,
        transport: str,
    ) -> dict[str, Any]:
        from uuid import UUID

        from tv_app.application.services.playlist_share_service import (
            ShareNotFoundError,
            create_edit_invite,
            redeem_edit_invite,
            upsert_share,
        )

        user = self._governed_write_user(user, authorization)
        payload = (operations or [{}])[0] if operations else {}
        if not isinstance(payload, dict):
            raise GptActionsError(
                "operations[0] deve ser um objeto.",
                code="VALIDATION_ERROR", status_code=422,
            )
        tgt = target if isinstance(target, dict) else {}

        if action == "accept_edit_invite":
            token = str(payload.get("token") or "").strip()
            if not token:
                raise GptActionsError(
                    "accept_edit_invite exige operations[0].token.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            try:
                result = redeem_edit_invite(token, user)
            except ShareNotFoundError as exc:
                raise GptActionsError(
                    "Convite inválido ou revogado.",
                    code="RESOURCE_NOT_FOUND", status_code=404,
                ) from exc
            return {
                "status": "VERIFIED",
                "operation": "accept_edit_invite",
                "share": result,
            }

        pid_raw = str(tgt.get("playlistId") or "").strip()
        if not pid_raw:
            raise GptActionsError(
                f"{action} exige target.playlistId.",
                code="VALIDATION_ERROR", status_code=422,
            )
        try:
            pid = UUID(pid_raw)
        except ValueError as exc:
            raise GptActionsError(
                "playlistId inválido.",
                code="INVALID_CHANGE", status_code=422,
            ) from exc

        try:
            if action == "share":
                role = str(payload.get("role") or "viewer").strip()
                share = upsert_share(
                    pid,
                    user,
                    target_user_id=str(payload.get("targetUserId") or ""),
                    role=role,
                )
                return {
                    "status": "VERIFIED",
                    "operation": "share",
                    "share": share,
                }
            if action == "create_edit_invite":
                invite = create_edit_invite(
                    pid,
                    user,
                    role=str(payload.get("role") or "editor").strip(),
                )
                return {
                    "status": "VERIFIED",
                    "operation": "create_edit_invite",
                    "invite": invite,
                }
        except PermissionError as exc:
            raise GptActionsError(
                str(exc), code="PERMISSION_DENIED", status_code=403
            ) from exc
        except ValueError as exc:
            raise GptActionsError(
                str(exc), code="VALIDATION_ERROR", status_code=422
            ) from exc
        raise GptActionsError(
            f"Ação desconhecida: {action!r}.",
            code="UNKNOWN_ACTION", status_code=422,
        )

    def _share_invite_delete(
        self,
        *,
        user: Any,
        entity: str,
        phase: str | None,
        target: dict[str, Any] | None,
        proposal_handle: str | None,
        consent_artifact: str | None,
        target_echo: str | None,
        idempotency_key: str | None,
        authorization: str | None,
        transport: str,
    ) -> dict[str, Any]:
        """Share/invite revoke — sealed proposal + A5 consent."""
        import hashlib
        import json as _json
        import time as _time
        import uuid as _uuid
        from uuid import UUID

        from tv_app.application.gpt_actions.proposal import VistaProposal
        from tv_app.application.gpt_actions.proposal_store import (
            load_valid_proposal,
            get_proposal_store,
        )
        from tv_app.application.gpt_actions.vista_consent_service import (
            challenge_view,
        )
        from tv_app.application.services.playlist_share_service import (
            ShareNotFoundError,
            list_shares,
            revoke_edit_invites,
            revoke_share,
        )

        user = self._governed_write_user(user, authorization)
        actor = self._actor(user)
        phase_key = str(phase or "prepare").strip().lower()
        if phase_key not in ("prepare", "commit"):
            raise GptActionsError(
                f"Fase desconhecida para delete: {phase_key!r}.",
                code="VALIDATION_ERROR", status_code=422,
            )
        capability = f"delete.{entity}"

        if phase_key == "commit":
            if not proposal_handle:
                raise GptActionsError(
                    "commit exige proposal_handle.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            proposal = load_valid_proposal(
                proposal_handle=proposal_handle,
                actor_id=actor,
                expected_capability=capability,
            )
            tgt = proposal.exact_change.get("target") or {}
            pid_raw = str(tgt.get("playlistId") or "").strip()
            expected_echo = str(tgt.get("targetUserId") or pid_raw)
            echo = str(target_echo or "").strip()
            if echo != expected_echo:
                raise GptActionsError(
                    "target_echo não corresponde ao alvo selado.",
                    code="CONFIRMATION_MISMATCH", status_code=409,
                )
            if self._consent is None:
                raise GptActionsError(
                    "Canal de consentimento indisponível.",
                    code="CONFIRMATION_UNAVAILABLE", status_code=503,
                )
            challenge = self._consent.verify_for_commit(
                proposal=proposal,
                actor_sub=actor,
                consent_artifact=consent_artifact,
                required=True,
            )
            try:
                if entity == "playlist_share":
                    revoke_share(
                        UUID(pid_raw),
                        user,
                        target_user_id=str(tgt.get("targetUserId") or ""),
                    )
                    result = {"targetUserId": tgt.get("targetUserId")}
                else:
                    count = revoke_edit_invites(UUID(pid_raw), user)
                    result = {"revoked": count}
            except ShareNotFoundError as exc:
                raise GptActionsError(
                    "Alvo não encontrado.",
                    code="RESOURCE_NOT_FOUND", status_code=404,
                ) from exc
            except PermissionError as exc:
                raise GptActionsError(
                    str(exc), code="PERMISSION_DENIED", status_code=403
                ) from exc
            self._consent.consume_for_commit(
                challenge=challenge,
                proposal_id=proposal.proposal_id,
                actor_sub=actor,
            )
            get_proposal_store().consume(proposal.proposal_id)
            return {
                "status": "VERIFIED",
                "operation": capability,
                "result": result,
                "playlistId": pid_raw,
            }

        tgt_map = target if isinstance(target, dict) else {}
        pid_raw = str(tgt_map.get("playlistId") or "").strip()
        if not pid_raw:
            raise GptActionsError(
                f"delete.{entity} exige target.playlistId.",
                code="VALIDATION_ERROR", status_code=422,
            )
        try:
            pid = UUID(pid_raw)
        except ValueError as exc:
            raise GptActionsError(
                "playlistId inválido.",
                code="INVALID_CHANGE", status_code=422,
            ) from exc
        try:
            current = list_shares(pid, user)
        except PermissionError as exc:
            raise GptActionsError(
                str(exc), code="PERMISSION_DENIED", status_code=403
            ) from exc
        sealed_target = {"playlistId": pid_raw}
        if entity == "playlist_share":
            tuid = str(tgt_map.get("targetUserId") or "").strip()
            if not tuid:
                raise GptActionsError(
                    "delete.playlist_share exige target.targetUserId.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            sealed_target["targetUserId"] = tuid
            match = next(
                (s for s in current
                 if str(s.get("userId") or s.get("targetUserId") or "")
                 == tuid),
                None,
            )
            if match is None:
                raise GptActionsError(
                    "Compartilhamento não encontrado.",
                    code="RESOURCE_NOT_FOUND", status_code=404,
                )
        state_fp = hashlib.sha256(
            _json.dumps(current, sort_keys=True, default=str).encode()
        ).hexdigest()
        exact_change = {"target": sealed_target,
                        "ops": [{"op": capability, **sealed_target}]}
        now = _time.time()
        content_hash = hashlib.sha256(
            _json.dumps(
                {
                    "capability": capability,
                    "actor_id": str(actor),
                    "resource_id": pid_raw,
                    "state": state_fp,
                    "exact_change": exact_change,
                },
                sort_keys=True, default=str,
            ).encode()
        ).hexdigest()
        proposal = VistaProposal(
            proposal_id=f"prop_{_uuid.uuid4().hex[:24]}",
            capability=capability,
            actor_id=str(actor),
            resource_type=entity,
            resource_id=pid_raw,
            current_state_fingerprint=state_fp,
            exact_change=exact_change,
            confirmation_requirement={
                "explicit_user_confirmation": True,
                "confirmation_policy": "confirm",
                "destructive": True,
            },
            risk="destructive",
            confirmation_policy="confirm",
            catalog_version="",
            base_revision=None,
            created_at=now,
            expires_at=now + 600,
            content_hash=content_hash,
        )
        handle = get_proposal_store().put(proposal)
        if self._consent is None:
            raise GptActionsError(
                "Canal de consentimento indisponível.",
                code="CONFIRMATION_UNAVAILABLE", status_code=503,
            )
        consent_challenge = challenge_view(
            self._consent.issue_for_proposal(
                proposal=proposal,
                actor_sub=actor,
                origin=transport,
                correlation_id=None,
            )
        )
        return {
            "status": "consent_required",
            "phase": "prepare",
            "operation": capability,
            "proposal_handle": handle,
            "consentChallenge": consent_challenge,
            "target": sealed_target,
            "impact": {"shares": len(current)},
        }

    def _slide_template_execute(
        self,
        *,
        user: Any,
        action: str,
        target: dict[str, Any] | None,
        operations: list[Any] | None,
        idempotency_key: str | None,
        authorization: str | None,
        transport: str,
    ) -> dict[str, Any]:
        from tv_app.core.security import assert_permission
        from uuid import UUID

        user = self._governed_write_user(user, authorization)
        assert_permission(user, TV_TEMPLATES_MANAGE)
        actor = self._actor(user)
        svc = self._template_service()
        payload = (operations or [{}])[0]
        if not isinstance(payload, dict):
            raise GptActionsError(
                "operations[0] deve ser um objeto com os campos do comando.",
                code="VALIDATION_ERROR", status_code=422,
            )
        target_map = target if isinstance(target, dict) else {}
        tid_raw = str(target_map.get("templateId") or payload.get("templateId")
                      or "").strip()

        if action == "create":
            label = str(payload.get("label") or "").strip()
            if not label:
                raise GptActionsError(
                    "create exige label.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            item = svc.create(
                label=label,
                description=payload.get("description"),
                native_config=payload.get("nativeConfig"),
                native_screen_key=payload.get("nativeScreenKey"),
                duration_sec=payload.get("durationSec"),
                key=payload.get("key"),
                publish_now=bool(payload.get("publishNow")),
                owner_user_id=actor,
                updated_by=actor,
            )
            return {"status": "VERIFIED", "operation": "create",
                    "item": item}

        if not tid_raw:
            raise GptActionsError(
                f"{action} exige target.templateId.",
                code="VALIDATION_ERROR", status_code=422,
            )
        try:
            tid = UUID(tid_raw)
        except ValueError as exc:
            raise GptActionsError(
                "templateId inválido.",
                code="INVALID_CHANGE", status_code=422,
            ) from exc

        if action == "update":
            fields = {
                k: payload[k]
                for k in ("label", "description", "nativeConfig",
                          "nativeScreenKey", "durationSec")
                if k in payload and payload[k] is not None
            }
            if not fields:
                raise GptActionsError(
                    "update exige ao menos um campo.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            item = svc.update(tid, updated_by=actor, **fields)
        elif action == "clone":
            item = svc.clone(
                tid, updated_by=actor, owner_user_id=actor
            )
        elif action == "publish":
            item = svc.publish(tid, updated_by=actor)
        elif action == "unpublish":
            item = svc.unpublish(tid, updated_by=actor)
        elif action == "archive":
            item = svc.archive(tid, updated_by=actor)
        else:
            raise GptActionsError(
                f"Ação desconhecida para slide_template: {action!r}.",
                code="UNKNOWN_ACTION", status_code=422,
            )
        return {"status": "VERIFIED", "operation": action, "item": item}

    def _slide_template_delete(
        self,
        *,
        user: Any,
        phase: str | None,
        target: dict[str, Any] | None,
        proposal_handle: str | None,
        consent_artifact: str | None,
        target_echo: str | None,
        idempotency_key: str | None,
        authorization: str | None,
        transport: str,
    ) -> dict[str, Any]:
        """slide_template delete — sealed proposal + consent artifact (A5)."""
        import hashlib
        import json as _json
        import time as _time
        import uuid as _uuid
        from uuid import UUID

        from tv_app.application.gpt_actions.proposal import (
            VistaProposal,
        )
        from tv_app.application.gpt_actions.proposal_store import (
            load_valid_proposal,
            get_proposal_store,
        )
        from tv_app.application.gpt_actions.vista_consent_service import (
            challenge_view,
        )
        from tv_app.core.security import assert_permission

        user = self._governed_write_user(user, authorization)
        assert_permission(user, TV_TEMPLATES_MANAGE)
        actor = self._actor(user)
        phase_key = str(phase or "prepare").strip().lower()
        if phase_key not in ("prepare", "commit"):
            raise GptActionsError(
                f"Fase desconhecida para delete: {phase_key!r}.",
                code="VALIDATION_ERROR", status_code=422,
            )
        svc = self._template_service()

        if phase_key == "commit":
            if not proposal_handle:
                raise GptActionsError(
                    "commit exige proposal_handle.",
                    code="VALIDATION_ERROR", status_code=422,
                )
            proposal = load_valid_proposal(
                proposal_handle=proposal_handle,
                actor_id=actor,
                expected_capability="delete.slide_template",
            )
            tid_raw = str(
                (proposal.exact_change.get("target") or {}).get("templateId")
                or ""
            ).strip()
            echo = str(target_echo or "").strip()
            if echo != tid_raw:
                raise GptActionsError(
                    "target_echo não corresponde ao alvo selado.",
                    code="CONFIRMATION_MISMATCH", status_code=409,
                )
            if self._consent is None:
                raise GptActionsError(
                    "Canal de consentimento indisponível.",
                    code="CONFIRMATION_UNAVAILABLE", status_code=503,
                )
            challenge = self._consent.verify_for_commit(
                proposal=proposal,
                actor_sub=actor,
                consent_artifact=consent_artifact,
                required=True,
            )
            deleted = svc.delete(UUID(tid_raw))
            self._consent.consume_for_commit(
                challenge=challenge,
                proposal_id=proposal.proposal_id,
                actor_sub=actor,
            )
            get_proposal_store().consume(proposal.proposal_id)
            return {
                "status": "VERIFIED",
                "operation": "delete_slide_template",
                "deleted": deleted,
                "templateId": tid_raw,
            }

        target_map = target if isinstance(target, dict) else {}
        tid_raw = str(target_map.get("templateId") or "").strip()
        if not tid_raw:
            raise GptActionsError(
                "delete.slide_template exige target.templateId.",
                code="VALIDATION_ERROR", status_code=422,
            )
        try:
            tid = UUID(tid_raw)
        except ValueError as exc:
            raise GptActionsError(
                "templateId inválido.",
                code="INVALID_CHANGE", status_code=422,
            ) from exc
        item = svc.get(tid)
        state_fp = hashlib.sha256(
            _json.dumps(item, sort_keys=True, default=str).encode()
        ).hexdigest()
        exact_change = {
            "target": {"templateId": tid_raw},
            "ops": [{"op": "delete_slide_template", "templateId": tid_raw}],
        }
        now = _time.time()
        content_hash = hashlib.sha256(
            _json.dumps(
                {
                    "capability": "delete.slide_template",
                    "actor_id": str(actor),
                    "resource_id": tid_raw,
                    "state": state_fp,
                    "exact_change": exact_change,
                },
                sort_keys=True, default=str,
            ).encode()
        ).hexdigest()
        proposal = VistaProposal(
            proposal_id=f"prop_{_uuid.uuid4().hex[:24]}",
            capability="delete.slide_template",
            actor_id=str(actor),
            resource_type="slide_template",
            resource_id=tid_raw,
            current_state_fingerprint=state_fp,
            exact_change=exact_change,
            confirmation_requirement={
                "explicit_user_confirmation": True,
                "confirmation_policy": "confirm",
                "destructive": True,
            },
            risk="destructive",
            confirmation_policy="confirm",
            catalog_version="",
            base_revision=None,
            created_at=now,
            expires_at=now + 600,
            content_hash=content_hash,
        )
        handle = get_proposal_store().put(proposal)
        if self._consent is None:
            raise GptActionsError(
                "Canal de consentimento indisponível.",
                code="CONFIRMATION_UNAVAILABLE", status_code=503,
            )
        consent_challenge = challenge_view(
            self._consent.issue_for_proposal(
                proposal=proposal,
                actor_sub=actor,
                origin=transport,
                correlation_id=None,
            )
        )
        return {
            "status": "consent_required",
            "phase": "prepare",
            "operation": "delete_slide_template",
            "proposal_handle": handle,
            "consentChallenge": consent_challenge,
            "target": {"templateId": tid_raw},
            "item": item,
        }

    def semantic_execute(
        self,
        *,
        user: Any,
        entity: str,
        action: str,
        phase: str | None = None,
        target: dict[str, Any] | None = None,
        operations: list[Any] | None = None,
        proposal_handle: str | None = None,
        consent_artifact: str | None = None,
        target_echo: str | None = None,
        idempotency_key: str | None = None,
        catalog_version: str | None = None,
        commit_now: bool = False,
        authorization: str | None = None,
        transport: str = "gpt_actions",
    ) -> dict[str, Any]:
        """``execute`` — closed facade over the canonical pipeline.

        ``phase=prepare`` (default): ``operations[]`` + optional
        ``target`` → canonical ``preview_change`` (sealed proposal +
        ``consentChallenge`` when the plan policy is ``confirm``;
        ``commit_now`` is the Actions-only single-shot and is ignored
        for confirm plans by the canonical pipeline).

        ``phase=commit``: ``proposal_handle`` + ``idempotency_key`` +
        ``consent_artifact``/``target_echo`` → canonical
        ``commit_change`` with ``consent_required=True``. The handle
        binds the sealed plan — ``operations[]`` re-sent at commit is
        plan substitution and is rejected (``PLAN_MISMATCH``); no plan
        is ever rebuilt from model output.
        """
        from tv_app.application.gpt_actions.capability_surface import (
            EXECUTE_ENTITIES,
            EXECUTE_PHASES,
        )

        entity_key = str(entity or "").strip()
        if entity_key not in EXECUTE_ENTITIES:
            raise GptActionsError(
                f"Entidade desconhecida para execute: {entity_key!r}.",
                code="UNKNOWN_ENTITY",
                status_code=422,
            )
        action_key = str(action or "").strip()
        if action_key not in EXECUTE_ENTITIES[entity_key]:
            raise GptActionsError(
                f"Ação desconhecida para execute.{entity_key}: {action_key!r}.",
                code="UNKNOWN_ACTION",
                status_code=422,
            )
        if entity_key == "playlist_history":
            return self._playlist_history_restore(
                user=user, target=target,
                authorization=authorization, transport=transport,
            )
        if entity_key == "playlist" and action_key in (
            "share", "create_edit_invite", "accept_edit_invite"
        ):
            return self._share_invite_command(
                user=user,
                action=action_key,
                target=target,
                operations=operations,
                authorization=authorization,
                transport=transport,
            )
        if entity_key in ("playlist", "slide_template") and action_key in (
            "import_preview", "import_apply"
        ):
            return self._mdd_import(
                user=user,
                entity=entity_key,
                action=action_key,
                operations=operations,
                authorization=authorization,
                transport=transport,
            )
        if entity_key == "slide_template":
            return self._slide_template_execute(
                user=user,
                action=action_key,
                target=target,
                operations=operations,
                idempotency_key=idempotency_key,
                authorization=authorization,
                transport=transport,
            )

        phase_key = str(phase or "prepare").strip().lower()
        if phase_key not in EXECUTE_PHASES:
            raise GptActionsError(
                f"Fase desconhecida para execute: {phase_key!r} "
                f"(esperado: {', '.join(EXECUTE_PHASES)}).",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        if phase_key == "commit":
            if operations:
                raise GptActionsError(
                    "operations[] não pertence à fase commit — o "
                    "proposal_handle já vincula o plano selado "
                    "(reenvio seria substituição de plano).",
                    code="PLAN_MISMATCH",
                    status_code=409,
                )
            for field, value in (
                ("target", target),
                ("catalog_version", catalog_version),
                ("commit_now", True if commit_now else None),
            ):
                if value is not None:
                    raise GptActionsError(
                        f"{field} não pertence à fase commit.",
                        code="VALIDATION_ERROR",
                        status_code=422,
                    )
            return self._semantic_commit(
                user=user,
                proposal_handle=str(proposal_handle or ""),
                idempotency_key=idempotency_key,
                consent_artifact=consent_artifact,
                target_echo=target_echo,
                authorization=authorization,
            )

        # phase=prepare — commit-phase fields are out of contract here.
        for field, value in (
            ("proposal_handle", proposal_handle),
            ("consent_artifact", consent_artifact),
            ("target_echo", target_echo),
        ):
            if value is not None and str(value).strip():
                raise GptActionsError(
                    f"{field} não pertence à fase prepare.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
        if commit_now and transport == "mcp":
            # Actions-only envelope mechanic — the MCP projection never
            # carries single-shot; enforced at the canonical boundary.
            raise GptActionsError(
                "commit_now não está disponível neste transporte — use "
                "phase=commit com proposal_handle.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
        ops = self._semantic_operations(operations)
        if not ops:
            raise GptActionsError(
                "execute phase=prepare exige operations[] do catálogo "
                "de typed ops (entradas {op, args?, as?}).",
                code="INVALID_CHANGE",
                status_code=422,
            )
        return self.preview_change(
            user=user,
            target=target if isinstance(target, dict) else {},
            ops=ops,
            catalog_version=catalog_version,
            authorization=authorization,
            commit_now=bool(commit_now),
            idempotency_key=idempotency_key,
            transport=transport,
        )

    def semantic_delete(
        self,
        *,
        user: Any,
        entity: str,
        phase: str | None = None,
        target: dict[str, Any] | None = None,
        proposal_handle: str | None = None,
        consent_artifact: str | None = None,
        target_echo: str | None = None,
        idempotency_key: str | None = None,
        catalog_version: str | None = None,
        authorization: str | None = None,
        transport: str = "gpt_actions",
    ) -> dict[str, Any]:
        """``delete`` — destructive verb over PREPARE/COMMIT + consent.

        ``entity`` ∈ {block, section, slide} (approved delete targets;
        ``delete_data_model``/sources stay forbidden on this surface).
        ``phase=prepare`` seals the delete plan + consent challenge;
        ``phase=commit`` requires the approved ``consent_artifact`` +
        ``target_echo`` — the sealed handle binds the plan (no
        substitution, no confirmation boolean).
        """
        from tv_app.application.gpt_actions.capability_surface import (
            DELETE_ENTITIES,
            EXECUTE_PHASES,
        )

        entity_key = str(entity or "").strip().lower()
        if entity_key in ("playlist_share", "edit_invite"):
            return self._share_invite_delete(
                user=user,
                entity=entity_key,
                phase=phase,
                target=target,
                proposal_handle=proposal_handle,
                consent_artifact=consent_artifact,
                target_echo=target_echo,
                idempotency_key=idempotency_key,
                authorization=authorization,
                transport=transport,
            )
        if entity_key == "playlist":
            return self._playlist_delete(
                user=user, phase=phase, target=target,
                proposal_handle=proposal_handle,
                consent_artifact=consent_artifact,
                target_echo=target_echo,
                idempotency_key=idempotency_key,
                authorization=authorization, transport=transport,
            )
        if entity_key == "slide_template":
            return self._slide_template_delete(
                user=user,
                phase=phase,
                target=target,
                proposal_handle=proposal_handle,
                consent_artifact=consent_artifact,
                target_echo=target_echo,
                idempotency_key=idempotency_key,
                authorization=authorization,
                transport=transport,
            )
        op_name = DELETE_ENTITIES.get(entity_key)
        if op_name is None:
            raise GptActionsError(
                "delete só cobre as entidades aprovadas "
                f"{sorted(DELETE_ENTITIES)}; "
                f"{entity_key!r} não tem contrato aprovado nesta superfície.",
                code="CAPABILITY_NOT_APPROVED",
                status_code=403,
            )
        phase_key = str(phase or "prepare").strip().lower()
        if phase_key not in EXECUTE_PHASES:
            raise GptActionsError(
                f"Fase desconhecida para delete: {phase_key!r}.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
        if phase_key == "commit":
            for field, value in (
                ("target", target),
                ("catalog_version", catalog_version),
            ):
                if value is not None:
                    raise GptActionsError(
                        f"{field} não pertence à fase commit.",
                        code="VALIDATION_ERROR",
                        status_code=422,
                    )
            return self._semantic_commit(
                user=user,
                proposal_handle=str(proposal_handle or ""),
                idempotency_key=idempotency_key,
                consent_artifact=consent_artifact,
                target_echo=target_echo,
                authorization=authorization,
            )
        for field, value in (
            ("proposal_handle", proposal_handle),
            ("consent_artifact", consent_artifact),
            ("target_echo", target_echo),
        ):
            if value is not None and str(value).strip():
                raise GptActionsError(
                    f"{field} não pertence à fase prepare.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
        tgt = target if isinstance(target, dict) else {}
        op: dict[str, Any] = {"op": op_name}
        for key in ("slideId", "sectionId", "blockId", "deleteSlides", "modelId"):
            if key in tgt and tgt[key] is not None:
                op[key] = tgt[key]
        return self.preview_change(
            user=user,
            target=tgt,
            ops=[op],
            catalog_version=catalog_version,
            authorization=authorization,
            commit_now=False,
            transport=transport,
        )

    def get_catalog(self, *, user: Any, transport: str = "actions") -> dict[str, Any]:
        assert_permission(user, TV_WRITE)
        doc = PresentationOpsContentService.capability_catalog_document(
            include_field_vocabulary=(transport == "mcp")
        )
        from tv_app.application.services.data.display_format_service import DisplayFormatService

        doc["displayFormatCatalog"] = [
            {"formatId": entry["formatId"], "spec": entry["spec"]}
            for entry in DisplayFormatService.format_catalog_entries()
        ]
        doc["capability_surface"] = build_capability_surface(transport=transport)
        if transport != "actions":
            # Product Guide discovery index — topic bodies stay on-demand via
            # get_product_guide. MCP-primary projection: the Actions envelope
            # sits at the OpenAI ~100 KiB ceiling and discovers the capability
            # through gpt_get_product_guide + capability_surface instead.
            from tv_app.application.product_guide.product_guide_registry import (
                get_product_guide_registry,
            )
            from tv_app.application.product_guide.product_guide_service import (
                guide_index_payload,
            )

            doc["productGuide"] = guide_index_payload(get_product_guide_registry())
        return doc

    def get_product_guide(
        self,
        *,
        user: Any,
        topic: str | None = None,
        section: str | None = None,
    ) -> dict[str, Any]:
        """Read-only Product Guide surface — GUIDANCE_NOT_DOMAIN_TRUTH.

        Never domain state, never AuthZ: visibility of a capability in the
        guide does not imply permission to execute it.
        """
        assert_permission(user, TV_READ)
        from tv_app.application.product_guide.product_guide_service import (
            ProductGuideService,
        )

        return ProductGuideService().get_product_guide(topic=topic, section=section)

    def list_display_formats(self, *, user: Any) -> dict[str, Any]:
        """Read-only display-format catalog — ``read.display_format.list``.

        TV_READ projection over the canonical owner services; never a
        second registry and never the TV_WRITE administrative
        ``get_catalog()`` document. Answers "which data-visualization
        formats exist": display modes + declared data-block bindings,
        data/view block types, canonical block vocabulary and the
        value-display format catalog.
        """
        assert_permission(user, TV_READ)
        from tv_app.application.services.data.display_format_service import (
            DisplayFormatService,
        )
        from tv_app.application.services.data.presentation_ops_content_service import (
            PresentationOpsContentService,
        )
        from tv_app.application.services.data.tv_data_presentation_modes_service import (
            supported_display_modes,
        )
        from tv_app.application.services.tv_data_route_catalog_service import (
            DATA_BLOCK_TYPES,
            DATA_VIEW_BLOCK_TYPES,
        )

        return {
            "entity": "display_format",
            "displayModes": supported_display_modes(),
            "dataBlockTypes": sorted(DATA_BLOCK_TYPES),
            "dataViewBlockTypes": sorted(DATA_VIEW_BLOCK_TYPES),
            "blockTypeVocabulary": (
                PresentationOpsContentService.block_type_vocabulary()
            ),
            "displayFormats": [
                {
                    "formatId": entry["formatId"],
                    "category": entry["category"],
                    "label": entry["label"],
                    "pattern": entry.get("pattern"),
                    "compatibleTypes": list(entry["compatibleTypes"]),
                }
                for entry in DisplayFormatService.format_catalog_entries()
            ],
        }

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

    def get_playlist_history(
        self,
        *,
        user: Any,
        playlist_id: str,
        snapshot_id: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """P9 V1 — read-only semantic history digest.

        Reuses the canonical Playlist history domain end-to-end: AuthZ via
        PlaylistAccessService (need=read), persistence/retention/diff via
        PlaylistHistoryRepository + PlaylistHistoryChangeService. Projects
        only a bounded digest — never raw snapshots, never author id/email,
        never block-level claims. snapshot_id absent → list mode; present →
        detail mode (same bounded digest, cross-playlist isolated by the
        repository's scoped lookup).
        """
        from tv_app.application.services.playlist_history_digest_service import (
            PlaylistHistoryNotFoundError,
            history_detail_projection,
            history_list_projection,
        )

        assert_permission(user, TV_READ)
        pid_raw = str(playlist_id or "").strip()
        if not pid_raw:
            raise GptActionsError(
                "playlistId é obrigatório.", code="INVALID_CHANGE", status_code=422
            )
        try:
            pid = UUID(pid_raw)
            sid = UUID(str(snapshot_id)) if snapshot_id else None
        except ValueError as exc:
            raise GptActionsError(
                "playlistId/snapshotId inválidos.",
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
        repo = self._history
        if repo is None:
            raise GptActionsError(
                "Histórico indisponível.",
                code="INTERNAL_ERROR",
                status_code=500,
            )
        if sid is not None:
            try:
                item = repo.get_history(pid, sid)
            except PlaylistHistoryNotFoundError as exc:
                raise GptActionsError(
                    "Versão do histórico não encontrada.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                ) from exc
            return history_detail_projection(item)
        payload = repo.list_history(pid, page=page, page_size=page_size)
        return history_list_projection(payload, playlist_id=str(pid))

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
        data_source_id: str | None = None,
        include_runtime: bool = False,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        from tv_app.application.gpt_actions.response_compact import (
            exceeds_actions_budget,
            focused_binding_from_blocks,
            classify_selection_state,
            iter_block_index_items,
            pick_focus_slide_id,
            project_block_index,
            project_data_models_from_slide,
            project_data_sources_from_slide,
            project_editor_focus_context,
            project_media_inventory,
            project_object_matches,
            project_playlist_summary,
            project_selected_objects,
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
        # DataModel addressability: derived from persisted nativeConfig +
        # persisted block bindings (modelId > dataSourceId). Ids are never
        # inferred from labels/fields/blockIds — inspect_data_model carries
        # the full definition after discovery.
        data_models = project_data_models_from_slide(
            detail_slide if isinstance(detail_slide, dict) else None
        )
        focused_binding = focused_binding_from_blocks(
            native_for_index.get("blocks"),
            (editor_focus or {}).get("selectedIds"),
        )
        if editor_focus is not None:
            # Grounding projection: resolve selectedIds against the persisted
            # detail slide (authoritative) — focus ids are hints, not state.
            selected_objects, missing_ids = project_selected_objects(
                native_for_index,
                editor_focus.get("selectedIds"),
            )
            editor_focus = {
                **editor_focus,
                "selectionState": classify_selection_state(
                    had_selection=bool(editor_focus.get("selectedIds")),
                    resolved_count=len(selected_objects),
                    stale=bool(editor_focus.get("stale")),
                ),
                "selectedObjects": selected_objects,
                "missingIds": missing_ids,
            }
            from tv_app.application.services.data.vista_quality_telemetry import (
                record_grounding,
            )

            record_grounding(
                selection_state=editor_focus["selectionState"],
                resolved=len(selected_objects),
                missing=len(missing_ids),
            )

        # Inspeção focada de data_source legado: bounded à fonte + deps dela.
        # Sem data_source_id o comportamento do contexto é inalterado;
        # include_runtime sem fonte focada é ignorado (nunca runtime do slide
        # inteiro por acidente).
        focused_did = str(data_source_id or "").strip()
        focused_payload: dict[str, Any] | None = None
        if focused_did:
            focused_payload = self._inspect_data_source(
                slide_row=self._find_data_source_host_slide(
                    slides,
                    data_source_id=focused_did,
                    preview_slide_id=preview_slide_id,
                ),
                data_source_id=focused_did,
                user=user,
                authorization=authorization,
                playlist_defaults=programming_defaults,
                include_runtime=include_runtime,
            )

        if focused_scope:
            focused_ctx = project_editor_focus_context(
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
                data_models=data_models,
                focused_binding=focused_binding,
            )
            if focused_payload is not None:
                focused_ctx["focusedDataSource"] = focused_payload
            return focused_ctx

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
                "dataModels[] lists DataModel ids + compact summaries for the focused slide. "
                "If this response is too large, the API auto-downgrades to scope=editorFocus "
                "and retains blockIndex + dataSources[] + dataModels[] (no invented blockIds). "
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
            preview_svc = get_slide_preview_render_service()
            slide_preview = preview_svc.build_preview_payload(
                playlist_id=str(pid),
                slide_id=str(slide["id"]),
                revision=revision,
                native_config=slide.get("nativeConfig")
                if isinstance(slide.get("nativeConfig"), dict)
                else {},
                title=str(slide.get("title") or "") or None,
            )
            rendered = preview_svc.build_rendered_payload(
                playlist_id=str(pid),
                slide_id=str(slide["id"]),
                revision=revision,
                renderable=str(slide.get("slideType") or "native") == "native",
            )
            rendered = self._apply_live_editor_visual_policy(
                playlist_id=pid,
                slide=slide,
                revision=revision,
                actor=actor,
                rendered=rendered,
                preview_svc=preview_svc,
            )
            slide_preview["rendered"] = rendered
            out["slidePreview"] = slide_preview

        if focused_payload is not None:
            out["focusedDataSource"] = focused_payload

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
                data_models=data_models,
                focused_binding=focused_binding,
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
        if str(claims.get("artifact") or "") == "canonical_stage":
            png = get_slide_preview_render_service().read_rendered_png(
                slide_id=str(slide["id"]),
                revision=token_rev or current_rev,
            )
            if not png:
                raise GptActionsError(
                    "Artifact renderizado expirou. Peça gpt_get_playlist_context com includePreview.",
                    code="PREVIEW_ARTIFACT_EXPIRED",
                    status_code=404,
                )
            return png, {
                "playlistId": claims["playlistId"],
                "slideId": claims["slideId"],
                "revision": current_rev or token_rev,
                "artifact": "canonical_stage",
            }
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

    # VISTA-LIVE-EDITOR-VISUAL-VERIFICATION-003 — canonical_stage só conta como
    # evidência visual quando vem do palco visível do editor do próprio usuário.
    _LIVE_ARTIFACT_MAX_AGE_SECONDS = 300.0
    _CAPTURE_REQUEST_RESEND_SECONDS = 8.0

    def _apply_live_editor_visual_policy(
        self,
        *,
        playlist_id: UUID,
        slide: dict[str, Any],
        revision: int,
        actor: str,
        rendered: dict[str, Any],
        preview_svc: Any,
    ) -> dict[str, Any]:
        """Policy canônica de evidência visual: editor ao vivo ou nada.

        Sem editor focado/online do usuário autenticado → ``EDITOR_NOT_OPEN``.
        Editor vivo com o slide visível + artifact com proveniência válida →
        ``ready``. Editor vivo sem artifact → pede captura ao palco visível via
        realtime e responde ``EDITOR_CAPTURE_PENDING`` (retry bounded do caller).
        """
        import time as _time

        from tv_app.application.services.editor_focus_store import editor_focus_store
        from tv_app.application.services.presentation_realtime_hub import (
            presentation_realtime_hub,
        )

        slide_id = str(slide.get("id") or "")
        base = {
            "kind": "canonical_stage",
            "source": "editor_live",
            "revision": revision,
        }
        if rendered.get("failureCode") == "UNSUPPORTED_SLIDE_TYPE":
            return rendered

        focus = (
            editor_focus_store.get_for_user_playlist(actor, str(playlist_id))
            if actor
            else None
        )
        client_id = str((focus or {}).get("clientId") or "").strip()
        live = bool(
            focus
            and not focus.get("stale")
            and client_id
            and presentation_realtime_hub.is_editor_client_live(
                str(playlist_id), user_id=actor, client_id=client_id
            )
        )
        if not live:
            return {
                **base,
                "status": "unavailable",
                "failureCode": "EDITOR_NOT_OPEN",
            }
        if str(focus.get("slideId") or "") != slide_id:
            return {
                **base,
                "status": "unavailable",
                "failureCode": "EDITOR_SLIDE_NOT_OPEN",
            }

        meta = preview_svc.rendered_artifact_meta(
            slide_id=slide_id, revision=revision
        )
        captured_at = float((meta or {}).get("uploadedAt") or 0)
        fresh = bool(captured_at) and (
            _time.time() - captured_at <= self._LIVE_ARTIFACT_MAX_AGE_SECONDS
        )
        if (
            meta
            and meta.get("source") == "editor_live"
            and str(meta.get("clientId") or "") == client_id
            and fresh
        ):
            rendered["source"] = "editor_live"
            rendered["capturedAt"] = captured_at
            return rendered

        key = (str(actor), slide_id, str(revision))
        last = self._capture_request_last.get(key) or 0.0
        if _time.monotonic() - last >= self._CAPTURE_REQUEST_RESEND_SECONDS:
            from uuid import uuid4

            sent = presentation_realtime_hub.request_visual_capture(
                playlist_id=str(playlist_id),
                user_id=actor,
                client_id=client_id,
                slide_id=slide_id,
                revision=revision,
                request_id=uuid4().hex,
            )
            if sent:
                self._capture_request_last[key] = _time.monotonic()
        return {
            **base,
            "status": "pending",
            "failureCode": "EDITOR_CAPTURE_PENDING",
        }

    def _solution_intelligence_on_miss(
        self, query: str, authorization: str | None
    ) -> dict[str, Any]:
        """Bounded Core solution-catalog lookup for a TV route miss.

        Called ONLY when the allowlist search returned nothing. User-parity:
        forwards the caller's Bearer — no service token, no elevation.
        Fail-closed: any gateway/contract/auth failure becomes CONTRACT_GAP,
        never a fabricated answer or a false-absence claim.
        """
        from tv_app.application.services.solution_intelligence_service import (
            SolutionIntelligenceService,
        )

        try:
            gateway = self._solutions
            if gateway is None:
                raise GptActionsError(
                    "Integração de soluções não configurada.",
                    code="SOLUTION_CATALOG_UNAVAILABLE",
                    status_code=503,
                    details={"error_kind": "not_configured"},
                )
            if not (authorization or "").strip():
                raise GptActionsError(
                    "Usuário não autenticado.",
                    code="UNAUTHENTICATED",
                    status_code=401,
                    details={"error_kind": "authn"},
                )
            solutions = gateway.list_solutions(authorization)
        except GptActionsError as exc:
            details = getattr(exc, "details", None) or {}
            return SolutionIntelligenceService.contract_gap(
                details.get("error_kind")
            )
        return SolutionIntelligenceService().classify(query, solutions)

    def search_data_routes(
        self,
        *,
        user: Any,
        query: str | None = None,
        limit: int = 8,
        category: str | None = None,
        authorization: str | None = None,
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
        response: dict[str, Any] = {
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
        if not items:
            response["solutionIntelligence"] = (
                self._solution_intelligence_on_miss(q, authorization)
            )
        else:
            # Typed outcome resolved before any ecosystem escalation —
            # a route hit never triggers a Core lookup.
            from tv_app.application.services.solution_intelligence_service import (
                SolutionIntelligenceService,
            )

            response["solutionIntelligence"] = (
                SolutionIntelligenceService.route_found()
            )
        # P7 — bounded quality signal: route hit/miss + ecosystem outcome.
        # Enums and buckets only; no query text or solution ids recorded.
        from tv_app.application.services.data.vista_quality_telemetry import (
            record_route_search,
        )

        intel = response.get("solutionIntelligence") or {}
        lookup_used = bool(intel) and not items
        if intel.get("reason") in {"not_configured", "authn"}:
            # Fail-closed before the gateway was ever invoked — not a lookup.
            lookup_used = False
        record_route_search(
            tv_route_hit=bool(items),
            solution_lookup_used=lookup_used,
            gap_classification=intel.get("gapClassification"),
            candidates=len(intel.get("candidates") or []),
        )
        return response

    @staticmethod
    def _preview_context_config(
        *,
        block: dict[str, Any],
        explicit_native: dict[str, Any] | None,
        slide_native: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Contexto do preview: candidate (nativeConfig) > slide persistido.

        O bloco alvo é upsert por id dentro do cfg de contexto para que
        siblings de merge fiquem materializáveis pelo resolver canônico.
        """
        base = (
            explicit_native
            if isinstance(explicit_native, dict)
            else slide_native
            if isinstance(slide_native, dict)
            else {"version": 1, "blocks": []}
        )
        cfg = copy.deepcopy(base)
        cfg.setdefault("version", 1)
        items = cfg.get("blocks")
        if not isinstance(items, list):
            items = []
            cfg["blocks"] = items
        target_id = str(block.get("id") or "")
        if target_id:
            for index, candidate in enumerate(items):
                if (
                    isinstance(candidate, dict)
                    and str(candidate.get("id") or "") == target_id
                ):
                    items[index] = block
                    break
            else:
                items.append(block)
        else:
            items.append(block)
        return cfg

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
        slide_id = str(body.get("slideId") or "").strip()
        block_id = str(body.get("blockId") or "").strip()
        slide_native: dict[str, Any] | None = None
        if slide_id:
            if not playlist_id:
                raise GptActionsError(
                    "slideId requer playlistId para resolver o contexto autorizado.",
                    code="INVALID_CHANGE",
                    status_code=422,
                )
            try:
                slide_row = self._writes.get_slide(UUID(slide_id), playlist_id=pid)
            except Exception as exc:
                raise GptActionsError(
                    "Tela não encontrada.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                ) from exc
            raw_native = slide_row.get("nativeConfig")
            slide_native = raw_native if isinstance(raw_native, dict) else {"version": 1}
        elif block_id and block_in is None and native_in is None:
            raise GptActionsError(
                "blockId requer slideId (persistido) ou nativeConfig (candidate).",
                code="INVALID_CHANGE",
                status_code=422,
            )
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
            native_config = self._preview_context_config(
                block=block,
                explicit_native=native_in,
                slide_native=slide_native,
            )
        elif block_in is not None:
            block = block_in
            native_config = self._preview_context_config(
                block=block,
                explicit_native=native_in,
                slide_native=slide_native,
            )
        elif block_id and slide_native is not None:
            # Persisted contextual preview: bloco já existe no slide autorizado.
            block = {}
            native_config = copy.deepcopy(slide_native)
        else:
            raise GptActionsError(
                "Informe operationId+params, block(+nativeConfig) ou "
                "playlistId+slideId+blockId.",
                code="INVALID_CHANGE",
                status_code=422,
            )

        try:
            cfg = self._validation.sanitize(native_config)
            # Alvo sempre resolvido dentro do cfg sanitizado (persistido ou
            # candidate) — mesmo objeto que o enrich materializa.
            target_id = block_id or str(block.get("id") or "")
            if target_id:
                target = next(
                    (
                        item
                        for item in (cfg.get("blocks") or [])
                        if isinstance(item, dict)
                        and str(item.get("id") or "") == target_id
                    ),
                    None,
                )
                if target is None:
                    raise GptActionsError(
                        "Bloco não encontrado no contexto do slide.",
                        code="RESOURCE_NOT_FOUND",
                        status_code=404,
                    )
                block = target
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
        preview_error: dict[str, Any] | None = None
        resolved = block.get("resolved") if isinstance(block, dict) else None
        if isinstance(resolved, dict):
            transform_error = resolved.get("transformError")
            if isinstance(transform_error, dict):
                preview_error = {
                    "code": transform_error.get("code") or "m.execution_error",
                    "message": str(resolved.get("error") or transform_error.get("message") or ""),
                    "blockId": str(block.get("id") or "") or None,
                    "stage": "transform",
                }
            elif resolved.get("error"):
                preview_error = {
                    "code": "DATA_RESOLUTION_FAILED",
                    "message": str(resolved.get("error")),
                    "blockId": str(block.get("id") or "") or None,
                    "stage": "resolution",
                }
        if preview_error:
            response["ok"] = False
            response["error"] = preview_error
        # PHASE 5 methodology eval — readiness/evidence contract over the same
        # digest; never blocks preview and never fabricates a strategy on
        # failure (preview_error → BLOCKED / NO_SAFE_RECOMMENDATION).
        methodology = DesignIntelligenceService.evaluate_methodology(
            intent="CHOOSE_VISUAL",
            digest=digest,
            dominant_family=dominant,
            has_data_source=bool(operation_id or route),
            preview_error=preview_error,
        )
        methodology.pop("_fabricated", None)
        response["designMethodology"] = methodology
        # P7 — bounded quality signal: intent/readiness/sufficiency enums.
        from tv_app.application.services.data.vista_quality_telemetry import (
            record_design_methodology,
        )

        record_design_methodology(
            design_intent="CHOOSE_VISUAL",
            readiness=methodology.get("readiness"),
            sufficiency=methodology.get("sufficiency"),
        )
        return response

    @staticmethod
    def _field_name(item: Any) -> str:
        """Canonical field identity — structured descriptors carry their own
        name (``name``/``key``/``field``); never stringify the descriptor."""
        if isinstance(item, dict):
            for attr in ("name", "key", "field"):
                value = item.get(attr)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return ""
        return str(item or "").strip()

    @classmethod
    def _columns_from_preview_block(cls, block: dict[str, Any]) -> list[str]:
        resolved = block.get("resolved") if isinstance(block.get("resolved"), dict) else {}
        for key in ("columns", "schemaColumns", "fields"):
            raw = resolved.get(key) if resolved else None
            if isinstance(raw, list) and raw:
                return [name for item in raw if (name := cls._field_name(item))]
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

    # Explicit selection carriers — presence (even empty) disables fallback.
    _EXPLICIT_SELECTION_CARRIERS = (
        "selectedBlockIds",
        "selectedBlockId",
        "focusBlockId",
    )

    def _merge_editor_focus_selection(
        self,
        host: dict[str, Any],
        *,
        user: Any,
    ) -> dict[str, Any]:
        """Bounded editor-focus fallback for suggest_change grounding.

        Explicit host_context selection always wins; a carrier key present
        but empty is still explicit (OMITTED != EMPTY). The fallback only
        enriches a missing selection — it never retargets an explicit slide
        scope, never invents ids, and authorizes nothing (AuthZ remains with
        PREPARE/ACT; access.can_read gates even the merge).
        """
        if any(key in host for key in self._EXPLICIT_SELECTION_CARRIERS):
            return host
        playlist_id = str(host.get("playlistId") or "").strip()
        if not playlist_id:
            return host
        actor = self._access.actor_id(user)
        if not actor:
            return host
        from tv_app.application.services.editor_focus_store import (
            editor_focus_store,
        )

        focus = editor_focus_store.get_for_user_playlist(actor, playlist_id)
        if not focus:
            return host
        focus_slide = str(focus.get("slideId") or "").strip()
        explicit_slide = str(host.get("slideId") or "").strip()
        if not focus_slide or (explicit_slide and explicit_slide != focus_slide):
            return host
        try:
            pid = UUID(playlist_id)
        except ValueError:
            return host
        access = self._access.resolve(pid, user)
        if not getattr(access, "can_read", False):
            return host
        try:
            slide = self._writes.get_slide(UUID(focus_slide), playlist_id=pid)
        except Exception:
            return host
        native = slide.get("nativeConfig") if isinstance(slide, dict) else None
        from tv_app.application.gpt_actions.response_compact import (
            project_selected_objects,
        )

        objects, _missing = project_selected_objects(native, focus.get("selectedIds"))
        if not objects:
            return host
        enriched = dict(host)
        enriched["selectedBlockIds"] = [str(o.get("id")) for o in objects]
        enriched["selectedBlockTypes"] = [str(o.get("type") or "") for o in objects]
        if not explicit_slide:
            enriched["slideId"] = focus_slide
        return enriched

    def suggest_change(
        self,
        *,
        user: Any,
        message: str,
        host_context: dict[str, Any] | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        assert_permission(user, TV_WRITE)
        host = host_context if isinstance(host_context, dict) else {}
        host = self._merge_editor_focus_selection(host, user=user)
        plan = PresentationCommandPlannerService.plan(
            message=message,
            host_context=host,
            user=user,
            authorization=authorization,
        )
        payload = PresentationCommandPlannerService.to_suggest_payload(plan)
        # PHASE 5 — bounded methodology advisory for high-level design intents
        # only. Direct typed commands bypass it; ops/policy stay canonical.
        intent = DesignIntelligenceService.design_intent_for_message(message)
        # DI-DESIGN-02 — um add_blank_slide solitário não satisfaz um
        # pedido de composição com requisitos de design; só vale `ready`
        # sem recipe quando o pedido é realmente só "slide vazio".
        _ops_out = payload.get("ops") or []
        _has_visual_ops = any(
            isinstance(o, dict)
            and str(o.get("op") or "") == "upsert_block"
            for o in _ops_out
        )
        import unicodedata as _unic
        _msg_norm = "".join(
            c
            for c in _unic.normalize(
                "NFD", str(message or "").lower()
            )
            if _unic.category(c) != "Mn"
        )
        _has_design_req = any(
            t in _msg_norm
            for t in (
                "kpi", "grafic", "tabela", "titulo",
                "hierarqu", "indicador", "tendenc",
                "visual", "design", "layout", "contraste",
                "identidade", "tipograf",
            )
        )
        if (
            intent == "COMPOSE_SLIDE"
            and (
                str(payload.get("status") or "")
                in {"unsupported", "not_command", "selection_pending"}
                and not payload.get("ops")
                or (
                    str(payload.get("status") or "") == "ready"
                    and _has_design_req
                    and not _has_visual_ops
                )
            )
        ):
            from tv_app.application.services.data.presentation_recipe_service import (
                PresentationRecipeService,
            )

            recipe = PresentationRecipeService.resolve_from_nl(message)
            if recipe:
                ops = PresentationRecipeService.ops_for_recipe(
                    recipe.recipe_id
                )
                if ops:
                    # DI-E2E-DESIGN-01 — recipe de tema (só patch) não
                    # satisfaz pedido de composição: mantém o tema e
                    # concatena a recipe genérica de componentes.
                    _has_blocks = any(
                        isinstance(o, dict)
                        and str(o.get("op") or "") == "upsert_block"
                        for o in ops
                    )
                    if _has_design_req and not _has_blocks:
                        composed = PresentationRecipeService.ops_for_recipe(
                            "TV_KPI_SERIES_TABLE"
                        )
                        theme_ops = ops
                        ops = [
                            o for o in theme_ops
                            if str(o.get("op") or "")
                            == "patch_native_config"
                        ] + [
                            o for o in composed
                            if str(o.get("op") or "")
                            != "patch_native_config"
                            or not any(
                                str(t.get("op") or "")
                                == "patch_native_config"
                                for t in theme_ops
                            )
                        ]
                    payload["status"] = "proposal"
                    payload["recipeId"] = recipe.recipe_id
                    if recipe.theme_key:
                        payload["themeKey"] = recipe.theme_key
                    payload["ops"] = ops
                    payload["matchedCapabilityKeys"] = [
                        f"recipe:{recipe.recipe_id}"
                    ]
                    payload["clarificationKey"] = None
                    payload["reason"] = None
            else:
                # Sem marker de recipe: se o pedido produz fontes
                # qualificadas no catálogo canônico, compõe por recipe
                # genérica do shape dominante — cobertura de intenção
                # (ex.: auditorias 5S -> tabela de NCs) sem engine nova.
                generic = None
                try:
                    rr = self._suggest.suggest(query=message, limit=6)
                    sugg = (
                        rr.get("suggestions") or []
                        if isinstance(rr, dict) else []
                    )
                    shapes = {
                        str(c.get("metaShape") or "")
                        for c in sugg[:3]
                        if isinstance(c, dict)
                    }
                    top_score = max(
                        (
                            float(c.get("score") or 0.0)
                            for c in sugg
                            if isinstance(c, dict)
                        ),
                        default=0.0,
                    )
                    # gate semântico (DI-3.6.3): score isolado não
                    # prova relevância (gibberish pode pontuar alto) —
                    # exige um token forte da mensagem presente no
                    # contrato dos top candidatos + domínio real.
                    stop = {
                        "crie", "criar", "quero", "uma", "painel",
                        "acompanhar", "mostrar", "para", "com", "das",
                        "dos", "que", "fábrica", "resultados",
                        "iniciativas", "mostrando", "coisas", "sinal",
                    }
                    tokens = {
                        t.strip(".,;:!?()\"'")
                        for t in str(message or "").lower().split()
                        if len(t.strip(".,;:!?()\"'")) >= 4
                    } - stop
                    token_hit = any(
                        any(
                            tok in (
                                str(c.get("operationId") or "")
                                + str(c.get("label") or "")
                                + str(c.get("description") or "")
                                + str(c.get("path") or "")
                            ).lower()
                            for tok in tokens
                        )
                        for c in sugg[:3]
                        if isinstance(c, dict)
                    )
                    domain_hit = any(
                        str(c.get("category") or "")
                        not in {"", "other"}
                        and float(c.get("score") or 0.0) >= 6.0
                        for c in sugg
                        if isinstance(c, dict)
                    )
                    if sugg and top_score >= 6.0 and domain_hit and token_hit:
                        generic = (
                            "TV_TABLE_FOCUS"
                            if shapes <= {
                                "list", "paged_list", "hierarchy",
                            }
                            else "TV_KPI_SERIES_TABLE"
                        )
                    elif _has_design_req:
                        # pedido de composição visual não depende de
                        # fonte — recipe genérica pelos componentes.
                        generic = "TV_KPI_SERIES_TABLE"
                except Exception:
                    sugg = []
                if generic:
                    ops = PresentationRecipeService.ops_for_recipe(
                        generic
                    )
                    if ops:
                        payload["status"] = "proposal"
                        payload["recipeId"] = generic
                        payload["ops"] = ops
                        payload["matchedCapabilityKeys"] = [
                            f"recipe:{generic}"
                        ]
                        payload["clarificationKey"] = None
                        payload["reason"] = None
                    else:
                        payload["status"] = "unsupported"
                        payload["compositionHints"] = (
                            PresentationRecipeService.recipe_ids()[:10]
                        )
                else:
                    payload["status"] = "unsupported"
                    payload["compositionHints"] = (
                        PresentationRecipeService.recipe_ids()[:10]
                    )
        # DI-3.3 — plano de binding para blocos de dados (paths recipe e
        # planner-ready): descoberta canônica de rotas (read-only); nunca
        # inventa fonte — RESOLVED / NEEDS_SOURCE_SELECTION /
        # NEEDS_CONTEXT tipados honestamente.
        ops_list = payload.get("ops")
        if isinstance(ops_list, list) and ops_list:
            data_ops = [
                op for op in ops_list
                if isinstance(op, dict)
                and (
                    str((op.get("block") or {}).get("type") or "")
                    in {"kpi_view", "chart_view", "data_kpi",
                        "data_chart", "data_table", "canvas_table",
                        "table_view"}
                    or str(op.get("op") or "") == "create_data_block"
                )
            ]
            if data_ops:
                try:
                    route_result = self._suggest.suggest(
                        query=message, limit=20
                    )
                    candidates = (
                        route_result.get("suggestions") or []
                        if isinstance(route_result, dict) else []
                    )
                except Exception:
                    candidates = []

                def _purpose_query(btype, chart_type):
                    # refinamento semântico por propósito do bloco —
                    # alinha o ranking lexical com a pergunta real
                    # do componente (DI-3.6).
                    if btype in {"kpi_view", "data_kpi"}:
                        return f"{message} indicador valor atual"
                    if btype in {"chart_view", "data_chart"}:
                        ct = str(chart_type or "").lower()
                        suffix = "série evolução período" if ct in {
                            "line", "area"
                        } else "comparação ranking categorias"
                        return f"{message} {suffix}"
                    if btype in {
                        "table_view", "data_table", "canvas_table",
                    }:
                        return f"{message} lista detalhes problemas"
                    return message

                def _suggest_for(q):
                    try:
                        rr = self._suggest.suggest(query=q, limit=20)
                        return (
                            rr.get("suggestions") or []
                            if isinstance(rr, dict) else []
                        )
                    except Exception:
                        return []

                # DI-3.4 — qualificação por contrato: document_export /
                # não-GET não são fontes de bloco de dashboard.
                def _eligible(cand):
                    # DI-3.6.3 — elegibilidade unificada: não-GET e
                    # shapes documentais fora; rotas de download/
                    # export retornam binário/anexo por contrato de
                    # operação — metaShape=scalar derivado é drift.
                    if not isinstance(cand, dict):
                        return False
                    if str(cand.get("httpMethod") or "GET").upper() != "GET":
                        return False
                    if str(cand.get("metaShape") or "") == "document_export":
                        return False
                    oid = str(cand.get("operationId") or "").lower()
                    return not oid.startswith(
                        ("download_", "export_", "upload_", "import_")
                    )

                qualified = [cand for cand in candidates if _eligible(cand)]
                # DI-3.6.1 — business domain anchoring: a mensagem
                # original (sem sufixo de propósito) define os domínios
                # relevantes; sufixos de propósito nunca podem promover
                # fontes cross-domain (get_openapi_diff, series
                # comerciais, auditorias 5S) para pedidos de produção.
                _anchor_top = max(
                    (float(c.get("score") or 0.0) for c in qualified),
                    default=0.0,
                )
                anchor_categories = {
                    str(c.get("category") or "").strip()
                    for c in qualified
                    if _anchor_top > 0
                    and float(c.get("score") or 0.0)
                    >= _anchor_top * 0.7
                    and str(c.get("category") or "").strip()
                }
                # multi-intent (DI-3.6.3): domínios citados
                # explicitamente na mensagem ancoram sua categoria
                # mesmo cortados pelo limit do ranking — "produtividade
                # e auditorias 5S" preserva production E quality.
                _mtok = {
                    t.strip(".,;:!?()\"'")
                    for t in str(message or "").lower().split()
                    if len(t.strip(".,;:!?()\"'")) >= 4
                } - {
                    "crie", "criar", "quero", "uma", "painel",
                    "acompanhar", "mostrar", "para", "com", "das",
                    "dos", "que", "resultados", "iniciativas",
                    "mostrando", "coisas", "sinal",
                    # DI-3.7.1 — contexto escopifica, não é objetivo:
                    "fabrica", "fábrica", "filial", "unidade",
                    "setor", "planta", "empresa", "período",
                    "periodo", "televisao", "televisão",
                    # DI-E2E — self-name, qualificadores e requisitos
                    # de design não são objetivos de negócio:
                    "vista", "delpi", "atual", "atualmente",
                    "identidade", "visual", "industrial",
                    "industria", "profissional", "dashboard",
                    "playlist", "lab", "slide", "destaque",
                    "compare", "comparacao",
                    "comparação", "utilize", "organize",
                    "elementos", "hierarquia", "contraste",
                    "tipografia", "adequada", "evolucao",
                    "evolução", "ultimos", "últimos", "apresente",
                    "mostre", "acompanhar", "dias", "horas",
                    "minutos", "semanas", "meses",
                    # DI-E2E-DESIGN-01R — palavras de instrução e
                    # função gramatical não são objetivos de negócio:
                    "desenvolva", "desenvolver", "usando", "mantendo",
                    "mantenha", "inventar", "fontes", "oficiais",
                    "oficial", "dados", "reais", "deste", "desta",
                    "este", "esta", "essa", "esse", "neste", "nesse",
                    "nesta",
                    # instruções de remoção/design não são objetivos de
                    # negócio — justificavam fontes erradas (#129 C04):
                    "remova", "remover", "removendo", "antiga",
                    "antigo", "antigas", "antigos", "preserve",
                    "preservar", "preservando", "sobreposição",
                    "sobreposicao", "realizado", "realizada",
                    "redesenhe", "redesenhar", "redesign",
                    "reorganize", "reorganizar", "reorganização",
                    "refaca", "refaça", "refazer", "rework",
                    "substitua", "substituir", "substituição",
                    "composicao", "composição", "parte", "tabela",
                    "também", "tambem", "então", "entao", "cada",
                    "quando", "onde", "como", "deve", "deveria",
                    "preciso", "precisa", "gostaria", "poderia",
                    "faça", "faca", "seja", "sejam", "sendo",
                    "tenha", "tenho", "são", "sao", "apenas",
                    "ainda", "assim", "depois", "antes", "sobre",
                    "entre", "sem", "com", "por", "dos", "das",
                    "nos", "nas", "aos", "às", "aos", "sua", "seu",
                    "suas", "seus", "nossos", "nossas", "um", "uma",
                    "dos", "das", "ele", "ela", "eles", "elas",
                    # design/formato solicitado — não é indicador:
                    "gráfico", "grafico", "gráficos", "titulo",
                    "título", "títulos", "design", "layout",
                    "formato", "resolução", "resolucao", "1080p",
                    "4k", "alto", "alta", "claro", "clara",
                    "limpo", "limpa", "bonito", "bonita",
                    "moderno", "moderna", "elegante", "simples",
                    "executivo", "executiva", "corporativo",
                    "corporativa", "minimalista", "equilibrado",
                    "equilibrada", "elementos", "tendencia",
                    "tendência", "evolução", "histórica",
                    "historica", "atualização", "atualizacao",
                }
                goal_map: dict[str, dict] = {}
                # contexto escopifica a busca mas não é objetivo —
                # parceiros de pairing usam TODOS os tokens fortes.
                _all_tok = {
                    t.strip(".,;:!?()\"'")
                    for t in str(message or "").lower().split()
                    if len(t.strip(".,;:!?()\"'")) >= 4
                } - {
                    "crie", "criar", "quero", "uma", "painel",
                    "acompanhar", "mostrar", "para", "com", "das",
                    "dos", "que", "resultados", "iniciativas",
                    "mostrando", "coisas", "sinal",
                }
                # DI-E2E — tokens de métrica curtos ("oee", "kpi")
                # viram objetivos quando há evidência direta nos
                # operationIds elegíveis do catálogo.
                _metric_tok = {
                    t.strip(".,;:!?()\"'")
                    for t in str(message or "").lower().split()
                    if 3 <= len(t.strip(".,;:!?()\"'")) < 4
                }
                _metric_tok = {
                    t
                    for t in _metric_tok
                    if any(
                        t
                        in str(
                            c.get("operationId") or ""
                        ).split("_")
                        for c in qualified
                    )
                }
                _mtok |= _metric_tok
                _all_tok |= _metric_tok
                if _mtok:
                    anchor_categories |= {
                        str(c.get("category") or "").strip()
                        for c in qualified
                        if str(c.get("category") or "").strip()
                        and any(
                            tok in (
                                str(c.get("operationId") or "")
                                + str(c.get("label") or "")
                                + str(c.get("description") or "")
                            ).lower()
                            for tok in _mtok
                        )
                    }
                    # cobertura multi-intent (DI-3.6.3): para cada
                    # token forte, uma query de suggest garante que o
                    # domínio citado tenha candidatos em `qualified`
                    # — citar um objetivo nunca pode deixá-lo
                    # silenciosamente sem cobertura.
                    present_ids = {
                        str(c.get("operationId") or "")
                        for c in qualified
                    }
                    # budget cap preservado, mas tokens de métrica
                    # com evidência direta no catálogo têm prioridade
                    # — antes, a ordem de set podia deixar "oee" fora
                    # do goal_map quando o briefing trazia ruído
                    # de instrução (#129 C04).
                    for tok in (
                        sorted(_metric_tok)
                        + [
                            t
                            for t in sorted(_mtok)
                            if t not in _metric_tok
                        ]
                    )[:6]:
                        tok_sugg = []
                        for variant in (tok, tok.rstrip("s")):
                            if variant == tok and tok_sugg:
                                continue
                            try:
                                rr = self._suggest.suggest(
                                    query=variant, limit=6
                                )
                                tok_sugg = (
                                    rr.get("suggestions") or []
                                    if isinstance(rr, dict) else []
                                )
                            except Exception:
                                tok_sugg = []
                            if tok_sugg:
                                break
                        if not tok_sugg:
                            # token único não ranqueia — union dos
                            # pairings com TODOS os tokens fortes
                            # (inclusive contexto) — "produtividade"
                            # só resolve com "fábrica"/"indicador".
                            merged: dict[str, dict] = {}
                            for other in sorted(_all_tok - {tok}):
                                try:
                                    rr = self._suggest.suggest(
                                        query=f"{tok} {other}",
                                        limit=6,
                                    )
                                    for cand in (
                                        rr.get("suggestions") or []
                                        if isinstance(rr, dict)
                                        else []
                                    ):
                                        oid = str(
                                            cand.get("operationId")
                                            or ""
                                        )
                                        if oid and oid not in merged:
                                            merged[oid] = cand
                                except Exception:
                                    continue
                            tok_sugg = list(merged.values())
                            if not tok_sugg:
                                try:
                                    rr = self._suggest.suggest(
                                        query=f"{tok} indicador",
                                        limit=6,
                                    )
                                    tok_sugg = (
                                        rr.get("suggestions") or []
                                        if isinstance(rr, dict)
                                        else []
                                    )
                                except Exception:
                                    tok_sugg = []
                        goal_map[tok] = {
                            "operationIds": {
                                str(c.get("operationId") or "")
                                for c in tok_sugg[:8]
                                if isinstance(c, dict)
                            } - {""},
                            "categories": {
                                str(c.get("category") or "").strip()
                                for c in tok_sugg[:8]
                                if isinstance(c, dict)
                                and str(c.get("category") or "").strip()
                            },
                        }
                        for cand in tok_sugg:
                            oid = str(cand.get("operationId") or "")
                            if (
                                _eligible(cand)
                                and oid
                                and oid not in present_ids
                                and len(qualified) < 40
                            ):
                                present_ids.add(oid)
                                qualified.append(dict(cand))
                    anchor_categories |= {
                        str(c.get("category") or "").strip()
                        for c in qualified
                        if str(c.get("category") or "").strip()
                        and any(
                            tok in (
                                str(c.get("operationId") or "")
                                + str(c.get("label") or "")
                                + str(c.get("description") or "")
                            ).lower()
                            for tok in _mtok
                        )
                    }
                # RC-D (DI-3.7.1): cobertura falsa — um objetivo só
                # pode ser atendido por fonte que passa a âncora de
                # domínio ("metas" comerciais não valem Kaizen/system).
                _oid_cat: dict[str, str] = {}
                try:
                    _all_routes = self._catalog.list_routes()
                except Exception:
                    _all_routes = []
                for r in list(qualified) + list(_all_routes):
                    if isinstance(r, dict):
                        _oid_cat.setdefault(
                            str(r.get("operationId") or ""),
                            str(r.get("category") or "").strip(),
                        )
                _oid_score = {
                    str(c.get("operationId") or ""): float(
                        c.get("score") or 0.0
                    )
                    for c in qualified
                    if isinstance(c, dict)
                }

                def _goal_ok(oid, goal_cats):
                    cat = _oid_cat.get(oid, "")
                    # categorias do PRÓPRIO objetivo são evidência —
                    # production serve produtividade, commercial serve
                    # metas, mesmo cortadas da âncora global.
                    if cat and cat in goal_cats:
                        return True
                    if not anchor_categories:
                        return True
                    if cat in anchor_categories:
                        return True
                    return (
                        _anchor_top > 0
                        and _oid_score.get(oid, 0.0)
                        >= _anchor_top * 0.5
                    )

                for _g in goal_map.values():
                    _g["operationIds"] = {
                        oid
                        for oid in _g["operationIds"]
                        if _goal_ok(oid, _g["categories"])
                    }

                # donos de categoria: uma categoria só pode
                # justificar associação quando pertence a UM único
                # objetivo — `production`→produtividade associa
                # séries não presentes nos opIds; `quality` é
                # compartilhada (auditorias/kaizen) e segue estrita.
                _cat_owners: dict[str, set] = {}
                for _tok, _g in goal_map.items():
                    for _c in _g["categories"]:
                        _cat_owners.setdefault(_c, set()).add(_tok)

                def _goals_of(cand):
                    # oid nos opIds do objetivo OU token no oid OU
                    # categoria de dono único COM afinidade etimológica
                    # ("produtividade"~"production"); sem afinidade,
                    # associação fica restrita a opIds (quality não
                    # justifica kaizen para auditorias).
                    oid = str(cand.get("operationId") or "")
                    cat = str(cand.get("category") or "").strip()
                    return [
                        tok for tok, g in goal_map.items()
                        if oid in g["operationIds"]
                        or tok in oid
                        or (
                            cat
                            and _cat_owners.get(cat) == {tok}
                            and (
                                tok[:4] == cat[:4]
                                or cat[:4] == tok[:4]
                            )
                        )
                    ]

                # goal-to-source association (DI-3.7): cada objetivo
                # forte carrega suas fontes justificadas; candidato
                # sem objetivo é descartável quando houver justificados.
                for cand in qualified:
                    if isinstance(cand, dict):
                        cand["goals"] = _goals_of(cand)

                # Domínio secundário só entra por relevância individual
                # forte na query bruta (>=50% do topo) — categoria
                # fraca não arrasta vizinhos (5S/Kaizen fora de
                # produção; T02/T03 DI-3.6.2).
                bare_scores = {
                    str(c.get("operationId") or ""): float(
                        c.get("score") or 0.0
                    )
                    for c in qualified
                }

                def _anchor_ok(cand):
                    cat = str(cand.get("category") or "").strip()
                    if not anchor_categories:
                        return True
                    if cat in anchor_categories:
                        return True
                    # score da QUERY BRUTA, não o da query de propósito
                    # — sufixos nunca promovem cross-domain.
                    return (
                        _anchor_top > 0
                        and bare_scores.get(
                            str(cand.get("operationId") or ""), 0.0
                        )
                        >= _anchor_top * 0.5
                    )

                def _slim(cand):
                    return {
                        key: cand.get(key)
                        for key in (
                            "operationId", "path", "category",
                            "description", "allowedDisplayModes",
                            "metaShape", "paramSchema", "goals",
                        )
                        if cand.get(key) is not None
                    }

                def _modes_for(block_type, chart_type):
                    """Modos ESPECÍFICOS exigidos — `auto` nunca conta
                    como evidência de compatibilidade (DI-3.5)."""
                    if block_type in {"kpi_view", "data_kpi"}:
                        return {"kpi"}
                    if block_type in {"chart_view", "data_chart"}:
                        ct = str(chart_type or "").lower()
                        if ct in {"line", "area"}:
                            return {"line_chart"}
                        if ct in {"bar", "horizontal_bar", "column"}:
                            return {"bar_chart"}
                        return {"line_chart", "bar_chart"}
                    if block_type in {
                        "table_view", "data_table", "canvas_table",
                    }:
                        return {"table"}
                    return set()

                # metaShape ↔ componente: evidência estrutural mínima
                # quando a rota declara apenas `auto` (o catálogo
                # auto-seleciona o modo pelo shape do retorno).
                _SHAPES_FOR_MODES = {
                    "kpi": {"scalar", "object", "composite_analysis",
                            "product_snapshot", "nested_object"},
                    "table": {"list", "paged_list", "hierarchy",
                              "playbook_report", "composite_analysis"},
                }

                def _compatible(cand, modes):
                    declared = {
                        str(m) for m in
                        (cand.get("allowedDisplayModes") or [])
                    }
                    if modes & (declared - {"auto"}):
                        return True
                    shape = str(cand.get("metaShape") or "")
                    return bool(
                        "auto" in declared
                        and any(
                            shape in _SHAPES_FOR_MODES.get(m, set())
                            for m in modes
                        )
                    )

                def _state(cands):
                    if len(cands) == 1:
                        return "RESOLVED"
                    if len(cands) > 1:
                        return "NEEDS_SOURCE_SELECTION"
                    return "NEEDS_CONTEXT"

                blocks = []
                for op in data_ops:
                    block = (
                        op.get("block")
                        if isinstance(op.get("block"), dict) else {}
                    )
                    btype = str(block.get("type") or "")
                    modes = _modes_for(btype, block.get("chartType"))
                    purpose_candidates = _suggest_for(
                        _purpose_query(btype, block.get("chartType"))
                    )
                    purpose_qualified = [
                        cand for cand in purpose_candidates
                        if _eligible(cand)
                    ]
                    # union deduplicada: query de propósito + query
                    # bruta + cobertura multi-intent — objetivo citado
                    # não pode ser descartado por ordem de consulta.
                    _seen = set()
                    _combined = []
                    for cand in purpose_qualified + qualified:
                        oid = str(cand.get("operationId") or "")
                        if oid and oid not in _seen:
                            _seen.add(oid)
                            if isinstance(cand, dict):
                                cand["goals"] = _goals_of(cand)
                            _combined.append(cand)
                    per = [
                        cand for cand in _combined
                        if _compatible(cand, modes)
                    ]
                    # limiar semântico: score relativo ao topo do bloco
                    # remove candidatos fracamente relacionados (ruído
                    # lexical — ex.: get_customer_avatar em vendas).
                    if len(per) > 1:
                        scores = [
                            float(c.get("score") or 0.0)
                            for c in per
                        ]
                        top = max(scores) if scores else 0.0
                        floor = top * 0.5 if top > 0 else 0.0
                        # goal-justified sources são evidência —
                        # o floor não pode cortá-las por escala
                        # de score entre queries distintas.
                        per = [
                            c for c in per
                            if c.get("goals")
                            or float(c.get("score") or 0.0) >= floor
                        ]
                    # domain anchor: sufixo de propósito não promove
                    # fontes fora do domínio de negócio âncora; secundárias
                    # só por relevância individual forte na query bruta.
                    per = [c for c in per if _anchor_ok(c)]
                    # multi-intent: ordenar por score evita que
                    # adições de cobertura percam o cap por posição.
                    per.sort(
                        key=lambda c: float(c.get("score") or 0.0),
                        reverse=True,
                    )
                    # goal-to-source (DI-3.7): quando há objetivos
                    # reconhecidos, candidato sem justificativa de
                    # objetivo não pode permanecer (Kaizen fora de
                    # produtividade+5S, transformômetro fora de 5S).
                    if goal_map:
                        justified = [
                            c for c in per if _goals_of(c)
                        ]
                        if justified:
                            per = justified
                    # goal floor (DI-3.7.1): cada objetivo reconhecido
                    # mantém >=1 representante no bloco — cap por score
                    # não pode apagar a cobertura de um objetivo.
                    per.sort(
                        key=lambda c: float(c.get("score") or 0.0),
                        reverse=True,
                    )
                    if len(per) > 8:
                        seen_goals = set()
                        kept = []
                        for c in per:
                            g = set(_goals_of(c))
                            if len(kept) < 6 or (g - seen_goals):
                                seen_goals |= g
                                kept.append(c)
                        per = kept
                    per = per[:8]
                    if not per and qualified:
                        # Fallback por domínio: ranking lexical fraco
                        # não prova inexistência — busca no catálogo
                        # canônico rotas do mesmo domínio das top
                        # candidates que declarem o modo exigido.
                        top_category = str(
                            (qualified[0].get("category") or "")
                        ).strip()
                        if top_category:
                            try:
                                catalog_routes = (
                                    self._catalog.list_routes()
                                )
                            except Exception:
                                catalog_routes = []
                            per = [
                                cand for cand in catalog_routes
                                if _eligible(cand)
                                and str(cand.get("category") or "")
                                == top_category
                                and _compatible(cand, modes)
                            ][:8]
                    block_state = _state(per)
                    entry = {
                        "blockType": btype or "data_block",
                        "requiredModes": sorted(modes),
                        "state": block_state,
                        "servesGoals": sorted({
                            g for c in per for g in c.get("goals") or []
                        }),
                        "candidates": [_slim(c) for c in per],
                    }
                    if block_state == "RESOLVED" and per:
                        # binding canônico: operationId + displayMode +
                        # params (required não-optional => missingParams
                        # explicitados, nunca inventados).
                        cand = per[0]
                        schema = cand.get("paramSchema")
                        missing = [
                            str(k)
                            for k, spec in (
                                schema.items() if isinstance(schema, dict)
                                else []
                            )
                            if isinstance(spec, dict)
                            and spec.get("optional") is False
                            and spec.get("default") is None
                        ]
                        modes_list = cand.get("allowedDisplayModes") or []
                        entry["binding"] = {
                            "operationId": cand.get("operationId"),
                            "displayMode": (
                                str(modes_list[0])
                                if modes_list else "auto"
                            ),
                            "missingParams": missing,
                        }
                    blocks.append(entry)
                payload["bindingPlan"] = {
                    "state": (
                        "RESOLVED"
                        if all(b["state"] == "RESOLVED" for b in blocks)
                        else "NEEDS_SOURCE_SELECTION"
                        if any(
                            b["state"] == "NEEDS_SOURCE_SELECTION"
                            for b in blocks
                        )
                        else "NEEDS_CONTEXT"
                    ),
                    "dataBlockOps": len(data_ops),
                    "blocks": blocks,
                    "disqualifiedSources": max(
                        0, len(candidates) - len(qualified)
                    ),
                    "note": (
                        "Fontes qualificadas por allowedDisplayModes/"
                        "metaShape; ambiguidade preservada — nunca "
                        "pick silencioso."
                    ),
                }
                # goal traceability (DI-3.7): objetivos reconhecidos
                # + ignorados no payload — nenhum descartado
                # silenciosamente.
                covered = {
                    g for b in blocks for g in b.get("servesGoals") or []
                }
                payload["interpretedGoals"] = [
                    {
                        "goal": tok,
                        "categories": sorted(g["categories"]),
                        "status": (
                            "COVERED" if tok in covered
                            else "NO_SOURCE_CANDIDATE"
                        ),
                    }
                    for tok, g in goal_map.items()
                    if g["operationIds"]
                ]
                payload["ignoredGoals"] = [
                    tok for tok, g in goal_map.items()
                    if not g["operationIds"]
                ]
                # DI-E2E-DESIGN-01 — bridge composição→binding: ops de
                # recipe ganham data_source + bind_visual canônicos,
                # heading recebe o título do briefing e componentes
                # não pedidos saem do plano.
                existing_blocks: list[dict[str, Any]] = []
                _sid = str(
                    (payload.get("host_context") or {}).get("slideId")
                    or (host or {}).get("slideId")
                    or ""
                ).strip()
                _pid = str(
                    (payload.get("host_context") or {}).get("playlistId")
                    or (host or {}).get("playlistId")
                    or ""
                ).strip()
                # estado de leitura explícito (issue #129 F1):
                # ausência tipada/id malformado ≠ falha de leitura ≠
                # slide vazio — erro inesperado nunca vira
                # existing_blocks=[].
                _sl: dict[str, Any] | None = None
                _slide_missing = False
                if _sid and _pid:
                    try:
                        _slide_uuid = UUID(_sid)
                        _playlist_uuid = UUID(_pid)
                    except ValueError:
                        # referência malformada no host_context —
                        # mesmo contrato de ausência, não é defeito.
                        _slide_missing = True
                    else:
                        try:
                            _sl = self._writes.get_slide(
                                _slide_uuid, playlist_id=_playlist_uuid
                            )
                        except PresentationWriteError as exc:
                            if str(exc.code or "") == "RESOURCE_NOT_FOUND":
                                _slide_missing = True
                            else:
                                raise
                        except GptActionsError:
                            raise
                        except Exception:
                            logger.exception(
                                "suggest_change: slide read failed "
                                "(playlist_id=%s, slide_id=%s)",
                                _pid, _sid,
                            )
                            raise
                    if _sl:
                        _raw_blocks = (
                            self._writes.slide_blocks(_sl)
                            if hasattr(self._writes, "slide_blocks")
                            else (
                                (_sl.get("nativeConfig") or {})
                                .get("blocks")
                                or []
                            )
                        )
                        for _b in _raw_blocks or []:
                            if isinstance(_b, dict) and _b.get("id"):
                                existing_blocks.append(
                                    {
                                        "id": str(_b["id"]),
                                        "type": str(
                                            _b.get("type") or ""
                                        ),
                                        "frame": _b.get("frame") or {},
                                    }
                                )
                self._enrich_composition_ops(
                    payload, blocks, message,
                    request_goals=set(goal_map),
                    existing_blocks=existing_blocks,
                )
                # consumo da capability de visão (issue #129 doc51):
                # evidência canônica — previewUrl assinada, rendered
                # (policy editor_live) e auditoria estrutural — com
                # basisRevision (estado persistido, não a proposta).
                try:
                    from tv_app.application.services.data.slide_preview_render_service import (
                        get_slide_preview_render_service,
                    )
                    _svc = get_slide_preview_render_service()
                    if _sid and _pid and _sl:
                        _rev = str(
                            self._writes.get_revision(UUID(_pid)) or ""
                        )
                        _native = _sl.get("nativeConfig") or {}
                        _sp = _svc.build_preview_payload(
                            playlist_id=_pid, slide_id=_sid,
                            revision=_rev, native_config=_native,
                            title=str(_sl.get("title") or "") or None,
                        )
                        _rnd = _svc.build_rendered_payload(
                            playlist_id=_pid, slide_id=_sid,
                            revision=_rev, renderable=True,
                        )
                        _rnd = self._apply_live_editor_visual_policy(
                            playlist_id=UUID(_pid), slide=_sl,
                            revision=_rev,
                            actor=self._access.actor_id(user) or "",
                            rendered=_rnd, preview_svc=_svc,
                        )
                        payload["visualEvidence"] = {
                            "status": "available",
                            "basisRevision": _rev,
                            "previewUrl": _sp.get("previewUrl"),
                            "rendered": _rnd,
                            "designAudit": (
                                DesignIntelligenceService.design_audit(_native)
                                if isinstance(_native, dict) else {}
                            ),
                        }
                    elif _sid and _pid and (_slide_missing or not _sl):
                        # ausência comprovada — só chega aqui quando a
                        # leitura não falhou (falha sobe exceção acima).
                        payload["visualEvidence"] = {
                            "status": "unavailable",
                            "failureCode": "SLIDE_NOT_FOUND",
                        }
                except GptActionsError:
                    raise
                except Exception:
                    # defeito de construção da evidência não é
                    # indisponibilidade operacional — sobe diagnosticável
                    # com log sanitizado, nunca vira PREVIEW_UNAVAILABLE
                    # fabricado (issue #129 F1).
                    logger.exception(
                        "suggest_change: visual evidence build failed "
                        "(playlist_id=%s, slide_id=%s)",
                        _pid, _sid,
                    )
                    raise
                # readiness honesto: layout pronto ≠ dados prontos.
                if payload["bindingPlan"]["state"] != "RESOLVED":
                    payload["dataReadiness"] = "pending_source_selection"
                    reason = str(payload.get("reason") or "")
                    if "execução direta" in reason:
                        payload["reason"] = (
                            "Layout pronto; seleção de fonte de dados "
                            "pendente (ver bindingPlan)."
                        )
        if intent:
            methodology = self._design_methodology_for_suggest(intent=intent, host=host)
            methodology.pop("_fabricated", None)
            payload["designMethodology"] = methodology
            # P7 — bounded quality signal: intent/readiness/sufficiency enums.
            from tv_app.application.services.data.vista_quality_telemetry import (
                record_design_methodology,
            )

            record_design_methodology(
                design_intent=intent,
                readiness=methodology.get("readiness"),
                sufficiency=methodology.get("sufficiency"),
            )
        return payload

    @staticmethod
    def _enrich_composition_ops(
        payload: dict[str, Any],
        blocks: list[dict[str, Any]],
        message: Any,
        request_goals: set[str] | None = None,
        existing_blocks: list[dict[str, Any]] | None = None,
    ) -> None:
        """DI-E2E-DESIGN-01 — ONE REQUEST → COMPLETE DASHBOARD.

        Recipe ops are layout scaffolds (frames/styles only). This
        bridge connects them to the canonical data path that the
        bindingPlan already qualified:

        - heading gains the briefing title (``content``/``contentRuns``);
        - each ``upsert_block`` data block gains an ``id`` and is
          followed by ``upsert_data_source`` + ``bind_visual`` ops
          (canonical flat contract);
        - ``table_view`` scaffold is dropped when the request never
          asked for a table/detail — recipe is a scaffold, not a
          prescription of components;
        - declared period intent (``N dias`` / mensal / semanal /
          anual / diário) fills route params only when the route's
          own ``paramSchema`` declares the key.
        """
        ops = payload.get("ops")
        if not isinstance(ops, list) or not ops:
            return
        import re
        import unicodedata as _u

        msg = str(message or "")
        msg_norm = "".join(
            c
            for c in _u.normalize("NFD", msg.lower())
            if _u.category(c) != "Mn"
        )
        title = ""
        m = re.search(
            r"t[íi]tulo\s*[:=\"']?\s*[\"']?([^\"'\n.,;]{3,80})",
            msg,
            re.I,
        )
        if m:
            title = m.group(1).strip()
        if not title:
            # sem título explícito — deriva do primeiro objetivo de
            # negócio em ORDEM DE APARIÇÃO no briefing (não por
            # ordem arbitrária de set).
            goals = payload.get("interpretedGoals") or []
            ordered = sorted(
                (
                    g
                    for g in goals
                    if str(g.get("goal") or "")
                ),
                key=lambda g: msg_norm.find(
                    str(g["goal"]).lower()
                )
                if msg_norm.find(str(g["goal"]).lower()) >= 0
                else 10**6,
            )
            if ordered:
                _g = str(ordered[0]["goal"])
                # sigla que o usuário escreveu em maiúsculas
                # permanece: OEE, não "Oee".
                _g = (
                    _g.upper()
                    if _g.upper()
                    in {
                        t.strip(".,;:!?()\"'")
                        for t in msg.split()
                    }
                    else _g.capitalize()
                )
                title = "Painel de " + _g

        params_msg: dict[str, Any] = {}
        mp = re.search(r"(\d{1,4})\s*dias", msg_norm, re.I)
        if mp:
            params_msg["periodDays"] = int(mp.group(1))
        for kw, gran in (
            (r"mensal|por\s+mes|mes\s+a\s+mes|monthly", "month"),
            (r"semanal|por\s+semana|weekly", "week"),
            (r"anual|por\s+ano|yearly", "year"),
            (r"diari|por\s+dia|daily", "day"),
        ):
            if re.search(kw, msg_norm, re.I):
                params_msg["granularity"] = gran

        # "não conformidades", problemas, ocorrências e similares
        # são semanticamente pedidos de apresentação em detalhe —
        # não precisam da palavra "tabela" para exigir o bloco.
        want_table = bool(
            re.search(
                r"tabela|detalh|lista|conformidades|conformidade"
                r"|ocorr|problem|item|itens|falha|pendenc|registro",
                msg_norm,
                re.I,
            )
        )
        # pedido de REMOÇÃO não é pedido de presença (issue #129 F2):
        # «remova a tabela antiga» contém "tabela" mas exige a saída
        # do componente — mencionar para remover não pode manter o
        # scaffold nem impedir o delete_block do redesign.
        _table_removed = bool(
            re.search(
                r"(remov|exclu|elimin|apag|delet|tir|retir|descart|sem)\w*"
                r"\s+(?:a|o|as|os|uma|da|do)?\s*tabela",
                msg_norm,
                re.I,
            )
        )
        if _table_removed:
            want_table = False
        plan_by_type = {
            str(b.get("blockType") or ""): b
            for b in blocks
            if isinstance(b, dict)
        }
        def _cand_role(c):
            segs = str(c.get("operationId") or "").split("_")
            if "meta" in segs or "metas" in segs:
                return "target"
            if "series" in segs or "serie" in segs:
                return "series"
            return "realized"

        # pré-computo: fonte TARGET que vai alimentar o componente
        # de meta — seus goals contam como cobertos pela proposta
        # final (a emissão ocorre após o loop).
        _meta_cand = None
        if (request_goals or set()) & {"meta", "metas", "alvo"}:
            for _p in plan_by_type.values():
                _mc = [
                    c
                    for c in (_p.get("candidates") or [])
                    if isinstance(c, dict)
                    and _cand_role(c) == "target"
                    and c.get("goals")
                ]
                if _mc:
                    _meta_cand = _mc[0]
                    break
        _meta_goals = (
            set(_meta_cand.get("goals") or []) if _meta_cand else set()
        )

        # reconciliação com estado persistido (issue #129 F3):
        # blocos existentes do mesmo papel são reutilizados
        # (upsert com id persistido = update, não add); sobras de
        # redesign saem por delete_block (gate de confirmação).
        _existing = list(existing_blocks or [])
        # redesign só por intenção explícita de substituição —
        # «design»/«desenvolva» descrevem qualidade/criação, não
        # autorizam varrer blocos persistidos (issue #129 F2/C02).
        _redesign = bool(
            re.search(
                r"redesenh|reorganiz|refaz|refazer|rework"
                r"|redesign|substitua|substituir",
                msg_norm,
                re.I,
            )
        )

        def _take_existing(btype):
            for i, eb in enumerate(_existing):
                if eb.get("type") == btype:
                    return _existing.pop(i)
            return None

        enriched: list[dict[str, Any]] = []
        dropped_types: set[str] = set()
        _bound_goals: set[str] = set()
        for op in ops:
            if (
                not isinstance(op, dict)
                or str(op.get("op") or "") != "upsert_block"
                or not isinstance(op.get("block"), dict)
            ):
                enriched.append(op)
                continue
            blk = op["block"]
            btype = str(blk.get("type") or "")
            plan = plan_by_type.get(btype)
            plan_cands = (
                plan.get("candidates") or [] if plan else []
            )
            justified = [
                c
                for c in plan_cands
                if isinstance(c, dict) and c.get("goals")
            ]
            # componente não pedido sai quando vazio OU redundante
            # — seus goals já estão cobertos por outros blocos
            # (ex.: tabela OEE com kpi+chart cobrindo tudo).
            if btype == "table_view" and not want_table:
                # briefing descreve componentes visuais? então
                # componente extra sem papel é arbitrário; pedido só
                # por domínio mantém detalhe justificado na tabela.
                _explicit_visuals = bool(
                    re.search(
                        r"kpi|grafic|titulo|tendenc|destaque"
                        r"|indicador|hierarqu|contraste|tipograf"
                        r"|dashboard",
                        msg_norm,
                        re.I,
                    )
                )
                _own_goals = {
                    g
                    for c in justified
                    for g in (c.get("goals") or [])
                }
                # remoção explícita («remova a tabela») descarta o
                # scaffold incondicionalmente — não depende de
                # justificativa/redundância de fontes (issue #129 F2).
                if (
                    _table_removed
                    or not justified
                    or (
                        _explicit_visuals
                        and _own_goals
                        <= (_bound_goals | _meta_goals)
                    )
                ):
                    dropped_types.add(btype)
                    continue
            if btype == "heading" and title:
                blk["content"] = title
                blk["contentRuns"] = [{"text": title}]
            # reconciliação: reutiliza bloco existente do mesmo
            # papel — upsert com id persistido = update, não add.
            # O consumo só acontece depois do drop de scaffold: um
            # bloco persistido "comido" por um op descartado sumia
            # de `_existing` e escapava do delete_block do redesign
            # (issue #129 F2 — tabela antiga sobrevivia ao redesign).
            _eb = _take_existing(btype)
            if _eb:
                blk["id"] = str(_eb["id"])
            if plan is None:
                enriched.append(op)
                continue
            # seleção por PAPEL (F2 issue #129): papel do segmento
            # do operationId — "meta"→TARGET, "series"→SERIES,
            # demais→REALIZED. KPI/tabela preferem REALIZED quando
            # existir; chart prefere SERIES; meta-segment nunca
            # serve KPI de realizado.
            def _cand_role(c):
                segs = str(c.get("operationId") or "").split("_")
                if "meta" in segs or "metas" in segs:
                    return "target"
                if "series" in segs or "serie" in segs:
                    return "series"
                return "realized"

            # papel = ELEGIBILIDADE, não ranking (issue #129):
            # fonte de meta NUNCA alimenta KPI de realizado; série
            # não alimenta scalar; realizado não vira meta.
            _ROLE_ELIGIBLE = {
                "kpi_view": {"realized"},
                "chart_view": {"series", "realized"},
                "table_view": {"realized", "series"},
            }
            _role_pref = {
                "kpi_view": ["realized", "target", "series"],
                "chart_view": ["series", "realized", "target"],
                "table_view": ["realized", "series", "target"],
            }.get(btype, ["realized", "series", "target"])

            pool = [
                c
                for c in justified
                if set(c.get("goals") or [])
                <= (request_goals or set())
            ] or justified
            # forma canônica por papel do bloco.
            _shape_ok = {
                "kpi_view": {"scalar", "object", "composite_analysis"},
                "chart_view": {"list", "series", "paged_list", "scalar"},
                "table_view": {"list", "paged_list", "hierarchy"},
            }.get(btype, set())
            if _shape_ok:
                _shaped = [
                    c
                    for c in pool
                    if str(c.get("metaShape") or "")
                    in _shape_ok
                ]
                if _shaped:
                    pool = _shaped
            # elegibilidade por papel é RESTRIÇÃO, não preferência
            # (issue #129 C04): fonte de meta nunca alimenta KPI de
            # realizado — sem elegível, o bloco fica sem binding
            # honesto em vez de ligar fonte de papel incompatível.
            _eligible_roles = _ROLE_ELIGIBLE.get(btype, set())
            if _eligible_roles:
                pool = [
                    c
                    for c in pool
                    if _cand_role(c) in _eligible_roles
                ]
            # role pref ordena mas não exclui: indicador meta que
            # cobre oee+meta é a comparação oficial pedida, não
            # contaminação — a chave de cobertura decide.
            pool = sorted(
                pool,
                key=lambda c: (
                    -len(
                        set(c.get("goals") or [])
                        & (request_goals or set())
                    ),
                    _role_pref.index(_cand_role(c))
                    if _cand_role(c) in _role_pref
                    else len(_role_pref),
                    -max(
                        (
                            msg_norm.count(g)
                            for g in (c.get("goals") or [])
                        ),
                        default=0,
                    ),
                    len(set(c.get("goals") or [])),
                    -float(c.get("score") or 0.0),
                ),
            )
            role_ok = pool

            def _rank_key(c):
                return (
                    -len(
                        set(c.get("goals") or [])
                        & (request_goals or set())
                    ),
                    _role_pref.index(_cand_role(c))
                    if _cand_role(c) in _role_pref
                    else len(_role_pref),
                    -max(
                        (
                            msg_norm.count(g)
                            for g in (c.get("goals") or [])
                        ),
                        default=0,
                    ),
                    len(set(c.get("goals") or [])),
                )

            _role_unique = len(role_ok) == 1 or (
                role_ok
                and _rank_key(role_ok[0]) < _rank_key(role_ok[1])
            )
            if (
                plan.get("state") != "RESOLVED"
                and len(justified) != 1
                and not _role_unique
            ):
                enriched.append(op)
                continue
            # fallback também respeita a elegibilidade de papel —
            # plan_cands[0] arbitrário podia ligar meta/série ao
            # bloco errado quando o pool esvaziava (#129 C04).
            _fallback = [
                c
                for c in plan_cands
                if not _eligible_roles
                or _cand_role(c) in _eligible_roles
            ]
            cand = role_ok[0] if role_ok else (
                _fallback[0] if _fallback else None
            )
            oid = (
                str(cand.get("operationId") or "").strip()
                if isinstance(cand, dict)
                else ""
            )
            if not oid:
                enriched.append(op)
                continue
            vid = str(blk.get("id") or f"v_{btype}")
            blk["id"] = vid
            dsid = f"ds_{btype}"
            params = dict(cand.get("params") or {})
            schema = cand.get("paramSchema") or {}
            for key, value in params_msg.items():
                if key in schema:
                    params[key] = value
            spec = plan.get("binding") or {}
            enriched.append(op)
            enriched.append(
                {
                    "op": "upsert_data_source",
                    "operationId": oid,
                    "blockId": dsid,
                    "displayMode": str(
                        spec.get("displayMode") or "auto"
                    ),
                    "label": str(cand.get("label") or oid),
                    "params": params,
                }
            )
            enriched.append(
                {
                    "op": "bind_visual",
                    "visualId": vid,
                    "dataSourceId": dsid,
                }
            )
            # o binding agora é concreto nos ops — o plano reflete
            # a resolução efetiva, não apenas a existência de spec.
            plan["state"] = "RESOLVED"
            plan["resolvedOperationId"] = oid
            plan["resolvedParams"] = params
            plan["binding"] = {
                "operationId": oid,
                "displayMode": str(
                    spec.get("displayMode") or "auto"
                ),
                "missingParams": spec.get("missingParams") or [],
            }
            _bound_goals |= set(cand.get("goals") or [])
        # sobras de redesign: existentes não consumidos saem por
        # delete_block — boundary decide a policy (confirm quando
        # destrutivo); sem redesign, conteúdo é preservado.
        if _redesign and _existing:
            for eb in _existing:
                enriched.append(
                    {"op": "delete_block", "blockId": str(eb["id"])}
                )
        payload["ops"] = enriched
        # meta é representação independente: quando o pedido pede
        # comparação e existe fonte TARGET justificada, emite um
        # KPI de meta próprio — nunca dentro do KPI de realizado.
        if (request_goals or set()) & {"meta", "metas", "goal", "alvo"}:
            for _plan in plan_by_type.values():
                _meta_cands = [
                    c
                    for c in (_plan.get("candidates") or [])
                    if isinstance(c, dict)
                    and _cand_role(c) == "target"
                    and c.get("goals")
                ]
                if not _meta_cands:
                    continue
                _mc = _meta_cands[0]
                _moid = str(_mc.get("operationId") or "").strip()
                if not _moid or any(
                    o.get("operationId") == _moid
                    for o in enriched
                    if isinstance(o, dict)
                ):
                    continue
                enriched.extend(
                    [
                        {
                            "op": "upsert_block",
                            "block": {
                                "id": "v_meta_view",
                                "type": "kpi_view",
                                "frame": {
                                    "x": 3, "y": 50,
                                    "w": 22, "h": 22,
                                },
                                # issue #129 — meta/referência = scorecard
                                "kpiOptions": {"variant": "scorecard"},
                                "style": {
                                    "color": "#0f172a",
                                    "backgroundColor": "#ffffff",
                                    "fontFamily": (
                                        "Inter, system-ui, sans-serif"
                                    ),
                                },
                            },
                        },
                        {
                            "op": "upsert_data_source",
                            "operationId": _moid,
                            "blockId": "ds_meta_view",
                            "displayMode": "kpi",
                            "label": str(
                                _mc.get("label") or _moid
                            ),
                            "params": dict(
                                _mc.get("params") or {}
                            ),
                        },
                        {
                            "op": "bind_visual",
                            "visualId": "v_meta_view",
                            "dataSourceId": "ds_meta_view",
                        },
                    ]
                )
                break
        # blocos do plano cujo componente foi descartado não podem
        # travar a prontidão da proposta.
        if dropped_types and isinstance(
            payload.get("bindingPlan"), dict
        ):
            payload["bindingPlan"]["blocks"] = [
                b
                for b in payload["bindingPlan"].get("blocks") or []
                if str(b.get("blockType") or "") not in dropped_types
            ]
            for dt in dropped_types:
                plan_by_type.pop(dt, None)
        # recomputa o estado agregado após a resolução dos ops.
        plan_list = [
            b for b in plan_by_type.values() if isinstance(b, dict)
        ]
        if plan_list and isinstance(
            payload.get("bindingPlan"), dict
        ):
            payload["bindingPlan"]["state"] = (
                "RESOLVED"
                if all(
                    b.get("state") == "RESOLVED" for b in plan_list
                )
                else "NEEDS_SOURCE_SELECTION"
                if any(
                    b.get("state") == "NEEDS_SOURCE_SELECTION"
                    for b in plan_list
                )
                else "NEEDS_CONTEXT"
            )

    def _design_methodology_for_suggest(
        self,
        *,
        intent: str,
        host: dict[str, Any],
    ) -> dict[str, Any]:
        """Assemble already-known facts from host_context (post P4 merge) and
        evaluate. Advisory only — no hidden I/O: facts the caller did not
        supply surface as missingFacts + nextAction READ instead of guesses."""
        ids = [
            str(item) for item in (host.get("selectedBlockIds") or [])
            if str(item or "").strip()
        ]
        types = host.get("selectedBlockTypes") or []
        selected = [
            {"id": bid, "type": str(types[i]) if i < len(types) else None}
            for i, bid in enumerate(ids)
        ]
        single = str(host.get("selectedBlockId") or host.get("focusBlockId") or "").strip()
        if single and not selected:
            selected = [
                {
                    "id": single,
                    "type": str(host.get("focusBlockType") or "") or None,
                }
            ]
        selection_state = (
            "AMBIGUOUS" if len(selected) > 1 else "ACTIVE" if selected else None
        )
        audit = None
        native = host.get("nativeConfig")
        if isinstance(native, dict):
            audit = DesignIntelligenceService.design_audit(native)
        return DesignIntelligenceService.evaluate_methodology(
            intent=intent,
            design_audit=audit,
            selected_objects=selected,
            selection_state=selection_state,
            has_data_source=bool(host.get("selectedDataSourceId")),
            slide_known=bool(host.get("slideId") or host.get("playlistId")),
        )

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

    def preview_data_model(
        self,
        *,
        user: Any,
        body: dict[str, Any],
        authorization: str | None,
    ) -> dict[str, Any]:
        """Preview de DataModel persistido (modelId) ou candidate inline (model).

        Mesmo resolver canônico do enrichment — sem persistir, sem engine nova.
        """
        from tv_app.application.services.data.data_model_service import (
            DataModelContractError,
            find_data_model,
            normalize_data_model,
        )
        from tv_app.application.services.data.presentation_mutation import (
            PresentationPatchError,
        )

        assert_permission(user, TV_READ)
        playlist_id = str(body.get("playlistId") or "").strip()
        playlist_defaults = body.get("playlistDefaults")
        pid = None
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

        slide_id = str(body.get("slideId") or "").strip()
        slide_native: dict[str, Any] | None = None
        if slide_id:
            if not playlist_id:
                raise GptActionsError(
                    "slideId requer playlistId para resolver o contexto autorizado.",
                    code="INVALID_CHANGE",
                    status_code=422,
                )
            try:
                slide_row = self._writes.get_slide(UUID(slide_id), playlist_id=pid)
            except Exception as exc:
                raise GptActionsError(
                    "Tela não encontrada.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                ) from exc
            raw_native = slide_row.get("nativeConfig")
            slide_native = raw_native if isinstance(raw_native, dict) else {"version": 1}

        native_in = (
            body.get("nativeConfig") if isinstance(body.get("nativeConfig"), dict) else None
        )
        base = (
            native_in
            if isinstance(native_in, dict)
            else slide_native
            if isinstance(slide_native, dict)
            else {"version": 1, "blocks": []}
        )
        cfg = copy.deepcopy(base)
        cfg.setdefault("version", 1)

        model_in = body.get("model") if isinstance(body.get("model"), dict) else None
        model_id = str(body.get("modelId") or "").strip()
        if model_in is not None:
            try:
                model = normalize_data_model(
                    model_in,
                    catalog=self._catalog,
                    sanitize_transform=self._patch.sanitize_vista_data_transform,
                    generate_id=True,
                )
            except DataModelContractError as exc:
                raise GptActionsError(
                    str(exc),
                    code=exc.code or "INVALID_CHANGE",
                    status_code=422,
                    details=dict(exc.details),
                ) from exc
            except PresentationPatchError as exc:
                raise GptActionsError(
                    str(exc),
                    code=exc.code or "INVALID_CHANGE",
                    status_code=422,
                    details=exc.details,
                ) from exc
            models = cfg.get("dataModels")
            if not isinstance(models, list):
                models = []
                cfg["dataModels"] = models
            for index, existing in enumerate(models):
                if isinstance(existing, dict) and str(existing.get("id") or "") == model["id"]:
                    models[index] = model
                    break
            else:
                models.append(model)
            model_id = str(model["id"])
        elif model_id:
            model = find_data_model(cfg, model_id)
            if model is None:
                raise GptActionsError(
                    "Modelo não encontrado no contexto do slide.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                )
        else:
            raise GptActionsError(
                "Informe model (candidate) ou modelId (+playlistId/slideId/nativeConfig).",
                code="INVALID_CHANGE",
                status_code=422,
            )

        try:
            resolved = self._preview.preview_data_model(
                model,
                native_config=cfg,
                authorization=authorization,
                user=user,
                playlist_defaults=(
                    playlist_defaults if isinstance(playlist_defaults, dict) else None
                ),
                force_refresh=bool(body.get("forceRefresh")),
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

        transform_error = (
            resolved.get("transformError")
            if isinstance(resolved.get("transformError"), dict)
            else None
        )
        output_schema = {
            "fields": resolved.get("fields") or resolved.get("projectableFields") or [],
            "valueFields": resolved.get("valueFields") or [],
        }
        return {
            "modelId": model_id,
            "resolved": resolved,
            "outputSchema": output_schema,
            "runtimeErrors": resolved.get("runtimeErrors"),
            "transformError": transform_error,
            "dependencyStatus": (
                "failed" if (transform_error or resolved.get("error")) else "ok"
            ),
        }

    def inspect_data_model(
        self,
        *,
        user: Any,
        playlist_id: str,
        slide_id: str,
        model_id: str,
        authorization: str | None,
        include_runtime: bool = True,
    ) -> dict[str, Any]:
        """Inspect persistido de DataModel — definition, inputs, transform,
        output schema, consumers e runtime status. Somente leitura."""
        from tv_app.application.services.data.data_model_service import (
            DataModelContractError,
            canonical_data_model_definition,
            find_data_model,
        )
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            _model_output_columns,
        )
        from tv_app.application.services.data.projection_fields_contract import (
            collect_source_consumer_field_refs,
        )
        from tv_app.application.gpt_actions.response_compact import (
            GPT_ACTIONS_RESPONSE_MAX_BYTES,
            ascii_utf8_size,
            exceeds_actions_budget,
        )

        assert_permission(user, TV_READ)
        pid_raw = str(playlist_id or "").strip()
        sid_raw = str(slide_id or "").strip()
        mid = str(model_id or "").strip()
        if not pid_raw or not sid_raw or not mid:
            raise GptActionsError(
                "playlistId, slideId e modelId são obrigatórios.",
                code="INVALID_CHANGE",
                status_code=422,
            )
        try:
            pid = UUID(pid_raw)
            sid = UUID(sid_raw)
        except ValueError as exc:
            raise GptActionsError(
                "playlistId/slideId inválidos.",
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
        try:
            slide_row = self._writes.get_slide(sid, playlist_id=pid)
        except Exception as exc:
            raise GptActionsError(
                "Tela não encontrada.",
                code="RESOURCE_NOT_FOUND",
                status_code=404,
            ) from exc
        cfg = (
            slide_row.get("nativeConfig")
            if isinstance(slide_row.get("nativeConfig"), dict)
            else {}
        )
        model = find_data_model(cfg, mid)
        if model is None:
            raise GptActionsError(
                f'DataModel "{mid}" não encontrado no slide.',
                code="RESOURCE_NOT_FOUND",
                status_code=404,
                details={"modelId": mid},
            )

        # Definição persistida — projeção canônica de normalize_data_model:
        # exatamente o objeto que o contrato DM0 persiste/round-trips
        # (upsert/patch). Metadados derivados (hasTransform, chaves fora do
        # contrato) ficam em `derived`, fora do digest.
        try:
            definition, derived = canonical_data_model_definition(model)
            definition_completeness = "full"
        except DataModelContractError as exc:
            # Modelo persistido fora do contrato: inspect continua lendo o
            # estado cru para diagnóstico, sem mascarar a falha.
            definition = dict(model)
            derived = {
                "inputHasTransform": {
                    str(item.get("id") or ""): isinstance(item.get("transform"), dict)
                    for item in model.get("inputs") or []
                    if isinstance(item, dict)
                },
                "modelHasTransform": isinstance(model.get("transform"), dict),
                "contractError": {"code": exc.code, "message": str(exc)},
            }
            definition_completeness = "raw_unvalidated"
        definition_digest = hashlib.sha256(
            json.dumps(
                definition, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()

        blocks = cfg.get("blocks")
        consumers = collect_source_consumer_field_refs(
            blocks if isinstance(blocks, list) else [], mid
        )

        runtime: dict[str, Any] = {"state": "not_executed"}
        output_schema: dict[str, Any] | None = None
        if include_runtime:
            defaults = (access.playlist or {}).get("dataDefaults")
            try:
                resolved = self._preview.preview_data_model(
                    model,
                    native_config=cfg,
                    authorization=authorization,
                    user=user,
                    playlist_defaults=(
                        defaults if isinstance(defaults, dict) else None
                    ),
                )
            except Exception as exc:  # noqa: BLE001 — runtime é best-effort
                resolved = {"error": str(exc)}
            transform_error = (
                resolved.get("transformError")
                if isinstance(resolved.get("transformError"), dict)
                else None
            )
            error_msg = str(resolved.get("error") or "").strip()
            columns = _model_output_columns(resolved)
            if transform_error or error_msg:
                runtime = {
                    "state": "error",
                    "error": transform_error or {"message": error_msg},
                }
            else:
                runtime = {
                    "state": "ready" if columns else "empty",
                }
            if columns is not None:
                output_schema = {"columns": sorted(columns)}

        out = {
            "modelId": mid,
            "definition": definition,
            "definitionCompleteness": definition_completeness,
            "definitionDigest": definition_digest,
            "derived": derived,
            "consumers": consumers,
            "consumerCount": len(consumers),
            "outputSchema": output_schema,
            "runtime": runtime,
        }
        # Budget: definition nunca é truncada — metadados de runtime são
        # compactados primeiro; se a definição canônica não couber, erro tipado.
        if exceeds_actions_budget(out):
            out["outputSchema"] = None
            out["runtime"] = {
                "state": "omitted",
                "reason": "response_budget",
            }
        if exceeds_actions_budget(out):
            raise GptActionsError(
                "Definição do DataModel excede o response budget.",
                code="RESPONSE_BUDGET_EXCEEDED",
                status_code=422,
                details={
                    "modelId": mid,
                    "sizeBytes": ascii_utf8_size(out),
                    "budgetBytes": GPT_ACTIONS_RESPONSE_MAX_BYTES,
                },
            )
        return out

    @staticmethod
    def _find_data_source_host_slide(
        slides: Any,
        *,
        data_source_id: str,
        preview_slide_id: str | None,
    ) -> dict[str, Any]:
        """Slide que hospeda o data_source pedido — canônico: persisted blocks,
        nunca inferência por label/nome. Quando preview_slide_id é passado, a
        fonte precisa existir nessa tela; caso contrário varre os slides."""

        def _hosts(slide: dict[str, Any]) -> bool:
            cfg = slide.get("nativeConfig")
            blocks = (
                cfg.get("blocks") if isinstance(cfg, dict) else []
            ) or []
            return any(
                isinstance(b, dict)
                and str(b.get("type") or "") == "data_source"
                and str(b.get("id") or "") == data_source_id
                for b in blocks
            )

        wanted = str(preview_slide_id or "").strip()
        if wanted:
            slide = next(
                (
                    s
                    for s in slides
                    if isinstance(s, dict) and str(s.get("id") or "") == wanted
                ),
                None,
            )
            if slide is None:
                raise GptActionsError(
                    "Tela não encontrada.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                )
            if _hosts(slide):
                return slide
        else:
            slide = next(
                (s for s in slides if isinstance(s, dict) and _hosts(s)),
                None,
            )
            if slide is not None:
                return slide
        raise GptActionsError(
            f'Data source "{data_source_id}" não encontrado.',
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"dataSourceId": data_source_id},
        )

    def _inspect_data_source(
        self,
        *,
        slide_row: dict[str, Any],
        data_source_id: str,
        user: Any,
        authorization: str | None,
        playlist_defaults: dict[str, Any] | None,
        include_runtime: bool = False,
    ) -> dict[str, Any]:
        """Inspeção focada de um data_source legado do slide — definição,
        transform, dependências, consumidores e evidência de runtime.
        Somente leitura; chamada pelo modo focado de `get_playlist_context`
        (AuthZ + resolução de playlist/slide já verificados pelo caller)."""
        from tv_app.application.services.data.m_query.m_query_dependency_service import (
            MQueryDependencyService,
        )
        from tv_app.application.services.data.projection_fields_contract import (
            collect_source_consumer_field_refs,
        )

        did = str(data_source_id or "").strip()
        cfg = (
            slide_row.get("nativeConfig")
            if isinstance(slide_row.get("nativeConfig"), dict)
            else {}
        )
        blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
        source_blocks = [
            b
            for b in blocks
            if isinstance(b, dict) and str(b.get("type") or "") == "data_source"
        ]
        target = next(
            (b for b in source_blocks if str(b.get("id") or "") == did),
            None,
        )
        if target is None:
            raise GptActionsError(
                f'Data source "{did}" não encontrado no slide.',
                code="RESOURCE_NOT_FOUND",
                status_code=404,
                details={"dataSourceId": did},
            )

        binding = (
            target.get("dataBinding")
            if isinstance(target.get("dataBinding"), dict)
            else {}
        )
        operation_id = str(binding.get("operationId") or "").strip()
        params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
        transform = target.get("dataTransform")
        has_transform = isinstance(transform, dict) and (
            bool(transform.get("steps")) or bool(transform.get("script"))
        )
        route = self._catalog.get_route(operation_id) if operation_id else None

        source: dict[str, Any] = {
            "id": did,
            "label": binding.get("label") or target.get("label"),
            "queryName": str(
                target.get("queryName") or binding.get("queryName") or did
            ).strip(),
            "operationId": operation_id or None,
            "displayMode": binding.get("displayMode"),
            "params": params,
            "fieldLabels": target.get("fieldLabels") or {},
            "hasTransform": has_transform,
        }
        if isinstance(route, dict):
            source["route"] = {
                "operationId": route.get("operationId"),
                "label": route.get("label"),
            }
        context_refs = _expression_context_refs(params)
        if context_refs:
            source["contextReferences"] = sorted(context_refs)

        # Dependências derivadas do contrato persistido (DAG canônico) — nunca
        # por convenção de nome. Merge v1 endereça sibling por sourceId; M v2
        # endereça por queryName via referenced_queries compiladas.
        graph = MQueryDependencyService().resolve(source_blocks)
        node = next((n for n in graph.nodes if n.source_id == did), None)
        ref_to_source: dict[str, str] = {n.query_name: n.source_id for n in graph.nodes}
        for n in graph.nodes:
            ref_to_source.setdefault(n.source_id, n.source_id)
        name_by_source = {n.source_id: n.query_name for n in graph.nodes}

        block_by_id = {
            str(b.get("id") or ""): b
            for b in source_blocks
            if str(b.get("id") or "")
        }
        dependencies: list[dict[str, Any]] = []
        dep_ids: list[str] = list(node.dependencies) if node else []
        for dep_id in dep_ids:
            fields = _merge_consumed_fields(transform, dep_id, ref_to_source)
            dep_block = block_by_id.get(dep_id) or {}
            dep_binding = (
                dep_block.get("dataBinding")
                if isinstance(dep_block.get("dataBinding"), dict)
                else {}
            )
            dep_params = dep_binding.get("params")
            entry: dict[str, Any] = {
                "kind": "data_source",
                "sourceId": dep_id,
                "queryName": name_by_source.get(dep_id),
                "status": "resolved",
                # Params persistidos do dependente — AST de expressão intacto
                # aqui; runtime.inputResults mostra o resolvido por entrada.
                "params": dep_params if isinstance(dep_params, dict) else {},
            }
            if fields is not None:
                entry["fields"] = fields
            dependencies.append(entry)
        unresolved_refs = [
            ref
            for ref in _legacy_merge_source_refs(transform)
            if ref not in ref_to_source
        ]
        for ref in sorted(set(unresolved_refs)):
            dependencies.append(
                {"kind": "data_source", "ref": ref, "status": "unresolved"}
            )
        if dep_ids:
            dependency_status = (
                "INCONCLUSIVE" if unresolved_refs else "RESOLVED"
            )
        else:
            dependency_status = "INCONCLUSIVE" if unresolved_refs else "NONE"

        transform_diagnostics = [
            item
            for item in graph.diagnostics
            if isinstance(item, dict) and item.get("sourceId") == did
        ]

        consumers = collect_source_consumer_field_refs(blocks, did)

        runtime: dict[str, Any] = {"state": "not_executed"}
        if include_runtime:
            closure_ids = {did, *dep_ids}
            closure = [
                dict(b)
                for b in source_blocks
                if str(b.get("id") or "") in closure_ids
            ]
            try:
                enriched = self._preview.resolve_blocks(
                    closure,
                    native_config=cfg,
                    authorization=authorization,
                    user=user,
                    playlist_defaults=playlist_defaults,
                )
            except Exception as exc:  # noqa: BLE001 — runtime é best-effort
                enriched = []
                runtime = {
                    "state": "error",
                    "error": {"code": "RUNTIME_FAILURE", "message": str(exc)},
                }
            if enriched:
                resolved_by_id = {
                    str(b.get("id") or ""): b.get("resolved")
                    for b in enriched
                    if isinstance(b, dict)
                    and isinstance(b.get("resolved"), dict)
                }
                runtime = self._inspect_source_runtime(
                    did,
                    dep_ids,
                    transform=transform,
                    ref_to_source=ref_to_source,
                    resolved_by_id=resolved_by_id,
                    execution_order=[
                        sid
                        for sid in graph.ordered_source_ids
                        if sid in closure_ids
                    ],
                )

        return {
            "slideId": str(slide_row.get("id") or ""),
            "dataSourceId": did,
            "source": source,
            "transform": {
                "persisted": transform if has_transform else None,
                "version": transform.get("version") if has_transform else None,
                "diagnostics": transform_diagnostics,
            },
            "dependencies": dependencies,
            "dependencyStatus": dependency_status,
            "consumers": consumers,
            "consumerCount": len(consumers),
            "runtime": runtime,
        }

    @staticmethod
    def _inspect_source_runtime(
        data_source_id: str,
        dependency_ids: list[str],
        *,
        transform: Any,
        ref_to_source: dict[str, str],
        resolved_by_id: dict[str, Any],
        execution_order: list[str],
    ) -> dict[str, Any]:
        target_resolved = resolved_by_id.get(data_source_id)
        if not isinstance(target_resolved, dict):
            return {
                "state": "error",
                "error": {
                    "code": "SOURCE_NOT_RESOLVED",
                    "message": "Fonte não produziu resultado de runtime.",
                },
            }

        input_results: list[dict[str, Any]] = []
        for dep_id in dependency_ids:
            dep_resolved = resolved_by_id.get(dep_id)
            entry: dict[str, Any] = {
                "sourceId": dep_id,
                "status": "resolved" if isinstance(dep_resolved, dict) else "unresolved",
            }
            if not isinstance(dep_resolved, dict):
                input_results.append(entry)
                continue
            fields = _merge_consumed_fields(transform, dep_id, ref_to_source)
            entry["effectiveParams"] = dict(dep_resolved.get("effectiveParams") or {})
            entry["requestedParams"] = dict(dep_resolved.get("requestedParams") or {})
            if dep_resolved.get("paramExpressions"):
                entry["paramExpressions"] = dep_resolved["paramExpressions"]
            row_count, sample = _inspect_table_sample(
                _inspect_source_table(dep_resolved), fields
            )
            entry["rowCount"] = row_count
            if sample is not None:
                entry["fields"] = sample
            if dep_resolved.get("transformError"):
                entry["transformError"] = dep_resolved["transformError"]
            if dep_resolved.get("error"):
                entry["error"] = str(dep_resolved["error"])
            input_results.append(entry)

        output_table = _inspect_source_table(target_resolved)
        transformed_result: dict[str, Any] | None = None
        if isinstance(output_table, dict):
            columns = [
                str(c)
                for c in (output_table.get("columns") or [])[: _INSPECT_MAX_COLUMNS]
            ]
            available = len(output_table.get("rows") or [])
            returned = min(available, _INSPECT_MAX_RESULT_ROWS)
            transformed_result = {
                "columns": columns,
                "rows": [
                    {col: row.get(col) for col in columns}
                    for row in (output_table.get("rows") or [])[:returned]
                    if isinstance(row, dict)
                ],
                "rowCount": available,
                "truncated": returned < available
                or len(output_table.get("columns") or []) > len(columns),
            }

        query_meta = (
            target_resolved.get("query")
            if isinstance(target_resolved.get("query"), dict)
            else {}
        )
        step_metrics = query_meta.get("stepMetrics")
        transform_error = target_resolved.get("transformError")
        error_msg = str(target_resolved.get("error") or "").strip()
        if transform_error or error_msg:
            state = "error"
        elif transformed_result is None or not transformed_result["rowCount"]:
            state = "empty"
        else:
            state = "ready"

        runtime: dict[str, Any] = {
            "state": state,
            "effectiveParams": dict(target_resolved.get("effectiveParams") or {}),
            "requestedParams": dict(target_resolved.get("requestedParams") or {}),
            "executionOrder": list(execution_order),
            "inputResults": input_results,
            "transformedResult": transformed_result,
            "transformError": transform_error or None,
            "runtimeErrors": target_resolved.get("runtimeErrors") or None,
        }
        if target_resolved.get("paramExpressions"):
            runtime["paramExpressions"] = target_resolved["paramExpressions"]
        if error_msg:
            runtime["error"] = {"message": error_msg}
        if isinstance(step_metrics, list) and step_metrics:
            runtime["trace"] = {"steps": step_metrics}
        return runtime

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
        transport: str = "gpt_actions",
    ) -> dict[str, Any]:
        user = self._governed_write_user(user, authorization)
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

        # Consent foundation (SEMANTIC_TOOLS_V1): when the sealed plan
        # requires human confirmation, PREPARE mints a consent challenge
        # bound to actor + proposal + plan hash. The artifact returned by
        # the trusted approval channel is then required at COMMIT on the
        # semantic surface — confirmation=true alone never proves consent.
        required_confirmation: list[str] = []
        consent_challenge: dict[str, Any] | None = None
        confirmation_unavailable = False
        if confirmation_policy == "confirm":
            from tv_app.application.gpt_actions.vista_consent_service import (
                challenge_view,
                confirm_op_names,
            )
            required_confirmation = confirm_op_names(proposal)
            if self._consent is None:
                confirmation_unavailable = True
            else:
                try:
                    consent_challenge = challenge_view(
                        self._consent.issue_for_proposal(
                            proposal=proposal,
                            actor_sub=actor,
                            origin=transport,
                            correlation_id=str(result.get("fingerprint") or "")
                            or None,
                        )
                    )
                except Exception:  # noqa: BLE001 — fail closed, keep preview honest
                    logger.exception(
                        "vista consent challenge issue failed (proposal_id=%s)",
                        proposal.proposal_id,
                    )
                    confirmation_unavailable = True
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
        # D-8 (CANON 2026-10-31): delete_data_model demands conclusive
        # consumer discovery — impact preview is attached to PREPARE;
        # inconclusive discovery fails closed (DEPENDENCY_UNRESOLVED).
        dm_ops = [
            o for o in stored_ops
            if isinstance(o, dict)
            and str(o.get("op") or "") == "delete_data_model"
        ]
        if dm_ops:
            from tv_app.application.services.data.projection_fields_contract import (
                collect_source_consumer_field_refs,
            )

            cfg = (
                result.get("nativeConfig")
                if isinstance(result.get("nativeConfig"), dict)
                else None
            )
            if cfg is None:
                raise GptActionsError(
                    "Descoberta de consumidores inconclusiva para "
                    "delete_data_model — exclusão bloqueada.",
                    code="DEPENDENCY_UNRESOLVED",
                    status_code=409,
                )
            cfg_blocks = (
                cfg.get("blocks") if isinstance(cfg.get("blocks"), list)
                else []
            )
            impacts = []
            for dm_op in dm_ops:
                mid = str(dm_op.get("modelId") or "").strip()
                refs = collect_source_consumer_field_refs(cfg_blocks, mid)
                impacts.append({
                    "modelId": mid,
                    "consumerBlocks": len(refs),
                    "consumerFieldRefs": sum(
                        len(v) for v in refs.values()
                    ),
                    "consumers": [
                        {"blockId": bid, "fields": fields}
                        for bid, fields in refs.items()
                    ],
                    "confirmationPolicy": "confirm",
                    "verificationStatus": "CONCLUSIVE",
                })
            preview_payload["dependencyImpact"] = impacts
        if required_confirmation:
            preview_payload["requiredConfirmation"] = required_confirmation
        if consent_challenge is not None:
            preview_payload["consentChallenge"] = consent_challenge
        if confirmation_unavailable:
            preview_payload["confirmationUnavailable"] = True
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
        safe_fixes = (
            result.get("sideEffects", {}).get("safeFixesApplied")
            if isinstance(result.get("sideEffects"), dict)
            else None
        )
        if isinstance(safe_fixes, list) and safe_fixes:
            preview_payload["safeFixesApplied"] = safe_fixes

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
        consent_required: bool = False,
    ) -> dict[str, Any]:
        user = self._governed_write_user(user, authorization)
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
                consent_required=consent_required,
            )
        )
