from datetime import datetime, timezone
import logging

from app.domain.ports.action_display_label_cache_port import ActionDisplayLabelCachePort
from app.extensions.db import db
from app.infrastructure.db.models.action_display_label_cache_model import (
    ActionDisplayLabelCacheModel,
)

logger = logging.getLogger(__name__)


class PostgresActionDisplayLabelCacheRepository(ActionDisplayLabelCachePort):
    def get_label(self, cache_key: str) -> str | None:
        token = str(cache_key or "").strip()
        if not token:
            return None

        try:
            row = ActionDisplayLabelCacheModel.query.filter_by(cache_key=token).first()
        except Exception:
            logger.debug("action_display_label_cache_get_failed", extra={"cacheKey": token})
            return None

        if row is None:
            return None

        label = str(row.label or "").strip()
        return label or None

    def put_label(
        self,
        cache_key: str,
        label: str,
        *,
        source: str = "LLM_LOCALIZATION",
    ) -> None:
        token = str(cache_key or "").strip()
        resolved = str(label or "").strip()
        if not token or not resolved:
            return

        now = datetime.now(timezone.utc)
        provenance = str(source or "LLM_LOCALIZATION").strip() or "LLM_LOCALIZATION"

        try:
            row = ActionDisplayLabelCacheModel.query.filter_by(cache_key=token).first()
            if row is None:
                db.session.add(
                    ActionDisplayLabelCacheModel(
                        cache_key=token,
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
                "action_display_label_cache_put_failed",
                extra={"cacheKey": token},
            )
            try:
                db.session.rollback()
            except Exception:
                pass
