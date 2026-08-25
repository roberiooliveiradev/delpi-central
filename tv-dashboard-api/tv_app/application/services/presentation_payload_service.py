from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.services.comunicado_enrichment_service import ComunicadoEnrichmentService
from tv_app.application.services.native_screen_data_service import NativeScreenDataService
from tv_app.application.services.playlist_section_inheritance_service import (
    is_slide_visible_in_presentation,
    merge_master_configs,
    resolve_slide_duration_sec,
    resolve_slide_transition_style,
)
from tv_app.application.services.public_filter_overrides_service import (
    allowlist_filter_overrides,
    collect_allowed_input_keys_from_playlist_slides,
)
from tv_app.application.services.tv_dashboard_content_service import (
    heartbeat_interval_sec,
    presentation_setting_int,
)
from tv_app.config import settings
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistNotFoundError,
    PlaylistRepository,
)


class PresentationPayloadService:
    def __init__(
        self,
        repository: PlaylistRepository | None = None,
        native_data: NativeScreenDataService | None = None,
        comunicado_enrichment: ComunicadoEnrichmentService | None = None,
    ) -> None:
        self._repo = repository or PlaylistRepository()
        self._native_data = native_data or NativeScreenDataService()
        self._comunicado = comunicado_enrichment or ComunicadoEnrichmentService()

    def build_public_url(self, public_token: str) -> str:
        base = (settings.PUBLIC_BASE_URL or "http://localhost").rstrip("/")
        path = settings.TV_DASHBOARD_PUBLIC_PATH.rstrip("/")
        return f"{base}{path}/{public_token}"

    def build_by_token(
        self,
        token: str,
        *,
        authorization: str | None = None,
        track_view: bool = False,
        user: Any | None = None,
        filter_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        playlist = self._repo.get_by_token(token)
        if not playlist or not playlist.get("isActive"):
            return None
        if track_view:
            try:
                self._repo.touch_view(token)
            except Exception:
                pass
        return self._assemble_payload(
            playlist,
            authorization=authorization,
            public_media_urls=True,
            user=user,
            filter_overrides=filter_overrides,
        )

    def build_by_id(
        self,
        playlist_id: UUID,
        *,
        authorization: str | None = None,
        user: Any | None = None,
        filter_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Payload da prévia admin (`/preview-payload`).

        `public_media_urls=True` — mesmo contrato de mídia do `/present/`
        (`/public/present/{token}/media/...`). `<img>`/CSS na prévia não enviam
        Authorization; URL admin + `access_token` é frágil e divergia da TV.
        """
        playlist = self._repo.get_by_id(playlist_id)
        if not playlist:
            raise PlaylistNotFoundError
        return self._assemble_payload(
            playlist,
            authorization=authorization,
            public_media_urls=True,
            user=user,
            filter_overrides=filter_overrides,
        )

    def _assemble_payload(
        self,
        playlist: dict[str, Any],
        *,
        authorization: str | None,
        public_media_urls: bool = False,
        user: Any | None = None,
        filter_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        playlist_uuid = UUID(playlist["id"])
        all_sections = self._repo.list_sections(playlist_uuid)
        section_by_id = {s["id"]: s for s in all_sections}
        active_sections = [s for s in all_sections if s.get("isActive", True)]

        slides = [
            slide
            for slide in self._repo.list_slides(playlist_uuid)
            if is_slide_visible_in_presentation(
                slide_active=bool(slide.get("isActive", True)),
                section=section_by_id.get(slide.get("sectionId") or ""),
            )
        ]
        default_duration = playlist.get("defaultDurationSec") or 30
        playlist_transition = playlist.get("transitionStyle") or "fade"
        playlist_id = str(playlist["id"])
        public_token = str(playlist["publicToken"]) if public_media_urls else None
        playlist_defaults = (
            playlist.get("dataDefaults") if isinstance(playlist.get("dataDefaults"), dict) else {}
        )
        allowed_slide_keys, allowed_by_source = collect_allowed_input_keys_from_playlist_slides(
            slides
        )
        safe_overrides = allowlist_filter_overrides(
            filter_overrides,
            allowed_slide_keys=allowed_slide_keys,
            allowed_by_source=allowed_by_source,
        )

        master_raw = (
            playlist.get("masterConfig") if isinstance(playlist.get("masterConfig"), dict) else {}
        )
        playlist_master = self._comunicado.enrich_master_config(
            master_raw,
            api_root_path=settings.TV_DASHBOARD_API_ROOT_PATH,
            playlist_id=playlist_id,
            public_token=public_token,
        )

        rendered_sections: list[dict[str, Any]] = []
        section_master_by_id: dict[str, dict[str, Any] | None] = {}
        for section in active_sections:
            sec_raw = (
                section.get("masterConfig")
                if isinstance(section.get("masterConfig"), dict)
                else {}
            )
            sec_master = self._comunicado.enrich_master_config(
                sec_raw,
                api_root_path=settings.TV_DASHBOARD_API_ROOT_PATH,
                playlist_id=playlist_id,
                public_token=public_token,
            )
            section_master_by_id[section["id"]] = sec_master
            item = {
                "id": section["id"],
                "name": section["name"],
                "sortOrder": section["sortOrder"],
                "isActive": section.get("isActive", True),
                "isMain": bool(section.get("isMain")),
            }
            if section.get("defaultDurationSec") is not None:
                item["defaultDurationSec"] = section["defaultDurationSec"]
            if section.get("transitionStyle"):
                item["transitionStyle"] = section["transitionStyle"]
            if sec_master:
                item["masterConfig"] = sec_master
            rendered_sections.append(item)

        rendered_slides: list[dict[str, Any]] = []
        for slide in slides:
            section = section_by_id.get(slide.get("sectionId") or "")
            duration = resolve_slide_duration_sec(
                slide_duration=slide.get("durationSec"),
                section_default=section.get("defaultDurationSec") if section else None,
                playlist_default=default_duration,
            )
            transition = resolve_slide_transition_style(
                slide_transition=slide.get("transitionStyle"),
                section_transition=section.get("transitionStyle") if section else None,
                playlist_transition=playlist_transition,
            )
            effective_master = merge_master_configs(
                playlist_master,
                section_master_by_id.get(slide.get("sectionId") or "") if section else None,
            )
            item: dict[str, Any] = {
                "id": slide["id"],
                "sortOrder": slide["sortOrder"],
                "slideType": slide["slideType"],
                "durationSec": duration,
                "title": slide["title"],
            }
            if slide.get("sectionId"):
                item["sectionId"] = slide["sectionId"]
            if transition:
                item["transitionStyle"] = transition
            if slide["slideType"] == "native":
                item["native"] = {
                    "screenKey": slide["nativeScreenKey"],
                    "config": slide.get("nativeConfig") or {},
                    "data": self._native_data.resolve(
                        screen_key=str(slide["nativeScreenKey"]),
                        config=slide.get("nativeConfig") or {},
                        authorization=authorization,
                        playlist_id=playlist_id,
                        public_token=public_token,
                        user=user,
                        playlist_defaults=playlist_defaults,
                        filter_overrides=safe_overrides,
                    ),
                }
            else:
                item["external"] = {
                    "url": slide["externalUrl"],
                    "sandbox": slide.get("externalSandbox"),
                }
            if effective_master:
                native = item.get("native")
                if isinstance(native, dict) and native.get("screenKey") == "custom_message":
                    data = native.get("data")
                    if isinstance(data, dict):
                        native["data"] = {**data, "master": effective_master}
            rendered_slides.append(item)

        return {
            "playlist": {
                "id": playlist["id"],
                "name": playlist["name"],
                "description": playlist.get("description"),
                "viewportProfile": playlist.get("viewportProfile") or "1080p",
                "viewportWidth": playlist.get("viewportWidth"),
                "viewportHeight": playlist.get("viewportHeight"),
                "transitionStyle": playlist_transition,
                "globalRefreshSec": playlist.get("globalRefreshSec") or 300,
                "defaultDurationSec": default_duration,
                "playbackMode": playlist.get("playbackMode") or "presentation",
                "publicToken": playlist["publicToken"],
                "publicUrl": self.build_public_url(playlist["publicToken"]),
                **({"masterConfig": playlist_master} if playlist_master else {}),
            },
            "presentationMeta": {
                "nativeErrorAdvanceSec": presentation_setting_int("nativeErrorAdvanceSec", 10),
                "heartbeatIntervalSec": heartbeat_interval_sec(),
            },
            "sections": rendered_sections,
            "slides": rendered_slides,
        }
