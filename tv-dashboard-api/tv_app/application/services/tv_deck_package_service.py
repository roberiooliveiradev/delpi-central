"""Exportação e importação do pacote portátil MDD (Minha Delpi Deck, `.mdd`)."""

from __future__ import annotations

import hashlib
import io
import json
import secrets
import threading
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from tv_app.application.services.media_storage_service import MediaStorageService
from tv_app.application.services.tv_deck_asset_collector import (
    collect_asset_ids,
    collect_data_bindings,
    rewrite_asset_ids,
)
from tv_app.application.services.tv_deck_binding_validator import TvDeckBindingValidator
from tv_app.config import settings
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistNotFoundError,
    PlaylistRepository,
)

PACKAGE_FORMAT = "minha_delpi_deck"
PACKAGE_FORMAT_ALIASES = frozenset({PACKAGE_FORMAT, "delpi_tv_deck", "mdd"})
PACKAGE_EXTENSION = ".mdd"
SCHEMA_VERSION = "1.0"
MANIFEST_FILENAME = "manifest.json"
PLAYLIST_PATH = "deck/playlist.json"
SECTIONS_PATH = "deck/sections.json"
SLIDES_PATH = "deck/slides.json"
MEDIA_INDEX_PATH = "deck/media.json"
BINDINGS_INDEX_PATH = "deck/data_bindings_index.json"
MEDIA_PREFIX = "media/"

BindingPolicy = Literal["lenient", "strict"]


def _sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _is_safe_archive_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip()
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        return False
    if normalized == MANIFEST_FILENAME:
        return True
    if normalized in {
        PLAYLIST_PATH,
        SECTIONS_PATH,
        SLIDES_PATH,
        MEDIA_INDEX_PATH,
        BINDINGS_INDEX_PATH,
    }:
        return True
    if normalized.startswith(MEDIA_PREFIX):
        parts = normalized.split("/")
        return len(parts) == 2 and bool(parts[1]) and "/" not in parts[1]
    return False


def _ext_from_stored_name(stored_name: str, mime_type: str | None) -> str:
    name = (stored_name or "").strip()
    suffix = Path(name).suffix
    if suffix:
        return suffix.lower()
    mime = (mime_type or "").split(";", 1)[0].strip().lower()
    fallback = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "font/woff2": ".woff2",
        "font/ttf": ".ttf",
        "font/otf": ".otf",
    }
    return fallback.get(mime, ".bin")


class TvDeckPackageError(ValueError):
    """Pacote inválido ou operação de import/export falhou."""


class _PreviewStore:
    """Cache em memória de preview → bytes do ZIP (TTL curto)."""

    def __init__(self, ttl_seconds: int = 900) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._items: dict[str, tuple[float, bytes, dict[str, Any]]] = {}

    def put(self, raw: bytes, summary: dict[str, Any]) -> str:
        token = secrets.token_urlsafe(24)
        with self._lock:
            self._purge_locked()
            self._items[token] = (time.monotonic() + self._ttl, raw, summary)
        return token

    def get(self, token: str) -> tuple[bytes, dict[str, Any]] | None:
        with self._lock:
            self._purge_locked()
            item = self._items.get(token)
            if not item:
                return None
            expires, raw, summary = item
            if expires < time.monotonic():
                self._items.pop(token, None)
                return None
            return raw, summary

    def pop(self, token: str) -> tuple[bytes, dict[str, Any]] | None:
        with self._lock:
            self._purge_locked()
            item = self._items.pop(token, None)
            if not item:
                return None
            expires, raw, summary = item
            if expires < time.monotonic():
                return None
            return raw, summary

    def _purge_locked(self) -> None:
        now = time.monotonic()
        expired = [key for key, (exp, _, _) in self._items.items() if exp < now]
        for key in expired:
            self._items.pop(key, None)


_PREVIEW_STORE = _PreviewStore()


