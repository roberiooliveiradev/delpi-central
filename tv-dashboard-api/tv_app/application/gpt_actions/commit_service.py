"""Semantic commit of PresentationMutation ops via shared presentation write boundary.

No HTTP loopback. No second catalog. Executes ops through TvPresentationWriteService.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.plan_digest import compute_request_fingerprint
from tv_app.application.gpt_actions.proposal import (
    CAPABILITY_PRESENTATION_CHANGE,
    fingerprint,
)
from tv_app.application.gpt_actions.proposal_store import (
    get_proposal_store,
    load_valid_proposal,
)
from tv_app.application.ports import IdempotencyRepositoryPort
from tv_app.application.services.data.presentation_ops_content_service import PresentationOpsContentService
from tv_app.application.services.data.presentation_mutation import (
    ExecutionContext,
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    RevisionConflictError,
    TvPresentationWriteService,
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

_ERROR_OUTCOME_STATUSES = frozenset(
    {"PARTIAL_COMMIT", "OUTCOME_NOT_VERIFIED"}
)


class _DeterministicPreWriteError(Exception):
    """Known rejection after acquire and before any material write."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "INVALID_CHANGE",
        status_code: int = 422,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _strip_transient_native(cfg: dict[str, Any]) -> dict[str, Any]:
    """Drop non-persisted enrichment keys before semantic compare."""
    out = json.loads(_canonical_json(cfg))
    if not isinstance(out, dict):
        return {}
    out.pop("resolved", None)
    blocks = out.get("blocks")
    if isinstance(blocks, list):
        cleaned = []
        for block in blocks:
            if not isinstance(block, dict):
                cleaned.append(block)
                continue
            item = dict(block)
            item.pop("resolved", None)
            cleaned.append(item)
        out["blocks"] = cleaned
    return out


