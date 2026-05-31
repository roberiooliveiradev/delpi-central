from functools import lru_cache
from pathlib import Path

from app.infrastructure.content.content_service import ContentService


class PromptPolicyService:
    POLICY_DIR = Path(__file__).resolve().parents[1] / "prompt_policies"

    CONTEXT_ENGINEERING_POLICY_FALLBACK = """Engenharia de contexto:
- Responda com dados autorizados (ferramentas, RAG, sessão); não invente.
- Conclusão primeiro; detalhes em tópicos se necessário.
- Se faltar dado (código, OV, filial), peça esclarecimento em vez de adivinhar.
- Para capacidades, liste só o que esta sessão permite; não invente módulos ou permissões globais.
- Priorize resultados de ferramentas sobre texto genérico da internet."""

    BASE_POLICY_FALLBACK = """Você é o assistente Minha DELPI, integrado à plataforma Minha DELPI.
Seu objetivo é ajudar o usuário de forma clara, precisa e objetiva.

Regras obrigatórias:
1. Responda apenas com base nas informações autorizadas ao usuário.
2. Não invente dados. Se não tiver informação suficiente, diga claramente.
3. Quando precisar de dados operacionais, use ferramentas autorizadas pelo backend.
4. Nunca exponha tokens, senhas, chaves, secrets ou variáveis sensíveis.
5. Se o usuário não tiver permissão para um módulo, informe que não há acesso suficiente.
6. Não execute ações críticas sem confirmação explícita do usuário.
7. Não crie regras de negócio que não estejam no sistema ou na documentação.
8. Siga a arquitetura Minha DELPI: SSO, RBAC, Core API, plugins e auditoria.

Comportamento esperado:
- Se a pergunta for ambígua, peça esclarecimento ao invés de adivinhar.
- Seja proativo: se identificar informação relacionada útil, ofereça.
- Adapte o nível de detalhe ao contexto da pergunta.
- Mantenha o contexto da conversa: use informações já discutidas na sessão.
- Use português brasileiro natural, profissional mas acessível."""

    RESPONSE_STYLE_POLICY_FALLBACK = """Estilo e formatação das respostas:
- Use português brasileiro natural e profissional.
- Nunca despeje JSON bruto ou payloads técnicos ao usuário.
- Transforme dados técnicos em texto humano com marcadores simples.
- Não mencione campos técnicos (humanizedSummary, authorizedResult, payload).
- Não diga que acessou banco de dados; diga que consultou informações da plataforma.
- Não extrapole além dos resultados autorizados.
- Não repita a pergunta do usuário antes de responder.
- Não use frases genéricas como "Claro!", "Com certeza!" — vá direto à resposta.
- Se não houver informação suficiente, diga claramente e sugira alternativas.
- Use **negrito** para destacar valores-chave e listas para múltiplos itens."""

    EXTERNAL_ACTIONS_POLICY_FALLBACK = """Instruções para resultados de `execute_external_action`:
- Se statusCode estiver entre 200 e 299 e ok=true, considere que a API foi consultada com sucesso; nunca diga que não tem acesso direto à API nesse caso.
- Use primeiro o campo `humanizedSummary` para responder em português claro.
- Se a resposta vier de API, diga de forma natural que consultou informações autorizadas da plataforma.
- Use o campo `summary` e o `authorizedResult` apenas como apoio técnico aos dados operacionais retornados.
- Se statusCode for 401 ou 403, informe que o usuário não possui permissão suficiente para acessar aquela informação.
- Se statusCode for 404, informe que o recurso não foi encontrado.
- Se statusCode for 422, informe que os parâmetros da consulta estão inválidos ou incompletos."""

    PLATFORM_TOOLS_POLICY_FALLBACK = """Instruções para ferramentas internas da plataforma:
- Se uma ferramenta retornar dados que respondem diretamente à pergunta, responda de forma direta e objetiva usando esses dados.
- Para `get_current_user`, informe nome e e-mail quando disponíveis. Não responda de forma genérica.
- Para `get_allowed_apps`, liste os aplicativos autorizados pelo nome e, se útil, pelo caminho/basePath.
- Para `get_allowed_routes`, liste os menus ou rotas autorizadas relevantes."""

    PRODUCT_FIELDS_POLICY_FALLBACK = """Instruções para dados de produtos:
- Para produtos, explique os campos com nomes em português.
- Use nomes como: código, descrição, tipo, unidade, grupo, ativo, armazém padrão, último preço de compra, custo padrão, última revisão e NCM.
- Não exponha nomes técnicos de campos se houver alias claro em português."""

    SQL_KNOWLEDGE_POLICY_FALLBACK = """Instruções para contexto documental com SQL, consultas ou exemplos técnicos:
- Não reproduza SQL bruto, query inteira, scripts ou blocos técnicos longos, exceto se o usuário pedir explicitamente.
- Use SQL/documentação técnica como referência para entender tabelas, campos e intenção.
- Quando houver resultado de ferramenta/API, responda com os dados retornados pela ferramenta, não com a query documental.
- Se o contexto documental trouxer exemplos de SQL, explique em linguagem natural o que ele indica.
- Não apresente o mesmo SQL em seções repetidas como consulta executada, resultado, resumo humanizado e resumo técnico.
- Se uma ferramenta foi executada, o resumo deve priorizar o resultado autorizado da ferramenta."""

    SESSION_KNOWLEDGE_POLICY_FALLBACK = """Instruções para fontes anexadas à conversa:
- Arquivos anexados pelo usuário nesta conversa são fontes de conhecimento da sessão atual.
- Use essas fontes para responder perguntas sobre o conteúdo do arquivo.
- Se a resposta vier do arquivo anexado, diga de forma natural que usou o material enviado na conversa.
- Não trate arquivo anexado como regra global da plataforma.
- Não aplique conhecimento de uma sessão em outra sessão.
- Se o arquivo foi indexado mas não houver trecho relevante, informe que não encontrou a informação no material enviado."""

    EXTERNAL_ACTION_MARKERS = (
        "execute_external_action",
        "authorizedResult",
        "humanizedSummary",
        "technicalSummary",
        "statusCode",
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

    API_DELPI_ROUTES_POLICY_FALLBACK = """Instruções para consultas via API DELPI (execute_external_action):
- Produto: analyser para descrição/ficha; /stock para saldo do item; /search sem código exato.
- LMP: /engineering/lmps para listar; /dashboard para painel; /lmps/{sale_number} para uma OV.
- Valor total de estoque da empresa: /supplies/stock-value (não confundir com estoque de produto).
- SQL leitura: POST /data/sql com campo sql."""

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

    CONTEXT_MEMORY_POLICY_FALLBACK = """Memória da conversa: use a seção de memória ativa para follow-ups; novo código/filial/período na mensagem prevalece; não repita consulta idêntica se o histórico já trouxe os dados."""

    ADMINISTRATIVE_WRITING_POLICY_FALLBACK = """Modo textual: corrija, traduza ou redija sem consultar ERP/API; preserve códigos e fatos; em correções simples entregue só o texto final."""

    def build_system_prompt(self) -> str:
        base = self._load_policy("base.md", self.BASE_POLICY_FALLBACK)
        context_engineering = self._load_policy(
            "context-engineering.md",
            self.CONTEXT_ENGINEERING_POLICY_FALLBACK,
        )
        context_memory = self._load_policy(
            "chat-context-memory.md",
            self.CONTEXT_MEMORY_POLICY_FALLBACK,
        )
        return f"{base}\n\n{context_engineering}\n\n{context_memory}"

    def build_rag_prompt(self, context: str) -> str:
        return self.build_contextual_prompt(
            rag_context=context,
            tool_context="",
        )

    SQL_ASSISTANT_SKILL_FALLBACK = """Skill SQL: elabore e revise consultas SELECT (SQL genérico) em blocos ```sql```; identifique erros quando o usuário colar SQL ou mensagens de erro; execução requer action /data/sql."""

    COMPANY_KNOWLEDGE_SKILL_FALLBACK = """Skill Conhecimento da empresa: priorize a base documental global (RAG e search_knowledge_base); cite fontes; não invente políticas."""

    WEB_SEARCH_POLICY_FALLBACK = (
        "Política web_search: cite fontes/URLs retornadas; se searchStatus=no_results, "
        "diga que a busca não trouxe resultados (sem negar a ferramenta) e complemente "
        "com conhecimento geral rotulado; não trate web como dados operacionais DELPI."
    )

    def build_active_skill_policy_sections(self, skills: dict | None) -> list[str]:
        """Políticas de skills ativas no runtime (chat comum ou agente), sem ação do usuário."""
        resolved_skills = skills or {}
        sections: list[str] = []

        if resolved_skills.get("sqlAuthoring"):
            from app.domain.skills.chat_skill_registry import ChatSkillRegistry, SQL_SKILL_KEY

            sql_policy = ChatSkillRegistry.get_policy_content(SQL_SKILL_KEY)
            sections.append(
                sql_policy
                or self._load_policy(
                    "sql-assistant-skill.md",
                    self.SQL_ASSISTANT_SKILL_FALLBACK,
                )
            )

        if resolved_skills.get("companyKnowledge"):
            from app.domain.skills.chat_skill_registry import (
                ChatSkillRegistry,
                COMPANY_KNOWLEDGE_SKILL_KEY,
            )

            company_policy = ChatSkillRegistry.get_policy_content(
                COMPANY_KNOWLEDGE_SKILL_KEY
            )
            sections.append(
                company_policy
                or self._load_policy(
                    "company-knowledge-skill.md",
                    self.COMPANY_KNOWLEDGE_SKILL_FALLBACK,
                )
            )

        if resolved_skills.get("drawingAnalysis"):
            from app.domain.skills.chat_skill_registry import (
                ChatSkillRegistry,
                DRAWING_ANALYSIS_SKILL_KEY,
            )

            drawing_policy = ChatSkillRegistry.get_policy_content(
                DRAWING_ANALYSIS_SKILL_KEY
            )
            sections.append(
                drawing_policy
                or self._load_policy(
                    "drawing-analysis-delpi-skill.md",
                    "Analise desenhos PDF confrontando com API DELPI e normas.",
                )
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
        skills: dict | None = None,
    ) -> str:
        sections: list[str] = [self.build_system_prompt()]
        resolved_skills = skills or {}

        if text_task_mode:
            sections.append(
                self._load_policy(
                    "administrative-writing.md",
                    self.ADMINISTRATIVE_WRITING_POLICY_FALLBACK,
                )
            )

        stream_texts = ContentService.stream()
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
            sections.append(
                self._load_policy(
                    "operational-agent.md",
                    "Modo operacional: respostas curtas com base nas ferramentas autorizadas.",
                )
            )

        if data_interpretation_mode:
            sections.append(
                self._load_policy(
                    "chat-data-interpretation.md",
                    "Modo interpretação: explique dados operacionais já obtidos; ignore perfil/permissões.",
                )
            )
        elif analysis_mode:
            sections.append(
                self._load_policy(
                    "chat-analysis-insights.md",
                    "Modo análise: compare dados do histórico e traga insights objetivos.",
                )
            )

        return "\n\n".join(
            section.strip()
            for section in sections
            if section and section.strip()
        )

    def _response_policy_sections(
        self,
        *,
        rag_context: str,
        tool_context: str,
        skills: dict | None = None,
    ) -> list[str]:
        resolved_skills = skills or {}
        sections = [
            self._load_policy(
                "response-style.md",
                self.RESPONSE_STYLE_POLICY_FALLBACK,
            )
        ]

        normalized_rag_context = self._normalize(rag_context)
        normalized_tool_context = self._normalize(tool_context)

        if self._contains_any(normalized_tool_context, self.EXTERNAL_ACTION_MARKERS):
            sections.append(
                self._load_policy(
                    "external-actions.md",
                    self.EXTERNAL_ACTIONS_POLICY_FALLBACK,
                )
            )

        if self._contains_any(normalized_tool_context, self.API_DELPI_MARKERS):
            sections.append(
                self._load_policy(
                    "api-delpi-routes.md",
                    self.API_DELPI_ROUTES_POLICY_FALLBACK,
                )
            )

        if self._contains_any(normalized_tool_context, self.PLATFORM_TOOL_MARKERS):
            sections.append(
                self._load_policy(
                    "platform-tools.md",
                    self.PLATFORM_TOOLS_POLICY_FALLBACK,
                )
            )

        if self._contains_any(normalized_tool_context, ("web_search",)):
            sections.append(
                self._load_policy(
                    "web-search-policy.md",
                    self.WEB_SEARCH_POLICY_FALLBACK,
                )
            )

        if self._contains_any(normalized_tool_context, self.PRODUCT_MARKERS):
            sections.append(
                self._load_policy(
                    "product-fields.md",
                    self.PRODUCT_FIELDS_POLICY_FALLBACK,
                )
            )

        if self._contains_any(normalized_rag_context, self.SESSION_KNOWLEDGE_MARKERS):
            sections.append(
                self._load_policy(
                    "session-knowledge.md",
                    self.SESSION_KNOWLEDGE_POLICY_FALLBACK,
                )
            )

        if not resolved_skills.get("sqlAuthoring") and (
            self._contains_any(normalized_rag_context, self.SQL_MARKERS)
            or self._contains_any(normalized_tool_context, self.SQL_MARKERS)
        ):
            sections.append(
                self._load_policy(
                    "sql-knowledge.md",
                    self.SQL_KNOWLEDGE_POLICY_FALLBACK,
                )
            )

        return sections

    def _contains_any(self, value: str, markers: tuple[str, ...]) -> bool:
        return any(self._normalize(marker) in value for marker in markers)

    def _normalize(self, value: str | None) -> str:
        return str(value or "").casefold()

    @classmethod
    @lru_cache(maxsize=32)
    def _load_policy(cls, filename: str, fallback: str) -> str:
        path = cls.POLICY_DIR / filename

        try:
            content = path.read_text(encoding="utf-8").strip()
        except OSError:
            return fallback.strip()

        return content or fallback.strip()
