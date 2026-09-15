from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from tv_app.application.services.media_video_optimize_service import MediaVideoOptimizeService


def _write_fake_mp4(path: Path, size: int = 64) -> None:
    path.write_bytes(b"\x00" * size)


def test_optimize_mp4_remux_and_poster(tmp_path: Path):
    media = tmp_path / "clip.mp4"
    _write_fake_mp4(media, 128)
    service = MediaVideoOptimizeService()

    probe_payload = {
        "format": {"duration": "12.5"},
        "streams": [{"codec_type": "video", "width": 1920, "height": 1080}],
    }

    def fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        result.stdout = ""
        if cmd and cmd[0] == "ffprobe":
            result.stdout = json.dumps(probe_payload)
            return result
        # ffmpeg remux or poster
        out = Path(cmd[-1])
        out.write_bytes(b"\x01" * 80)
        return result

    with patch(
        "tv_app.application.services.media_video_optimize_service.subprocess.run",
        side_effect=fake_run,
    ):
        result = service.optimize_stored_video(
            media_path=media,
            mime_type="video/mp4",
            base_dir=tmp_path,
        )

    assert result.optimized is True
    assert result.duration_ms == 12500
    assert result.width_px == 1920
    assert result.height_px == 1080
    assert result.poster_stored_name
    assert (tmp_path / result.poster_stored_name).is_file()


def test_optimize_webm_skips_faststart_but_can_poster(tmp_path: Path):
    media = tmp_path / "clip.webm"
    _write_fake_mp4(media, 64)
    service = MediaVideoOptimizeService()

    def fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        result.stdout = ""
        if cmd and cmd[0] == "ffprobe":
            result.stdout = json.dumps(
                {"format": {"duration": "3"}, "streams": [{"codec_type": "video", "width": 640, "height": 360}]}
            )
            return result
        # Must not be asked for movflags on webm path in remux — only poster ffmpeg.
        assert "+faststart" not in cmd
        Path(cmd[-1]).write_bytes(b"jpg")
        return result

    with patch(
        "tv_app.application.services.media_video_optimize_service.subprocess.run",
        side_effect=fake_run,
    ):
        result = service.optimize_stored_video(
            media_path=media,
            mime_type="video/webm",
            base_dir=tmp_path,
        )

    assert result.poster_stored_name
    assert result.height_px == 360


def test_optimize_ffmpeg_missing_does_not_raise(tmp_path: Path):
    media = tmp_path / "clip.mp4"
    _write_fake_mp4(media)
    service = MediaVideoOptimizeService()

    with patch(
        "tv_app.application.services.media_video_optimize_service.subprocess.run",
        side_effect=FileNotFoundError("ffmpeg"),
    ):
        result = service.optimize_stored_video(
            media_path=media,
            mime_type="video/mp4",
            base_dir=tmp_path,
        )

    assert result.optimized is False
    assert result.poster_stored_name is None
