"""Traduz ops tipadas do copiloto em comandos HTTP CRUD allowlisted.

O BFF planeja; a AI executa as rotas reais ``/playlists/**`` com o JWT do
usuário. Não há segundo writer: create/update/delete passam pelas mesmas
rotas do editor.
"""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.presentation_mutation.execution_context import (
    is_synthetic_id,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)

# Ops que mutam o documento nativeConfig do slide — um PATCH coalescido por slide.
_NATIVE_CONFIG_OPS = frozenset(
    {
        "upsert_data_source",
        "set_data_transform",
        "upsert_block",
        "delete_block",
        "bind_visual",
        "patch_native_config",
        "ensure_brand_logo_on_slide",
        "apply_published_slide_template",
        "re_layer_playlist_filters",
    }
)

_ALLOWED_METHODS = frozenset({"GET", "POST", "PATCH", "DELETE"})


def _cmd(
    *,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    op: str,
    requires_if_match: bool = True,
) -> dict[str, Any]:
    method_u = str(method or "").strip().upper()
    path_s = str(path or "").strip()
    if method_u not in _ALLOWED_METHODS:
        raise ValueError(f"Método HTTP não allowlisted: {method_u}")
    if not path_s.startswith("/playlists"):
        raise ValueError(f"Path HTTP fora do CRUD TV: {path_s}")
    out: dict[str, Any] = {
        "method": method_u,
        "path": path_s,
        "op": op,
        "requiresIfMatch": bool(requires_if_match),
    }
    if body is not None:
        out["body"] = body
    return out


def _resolve_op_slide_id(
    raw: dict[str, Any],
    *,
    current_slide: str | None,
    aliases: dict[str, str],
) -> str | None:
    ref = str(raw.get("slideRef") or "").strip()
    if ref:
        return str(aliases.get(ref, ref)).strip() or None
    return current_slide


