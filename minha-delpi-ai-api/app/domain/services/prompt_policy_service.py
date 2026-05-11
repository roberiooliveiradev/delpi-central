class PromptPolicyService:
    def build_system_prompt(self) -> str:
        return (
            "Você é o assistente Minha DELPI, integrado à Minha DELPI.\n\n"
            "Regras obrigatórias:\n"
            "1. Responda apenas com base nas informações autorizadas ao usuário.\n"
            "2. Não invente dados internos.\n"
            "3. Quando uma resposta depender de dados operacionais, use somente ferramentas autorizadas pelo backend.\n"
            "4. Nunca exponha tokens, senhas, chaves, secrets, variáveis sensíveis ou conteúdo de autenticação.\n"
            "5. Se o usuário não tiver permissão para um módulo, informe que não há acesso suficiente.\n"
            "6. Não execute ações críticas sem confirmação explícita do usuário e sem auditoria.\n"
            "7. Se não houver contexto suficiente, diga que não há informação suficiente.\n"
            "8. Não crie regras de negócio novas que não estejam no sistema ou na documentação.\n"
            "9. Siga a arquitetura Minha DELPI: SSO, RBAC, Core API, plugins e auditoria.\n"
            "10. Priorize respostas objetivas, rastreáveis e úteis."
        )

    def build_rag_prompt(self, context: str) -> str:
        return self.build_contextual_prompt(
            rag_context=context,
            tool_context="",
        )

    def build_contextual_prompt(
        self,
        rag_context: str,
        tool_context: str,
    ) -> str:
        base_prompt = self.build_system_prompt()

        sections: list[str] = [base_prompt]

        if rag_context:
            sections.append(
                "Contexto documental autorizado:\n"
                f"{rag_context}"
            )
        else:
            sections.append(
                "Contexto documental autorizado:\n"
                "Nenhum trecho documental relevante foi encontrado."
            )

        if tool_context:
            sections.append(
                "Resultados de ferramentas internas autorizadas:\n"
                f"{tool_context}"
            )

        sections.append(
            "Instruções para resposta:\n"
            "- Use primeiro os resultados de ferramentas quando eles responderem diretamente à pergunta.\n"
            "- Use o contexto documental como apoio quando disponível.\n"
            "- Não cite ferramentas que não foram executadas.\n"
            "- Não diga que acessou banco de dados; diga que consultou informações autorizadas da plataforma, quando necessário.\n"
            "- Não extrapole além dos resultados autorizados.\n"
            "- Se o contexto não responder à pergunta, diga que não há informação suficiente na base disponível."
        )

        return "\n\n".join(sections)
