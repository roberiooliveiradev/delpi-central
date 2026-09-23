"""Server-side schematic PNG of a TV slide for VISTA vision (owner-local).

Renders frames/colors/labels from native_config — spatial fidelity for layout
reasoning, not pixel-perfect React SSR. Cache key: (slideId, revision).
"""

from __future__ import annotations

import hashlib
import threading
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

from PIL import Image, ImageDraw, ImageFont

from tv_app.application.services.data.slide_preview_token import (
    DEFAULT_TTL_SEC,
    mint_slide_preview_token,
)
from tv_app.config import settings

# Medium resolution by default (budget / OOM mitigation).
DEFAULT_WIDTH = 960
DEFAULT_HEIGHT = 540

_TYPE_FILL: dict[str, tuple[int, int, int, int]] = {
    "kpi_view": (255, 255, 255, 230),
    "data_kpi": (255, 255, 255, 230),
    "chart_view": (226, 232, 240, 220),
    "data_chart": (226, 232, 240, 220),
    "table_view": (241, 245, 249, 220),
    "data_table": (241, 245, 249, 220),
    "heading": (0, 0, 0, 0),
    "text": (0, 0, 0, 0),
    "shape": (0, 102, 179, 180),
    "icon": (0, 102, 179, 120),
    "input": (255, 255, 255, 200),
    "image": (148, 163, 184, 160),
}

_TYPE_STROKE: dict[str, tuple[int, int, int]] = {
    "kpi_view": (0, 102, 179),
    "data_kpi": (0, 102, 179),
    "chart_view": (15, 23, 42),
    "data_chart": (15, 23, 42),
    "table_view": (71, 85, 105),
    "data_table": (71, 85, 105),
    "heading": (255, 255, 255),
    "text": (226, 232, 240),
    "shape": (0, 56, 102),
    "icon": (0, 102, 179),
    "input": (148, 163, 184),
    "image": (100, 116, 139),
}


def _parse_hex(color: Any, default: tuple[int, int, int] = (0, 56, 102)) -> tuple[int, int, int]:
    if not isinstance(color, str):
        return default
    raw = color.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return default
    try:
        return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    except ValueError:
        return default


def _bg_colors(cfg: Mapping[str, Any]) -> tuple[tuple[int, int, int], tuple[int, int, int] | None]:
    bg = cfg.get("background")
    if not isinstance(bg, dict):
        return (0, 56, 102), (13, 40, 64)
    if bg.get("type") == "color" and isinstance(bg.get("value"), str):
        c = _parse_hex(bg["value"])
        return c, None
    if bg.get("type") == "gradient":
        top = _parse_hex(bg.get("from") or bg.get("value") or "#003866")
        bottom = _parse_hex(bg.get("to") or "#0d2840")
        return top, bottom
    return (0, 56, 102), (13, 40, 64)


def _frame_px(
    frame: Mapping[str, Any],
    *,
    width: int,
    height: int,
) -> tuple[int, int, int, int] | None:
    try:
        x = float(frame.get("x", 0))
        y = float(frame.get("y", 0))
        w = float(frame.get("w", 0))
        h = float(frame.get("h", 0))
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    left = int(round(x / 100.0 * width))
    top = int(round(y / 100.0 * height))
    right = int(round((x + w) / 100.0 * width))
    bottom = int(round((y + h) / 100.0 * height))
    left = max(0, min(width - 1, left))
    top = max(0, min(height - 1, top))
    right = max(left + 1, min(width, right))
    bottom = max(top + 1, min(height, bottom))
    return left, top, right, bottom


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=size)
        except OSError:
            return ImageFont.load_default()


def _fill_for_block(block: Mapping[str, Any]) -> tuple[int, int, int, int]:
    btype = str(block.get("type") or "")
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    for key in ("fill", "backgroundColor", "background"):
        raw = style.get(key)
        if isinstance(raw, str) and raw.strip().startswith("#"):
            r, g, b = _parse_hex(raw)
            return r, g, b, 220
    return _TYPE_FILL.get(btype, (148, 163, 184, 160))


def _label_for_block(block: Mapping[str, Any]) -> str:
    btype = str(block.get("type") or "")
    title = ""
    content = block.get("content")
    if isinstance(content, str) and content.strip():
        title = content.strip()[:40]
    elif isinstance(block.get("title"), str):
        title = str(block["title"]).strip()[:40]
    parts = block.get("parts") if isinstance(block.get("parts"), dict) else {}
    tpart = parts.get("title") if isinstance(parts.get("title"), dict) else {}
    if not title and isinstance(tpart.get("text"), str):
        title = str(tpart["text"]).strip()[:40]
    bid = str(block.get("id") or "")[:8]
    if title:
        return f"{btype}: {title}"
    return f"{btype} {bid}".strip()


