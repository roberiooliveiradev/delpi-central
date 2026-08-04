"""TvCopilotPatchV1 — preview/apply de ops tipadas no modelo de slide/playlist.

Não grava `resolved`. Não gera M. Preview usa SlideDataResolutionService.
Apply persiste + notify_presentation_changed (cache + WS).
"""

from __future__ import annotations

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
from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)
from tv_app.application.services.data.tv_copilot_telemetry import record_copilot_event
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
    PlaylistNotFoundError,
    PlaylistRepository,
    SlideNotFoundError,
)


class TvCopilotPatchError(ValueError):
    """Erro de validação do envelope / ops."""


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
            # Campos típicos IDD/SI / KPI — valores escalares ou summary
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


class TvCopilotPatchService:
    """Aplica envelope TvCopilotPatchV1 sobre native_config / playlist."""

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
            result = self._run(envelope, user=user, persist=False, authorization=authorization)
            if include_fingerprint and result.get("nativeConfig"):
                result["fingerprint"] = self._resolve_fingerprint(
                    result["nativeConfig"],
                    user=user,
                    authorization=authorization,
                    playlist_defaults=result.get("playlistDefaults"),
                )
            record_copilot_event(
                kind="preview",
                ok=True,
                ops_count=len(result.get("appliedOps") or []),
                elapsed_ms=(time.perf_counter() - started) * 1000,
            )
            result["message"] = TvCopilotContentService.message(
                "previewOk",
                ops=len(result.get("appliedOps") or []),
            )
            return result
        except TvCopilotPatchError as exc:
            record_copilot_event(
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
        started = time.perf_counter()
        try:
            result = self._run(
                envelope,
                user=user,
                persist=True,
                authorization=authorization,
                actor_user_id=actor_user_id,
            )
            record_copilot_event(
                kind="apply",
                ok=True,
                ops_count=len(result.get("appliedOps") or []),
                elapsed_ms=(time.perf_counter() - started) * 1000,
            )
            result["message"] = TvCopilotContentService.message(
                "applyOk",
                ops=len(result.get("appliedOps") or []),
            )
            return result
        except TvCopilotPatchError as exc:
            record_copilot_event(
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
        if not isinstance(envelope, dict):
            raise TvCopilotPatchError(TvCopilotContentService.message("invalidEnvelope"))

        ops = envelope.get("ops")
        if not isinstance(ops, list) or not ops:
            raise TvCopilotPatchError(TvCopilotContentService.message("noOps"))

        max_ops = TvCopilotContentService.setting_int("maxOpsPerPatch", 40)
        if len(ops) > max_ops:
            raise TvCopilotPatchError(TvCopilotContentService.message("noOps"))

        target = envelope.get("target") if isinstance(envelope.get("target"), dict) else {}
        allowed = TvCopilotContentService.allowed_ops()
        applied: list[str] = []
        side_effects: dict[str, Any] = {}

        # create_playlist pode rodar sem slide
        playlist_id = str(target.get("playlistId") or "").strip() or None
        slide_id = str(target.get("slideId") or "").strip() or None
        native_config: dict[str, Any] | None = None
        playlist_defaults: dict[str, Any] | None = None
        before_blocks: list[dict[str, Any]] = []

        needs_slide = any(
            str((op or {}).get("op") or "")
            in {
                "upsert_data_source",
                "set_data_transform",
                "upsert_block",
                "bind_visual",
            }
            for op in ops
            if isinstance(op, dict)
        )

        if needs_slide:
            if not playlist_id or not slide_id:
                raise TvCopilotPatchError(TvCopilotContentService.message("missingTarget"))
            slide = self._load_slide(playlist_id, slide_id)
            native_config = copy.deepcopy(slide.get("nativeConfig") or {})
            if not isinstance(native_config, dict):
                native_config = {}
            if "version" not in native_config:
                native_config["version"] = 5
            before_blocks = copy.deepcopy(_blocks_of(native_config))
            try:
                pl = self._repo.get(UUID(playlist_id))
                playlist_defaults = (
                    dict(pl.get("dataDefaults") or {})
                    if isinstance(pl.get("dataDefaults"), dict)
                    else None
                )
            except (PlaylistNotFoundError, ValueError):
                playlist_defaults = None

        for raw_op in ops:
            if not isinstance(raw_op, dict):
                raise TvCopilotPatchError(TvCopilotContentService.message("unknownOp", op="?"))
            op_name = str(raw_op.get("op") or "").strip()
            if op_name not in allowed:
                record_copilot_event(kind="preview", ok=False, rejected_op=op_name)
                raise TvCopilotPatchError(
                    TvCopilotContentService.message("unknownOp", op=op_name or "?")
                )
            if op_name == "create_playlist":
                created = self._op_create_playlist(
                    raw_op,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                side_effects["playlist"] = created
                if created.get("id"):
                    playlist_id = str(created["id"])
                applied.append(op_name)
                continue

            if op_name == "add_slide_from_preset":
                if not playlist_id:
                    raise TvCopilotPatchError(TvCopilotContentService.message("missingTarget"))
                created_slide = self._op_add_slide_from_preset(
                    playlist_id,
                    raw_op,
                    user=user,
                    persist=persist,
                    actor_user_id=actor_user_id,
                )
                side_effects.setdefault("slides", []).append(created_slide)
                if created_slide.get("id") and not slide_id:
                    slide_id = str(created_slide["id"])
                    native_config = copy.deepcopy(created_slide.get("nativeConfig") or {})
                    if isinstance(native_config, dict):
                        before_blocks = copy.deepcopy(_blocks_of(native_config))
                applied.append(op_name)
                continue

            assert native_config is not None
            if op_name == "upsert_data_source":
                self._op_upsert_data_source(native_config, raw_op)
            elif op_name == "set_data_transform":
                self._op_set_data_transform(native_config, raw_op)
            elif op_name == "upsert_block":
                self._op_upsert_block(native_config, raw_op)
            elif op_name == "bind_visual":
                self._op_bind_visual(native_config, raw_op)
            applied.append(op_name)

        result: dict[str, Any] = {
            "ok": True,
            "version": "TvCopilotPatchV1",
            "appliedOps": applied,
            "target": {"playlistId": playlist_id, "slideId": slide_id},
            "sideEffects": side_effects,
            "playlistDefaults": playlist_defaults,
        }

        if native_config is not None:
            # Nunca persistir resolved
            cleaned = sanitize_and_hydrate_comunicado_config(
                native_config, catalog=self._catalog
            )
            validate_comunicado_native_config(cleaned, user=user, catalog=self._catalog)
            after_blocks = _blocks_of(cleaned)
            result["nativeConfig"] = cleaned
            result["diff"] = _diff_blocks(before_blocks, after_blocks)

            if persist and playlist_id and slide_id and actor_user_id:
                self._repo.update_slide(
                    UUID(playlist_id),
                    UUID(slide_id),
                    {"nativeConfig": cleaned},
                    actor_user_id=actor_user_id,
                    reason="copilot_patch_applied",
                )
                notify_presentation_changed(
                    playlist_id=playlist_id,
                    reason="copilot_patch_applied",
                )
                result["persisted"] = True
            else:
                result["persisted"] = False

        return result

    def _load_slide(self, playlist_id: str, slide_id: str) -> dict[str, Any]:
        try:
            return self._repo.get_slide(UUID(slide_id), playlist_id=UUID(playlist_id))
        except (SlideNotFoundError, ValueError) as exc:
            raise TvCopilotPatchError(TvCopilotContentService.message("slideNotFound")) from exc
        except PlaylistNotFoundError as exc:
            raise TvCopilotPatchError(
                TvCopilotContentService.message("playlistNotFound")
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
        cap = TvCopilotContentService.setting_int("fingerprintMaxBlocks", 12)
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

    def _op_upsert_data_source(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        operation_id = str(op.get("operationId") or "").strip()
        if not operation_id:
            raise TvCopilotPatchError(
                TvCopilotContentService.message("operationNotInCatalog", operationId="")
            )
        route = self._catalog.get_route(operation_id)
        if not route:
            raise TvCopilotPatchError(
                TvCopilotContentService.message(
                    "operationNotInCatalog", operationId=operation_id
                )
            )
        block_id = str(op.get("blockId") or "").strip() or _new_block_id()
        params = op.get("params") if isinstance(op.get("params"), dict) else {}
        label = op.get("label") or route.get("label") or operation_id
        blocks = _blocks_of(cfg)
        existing = _find_block(blocks, block_id)
        binding = {
            "operationId": operation_id,
            "params": dict(params),
            "displayMode": str(op.get("displayMode") or "auto"),
            "label": label,
        }
        if existing is not None:
            existing["type"] = "data_source"
            existing["dataBinding"] = binding
            existing.pop("resolved", None)
            if isinstance(op.get("dataTransform"), dict):
                existing["dataTransform"] = op["dataTransform"]
            return
        block: dict[str, Any] = {
            "id": block_id,
            "type": "data_source",
            "frame": {"x": 8, "y": 30, "w": 18, "h": 18},
            "style": {"zIndex": 1},
            "dataBinding": binding,
        }
        if isinstance(op.get("dataTransform"), dict):
            block["dataTransform"] = op["dataTransform"]
        blocks.append(block)
        cfg["blocks"] = blocks

    def _op_set_data_transform(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        block_id = str(op.get("blockId") or "").strip()
        blocks = _blocks_of(cfg)
        block = _find_block(blocks, block_id) if block_id else None
        if block is None:
            # fallback: primary data_source
            for candidate in blocks:
                if str(candidate.get("type") or "") == "data_source":
                    block = candidate
                    break
        if block is None:
            raise TvCopilotPatchError(
                TvCopilotContentService.message("blockNotFound", blockId=block_id or "?")
            )
        steps = op.get("steps")
        if steps is None and isinstance(op.get("dataTransform"), dict):
            transform = op["dataTransform"]
        else:
            transform = {"steps": list(steps) if isinstance(steps, list) else []}
        block["dataTransform"] = transform
        block.pop("resolved", None)

    def _op_upsert_block(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        block = op.get("block")
        if not isinstance(block, dict):
            raise TvCopilotPatchError(
                TvCopilotContentService.message("blockNotFound", blockId="?")
            )
        # Anti-padrão: nunca aceitar resolved / M script
        cleaned = dict(block)
        cleaned.pop("resolved", None)
        cleaned.pop("url", None)
        if cleaned.get("mScript") or cleaned.get("powerQueryM"):
            raise TvCopilotPatchError(TvCopilotContentService.message("mForbidden"))
        block_id = str(cleaned.get("id") or "").strip() or _new_block_id()
        cleaned["id"] = block_id
        blocks = _blocks_of(cfg)
        existing = _find_block(blocks, block_id)
        if existing is not None:
            existing.clear()
            existing.update(cleaned)
        else:
            blocks.append(cleaned)
        cfg["blocks"] = blocks

    def _op_bind_visual(self, cfg: dict[str, Any], op: dict[str, Any]) -> None:
        visual_id = str(op.get("visualId") or "").strip()
        data_source_id = str(op.get("dataSourceId") or "").strip()
        if not visual_id or not data_source_id:
            raise TvCopilotPatchError(TvCopilotContentService.message("bindNeedIds"))
        blocks = _blocks_of(cfg)
        visual = _find_block(blocks, visual_id)
        source = _find_block(blocks, data_source_id)
        if visual is None:
            raise TvCopilotPatchError(
                TvCopilotContentService.message("blockNotFound", blockId=visual_id)
            )
        if source is None:
            raise TvCopilotPatchError(
                TvCopilotContentService.message("blockNotFound", blockId=data_source_id)
            )
        visual["dataSourceId"] = data_source_id
        visual.pop("resolved", None)

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
            raise TvCopilotPatchError(TvCopilotContentService.message("presetRequired"))
        try:
            payload = resolve_preset_slide(preset_key)
        except SlidePresetNotFoundError as exc:
            raise TvCopilotPatchError(
                TvCopilotContentService.message("presetRequired")
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
            raise TvCopilotPatchError(TvCopilotContentService.message("missingTarget"))
        slide = self._repo.add_slide(
            UUID(playlist_id),
            payload,
            actor_user_id=actor_user_id,
            reason="copilot_slide_from_preset",
        )
        notify_presentation_changed(
            playlist_id=playlist_id,
            reason="copilot_slide_from_preset",
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
            raise TvCopilotPatchError(TvCopilotContentService.message("playlistNameRequired"))
        description = op.get("description")
        if not persist:
            return {
                "id": None,
                "preview": True,
                "name": name,
                "description": description,
            }
        if not actor_user_id:
            raise TvCopilotPatchError(TvCopilotContentService.message("missingTarget"))
        playlist = self._repo.create(
            name=name,
            description=str(description) if description is not None else None,
            created_by=actor_user_id,
        )
        notify_presentation_changed(
            playlist_id=str(playlist.get("id") or ""),
            reason="copilot_playlist_created",
        )
        # Seed opcional de presets
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
                        reason="copilot_playlist_seed",
                    )
                    seeded.append({"id": slide.get("id"), "presetKey": key_s})
                except SlidePresetNotFoundError:
                    continue
            if seeded:
                notify_presentation_changed(
                    playlist_id=str(playlist["id"]),
                    reason="copilot_playlist_seed",
                )
        playlist["seededSlides"] = seeded
        return playlist
