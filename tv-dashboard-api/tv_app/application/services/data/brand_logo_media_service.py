"""Ensure Delpi brand logo PNGs exist as playlist media assets (ASSET_ID_ONLY)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from tv_app.application.services.media_storage_service import MediaStorageService
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository

BRAND_LOGO_ROLE = "brandLogo"

# Stable originalName markers — VISTA / digest match without inventing assetId.
ORIGINAL_NAME_ON_DARK = "delpi-brand-logo-onDark.png"
ORIGINAL_NAME_ON_LIGHT = "delpi-brand-logo-onLight.png"

_VARIANT_FILES = {
    "onDark": ("logoDelpiOnDark.png", ORIGINAL_NAME_ON_DARK),
    "onLight": ("logoDelpiOnLight.png", ORIGINAL_NAME_ON_LIGHT),
}

# Frame % aligned with plugins/.../delpiBrandTheme.json logo (bottom-right).
BRAND_LOGO_FRAME = {"x": 86.0, "y": 90.0, "w": 11.0, "h": 7.0}


def brand_logo_packaged_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "content" / "brand"


class BrandLogoMediaService:
    """Seeds packaged Delpi logos into playlist media; idempotent by originalName."""

    def __init__(
        self,
        *,
        media_repo: MediaRepository | None = None,
        storage: MediaStorageService | None = None,
    ) -> None:
        self._repo = media_repo or MediaRepository()
        self._storage = storage or MediaStorageService()

    def list_brand_assets(self, playlist_id: str | UUID) -> dict[str, dict[str, Any]]:
        """Return {onDark|onLight: asset} for known brand logos already in the library."""
        pid = UUID(str(playlist_id))
        found: dict[str, dict[str, Any]] = {}
        for asset in self._repo.list_for_playlist(pid, media_kind="image"):
            name = str(asset.get("originalName") or "")
            if name == ORIGINAL_NAME_ON_DARK:
                found["onDark"] = asset
            elif name == ORIGINAL_NAME_ON_LIGHT:
                found["onLight"] = asset
        return found

    def ensure_playlist_assets(
        self,
        playlist_id: str | UUID,
        *,
        created_by: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Ensure both variants exist; create missing from packaged PNGs."""
        pid = UUID(str(playlist_id))
        existing = self.list_brand_assets(pid)
        out = dict(existing)
        pack = brand_logo_packaged_dir()
        for variant, (filename, original_name) in _VARIANT_FILES.items():
            if variant in out:
                continue
            source = pack / filename
            if not source.is_file():
                raise FileNotFoundError(f"Packaged brand logo missing: {source}")
            content = source.read_bytes()
            stored_name, mime, kind = self._storage.save(
                content=content,
                mime_type="image/png",
            )
            asset = self._repo.create(
                playlist_id=pid,
                stored_name=stored_name,
                original_name=original_name,
                mime_type=mime,
                media_kind=kind,
                file_size_bytes=len(content),
                created_by=created_by,
            )
            out[variant] = asset
        return out

    @staticmethod
    def resolve_variant_for_native(native_config: dict[str, Any] | None) -> str:
        """Pick onDark/onLight from brandThemeKey or background luminance heuristic."""
        cfg = native_config if isinstance(native_config, dict) else {}
        key = str(cfg.get("brandThemeKey") or "").strip()
        if key in ("delpi-dark", "delpi"):
            return "onDark"
        if key in ("delpi-light", "light"):
            return "onLight"
        bg = cfg.get("background") if isinstance(cfg.get("background"), dict) else {}
        bg_type = str(bg.get("type") or "")
        if bg_type == "gradient":
            # Delpi dark gradients are near-black blues.
            return "onDark"
        value = str(bg.get("value") or "").lower()
        if value in ("#ffffff", "#f8fafc", "#fff", "white"):
            return "onLight"
        # Default: dark TV / Delpi escuro family.
        return "onDark"

    @staticmethod
    def find_brand_logo_block(native_config: dict[str, Any] | None) -> dict[str, Any] | None:
        cfg = native_config if isinstance(native_config, dict) else {}
        blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if str(block.get("type") or "") != "image":
                continue
            if str(block.get("role") or "") == BRAND_LOGO_ROLE:
                return block
            if str(block.get("brandLogoVariant") or "") in ("onDark", "onLight"):
                return block
        return None

    @staticmethod
    def theme_provides_logo(native_config: dict[str, Any] | None) -> bool:
        key = str((native_config or {}).get("brandThemeKey") or "").strip()
        return key in ("delpi-dark", "delpi-light", "delpi", "light")

    def brand_logo_presence(self, native_config: dict[str, Any] | None) -> dict[str, Any]:
        if self.theme_provides_logo(native_config):
            return {
                "present": True,
                "source": "theme",
                "brandThemeKey": str((native_config or {}).get("brandThemeKey") or ""),
            }
        block = self.find_brand_logo_block(native_config)
        if block:
            return {
                "present": True,
                "source": "block",
                "blockId": str(block.get("id") or ""),
                "assetId": str(block.get("assetId") or "") or None,
                "variant": str(block.get("brandLogoVariant") or "") or None,
            }
        return {"present": False, "source": "none"}
