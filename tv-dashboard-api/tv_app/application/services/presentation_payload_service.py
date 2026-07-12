from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.services.comunicado_enrichment_service import ComunicadoEnrichmentService
from tv_app.application.services.native_screen_data_service import NativeScreenDataService
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
        )

    def build_by_id(
        self,
        playlist_id: UUID,
        *,
        authorization: str | None = None,
        user: Any | None = None,
    ) -> dict[str, Any]:
        playlist = self._repo.get_by_id(playlist_id)
        if not playlist:
            raise PlaylistNotFoundError
        return self._assemble_payload(
            playlist,
            authorization=authorization,
            public_media_urls=False,
            user=user,
        )

    def _assemble_payload(
        self,
        playlist: dict[str, Any],
        *,
        authorization: str | None,
        public_media_urls: bool = False,
        user: Any | None = None,
    ) -> dict[str, Any]:
        slides = [
            slide
            for slide in self._repo.list_slides(UUID(playlist["id"]))
            if slide.get("isActive", True)
        ]
        default_duration = playlist.get("defaultDurationSec") or 30
        playlist_id = str(playlist["id"])
        public_token = str(playlist["publicToken"]) if public_media_urls else None
        playlist_defaults = playlist.get("dataDefaults") if isinstance(playlist.get("dataDefaults"), dict) else {}
        rendered_slides: list[dict[str, Any]] = []
        for slide in slides:
            duration = slide.get("durationSec") or default_duration
            item: dict[str, Any] = {
                "id": slide["id"],
                "sortOrder": slide["sortOrder"],
                "slideType": slide["slideType"],
                "durationSec": duration,
                "title": slide["title"],
            }
            if slide.get("transitionStyle"):
                item["transitionStyle"] = slide["transitionStyle"]
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
                    ),
                }
            else:
                item["external"] = {
                    "url": slide["externalUrl"],
                    "sandbox": slide.get("externalSandbox"),
                }
            rendered_slides.append(item)

        master_raw = playlist.get("masterConfig") if isinstance(playlist.get("masterConfig"), dict) else {}
        master = self._comunicado.enrich_master_config(
            master_raw,
            api_root_path=settings.TV_DASHBOARD_API_ROOT_PATH,
            playlist_id=playlist_id,
            public_token=public_token,
        )

        if master:
            for item in rendered_slides:
                native = item.get("native")
                if not isinstance(native, dict):
                    continue
                if native.get("screenKey") != "custom_message":
                    continue
                data = native.get("data")
                if isinstance(data, dict):
                    native["data"] = {**data, "master": master}

        return {
            "playlist": {
                "id": playlist["id"],
                "name": playlist["name"],
                "description": playlist.get("description"),
                "viewportProfile": playlist.get("viewportProfile") or "1080p",
                "transitionStyle": playlist.get("transitionStyle") or "fade",
                "globalRefreshSec": playlist.get("globalRefreshSec") or 300,
                "defaultDurationSec": default_duration,
                "publicUrl": self.build_public_url(playlist["publicToken"]),
                **({"masterConfig": master} if master else {}),
            },
            "presentationMeta": {
                "nativeErrorAdvanceSec": presentation_setting_int("nativeErrorAdvanceSec", 10),
                "heartbeatIntervalSec": heartbeat_interval_sec(),
            },
            "slides": rendered_slides,
        }
