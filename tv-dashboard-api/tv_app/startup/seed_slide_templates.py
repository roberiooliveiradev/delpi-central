"""Seed idempotente de templates system a partir de content/slide_templates/*.mdd."""

from __future__ import annotations

import logging

from tv_app.application.services.slide_template_library_service import SlideTemplateLibraryService

logger = logging.getLogger(__name__)


def seed_slide_templates_on_startup() -> dict:
    """Best-effort seed; não derruba o boot se a tabela ainda não existir."""
    try:
        report = SlideTemplateLibraryService().seed_from_disk()
        logger.info(
            "Slide templates seed: upserted=%s skipped=%s",
            report.get("upserted"),
            report.get("skipped"),
        )
        if report.get("errors"):
            logger.warning("Slide templates seed errors: %s", report["errors"])
        return report
    except Exception:
        logger.exception(
            "Seed de slide templates falhou (API segue; rode migration/seed manualmente)."
        )
        return {"upserted": 0, "skipped": 0, "errors": ["seed_failed"]}
