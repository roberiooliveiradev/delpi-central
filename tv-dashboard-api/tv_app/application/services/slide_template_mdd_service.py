"""Pacote MDD de template de slide (1 slide custom_message) — pasta content/slide_templates/."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Constantes alinhadas a tv_deck_package_service (sem importar o serviço pesado).
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

SLIDE_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "content" / "slide_templates"
TEMPLATE_KIND = "slide_template"


class SlideTemplateMddError(ValueError):
    """Pacote MDD de template inválido."""


def _sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _collect_bindings_from_native_config(native_config: dict[str, Any]) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    blocks = native_config.get("blocks") if isinstance(native_config, dict) else None
    if not isinstance(blocks, list):
        return bindings
    for block in blocks:
        if not isinstance(block, dict):
            continue
        binding = block.get("dataBinding")
        if not isinstance(binding, dict):
            continue
        operation_id = str(binding.get("operationId") or "").strip()
        if not operation_id:
            continue
        bindings.append(
            {
                "blockId": block.get("id"),
                "blockType": block.get("type"),
                "operationId": operation_id,
                "params": binding.get("params") or {},
            }
        )
    return bindings


def build_slide_template_mdd(
    *,
    key: str,
    label: str,
    description: str | None,
    title: str,
    duration_sec: int | None,
    native_config: dict[str, Any],
    native_screen_key: str = "custom_message",
    exported_by: str | None = None,
) -> tuple[bytes, str]:
    """Monta ZIP `.mdd` mínimo (1 slide) com metadata de template no manifest."""
    section_id = "tmpl-section"
    slide_id = "tmpl-slide"
    playlist_payload = {
        "sourceId": "tmpl-playlist",
        "name": label,
        "description": description,
        "viewportProfile": "full_hd",
        "transitionStyle": "fade",
        "defaultDurationSec": duration_sec or 45,
        "globalRefreshSec": None,
        "dataDefaults": {},
        "masterConfig": {},
    }
    sections_payload = [
        {
            "sourceId": section_id,
            "name": "Principal",
            "sortOrder": 0,
            "isCollapsed": False,
            "isActive": True,
            "isMain": True,
            "defaultDurationSec": duration_sec,
            "transitionStyle": None,
            "masterConfig": {},
        }
    ]
    slides_payload = [
        {
            "sourceId": slide_id,
            "sourceSectionId": section_id,
            "sortOrder": 0,
            "slideType": "native",
            "durationSec": duration_sec,
            "title": title,
            "nativeScreenKey": native_screen_key,
            "nativeConfig": native_config,
            "externalUrl": None,
            "externalSandbox": None,
            "isActive": True,
            "transitionStyle": None,
        }
    ]
    media_index: list[dict[str, Any]] = []
    bindings_index = _collect_bindings_from_native_config(native_config)

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
            entries[path] = {"sha256": _sha256_hex(content), "size_bytes": len(content)}

        manifest = {
            "format": PACKAGE_FORMAT,
            "schemaVersion": SCHEMA_VERSION,
            "kind": TEMPLATE_KIND,
            "template": {
                "key": key,
                "label": label,
                "description": description,
                "durationSec": duration_sec,
                "slideType": "native",
                "nativeScreenKey": native_screen_key,
                "title": title,
            },
            "source": {
                "exportedBy": exported_by,
                "exportedAt": datetime.now(timezone.utc).isoformat(),
            },
            "entries": entries,
            "stats": {
                "slideCount": 1,
                "sectionCount": 1,
                "mediaCount": 0,
                "bindingCount": len(bindings_index),
            },
        }
        archive.writestr(MANIFEST_FILENAME, _json_bytes(manifest))

    safe_key = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in key)
    filename = f"{safe_key}{PACKAGE_EXTENSION}"
    return buffer.getvalue(), filename


def parse_slide_template_mdd(raw: bytes) -> dict[str, Any]:
    """Extrai metadata + nativeConfig de um `.mdd` de template (ou MDD com 1 slide)."""
    try:
        with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
            names = set(archive.namelist())
            if MANIFEST_FILENAME not in names or SLIDES_PATH not in names:
                raise SlideTemplateMddError("Pacote MDD incompleto (falta manifest ou slides).")
            manifest = json.loads(archive.read(MANIFEST_FILENAME).decode("utf-8"))
            fmt = str(manifest.get("format") or "").strip()
            if fmt not in PACKAGE_FORMAT_ALIASES:
                raise SlideTemplateMddError(f"Formato MDD inválido: {fmt or '(vazio)'}")
            slides = json.loads(archive.read(SLIDES_PATH).decode("utf-8"))
    except zipfile.BadZipFile as exc:
        raise SlideTemplateMddError("Arquivo não é um ZIP/MDD válido.") from exc
    except json.JSONDecodeError as exc:
        raise SlideTemplateMddError("JSON inválido dentro do MDD.") from exc

    if not isinstance(slides, list) or not slides:
        raise SlideTemplateMddError("MDD sem slides.")
    slide = slides[0]
    if not isinstance(slide, dict):
        raise SlideTemplateMddError("Slide inválido no MDD.")
    native_config = slide.get("nativeConfig")
    if not isinstance(native_config, dict):
        native_config = {}

    template_meta = manifest.get("template") if isinstance(manifest.get("template"), dict) else {}
    key = str(template_meta.get("key") or slide.get("sourceId") or "imported_template").strip()
    label = str(
        template_meta.get("label") or slide.get("title") or key
    ).strip()
    description = template_meta.get("description")
    if description is not None:
        description = str(description)
    duration = template_meta.get("durationSec")
    if duration is None:
        duration = slide.get("durationSec")
    title = str(template_meta.get("title") or slide.get("title") or label).strip()
    native_screen_key = str(
        template_meta.get("nativeScreenKey") or slide.get("nativeScreenKey") or "custom_message"
    ).strip()

    return {
        "key": key,
        "label": label,
        "description": description,
        "slideType": "native",
        "title": title,
        "durationSec": duration,
        "nativeScreenKey": native_screen_key,
        "nativeConfig": native_config,
        "source": "mdd",
    }


def list_mdd_template_files(directory: Path | None = None) -> list[Path]:
    root = directory or SLIDE_TEMPLATES_DIR
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob(f"*{PACKAGE_EXTENSION}") if p.is_file())


def load_mdd_templates(directory: Path | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in list_mdd_template_files(directory):
        try:
            items.append(parse_slide_template_mdd(path.read_bytes()))
        except (SlideTemplateMddError, OSError):
            continue
    return items


def resolve_mdd_template_bytes(preset_key: str, directory: Path | None = None) -> bytes | None:
    root = directory or SLIDE_TEMPLATES_DIR
    direct = root / f"{preset_key}{PACKAGE_EXTENSION}"
    if direct.is_file():
        return direct.read_bytes()
    for path in list_mdd_template_files(root):
        try:
            meta = parse_slide_template_mdd(path.read_bytes())
        except (SlideTemplateMddError, OSError):
            continue
        if meta.get("key") == preset_key:
            return path.read_bytes()
    return None
