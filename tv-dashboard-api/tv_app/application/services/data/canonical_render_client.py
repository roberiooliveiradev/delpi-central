"""Client for the bounded TV canonical render worker (execution host only).

The worker is internal: ``tv-dashboard-api`` is its only caller, with the
shared platform service token. It mounts the shared presentation package and
returns browser-rasterized PNG bytes — artifact storage/lifecycle stays here
in the API (``SlidePreviewRenderService``). Failures are typed and mapped to
``slidePreview.rendered`` failure codes; the context call never breaks on a
render outage.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from tv_app.config import settings

RENDER_REQUEST_MAX_BYTES = 32 * 1024 * 1024
RENDER_RESPONSE_MAX_BYTES = 8_000_000  # same bound as the upload route


class CanonicalRenderError(Exception):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


@dataclass(frozen=True)
class RenderWorkerConfig:
    url: str
    timeout_sec: float

    @property
    def enabled(self) -> bool:
        return bool(self.url.strip())


def render_worker_config() -> RenderWorkerConfig:
    return RenderWorkerConfig(
        url=(settings.TV_RENDER_WORKER_URL or "").rstrip("/"),
        timeout_sec=settings.TV_RENDER_WORKER_TIMEOUT_SECONDS,
    )


class CanonicalRenderClient:
    """POST {worker}/render with the bounded contract — bytes in, PNG out."""

    def __init__(self, config: RenderWorkerConfig | None = None) -> None:
        self._config = config or render_worker_config()

    def render_png(
        self,
        *,
        playlist_id: str,
        slide_id: str,
        revision: int,
        presentation: Mapping[str, Any],
        viewport: Mapping[str, int] | None,
    ) -> bytes:
        if not self._config.enabled:
            raise CanonicalRenderError("RENDER_WORKER_DISABLED")
        token = (settings.TV_RENDER_WORKER_SERVICE_TOKEN or "").strip()
        if not token:
            raise CanonicalRenderError("RENDER_WORKER_AUTH_MISSING")
        authorization = f"Bearer {token}"
        body: dict[str, Any] = {
            "playlistId": str(playlist_id),
            "slideId": str(slide_id),
            "revision": int(revision),
            "presentation": dict(presentation),
        }
        if viewport:
            body["viewport"] = {
                "width": int(viewport["width"]),
                "height": int(viewport["height"]),
            }
        try:
            with httpx.Client(timeout=self._config.timeout_sec) as client:
                response = client.post(
                    f"{self._config.url}/render",
                    json=body,
                    headers={"Authorization": authorization},
                )
                if response.status_code != 200:
                    code = "RENDER_FAILED"
                    try:
                        code = str(response.json().get("code") or code)
                    except ValueError:
                        pass
                    raise CanonicalRenderError(code)
                png = response.content
        except CanonicalRenderError:
            raise
        except httpx.TimeoutException as exc:
            raise CanonicalRenderError("RENDER_TIMEOUT") from exc
        except httpx.HTTPError as exc:
            raise CanonicalRenderError("RENDER_WORKER_UNAVAILABLE") from exc
        if len(png) > RENDER_RESPONSE_MAX_BYTES:
            raise CanonicalRenderError("RENDER_OUTPUT_TOO_LARGE")
        if png[:8] != b"\x89PNG\r\n\x1a\n":
            raise CanonicalRenderError("RENDER_OUTPUT_INVALID")
        return png


class CanonicalStageRenderService:
    """Fill-miss orchestration: render → revision recheck → canonical store.

    Single-flight per (slide, revision) so concurrent readers cannot trigger
    duplicate renders: the loser gets ``RENDER_PENDING`` (projected as
    ``rendered.status = "pending"``), the owner renders, and a later request
    reads the completed artifact.
    """

    _inflight: set[tuple[str, str]] = set()
    _inflight_lock = threading.Lock()

    def __init__(self, client: CanonicalRenderClient | None = None) -> None:
        self._client = client or CanonicalRenderClient()

    def ensure_rendered(
        self,
        *,
        playlist_id: Any,
        slide_id: str,
        revision: int,
        writes: Any,
        present: Any,
        preview_svc: Any,
    ) -> dict[str, Any] | None:
        """Return artifact meta when a canonical_stage PNG now exists, else None.

        Fail-closed on revision race: if the playlist moved between request
        start and render completion the PNG is discarded (never stored under
        a stale revision).
        """
        key = (str(slide_id), str(revision))
        with self._inflight_lock:
            if key in self._inflight:
                raise CanonicalRenderError("RENDER_PENDING")
            if preview_svc.rendered_artifact_meta(slide_id=slide_id, revision=revision):
                return preview_svc.rendered_artifact_meta(
                    slide_id=slide_id, revision=revision
                )
            self._inflight.add(key)
        try:
            payload = present.build_by_id(playlist_id)
        except Exception:
            with self._inflight_lock:
                self._inflight.discard(key)
            raise CanonicalRenderError("RENDER_PAYLOAD_UNAVAILABLE")
        # Stamp the revision this payload was built for — the worker binds it
        # to the request revision (payload-identity binding), while the
        # post-render re-read below remains the authoritative staleness check.
        if isinstance(payload, dict):
            meta = payload.get("presentationMeta")
            if not isinstance(meta, dict):
                meta = {}
                payload["presentationMeta"] = meta
            meta["revision"] = int(revision)
        try:
            playlist = payload.get("playlist") if isinstance(payload, dict) else {}
            width = playlist.get("viewportWidth")
            height = playlist.get("viewportHeight")
            viewport = (
                {"width": int(width), "height": int(height)}
                if isinstance(width, int) and isinstance(height, int)
                and width > 0 and height > 0
                else None
            )
            png = self._client.render_png(
                playlist_id=str(playlist_id),
                slide_id=slide_id,
                revision=revision,
                presentation=payload,
                viewport=viewport,
            )
        finally:
            with self._inflight_lock:
                self._inflight.discard(key)
        # Authoritative re-read: discard the PNG if the revision raced ahead.
        current_revision = writes.get_revision(playlist_id)
        if int(current_revision) != int(revision):
            raise CanonicalRenderError("RENDER_REVISION_STALE")
        from io import BytesIO

        from PIL import Image

        probe = Image.open(BytesIO(png))
        probe.verify()
        probe = Image.open(BytesIO(png))
        img_w, img_h = probe.size
        return preview_svc.store_rendered_png(
            slide_id=slide_id,
            revision=revision,
            png=png,
            width=img_w,
            height=img_h,
        )


_default_render_service: CanonicalStageRenderService | None = None


def get_canonical_stage_render_service() -> CanonicalStageRenderService:
    global _default_render_service
    if _default_render_service is None:
        _default_render_service = CanonicalStageRenderService()
    return _default_render_service
