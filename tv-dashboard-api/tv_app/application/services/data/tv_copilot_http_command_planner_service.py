"""Traduz ops tipadas do copiloto em comandos HTTP CRUD allowlisted.

O BFF planeja; a AI executa as rotas reais ``/playlists/**`` com o JWT do
usuário. Não há segundo writer: create/update/delete passam pelas mesmas
rotas do editor.
"""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)

# Ops que mutam o documento nativeConfig do slide — um único PATCH coalescido.
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


class TvCopilotHttpCommandPlannerService:
    """Gera lista ordenada de comandos CRUD a partir do resultado do redutor."""

    @classmethod
    def build(
        cls,
        *,
        ops: list[Any],
        target: dict[str, Any] | None,
        native_config: dict[str, Any] | None,
        base_revision: int | None,
    ) -> list[dict[str, Any]]:
        playlist_id = str((target or {}).get("playlistId") or "").strip() or None
        slide_id = str((target or {}).get("slideId") or "").strip() or None
        commands: list[dict[str, Any]] = []
        pending_native = False
        # playlistId pode ser criado no meio do lote; track local para paths seguintes.
        current_playlist = playlist_id
        current_slide = slide_id

        for raw in ops:
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
                    TvCopilotContentService.message("missingPlaylist")
                )

            if op_name == "add_blank_slide":
                title = str(raw.get("title") or "").strip() or TvCopilotContentService.setting_str(
                    "defaultSlideTitle", "Slide personalizado"
                )
                body = {
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
                    body["sectionId"] = section_id
                commands.append(
                    _cmd(
                        method="POST",
                        path=f"/playlists/{current_playlist}/slides",
                        body=body,
                        op=op_name,
                    )
                )
                if not current_slide:
                    current_slide = "{slideId}"
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
                if not current_slide:
                    current_slide = "{slideId}"
                continue

            if op_name == "update_slide":
                if not current_slide:
                    raise ValueError(TvCopilotContentService.message("missingSlide"))
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
                        path=f"/playlists/{current_playlist}/slides/{current_slide}",
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
                if not current_slide:
                    raise ValueError(TvCopilotContentService.message("missingSlide"))
                commands.append(
                    _cmd(
                        method="DELETE",
                        path=f"/playlists/{current_playlist}/slides/{current_slide}",
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
                        or TvCopilotContentService.setting_str(
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
                if not current_slide:
                    raise ValueError(TvCopilotContentService.message("missingSlide"))
                section_id = raw.get("sectionId")
                body = {
                    "sectionId": (
                        str(section_id).strip() if section_id is not None else None
                    )
                }
                commands.append(
                    _cmd(
                        method="PATCH",
                        path=f"/playlists/{current_playlist}/slides/{current_slide}",
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
                TvCopilotContentService.message("unknownOp", op=op_name or "?")
            )

        if pending_native:
            if not current_playlist or not current_slide:
                raise ValueError(TvCopilotContentService.message("missingTarget"))
            if not isinstance(native_config, dict):
                raise ValueError(TvCopilotContentService.message("missingTarget"))
            commands.append(
                _cmd(
                    method="PATCH",
                    path=f"/playlists/{current_playlist}/slides/{current_slide}",
                    body={"nativeConfig": native_config},
                    op="native_config_batch",
                )
            )

        if base_revision is not None:
            for command in commands:
                if command.get("requiresIfMatch"):
                    command["expectedRevision"] = int(base_revision)

        return commands
