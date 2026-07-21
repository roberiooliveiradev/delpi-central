"""Persistência de artefato HTML das runs Delpi Reports."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_SAFE_RUN_ID = re.compile(r"[^a-zA-Z0-9_-]+")


class ReportRunArtifactStorage:
    """Grava HTML da run em volume persistente (não bloqueia envio se falhar)."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir)

    def save_html(self, *, run_id: str, html_body: str) -> str | None:
        safe_id = _SAFE_RUN_ID.sub("_", str(run_id or "").strip()) or "unknown"
        try:
            self._base.mkdir(parents=True, exist_ok=True)
            path = self._base / f"{safe_id}.html"
            path.write_text(html_body or "", encoding="utf-8")
            return str(path)
        except OSError as exc:
            logger.warning(
                "report_artifact_write_failed runId=%s error=%s",
                run_id,
                exc,
            )
            return None
