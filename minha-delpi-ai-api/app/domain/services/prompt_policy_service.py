from functools import lru_cache
from pathlib import Path

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class PromptPolicyService:
    POLICY_DIR = Path(__file__).resolve().parents[1] / "prompt_policies"

    EXTERNAL_ACTION_MARKERS = (
        "execute_external_action",
        "authorizedResult",
        "humanizedSummary",
        "technicalSummary",
        "statusCode",
    )

    HUMANIZED_DATA_MARKERS = (
        "dataAnswer",
        "dataCommentary",
        "presentationDecision",
        "narrativeInsight",
        "alertLevel",
        "riskLevel",
    )

    API_DELPI_MARKERS = (
        "api_delpi",
        "api-delpi",
        "/products/",
        "/engineering/lmps",
        "/supplies/stock-value",
        "/data/sql",
        "get_product_stock",
        "get_product_analyser",
        "list_lmps",
        "execute_readonly_sql",
    )

    PLATFORM_TOOL_MARKERS = (
        "get_current_user",
        "get_allowed_apps",
        "get_allowed_routes",
        "web_search",
    )

    PRODUCT_MARKERS = (
        "produto",
        "produtos",
        "estoque",
        "armazém",
        "armazem",
        "ncm",
        "último preço",
        "ultimo preco",
        "custo padrão",
        "custo padrao",
        "fornecedor",
        "fornecedores",
        "cliente",
        "clientes",
        "estrutura",
        "parents",
        "onde é usado",
        "preço",
        "preco",
        "pricing",
    )

    SQL_MARKERS = (
        "select ",
        " from ",
        " join ",
        " where ",
        " group by ",
        " order by ",
        "insert ",
        "update ",
        "delete ",
        "sql",
        "query",
    )

    SESSION_KNOWLEDGE_MARKERS = (
        "session_source",
        "attachmentId",
        "originalFilename",
        "chat_attachment",
    )

    PROJECT_SOURCE_MARKERS = (
        "escopo: project_source",
        "scope: project_source",
    )

    DRAWING_ANALYSIS_MARKERS = (
        "drawinganalysismode",
        "drawinganalysisexport",
        "drawinganalysis",
        "checklist completo",
        "relatório de análise",
        "relatorio de analise",
        "templatekey",
    )

    def build_system_prompt(self) -> str:
        return self._join_policy_sections(
            self._load_policy("base.md"),
            self._load_policy("context-engineering.md"),
            self._load_policy("chat-context-memory.md"),
        )

    def build_rag_prompt(self, context: str) -> str:
        return self.build_contextual_prompt(
            rag_context=context,
            tool_context="",
        )

    def build_active_skill_policy_sections(self, skills: dict | None) -> list[str]:
        """Políticas de skills ativas no runtime (chat comum ou agente), sem ação do usuário."""
        resolved_skills = skills or {}
        sections: list[str] = []

        if resolved_skills.get("sqlAuthoring"):
            from app.domain.skills.chat_skill_registry import ChatSkillRegistry, SQL_SKILL_KEY

            sql_policy = ChatSkillRegistry.get_policy_content(SQL_SKILL_KEY)
            sections.append(sql_policy or self._load_policy("sql-assistant-skill.md"))

        if resolved_skills.get("companyKnowledge"):
            from app.domain.skills.chat_skill_registry import (
                ChatSkillRegistry,
                COMPANY_KNOWLEDGE_SKILL_KEY,
            )

            company_policy = ChatSkillRegistry.get_policy_content(COMPANY_KNOWLEDGE_SKILL_KEY)
            sections.append(company_policy or self._load_policy("company-knowledge-skill.md"))

        if resolved_skills.get("drawingAnalysis"):
            from app.domain.skills.chat_skill_registry import (
                ChatSkillRegistry,
                DRAWING_ANALYSIS_SKILL_KEY,
            )

            drawing_policy = ChatSkillRegistry.get_policy_content(DRAWING_ANALYSIS_SKILL_KEY)
            sections.append(
                drawing_policy or self._load_policy("drawing-analysis-delpi-skill.md")
            )

        if resolved_skills.get("documentVision"):
            from app.domain.skills.chat_skill_registry import (
                ChatSkillRegistry,
                DOCUMENT_VISION_SKILL_KEY,
            )

            vision_policy = ChatSkillRegistry.get_policy_content(DOCUMENT_VISION_SKILL_KEY)
            sections.append(
                vision_policy or self._load_policy("document-vision-delpi-skill.md")
            )

        return [
            section.strip()
            for section in sections
            if section and section.strip()
        ]

    def build_contextual_prompt(
        self,
        rag_context: str,
        tool_context: str,
        *,
        operational_mode: bool = False,
        analysis_mode: bool = False,
        data_interpretation_mode: bool = False,
        text_task_mode: bool = False,
        email_writing_mode: bool = False,
        text_correction_mode: bool = False,
        skills: dict | None = None,
    ) -> str:
        sections: list[str] = [self.build_system_prompt()]
        resolved_skills = skills or {}

        if text_task_mode:
            sections.append(self._load_policy("administrative-writing.md"))
            sections.append(self._load_policy("text-specialist.md"))

        if email_writing_mode:
            sections.append(self._load_policy("email-writing.md"))

        if text_correction_mode:
            sections.append(self._load_policy("text-correction.md"))

        stream_texts = ChatAssistantContentService.load_stream()
        rag_header = str(stream_texts.get("ragContextHeader") or "Contexto documental autorizado:")
        rag_empty = str(
            stream_texts.get("ragEmptyContext")
            or "Nenhum trecho documental relevante foi encontrado."
        )
        tool_header = str(
            stream_texts.get("toolContextHeader")
            or "Resultados de ferramentas internas autorizadas:"
        )

        if rag_context:
            sections.append(f"{rag_header}\n{rag_context}")
        else:
            sections.append(f"{rag_header}\n{rag_empty}")

        if tool_context:
            sections.append(f"{tool_header}\n{tool_context}")

        sections.extend(
            self._response_policy_sections(
                rag_context=rag_context,
                tool_context=tool_context,
                skills=resolved_skills,
            )
        )

        sections.extend(self.build_active_skill_policy_sections(resolved_skills))

        if operational_mode:
            sections.append(self._load_policy("operational-agent.md"))

        if data_interpretation_mode:
            sections.append(self._load_policy("chat-data-interpretation.md"))
        elif analysis_mode:
            sections.append(self._load_policy("chat-analysis-insights.md"))

        return self._join_policy_sections(*sections)

    def _response_policy_sections(
        self,
        *,
        rag_context: str,
        tool_context: str,
        skills: dict | None = None,
    ) -> list[str]:
        resolved_skills = skills or {}
        sections = [self._load_policy("response-style.md")]

        normalized_rag_context = self._normalize(rag_context)
        normalized_tool_context = self._normalize(tool_context)

        if self._contains_any(normalized_tool_context, self.EXTERNAL_ACTION_MARKERS):
            sections.append(self._load_policy("external-actions.md"))

        if self._contains_any(normalized_tool_context, self.HUMANIZED_DATA_MARKERS):
            sections.append(self._load_policy("humanized-data-response.md"))

        if self._contains_any(normalized_tool_context, self.API_DELPI_MARKERS):
            sections.append(self._load_policy("api-delpi-routes.md"))

        if self._contains_any(normalized_tool_context, self.PLATFORM_TOOL_MARKERS):
            sections.append(self._load_policy("platform-tools.md"))

        if self._contains_any(normalized_tool_context, ("web_search",)):
            sections.append(self._load_policy("web-search-policy.md"))

        if self._contains_any(normalized_tool_context, self.PRODUCT_MARKERS):
            sections.append(self._load_policy("product-fields.md"))

        if self._contains_any(normalized_rag_context, self.SESSION_KNOWLEDGE_MARKERS):
            sections.append(self._load_policy("session-knowledge.md"))

        if self._contains_any(normalized_rag_context, self.PROJECT_SOURCE_MARKERS):
            sections.append(self._load_policy("project-sources-content.md"))

        if self._contains_any(normalized_tool_context, self.DRAWING_ANALYSIS_MARKERS):
            sections.append(self._load_policy("drawing-analysis-render-only.md"))

            if normalized_rag_context.strip():
                rag_policy = self._drawing_rag_normative_policy_file()
                sections.append(self._load_policy(rag_policy))

        if not resolved_skills.get("sqlAuthoring") and (
            self._contains_any(normalized_rag_context, self.SQL_MARKERS)
            or self._contains_any(normalized_tool_context, self.SQL_MARKERS)
        ):
            sections.append(self._load_policy("sql-knowledge.md"))

        return [section for section in sections if section]

    def _join_policy_sections(self, *sections: str) -> str:
        return "\n\n".join(
            section.strip()
            for section in sections
            if section and section.strip()
        )

    def _contains_any(self, value: str, markers: tuple[str, ...]) -> bool:
        return any(self._normalize(marker) in value for marker in markers)

    @classmethod
    def _drawing_rag_normative_policy_file(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                "drawing_query_intent",
                "ragNormative",
                "policyFile",
                default="drawing-analysis-rag-normative.md",
            )
        )

    def _normalize(self, value: str | None) -> str:
        return str(value or "").casefold()

    @classmethod
    @lru_cache(maxsize=32)
    def _load_policy(cls, filename: str) -> str:
        path = cls.POLICY_DIR / filename

        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError:
            return ""
