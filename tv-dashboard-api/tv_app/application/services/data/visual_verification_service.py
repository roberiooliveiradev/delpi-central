"""Commit visual verification. VERIFIED requires persisted, rendered and layout gate."""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.slide_layout_quality_service import (
    SlideLayoutQualityService,
)
from tv_app.application.services.data.slide_preview_render_service import (
    get_slide_preview_render_service,
)


class VisualVerificationService:
    @classmethod
    def build(
        cls,
        *,
        persisted: bool,
        before_native: Mapping[str, Any] | None,
        after_native: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        before = DesignIntelligenceService.design_audit(before_native)
        after = DesignIntelligenceService.design_audit(after_native)
        before_ids = {str(item.get("id")) for item in before.get("issues") or []}
        after_issues = [item for item in after.get("issues") or [] if isinstance(item, dict)]
        after_ids = {str(item.get("id")) for item in after_issues}
        layout_codes = (
            SlideLayoutQualityService.collect_native_layout_issues(after_native)
            if isinstance(after_native, Mapping)
            else []
        )
        return {
            "persisted": bool(persisted),
            "rendered": cls._rendered(after_native),
            "layoutGatePassed": not layout_codes,
            "issuesFixed": [
                item
                for item in before.get("issues") or []
                if isinstance(item, dict) and str(item.get("id")) not in after_ids
            ],
            "issuesIntroduced": [
                item for item in after_issues if str(item.get("id")) not in before_ids
            ],
            "remainingIssues": after_issues,
        }

    @classmethod
    def is_verified(cls, verification: Mapping[str, Any]) -> bool:
        return bool(
            verification.get("persisted")
            and verification.get("rendered")
            and verification.get("layoutGatePassed")
        )

    @staticmethod
    def _rendered(native: Mapping[str, Any] | None) -> bool:
        if not isinstance(native, Mapping):
            return True
        try:
            png = get_slide_preview_render_service().render_png(native)
        except Exception:
            return False
        return isinstance(png, (bytes, bytearray)) and len(png) > 8