class PresentationHttpCommandPlannerService:
    """Gera lista ordenada de comandos CRUD a partir do resultado do redutor."""

    @classmethod
    def build(
        cls,
        *,
        ops: list[Any],
        target: dict[str, Any] | None,
        native_config: dict[str, Any] | None,
        base_revision: int | None,
        native_configs_by_slide: dict[str, Any] | None = None,
        alias_map: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        playlist_id = str((target or {}).get("playlistId") or "").strip() or None
        slide_id = str((target or {}).get("slideId") or "").strip() or None
        commands: list[dict[str, Any]] = []
        pending_native_any = False
        # playlistId pode ser criado no meio do lote; track local para paths seguintes.
        current_playlist = playlist_id
        current_slide = slide_id
        aliases = {
            str(k): str(v)
            for k, v in (alias_map or {}).items()
            if str(k).strip() and str(v).strip()
        }

        for raw in ops:
            if not isinstance(raw, dict):
                continue
            op_name = str(raw.get("op") or "").strip()
            if not op_name:
                continue

            if op_name in _NATIVE_CONFIG_OPS:
                pending_native_any = True
                continue

            if op_name == "create_playlist":
                name = str(raw.get("name") or "").strip() or PresentationOpsContentService.setting_str(
                    "defaultPlaylistName", "Nova programação"
                )
                body: dict[str, Any] = {"name": name}
                description = raw.get("description")
                if description is not None and str(description).strip():
                    body["description"] = str(description).strip()
                commands.append(
                    _cmd(
                        method="POST",
                        path="/playlists",
                        body=body,
                        op=op_name,
                        requires_if_match=False,
                    )
                )
                # Paths seguintes precisam do id retornado; o executor AI
                # substitui {playlistId} pelo id da resposta anterior.
                current_playlist = "{playlistId}"
                seed_presets = raw.get("seedPresetKeys")
                if isinstance(seed_presets, list):
                    for key in seed_presets:
                        key_s = str(key or "").strip()
                        if not key_s:
                            continue
                        commands.append(
                            _cmd(
                                method="POST",
                                path=f"/playlists/{current_playlist}/slides/from-preset",
                                body={"presetKey": key_s},
                                op="add_slide_from_preset",
                                requires_if_match=False,
                            )
                        )
                continue

            if not current_playlist:
                raise ValueError(
                    PresentationOpsContentService.message("missingPlaylist")
                )

            if op_name == "patch_playlist_data_defaults":
                raw_defaults = raw.get("dataDefaults")
                if not isinstance(raw_defaults, dict):
                    raise ValueError(
                        PresentationOpsContentService.message("playlistDefaultsRequired")
                    )
                commands.append(
                    _cmd(
                        method="PATCH",
                        path=f"/playlists/{current_playlist}",
                        body={"dataDefaults": raw_defaults},
                        op=op_name,
                    )
                )
                continue

            if op_name == "add_blank_slide":
                title = str(raw.get("title") or "").strip() or PresentationOpsContentService.setting_str(
                    "defaultSlideTitle", "Slide personalizado"
                )
                native_cfg: dict[str, Any] = {
                    "version": 5,
                    "headline": "",
                    "subtitle": "",
                    "blocks": [],
                }
                if isinstance(raw.get("background"), dict):
                    native_cfg["background"] = dict(raw["background"])
                duration_sec = raw.get("durationSec")
                try:
                    duration = int(duration_sec) if duration_sec is not None else 30
                except (TypeError, ValueError):
                    duration = 30
                body = {
                    "slideType": "native",
                    "title": title,
                    "nativeScreenKey": "custom_message",
                    "nativeConfig": native_cfg,
                    "durationSec": duration,
                }
                section_id = str(raw.get("sectionId") or "").strip()
                if section_id:
                    body["sectionId"] = section_id
                commands.append(
                    _cmd(
                        method="POST",
                        path=f"/playlists/{current_playlist}/slides",
                        body=body,
                        op=op_name,
                    )
                )
                as_alias = str(raw.get("as") or "").strip()
                current_slide = "{slideId}"
                if as_alias:
                    aliases[as_alias] = "{slideId}"
                continue

            if op_name == "add_slide_from_preset":
                preset_key = str(raw.get("presetKey") or "").strip()
                body = {"presetKey": preset_key}
                branch = str(raw.get("branch") or "").strip()
                if branch:
                    body["branch"] = branch
                commands.append(
                    _cmd(
                        method="POST",
                        path=f"/playlists/{current_playlist}/slides/from-preset",
                        body=body,
                        op=op_name,
                    )
                )
                as_alias = str(raw.get("as") or "").strip()
                current_slide = "{slideId}"
                if as_alias:
                    aliases[as_alias] = "{slideId}"
                continue

            if op_name == "update_slide":
                sid = _resolve_op_slide_id(
                    raw, current_slide=current_slide, aliases=aliases
                )
                if not sid:
                    raise ValueError(PresentationOpsContentService.message("missingSlide"))
                body = {}
                if "title" in raw and raw["title"] is not None:
                    body["title"] = str(raw["title"]).strip()
                if "durationSec" in raw:
                    body["durationSec"] = raw["durationSec"]
                if "isActive" in raw and raw["isActive"] is not None:
                    body["isActive"] = bool(raw["isActive"])
                if not body:
                    continue
                commands.append(
                    _cmd(
                        method="PATCH",
                        path=f"/playlists/{current_playlist}/slides/{sid}",
                        body=body,
                        op=op_name,
                    )
                )
                continue

            if op_name == "reorder_slides":
                items = raw.get("items") if isinstance(raw.get("items"), list) else []
                commands.append(
                    _cmd(
                        method="POST",
                        path=f"/playlists/{current_playlist}/slides/reorder",
                        body={"items": items},
                        op=op_name,
                    )
                )
                continue

            if op_name == "delete_slide":
                sid = _resolve_op_slide_id(
                    raw, current_slide=current_slide, aliases=aliases
                )
                if not sid:
                    raise ValueError(PresentationOpsContentService.message("missingSlide"))
                commands.append(
                    _cmd(
                        method="DELETE",
                        path=f"/playlists/{current_playlist}/slides/{sid}",
                        op=op_name,
                    )
                )
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
                    commands.append(
                        _cmd(
                            method="PATCH",
                            path=f"/playlists/{current_playlist}/sections/{section_id}",
                            body=body,
                            op=op_name,
                        )
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
                    commands.append(
                        _cmd(
                            method="POST",
                            path=f"/playlists/{current_playlist}/sections",
                            body=body,
                            op=op_name,
                        )
                    )
                continue

            if op_name == "delete_section":
                section_id = str(raw.get("sectionId") or "").strip()
                delete_slides = bool(raw.get("deleteSlides"))
                path = (
                    f"/playlists/{current_playlist}/sections/{section_id}"
                    f"?deleteSlides={'true' if delete_slides else 'false'}"
                )
                commands.append(
                    _cmd(method="DELETE", path=path, op=op_name)
                )
                continue

            if op_name == "move_slide_to_section":
                sid = _resolve_op_slide_id(
                    raw, current_slide=current_slide, aliases=aliases
                )
                if not sid:
                    raise ValueError(PresentationOpsContentService.message("missingSlide"))
                section_id = raw.get("sectionId")
                body = {
                    "sectionId": (
                        str(section_id).strip() if section_id is not None else None
                    )
                }
                commands.append(
                    _cmd(
                        method="PATCH",
                        path=f"/playlists/{current_playlist}/slides/{sid}",
                        body=body,
                        op=op_name,
                    )
                )
                continue

            if op_name == "reorder_sections":
                items = raw.get("items") if isinstance(raw.get("items"), list) else []
                commands.append(
                    _cmd(
                        method="POST",
                        path=f"/playlists/{current_playlist}/sections/reorder",
                        body={"items": items},
                        op=op_name,
                    )
                )
                continue

            raise ValueError(
                PresentationOpsContentService.message("unknownOp", op=op_name or "?")
            )

        if pending_native_any:
            if not current_playlist:
                raise ValueError(PresentationOpsContentService.message("missingTarget"))
            by_slide: dict[str, dict[str, Any]] = {}
            if isinstance(native_configs_by_slide, dict):
                for sid, cfg in native_configs_by_slide.items():
                    sid_s = str(sid or "").strip()
                    if (
                        sid_s
                        and isinstance(cfg, dict)
                        and not is_synthetic_id(sid_s)
                    ):
                        by_slide[sid_s] = cfg
            emitted: set[str] = set()
            for sid, cfg in by_slide.items():
                commands.append(
                    _cmd(
                        method="PATCH",
                        path=f"/playlists/{current_playlist}/slides/{sid}",
                        body={"nativeConfig": cfg},
                        op="native_config_batch",
                    )
                )
                emitted.add(sid)
            # New slide (syn filtered from by_slide) or legacy single blob.
            if not emitted:
                if not isinstance(native_config, dict):
                    raise ValueError(PresentationOpsContentService.message("missingTarget"))
                path_sid = current_slide or "{slideId}"
                if not path_sid:
                    raise ValueError(PresentationOpsContentService.message("missingTarget"))
                commands.append(
                    _cmd(
                        method="PATCH",
                        path=f"/playlists/{current_playlist}/slides/{path_sid}",
                        body={"nativeConfig": native_config},
                        op="native_config_batch",
                    )
                )

        if base_revision is not None:
            for command in commands:
                if command.get("requiresIfMatch"):
                    command["expectedRevision"] = int(base_revision)

        return commands
