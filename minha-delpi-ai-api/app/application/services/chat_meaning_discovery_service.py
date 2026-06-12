from uuid import UUID

from app.domain.services.chat_term_extraction_service import ChatTermExtractionService
from app.domain.services.chat_web_meaning_research_service import (
    ChatWebMeaningResearchService,
)
from app.infrastructure.config.settings import Settings

_MEANING_MAX_CHARS = 500
_MAX_SOURCES = 3


class ChatMeaningDiscoveryService:
    """Descobre o significado de termos desconhecidos (playbook §9, §11, §34).

    Cascata: glossário interno → (autorizado) pesquisa web pública → candidato
    pendente para revisão. Tudo gated por flag e best-effort (SAVEPOINT na escrita).
    """

    def __init__(
        self,
        *,
        glossary_service=None,
        candidate_service=None,
        web_search_gateway=None,
    ):
        if glossary_service is None:
            from app.application.services.chat_glossary_retrieval_service import (
                ChatGlossaryRetrievalService,
            )

            glossary_service = ChatGlossaryRetrievalService()

        if candidate_service is None:
            from app.application.services.chat_knowledge_candidate_service import (
                ChatKnowledgeCandidateService,
            )

            candidate_service = ChatKnowledgeCandidateService()

        self.glossary_service = glossary_service
        self.candidate_service = candidate_service
        self._web_search_gateway = web_search_gateway

    def _web_gateway(self):
        if self._web_search_gateway is not None:
            return self._web_search_gateway

        from app.infrastructure.gateways.web_search_http_gateway import (
            WebSearchHttpGateway,
        )

        self._web_search_gateway = WebSearchHttpGateway()
        return self._web_search_gateway

    def research_web_meaning(self, term: str, *, message: str | None = None) -> dict | None:
        """Pesquisa significado público na web (gated). Retorna {meaning, sources}."""
        from app.application.services.chat_platform_runtime_access import learning_flag

        if not learning_flag("learningGlossaryWebMeaning"):
            return None

        if not ChatWebMeaningResearchService.is_eligible(term, message=message):
            return None

        try:
            payload = self._web_gateway().search(
                ChatWebMeaningResearchService.build_query(term),
                max_results=4,
            )
        except Exception:
            return None

        if not isinstance(payload, dict):
            return None

        try:
            from app.domain.services.chat_web_search_source_evaluation_service import (
                ChatWebSearchSourceEvaluationService,
            )

            payload = ChatWebSearchSourceEvaluationService.enrich_payload(payload) or payload
        except Exception:
            pass

        results = payload.get("results") if isinstance(payload.get("results"), list) else []

        if not results:
            return None

        top = results[0]
        snippet = str(top.get("snippet") or top.get("title") or "").strip()

        if not snippet:
            return None

        sources = [
            str(item.get("url"))
            for item in results[:_MAX_SOURCES]
            if isinstance(item, dict) and item.get("url")
        ]

        return {"meaning": snippet[:_MEANING_MAX_CHARS], "sources": sources}

    def capture_unknown_term_from_turn(
        self,
        *,
        message: str,
        project_id: str | None = None,
        created_by: str | None = None,
    ) -> dict | None:
        """Detecta "o que é X?"; se X for desconhecido internamente, cria candidato."""
        from app.application.services.chat_platform_runtime_access import (
            learning_pipeline_settings,
        )

        learning = learning_pipeline_settings()
        if not (
            learning.get("learningEnabled") and learning.get("learningGlossaryCapture")
        ):
            return None

        if learning.get("learningTermConfirmationEnabled"):
            return None

        term = ChatTermExtractionService.detect_definition_question(message or "")

        if not term:
            return None

        project_uuid = self._as_uuid(project_id)

        # Já existe no glossário interno? Então não há o que aprender.
        if self.glossary_service.lookup_internal(term, project_id=project_uuid) is not None:
            return None

        web = self.research_web_meaning(term, message=message)

        candidate = {
            "candidateType": "term_definition",
            "term": term,
            "inputText": (message or "")[:4000],
            "proposedMeaning": web.get("meaning") if web else None,
            "confidence": 0.3 if web else 0.1,
            "scope": "project" if project_uuid else "global",
            "source": "glossary_web" if web else "glossary_unknown_term",
        }

        if project_uuid:
            candidate["projectId"] = str(project_uuid)

        if web and web.get("sources"):
            candidate["evidence"] = {"sources": web["sources"][:_MAX_SOURCES]}

        from app.extensions.db import db

        try:
            with db.session.begin_nested():
                return self.candidate_service.register_candidate(
                    candidate,
                    created_by=created_by,
                )
        except Exception:
            return None

    @staticmethod
    def _as_uuid(value: str | None) -> UUID | None:
        if not value:
            return None
        try:
            return UUID(str(value))
        except (ValueError, TypeError):
            return None
