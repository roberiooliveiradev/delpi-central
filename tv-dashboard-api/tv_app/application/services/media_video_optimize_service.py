"""Otimização best-effort de vídeo após upload: faststart (MP4) + poster JPEG."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_FFMPEG_TIMEOUT_SEC = 120
_FFPROBE_TIMEOUT_SEC = 30
_POSTER_SEEK_SEC = 1.0


@dataclass(frozen=True)
class VideoOptimizeResult:
    poster_stored_name: str | None = None
    duration_ms: int | None = None
    width_px: int | None = None
    height_px: int | None = None
    file_size_bytes: int | None = None
    optimized: bool = False


class MediaVideoOptimizeService:
    """
    Remux MP4 com moov no início e extrai frame ~1s como JPEG sidecar.
    Falhas não propagam — o upload permanece válido sem poster/faststart.
    """

    def __init__(
        self,
        *,
        ffmpeg_bin: str = "ffmpeg",
        ffprobe_bin: str = "ffprobe",
        timeout_sec: int = _FFMPEG_TIMEOUT_SEC,
    ) -> None:
        self._ffmpeg = ffmpeg_bin
        self._ffprobe = ffprobe_bin
        self._timeout = timeout_sec

    def optimize_stored_video(
        self,
        *,
        media_path: Path,
        mime_type: str,
        base_dir: Path,
    ) -> VideoOptimizeResult:
        if not media_path.is_file():
            return VideoOptimizeResult()

        normalized = (mime_type or "").split(";", 1)[0].strip().lower()
        duration_ms, width_px, height_px = self._probe(media_path)

        size_bytes = media_path.stat().st_size
        remuxed = False
        if normalized == "video/mp4":
            remuxed = self._remux_faststart(media_path)
            if remuxed:
                size_bytes = media_path.stat().st_size

        poster_name = self._extract_poster(media_path, base_dir=base_dir)
        optimized = bool(poster_name) or remuxed
        return VideoOptimizeResult(
            poster_stored_name=poster_name,
            duration_ms=duration_ms,
            width_px=width_px,
            height_px=height_px,
            file_size_bytes=size_bytes,
            optimized=optimized,
        )

    def _probe(self, path: Path) -> tuple[int | None, int | None, int | None]:
        try:
            proc = subprocess.run(
                [
                    self._ffprobe,
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=_FFPROBE_TIMEOUT_SEC,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("ffprobe unavailable for %s: %s", path.name, exc)
            return None, None, None
        if proc.returncode != 0 or not proc.stdout.strip():
            logger.warning("ffprobe failed for %s: %s", path.name, (proc.stderr or "")[:200])
            return None, None, None
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return None, None, None

        duration_ms: int | None = None
        fmt = payload.get("format") if isinstance(payload, dict) else None
        if isinstance(fmt, dict):
            try:
                duration_ms = int(float(fmt.get("duration") or 0) * 1000)
                if duration_ms <= 0:
                    duration_ms = None
            except (TypeError, ValueError):
                duration_ms = None

        width_px: int | None = None
        height_px: int | None = None
        streams = payload.get("streams") if isinstance(payload, dict) else None
        if isinstance(streams, list):
            for stream in streams:
                if not isinstance(stream, dict):
                    continue
                if stream.get("codec_type") != "video":
                    continue
                try:
                    width_px = int(stream.get("width") or 0) or None
                    height_px = int(stream.get("height") or 0) or None
                except (TypeError, ValueError):
                    width_px, height_px = None, None
                break
        return duration_ms, width_px, height_px

    def _remux_faststart(self, path: Path) -> bool:
        temp = path.with_suffix(path.suffix + ".faststart.tmp")
        try:
            proc = subprocess.run(
                [
                    self._ffmpeg,
                    "-y",
                    "-i",
                    str(path),
                    "-c",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(temp),
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
            if proc.returncode != 0 or not temp.is_file() or temp.stat().st_size <= 0:
                logger.warning(
                    "ffmpeg faststart failed for %s: %s",
                    path.name,
                    (proc.stderr or "")[:300],
                )
                if temp.exists():
                    temp.unlink(missing_ok=True)
                return False
            temp.replace(path)
            return True
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("ffmpeg faststart unavailable for %s: %s", path.name, exc)
            if temp.exists():
                temp.unlink(missing_ok=True)
            return False

    def _extract_poster(self, path: Path, *, base_dir: Path) -> str | None:
        poster_name = f"{uuid.uuid4().hex}.poster.jpg"
        poster_path = base_dir / poster_name
        seek = _POSTER_SEEK_SEC
        try:
            proc = subprocess.run(
                [
                    self._ffmpeg,
                    "-y",
                    "-ss",
                    str(seek),
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "3",
                    str(poster_path),
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
            if proc.returncode != 0 or not poster_path.is_file() or poster_path.stat().st_size <= 0:
                # Vídeo curto: tentar frame em 0s.
                if poster_path.exists():
                    poster_path.unlink(missing_ok=True)
                proc = subprocess.run(
                    [
                        self._ffmpeg,
                        "-y",
                        "-ss",
                        "0",
                        "-i",
                        str(path),
                        "-frames:v",
                        "1",
                        "-q:v",
                        "3",
                        str(poster_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    check=False,
                )
            if proc.returncode != 0 or not poster_path.is_file() or poster_path.stat().st_size <= 0:
                logger.warning(
                    "ffmpeg poster failed for %s: %s",
                    path.name,
                    (proc.stderr or "")[:300],
                )
                if poster_path.exists():
                    poster_path.unlink(missing_ok=True)
                return None
            return poster_name
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("ffmpeg poster unavailable for %s: %s", path.name, exc)
            if poster_path.exists():
                poster_path.unlink(missing_ok=True)
            return None

    @staticmethod
    def copy_poster_file(
        *,
        storage_base: Path,
        source_poster_name: str,
    ) -> str | None:
        source = storage_base / source_poster_name
        if not source.is_file():
            return None
        dest_name = f"{uuid.uuid4().hex}.poster.jpg"
        dest = storage_base / dest_name
        try:
            shutil.copy2(source, dest)
        except OSError:
            return None
        return dest_name