class SlidePreviewRenderService:
    """Raster schematic + disk cache keyed by slideId+revision."""

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        base = cache_dir or Path(
            getattr(settings, "TV_DASHBOARD_MEDIA_UPLOAD_DIR", None)
            or "/tmp/tv-dashboard-media"
        )
        self._cache_dir = Path(base) / "slide-previews"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._meta: dict[str, float] = {}

    def _cache_key(self, slide_id: str, revision: str | int | None) -> str:
        raw = f"{slide_id}:{revision or ''}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]

    def _cache_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.png"

    def render_png(
        self,
        native_config: Mapping[str, Any] | None,
        *,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        title: str | None = None,
    ) -> bytes:
        cfg = native_config if isinstance(native_config, dict) else {}
        img = Image.new("RGB", (width, height), color=(0, 56, 102))
        draw = ImageDraw.Draw(img, "RGBA")
        top, bottom = _bg_colors(cfg)
        if bottom is None:
            draw.rectangle([0, 0, width, height], fill=top)
        else:
            for y in range(height):
                t = y / max(1, height - 1)
                r = int(top[0] + (bottom[0] - top[0]) * t)
                g = int(top[1] + (bottom[1] - top[1]) * t)
                b = int(top[2] + (bottom[2] - top[2]) * t)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

        blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
        spatial = [
            b
            for b in blocks
            if isinstance(b, dict) and str(b.get("type") or "") != "data_source"
        ]

        def sort_key(b: Mapping[str, Any]) -> int:
            style = b.get("style") if isinstance(b.get("style"), dict) else {}
            try:
                return int(style.get("zIndex") or b.get("zIndex") or 0)
            except (TypeError, ValueError):
                return 0

        spatial.sort(key=sort_key)
        label_font = _font(max(10, height // 48))
        small_font = _font(max(9, height // 54))

        for block in spatial:
            fr = block.get("frame")
            if not isinstance(fr, dict):
                continue
            box = _frame_px(fr, width=width, height=height)
            if not box:
                continue
            left, top_y, right, bottom_y = box
            btype = str(block.get("type") or "")
            fill = _fill_for_block(block)
            stroke = _TYPE_STROKE.get(btype, (226, 232, 240))
            radius = 8
            style = block.get("style") if isinstance(block.get("style"), dict) else {}
            try:
                if style.get("borderRadius") is not None:
                    radius = max(0, min(48, int(float(style["borderRadius"]) * 0.25)))
            except (TypeError, ValueError):
                pass
            draw.rounded_rectangle(
                [left, top_y, right, bottom_y],
                radius=radius,
                fill=fill,
                outline=stroke,
                width=2,
            )
            label = _label_for_block(block)
            text_fill = (15, 23, 42) if fill[0] > 180 else (248, 250, 252)
            if btype in {"heading", "text"}:
                text_fill = (248, 250, 252)
            pad = 6
            draw.text(
                (left + pad, top_y + pad),
                label,
                fill=text_fill,
                font=label_font,
            )
            signals = []
            if btype in {"kpi_view", "data_kpi"}:
                parts = block.get("parts") if isinstance(block.get("parts"), dict) else {}
                value = parts.get("value") if isinstance(parts.get("value"), dict) else {}
                if value.get("fontSize") is not None:
                    signals.append(f"valFs={value.get('fontSize')}")
            chart_type = block.get("chartType")
            if chart_type:
                signals.append(f"chart={chart_type}")
            if signals:
                draw.text(
                    (left + pad, top_y + pad + 16),
                    " ".join(signals),
                    fill=text_fill,
                    font=small_font,
                )

        if title:
            banner = _font(max(12, height // 36))
            draw.rectangle([0, 0, width, 28], fill=(15, 23, 42, 180))
            draw.text((8, 6), str(title)[:80], fill=(248, 250, 252), font=banner)

        buf = BytesIO()
        img.convert("RGB").save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def get_or_render(
        self,
        *,
        slide_id: str,
        revision: str | int | None,
        native_config: Mapping[str, Any] | None,
        title: str | None = None,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
    ) -> bytes:
        key = self._cache_key(slide_id, revision)
        path = self._cache_path(key)
        with self._lock:
            if path.is_file():
                self._meta[key] = time.time()
                return path.read_bytes()
            png = self.render_png(
                native_config, width=width, height=height, title=title
            )
            path.write_bytes(png)
            self._meta[key] = time.time()
            self._prune_locked()
            return png

    def _prune_locked(self, max_files: int = 64) -> None:
        files = sorted(self._cache_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)
        while len(files) > max_files:
            oldest = files.pop(0)
            try:
                oldest.unlink(missing_ok=True)
            except OSError:
                pass
            self._meta.pop(oldest.stem, None)

    def build_preview_payload(
        self,
        *,
        playlist_id: str,
        slide_id: str,
        revision: str | int | None,
        native_config: Mapping[str, Any] | None,
        title: str | None = None,
        public_base_url: str | None = None,
        root_path: str | None = None,
        ttl_sec: int = DEFAULT_TTL_SEC,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
    ) -> dict[str, Any]:
        """Ensure PNG cached and return contract fields (no image bytes)."""
        self.get_or_render(
            slide_id=slide_id,
            revision=revision,
            native_config=native_config,
            title=title,
            width=width,
            height=height,
        )
        token, exp = mint_slide_preview_token(
            playlist_id=playlist_id,
            slide_id=slide_id,
            revision=revision,
            ttl_sec=ttl_sec,
        )
        base = (public_base_url or settings.PUBLIC_BASE_URL or "http://localhost").rstrip("/")
        root = (root_path or settings.TV_DASHBOARD_API_ROOT_PATH or "/apps/tv-dashboard-api").rstrip(
            "/"
        )
        preview_url = f"{base}{root}/gpt-actions/v1/slide-previews/{token}"
        from datetime import datetime, timezone

        return {
            "playlistId": str(playlist_id),
            "slideId": str(slide_id),
            "revision": revision,
            "previewUrl": preview_url,
            "expiresAt": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat(),
            "width": width,
            "height": height,
            "mimeType": "image/png",
            "kind": "schematic_layout",
        }


_default_service: SlidePreviewRenderService | None = None


def get_slide_preview_render_service() -> SlidePreviewRenderService:
    global _default_service
    if _default_service is None:
        _default_service = SlidePreviewRenderService()
    return _default_service
