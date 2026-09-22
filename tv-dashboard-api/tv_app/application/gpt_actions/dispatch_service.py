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
from tv_app.application.services.data.tv_copilot_command_planner_service import (
    TvCopilotCommandPlannerService,
)
from tv_app.application.services.data.tv_copilot_content_service import TvCopilotContentService
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
        doc = TvCopilotContentService.capability_catalog_document()
        doc["capability_surface"] = build_capability_surface()
        return doc

    def list_playlists(
        self,
        *,
        user: Any,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        assert_permission(user, TV_READ)
        actor = self._actor(user)
        items = self._repo.list_playlists(
            limit=limit,
            offset=offset,
            user_id=actor,
            include_all=False,
        )
        for item in items:
            item["publicUrl"] = self._present.build_public_url(item["publicToken"])
            if actor and item.get("ownerUserId") == actor:
                item["accessRole"] = "owner"
            elif actor:
                share = self._repo.get_share_role(UUID(item["id"]), actor)
                item["accessRole"] = share or "viewer"
            else:
                item["accessRole"] = "viewer"
        return {"items": items, "limit": limit, "offset": offset}

    def get_playlist_context(self, *, user: Any, playlist_id: str) -> dict[str, Any]:
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
        return {
            "playlist": playlist,
            "slides": slides,
            "sections": sections,
            "accessRole": access.level,
            "currentRevision": self._writes.get_revision(pid),
            "localDraftCoordination": "unavailable_external",
        }

    def search_data_routes(
        self,
        *,
        user: Any,
        query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        assert_permission(user, TV_READ)
        q = str(query or "").strip()
        if q:
            result = self._suggest.suggest(query=q, limit=limit)
            items = result.get("suggestions") if isinstance(result, dict) else []
            if not isinstance(items, list):
                items = []
            return {
                "items": items,
                "query": q,
                "total": result.get("total") if isinstance(result, dict) else len(items),
                "degraded": bool(result.get("degraded")) if isinstance(result, dict) else False,
            }
        items = self._catalog.list_routes()[: max(1, min(int(limit), 100))]
        return {"items": items, "query": None, "total": len(items), "degraded": False}

    def preview_data_block(
        self,
        *,
        user: Any,
        body: dict[str, Any],
        authorization: str | None,
    ) -> dict[str, Any]:
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
        try:
            cfg = self._validation.sanitize(body.get("nativeConfig") or {})
            block = self._preview.preview_block(
                body.get("block") or {},
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
        return {"block": block, "persisted": False}

    def suggest_change(
        self,
        *,
        user: Any,
        message: str,
        host_context: dict[str, Any] | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        assert_permission(user, TV_WRITE)
        plan = TvCopilotCommandPlannerService.plan(
            message=message,
            host_context=host_context if isinstance(host_context, dict) else {},
            user=user,
            authorization=authorization,
        )
        return TvCopilotCommandPlannerService.to_suggest_payload(plan)

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
                catalog_version or TvCopilotContentService.catalog_version()
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
            raise GptActionsError(str(exc), code=code, status_code=422) from exc

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
        policy = TvCopilotContentService.aggregate_ops_policy(stored_ops)
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

        if not commit_now:
            return preview_payload

        if confirmation_policy == "confirm":
            preview_payload["message"] = (
                "commit_now ignorado: confirmationPolicy=confirm exige "
                "confirmação explícita do usuário e gpt_commit_change com o "
                "proposal_handle exato deste preview."
            )
            preview_payload["commit_now_applied"] = False
            return preview_payload

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
        return {
            **preview_payload,
            **outcome,
            "proposal_handle": proposal_handle,
            "commit_now_applied": True,
            "persisted": bool(outcome.get("persisted", True)),
        }

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
        return self._commit.commit(
            user=user,
            actor_id=actor,
            proposal_handle=proposal_handle,
            confirmation=confirmation,
            idempotency_key=idempotency_key,
            authorization=authorization,
        )