class TvDeckPackageService:
    def __init__(
        self,
        *,
        playlist_repo: PlaylistRepository | None = None,
        media_repo: MediaRepository | None = None,
        media_storage: MediaStorageService | None = None,
        binding_validator: TvDeckBindingValidator | None = None,
        max_bytes: int | None = None,
        preview_store: _PreviewStore | None = None,
    ) -> None:
        self._playlists = playlist_repo or PlaylistRepository()
        self._media = media_repo or MediaRepository()
        self._storage = media_storage or MediaStorageService()
        self._bindings = binding_validator or TvDeckBindingValidator()
        self._max_bytes = int(
            max_bytes
            if max_bytes is not None
            else getattr(settings, "TV_DECK_PACKAGE_MAX_BYTES", 500 * 1024 * 1024)
        )
        self._previews = preview_store or _PREVIEW_STORE

    def export_package(
        self,
        playlist_id: UUID,
        *,
        exported_by: str | None = None,
    ) -> tuple[bytes, str]:
        playlist = self._playlists.get_by_id(playlist_id)
        if not playlist:
            raise PlaylistNotFoundError
        slides = self._playlists.list_slides(playlist_id)
        sections = self._playlists.list_sections(playlist_id)
        assets = self._media.list_for_playlist(playlist_id)
        assets_by_id = {str(a["id"]): a for a in assets}

        playlist_payload = {
            "sourceId": playlist["id"],
            "name": playlist["name"],
            "description": playlist.get("description"),
            "viewportProfile": playlist["viewportProfile"],
            "transitionStyle": playlist["transitionStyle"],
            "defaultDurationSec": playlist["defaultDurationSec"],
            "globalRefreshSec": playlist["globalRefreshSec"],
            "dataDefaults": playlist.get("dataDefaults") or {},
            "masterConfig": playlist.get("masterConfig") or {},
        }
        sections_payload = [
            {
                "sourceId": section["id"],
                "name": section["name"],
                "sortOrder": section["sortOrder"],
                "isCollapsed": bool(section.get("isCollapsed")),
                "isActive": bool(section.get("isActive", True)),
                "isMain": bool(section.get("isMain")),
                "defaultDurationSec": section.get("defaultDurationSec"),
                "transitionStyle": section.get("transitionStyle"),
                "masterConfig": section.get("masterConfig") or {},
            }
            for section in sections
        ]
        slides_payload = [
            {
                "sourceId": slide["id"],
                "sourceSectionId": slide.get("sectionId"),
                "sortOrder": slide["sortOrder"],
                "slideType": slide["slideType"],
                "durationSec": slide.get("durationSec"),
                "title": slide["title"],
                "nativeScreenKey": slide.get("nativeScreenKey"),
                "nativeConfig": slide.get("nativeConfig") or {},
                "externalUrl": slide.get("externalUrl"),
                "externalSandbox": slide.get("externalSandbox"),
                "isActive": bool(slide.get("isActive", True)),
                "transitionStyle": slide.get("transitionStyle"),
            }
            for slide in slides
        ]

        referenced_ids = collect_asset_ids(
            playlist_payload.get("masterConfig"),
            *[s.get("masterConfig") for s in sections_payload],
            *[s.get("nativeConfig") for s in slides_payload],
        )
        missing: list[str] = []
        media_index: list[dict[str, Any]] = []
        media_files: dict[str, bytes] = {}

        for asset_id in sorted(referenced_ids):
            asset = assets_by_id.get(asset_id)
            if not asset:
                missing.append(asset_id)
                continue
            content = self._storage.read(str(asset["storedName"]))
            if content is None:
                missing.append(asset_id)
                continue
            ext = _ext_from_stored_name(str(asset["storedName"]), asset.get("mimeType"))
            archive_path = f"{MEDIA_PREFIX}{asset_id}{ext}"
            media_files[archive_path] = content
            media_index.append(
                {
                    "sourceAssetId": asset_id,
                    "originalName": asset.get("originalName"),
                    "mimeType": asset.get("mimeType"),
                    "mediaKind": asset.get("mediaKind"),
                    "archivePath": archive_path,
                    "fileSizeBytes": len(content),
                }
            )

        if missing:
            preview = "; ".join(missing[:8])
            extra = f" (+{len(missing) - 8} outras)" if len(missing) > 8 else ""
            raise TvDeckPackageError(
                "Exportação incompleta: mídias referenciadas ausentes no volume "
                f"({len(missing)}). Ausentes: {preview}{extra}"
            )

        bindings_index = collect_data_bindings(slides_payload)

        entries: dict[str, dict[str, Any]] = {}
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            deck_files = {
                PLAYLIST_PATH: _json_bytes(playlist_payload),
                SECTIONS_PATH: _json_bytes(sections_payload),
                SLIDES_PATH: _json_bytes(slides_payload),
                MEDIA_INDEX_PATH: _json_bytes(media_index),
                BINDINGS_INDEX_PATH: _json_bytes(bindings_index),
            }
            for path, content in deck_files.items():
                archive.writestr(path, content)
                entries[path] = {
                    "sha256": _sha256_hex(content),
                    "size_bytes": len(content),
                }
            for path, content in media_files.items():
                archive.writestr(path, content)
                entries[path] = {
                    "sha256": _sha256_hex(content),
                    "size_bytes": len(content),
                }

            manifest = {
                "format": PACKAGE_FORMAT,
                "schemaVersion": SCHEMA_VERSION,
                "source": {
                    "playlistId": playlist["id"],
                    "playlistName": playlist["name"],
                    "exportedBy": exported_by,
                    "exportedAt": datetime.now(timezone.utc).isoformat(),
                },
                "entries": entries,
                "stats": {
                    "slideCount": len(slides_payload),
                    "sectionCount": len(sections_payload),
                    "mediaCount": len(media_index),
                    "bindingCount": len(bindings_index),
                },
            }
            archive.writestr(MANIFEST_FILENAME, _json_bytes(manifest))

        payload = buffer.getvalue()
        if len(payload) > self._max_bytes:
            raise TvDeckPackageError(
                f"Pacote excede o limite de {self._max_bytes // (1024 * 1024)} MB."
            )
        safe_name = "".join(
            ch if ch.isalnum() or ch in {"-", "_"} else "-"
            for ch in str(playlist["name"]).strip()
        ).strip("-") or "programacao"
        filename = f"{safe_name}{PACKAGE_EXTENSION}"
        return payload, filename

    def parse_package(self, raw: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
        if len(raw) > self._max_bytes:
            raise TvDeckPackageError(
                f"Pacote excede o limite de {self._max_bytes // (1024 * 1024)} MB."
            )
        files: dict[str, bytes] = {}
        try:
            with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    name = info.filename.replace("\\", "/").strip()
                    if not _is_safe_archive_path(name):
                        raise TvDeckPackageError(f"Caminho inválido no pacote: {name}")
                    files[name] = archive.read(info)
        except zipfile.BadZipFile as exc:
            raise TvDeckPackageError("Arquivo ZIP inválido.") from exc

        manifest_raw = files.get(MANIFEST_FILENAME)
        if not manifest_raw:
            raise TvDeckPackageError("Pacote sem manifest.json.")
        try:
            manifest = json.loads(manifest_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TvDeckPackageError("manifest.json inválido.") from exc
        if not isinstance(manifest, dict):
            raise TvDeckPackageError("manifest.json inválido.")
        if str(manifest.get("format") or "").strip() not in PACKAGE_FORMAT_ALIASES:
            raise TvDeckPackageError("Formato de pacote não reconhecido (esperado MDD / minha_delpi_deck).")
        schema = str(manifest.get("schemaVersion") or "").strip()
        if schema.split(".")[0] != "1":
            raise TvDeckPackageError(f"schemaVersion não suportada: {schema or '?'}.")
        return manifest, files

    def validate_package_integrity(
        self,
        manifest: dict[str, Any],
        files: dict[str, bytes],
    ) -> list[str]:
        errors: list[str] = []
        entries = manifest.get("entries") or {}
        if not isinstance(entries, dict):
            return ["Manifesto inválido: entries ausente."]

        for path, meta in entries.items():
            if not isinstance(meta, dict):
                errors.append(f"Entrada inválida no manifesto: {path}.")
                continue
            expected = meta.get("sha256")
            content = files.get(path)
            if content is None:
                errors.append(f"Arquivo ausente no pacote: {path}.")
                continue
            if expected and _sha256_hex(content) != expected:
                errors.append(f"Checksum inválido: {path}.")

        for required in (PLAYLIST_PATH, SECTIONS_PATH, SLIDES_PATH, MEDIA_INDEX_PATH):
            if required not in files:
                errors.append(f"Arquivo obrigatório ausente: {required}.")

        for path in files:
            if path == MANIFEST_FILENAME:
                continue
            if path.startswith(MEDIA_PREFIX) and path not in entries:
                errors.append(f"Mídia não listada no manifesto: {path}.")
        return errors

    def _load_deck_json(
        self,
        files: dict[str, bytes],
        path: str,
        *,
        expect_list: bool = False,
    ) -> Any:
        raw = files.get(path)
        if raw is None:
            raise TvDeckPackageError(f"Arquivo ausente: {path}.")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TvDeckPackageError(f"JSON inválido: {path}.") from exc
        if expect_list and not isinstance(payload, list):
            raise TvDeckPackageError(f"Esperado array em {path}.")
        if not expect_list and not isinstance(payload, dict):
            raise TvDeckPackageError(f"Esperado objeto em {path}.")
        return payload

    def preview_import(self, raw: bytes) -> dict[str, Any]:
        try:
            manifest, files = self.parse_package(raw)
        except TvDeckPackageError as exc:
            return {
                "valid": False,
                "errors": [str(exc)],
                "format": PACKAGE_FORMAT,
                "schemaVersion": SCHEMA_VERSION,
            }

        integrity = self.validate_package_integrity(manifest, files)
        if integrity:
            return {
                "valid": False,
                "errors": integrity,
                "format": PACKAGE_FORMAT,
                "schemaVersion": str(manifest.get("schemaVersion") or SCHEMA_VERSION),
                "source": manifest.get("source"),
                "stats": manifest.get("stats"),
            }

        try:
            playlist = self._load_deck_json(files, PLAYLIST_PATH)
            sections = self._load_deck_json(files, SECTIONS_PATH, expect_list=True)
            slides = self._load_deck_json(files, SLIDES_PATH, expect_list=True)
            media_index = self._load_deck_json(files, MEDIA_INDEX_PATH, expect_list=True)
            bindings_raw = files.get(BINDINGS_INDEX_PATH)
            if bindings_raw is not None:
                try:
                    bindings = json.loads(bindings_raw.decode("utf-8"))
                    if not isinstance(bindings, list):
                        bindings = collect_data_bindings(slides)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    bindings = collect_data_bindings(slides)
            else:
                bindings = collect_data_bindings(slides)
        except TvDeckPackageError as exc:
            return {
                "valid": False,
                "errors": [str(exc)],
                "format": PACKAGE_FORMAT,
                "schemaVersion": str(manifest.get("schemaVersion") or SCHEMA_VERSION),
            }

        media_errors: list[str] = []
        for row in media_index:
            if not isinstance(row, dict):
                media_errors.append("Entrada inválida em deck/media.json.")
                continue
            archive_path = str(row.get("archivePath") or "").strip()
            if not archive_path or archive_path not in files:
                media_errors.append(
                    f"Mídia sem arquivo no pacote: {row.get('sourceAssetId') or archive_path}."
                )

        binding_reports = self._bindings.validate_index(
            [b for b in bindings if isinstance(b, dict)]
        )
        warnings = [
            r["message"]
            for r in binding_reports
            if r.get("status") == "warning" and r.get("message")
        ]
        errors = list(media_errors)
        errors.extend(
            r["message"]
            for r in binding_reports
            if r.get("status") == "error" and r.get("message")
        )

        summary = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "format": PACKAGE_FORMAT,
            "schemaVersion": str(manifest.get("schemaVersion") or SCHEMA_VERSION),
            "source": manifest.get("source"),
            "stats": {
                "slideCount": len(slides),
                "sectionCount": len(sections),
                "mediaCount": len(media_index),
                "bindingCount": len(bindings),
            },
            "playlistName": str(playlist.get("name") or "").strip() or "Programação importada",
            "slides": [
                {
                    "sourceId": s.get("sourceId"),
                    "title": s.get("title"),
                    "slideType": s.get("slideType"),
                    "sortOrder": s.get("sortOrder"),
                }
                for s in slides
                if isinstance(s, dict)
            ],
            "sections": [
                {
                    "sourceId": s.get("sourceId"),
                    "name": s.get("name"),
                    "isMain": bool(s.get("isMain")),
                    "sortOrder": s.get("sortOrder"),
                }
                for s in sections
                if isinstance(s, dict)
            ],
            "bindings": binding_reports,
        }
        if summary["valid"]:
            summary["importToken"] = self._previews.put(raw, summary)
        return summary

    def apply_import(
        self,
        *,
        import_token: str | None = None,
        raw: bytes | None = None,
        created_by: str,
        name_override: str | None = None,
        activate_after_import: bool = False,
        binding_policy: BindingPolicy = "lenient",
    ) -> dict[str, Any]:
        package_bytes: bytes | None = raw
        preview_summary: dict[str, Any] | None = None
        if import_token:
            stored = self._previews.pop(import_token)
            if not stored:
                raise TvDeckPackageError(
                    "Token de importação inválido ou expirado. Gere um novo preview."
                )
            package_bytes, preview_summary = stored
        if package_bytes is None:
            raise TvDeckPackageError("Informe importToken ou o arquivo do pacote.")

        preview = preview_summary or self.preview_import(package_bytes)
        if not preview.get("valid"):
            raise TvDeckPackageError(
                "; ".join(preview.get("errors") or ["Pacote inválido."])
            )
        if self._bindings.has_blocking_errors(
            preview.get("bindings") or [],
            binding_policy=binding_policy,
        ):
            raise TvDeckPackageError(
                "Há bindings incompatíveis e a política strict está ativa."
            )

        manifest, files = self.parse_package(package_bytes)
        integrity = self.validate_package_integrity(manifest, files)
        if integrity:
            raise TvDeckPackageError("; ".join(integrity))

        playlist_payload = self._load_deck_json(files, PLAYLIST_PATH)
        sections_payload = self._load_deck_json(files, SECTIONS_PATH, expect_list=True)
        slides_payload = self._load_deck_json(files, SLIDES_PATH, expect_list=True)
        media_index = self._load_deck_json(files, MEDIA_INDEX_PATH, expect_list=True)

        name = (name_override or str(playlist_payload.get("name") or "")).strip()
        if not name:
            name = "Programação importada"

        # 1) Criar playlist base
        created = self._playlists.create(
            name=name,
            description=playlist_payload.get("description"),
            created_by=created_by,
        )
        new_playlist_id = UUID(created["id"])

        # 2) Importar mídias e montar mapa de assetId
        asset_id_map: dict[str, str] = {}
        for row in media_index:
            if not isinstance(row, dict):
                continue
            source_id = str(row.get("sourceAssetId") or "").strip()
            archive_path = str(row.get("archivePath") or "").strip()
            if not source_id or not archive_path:
                continue
            content = files.get(archive_path)
            if content is None:
                raise TvDeckPackageError(f"Mídia ausente no pacote: {archive_path}.")
            mime = str(row.get("mimeType") or "application/octet-stream")
            stored_name, normalized_mime, kind = self._storage.save(
                content=content,
                mime_type=mime,
            )
            asset = self._media.create(
                playlist_id=new_playlist_id,
                stored_name=stored_name,
                original_name=row.get("originalName"),
                mime_type=normalized_mime,
                media_kind=str(row.get("mediaKind") or kind),
                file_size_bytes=len(content),
                created_by=created_by,
            )
            asset_id_map[source_id] = str(asset["id"])

        remapped_master = rewrite_asset_ids(
            playlist_payload.get("masterConfig") or {},
            asset_id_map,
        )
        remapped_defaults = playlist_payload.get("dataDefaults") or {}

        updated = self._playlists.update(
            new_playlist_id,
            actor_user_id=created_by,
            reason="playlist_imported",
            viewport_profile=playlist_payload.get("viewportProfile"),
            transition_style=playlist_payload.get("transitionStyle"),
            default_duration_sec=playlist_payload.get("defaultDurationSec"),
            global_refresh_sec=playlist_payload.get("globalRefreshSec"),
            data_defaults=remapped_defaults if isinstance(remapped_defaults, dict) else {},
            master_config=remapped_master if isinstance(remapped_master, dict) else {},
        )

        # 3) Seções (bulk via repositório dedicado)
        section_id_map = self._playlists.import_sections_from_deck(
            new_playlist_id,
            [
                {
                    **section,
                    "masterConfig": rewrite_asset_ids(
                        section.get("masterConfig") or {},
                        asset_id_map,
                    ),
                }
                for section in sections_payload
                if isinstance(section, dict)
            ],
            actor_user_id=created_by,
        )

        # 4) Slides
        remapped_slides: list[dict[str, Any]] = []
        for slide in slides_payload:
            if not isinstance(slide, dict):
                continue
            source_section = slide.get("sourceSectionId")
            mapped_section = (
                section_id_map.get(str(source_section)) if source_section else None
            )
            remapped_slides.append(
                {
                    "slideType": slide.get("slideType") or "native",
                    "title": slide.get("title") or "Tela",
                    "durationSec": slide.get("durationSec"),
                    "sortOrder": slide.get("sortOrder"),
                    "nativeScreenKey": slide.get("nativeScreenKey"),
                    "nativeConfig": rewrite_asset_ids(
                        slide.get("nativeConfig") or {},
                        asset_id_map,
                    ),
                    "externalUrl": slide.get("externalUrl"),
                    "externalSandbox": slide.get("externalSandbox"),
                    "isActive": bool(slide.get("isActive", True)),
                    "transitionStyle": slide.get("transitionStyle"),
                    "sectionId": mapped_section,
                }
            )
        self._playlists.import_slides_from_deck(
            new_playlist_id,
            remapped_slides,
            actor_user_id=created_by,
        )

        if activate_after_import:
            updated = self._playlists.set_active(
                new_playlist_id,
                is_active=True,
                actor_user_id=created_by,
                reason="playlist_imported_activated",
            )

        result = dict(updated)
        result["slides"] = self._playlists.list_slides(new_playlist_id)
        result["sections"] = self._playlists.list_sections(new_playlist_id)
        result["accessRole"] = "owner"
        result["importStats"] = {
            "mediaRemapped": len(asset_id_map),
            "sectionRemapped": len(section_id_map),
            "slideCount": len(remapped_slides),
            "bindingWarnings": len(preview.get("warnings") or []),
        }
        return result
