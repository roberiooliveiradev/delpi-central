from __future__ import annotations

from app.application.services.chat_action_label_service import ChatActionLabelService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_CAPABILITIES_QUESTION_TERMS = (
    "o que voce pode fazer",
    "o que você pode fazer",
    "o que vc pode fazer",
    "o que voce e capaz de fazer",
    "o que vc e capaz de fazer",
    "o que e capaz de fazer",
    "do que voce e capaz",
    "do que vc e capaz",
    "do que e capaz",
    "quais coisas voce e capaz",
    "quais coisas vc e capaz",
    "o que consegue fazer",
    "o que sabe fazer",
    "o que voce sabe",
    "quais suas capacidades",
    "suas capacidades",
    "suas funcionalidades",
    "quais funcionalidades",
    "o que faz",
    "o que voce faz",
    "o que vc faz",
    "o que você faz",
    "para que serve",
    "como pode me ajudar",
    "como voce pode ajudar",
    "como voce pode me ajudar",
    "como você pode ajudar",
    "como você pode me ajudar",
    "como voce me ajuda",
    "me ajuda com o que",
    "me ajude com o que",
    "lista de comandos",
    "quais comandos",
    "quais apis",
    "quais api",
    "quais actions",
    "quais acoes",
    "quais rotas da api",
    "quais ferramentas",
    "ferramentas disponiveis",
    "rotas disponiveis",
    "o que tenho disponivel",
    "o que esta disponivel",
    "me explique suas funcoes",
    "quais consultas",
    "pode consultar o que",
    "o que consegue consultar",
    "o que voce consulta",
    "quais dados voce acessa",
    "quais dados você acessa",
    "me mostre o que da pra fazer",
    "da pra fazer o que",
    "o que da pra consultar",
    "menu de comandos",
    "help",
)

_PLATFORM_TOOLS = (
    ("get_current_user", "Dados do seu perfil (nome, e-mail, papéis e grupos, conforme consentimento)."),
    ("get_allowed_apps", "Aplicativos e módulos que você pode acessar na plataforma."),
    ("get_allowed_routes", "Menus e rotas autorizados no seu perfil."),
)

# (fragmento de path, categoria, exemplos de pergunta)
_PATH_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("/stock", "Estoque de produto", (
        "estoque do produto 10080001",
        "saldo do 10080001",
        "quanto tem em estoque do 10080001",
    )),
    ("/suppliers", "Fornecedores de produto", (
        "fornecedores do 10080001",
        "quem fornece o produto 10080001",
        "forncedores do 10080001 em tabela",
    )),
    ("/customers", "Clientes de produto", (
        "clientes do produto 10080001",
        "quem compra o 10080001",
    )),
    ("/structure", "Estrutura (BOM)", (
        "estrutura do produto 10080001",
        "componentes do 10080001",
        "bom do 10080001",
    )),
    ("/parents", "Onde o produto é usado (pais)", (
        "onde o 10080001 é usado",
        "produtos pai do 10080001",
        "pai do 10080001",
    )),
    ("/purchases", "Compras de produto", (
        "compras do produto 10080001",
        "historico de compras do 10080001",
    )),
    ("/sales", "Vendas de produto", (
        "vendas do produto 10080001",
        "faturamento do 10080001",
    )),
    ("/prices", "Preços / tabelas", (
        "preço do produto 10080001",
        "tabela de preço do 10080001",
        "quanto custa o 10080001",
    )),
    ("/guide", "Roteiro de produção", (
        "roteiro do produto 10080001",
        "etapas do 10080001",
    )),
    ("/inspection", "Inspeção / qualidade", (
        "inspeção do produto 10080001",
        "plano de inspeção do 10080001",
    )),
    ("/internal-movements", "Movimentações internas", (
        "movimentações internas do 10080001",
        "transferências do 10080001",
    )),
    ("/inbound-invoice", "Notas fiscais de entrada", (
        "notas de entrada do 10080001",
        "nfe entrada do 10080001",
    )),
    ("/outbound-invoice", "Notas fiscais de saída", (
        "notas de saída do 10080001",
        "nfe saída do 10080001",
    )),
    ("/search", "Busca de produtos", (
        "buscar produto por descrição parafuso",
        "pesquisar produto bandeira",
    )),
    ("/analyser", "Ficha / descrição do produto", (
        "descrição do produto 10080001",
        "me fala do produto 10080001",
        "dados cadastrais do 10080001",
    )),
    ("/engineering/lmps", "LMP / listas de materiais de projeto", (
        "listar lmps",
        "lmps da filial 01",
        "detalhe da lmp ov 12345",
    )),
    ("/lmps/", "Detalhe de LMP", (
        "lmp ov 12345",
        "detalhes da ov 12345",
    )),
    ("/supplies/stock-value", "Valor total de estoque (empresa)", (
        "valor total de estoque",
        "quanto vale o estoque",
    )),
    ("/inventory-turnover", "Giro de estoque (IDD)", (
        "giro de estoque",
        "idd do estoque",
    )),
    ("/cpv", "Indicador CPV", ("cpv de suprimentos", "indicador cpv")),
    ("/otd", "Indicador OTD", ("otd de entregas", "indicador otd")),
    ("/data/sql", "Consulta SQL (leitura)", (
        "consulta sql autorizada",
        "select somente leitura",
    )),
    ("/sale-order", "Ordens de venda", (
        "ordens de venda do período",
        "listar ovs",
    )),
    ("/commercial/", "Indicadores comerciais", ("indicadores comerciais do mês",)),
    ("/financial/", "Indicadores financeiros", ("indicadores financeiros",)),
    ("/production/", "Indicadores de produção", ("indicadores de produção",)),
    ("/hr/", "Indicadores de RH", ("indicadores de rh", "snapshot rh")),
    ("/quality/", "Indicadores de qualidade", ("indicadores de qualidade",)),
)

