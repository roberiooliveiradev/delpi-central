"""Resolução do turno de análise de desenho — gates de skill, PDF e código."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_drawing_intent_service import (
    DRAWING_ANALYSIS_SKILL_ALIAS,
    DRAWING_ANALYSIS_SKILL_KEY,
    ChatDrawingIntentService,
)
from app.domain.services.chat_drawing_product_code_resolution_service import (
    ChatDrawingProductCodeResolutionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.skills.chat_skill_registry import ChatSkillRegistry


@dataclass(frozen=True)
class DrawingTurnResolution:
    active: bool
    direct_answer: str | None = None
    product_code: str | None = None
    product_codes: tuple[str, ...] = ()
    product_code_source: str | None = None
    has_pdf_attachment: bool = False
    requires_pdf: bool = False
    skill_enabled: bool = False


class ChatDrawingAnalysisTurnService:
    @classmethod
    def resolve(
        cls,
        *,
        message: str | None,
        attachment_ids: list[str] | None = None,
        agent_metadata: dict | None = None,
        skills: dict | None = None,
        previous_messages: list | None = None,
        attachment_context: str | None = None,
        user_context_items: list | None = None,
    ) -> DrawingTurnResolution | None:
        if not ChatDrawingIntentService.is_drawing_analysis_request(
            message,
            attachment_ids=attachment_ids,
        ):
            return None

        has_pdf = bool(attachment_ids)
        skill_enabled = cls._is_skill_enabled(agent_metadata, skills)

        if not skill_enabled:
            return DrawingTurnResolution(
                active=True,
                direct_answer=ChatDrawingIntentService.build_skill_disabled_answer(),
                skill_enabled=False,
                has_pdf_attachment=has_pdf,
            )

        if has_pdf:
            product_code = ChatProductQueryIntentService.extract_product_code(message or "")
            product_codes = (product_code,) if product_code else ()
            code_source = "message" if product_code else None
        else:
            product_codes, code_source = (
                ChatDrawingProductCodeResolutionService.resolve_explicit_codes_without_attachment(
                    message=message or "",
                    user_context_items=user_context_items,
                )
            )
            product_code = product_codes[0] if product_codes else None

        if not product_code and attachment_context and not has_pdf:
            from app.domain.services.chat_drawing_pdf_extraction_service import (
                ChatDrawingPdfExtractionService,
            )

            pdf_extract = ChatDrawingPdfExtractionService.parse_from_attachment_context(
                attachment_context
            )

            if pdf_extract and pdf_extract.get("productCode"):
                product_code = str(pdf_extract["productCode"])

            if pdf_extract and pdf_extract.get("productCode"):
                product_code = str(pdf_extract["productCode"])
                product_codes = (product_code,)
                code_source = code_source or "attachment_context"

        if (
            not has_pdf
            and not product_code
            and ChatDrawingIntentService.is_drawing_analysis_request(
                message,
                attachment_ids=attachment_ids,
            )
        ):
            return DrawingTurnResolution(
                active=True,
                direct_answer=ChatDrawingIntentService.build_missing_product_code_answer(),
                skill_enabled=True,
                has_pdf_attachment=False,
                requires_pdf=True,
            )

        if ChatDrawingIntentService.wants_product_analyser(message) and not product_code:
            return DrawingTurnResolution(
                active=True,
                direct_answer=ChatDrawingIntentService.build_missing_product_code_answer(),
                skill_enabled=True,
                has_pdf_attachment=has_pdf,
                requires_pdf=not has_pdf,
            )

        return DrawingTurnResolution(
            active=True,
            product_code=product_code,
            product_codes=product_codes,
            product_code_source=code_source,
            has_pdf_attachment=has_pdf,
            skill_enabled=True,
            requires_pdf=ChatDrawingIntentService.requires_pdf_for_full_analysis(
                message,
                attachment_ids=attachment_ids,
            ),
        )

    @classmethod
    def _is_skill_enabled(cls, agent_metadata: dict | None, skills: dict | None) -> bool:
        if (skills or {}).get("drawingAnalysis"):
            return True

        if ChatSkillRegistry.is_enabled(agent_metadata, DRAWING_ANALYSIS_SKILL_KEY):
            return True

        return ChatSkillRegistry.is_enabled(agent_metadata, DRAWING_ANALYSIS_SKILL_ALIAS)
