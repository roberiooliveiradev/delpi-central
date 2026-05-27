from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_CAPABILITIES_QUESTION_TERMS = (
    "o que voce pode fazer",
    "o que você pode fazer",
    "o que vc pode fazer",
    "o que consegue fazer",
    "o que sabe fazer",
    "quais suas capacidades",
    "suas capacidades",
    "suas funcionalidades",
    "quais funcionalidades",
    "o que faz",
    "para que serve",
    "como pode me ajudar",
    "como voce pode ajudar",
    "como você pode ajudar",
    "me ajuda com o que",
    "lista de comandos",
    "quais comandos",
    "quais apis",
    "quais api",
    "quais actions",
    "quais acoes",
    "quais ferramentas",
    "ferramentas disponiveis",
    "rotas disponiveis",
    "o que tenho disponivel",
    "o que esta disponivel",
    "me explique suas funcoes",
    "quais consultas",
    "pode consultar o que",
    "o que consegue consultar",
)

_PLATFORM_TOOLS = (
    ("get_current_user", "Dados do seu perfil (nome, e-mail, papéis e grupos, conforme consentimento)."),
    ("get_allowed_apps", "Aplicativos e módulos que você pode acessar na plataforma."),
    ("get_allowed_routes", "Menus e rotas autorizados no seu perfil."),
)

_PATH_CATEGORY_HINTS: tuple[tuple[str, str], ...] = (
    ("/products/", "Produtos (estoque, estrutura, fornecedores, preços, compras, vendas…)"),
    ("/engineering/lmps", "LMP / engenharia (listas, OVs, dashboard)"),
    ("/supplies/", "Suprimentos (indicadores CPV, OTD, giro e valor de estoque)"),
    ("/commercial/", "Indicadores comerciais"),
    ("/financial/", "Indicadores financeiros"),
    ("/production/", "Indicadores de produção"),
    ("/hr/", "Indicadores de RH"),
    ("/quality/", "Indicadores de qualidade"),
    ("/data/sql", "Consultas SQL somente leitura (quando habilitado)"),
    ("/sale-order", "Ordens de venda"),
)


class ChatCapabilitiesService:
    """Responde perguntas sobre o que o chat/agente consegue fazer."""

    @classmethod
    def is_capabilities_question(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > 220:
            return False

        if ChatMessageNormalizationService.contains_any(message, _CAPABILITIES_QUESTION_TERMS):
            return True

        short_help = (
            "ajuda",
            "help",
            "comandos",
            "capacidades",
            "funcionalidades",
        )
        if normalized in short_help:
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
            ]
        )

        agent = workspace_context.get("agent") or {}
        agent_name = str(agent.get("name") or workspace_context.get("agentKey") or "").strip()
        allowed = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]

        if allowed and action_catalog:
            lines.extend(["", f"**Consultas operacionais — agente {agent_name or 'atual'}**"])
            lines.append(
                "Com as APIs/actions abaixo habilitadas neste agente, consigo buscar dados "
                "reais na api-delpi e apresentar em texto, tabela ou gráfico (quando fizer sentido):"
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
                    "- Exemplos: estoque do produto 10080001, fornecedores, estrutura (BOM), "
                    "LMPs, indicadores de suprimentos.",
                    "- Você pode pedir em linguagem natural; erros leves de digitação "
                    "costumam ser interpretados (ex.: *forncedores*, *estoq*).",
                ]
            )

        lines.extend(
            [
                "",
                "**Dicas**",
                "- Seja específico: inclua **código do produto** ou **número da OV** quando souber.",
                "- Peça formato: *em tabela*, *em gráfico* ou *só texto*.",
                "- Perguntas ambíguas: vou pedir esclarecimento em vez de inventar dados.",
            ]
        )

        return "\n".join(lines)

    @classmethod
    def _format_action_catalog(cls, catalog: list[dict], allowed_ids: list[str]) -> list[str]:
        allowed_set = set(allowed_ids)
        by_category: dict[str, list[str]] = {}

        for action in catalog:
            action_id = str(action.get("actionId") or "").strip()
            if action_id not in allowed_set:
                continue

            path = str(action.get("path") or "")
            method = str(action.get("method") or "GET").upper()
            summary = str(action.get("summary") or action.get("description") or action_id).strip()
            category = cls._category_for_path(path)

            label = summary
            if path:
                label = f"{summary} — `{method} {path}`"

            by_category.setdefault(category, []).append(label)

        if not by_category:
            return ["- Nenhuma action detalhada no catálogo; verifique a configuração do agente."]

        output: list[str] = []
        max_per_category = 8

        for category in sorted(by_category.keys()):
            items = by_category[category]
            output.append(f"**{category}**")
            for item in items[:max_per_category]:
                output.append(f"- {item}")
            if len(items) > max_per_category:
                output.append(f"- … e mais {len(items) - max_per_category} action(s)")
            output.append("")

        return output

    @classmethod
    def _category_for_path(cls, path: str) -> str:
        lowered = path.lower()
        for token, label in _PATH_CATEGORY_HINTS:
            if token in lowered:
                return label
        return "Outras APIs"

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