# Exemplos gerais quando não há agente (chat comum)
_COMMON_CHAT_EXAMPLES: tuple[str, ...] = (
    "estoque do produto 10080001",
    "fornecedores do 10080001 em tabela",
    "estrutura do 10080001",
    "preço do 10080001",
    "listar lmps da filial",
    "o que você pode fazer",
    "quais apps tenho acesso",
)


class ChatCapabilitiesService:
    """Responde perguntas sobre o que o chat/agente consegue fazer."""

    @classmethod
    def is_capabilities_question(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > 280:
            return False

        if ChatMessageNormalizationService.contains_any(message, _CAPABILITIES_QUESTION_TERMS):
            return True

        short_help = (
            "ajuda",
            "help",
            "comandos",
            "capacidades",
            "funcionalidades",
            "menu",
        )
        if normalized in short_help:
            return True

        if normalized.startswith(("ajuda ", "help ")) and len(normalized) < 80:
            return True

        if "capaz" in normalized and any(
            token in normalized for token in ("fazer", "consultar", "ajudar", "oferecer")
        ):
            return True

        return False

    @classmethod
    def build_direct_answer(
        cls,
        *,
        workspace_context: dict,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
    ) -> str | None:
        lines: list[str] = [
            "Posso ajudar você nestes formatos:",
            "",
            "**Sempre disponíveis (chat comum e agentes)**",
        ]

        for _tool, description in _PLATFORM_TOOLS:
            lines.append(f"- {description}")

        lines.extend(
            [
                "- Respostas com base na **documentação e conhecimento** autorizado (RAG).",
                "- Anexos e fontes da conversa ou do projeto, quando enviados.",
                "- Entendo perguntas com **pequenos erros de digitação** (ex.: *forncedores*, "
                "*estoq*, *preco*, *estrutur*).",
            ]
        )

        skills = workspace_context.get("skills") or {}
        skill_lines = cls._format_skills_section(skills, workspace_context.get("allowedActionIds"))
        if skill_lines:
            lines.extend(["", "**Skills (comportamento do assistente)**"])
            lines.extend(skill_lines)

        agent = workspace_context.get("agent") or {}
        agent_name = str(agent.get("name") or workspace_context.get("agentKey") or "").strip()
        allowed = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]

        if allowed and action_catalog:
            lines.extend(["", f"**Consultas operacionais — agente {agent_name or 'atual'}**"])
            lines.append(
                "Com as APIs/actions abaixo habilitadas neste agente, busco dados reais na "
                "api-delpi e apresento em **texto**, **tabela** ou **gráfico** (quando fizer sentido):"
            )
            lines.append("")
            lines.extend(cls._format_action_catalog(action_catalog, allowed))
        else:
            lines.extend(
                [
                    "",
                    "**Consultas operacionais (produto, estoque, LMP, fornecedores…)**",
                    "- No **chat comum**, selecione um **agente especializado** com as actions "
                    "OpenAPI habilitadas para a consulta desejada.",
                    "- Exemplos de perguntas que funcionam com um agente configurado:",
                ]
            )
            for example in _COMMON_CHAT_EXAMPLES:
                lines.append(f"  - *{example}*")

        lines.extend(
            [
                "",
                "**Dicas**",
                "- Inclua **código do produto** (ex.: 10080001) ou **número da OV** quando souber.",
                "- Peça formato: *em tabela*, *em gráfico* ou *só texto*.",
                "- Se faltar contexto, pergunto o que você precisa em vez de inventar dados.",
            ]
        )

        return "\n".join(lines)

    @classmethod
    def _format_skills_section(
        cls,
        skills: dict,
        allowed_action_ids: list[str] | None,
    ) -> list[str]:
        lines: list[str] = []
        allowed = allowed_action_ids or []

        if skills.get("sqlAuthoring"):
            lines.append(
                "- **SQL (elaborar consultas)**: posso montar e explicar queries `SELECT` em "
                "blocos de código, como um assistente SQL (skill)."
            )
        else:
            lines.append(
                "- **SQL (elaborar consultas)**: desligado nesta sessão — habilite a skill no "
                "agente ou use o chat comum (padrão global)."
            )

        if skills.get("sqlExecutionAvailable"):
            lines.append(
                "- **SQL (executar)**: action `POST /data/sql` habilitada — consigo rodar "
                "consultas somente leitura autorizadas e mostrar o resultado."
            )
        elif allowed:
            lines.append(
                "- **SQL (executar)**: não há action de execução SQL habilitada; só elaboro "
                "o texto da query se a skill estiver ativa."
            )
        else:
            lines.append(
                "- **SQL (executar)**: requer agente com action `POST /data/sql` configurada "
                "(diferente da skill de elaboração)."
            )

        lines.append(
            "- **Skills ≠ Actions**: skills orientam *como* respondo; actions *executam* APIs."
        )

        return lines

    @classmethod
    def _format_action_catalog(cls, catalog: list[dict], allowed_ids: list[str]) -> list[str]:
        allowed_set = set(allowed_ids)
        by_category: dict[str, list[dict]] = {}

        for action in catalog:
            action_id = str(action.get("actionId") or "").strip()
            if action_id not in allowed_set:
                continue

            path = str(action.get("path") or "")
            category, _examples = cls._resolve_path_rule(path)
            raw_summary = str(
                action.get("summary") or action.get("description") or action_id
            ).strip()
            method = str(action.get("method") or "GET").upper()
            by_category.setdefault(category, []).append(
                {
                    "summary": ChatActionLabelService.humanize(
                        path=path,
                        method=method,
                        summary=raw_summary,
                        action_id=action_id,
                    ),
                    "method": method,
                    "path": path,
                    "examples": _examples,
                }
            )

        if not by_category:
            return ["- Nenhuma action detalhada no catálogo; verifique a configuração do agente."]

        output: list[str] = []
        max_per_category = 8

        for category in sorted(by_category.keys()):
            items = by_category[category]
            output.append(f"**{category}**")
            shown_examples: set[str] = set()

            for item in items[:max_per_category]:
                summary = item["summary"]
                path = item["path"]
                method = item["method"]
                line = f"- {summary} — `{method} {path}`" if path else f"- {summary}"
                output.append(line)

                for ex in item.get("examples") or ():
                    if ex not in shown_examples and len(shown_examples) < 3:
                        output.append(f"  - Ex.: *{ex}*")
                        shown_examples.add(ex)

            if len(items) > max_per_category:
                output.append(f"- … e mais {len(items) - max_per_category} action(s) nesta categoria")
            output.append("")

        return output

    @classmethod
    def _resolve_path_rule(cls, path: str) -> tuple[str, tuple[str, ...]]:
        lowered = path.lower()
        for token, category, examples in _PATH_RULES:
            if token in lowered:
                return category, examples
        return "Outras APIs", (
            "consulta conforme rota habilitada",
            "dados operacionais autorizados",
        )

    @classmethod
    def load_action_catalog_for_agent(
        cls, allowed_action_ids: list[str] | None,
    ) -> list[dict]:
        if not allowed_action_ids:
            return []

        try:
            from app.infrastructure.persistence.postgres_external_action_repository import (
                PostgresExternalActionRepository,
            )

            repository = PostgresExternalActionRepository()
            catalog = repository.list_actions()
            allowed_set = {str(item).strip() for item in allowed_action_ids}
            return [
                item
                for item in catalog
                if str(item.get("actionId") or "") in allowed_set
            ]
        except Exception:
            return []
