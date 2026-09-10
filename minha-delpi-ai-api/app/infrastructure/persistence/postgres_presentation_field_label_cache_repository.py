from datetime import datetime, timezone
import logging

from app.domain.ports.presentation_field_label_cache_port import (
    PresentationFieldLabelCachePort,
)
from app.extensions.db import db
from app.infrastructure.db.models.presentation_field_label_cache_model import (
    PresentationFieldLabelCacheModel,
)

logger = logging.getLogger(__name__)


class PostgresPresentationFieldLabelCacheRepository(PresentationFieldLabelCachePort):
    def get_label(self, field_key: str) -> str | None:
        token = str(field_key or "").strip()
        if not token:
            return None

        try:
            row = PresentationFieldLabelCacheModel.query.filter_by(field_key=token).first()
        except Exception:
            logger.debug("presentation_field_label_cache_get_failed", extra={"fieldKey": token})
            return None

        if row is None:
            return None

        label = str(row.label or "").strip()
        return label or None

    def put_label(
        self,
        field_key: str,
        label: str,
        *,
        source: str = "LLM_LOCALIZATION",
    ) -> None:
        token = str(field_key or "").strip()
        resolved = str(label or "").strip()
        if not token or not resolved:
            return

        now = datetime.now(timezone.utc)
        provenance = str(source or "LLM_LOCALIZATION").strip() or "LLM_LOCALIZATION"

        try:
            row = PresentationFieldLabelCacheModel.query.filter_by(field_key=token).first()
            if row is None:
                db.session.add(
                    PresentationFieldLabelCacheModel(
                        field_key=token,
                        label=resolved,
                        source=provenance,
                        updated_at=now,
                    )
                )
            else:
                row.label = resolved
                row.source = provenance
                row.updated_at = now

            db.session.commit()
        except Exception:
            logger.debug(
                "presentation_field_label_cache_put_failed",
                extra={"fieldKey": token},
            )
            try:
                db.session.rollback()
            except Exception:
                pass
