"""Avaliação de descrição cadastral × Normas Técnicas DELPI (follow-up pós-/products/).

MP / intermediário / consumível → RAG com a descrição em foco.
Produto acabado (90xx) ou família sem doc → resposta direta honesta (sem inventar norma).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.domain.services.chat_drawing_product_family_classification_service import (
    ChatDrawingProductFamilyClassificationService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_technical_description_vocabulary_service import (
    ChatTechnicalDescriptionVocabularyService,
)

OUTCOME_EVALUATE = "evaluate"
OUTCOME_MISSING_DOCS = "missing_documentation"
OUTCOME_NEED_CONTEXT = "need_context"


@dataclass(frozen=True)
class TechnicalDescriptionComplianceAssessment:
    is_compliance_request: bool
    outcome: str
    product_code: str | None = None
    description_text: str | None = None
    family_kind: str | None = None
    group_code: str | None = None
    has_normas_documentation: bool = False
    direct_answer: str | None = None


class ChatTechnicalDescriptionComplianceService:
    @classmethod
    def is_compliance_follow_up(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return any(
            ChatMessageNormalizationService.strip_accents(marker) in normalized
            for marker in ChatTechnicalDescriptionVocabularyService.compliance_follow_up_markers()
            if str(marker or "").strip()
        )

    @classmethod
    def assess(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
    ) -> TechnicalDescriptionComplianceAssessment | None:
        if not cls.is_compliance_follow_up(message):
            return None

        product_code = cls._resolve_product_code(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
        )
        description_text = cls._resolve_description_text(
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            product_code=product_code,
        )

        if not product_code and not description_text:
            answer = ChatTechnicalDescriptionVocabularyService.compliance_answer(
                "missingProductContext",
                productCode="",
            )
            return TechnicalDescriptionComplianceAssessment(
                is_compliance_request=True,
                outcome=OUTCOME_NEED_CONTEXT,
                direct_answer=answer or None,
            )

        family = ChatDrawingProductFamilyClassificationService.classify(
            product_code,
            description=description_text,
        )
        kind = str(family.kind or ChatDrawingProductFamilyClassificationService.KIND_UNKNOWN)
        documented = kind in set(
            ChatTechnicalDescriptionVocabularyService.compliance_kinds_with_documentation()
        )

        if kind == ChatDrawingProductFamilyClassificationService.KIND_FINISHED:
            answer = ChatTechnicalDescriptionVocabularyService.compliance_answer(
                "finishedProduct",
                productCode=product_code or "—",
            )
            return TechnicalDescriptionComplianceAssessment(
                is_compliance_request=True,
                outcome=OUTCOME_MISSING_DOCS,
                product_code=product_code,
                description_text=description_text,
                family_kind=kind,
                group_code=family.group_code,
                has_normas_documentation=False,
                direct_answer=answer or None,
            )

        if not documented:
            answer = ChatTechnicalDescriptionVocabularyService.compliance_answer(
                "unknownFamily",
                productCode=product_code or "—",
            )
            return TechnicalDescriptionComplianceAssessment(
                is_compliance_request=True,
                outcome=OUTCOME_MISSING_DOCS,
                product_code=product_code,
                description_text=description_text,
                family_kind=kind,
                group_code=family.group_code,
                has_normas_documentation=False,
                direct_answer=answer or None,
            )

        if not description_text:
            answer = ChatTechnicalDescriptionVocabularyService.compliance_answer(
                "missingDescription",
                productCode=product_code or "—",
            )
            return TechnicalDescriptionComplianceAssessment(
                is_compliance_request=True,
                outcome=OUTCOME_NEED_CONTEXT,
                product_code=product_code,
                family_kind=kind,
                group_code=family.group_code,
                has_normas_documentation=True,
                direct_answer=answer or None,
            )

        return TechnicalDescriptionComplianceAssessment(
            is_compliance_request=True,
            outcome=OUTCOME_EVALUATE,
            product_code=product_code,
            description_text=description_text,
            family_kind=kind,
            group_code=family.group_code or (
                ChatDrawingProductFamilyClassificationService.resolve_mp_group_code(
                    product_code
                )
            ),
            has_normas_documentation=True,
        )

    @classmethod
    def try_build_direct_answer(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
    ) -> dict[str, Any] | None:
        assessment = cls.assess(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
        )

        if not assessment or not assessment.direct_answer:
            return None

        if assessment.outcome not in {OUTCOME_MISSING_DOCS, OUTCOME_NEED_CONTEXT}:
            return None

        return {
            "directAnswer": assessment.direct_answer,
            "pipelineStage": "technical_description_compliance",
            "skipRag": True,
            "assessment": {
                "outcome": assessment.outcome,
                "productCode": assessment.product_code,
                "familyKind": assessment.family_kind,
                "hasNormasDocumentation": assessment.has_normas_documentation,
            },
        }

    @classmethod
    def build_rag_query(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
    ) -> str | None:
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        assessment = cls.assess(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
        )

        if not assessment or assessment.outcome != OUTCOME_EVALUATE:
            return None

        parts: list[str] = []
        lead = ChatTechnicalDescriptionVocabularyService.compliance_rag_query_lead(
            family_kind=assessment.family_kind,
        )

        if lead:
            parts.append(lead)

        if assessment.family_kind == ChatDrawingProductFamilyClassificationService.KIND_INTERMEDIATE:
            # Só doc de intermediários — lead/seeds de Normas MP diluem FTS e o LLM admite «não tenho».
            parts.extend(
                ChatTechnicalDescriptionVocabularyService.intermediate_rag_query_seeds()
            )
            if assessment.group_code:
                parts.append(f"família {assessment.group_code}")
                parts.append(f"grupo {assessment.group_code}")
            parts.append("código intermediário segmentos isolação bitola cor comprimento decape")
            # Explicitamente evitar puxar Normas MP no FTS.
            parts.append("produto intermediário 50xx nomenclatura")
        else:
            parts.append("Normas_Tecnicas_DELPI")
            if assessment.group_code:
                parts.append(f"grupo {assessment.group_code}")
            group_seeds = ChatTechnicalDescriptionVocabularyService.group_rag_query_seeds(
                assessment.group_code
            )
            parts.extend(group_seeds)
            base = ChatTechnicalDescriptionIntentService.build_rag_query(
                f"grupo {assessment.group_code or ''} {message or ''}"
            )
            if base:
                parts.append(base)

        if assessment.product_code:
            parts.append(f"produto {assessment.product_code}")

        if assessment.description_text:
            parts.append(f"descrição cadastral: {assessment.description_text}")
            # Tokens da descrição (ex.: PINO) focam FTS no subtipo dentro do grupo.
            desc_fold = ChatMessageNormalizationService.strip_accents(
                assessment.description_text
            ).lower()
            for hint in ChatTechnicalDescriptionVocabularyService.compliance_description_rag_token_hints():
                hint_fold = ChatMessageNormalizationService.strip_accents(hint).lower()

                if hint_fold and hint_fold in desc_fold:
                    parts.append(hint)

        return " ".join(dict.fromkeys(part for part in parts if str(part).strip()))

    @classmethod
    def _resolve_product_code(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None,
        workspace_context: dict | None,
    ) -> str | None:
        code = ChatProductQueryIntentService.extract_product_code(message or "")

        if code:
            return code

        working = (
            workspace_context.get("workingMemory")
            if isinstance(workspace_context, dict)
            else None
        )

        if isinstance(working, dict):
            focus = working.get("operationalFocus")

            if isinstance(focus, dict):
                focus_code = ChatProductQueryIntentService.normalize_product_code(
                    str(focus.get("productCode") or "")
                )

                if focus_code:
                    return focus_code

            excerpt = working.get("lastResultExcerpt")

            if isinstance(excerpt, dict):
                for key in excerpt.get("topKeys") or []:
                    candidate = ChatProductQueryIntentService.normalize_product_code(
                        str(key or "")
                    )

                    if candidate:
                        return candidate

        for item in reversed(list(previous_messages or [])):
            content = ChatConversationContextService.message_content(item)
            found = ChatProductQueryIntentService.extract_product_code(content)

            if found:
                return found

        return None

    @classmethod
    def _resolve_description_text(
        cls,
        *,
        previous_messages: list[Any] | None,
        workspace_context: dict | None,
        product_code: str | None,
    ) -> str | None:
        field_keys = {
            ChatMessageNormalizationService.strip_accents(str(key).lower())
            for key in ChatTechnicalDescriptionVocabularyService.compliance_description_field_keys()
            if str(key).strip()
        }

        # Prefer structured tool payload (B1_DESC) over prosa de insight (ipi_rate…).
        for item in reversed(list(previous_messages or [])):
            role = ChatConversationContextService.message_role(item).lower()

            if role not in {"assistant", "ai"}:
                continue

            from_tools = cls._description_from_tool_calls(
                item,
                field_keys=field_keys,
                product_code=product_code,
            )

            if from_tools:
                return from_tools

        working = (
            workspace_context.get("workingMemory")
            if isinstance(workspace_context, dict)
            else None
        )

        if isinstance(working, dict):
            excerpt = working.get("lastResultExcerpt")

            if isinstance(excerpt, dict):
                payload = excerpt.get("responsePreview") or excerpt.get("payload")

                if isinstance(payload, dict):
                    found = cls._description_from_mapping(payload, field_keys)

                    if found:
                        return found

                from_preview = cls._description_from_preview(
                    str(excerpt.get("preview") or ""),
                    product_code=product_code,
                )

                if from_preview:
                    return from_preview

        for item in reversed(list(previous_messages or [])):
            role = ChatConversationContextService.message_role(item).lower()

            if role not in {"assistant", "ai"}:
                continue

            content = ChatConversationContextService.message_content(item)
            from_content = cls._description_from_preview(
                content,
                product_code=product_code,
            )

            if from_content:
                return from_content

            metadata = ChatConversationContextService.message_metadata(item)
            humanized = metadata.get("humanizedSummary")

            if isinstance(humanized, dict):
                lines = humanized.get("linhas") or []

                for line in lines:
                    text = str(line or "").strip()

                    if text and len(text) >= 12 and not cls._looks_like_insight_noise(text):
                        return text

        return None

    @classmethod
    def _description_from_tool_calls(
        cls,
        message: Any,
        *,
        field_keys: set[str],
        product_code: str | None,
    ) -> str | None:
        metadata = ChatConversationContextService.message_metadata(message)
        tool_calls = metadata.get("toolCalls")

        if not isinstance(tool_calls, list) and isinstance(message, dict):
            tool_calls = message.get("toolCalls")

        if not isinstance(tool_calls, list):
            return None

        for tool in tool_calls:
            if not isinstance(tool, dict):
                continue

            tool_meta = tool.get("metadata") if isinstance(tool.get("metadata"), dict) else {}

            table = tool_meta.get("tablePresentation")

            if isinstance(table, dict):
                for row in table.get("rows") or []:
                    if not isinstance(row, dict):
                        continue

                    found = cls._description_from_mapping(row, field_keys)

                    if found:
                        return found

            for key in ("responsePreview", "data", "result", "payload"):
                payload = tool_meta.get(key)

                if isinstance(payload, str) and payload.strip().startswith("{"):
                    try:
                        import json

                        payload = json.loads(payload)
                    except Exception:
                        payload = None

                if isinstance(payload, dict):
                    # Envelope api-delpi: data.product.description
                    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
                    product = data.get("product") if isinstance(data, dict) else None

                    if isinstance(product, dict):
                        found = cls._description_from_mapping(product, field_keys)

                        if found:
                            return found

                    found = cls._description_from_mapping(payload, field_keys)

                    if found:
                        return found

            data_answer = tool_meta.get("dataAnswer")

            if isinstance(data_answer, dict):
                summary = data_answer.get("summary")

                if isinstance(summary, dict):
                    answer = str(summary.get("answer") or "").strip()

                    if answer and "ipi" not in answer.lower() and len(answer) >= 12:
                        return answer

        return None

    @classmethod
    def _description_from_mapping(
        cls,
        payload: dict[str, Any],
        field_keys: set[str],
    ) -> str | None:
        for key, value in payload.items():
            compact = ChatMessageNormalizationService.strip_accents(str(key).lower())

            if compact in field_keys:
                text = str(value or "").strip()

                if text and len(text) >= 3:
                    return text

            if isinstance(value, dict):
                nested = cls._description_from_mapping(value, field_keys)

                if nested:
                    return nested

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        nested = cls._description_from_mapping(item, field_keys)

                        if nested:
                            return nested

        return None

    @classmethod
    def _looks_like_insight_noise(cls, text: str) -> bool:
        low = ChatMessageNormalizationService.strip_accents(str(text or "").lower())
        noise = (
            "ipi_rate",
            "ipi rate",
            "media quantity",
            "package quantity",
            "pontos de atencao",
            "valor zerado",
            "total de **",
            "cofins",
            "registros",
        )
        return any(token in low for token in noise)

    @classmethod
    def _description_from_preview(
        cls,
        preview: str,
        *,
        product_code: str | None,
    ) -> str | None:
        text = str(preview or "").strip()

        if not text or len(text) < 12:
            return None

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        markers = ("descrição", "descricao", "b1_desc", "nome")

        for line in lines:
            if cls._looks_like_insight_noise(line):
                continue

            low = ChatMessageNormalizationService.strip_accents(line.lower())

            if any(marker in low for marker in markers) and ":" in line:
                value = line.split(":", 1)[1].strip(" *")

                if value and len(value) >= 3 and not cls._looks_like_insight_noise(value):
                    return value

        for line in lines:
            if cls._looks_like_insight_noise(line):
                continue

            compact = line.replace("*", "").strip()

            if product_code and product_code in compact and len(compact) < 40:
                continue

            if len(compact) >= 20 and not compact.lower().startswith(
                ("o que você", "pontos de", "total de", "nenhum")
            ):
                return compact

        return None
