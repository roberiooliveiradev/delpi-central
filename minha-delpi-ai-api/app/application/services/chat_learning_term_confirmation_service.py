"""Confirmação de significado de termos — fluxo de aprendizado com human-in-the-loop."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.domain.services.chat_learning_term_ambiguity_service import (
    ChatLearningTermAmbiguityService,
)
from app.domain.services.chat_term_extraction_service import ChatTermExtractionService
from app.infrastructure.config.settings import Settings


class ChatLearningTermConfirmationService:
    def __init__(self, *, meaning_discovery_service=None, candidate_service=None):
        if meaning_discovery_service is None:
            from app.application.services.chat_meaning_discovery_service import (
                ChatMeaningDiscoveryService,
            )

            meaning_discovery_service = ChatMeaningDiscoveryService()

        if candidate_service is None:
            from app.application.services.chat_knowledge_candidate_service import (
                ChatKnowledgeCandidateService,
            )

            candidate_service = ChatKnowledgeCandidateService()

        self._meaning_discovery = meaning_discovery_service
        self._candidate_service = candidate_service

    @staticmethod
    def _enabled() -> bool:
        from app.application.services.chat_platform_runtime_access import (
            learning_pipeline_settings,
        )

        learning = learning_pipeline_settings()
        return bool(
            learning.get("learningEnabled")
            and learning.get("learningGlossaryCapture")
            and learning.get("learningTermConfirmationEnabled")
        )

    def try_build(
        self,
        *,
        message: str,
        workspace_context: dict | None,
        project_id: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any] | None:
        if not self._enabled():
            return None

        working_memory = (workspace_context or {}).get("workingMemory") or {}
        pending = ChatLearningTermAmbiguityService.get_pending(working_memory)

        if pending:
            return self._resolve_pending(
                message=message,
                pending=pending,
                project_id=project_id,
                created_by=created_by,
            )

        return self._build_definition_question(
            message=message,
            project_id=project_id,
        )

    def _build_definition_question(
        self,
        *,
        message: str,
        project_id: str | None,
    ) -> dict[str, Any] | None:
        term = ChatTermExtractionService.detect_definition_question(message or "")

        if not term:
            return None

        project_uuid = self._as_uuid(project_id)
        internal = self._meaning_discovery.glossary_service.lookup_internal(
            term,
            project_id=project_uuid,
        )

        if internal and internal.get("meaning"):
            return {
                "directAnswer": ChatLearningTermAmbiguityService.format_known_definition(
                    term=str(internal.get("term") or term),
                    meaning=str(internal.get("meaning")),
                ),
                "workingMemoryPatch": ChatLearningTermAmbiguityService.clear_pending_patch(),
                "pipelineStage": "learning_term_known",
                "skipRag": True,
            }

        web = self._meaning_discovery.research_web_meaning(term, message=message)
        proposed_meaning = web.get("meaning") if web else None
        confidence = 0.35 if proposed_meaning else 0.1
        sources = web.get("sources") if web else None

        if proposed_meaning and not ChatLearningTermAmbiguityService.needs_confirmation(
            confidence
        ):
            return None

        if proposed_meaning:
            direct_answer = ChatLearningTermAmbiguityService.format_proposed_meaning_prompt(
                term=term,
                meaning=proposed_meaning,
            )
        else:
            direct_answer = ChatLearningTermAmbiguityService.format_unknown_term_prompt(
                term=term,
            )

        return {
            "directAnswer": direct_answer,
            "workingMemoryPatch": ChatLearningTermAmbiguityService.build_pending_patch(
                term=term,
                proposed_meaning=proposed_meaning,
                confidence=confidence,
                sources=sources,
            ),
            "pipelineStage": "learning_term_confirmation",
            "skipRag": True,
        }

    def _resolve_pending(
        self,
        *,
        message: str,
        pending: dict,
        project_id: str | None,
        created_by: str | None,
    ) -> dict[str, Any] | None:
        term = str(pending.get("term") or "").strip()

        if not term:
            return None

        explicit_meaning = ChatLearningTermAmbiguityService.extract_explicit_meaning_for_term(
            message,
            term=term,
        )
        reply_kind = ChatLearningTermAmbiguityService.parse_confirmation_reply(message)

        if explicit_meaning:
            self._register_candidate(
                term=term,
                meaning=explicit_meaning,
                confidence=0.75,
                source="term_confirmation_corrected",
                project_id=project_id,
                created_by=created_by,
                input_text=message,
            )
            return {
                "directAnswer": ChatLearningTermAmbiguityService.format_confirmation_ack(
                    kind="corrected",
                    term=term,
                ),
                "workingMemoryPatch": ChatLearningTermAmbiguityService.clear_pending_patch(),
                "pipelineStage": "learning_term_confirmed",
                "skipRag": True,
            }

        if reply_kind == "confirm":
            proposed = str(pending.get("proposedMeaning") or "").strip()

            if not proposed:
                return {
                    "directAnswer": ChatLearningTermAmbiguityService.format_unknown_term_prompt(
                        term=term,
                    ),
                    "workingMemoryPatch": ChatLearningTermAmbiguityService.build_pending_patch(
                        term=term,
                        proposed_meaning=None,
                        confidence=float(pending.get("confidence") or 0.1),
                        sources=pending.get("sources"),
                    ),
                    "pipelineStage": "learning_term_confirmation",
                    "skipRag": True,
                }

            self._register_candidate(
                term=term,
                meaning=proposed,
                confidence=0.65,
                source="term_confirmation_accepted",
                project_id=project_id,
                created_by=created_by,
                input_text=message,
                evidence={"sources": pending.get("sources") or []},
            )
            return {
                "directAnswer": ChatLearningTermAmbiguityService.format_confirmation_ack(
                    kind="confirmed",
                    term=term,
                ),
                "workingMemoryPatch": ChatLearningTermAmbiguityService.clear_pending_patch(),
                "pipelineStage": "learning_term_confirmed",
                "skipRag": True,
            }

        if reply_kind == "reject":
            return {
                "directAnswer": ChatLearningTermAmbiguityService.format_confirmation_ack(
                    kind="rejected",
                    term=term,
                ),
                "workingMemoryPatch": ChatLearningTermAmbiguityService.clear_pending_patch(),
                "pipelineStage": "learning_term_rejected",
                "skipRag": True,
            }

        return None

    def _register_candidate(
        self,
        *,
        term: str,
        meaning: str,
        confidence: float,
        source: str,
        project_id: str | None,
        created_by: str | None,
        input_text: str,
        evidence: dict | None = None,
    ) -> None:
        project_uuid = self._as_uuid(project_id)
        candidate = {
            "candidateType": "term_definition",
            "term": term,
            "inputText": input_text[:4000],
            "proposedMeaning": meaning,
            "confidence": confidence,
            "scope": "project" if project_uuid else "global",
            "source": source,
        }

        if project_uuid:
            candidate["projectId"] = str(project_uuid)

        if evidence:
            candidate["evidence"] = evidence

        from app.extensions.db import db

        try:
            with db.session.begin_nested():
                self._candidate_service.register_candidate(
                    candidate,
                    created_by=created_by,
                )
        except Exception:
            return

    @staticmethod
    def _as_uuid(value: str | None) -> UUID | None:
        if not value:
            return None

        try:
            return UUID(str(value))
        except (ValueError, TypeError):
            return None
