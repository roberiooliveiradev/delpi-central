class ResponseEvaluationSuggestionService:
    def build_suggestions(
        self,
        *,
        score: int,
        verdict: str,
        message_metadata: dict | None,
        user_question: str | None,
        assistant_answer: str,
    ) -> dict:
        metadata = message_metadata or {}
        sources = metadata.get("sources") or []
        guidelines = metadata.get("adminGuidelines") or []
        tool_calls = metadata.get("toolCalls") or []
        rag = metadata.get("rag") or {}

        suggestions: dict = {
            "documents": [],
            "guidelines": [],
            "notes": [],
        }

        question_preview = self._truncate(user_question or "", 160)
        answer_preview = self._truncate(assistant_answer or "", 160)

        if not sources:
            suggestions["documents"].append(
                {
                    "type": "create_or_expand_knowledge",
                    "priority": "high" if verdict == "unhelpful" else "medium",
                    "reason": "A resposta não recuperou fontes documentais no RAG.",
                    "suggestedTitle": question_preview or "Novo documento global",
                    "suggestedAction": (
                        "Adicionar ou ampliar documento na base global sobre o tema da pergunta."
                    ),
                }
            )
        elif verdict in {"unhelpful", "neutral"} and score <= 3:
            for source in sources[:3]:
                suggestions["documents"].append(
                    {
                        "type": "improve_document",
                        "priority": "high" if verdict == "unhelpful" else "medium",
                        "documentId": source.get("documentId"),
                        "title": source.get("title"),
                        "sourceType": source.get("sourceType"),
                        "reason": (
                            "Fontes foram usadas, mas a resposta recebeu avaliação baixa."
                        ),
                        "suggestedAction": (
                            "Revisar conteúdo, metadados curadoriais ou reindexar o documento."
                        ),
                    }
                )

        if not guidelines:
            suggestions["guidelines"].append(
                {
                    "type": "create_guideline",
                    "priority": "high" if verdict == "unhelpful" else "medium",
                    "reason": "Nenhuma diretriz administrativa foi aplicada nesta resposta.",
                    "suggestedAction": (
                        "Criar diretriz global alinhada ao tom e às regras esperadas para este tema."
                    ),
                    "suggestedTopic": question_preview or None,
                }
            )
        elif verdict in {"unhelpful", "neutral"} and score <= 3:
            for guideline in guidelines[:3]:
                suggestions["guidelines"].append(
                    {
                        "type": "review_guideline",
                        "priority": "medium",
                        "guidelineId": guideline.get("id"),
                        "title": guideline.get("title"),
                        "category": guideline.get("category"),
                        "reason": "Diretrizes estavam ativas, mas a resposta não atendeu à expectativa.",
                        "suggestedAction": "Revisar conteúdo publicado ou reforçar prioridade da diretriz.",
                    }
                )

        if tool_calls:
            suggestions["notes"].append(
                {
                    "type": "review_tool_usage",
                    "reason": f"A resposta executou {len(tool_calls)} tool(s).",
                    "suggestedAction": (
                        "Validar se os dados retornados pelas ferramentas foram usados corretamente."
                    ),
                }
            )

        if rag.get("enabled") is False:
            suggestions["notes"].append(
                {
                    "type": "rag_disabled",
                    "reason": "RAG estava desabilitado no contexto desta resposta.",
                    "suggestedAction": "Confirmar se o escopo da sessão deveria incluir busca documental.",
                }
            )

        if verdict == "helpful" and score >= 4 and sources:
            suggestions["notes"].append(
                {
                    "type": "positive_pattern",
                    "reason": "Resposta bem avaliada com fontes documentais.",
                    "suggestedAction": (
                        "Considere replicar estrutura de conhecimento/diretrizes desta interação."
                    ),
                }
            )

        if not question_preview:
            suggestions["notes"].append(
                {
                    "type": "missing_user_question",
                    "reason": "Não foi possível identificar a pergunta do usuário imediatamente anterior.",
                    "suggestedAction": (
                        "Abra a sessão completa para contextualizar a avaliação."
                    ),
                }
            )
        else:
            suggestions["notes"].append(
                {
                    "type": "context_snapshot",
                    "userQuestionPreview": question_preview,
                    "answerPreview": answer_preview,
                }
            )

        return suggestions

    def score_to_verdict(self, score: int) -> str:
        if score >= 4:
            return "helpful"

        if score == 3:
            return "neutral"

        return "unhelpful"

    def _truncate(self, value: str, max_chars: int) -> str:
        normalized = " ".join(str(value or "").split())

        if len(normalized) <= max_chars:
            return normalized

        return f"{normalized[: max_chars - 1].rstrip()}…"
