from functools import lru_cache
from pathlib import Path


class PromptPolicyService:
    POLICY_DIR = Path(__file__).resolve().parents[1] / "prompt_policies"

    BASE_POLICY_FALLBACK = """Você é o assistente Minha DELPI, integrado à Minha DELPI.

Regras obrigatórias:
1. Responda apenas com base nas informações autorizadas ao usuário.
2. Não invente dados internos.
3. Quando uma resposta depender de dados operacionais, use somente ferramentas autorizadas pelo backend.
4. Nunca exponha tokens, senhas, chaves, secrets, variáveis sensíveis ou conteúdo de autenticação.
5. Se o usuário não tiver permissão para um módulo, informe que não há acesso suficiente.
6. Não execute ações críticas sem confirmação explícita do usuário e sem auditoria.
7. Se não houver contexto suficiente, diga que não há informação suficiente.
8. Não crie regras de negócio novas que não estejam no sistema ou na documentação.
9. Siga a arquitetura Minha DELPI: SSO, RBAC, Core API, plugins e auditoria.
10. Priorize respostas objetivas, rastreáveis e úteis."""

    RESPONSE_STYLE_POLICY_FALLBACK = """Instruções gerais para resposta:
- Nunca responda despejando JSON bruto, objetos, chaves técnicas ou payloads completos ao usuário.
- Transforme dados técnicos em texto humano, com marcadores simples e aliases em português.
- Não mencione campos técnicos como humanizedSummary, technicalSummary, authorizedResult, payload ou JSON.
- Use o contexto documental como apoio quando disponível.
- Não cite ferramentas que não foram executadas.
- Não diga que acessou banco de dados; diga que consultou informações autorizadas da plataforma, quando necessário.
- Não extrapole além dos resultados autorizados.
- Se o contexto não responder à pergunta, diga que não há informação suficiente na base disponível."""

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

    EXTERNAL_ACTION_MARKERS = (
        "execute_external_action",
        "authorizedResult",
        "humanizedSummary",
        "technicalSummary",
        "statusCode",
    )

    PLATFORM_TOOL_MARKERS = (
        "get_current_user",
        "get_allowed_apps",
        "get_allowed_routes",
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
    )

    def build_system_prompt(self) -> str:
        return self._load_policy("base.md", self.BASE_POLICY_FALLBACK)

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
        sections: list[str] = [self.build_system_prompt()]

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

        sections.extend(self._response_policy_sections(tool_context=tool_context))

        return "\n\n".join(
            section.strip()
            for section in sections
            if section and section.strip()
        )

    def _response_policy_sections(self, *, tool_context: str) -> list[str]:
        sections = [
            self._load_policy(
                "response-style.md",
                self.RESPONSE_STYLE_POLICY_FALLBACK,
            )
        ]

        normalized_tool_context = self._normalize(tool_context)

        if self._contains_any(normalized_tool_context, self.EXTERNAL_ACTION_MARKERS):
            sections.append(
                self._load_policy(
                    "external-actions.md",
                    self.EXTERNAL_ACTIONS_POLICY_FALLBACK,
                )
            )

        if self._contains_any(normalized_tool_context, self.PLATFORM_TOOL_MARKERS):
            sections.append(
                self._load_policy(
                    "platform-tools.md",
                    self.PLATFORM_TOOLS_POLICY_FALLBACK,
                )
            )

        if self._contains_any(normalized_tool_context, self.PRODUCT_MARKERS):
            sections.append(
                self._load_policy(
                    "product-fields.md",
                    self.PRODUCT_FIELDS_POLICY_FALLBACK,
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
