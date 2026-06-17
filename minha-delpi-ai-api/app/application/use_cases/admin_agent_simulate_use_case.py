from uuid import UUID

from app.application.services.admin_guideline_prompt_service import AdminGuidelinePromptService
from app.application.services.agent_specialization_service import AgentSpecializationService
from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.domain.services.tool_selection_service import ToolSelectionService
from app.infrastructure.config.settings import Settings


class AdminAgentSimulateUseCase:
    def __init__(
        self,
        *,
        rag_context_service,
        guideline_prompt_service: AdminGuidelinePromptService,
        chat_agent_repository: ChatAgentRepositoryPort,
        chat_session_repository: ChatSessionRepositoryPort,
        tool_selection_service: ToolSelectionService | None = None,
        chat_tool_context_service=None,
        llm_gateway=None,
    ):
        self.rag_context_service = rag_context_service
        self.guideline_prompt_service = guideline_prompt_service
        self.chat_agent_repository = chat_agent_repository
        self.chat_session_repository = chat_session_repository
        self.tool_selection_service = tool_selection_service or ToolSelectionService()
        self.chat_tool_context_service = chat_tool_context_service
        self.llm_gateway = llm_gateway
        self.prompt_builder_service = ChatPromptBuilderService(PromptPolicyService())
        self.specialization_service = AgentSpecializationService()

    def execute(
        self,
        *,
        question: str,
        agent_id: str | None = None,
        document_id: str | None = None,
        session_id: str | None = None,
        generate_answer: bool = False,
        execute_tools_in_sandbox: bool = False,
        user_id: str | None = None,
        access_token: str | None = None,
        agent_prompt_override: str | None = None,
        agent_metadata_override: dict | None = None,
        skip_enabled_check: bool = False,
        previous_messages: list[dict] | None = None,
    ) -> dict:
        normalized_question = str(question or "").strip()

        if not normalized_question:
            raise ValueError("question is required")

        if agent_prompt_override is not None or agent_metadata_override is not None:
            agent_prompt = agent_prompt_override
            agent_meta = {
                "id": agent_id,
            }
            specialization = self.specialization_service.parse(
                (agent_metadata_override or {}).get("specialization")
            )
        else:
            agent_prompt, agent_meta, specialization = self._resolve_agent(
                agent_id=agent_id,
                user_id=user_id,
                skip_enabled_check=skip_enabled_check,
            )

        filters: dict = {"include_global": True}

        if document_id:
            filters["document_id"] = str(document_id)

        filters = self.specialization_service.build_rag_filters(specialization, filters)

        rag = self.rag_context_service.build_context(normalized_question, filters=filters)
        guideline_categories = (specialization or {}).get("guidelineCategories")
        guidelines_prompt, applied_guidelines = (
            self.guideline_prompt_service.build_active_guidelines_prompt(
                categories=guideline_categories,
            )
        )
        history = self._load_session_history(session_id=session_id, user_id=user_id)

        if previous_messages is not None:
            history = previous_messages

        tool_context_payload, planned_tool_calls = self._build_tool_context(
            question=normalized_question,
            user_id=user_id,
            access_token=access_token,
            specialization=specialization,
            execute_tools_in_sandbox=execute_tools_in_sandbox,
            previous_messages=history,
        )
        tool_context = str(tool_context_payload.get("context") or "")
        analysis_mode = ChatIntelligencePipelineService.analysis_mode_from_tool_context(
            tool_context_payload,
        )

        full_messages = self.prompt_builder_service.build_messages(
            history=history,
            current_message=normalized_question,
            rag_context=rag["context"],
            tool_context=tool_context,
            agent_prompt=agent_prompt,
            admin_guidelines_prompt=guidelines_prompt,
            analysis_mode=analysis_mode,
        )

        without_guidelines_messages = self.prompt_builder_service.build_messages(
            history=history,
            current_message=normalized_question,
            rag_context=rag["context"],
            tool_context=tool_context,
            agent_prompt=agent_prompt,
            admin_guidelines_prompt="",
            analysis_mode=analysis_mode,
        )

        without_rag_messages = self.prompt_builder_service.build_messages(
            history=history,
            current_message=normalized_question,
            rag_context="",
            tool_context=tool_context,
            agent_prompt=agent_prompt,
            admin_guidelines_prompt=guidelines_prompt,
            analysis_mode=analysis_mode,
        )

        system_prompt = self._system_prompt_from_messages(full_messages)
        answer_preview = None

        if generate_answer and self.llm_gateway:
            answer_preview = self.llm_gateway.generate(full_messages)

        chunks = self._chunks_from_sources(rag.get("sources") or [], rag.get("context") or "")

        return {
            "question": normalized_question,
            "agent": agent_meta,
            "specialization": specialization,
            "score": self._top_source_score(rag.get("sources") or []),
            "answerPreview": answer_preview
            or self._structural_answer_preview(
                chunks=chunks,
                applied_guidelines=applied_guidelines,
                planned_tool_calls=planned_tool_calls,
            ),
            "appliedGuidelines": self._guideline_cards(applied_guidelines),
            "matchedDocuments": self._matched_documents(rag.get("sources") or []),
            "chunks": chunks,
            "plannedToolCalls": planned_tool_calls,
            "finalPrompt": {
                "systemPrompt": system_prompt,
                "messages": full_messages,
                "preview": self._safe_preview(system_prompt, limit=4000),
            },
            "comparison": {
                "withGuidelines": self._prompt_comparison(
                    messages=full_messages,
                    enabled=len(applied_guidelines) > 0,
                    summary=self._guideline_summary(applied_guidelines),
                    extra={"guidelineCount": len(applied_guidelines)},
                ),
                "withoutGuidelines": self._prompt_comparison(
                    messages=without_guidelines_messages,
                    enabled=False,
                    summary=(
                        "Sem diretrizes administrativas, o agente usaria apenas políticas base, "
                        "RAG e instruções do agente."
                    ),
                    extra={"guidelineCount": 0},
                ),
                "withRag": self._prompt_comparison(
                    messages=full_messages,
                    enabled=bool(rag.get("context")),
                    summary=self._rag_summary(chunks, rag.get("sources") or []),
                    extra={
                        "chunkCount": len(chunks),
                        "documentCount": len(rag.get("sources") or []),
                    },
                ),
                "withoutRag": self._prompt_comparison(
                    messages=without_rag_messages,
                    enabled=False,
                    summary="Sem RAG, o prompt não incluiria trechos documentais recuperados.",
                    extra={"chunkCount": 0, "documentCount": 0},
                ),
            },
            "sessionHistory": [
                {
                    "role": getattr(item, "role", None),
                    "contentPreview": self._safe_preview(
                        str(getattr(item, "content", None) or ""),
                        limit=240,
                    ),
                }
                for item in history
            ],
            "debugContext": {
                "question": normalized_question,
                "sessionId": session_id,
                "historyMessageCount": len(history),
                "guidelineCount": len(applied_guidelines),
                "documentCount": len(rag.get("sources") or []),
                "chunkCount": len(chunks),
                "plannedToolCount": len(planned_tool_calls),
                "toolsExecuted": any(
                    item.get("status") == "executed" for item in planned_tool_calls
                ),
                "executeToolsInSandbox": execute_tools_in_sandbox,
                "generateAnswer": generate_answer,
                "filters": filters,
                "safeContextPreview": self._safe_preview(
                    "\n\n".join(
                        part
                        for part in [
                            rag.get("context") or "",
                            guidelines_prompt or "",
                            tool_context or "",
                        ]
                        if part
                    ),
                    limit=2600,
                ),
            },
        }

    def _load_session_history(
        self,
        *,
        session_id: str | None,
        user_id: str | None,
    ) -> list[dict]:
        if not session_id or not user_id:
            return []

        try:
            parsed_session_id = UUID(str(session_id))
        except ValueError:
            return []

        session = self.chat_session_repository.get_session_by_id(parsed_session_id)

        if not session or str(session.user_id) != str(user_id):
            return []

        messages = self.chat_session_repository.list_messages_by_session(parsed_session_id)
        tail = messages[-Settings.CHAT_HISTORY_MAX_MESSAGES :]

        return [message for message in tail if message.role in {"user", "assistant"}]

    def _build_tool_context(
        self,
        *,
        question: str,
        user_id: str | None,
        access_token: str | None,
        specialization: dict | None = None,
        execute_tools_in_sandbox: bool = False,
        previous_messages: list | None = None,
    ) -> tuple[dict, list[dict]]:
        if (
            execute_tools_in_sandbox
            and self.chat_tool_context_service
            and access_token
            and user_id
        ):
            allowed_tool_names = (specialization or {}).get("allowedTools")

            result = self.chat_tool_context_service.build_context(
                user_id=str(user_id),
                access_token=access_token,
                message=question,
                actions_enabled=True,
                allowed_tool_names=allowed_tool_names,
                previous_messages=previous_messages,
            )

            tool_calls = [
                {
                    "name": item.get("name"),
                    "arguments": item.get("arguments") or {},
                    "reason": item.get("reason"),
                    "status": "executed",
                    "sandbox": True,
                    "metadata": item.get("metadata"),
                }
                for item in (result.get("toolCalls") or [])
            ]

            return result, tool_calls

        return {"context": ""}, self._planned_tool_calls(question)

    def _resolve_agent(
        self,
        *,
        agent_id: str | None,
        user_id: str | None,
        skip_enabled_check: bool = False,
    ) -> tuple[str | None, dict | None, dict | None]:
        if not agent_id:
            return None, None, None

        try:
            parsed_agent_id = UUID(str(agent_id))
        except ValueError:
            return None, None, None

        agent = None

        if user_id:
            loaded = self.chat_agent_repository.get_accessible_by_id(
                parsed_agent_id,
                UUID(str(user_id)),
            )

            if not loaded:
                return None, None, None

            agent, _role = loaded

            if not skip_enabled_check and not agent.enabled:
                return None, None, None
        elif skip_enabled_check:
            agent = self.chat_agent_repository.get_by_id(parsed_agent_id)
        else:
            agent = self.chat_agent_repository.get_enabled_by_id(parsed_agent_id)

        if not agent:
            return None, None, None

        specialization = self.specialization_service.parse((agent.metadata or {}).get("specialization"))

        return agent.system_prompt, {
            "id": str(agent.id),
            "name": agent.name,
        }, specialization

    def _planned_tool_calls(self, question: str) -> list[dict]:
        selected = self.tool_selection_service.select_tools(question)

        return [
            {
                "name": item.get("name"),
                "arguments": item.get("arguments") or {},
                "reason": item.get("reason"),
                "status": "planned",
            }
            for item in selected
        ]

    def _chunks_from_sources(self, sources: list[dict], context: str) -> list[dict]:
        chunks = []

        for index, source in enumerate(sources, start=1):
            preview = ""

            if context:
                marker = f"[Fonte {index}]"
                start = context.find(marker)
                if start >= 0:
                    end = context.find("[Fonte", start + len(marker))
                    preview = context[start:end if end > start else start + 700].strip()

            chunks.append(
                {
                    "id": source.get("id") or f"source-{index}",
                    "documentId": source.get("documentId") or source.get("id"),
                    "title": source.get("title") or "Documento sem título",
                    "sourceType": source.get("sourceType"),
                    "sourceRef": source.get("sourceRef"),
                    "score": float(source.get("score") or 0),
                    "preview": self._safe_preview(preview or source.get("title") or "", limit=700),
                }
            )

        return chunks

    def _matched_documents(self, sources: list[dict]) -> list[dict]:
        return [
            {
                "id": str(item.get("documentId") or item.get("id") or ""),
                "title": item.get("title") or "Documento sem título",
                "score": float(item.get("score") or 0),
                "sourceType": item.get("sourceType"),
                "sourceRef": item.get("sourceRef"),
            }
            for item in sources
        ]

    def _guideline_cards(self, guidelines: list[dict]) -> list[dict]:
        return [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "status": item.get("status"),
                "description": item.get("description"),
            }
            for item in guidelines
        ]

    def _top_source_score(self, sources: list[dict]) -> float:
        if not sources:
            return 0.0

        return max(float(item.get("score") or 0) for item in sources)

    def _system_prompt_from_messages(self, messages: list[dict]) -> str:
        for message in messages:
            if message.get("role") == "system":
                return str(message.get("content") or "")

        return ""

    def _prompt_comparison(
        self,
        *,
        messages: list[dict],
        enabled: bool,
        summary: str,
        extra: dict,
    ) -> dict:
        system_prompt = self._system_prompt_from_messages(messages)

        return {
            "enabled": enabled,
            "summary": summary,
            "systemPromptPreview": self._safe_preview(system_prompt, limit=1200),
            **extra,
        }

    def _guideline_summary(self, guidelines: list[dict]) -> str:
        if not guidelines:
            return "Nenhuma diretriz administrativa ativa seria aplicada."

        titles = [str(item.get("title") or "Diretriz") for item in guidelines[:3]]
        suffix = f" e mais {len(guidelines) - 3}" if len(guidelines) > 3 else ""

        return f"Aplicaria {len(guidelines)} diretriz(es): {', '.join(titles)}{suffix}."

    def _rag_summary(self, chunks: list[dict], sources: list[dict]) -> str:
        if not chunks:
            return "Nenhum chunk documental seria incluído no prompt."

        return (
            f"Incluiria {len(chunks)} trecho(s) de "
            f"{len(sources)} documento(s) no contexto do agente."
        )

    def _structural_answer_preview(
        self,
        *,
        chunks: list[dict],
        applied_guidelines: list[dict],
        planned_tool_calls: list[dict],
    ) -> str:
        lines = [
            "Prévia estrutural (sem chamada ao LLM).",
            f"Diretrizes ativas: {len(applied_guidelines)}.",
            f"Documentos recuperados: {len(chunks)}.",
            f"Tools previstas: {len(planned_tool_calls)}.",
        ]

        if planned_tool_calls:
            names = ", ".join(str(item.get("name")) for item in planned_tool_calls[:5])
            lines.append(f"Tools: {names}.")

        if chunks:
            titles = ", ".join(str(item.get("title")) for item in chunks[:3])
            lines.append(f"Fontes: {titles}.")

        lines.append("Ative 'Gerar resposta com LLM' para simular a resposta final.")

        return "\n".join(lines)

    def _safe_preview(self, value: str, *, limit: int) -> str:
        normalized = " ".join(str(value or "").split())

        if len(normalized) <= limit:
            return normalized

        return f"{normalized[:limit]}..."
