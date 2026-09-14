"""Semantic commit of TvCopilotPatchV1 ops via shared presentation write boundary.

No HTTP loopback. No second catalog. Executes ops through TvPresentationWriteService.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.plan_digest import (
    compute_plan_digest,
    compute_request_fingerprint,
    digests_match,
)
from tv_app.application.services.data.tv_copilot_content_service import TvCopilotContentService
from tv_app.application.services.data.tv_copilot_patch_service import (
    TvCopilotPatchError,
    TvCopilotPatchService,
)
from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    RevisionConflictError,
    TvPresentationWriteService,
)
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    IdempotencyConflictError,
    IdempotencyRepositoryPort,
    PostgresIdempotencyRepository,
)

_NATIVE_CONFIG_OPS = frozenset(
    {
        "upsert_data_source",
        "set_data_transform",
        "upsert_block",
        "delete_block",
        "bind_visual",
        "patch_native_config",
    }
)


class TvGptCommitService:
    def __init__(
        self,
        *,
        writes: TvPresentationWriteService | None = None,
        patch: TvCopilotPatchService | None = None,
        access: PlaylistAccessService | None = None,
        idempotency: IdempotencyRepositoryPort | None = None,
    ) -> None:
        self._writes = writes or TvPresentationWriteService()
        self._patch = patch or TvCopilotPatchService()
        self._access = access or PlaylistAccessService()
        self._idempotency = idempotency or PostgresIdempotencyRepository()

    def commit(
        self,
        *,
        user: Any,
        actor_id: str,
        target: dict[str, Any] | None,
        ops: list[Any],
        catalog_version: str,
        expected_revision: int | None,
        plan_digest: str,
        idempotency_key: str,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        key = str(idempotency_key or "").strip()
        if not key:
            raise GptActionsError(
                "Idempotency-Key é obrigatório para gpt_commit_change.",
                code="INVALID_CHANGE",
                status_code=422,
            )
        fingerprint_payload = {
            "target": target if isinstance(target, dict) else {},
            "ops": ops if isinstance(ops, list) else [],
            "catalogVersion": str(catalog_version or "").strip(),
            "expectedRevision": expected_revision,
            "planDigest": str(plan_digest or "").strip(),
        }
        request_fingerprint = compute_request_fingerprint(fingerprint_payload)
        try:
            cached = self._idempotency.get(
                key=key,
                actor_user_id=actor_id,
                request_fingerprint=request_fingerprint,
            )
        except IdempotencyConflictError as exc:
            raise GptActionsError(
                str(exc),
                code="IDEMPOTENCY_CONFLICT",
                status_code=409,
            ) from exc
        if cached is not None:
            return cached

        current_catalog = TvCopilotContentService.catalog_version()
        if str(catalog_version or "").strip() != current_catalog:
            raise GptActionsError(
                "Catálogo de capabilities mudou. Refaça catalog → plan → preview.",
                code="CATALOG_VERSION_STALE",
                status_code=409,
                details={
                    "expectedCatalogVersion": str(catalog_version or "").strip(),
                    "currentCatalogVersion": current_catalog,
                },
            )

        playlist_id_raw = str((target or {}).get("playlistId") or "").strip()
        create_only = any(
            isinstance(op, dict) and str(op.get("op") or "").strip() == "create_playlist"
            for op in (ops or [])
        )
        if playlist_id_raw:
            playlist_uuid = UUID(playlist_id_raw)
            access = self._access.resolve(playlist_uuid, user)
            if not access.can_edit:
                raise GptActionsError(
                    "Programação não encontrada.",
                    code="RESOURCE_NOT_FOUND",
                    status_code=404,
                )
            try:
                self._writes.assert_expected_revision(playlist_uuid, expected_revision)
            except RevisionConflictError as exc:
                raise GptActionsError(
                    exc.message,
                    code=exc.code,
                    status_code=exc.status_code,
                    details=exc.details,
                ) from exc
            revision_before = int(expected_revision) if expected_revision is not None else self._writes.get_revision(playlist_uuid)
        elif not create_only:
            raise GptActionsError(
                "playlistId é obrigatório salvo create_playlist.",
                code="INVALID_CHANGE",
                status_code=422,
            )
        else:
            playlist_uuid = None
            revision_before = None

        expected_digest = compute_plan_digest(
            actor_id=actor_id,
            target=target if isinstance(target, dict) else {},
            ops=ops if isinstance(ops, list) else [],
            catalog_version=str(catalog_version or "").strip(),
            base_revision=expected_revision,
        )
        if not digests_match(expected_digest, str(plan_digest or "")):
            raise GptActionsError(
                "planDigest não corresponde ao plano autenticado.",
                code="PLAN_MISMATCH",
                status_code=409,
            )

        envelope = {
            "target": target if isinstance(target, dict) else {},
            "ops": ops if isinstance(ops, list) else [],
            "catalogVersion": str(catalog_version or "").strip(),
        }
        try:
            preview = self._patch.preview(
                envelope,
                user=user,
                authorization=authorization,
                include_fingerprint=False,
            )
        except TvCopilotPatchError as exc:
            raise GptActionsError(
                str(exc),
                code="INVALID_CHANGE",
                status_code=422,
            ) from exc

        confirmation = str(preview.get("confirmationPolicy") or "direct").strip().lower()
        if confirmation == "confirm":
            # Consequential Action already gates UI confirmation in GPT Builder;
            # catalog policy remains authoritative — do not treat prompt text as AuthZ.
            pass

        applied: list[dict[str, Any]] = []
        outcome: dict[str, Any] = {"appliedOps": [], "created": {}}
        current_playlist = playlist_uuid
        current_slide_raw = str((target or {}).get("slideId") or "").strip() or None
        current_slide = UUID(current_slide_raw) if current_slide_raw else None
        pending_native = False
        chain_revision: int | None = expected_revision

        try:
            for raw in ops or []:
                if not isinstance(raw, dict):
                    continue
                op_name = str(raw.get("op") or "").strip()
                if not op_name:
                    continue
                if op_name in _NATIVE_CONFIG_OPS:
                    pending_native = True
                    continue

                if op_name == "create_playlist":
                    name = str(raw.get("name") or "").strip() or TvCopilotContentService.setting_str(
                        "defaultPlaylistName", "Nova programação"
                    )
                    description = raw.get("description")
                    playlist = self._writes.create_playlist(
                        name=name,
                        description=str(description).strip() if description else None,
                        actor_user_id=actor_id,
                    )
                    current_playlist = UUID(str(playlist["id"]))
                    outcome["created"]["playlistId"] = str(current_playlist)
                    applied.append({"op": op_name, "playlistId": str(current_playlist)})
                    chain_revision = self._writes.get_revision(current_playlist)
                    seed_presets = raw.get("seedPresetKeys")
                    if isinstance(seed_presets, list):
                        for key_raw in seed_presets:
                            key_s = str(key_raw or "").strip()
                            if not key_s or current_playlist is None:
                                continue
                            slide = self._writes.add_slide_from_preset(
                                current_playlist,
                                preset_key=key_s,
                                branch=None,
                                actor_user_id=actor_id,
                                user=user,
                                expected_revision=chain_revision,
                            )
                            chain_revision = self._writes.get_revision(current_playlist)
                            current_slide = UUID(str(slide["id"]))
                            applied.append(
                                {
                                    "op": "add_slide_from_preset",
                                    "slideId": str(current_slide),
                                }
                            )
                    continue

                if current_playlist is None:
                    raise GptActionsError(
                        TvCopilotContentService.message("missingPlaylist"),
                        code="INVALID_CHANGE",
                        status_code=422,
                    )

                if op_name == "add_blank_slide":
                    title = str(raw.get("title") or "").strip() or TvCopilotContentService.setting_str(
                        "defaultSlideTitle", "Slide personalizado"
                    )
                    payload: dict[str, Any] = {
                        "slideType": "native",
                        "title": title,
                        "nativeScreenKey": "custom_message",
                        "nativeConfig": {
                            "version": 5,
                            "headline": "",
                            "subtitle": "",
                            "blocks": [],
                        },
                        "durationSec": 30,
                    }
                    section_id = str(raw.get("sectionId") or "").strip()
                    if section_id:
                        payload["sectionId"] = section_id
                    slide = self._writes.add_slide(
                        current_playlist,
                        payload,
                        actor_user_id=actor_id,
                        user=user,
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    current_slide = UUID(str(slide["id"]))
                    outcome["created"]["slideId"] = str(current_slide)
                    applied.append({"op": op_name, "slideId": str(current_slide)})
                    continue

                if op_name == "add_slide_from_preset":
                    slide = self._writes.add_slide_from_preset(
                        current_playlist,
                        preset_key=str(raw.get("presetKey") or "").strip(),
                        branch=str(raw.get("branch") or "").strip() or None,
                        actor_user_id=actor_id,
                        user=user,
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    current_slide = UUID(str(slide["id"]))
                    outcome["created"]["slideId"] = str(current_slide)
                    applied.append({"op": op_name, "slideId": str(current_slide)})
                    continue

                if op_name == "update_slide":
                    if current_slide is None:
                        raise GptActionsError(
                            TvCopilotContentService.message("missingSlide"),
                            code="INVALID_CHANGE",
                            status_code=422,
                        )
                    body: dict[str, Any] = {}
                    if "title" in raw and raw["title"] is not None:
                        body["title"] = str(raw["title"]).strip()
                    if "durationSec" in raw:
                        body["durationSec"] = raw["durationSec"]
                    if "isActive" in raw and raw["isActive"] is not None:
                        body["isActive"] = bool(raw["isActive"])
                    if body:
                        self._writes.update_slide(
                            current_playlist,
                            current_slide,
                            body,
                            actor_user_id=actor_id,
                            user=user,
                            expected_revision=chain_revision,
                        )
                        chain_revision = self._writes.get_revision(current_playlist)
                        applied.append({"op": op_name, "slideId": str(current_slide)})
                    continue

                if op_name == "reorder_slides":
                    items = raw.get("items") if isinstance(raw.get("items"), list) else []
                    self._writes.reorder_slides(
                        current_playlist,
                        items,
                        actor_user_id=actor_id,
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    applied.append({"op": op_name})
                    continue

                if op_name == "delete_slide":
                    if current_slide is None:
                        raise GptActionsError(
                            TvCopilotContentService.message("missingSlide"),
                            code="INVALID_CHANGE",
                            status_code=422,
                        )
                    deleted_id = current_slide
                    self._writes.delete_slide(
                        current_playlist,
                        deleted_id,
                        actor_user_id=actor_id,
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    current_slide = None
                    applied.append({"op": op_name, "slideId": str(deleted_id)})
                    continue

                if op_name == "upsert_section":
                    section_id = str(raw.get("sectionId") or "").strip()
                    name = str(raw.get("name") or "").strip()
                    if section_id:
                        body = {"name": name} if name else {}
                        if "isCollapsed" in raw:
                            body["isCollapsed"] = bool(raw["isCollapsed"])
                        if "isActive" in raw:
                            body["isActive"] = bool(raw["isActive"])
                        section = self._writes.update_section(
                            current_playlist,
                            UUID(section_id),
                            body,
                            actor_user_id=actor_id,
                            expected_revision=chain_revision,
                        )
                    else:
                        body = {
                            "name": name
                            or TvCopilotContentService.setting_str(
                                "defaultSectionName", "Nova seção"
                            )
                        }
                        if "sortOrder" in raw:
                            body["sortOrder"] = raw["sortOrder"]
                        section = self._writes.add_section(
                            current_playlist,
                            body,
                            actor_user_id=actor_id,
                            expected_revision=chain_revision,
                        )
                        outcome["created"]["sectionId"] = str(section.get("id") or "")
                    chain_revision = self._writes.get_revision(current_playlist)
                    applied.append({"op": op_name, "sectionId": str(section.get("id") or "")})
                    continue

                if op_name == "delete_section":
                    section_id = str(raw.get("sectionId") or "").strip()
                    self._writes.delete_section(
                        current_playlist,
                        UUID(section_id),
                        actor_user_id=actor_id,
                        delete_slides=bool(raw.get("deleteSlides")),
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    applied.append({"op": op_name, "sectionId": section_id})
                    continue

                if op_name == "move_slide_to_section":
                    if current_slide is None:
                        raise GptActionsError(
                            TvCopilotContentService.message("missingSlide"),
                            code="INVALID_CHANGE",
                            status_code=422,
                        )
                    section_id = raw.get("sectionId")
                    self._writes.update_slide(
                        current_playlist,
                        current_slide,
                        {
                            "sectionId": (
                                str(section_id).strip() if section_id is not None else None
                            )
                        },
                        actor_user_id=actor_id,
                        user=user,
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    applied.append({"op": op_name, "slideId": str(current_slide)})
                    continue

                if op_name == "reorder_sections":
                    items = raw.get("items") if isinstance(raw.get("items"), list) else []
                    self._writes.reorder_sections(
                        current_playlist,
                        items,
                        actor_user_id=actor_id,
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    applied.append({"op": op_name})
                    continue

                raise GptActionsError(
                    TvCopilotContentService.message("unknownOp", op=op_name or "?"),
                    code="UNSUPPORTED_CAPABILITY",
                    status_code=400,
                )

            if pending_native:
                if current_playlist is None or current_slide is None:
                    raise GptActionsError(
                        TvCopilotContentService.message("missingTarget"),
                        code="INVALID_CHANGE",
                        status_code=422,
                    )
                native_config = preview.get("nativeConfig")
                if not isinstance(native_config, dict):
                    raise GptActionsError(
                        TvCopilotContentService.message("missingTarget"),
                        code="INVALID_CHANGE",
                        status_code=422,
                    )
                self._writes.update_slide(
                    current_playlist,
                    current_slide,
                    {"nativeConfig": native_config},
                    actor_user_id=actor_id,
                    user=user,
                    expected_revision=chain_revision,
                )
                chain_revision = self._writes.get_revision(current_playlist)
                applied.append({"op": "native_config_batch", "slideId": str(current_slide)})

        except PresentationWriteError as exc:
            if applied:
                raise GptActionsError(
                    f"Commit parcial: {exc.message}",
                    code="PARTIAL_COMMIT",
                    status_code=409,
                    details={
                        "appliedOps": applied,
                        "failed": {"code": exc.code, "message": exc.message, **exc.details},
                        "revisionAfter": (
                            self._writes.get_revision(current_playlist)
                            if current_playlist is not None
                            else None
                        ),
                    },
                ) from exc
            raise GptActionsError(
                exc.message,
                code=exc.code,
                status_code=exc.status_code,
                details=exc.details,
            ) from exc
        except GptActionsError:
            if applied:
                # Already raised PARTIAL above for write errors; re-raise others with partial if needed
                raise
            raise

        outcome["appliedOps"] = applied
        revision_after = (
            self._writes.get_revision(current_playlist) if current_playlist is not None else None
        )
        verified, verify_details = self._verify_postcondition(
            current_playlist=current_playlist,
            current_slide=current_slide,
            applied=applied,
            expected_native=preview.get("nativeConfig") if pending_native else None,
        )
        if not verified:
            result = {
                "status": "OUTCOME_NOT_VERIFIED",
                "persisted": True,
                "verified": False,
                "revisionBefore": revision_before,
                "revisionAfter": revision_after,
                "outcome": outcome,
                "verification": verify_details,
            }
            # Still record idempotency so replay returns same non-success outcome.
            self._idempotency.save(
                key=key,
                actor_user_id=actor_id,
                request_fingerprint=request_fingerprint,
                response_snapshot=result,
            )
            raise GptActionsError(
                "Write persistido mas pós-condição não comprovada.",
                code="OUTCOME_NOT_VERIFIED",
                status_code=409,
                details=result,
            )

        result = {
            "status": "VERIFIED",
            "persisted": True,
            "verified": True,
            "revisionBefore": revision_before,
            "revisionAfter": revision_after,
            "outcome": outcome,
        }
        self._idempotency.save(
            key=key,
            actor_user_id=actor_id,
            request_fingerprint=request_fingerprint,
            response_snapshot=result,
        )
        return result

    def _verify_postcondition(
        self,
        *,
        current_playlist: UUID | None,
        current_slide: UUID | None,
        applied: list[dict[str, Any]],
        expected_native: Any,
    ) -> tuple[bool, dict[str, Any]]:
        details: dict[str, Any] = {"checks": []}
        if not applied:
            details["checks"].append({"ok": True, "reason": "empty_ops"})
            return True, details
        if current_playlist is None:
            return False, {"checks": [{"ok": False, "reason": "missing_playlist"}]}

        slides = {str(s.get("id")): s for s in self._writes.list_slides(current_playlist)}
        sections = {str(s.get("id")): s for s in self._writes.list_sections(current_playlist)}
        playlist = self._writes.get_playlist(current_playlist)

        for item in applied:
            op = str(item.get("op") or "")
            if op == "create_playlist":
                ok = bool(playlist and str(playlist.get("id")) == str(item.get("playlistId")))
                details["checks"].append({"op": op, "ok": ok})
                if not ok:
                    return False, details
            elif op in {"add_blank_slide", "add_slide_from_preset"}:
                sid = str(item.get("slideId") or "")
                ok = sid in slides
                details["checks"].append({"op": op, "ok": ok, "slideId": sid})
                if not ok:
                    return False, details
            elif op == "delete_slide":
                sid = str(item.get("slideId") or "")
                ok = sid not in slides
                details["checks"].append({"op": op, "ok": ok, "slideId": sid})
                if not ok:
                    return False, details
            elif op == "upsert_section":
                sid = str(item.get("sectionId") or "")
                ok = bool(sid) and sid in sections
                details["checks"].append({"op": op, "ok": ok, "sectionId": sid})
                if not ok:
                    return False, details
            elif op == "delete_section":
                sid = str(item.get("sectionId") or "")
                ok = sid not in sections
                details["checks"].append({"op": op, "ok": ok, "sectionId": sid})
                if not ok:
                    return False, details
            elif op == "native_config_batch":
                sid = str(item.get("slideId") or (current_slide or ""))
                slide = slides.get(sid)
                if not slide:
                    details["checks"].append({"op": op, "ok": False, "reason": "slide_missing"})
                    return False, details
                persisted_native = slide.get("nativeConfig")
                ok = isinstance(persisted_native, dict) and isinstance(expected_native, dict)
                if ok:
                    # Spot-check block ids if present
                    expected_blocks = expected_native.get("blocks")
                    persisted_blocks = persisted_native.get("blocks")
                    if isinstance(expected_blocks, list) and isinstance(persisted_blocks, list):
                        exp_ids = {
                            str(b.get("id"))
                            for b in expected_blocks
                            if isinstance(b, dict) and b.get("id")
                        }
                        got_ids = {
                            str(b.get("id"))
                            for b in persisted_blocks
                            if isinstance(b, dict) and b.get("id")
                        }
                        ok = exp_ids == got_ids
                details["checks"].append({"op": op, "ok": ok, "slideId": sid})
                if not ok:
                    return False, details
            else:
                details["checks"].append({"op": op, "ok": True, "reason": "structure_ok"})
        return True, details
