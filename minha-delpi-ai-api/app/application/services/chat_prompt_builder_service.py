_FAST_PATH_SYSTEM_PROMPT = (
    "Você é o assistente Minha DELPI. "
    "Responda de forma breve e cordial em português. "
    "Use só o contexto desta conversa; não invente dados, permissões ou módulos. "
    "Conclusão primeiro; se faltar informação, diga claramente."
)


class ChatPromptBuilderService:
    def __init__(self, prompt_policy_service):
        self.prompt_policy_service = prompt_policy_service

    def _assistant_identity_policy_addon(self, current_message: str) -> str:
        from app.application.services.chat_assistant_identity_service import (
            ChatAssistantIdentityService,
        )

        if not ChatAssistantIdentityService.is_assistant_identity_question(current_message):
            return ""

        return (
            "\n\n"
            + self.prompt_policy_service._load_policy(
                "chat-assistant-identity.md",
                "Apresente-se de forma humana; não peça e-mail só por quem você é.",
            )
        )

    def _capabilities_policy_addon(self, current_message: str) -> str:
        from app.application.services.chat_capabilities_service import (
            ChatCapabilitiesService,
        )

        if not ChatCapabilitiesService.is_capabilities_question(current_message):
            return ""

        return (
            "\n\n"
            + self.prompt_policy_service._load_policy(
                "chat-capabilities.md",
                "Quando perguntarem suas capacidades, liste ferramentas e actions autorizadas.",
            )
        )

    def _technical_description_policy_addon(self, current_message: str) -> str:
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if not ChatTechnicalDescriptionIntentService.requires_normas_knowledge(current_message):
            return ""

        return (
            "\n\n"
            + self.prompt_policy_service._load_policy(
                "technical-description-normas.md",
                "Use Normas_Tecnicas_DELPI.md para explicar descrições técnicas de matérias-primas.",
            )
        )

    def build_fast_path_messages(
        self,
        *,
        current_message: str,
        history: list | None = None,
        skills: dict | None = None,
    ) -> list[dict]:
        system_prompt = _FAST_PATH_SYSTEM_PROMPT
        skill_sections = self.prompt_policy_service.build_active_skill_policy_sections(
            skills
        )

        if skill_sections:
            system_prompt = f"{system_prompt}\n\n" + "\n\n".join(skill_sections)

        messages = [{"role": "system", "content": system_prompt}]

        for item in history or []:
            if item.role in {"user", "assistant"}:
                messages.append({"role": item.role, "content": item.content})

        messages.append({"role": "user", "content": current_message})
        return messages

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
        attachment_context: str | None = None,
        history_summary: str | None = None,
        operational_mode: bool = False,
        analysis_mode: bool = False,
        data_interpretation_mode: bool = False,
        text_task_mode: bool = False,
        user_context: str | None = None,
        skills: dict | None = None,
    ) -> list[dict]:
        base_prompt = self.prompt_policy_service.build_contextual_prompt(
            rag_context=rag_context,
            tool_context=tool_context,
            operational_mode=operational_mode,
            analysis_mode=analysis_mode,
            data_interpretation_mode=data_interpretation_mode,
            text_task_mode=text_task_mode,
            skills=skills,
        )
        base_prompt += self._assistant_identity_policy_addon(current_message)
        base_prompt += self._capabilities_policy_addon(current_message)
        base_prompt += self._technical_description_policy_addon(current_message)

        if user_context:
            base_prompt = f"{base_prompt}\n\n{user_context}"

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

        if history_summary:
            base_prompt = (
                f"{base_prompt}\n\n"
                "Resumo da conversa anterior:\n"
                f"{history_summary}"
            )

        if attachment_context:
            base_prompt = f"{base_prompt}\n\n{attachment_context}"
        elif attachments:
            attachment_lines = "\n".join(
                f"- {item.get('original_filename')} ({item.get('content_type') or 'tipo desconhecido'})"
                for item in attachments
            )
            base_prompt = (
                f"{base_prompt}\n\n"
                "Arquivos anexados pelo usuário nesta mensagem:\n"
                f"{attachment_lines}\n"
                "Observação: o conteúdo indexado também pode aparecer nas fontes RAG."
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