class TvGptCommitService:
    def __init__(
        self,
        *,
        writes: TvPresentationWriteService,
        idempotency: IdempotencyRepositoryPort,
        patch: PresentationPatchService | None = None,
        access: PlaylistAccessService | None = None,
    ) -> None:
        self._writes = writes
        self._idempotency = idempotency
        self._patch = patch or PresentationPatchService()
        self._access = access or PlaylistAccessService()

    @staticmethod
    def _normalize_confirmation(confirmation: dict[str, Any] | bool | None) -> bool:
        if confirmation is True:
            return True
        if isinstance(confirmation, dict):
            return bool(confirmation.get("confirmed") is True or confirmation.get("confirmation") is True)
        return False

    def commit(
        self,
        *,
        user: Any,
        actor_id: str,
        proposal_handle: str,
        confirmation: dict[str, Any] | bool | None,
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
        if not self._normalize_confirmation(confirmation):
            raise GptActionsError(
                "confirmation.confirmed=true é obrigatório para COMMIT. "
                "Confirmação conversacional não substitui AuthZ.",
                code="CONFIRMATION_REQUIRED",
                status_code=400,
            )

        handle = str(proposal_handle or "").strip()
        fingerprint_payload = {
            "proposal_handle": handle,
            "confirmation": True,
        }
        request_fingerprint = compute_request_fingerprint(fingerprint_payload)

        acquired = self._idempotency.acquire(
            key=key,
            actor_user_id=actor_id,
            request_fingerprint=request_fingerprint,
        )
        if acquired.status == "CONFLICT":
            raise GptActionsError(
                "Idempotency-Key reused with a different request.",
                code="IDEMPOTENCY_CONFLICT",
                status_code=409,
            )
        if acquired.status == "IN_PROGRESS":
            raise GptActionsError(
                "Commit já em andamento para esta Idempotency-Key.",
                code="IDEMPOTENCY_IN_PROGRESS",
                status_code=409,
                retryable=True,
            )
        if acquired.status == "REPLAY":
            return self._replay_snapshot(acquired.response_snapshot or {})

        proposal = load_valid_proposal(
            proposal_handle=handle,
            actor_id=actor_id,
            expected_capability=CAPABILITY_PRESENTATION_CHANGE,
        )
        exact = proposal.exact_change if isinstance(proposal.exact_change, dict) else {}
        target = exact.get("target") if isinstance(exact.get("target"), dict) else {}
        ops = exact.get("ops") if isinstance(exact.get("ops"), list) else []
        catalog_version = str(
            exact.get("catalogVersion") or proposal.catalog_version or ""
        ).strip()
        expected_revision = proposal.base_revision
        if expected_revision is None and exact.get("baseRevision") is not None:
            expected_revision = int(exact["baseRevision"])

        # ACQUIRED — reservation held before any write.
        try:
            outcome = self._execute_acquired(
                user=user,
                actor_id=actor_id,
                target=target,
                ops=ops,
                catalog_version=catalog_version,
                expected_revision=expected_revision,
                state_fingerprint=proposal.current_state_fingerprint,
                proposal_id=proposal.proposal_id,
                key=key,
                request_fingerprint=request_fingerprint,
                authorization=authorization,
            )
            get_proposal_store().consume(proposal.proposal_id)
            return outcome
        except _DeterministicPreWriteError as exc:
            err = {
                "status": exc.code,
                "_raise": True,
                "_code": exc.code,
                "_statusCode": exc.status_code,
                "message": exc.message,
                **(exc.details or {}),
            }
            self._complete(
                key=key,
                actor_id=actor_id,
                request_fingerprint=request_fingerprint,
                snapshot=err,
            )
            raise GptActionsError(
                exc.message,
                code=exc.code,
                status_code=exc.status_code,
                details=exc.details,
            ) from exc

    def _parse_uuid_prewrite(self, raw: str, *, field: str) -> UUID:
        try:
            return UUID(str(raw).strip())
        except ValueError as exc:
            raise _DeterministicPreWriteError(f"{field} inválido.") from exc

    def _parse_uuid_op(self, raw: str, *, field: str) -> UUID:
        """UUID from op payload during execution — maps to write-path errors."""
        try:
            return UUID(str(raw).strip())
        except ValueError as exc:
            raise PresentationWriteError(
                f"{field} inválido.",
                status_code=422,
                code="INVALID_CHANGE",
            ) from exc

    def _replay_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        status = str(snapshot.get("status") or "")
        if status in _ERROR_OUTCOME_STATUSES or snapshot.get("_raise"):
            raise GptActionsError(
                str(snapshot.get("message") or snapshot.get("_message") or status),
                code=str(snapshot.get("_code") or status),
                status_code=int(snapshot.get("_statusCode") or 409),
                details=snapshot,
            )
        return snapshot

    def _complete(
        self,
        *,
        key: str,
        actor_id: str,
        request_fingerprint: str,
        snapshot: dict[str, Any],
    ) -> None:
        self._idempotency.complete(
            key=key,
            actor_user_id=actor_id,
            request_fingerprint=request_fingerprint,
            response_snapshot=snapshot,
        )

    def _execute_acquired(
        self,
        *,
        user: Any,
        actor_id: str,
        target: dict[str, Any] | None,
        ops: list[Any],
        catalog_version: str,
        expected_revision: int | None,
        state_fingerprint: str,
        proposal_id: str,
        key: str,
        request_fingerprint: str,
        authorization: str | None,
    ) -> dict[str, Any]:
        current_catalog = PresentationOpsContentService.catalog_version()
        if str(catalog_version or "").strip() != current_catalog:
            # No write yet — still complete with error so replay is stable.
            err = {
                "status": "CATALOG_VERSION_STALE",
                "_raise": True,
                "_code": "CATALOG_VERSION_STALE",
                "_statusCode": 409,
                "message": "Catálogo de capabilities mudou. Refaça catalog → plan → preview.",
                "expectedCatalogVersion": str(catalog_version or "").strip(),
                "currentCatalogVersion": current_catalog,
            }
            self._complete(
                key=key,
                actor_id=actor_id,
                request_fingerprint=request_fingerprint,
                snapshot=err,
            )
            raise GptActionsError(
                err["message"],
                code="CATALOG_VERSION_STALE",
                status_code=409,
                details={
                    "expectedCatalogVersion": err["expectedCatalogVersion"],
                    "currentCatalogVersion": current_catalog,
                },
            )

        playlist_id_raw = str((target or {}).get("playlistId") or "").strip()
        create_only = any(
            isinstance(op, dict) and str(op.get("op") or "").strip() == "create_playlist"
            for op in (ops or [])
        ) and not playlist_id_raw

        if playlist_id_raw:
            if expected_revision is None:
                err = {
                    "status": "INVALID_CHANGE",
                    "_raise": True,
                    "_code": "INVALID_CHANGE",
                    "_statusCode": 422,
                    "message": "expectedRevision é obrigatório para playlist existente.",
                }
                self._complete(
                    key=key,
                    actor_id=actor_id,
                    request_fingerprint=request_fingerprint,
                    snapshot=err,
                )
                raise GptActionsError(
                    err["message"],
                    code="INVALID_CHANGE",
                    status_code=422,
                )
            playlist_uuid = self._parse_uuid_prewrite(playlist_id_raw, field="playlistId")
            access = self._access.resolve(playlist_uuid, user)
            if not access.can_edit:
                err = {
                    "status": "RESOURCE_NOT_FOUND",
                    "_raise": True,
                    "_code": "RESOURCE_NOT_FOUND",
                    "_statusCode": 404,
                    "message": "Programação não encontrada.",
                }
                self._complete(
                    key=key,
                    actor_id=actor_id,
                    request_fingerprint=request_fingerprint,
                    snapshot=err,
                )
                raise GptActionsError(err["message"], code="RESOURCE_NOT_FOUND", status_code=404)

            current_fp = fingerprint(
                {
                    "playlistId": playlist_id_raw,
                    "baseRevision": int(expected_revision),
                    "catalogVersion": str(catalog_version or "").strip(),
                }
            )
            if current_fp != state_fingerprint:
                err = {
                    "status": "PROPOSAL_CHANGED",
                    "_raise": True,
                    "_code": "PROPOSAL_CHANGED",
                    "_statusCode": 409,
                    "message": "Proposta não corresponde ao estado preparado. Refaça o preview.",
                    "expectedFingerprint": state_fingerprint,
                    "actualFingerprint": current_fp,
                    "proposalId": proposal_id,
                }
                self._complete(
                    key=key,
                    actor_id=actor_id,
                    request_fingerprint=request_fingerprint,
                    snapshot=err,
                )
                raise GptActionsError(
                    err["message"],
                    code="PROPOSAL_CHANGED",
                    status_code=409,
                    details={
                        "expectedFingerprint": state_fingerprint,
                        "actualFingerprint": current_fp,
                    },
                )

            try:
                self._writes.assert_expected_revision(playlist_uuid, int(expected_revision))
            except RevisionConflictError as exc:
                err = {
                    "status": "PROPOSAL_CHANGED",
                    "_raise": True,
                    "_code": "PROPOSAL_CHANGED",
                    "_statusCode": 409,
                    "message": (
                        "Estado da playlist mudou desde o PREPARE. Refaça o preview. "
                        f"({exc.message})"
                    ),
                    **exc.details,
                }
                self._complete(
                    key=key,
                    actor_id=actor_id,
                    request_fingerprint=request_fingerprint,
                    snapshot=err,
                )
                raise GptActionsError(
                    err["message"],
                    code="PROPOSAL_CHANGED",
                    status_code=409,
                    details=exc.details,
                ) from exc
            revision_before = int(expected_revision)
        elif not create_only:
            err = {
                "status": "INVALID_CHANGE",
                "_raise": True,
                "_code": "INVALID_CHANGE",
                "_statusCode": 422,
                "message": "playlistId é obrigatório salvo create_playlist.",
            }
            self._complete(
                key=key,
                actor_id=actor_id,
                request_fingerprint=request_fingerprint,
                snapshot=err,
            )
            raise GptActionsError(err["message"], code="INVALID_CHANGE", status_code=422)
        else:
            playlist_uuid = None
            revision_before = None

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
        except PresentationPatchError as exc:
            code = (
                str(getattr(exc, "code", None) or "INVALID_CHANGE").strip()
                or "INVALID_CHANGE"
            )
            err = {
                "status": code,
                "_raise": True,
                "_code": code,
                "_statusCode": 422,
                "message": str(exc),
            }
            self._complete(
                key=key,
                actor_id=actor_id,
                request_fingerprint=request_fingerprint,
                snapshot=err,
            )
            raise GptActionsError(str(exc), code=code, status_code=422) from exc

        applied: list[dict[str, Any]] = []
        outcome: dict[str, Any] = {"appliedOps": [], "created": {}}
        ctx = ExecutionContext.from_target(target if isinstance(target, dict) else {})
        current_playlist = playlist_uuid
        if current_playlist is not None:
            ctx.playlist_id = str(current_playlist)
        current_slide_raw = str((target or {}).get("slideId") or "").strip() or None
        current_slide = (
            self._parse_uuid_prewrite(current_slide_raw, field="slideId")
            if current_slide_raw
            else None
        )
        if current_slide is not None:
            ctx.slide_id = str(current_slide)
        pending_native = False
        chain_revision: int | None = expected_revision
        expected_native_for_verify: dict[str, Any] | None = None

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
                    name = str(raw.get("name") or "").strip() or PresentationOpsContentService.setting_str(
                        "defaultPlaylistName", "Nova programação"
                    )
                    description = raw.get("description")
                    playlist = self._writes.create_playlist(
                        name=name,
                        description=str(description).strip() if description else None,
                        actor_user_id=actor_id,
                    )
                    current_playlist = UUID(str(playlist["id"]))
                    ctx.set_playlist(str(current_playlist), op=raw)
                    outcome["created"]["playlistId"] = str(current_playlist)
                    applied.append(
                        {
                            "op": op_name,
                            "playlistId": str(current_playlist),
                            "expected": {"name": name},
                        }
                    )
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
                                    "expected": {"presetKey": key_s},
                                }
                            )
                    continue

                resolved_playlist = ctx.resolve_playlist_id(raw)
                if resolved_playlist:
                    try:
                        current_playlist = UUID(str(resolved_playlist))
                        ctx.playlist_id = str(current_playlist)
                    except ValueError:
                        pass

                if current_playlist is None:
                    raise GptActionsError(
                        PresentationOpsContentService.message("missingPlaylist"),
                        code="INVALID_CHANGE",
                        status_code=422,
                    )

                if op_name == "add_blank_slide":
                    title = str(raw.get("title") or "").strip() or PresentationOpsContentService.setting_str(
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
                    ctx.set_slide(str(current_slide), op=raw)
                    outcome["created"]["slideId"] = str(current_slide)
                    applied.append(
                        {
                            "op": op_name,
                            "slideId": str(current_slide),
                            "expected": {"title": title},
                        }
                    )
                    continue

                if op_name == "add_slide_from_preset":
                    preset_key = str(raw.get("presetKey") or "").strip()
                    branch = str(raw.get("branch") or "").strip() or None
                    slide = self._writes.add_slide_from_preset(
                        current_playlist,
                        preset_key=preset_key,
                        branch=branch,
                        actor_user_id=actor_id,
                        user=user,
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    current_slide = UUID(str(slide["id"]))
                    ctx.set_slide(str(current_slide), op=raw)
                    outcome["created"]["slideId"] = str(current_slide)
                    applied.append(
                        {
                            "op": op_name,
                            "slideId": str(current_slide),
                            "expected": {"presetKey": preset_key, "branch": branch},
                        }
                    )
                    continue

                if op_name == "update_slide":
                    if current_slide is None:
                        raise GptActionsError(
                            PresentationOpsContentService.message("missingSlide"),
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
                        applied.append(
                            {
                                "op": op_name,
                                "slideId": str(current_slide),
                                "expected": dict(body),
                            }
                        )
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
                    applied.append({"op": op_name, "expected": {"items": items}})
                    continue

                if op_name == "delete_slide":
                    if current_slide is None:
                        raise GptActionsError(
                            PresentationOpsContentService.message("missingSlide"),
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
                            self._parse_uuid_op(section_id, field="sectionId"),
                            body,
                            actor_user_id=actor_id,
                            expected_revision=chain_revision,
                        )
                    else:
                        body = {
                            "name": name
                            or PresentationOpsContentService.setting_str(
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
                    applied.append(
                        {
                            "op": op_name,
                            "sectionId": str(section.get("id") or ""),
                            "expected": dict(body),
                        }
                    )
                    continue

                if op_name == "delete_section":
                    section_id = str(raw.get("sectionId") or "").strip()
                    self._writes.delete_section(
                        current_playlist,
                        self._parse_uuid_op(section_id, field="sectionId"),
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
                            PresentationOpsContentService.message("missingSlide"),
                            code="INVALID_CHANGE",
                            status_code=422,
                        )
                    section_id = raw.get("sectionId")
                    expected_section = (
                        str(section_id).strip() if section_id is not None else None
                    )
                    self._writes.update_slide(
                        current_playlist,
                        current_slide,
                        {"sectionId": expected_section},
                        actor_user_id=actor_id,
                        user=user,
                        expected_revision=chain_revision,
                    )
                    chain_revision = self._writes.get_revision(current_playlist)
                    applied.append(
                        {
                            "op": op_name,
                            "slideId": str(current_slide),
                            "expected": {"sectionId": expected_section},
                        }
                    )
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
                    applied.append({"op": op_name, "expected": {"items": items}})
                    continue

                raise GptActionsError(
                    PresentationOpsContentService.message("unknownOp", op=op_name or "?"),
                    code="UNSUPPORTED_CAPABILITY",
                    status_code=400,
                )

            if pending_native:
                if current_playlist is None or current_slide is None:
                    raise GptActionsError(
                        PresentationOpsContentService.message("missingTarget"),
                        code="INVALID_CHANGE",
                        status_code=422,
                    )
                native_config = preview.get("nativeConfig")
                if not isinstance(native_config, dict):
                    raise GptActionsError(
                        PresentationOpsContentService.message("missingTarget"),
                        code="INVALID_CHANGE",
                        status_code=422,
                    )
                expected_native_for_verify = _strip_transient_native(native_config)
                self._writes.update_slide(
                    current_playlist,
                    current_slide,
                    {"nativeConfig": native_config},
                    actor_user_id=actor_id,
                    user=user,
                    expected_revision=chain_revision,
                )
                chain_revision = self._writes.get_revision(current_playlist)
                applied.append(
                    {
                        "op": "native_config_batch",
                        "slideId": str(current_slide),
                        "expected": {"nativeConfig": expected_native_for_verify},
                    }
                )

        except PresentationWriteError as exc:
            if applied:
                partial = {
                    "status": "PARTIAL_COMMIT",
                    "persisted": True,
                    "verified": False,
                    "revisionBefore": revision_before,
                    "revisionAfter": (
                        self._writes.get_revision(current_playlist)
                        if current_playlist is not None
                        else None
                    ),
                    "outcome": {"appliedOps": applied, "created": outcome.get("created")},
                    "failed": {"code": exc.code, "message": exc.message, **exc.details},
                    "_raise": True,
                    "_code": "PARTIAL_COMMIT",
                    "_statusCode": 409,
                    "message": f"Commit parcial: {exc.message}",
                }
                self._complete(
                    key=key,
                    actor_id=actor_id,
                    request_fingerprint=request_fingerprint,
                    snapshot=partial,
                )
                raise GptActionsError(
                    partial["message"],
                    code="PARTIAL_COMMIT",
                    status_code=409,
                    details=partial,
                ) from exc
            err = {
                "status": exc.code,
                "_raise": True,
                "_code": exc.code,
                "_statusCode": exc.status_code,
                "message": exc.message,
                **exc.details,
            }
            self._complete(
                key=key,
                actor_id=actor_id,
                request_fingerprint=request_fingerprint,
                snapshot=err,
            )
            raise GptActionsError(
                exc.message,
                code=exc.code,
                status_code=exc.status_code,
                details=exc.details,
            ) from exc
        except GptActionsError as exc:
            # Deterministic rejects raised inside the write loop (before or after
            # material effects) must complete the reservation; uncertain infra
            # failures are not converted here.
            if applied:
                partial = {
                    "status": "PARTIAL_COMMIT",
                    "persisted": True,
                    "verified": False,
                    "revisionBefore": revision_before,
                    "revisionAfter": (
                        self._writes.get_revision(current_playlist)
                        if current_playlist is not None
                        else None
                    ),
                    "outcome": {"appliedOps": applied, "created": outcome.get("created")},
                    "failed": {"code": exc.code, "message": str(exc)},
                    "_raise": True,
                    "_code": "PARTIAL_COMMIT",
                    "_statusCode": 409,
                    "message": f"Commit parcial: {exc}",
                }
                self._complete(
                    key=key,
                    actor_id=actor_id,
                    request_fingerprint=request_fingerprint,
                    snapshot=partial,
                )
                raise GptActionsError(
                    partial["message"],
                    code="PARTIAL_COMMIT",
                    status_code=409,
                    details=partial,
                ) from exc
            err = {
                "status": exc.code,
                "_raise": True,
                "_code": exc.code,
                "_statusCode": exc.status_code,
                "message": str(exc),
            }
            if exc.details:
                err.update(exc.details)
            self._complete(
                key=key,
                actor_id=actor_id,
                request_fingerprint=request_fingerprint,
                snapshot=err,
            )
            raise

        outcome["appliedOps"] = applied
        revision_after = (
            self._writes.get_revision(current_playlist) if current_playlist is not None else None
        )
        verified, verify_details = self._verify_postcondition(
            current_playlist=current_playlist,
            applied=applied,
            expected_native=expected_native_for_verify,
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
                "_raise": True,
                "_code": "OUTCOME_NOT_VERIFIED",
                "_statusCode": 409,
                "message": "Write persistido mas pós-condição não comprovada.",
            }
            self._complete(
                key=key,
                actor_id=actor_id,
                request_fingerprint=request_fingerprint,
                snapshot=result,
            )
            raise GptActionsError(
                result["message"],
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
        self._complete(
            key=key,
            actor_id=actor_id,
            request_fingerprint=request_fingerprint,
            snapshot=result,
        )
        return result

    def _verify_postcondition(
        self,
        *,
        current_playlist: UUID | None,
        applied: list[dict[str, Any]],
        expected_native: dict[str, Any] | None,
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
            expected = item.get("expected") if isinstance(item.get("expected"), dict) else {}

            if op == "create_playlist":
                ok = bool(playlist and str(playlist.get("id")) == str(item.get("playlistId")))
                if ok and expected.get("name") is not None:
                    ok = str(playlist.get("name") or "") == str(expected["name"])
                details["checks"].append({"op": op, "ok": ok})
                if not ok:
                    return False, details

            elif op in {"add_blank_slide", "add_slide_from_preset"}:
                sid = str(item.get("slideId") or "")
                slide = slides.get(sid)
                ok = slide is not None
                if ok and "title" in expected:
                    ok = str(slide.get("title") or "") == str(expected["title"])
                details["checks"].append({"op": op, "ok": ok, "slideId": sid})
                if not ok:
                    return False, details

            elif op == "update_slide":
                sid = str(item.get("slideId") or "")
                slide = slides.get(sid)
                if not slide:
                    details["checks"].append({"op": op, "ok": False, "slideId": sid})
                    return False, details
                ok = True
                for field, value in expected.items():
                    if field == "title" and str(slide.get("title") or "") != str(value):
                        ok = False
                    elif field == "durationSec" and slide.get("durationSec") != value:
                        ok = False
                    elif field == "isActive" and bool(slide.get("isActive")) != bool(value):
                        ok = False
                details["checks"].append({"op": op, "ok": ok, "slideId": sid, "expected": expected})
                if not ok:
                    return False, details

            elif op == "delete_slide":
                sid = str(item.get("slideId") or "")
                ok = sid not in slides
                details["checks"].append({"op": op, "ok": ok, "slideId": sid})
                if not ok:
                    return False, details

            elif op == "reorder_slides":
                items = expected.get("items") if isinstance(expected.get("items"), list) else []
                ok = True
                by_id = {str(s.get("id")): s for s in slides.values()}
                for entry in items:
                    if not isinstance(entry, dict):
                        continue
                    sid = str(entry.get("id") or "")
                    want = entry.get("sortOrder")
                    got = (by_id.get(sid) or {}).get("sortOrder")
                    if sid not in by_id or got != want:
                        ok = False
                        break
                details["checks"].append({"op": op, "ok": ok})
                if not ok:
                    return False, details

            elif op == "upsert_section":
                sid = str(item.get("sectionId") or "")
                section = sections.get(sid)
                if not section:
                    details["checks"].append({"op": op, "ok": False, "sectionId": sid})
                    return False, details
                ok = True
                for field, value in expected.items():
                    if field == "name" and str(section.get("name") or "") != str(value):
                        ok = False
                    elif field == "isCollapsed" and bool(section.get("isCollapsed")) != bool(value):
                        ok = False
                    elif field == "isActive" and bool(section.get("isActive")) != bool(value):
                        ok = False
                    elif field == "sortOrder" and section.get("sortOrder") != value:
                        ok = False
                details["checks"].append({"op": op, "ok": ok, "sectionId": sid})
                if not ok:
                    return False, details

            elif op == "delete_section":
                sid = str(item.get("sectionId") or "")
                ok = sid not in sections
                details["checks"].append({"op": op, "ok": ok, "sectionId": sid})
                if not ok:
                    return False, details

            elif op == "move_slide_to_section":
                sid = str(item.get("slideId") or "")
                slide = slides.get(sid)
                if not slide:
                    details["checks"].append({"op": op, "ok": False, "slideId": sid})
                    return False, details
                want = expected.get("sectionId")
                got = slide.get("sectionId")
                got_s = str(got).strip() if got is not None else None
                want_s = str(want).strip() if want is not None else None
                ok = got_s == want_s
                details["checks"].append(
                    {"op": op, "ok": ok, "slideId": sid, "sectionId": got_s}
                )
                if not ok:
                    return False, details

            elif op == "reorder_sections":
                items = expected.get("items") if isinstance(expected.get("items"), list) else []
                ok = True
                for entry in items:
                    if not isinstance(entry, dict):
                        continue
                    sid = str(entry.get("id") or "")
                    want = entry.get("sortOrder")
                    got = (sections.get(sid) or {}).get("sortOrder")
                    if sid not in sections or got != want:
                        ok = False
                        break
                details["checks"].append({"op": op, "ok": ok})
                if not ok:
                    return False, details

            elif op == "native_config_batch":
                sid = str(item.get("slideId") or "")
                slide = slides.get(sid)
                if not slide:
                    details["checks"].append({"op": op, "ok": False, "reason": "slide_missing"})
                    return False, details
                persisted = slide.get("nativeConfig")
                want = expected.get("nativeConfig") or expected_native
                if not isinstance(persisted, dict) or not isinstance(want, dict):
                    details["checks"].append({"op": op, "ok": False, "reason": "native_missing"})
                    return False, details
                ok = _strip_transient_native(persisted) == _strip_transient_native(want)
                details["checks"].append({"op": op, "ok": ok, "slideId": sid})
                if not ok:
                    return False, details
                from tv_app.application.services.data.ready_slide_quality_service import (
                    ReadySlideQualityService,
                )
                from tv_app.application.services.tv_data_route_catalog_service import (
                    TvDataRouteCatalogService,
                )

                catalog = TvDataRouteCatalogService()
                quality_issues = ReadySlideQualityService.collect_native_quality_issues(
                    want if isinstance(want, dict) else persisted,
                    catalog=catalog,
                )
                if quality_issues:
                    details["checks"].append(
                        {
                            "op": op,
                            "ok": False,
                            "reason": "ready_slide_quality",
                            "issues": quality_issues[:8],
                        }
                    )
                    return False, details

            else:
                details["checks"].append(
                    {"op": op, "ok": False, "reason": "unsupported_postcondition"}
                )
                return False, details

        return True, details
