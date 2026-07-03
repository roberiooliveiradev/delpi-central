from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache

from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort
from app.domain.services.chat_capabilities_catalog_answer_service import (
    ChatCapabilitiesCatalogAnswerService,
)
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


_external_action_repository_loader: Callable[[], ExternalActionRepositoryPort] | None = None


def configure_external_action_repository_loader(
    loader: Callable[[], ExternalActionRepositoryPort],
) -> None:
    global _external_action_repository_loader
    _external_action_repository_loader = loader


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


@lru_cache(maxsize=1)
def _self_help_agent_context() -> dict:
    return _capabilities_content().get("selfHelpAgentContext") or {}


@lru_cache(maxsize=1)
def _operational_query_patterns() -> tuple[str, ...]:
    patterns = _detection().get("operationalQueryPatterns") or []
    return tuple(str(item) for item in patterns if str(item).strip())


@lru_cache(maxsize=1)
def _operational_data_topics() -> tuple[str, ...]:
    topics = _detection().get("operationalDataTopics") or []
    return tuple(str(item) for item in topics if str(item).strip())


@lru_cache(maxsize=1)
def _supplies_kpi_terms() -> tuple[str, ...]:
    terms = _detection().get("suppliesKpiTerms") or []
    return tuple(str(item) for item in terms if str(item).strip())


