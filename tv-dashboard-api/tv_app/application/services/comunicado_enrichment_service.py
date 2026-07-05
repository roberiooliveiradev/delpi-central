from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository


class ComunicadoEnrichmentService:
    """Resolve blocos de comunicado e URLs de mídia para apresentação."""

    def __init__(self, media_repo: MediaRepository | None = None) -> None:
        self._media_repo = media_repo or MediaRepository()

    @staticmethod
    def build_media_url(
        *,
        api_root_path: str,
        playlist_id: str,
        asset_id: str,
        public_token: str | None = None,
    ) -> str:
        root = api_root_path.rstrip("/")
        if public_token:
            return f"{root}/public/present/{public_token}/media/{asset_id}"
        return f"{root}/playlists/{playlist_id}/media/{asset_id}"

    def enrich(
        self,
        cfg: dict[str, Any],
        *,
        api_root_path: str,
        playlist_id: str,
        public_token: str | None = None,
    ) -> dict[str, Any]:
        blocks_raw = cfg.get("blocks")
        if not isinstance(blocks_raw, list) or not blocks_raw:
            return {
                "headline": str(cfg.get("headline") or message("comunicadoDefaultHeadline", "Comunicado")),
                "subtitle": str(cfg.get("subtitle") or ""),
            }

        background = self._enrich_background(
            cfg.get("background"),
            api_root_path=api_root_path,
            playlist_id=playlist_id,
            public_token=public_token,
        )
        blocks = [
            self._enrich_block(
                block,
                api_root_path=api_root_path,
                playlist_id=playlist_id,
                public_token=public_token,
            )
            for block in blocks_raw
            if isinstance(block, dict)
        ]
        headline = str(cfg.get("headline") or self._headline_from_blocks(blocks_raw) or "Comunicado")
        subtitle = str(cfg.get("subtitle") or "")
        return {
            "version": 2,
            "headline": headline,
            "subtitle": subtitle,
            "background": background,
            "blocks": blocks,
        }

    def _headline_from_blocks(self, blocks: list[Any]) -> str:
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "heading":
                content = block.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
        return ""

    def _enrich_background(
        self,
        background: Any,
        *,
        api_root_path: str,
        playlist_id: str,
        public_token: str | None,
    ) -> dict[str, Any]:
        if not isinstance(background, dict):
            return {"type": "color", "value": "#0f172a"}
        bg_type = str(background.get("type") or "color")
        if bg_type == "image":
            asset_id = background.get("assetId")
            if isinstance(asset_id, str) and asset_id.strip():
                url = self._resolve_asset_url(
                    asset_id.strip(),
                    api_root_path=api_root_path,
                    playlist_id=playlist_id,
                    public_token=public_token,
                )
                if url:
                    return {"type": "image", "url": url}
        value = background.get("value")
        if bg_type == "color" and isinstance(value, str) and value.strip():
            return {"type": "color", "value": value.strip()}
        return {"type": "color", "value": "#0f172a"}

    def _enrich_block(
        self,
        block: dict[str, Any],
        *,
        api_root_path: str,
        playlist_id: str,
        public_token: str | None,
    ) -> dict[str, Any]:
        block_type = str(block.get("type") or "text")
        enriched: dict[str, Any] = {
            "id": str(block.get("id") or ""),
            "type": block_type,
            "frame": self._normalize_frame(block.get("frame")),
            "style": block.get("style") if isinstance(block.get("style"), dict) else {},
        }
        if block_type in {"heading", "text"}:
            enriched["content"] = str(block.get("content") or "")
        elif block_type in {"image", "video"}:
            asset_id = block.get("assetId")
            if isinstance(asset_id, str) and asset_id.strip():
                url = self._resolve_asset_url(
                    asset_id.strip(),
                    api_root_path=api_root_path,
                    playlist_id=playlist_id,
                    public_token=public_token,
                )
                if url:
                    enriched["url"] = url
                enriched["assetId"] = asset_id.strip()
        return enriched

    def _resolve_asset_url(
        self,
        asset_id: str,
        *,
        api_root_path: str,
        playlist_id: str,
        public_token: str | None,
    ) -> str | None:
        try:
            parsed = UUID(asset_id)
        except ValueError:
            return None
        if public_token:
            asset = self._media_repo.get_for_token(public_token, parsed)
        else:
            asset = self._media_repo.get_for_playlist(UUID(playlist_id), parsed)
        if not asset:
            return None
        return self.build_media_url(
            api_root_path=api_root_path,
            playlist_id=playlist_id,
            asset_id=asset_id,
            public_token=public_token,
        )

    @staticmethod
    def _normalize_frame(frame: Any) -> dict[str, float]:
        if not isinstance(frame, dict):
            return {"x": 5, "y": 10, "w": 90, "h": 20}
        def _num(key: str, default: float) -> float:
            try:
                return float(frame.get(key, default))
            except (TypeError, ValueError):
                return default
        return {
            "x": max(0, min(100, _num("x", 5))),
            "y": max(0, min(100, _num("y", 10))),
            "w": max(5, min(100, _num("w", 90))),
            "h": max(5, min(100, _num("h", 20))),
        }
