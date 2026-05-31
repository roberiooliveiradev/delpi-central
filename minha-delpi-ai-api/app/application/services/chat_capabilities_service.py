from __future__ import annotations

import re
from functools import lru_cache

from app.application.services.chat_action_label_service import ChatActionLabelService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _capabilities_content() -> dict:
    return ContentService.load_json("assistant/capabilities")


def _sections() -> dict:
    return _capabilities_content().get("sections") or {}


def _skills_texts() -> dict:
    return _capabilities_content().get("skills") or {}


def _catalog_texts() -> dict:
    return _capabilities_content().get("catalog") or {}


def _detection() -> dict:
    return _capabilities_content().get("detection") or {}


@lru_cache(maxsize=1)
def _path_rules() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    data = _capabilities_content()
    rules = data.get("pathRules") or []
    parsed: list[tuple[str, str, tuple[str, ...]]] = []
    for item in rules:
        if not isinstance(item, dict):
            continue
        token = str(item.get("token") or "").strip()
        category = str(item.get("category") or "").strip()
        examples = item.get("examples") or []
        if token and category:
            parsed.append((token, category, tuple(str(ex) for ex in examples)))
    return tuple(parsed)


@lru_cache(maxsize=1)
def _path_rule_default() -> tuple[str, tuple[str, ...]]:
    data = _capabilities_content()
    default = data.get("pathRuleDefault") or {}
    if not isinstance(default, dict):
        return "Outras APIs", ("consulta conforme rota habilitada", "dados operacionais autorizados")
    category = str(default.get("category") or "Outras APIs")
    examples = tuple(str(item) for item in (default.get("examples") or ()))
    return category, examples


@lru_cache(maxsize=1)
def _common_chat_examples() -> tuple[str, ...]:
    data = _capabilities_content()
    return tuple(str(item) for item in (data.get("commonExamples") or ()))


@lru_cache(maxsize=1)
def _feature_answers() -> dict:
    return _capabilities_content().get("featureAnswers") or {}