@lru_cache(maxsize=1)
def _supplies_kpi_qual_pattern() -> str:
    return str(_detection().get("suppliesKpiQualPattern") or r"\bqual\s+(o|a)\s+")


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

    @classmethod
    def is_capability_inquiry(cls, message: str) -> bool:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        if ChatSqlIntentService.is_sql_conversation_turn(message):
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if cls.is_capabilities_question(message):
            return True

        if cls.is_release_notes_question(message):
            return True

        if cls._is_permission_help_inquiry(normalized):
            return True

        if cls.is_help_about_topic_inquiry(message):
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

        if cls.is_api_action_routes_inquiry(message):
            return cls.build_api_action_routes_answer(
                workspace_context=workspace_context,
                allowed_action_ids=allowed_action_ids,
                action_catalog=action_catalog,
            )

        if cls.is_help_about_topic_inquiry(message):
            help_about = cls.build_help_about_answer(
                message=message,
                workspace_context=workspace_context,
                allowed_action_ids=allowed_action_ids,
                action_catalog=action_catalog,
            )

            if help_about:
                return help_about

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
        from app.domain.services.chat_capabilities_detection_service import (
            ChatCapabilitiesDetectionService,
        )

        return ChatCapabilitiesDetectionService.is_capabilities_question(message)

    @classmethod
    def is_api_action_routes_inquiry(cls, message: str) -> bool:
        from app.domain.services.chat_capabilities_detection_service import (
            ChatCapabilitiesDetectionService,
        )

        return ChatCapabilitiesDetectionService.is_api_action_routes_inquiry(message)

    @classmethod
    def build_api_action_routes_answer(
        cls,
        *,
        workspace_context: dict,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
    ) -> str | None:
        return ChatCapabilitiesCatalogAnswerService.build_action_routes_answer(
            workspace_context=workspace_context,
            allowed_action_ids=allowed_action_ids,
            action_catalog=action_catalog,
        )

    @classmethod
    def _is_feature_capability_inquiry(cls, message: str) -> bool:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        if ChatSqlIntentService.is_sql_conversation_turn(message):
            return False

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
    def looks_like_operational_data_request(
        cls,
        message: str,
        normalized: str | None = None,
    ) -> bool:
        """Consulta operacional real (ex.: estoque de produto), não pergunta «consegue?»."""
        return cls._looks_like_operational_data_request(message, normalized=normalized)

    @classmethod
    def _looks_like_operational_data_request(cls, message: str, normalized: str | None = None) -> bool:
        """Consulta operacional real (ex.: estoque de produto), não pergunta «consegue?»."""
        normalized = normalized or ChatMessageNormalizationService.normalize_for_matching(message)

        from app.domain.services.chat_department_kpi_intent_service import (
            ChatDepartmentKpiIntentService,
        )
        from app.domain.services.chat_sql_operational_intent_service import (
            ChatSqlOperationalIntentService,
        )

        if ChatDepartmentKpiIntentService.resolve(message):
            return True

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return True

        if cls._looks_like_supplies_kpi_request(message, normalized):
            return True

        if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            return True

        from app.domain.services.chat_operational_follow_up_routing_service import (
            ChatOperationalFollowUpRoutingService,
        )

        if ChatOperationalFollowUpRoutingService.blocks_capability_inquiry(
            message,
            normalized=normalized,
            operational_data_topics=_operational_data_topics(),
        ):
            return True

        if any(
            re.search(pattern, normalized) for pattern in _operational_query_patterns()
        ):
            return True

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        product_code = ChatProductQueryIntentService.extract_product_code(message)

        if product_code and any(
            topic in normalized for topic in _operational_data_topics()
        ):
            return True

        if product_code and not any(marker in normalized for marker in cls._INQUIRY_MARKERS):
            return True

        if cls._looks_like_operational_command(normalized) and any(
            topic in normalized for topic in _operational_data_topics()
        ):
            return True

        return False

    @classmethod
    def _looks_like_supplies_kpi_request(cls, message: str, normalized: str) -> bool:
        """KPIs de suprimentos (CPV, OTD, giro…) — não confundir com «consegue consultar cpv?»."""
        if not any(term in normalized for term in _supplies_kpi_terms()):
            return False

        if any(marker in normalized for marker in cls._INQUIRY_MARKERS):
            return False

        if re.search(_supplies_kpi_qual_pattern(), normalized):
            return True

        return "?" not in str(message or "").strip()

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
            "textTasksHelp": "text",
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
    def is_help_about_topic_inquiry(cls, message: str) -> bool:
        from app.domain.services.chat_capabilities_detection_service import (
            ChatCapabilitiesDetectionService,
        )

        return ChatCapabilitiesDetectionService.is_help_about_topic_inquiry(message)

    @classmethod
    def extract_help_about_topic(cls, message: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        prefixes = tuple(str(item) for item in (_detection().get("helpAboutPrefixes") or ()))

        for prefix in prefixes:
            if normalized.startswith(prefix):
                return normalized[len(prefix) :].strip()

        return normalized.strip()

    @classmethod
    def build_help_about_answer(
        cls,
        *,
        message: str,
        workspace_context: dict,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
    ) -> str | None:
        from app.application.services.assistant_capabilities_registry import (
            AssistantCapabilitiesRegistry,
        )

        topic = cls.extract_help_about_topic(message)

        if not topic:
            return None

        feature = AssistantCapabilitiesRegistry.find_by_help_topic(topic)

        if not feature:
            for candidate in AssistantCapabilitiesRegistry.search(topic, limit=1):
                feature = candidate
                break

        if feature:
            formatted = cls._format_catalog_feature_help(feature)

            if formatted:
                intro = cls._self_help_context_intro(workspace_context)

                if intro:
                    return f"{intro}\n\n{formatted}".strip()

                return formatted

        texts = _feature_answers().get("helpAboutFallback") or {}

        if isinstance(texts, dict):
            title = str(texts.get("title") or "").strip()
            body = str(texts.get("body") or "").format(topic=topic).strip()

            if title and body:
                return f"{title}\n\n{body}".strip()

        return None

    @classmethod
    def _self_help_context_intro(cls, workspace_context: dict) -> str | None:
        return ChatCapabilitiesCatalogAnswerService.self_help_context_intro(workspace_context)

    @classmethod
    def build_direct_answer(
        cls,
        *,
        workspace_context: dict,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
    ) -> str | None:
        return ChatCapabilitiesCatalogAnswerService.build_direct_answer(
            workspace_context=workspace_context,
            allowed_action_ids=allowed_action_ids,
            action_catalog=action_catalog,
        )

    @classmethod
    def _format_business_suggestions(cls, content: dict) -> list[str]:
        return ChatCapabilitiesCatalogAnswerService.format_business_suggestions(content)

    @classmethod
    def _format_skills_section(
        cls,
        skills: dict,
        allowed_action_ids: list[str] | None,
    ) -> list[str]:
        return ChatCapabilitiesCatalogAnswerService.format_skills_section(
            skills,
            allowed_action_ids,
        )

    @classmethod
    def _format_action_catalog(cls, catalog: list[dict], allowed_ids: list[str]) -> list[str]:
        return ChatCapabilitiesCatalogAnswerService.format_action_catalog(catalog, allowed_ids)

    @classmethod
    def _resolve_path_rule(cls, path: str) -> tuple[str, tuple[str, ...]]:
        return ChatCapabilitiesCatalogAnswerService.resolve_path_rule(path)

    @classmethod
    def load_action_catalog_for_agent(
        cls,
        allowed_action_ids: list[str] | None,
        *,
        action_repository: ExternalActionRepositoryPort | None = None,
    ) -> list[dict]:
        if not allowed_action_ids:
            return []

        repository = action_repository
        if repository is None and _external_action_repository_loader is not None:
            try:
                repository = _external_action_repository_loader()
            except Exception:
                repository = None

        if repository is None:
            return []

        try:
            catalog = repository.list_actions()
            allowed_set = {str(item).strip() for item in allowed_action_ids}
            return [
                item
                for item in catalog
                if str(item.get("actionId") or "") in allowed_set
            ]
        except Exception:
            return []
