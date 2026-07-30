"""Clona mídias (imagem/vídeo/fonte) ao duplicar uma programação."""

from __future__ import annotations

from uuid import UUID

from tv_app.application.services.media_storage_service import MediaStorageService
from tv_app.application.services.tv_deck_asset_collector import rewrite_asset_ids
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistNotFoundError,
    PlaylistRepository,
)


class PlaylistMediaCloneService:
    """Copia arquivos + `media_assets` e remapeia `assetId` na programação destino."""

    def __init__(
        self,
        *,
        media: MediaRepository | None = None,
        storage: MediaStorageService | None = None,
        playlists: PlaylistRepository | None = None,
    ) -> None:
        self._media = media or MediaRepository()
        self._storage = storage or MediaStorageService()
        self._playlists = playlists or PlaylistRepository()

    def clone_media_and_remap(
        self,
        *,
        source_playlist_id: UUID,
        target_playlist_id: UUID,
        created_by: str | None,
    ) -> dict[str, str]:
        """
        Copia todas as mídias da origem para o destino e reescreve assetId
        em masterConfig / seções / slides da cópia.
        Retorna mapa sourceAssetId → targetAssetId.
        """
        id_map = self._copy_assets(
            source_playlist_id=source_playlist_id,
            target_playlist_id=target_playlist_id,
            created_by=created_by,
        )
        if not id_map:
            return id_map

        target = self._playlists.get_by_id(target_playlist_id)
        if not target:
            raise PlaylistNotFoundError

        sections = self._playlists.list_sections(target_playlist_id)
        slides = self._playlists.list_slides(target_playlist_id)
        self._playlists.bulk_replace_asset_configs(
            target_playlist_id,
            master_config=rewrite_asset_ids(target.get("masterConfig") or {}, id_map),
            section_master_configs={
                str(section["id"]): rewrite_asset_ids(section.get("masterConfig") or {}, id_map)
                for section in sections
            },
            slide_native_configs={
                str(slide["id"]): rewrite_asset_ids(slide.get("nativeConfig") or {}, id_map)
                for slide in slides
            },
        )
        return id_map

    def _copy_assets(
        self,
        *,
        source_playlist_id: UUID,
        target_playlist_id: UUID,
        created_by: str | None,
    ) -> dict[str, str]:
        id_map: dict[str, str] = {}
        for asset in self._media.list_for_playlist(source_playlist_id):
            source_id = str(asset.get("id") or "").strip()
            stored_name = str(asset.get("storedName") or "").strip()
            if not source_id or not stored_name:
                continue
            content = self._storage.read(stored_name)
            if content is None:
                continue
            mime = str(asset.get("mimeType") or "application/octet-stream")
            new_stored, normalized_mime, kind = self._storage.save(
                content=content,
                mime_type=mime,
            )
            created = self._media.create(
                playlist_id=target_playlist_id,
                stored_name=new_stored,
                original_name=asset.get("originalName"),
                mime_type=normalized_mime,
                media_kind=str(asset.get("mediaKind") or kind),
                file_size_bytes=len(content),
                created_by=created_by,
            )
            id_map[source_id] = str(created["id"])
        return id_map
