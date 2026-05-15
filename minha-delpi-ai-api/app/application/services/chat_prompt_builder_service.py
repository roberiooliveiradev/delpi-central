class ChatPromptBuilderService:
    def __init__(self, prompt_policy_service):
        self.prompt_policy_service = prompt_policy_service

    def build_messages(
        self,
        *,
        history,
        current_message: str,
        rag_context: str,
        tool_context: str,
        project_prompt: str | None = None,
        agent_prompt: str | None = None,
        admin_guidelines_prompt: str | None = None,
        attachments: list[dict] | None = None,
    ) -> list[dict]:
        base_prompt = self.prompt_policy_service.build_contextual_prompt(
            rag_context=rag_context,
            tool_context=tool_context,
        )

        if admin_guidelines_prompt:
            base_prompt = (
                f"{base_prompt}\n\n"
                f"{admin_guidelines_prompt}"
            )

        if project_prompt:
            base_prompt = (
                f"{base_prompt}\n\n"
                "Contexto e instruções do projeto atual:\n"
                f"{project_prompt}"
            )

        if agent_prompt:
            base_prompt = (
                f"{base_prompt}\n\n"
                "Instruções do agente selecionado:\n"
                f"{agent_prompt}"
            )

        if attachments:
            attachment_lines = "\n".join(
                f"- {item.get('original_filename')} ({item.get('content_type') or 'tipo desconhecido'})"
                for item in attachments
            )
            base_prompt = (
                f"{base_prompt}\n\n"
                "Arquivos anexados pelo usuário nesta mensagem:\n"
                f"{attachment_lines}\n"
                "Observação: nesta etapa os arquivos estão vinculados à mensagem, "
                "o conteúdo será usado pelo RAG quando estiver indexado."
            )

        messages = [
            {
                "role": "system",
                "content": base_prompt,
            }
        ]

        for item in history:
            if item.role not in {"user", "assistant", "system"}:
                continue

            messages.append(
                {
                    "role": item.role,
                    "content": item.content,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": current_message,
            }
        )

        return messages
