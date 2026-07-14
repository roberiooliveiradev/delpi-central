from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.services.comunicado_data_enrichment_service import ComunicadoDataEnrichmentService
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository


class ComunicadoEnrichmentService:
    """Resolve blocos de comunicado e URLs de mídia para apresentação."""

    def __init__(
        self,
        media_repo: MediaRepository | None = None,
        data_enrichment: ComunicadoDataEnrichmentService | None = None,
    ) -> None:
        self._media_repo = media_repo or MediaRepository()
        self._data_enrichment = data_enrichment or ComunicadoDataEnrichmentService()

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
        authorization: str | None = None,
        playlist_defaults: dict[str, Any] | None = None,
        user: Any | None = None,
        filter_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        custom_fonts = self._enrich_custom_fonts(
            cfg.get("customFonts"),
            api_root_path=api_root_path,
            playlist_id=playlist_id,
            public_token=public_token,
        )
        blocks_raw = cfg.get("blocks")
        # Sem chave `blocks` = legado headline/subtitle (tdp-message).
        # `blocks: []` = slide WYSIWYG em branco — manter layout rico (fundo branco).
        if not isinstance(blocks_raw, list):
            legacy_payload: dict[str, Any] = {
                "headline": str(cfg.get("headline") or message("comunicadoDefaultHeadline", "Comunicado")),
                "subtitle": str(cfg.get("subtitle") or ""),
            }
            if custom_fonts:
                legacy_payload["customFonts"] = custom_fonts
            return legacy_payload

        background = self._enrich_background(
            cfg.get("background"),
            api_root_path=api_root_path,
            playlist_id=playlist_id,
            public_token=public_token,
        )
        if len(blocks_raw) == 0:
            empty_payload: dict[str, Any] = {
                "version": int(cfg.get("version") or 2),
                "headline": str(cfg.get("headline") or ""),
                "subtitle": str(cfg.get("subtitle") or ""),
                "background": background,
                "blocks": [],
            }
            data_filters = cfg.get("dataFilters") if isinstance(cfg.get("dataFilters"), dict) else None
            if data_filters:
                empty_payload["dataFilters"] = data_filters
            if custom_fonts:
                empty_payload["customFonts"] = custom_fonts
            return empty_payload

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
        headline = str(
            cfg.get("headline")
            or self._headline_from_blocks(blocks_raw)
            or message("comunicadoDefaultHeadline", "Título")
        )
        subtitle = str(cfg.get("subtitle") or "")
        version = int(cfg.get("version") or 0) or self._detect_version(blocks)
        data_filters = cfg.get("dataFilters") if isinstance(cfg.get("dataFilters"), dict) else None
        blocks = self._data_enrichment.enrich_blocks(
            blocks,
            cfg=cfg,
            authorization=authorization,
            playlist_defaults=playlist_defaults,
            user=user,
            filter_overrides=filter_overrides,
        )
        payload: dict[str, Any] = {
            "version": version,
            "headline": headline,
            "subtitle": subtitle,
            "background": background,
            "blocks": blocks,
        }
        if data_filters:
            payload["dataFilters"] = data_filters
        if custom_fonts:
            payload["customFonts"] = custom_fonts
        return payload

    def _enrich_custom_fonts(
        self,
        fonts: Any,
        *,
        api_root_path: str,
        playlist_id: str,
        public_token: str | None,
    ) -> list[dict[str, str]]:
        if not isinstance(fonts, list):
            return []
        enriched: list[dict[str, str]] = []
        for font in fonts:
            if not isinstance(font, dict):
                continue
            asset_id = font.get("assetId")
            family_name = font.get("familyName")
            if not isinstance(asset_id, str) or not asset_id.strip():
                continue
            if not isinstance(family_name, str) or not family_name.strip():
                continue
            url = self._resolve_asset_url(
                asset_id.strip(),
                api_root_path=api_root_path,
                playlist_id=playlist_id,
                public_token=public_token,
            )
            if url:
                enriched.append(
                    {
                        "assetId": asset_id.strip(),
                        "familyName": family_name.strip(),
                        "url": url,
                    }
                )
        return enriched

    @staticmethod
    def _detect_version(blocks: list[dict[str, Any]]) -> int:
        for block in blocks:
            block_type = str(block.get("type") or "")
            if (
                block_type.startswith("data_")
                or block_type in {"chart_view", "table_view", "kpi_view"}
            ):
                return 4
        return 3 if blocks else 2

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
            return {"type": "color", "value": "#ffffff"}
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
        if bg_type == "gradient":
            from_color = background.get("from")
            to_color = background.get("to")
            if isinstance(from_color, str) and isinstance(to_color, str):
                angle = background.get("angle")
                payload: dict[str, Any] = {
                    "type": "gradient",
                    "from": from_color.strip() or "#ffffff",
                    "to": to_color.strip() or "#ffffff",
                }
                if isinstance(angle, (int, float)):
                    payload["angle"] = int(angle)
                return payload
        return {"type": "color", "value": "#ffffff"}

    def _enrich_block(
        self,
        block: dict[str, Any],
        *,
        api_root_path: str,
        playlist_id: str,
        public_token: str | None,
    ) -> dict[str, Any]:
        block_type = str(block.get("type") or "text")
        # Fonte + views: preservar config do editor (binding, chartType, parts…).
        # Strip aqui quebrava prévia admin e link público (tela branca / sem gráfico).
        if block_type in {"data_source", "chart_view", "table_view", "kpi_view"}:
            enriched = dict(block)
            enriched["id"] = str(block.get("id") or "")
            enriched["type"] = block_type
            enriched["frame"] = self._normalize_frame(block.get("frame"))
            if not isinstance(enriched.get("style"), dict):
                enriched["style"] = {}
            return enriched

        enriched: dict[str, Any] = {
            "id": str(block.get("id") or ""),
            "type": block_type,
            "frame": self._normalize_frame(block.get("frame")),
            "style": block.get("style") if isinstance(block.get("style"), dict) else {},
        }
        animations = block.get("animations")
        if isinstance(animations, dict):
            enriched["animations"] = animations
        if block_type in {"heading", "text"}:
            enriched["content"] = str(block.get("content") or "")
            href = block.get("href")
            if isinstance(href, str) and href.strip():
                enriched["href"] = href.strip()
            link_target = block.get("linkTarget")
            if link_target in {"_blank", "_self"}:
                enriched["linkTarget"] = link_target
            content_runs = block.get("contentRuns")
            if isinstance(content_runs, list):
                enriched["contentRuns"] = content_runs
        elif block_type == "shape":
            enriched["shape"] = str(block.get("shape") or "rectangle")
            content = block.get("content")
            if isinstance(content, str) and content.strip():
                enriched["content"] = content
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
        elif block_type == "icon":
            for key in ("iconName", "iconSet", "content", "href", "linkTarget"):
                value = block.get(key)
                if value is not None and value != "":
                    enriched[key] = value
        elif block_type in {"data_kpi", "data_chart", "data_table", "data_metric"}:
            binding = block.get("dataBinding")
            if isinstance(binding, dict):
                enriched["dataBinding"] = binding
            resolved = block.get("resolved")
            if isinstance(resolved, dict):
                enriched["resolved"] = resolved
        return enriched

    def enrich_master_config(
        self,
        master: dict[str, Any] | None,
        *,
        api_root_path: str,
        playlist_id: str,
        public_token: str | None = None,
    ) -> dict[str, Any] | None:
        """Resolve URLs de fundo/logo do master slide (4E.3)."""
        if not isinstance(master, dict) or not master.get("enabled"):
            return None
        out: dict[str, Any] = {"enabled": True}
        background = self._enrich_background(
            master.get("background"),
            api_root_path=api_root_path,
            playlist_id=playlist_id,
            public_token=public_token,
        )
        if background:
            out["background"] = background
        logo = master.get("logo")
        if isinstance(logo, dict):
            asset_id = logo.get("assetId")
            logo_out: dict[str, Any] = {}
            if isinstance(asset_id, str) and asset_id.strip():
                logo_out["assetId"] = asset_id.strip()
                url = self._resolve_asset_url(
                    asset_id.strip(),
                    api_root_path=api_root_path,
                    playlist_id=playlist_id,
                    public_token=public_token,
                )
                if url:
                    logo_out["url"] = url
            frame = logo.get("frame")
            if isinstance(frame, dict):
                logo_out["frame"] = frame
            opacity = logo.get("opacity")
            if isinstance(opacity, (int, float)):
                logo_out["opacity"] = max(0.0, min(1.0, float(opacity)))
            if logo_out:
                out["logo"] = logo_out
        return out

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
