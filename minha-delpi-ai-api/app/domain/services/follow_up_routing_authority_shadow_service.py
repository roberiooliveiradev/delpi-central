"""E3.S7 — shadow/cutover de follow-up routing (terms vs follow_up_type→routeSegment)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FollowUpRoutingAuthorityShadowService:
    @classmethod
    def record(cls, shadow: dict[str, Any] | None) -> None:
        if not isinstance(shadow, dict):
            return
        logger.info(
            "follow_up_routing_authority_shadow",
            extra={
                "metric": "follow_up_routing_authority_shadow",
                "legacySegment": shadow.get("legacySegment"),
                "candidateSegment": shadow.get("candidateSegment"),
                "followUpType": shadow.get("followUpType"),
                "agree": bool(shadow.get("agree")),
                "authority": shadow.get("authority"),
                "cutoverEnabled": bool(shadow.get("cutoverEnabled")),
            },
        )