class ChatCapabilitiesService:
    """Responde perguntas sobre o que o chat/agente consegue fazer."""

    _COMMAND_VERBS = (
        "busque",
        "buscar",
        "pesquise",
        "pesquisar",
        "liste",
        "listar",
        "procure",
        "procurar",
        "traga",
        "mostre",
        "mostrar",
        "exiba",
        "exibir",
    )

    _INQUIRY_MARKERS = (
        "consegue",
        "pode buscar",
        "pode pesquisar",
        "pode consultar",
        "pode listar",
        "da pra buscar",
        "da pra pesquisar",
        "da pra consultar",
        "dá pra buscar",
        "e possivel buscar",
        "é possivel buscar",
        "sabe buscar",
        "tem como buscar",
    )

    _OPERATIONAL_QUERY_PATTERNS = (
        r"\bqual\s+o\s+estoque\b",
        r"\bqual\s+o\s+preco\b",
        r"\bqual\s+o\s+pre[cç]o\b",
        r"\bquem\s+fornece\b",
        r"\bme\s+fale\s+do\s+produto\b",
        r"\bmostre\s+o\s+estoque\b",
        r"\bmostre\s+a\s+estrutura\b",
        r"\bestoque\s+do\s+produto\b",
        r"\bestoque\s+do\b",
        r"\bvis[aã]o\s+360\b",
        r"\bconsulte\b",
        r"\bconsultar\b",
        r"\bliste\s+os\s+fornecedores\b",
        r"\bonde\s+o\s+produto\b",
        r"\bonde\s+[eé]\s+usado\b",
    )

    _OPERATIONAL_DATA_TOPICS = (
        "estoque",
        "fornecedor",
        "estrutura",
        "roteiro",
        "inspecao",
        "inspeção",
        "faturamento",
        "venda",
        "compra",
        "preco",
        "preço",
        "lmp",
        "ov ",
    )

    @classmethod
    def is_capability_inquiry(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if cls.is_capabilities_question(message):
            return True

        if cls.is_release_notes_question(message):
            return True

        if cls._is_permission_help_inquiry(normalized):
            return True

        if cls._is_feature_capability_inquiry(message):
            return True

        return False

    @classmethod
    def is_release_notes_question(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > 120:
            return False

        terms = (
            "o que mudou",
            "novidades",
            "novidade",
            "changelog",
            "release notes",
            "ultima versao",
            "última versão",
            "o que tem de novo",
            "o que ha de novo",
            "o que há de novo",
        )

        return any(term in normalized for term in terms)

    @classmethod
    def resolve_capability_answer(
        cls,
        *,
        message: str,
        workspace_context: dict,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
    ) -> str | None:
        from app.application.services.chat_onboarding_service import (
            ChatOnboardingService,
        )

        training = ChatOnboardingService.resolve_direct_answer(message=message)

        if training:
            return training

        if cls.is_release_notes_question(message):
            from app.application.services.assistant_capabilities_registry import (
                AssistantCapabilitiesRegistry,
            )

            release_answer = AssistantCapabilitiesRegistry.format_release_notes_answer()

            if release_answer:
                return release_answer

        targeted = cls.build_feature_answer(
            message=message,
            workspace_context=workspace_context,
            allowed_action_ids=allowed_action_ids,
            action_catalog=action_catalog,
        )

        if targeted:
            return targeted

        if cls.is_capabilities_question(message):
            return cls.build_direct_answer(
                workspace_context=workspace_context,
                allowed_action_ids=allowed_action_ids,
                action_catalog=action_catalog,
            )

        return None

    @classmethod
    def build_feature_answer(
        cls,
        *,
        message: str,
        workspace_context: dict,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
    ) -> str | None:
        if not cls._is_feature_capability_inquiry(message):
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        allowed = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]
        catalog = action_catalog or []

        if "grupo" in normalized or "group" in normalized:
            return cls._answer_product_search_by_group(
                workspace_context=workspace_context,
                allowed=allowed,
                catalog=catalog,
            )

        if any(
            token in normalized
            for token in (
                "descricao",
                "descrição",
                "termo",
                "nome",
                "texto",
                "palavra",
            )
        ) and any(token in normalized for token in ("buscar", "pesquisar", "consultar")):
            return cls._answer_product_search_by_description(
                workspace_context=workspace_context,
                allowed=allowed,
                catalog=catalog,
            )

        if cls._is_web_search_help_inquiry(normalized):
            return cls._answer_web_search_help()

        if cls._is_destructive_capability_inquiry(normalized):
            return cls._answer_topic_help("destructiveAction")

        if cls._is_permission_help_inquiry(normalized):
            return cls._answer_topic_help("permissionsHelp")

        if cls._is_stock_help_inquiry(normalized):
            stock_answer = cls._answer_topic_help("stockHelp")

            if stock_answer:
                return stock_answer

        if cls._is_text_tasks_help_inquiry(normalized):
            text_answer = cls._answer_topic_help("textTasksHelp")

            if text_answer:
                return text_answer

        topic = cls.classify_help_topic(message)

        if topic == "canvas":
            return cls._answer_topic_help("canvasHelp")

        if topic == "chart":
            return cls._answer_topic_help("chartHelp")

        if topic == "attachment":
            return cls._answer_topic_help("attachmentHelp")

        if topic == "agent":
            return cls._answer_topic_help("agentHelp")

        generic = _feature_answers().get("genericInquiry") or {}

        if isinstance(generic, dict):
            hint = (
                "Descreva o que precisa (ex.: estoque, estrutura, fornecedores, preço) "
                "ou peça *o que você pode fazer?* para a lista completa."
            )
            body = str(generic.get("body") or "").format(hint=hint)
            title = str(generic.get("title") or "")

            if title and body:
                return f"{title}\n\n{body}".strip()

        return None

    @classmethod
    def is_capabilities_question(cls, message: str) -> bool:
        detection = _detection()
        max_length = int(detection.get("maxMessageLength") or 280)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > max_length:
            return False

        question_terms = tuple(str(item) for item in (detection.get("questionTerms") or ()))
        if ChatMessageNormalizationService.contains_any(message, question_terms):
            return True

        short_help = tuple(str(item) for item in (detection.get("shortHelp") or ()))
        if normalized in short_help:
            return True

        help_prefix_max = int(detection.get("helpPrefixMaxLength") or 80)
        if normalized.startswith(("ajuda ", "help ")) and len(normalized) < help_prefix_max:
            return True

        capaz_tokens = tuple(str(item) for item in (detection.get("capazTokens") or ()))
        if "capaz" in normalized and any(token in normalized for token in capaz_tokens):
            return True

        return False

    @classmethod
    def _is_feature_capability_inquiry(cls, message: str) -> bool:
        detection = _detection()
        max_length = int(detection.get("maxMessageLength") or 280)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        raw = str(message or "").strip()

        if not normalized or len(normalized) > max_length:
            return False

        if cls._is_permission_help_inquiry(normalized):
            return True

        if cls._looks_like_operational_data_request(message, normalized):
            return False

        if cls._looks_like_operational_command(normalized):
            return False

        if not cls._is_ability_question(normalized, raw):
            return False

        topics = tuple(str(item) for item in (detection.get("inquiryTopics") or ()))
        return any(topic in normalized for topic in topics)

    @classmethod
    def _looks_like_operational_data_request(cls, message: str, normalized: str | None = None) -> bool:
        """Consulta operacional real (ex.: estoque de produto), não pergunta «consegue?»."""
        normalized = normalized or ChatMessageNormalizationService.normalize_for_matching(message)

        if any(re.search(pattern, normalized) for pattern in cls._OPERATIONAL_QUERY_PATTERNS):
            return True

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        product_code = ChatProductQueryIntentService.extract_product_code(message)

        if product_code and any(topic in normalized for topic in cls._OPERATIONAL_DATA_TOPICS):
            return True

        if product_code and not any(marker in normalized for marker in cls._INQUIRY_MARKERS):
            return True

        return False

    @classmethod
    def _is_ability_question(cls, normalized: str, raw: str) -> bool:
        if "?" in raw:
            return True

        if normalized.startswith(("vc ", "voce ", "você ", "ce ")):
            return True

        return any(marker in normalized for marker in cls._INQUIRY_MARKERS)

    @classmethod
    def _looks_like_operational_command(cls, normalized: str) -> bool:
        if any(marker in normalized for marker in cls._INQUIRY_MARKERS):
            return False

        if "?" in normalized and any(
            token in normalized for token in ("consegue", "pode ", "da pra", "e possivel")
        ):
            return False

        return any(verb in normalized for verb in cls._COMMAND_VERBS)

    @classmethod
    def classify_help_topic(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if cls._is_web_search_help_inquiry(normalized):
            return "web"

        if any(token in normalized for token in ("lousa", "canvas")):
            return "canvas"

        if any(
            token in normalized
            for token in ("grafico", "gráfico", "chart", "visualiz", "barras", "linhas")
        ):
            return "chart"

        if any(
            token in normalized
            for token in ("anexo", "anexar", "arquivo", "pdf", "planilha")
        ):
            return "attachment"

        if any(
            token in normalized
            for token in ("agente", "especialista", "selecionar agente", "qual agente")
        ):
            return "agent"

        return None

    @classmethod
    def _answer_topic_help(cls, key: str) -> str | None:
        from app.application.services.assistant_capabilities_registry import (
            AssistantCapabilitiesRegistry,
        )

        topic_by_key = {
            "canvasHelp": "canvas",
            "chartHelp": "chart",
            "attachmentHelp": "attachment",
            "agentHelp": "agent",
            "webSearchHelp": "web",
            "stockHelp": "stock_lookup",
            "destructiveAction": None,
            "permissionsHelp": None,
            "textTasksHelp": "text_tasks",
        }
        registry_topic = topic_by_key.get(key)

        if registry_topic and not str(registry_topic).endswith("_lookup"):
            feature = AssistantCapabilitiesRegistry.find_by_help_topic(registry_topic)
        elif registry_topic == "stock_lookup":
            feature = AssistantCapabilitiesRegistry.get_feature("stock_lookup")
        else:
            feature = None

        if feature:
            formatted = cls._format_catalog_feature_help(feature)

            if formatted:
                return formatted

        texts = _feature_answers().get(key) or {}

        if not isinstance(texts, dict):
            return None

        title = str(texts.get("title") or "").strip()
        body = str(texts.get("body") or texts.get("enabled") or "").strip()

        if title and body:
            return f"{title}\n\n{body}".strip()

        return body or None

    @classmethod
    def _format_catalog_feature_help(cls, feature: dict) -> str | None:
        title = str(feature.get("title") or "").strip()
        summary = str(feature.get("summary") or "").strip()
        how_to = feature.get("howToUse") or []
        examples = feature.get("examples") or []

        if not title and not summary:
            return None

        lines = [f"**{title}**" if title else "", "", summary, ""]

        if isinstance(how_to, list) and how_to:
            lines.append("**Como usar:**")
            lines.extend(f"- {str(item).strip()}" for item in how_to if str(item).strip())
            lines.append("")

        if isinstance(examples, list) and examples:
            lines.append("**Exemplos:**")
            lines.extend(f"- «{str(item).strip()}»" for item in examples[:4] if str(item).strip())

        return "\n".join(line for line in lines if line is not None).strip()

    @classmethod
    def _is_stock_help_inquiry(cls, normalized: str) -> bool:
        return "estoque" in normalized and cls._is_how_to_help_inquiry(normalized)

    @classmethod
    def _is_text_tasks_help_inquiry(cls, normalized: str) -> bool:
        return any(
            token in normalized
            for token in ("corrige", "corrigir", "texto", "textos", "traduz", "reescreve")
        ) and cls._is_ability_question(normalized, normalized)

    @classmethod
    def _is_destructive_capability_inquiry(cls, normalized: str) -> bool:
        if not cls._is_ability_question(normalized, normalized):
            return False

        return any(
            token in normalized
            for token in ("excluir", "deletar", "apagar", "remover", "alterar cadastro", "criar produto")
        )

    @classmethod
    def _is_permission_help_inquiry(cls, normalized: str) -> bool:
        markers = (
            "por que nao",
            "por que não",
            "nao consigo",
            "não consigo",
            "sem acesso",
            "sem permiss",
            "nao tenho acesso",
            "não tenho acesso",
        )

        return any(marker in normalized for marker in markers)

    @classmethod
    def _is_how_to_help_inquiry(cls, normalized: str) -> bool:
        return any(
            term in normalized
            for term in (
                "como ",
                "como faço",
                "como faco",
                "como uso",
                "como usar",
                "como consulto",
                "como consultar",
            )
        )

    @classmethod
    def _is_web_search_help_inquiry(cls, normalized: str) -> bool:
        if "web" not in normalized and "internet" not in normalized:
            return False

        help_markers = (
            "como ",
            "como faço",
            "como faco",
            "como uso",
            "como usar",
            "me ensine",
            "me explique",
            "o que e",
            "o que é",
        )

        search_markers = (
            "pesquisa",
            "pesquisar",
            "busca",
            "buscar",
            "web",
            "internet",
            "google",
        )

        return any(marker in normalized for marker in help_markers) and any(
            marker in normalized for marker in search_markers
        )

    @classmethod
    def _answer_web_search_help(cls) -> str:
        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        texts = _feature_answers().get("webSearchHelp") or {}
        title = str(texts.get("title") or "**Pesquisa na internet**")
        body_key = "enabled" if ChatWebSearchIntentService.is_feature_enabled() else "disabled"
        body = str(texts.get(body_key) or texts.get("enabled") or "")

        return f"{title}\n\n{body}".strip()

    @classmethod
    def _answer_product_search_by_group(
        cls,
        *,
        workspace_context: dict,
        allowed: list[str],
        catalog: list[dict],
    ) -> str:
        texts = _feature_answers().get("productSearchByGroup") or {}
        title = str(texts.get("title") or "**Busca por grupo**")
        agent = workspace_context.get("agent") or {}
        agent_name = str(agent.get("name") or "").strip()

        if not allowed:
            body = str(texts.get("commonChat") or "")
            return f"{title}\n\n{body}".strip()

        search_action = cls._find_product_search_action(catalog, allowed)

        if not search_action:
            body = str(texts.get("unsupportedAction") or "")
            return f"{title}\n\n{body}".strip()

        if not cls._action_supports_parameter(search_action, "group_code", "groupcode"):
            body = str(texts.get("unsupportedParam") or "")
            return f"{title}\n\n{body}".strip()

        body = str(texts.get("supported") or "")
        if agent_name:
            body = body.replace("Neste agente", f"No agente **{agent_name}**", 1)

        return f"{title}\n\n{body}".strip()

    @classmethod
    def _answer_product_search_by_description(
        cls,
        *,
        workspace_context: dict,
        allowed: list[str],
        catalog: list[dict],
    ) -> str:
        texts = _feature_answers().get("productSearchByDescription") or {}
        title = str(texts.get("title") or "**Busca por descrição**")

        if not allowed:
            body = str(texts.get("commonChat") or "")
            return f"{title}\n\n{body}".strip()

        search_action = cls._find_product_search_action(catalog, allowed)

        if not search_action:
            body = str(texts.get("unsupportedAction") or "")
            return f"{title}\n\n{body}".strip()

        body = str(texts.get("supported") or "")
        return f"{title}\n\n{body}".strip()

    @classmethod
    def _find_product_search_action(
        cls,
        catalog: list[dict],
        allowed_ids: list[str],
    ) -> dict | None:
        allowed_set = set(allowed_ids)

        for action in catalog:
            action_id = str(action.get("actionId") or "").strip()

            if action_id not in allowed_set:
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if "search" in path or "search" in operation_id:
                return action

        return None

    @classmethod
    def _action_supports_parameter(cls, action: dict, *names: str) -> bool:
        expected = {name.lower() for name in names}

        for parameter in action.get("parametersSchema") or []:
            if not isinstance(parameter, dict):
                continue

            name = str(parameter.get("name") or "").lower()

            if name in expected:
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
        content = _capabilities_content()
        sections = _sections()
        lines: list[str] = [
            str(content.get("intro") or "Posso ajudar você nestes formatos:"),
            "",
            str(sections.get("alwaysAvailableTitle") or "**Sempre disponíveis (chat comum e agentes)**"),
        ]

        for tool in sections.get("platformTools") or []:
            if isinstance(tool, dict) and tool.get("description"):
                lines.append(f"- {tool['description']}")

        for item in sections.get("alwaysAvailableItems") or []:
            lines.append(f"- {item}")

        skills = workspace_context.get("skills") or {}
        skill_lines = cls._format_skills_section(skills, workspace_context.get("allowedActionIds"))
        if skill_lines:
            lines.extend(["", str(sections.get("skillsTitle") or "**Skills (comportamento do assistente)**")])
            lines.extend(skill_lines)

        agent = workspace_context.get("agent") or {}
        agent_name = str(agent.get("name") or "").strip()
        allowed = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]

        if allowed and action_catalog:
            title_template = str(
                sections.get("operationalWithAgentTitle")
                or "**Consultas operacionais — agente {agent_name}**"
            )
            lines.extend(["", title_template.format(agent_name=agent_name or "atual")])
            lines.append(str(sections.get("operationalWithAgentIntro") or ""))
            lines.append("")
            lines.extend(cls._format_action_catalog(action_catalog, allowed))
        else:
            lines.extend(
                [
                    "",
                    str(
                        sections.get("operationalCommonTitle")
                        or "**Consultas operacionais (produto, estoque, LMP, fornecedores…)**"
                    ),
                ]
            )
            for item in sections.get("operationalCommonItems") or []:
                lines.append(f"- {item}")
            prefix = str(_catalog_texts().get("examplePrefix") or "  - Ex.: *{example}*")
            for example in _common_chat_examples():
                lines.append(prefix.format(example=example))

        lines.extend(["", str(sections.get("tipsTitle") or "**Dicas**")])
        for item in sections.get("tipsItems") or []:
            lines.append(f"- {item}")

        lines.extend(cls._format_business_suggestions(content))

        return "\n".join(lines)

    @classmethod
    def _format_business_suggestions(cls, content: dict) -> list[str]:
        rich = content.get("richExamples") or {}
        combined = content.get("combinedQuestions") or []

        if not rich and not combined:
            return []

        section_titles = content.get("richExampleTitles") or {}
        lines: list[str] = ["", str(section_titles.get("header") or "**Perguntas úteis (negócio)**")]

        for key, examples in rich.items():
            if not isinstance(examples, list) or not examples:
                continue

            title = str(section_titles.get(key) or key.replace("_", " ").title())
            lines.append(f"**{title}**")

            for example in examples[:4]:
                lines.append(f"- *{example}*")

        if combined:
            lines.append("")
            lines.append(
                str(
                    section_titles.get("combinedHeader")
                    or "**Perguntas que cruzam várias fontes**"
                )
            )

            for example in combined[:6]:
                lines.append(f"- *{example}*")

        return lines

    @classmethod
    def _format_skills_section(
        cls,
        skills: dict,
        allowed_action_ids: list[str] | None,
    ) -> list[str]:
        texts = _skills_texts()
        lines: list[str] = []
        allowed = allowed_action_ids or []

        if skills.get("sqlAuthoring"):
            lines.append(str(texts.get("sqlAuthoringOn") or ""))
        else:
            lines.append(str(texts.get("sqlAuthoringOff") or ""))

        if skills.get("sqlExecutionAvailable"):
            lines.append(str(texts.get("sqlExecutionOn") or ""))
        elif allowed:
            lines.append(str(texts.get("sqlExecutionOffWithActions") or ""))
        else:
            lines.append(str(texts.get("sqlExecutionOff") or ""))

        skills_vs_actions = texts.get("skillsVsActions")
        if skills_vs_actions:
            lines.append(str(skills_vs_actions))

        return lines

    @classmethod
    def _format_action_catalog(cls, catalog: list[dict], allowed_ids: list[str]) -> list[str]:
        catalog_texts = _catalog_texts()
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
            empty = catalog_texts.get("emptyActions")
            return [str(empty or "- Nenhuma action detalhada no catálogo; verifique a configuração do agente.")]

        output: list[str] = []
        max_per_category = 8
        line_with_path = str(
            catalog_texts.get("actionLineWithPath") or "- {summary} — `{method} {path}`"
        )
        line_plain = str(catalog_texts.get("actionLine") or "- {summary}")
        example_prefix = str(catalog_texts.get("examplePrefix") or "  - Ex.: *{example}*")
        more_actions = str(
            catalog_texts.get("moreActions") or "- … e mais {count} action(s) nesta categoria"
        )

        for category in sorted(by_category.keys()):
            items = by_category[category]
            output.append(f"**{category}**")
            shown_examples: set[str] = set()

            for item in items[:max_per_category]:
                summary = item["summary"]
                path = item["path"]
                method = item["method"]
                if path:
                    line = line_with_path.format(summary=summary, method=method, path=path)
                else:
                    line = line_plain.format(summary=summary)
                output.append(line)

                for ex in item.get("examples") or ():
                    if ex not in shown_examples and len(shown_examples) < 3:
                        output.append(example_prefix.format(example=ex))
                        shown_examples.add(ex)

            if len(items) > max_per_category:
                output.append(more_actions.format(count=len(items) - max_per_category))
            output.append("")

        return output

    @classmethod
    def _resolve_path_rule(cls, path: str) -> tuple[str, tuple[str, ...]]:
        lowered = path.lower()
        for token, category, examples in _path_rules():
            if token in lowered:
                return category, examples
        return _path_rule_default()

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
