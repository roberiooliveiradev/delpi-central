"""Guia interativo para elaborar SQL Protheus usando metadados /system/tables."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_domain_config_service import ChatDomainConfigService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("interactivity")


class ChatSqlAuthoringGuidanceService:
    _TABLE_CODE_RE = re.compile(r"\b([A-Z]{2,4}\d{0,4})\b", re.IGNORECASE)
    # Palavras funcionais que aparecem após "tabela"/"colunas de" e NÃO são nome de
    # tabela (ex.: "qual a tabela QUE guarda informações de produto?" → "que" é
    # pronome, não a tabela QUE). Sem isto o prefetch buscava o schema errado.
    _TABLE_NAME_STOPWORDS = frozenset(
        {
            "que", "de", "do", "da", "dos", "das", "com", "para", "pra", "por",
            "sobre", "onde", "qual", "quais", "essa", "esse", "esta", "este",
            "isso", "isto", "uma", "uns", "umas", "sua", "seu", "suas", "seus",
            "tem", "num", "numa", "dele", "dela", "deles", "delas", "ou", "em",
            "no", "na", "nos", "nas", "ao", "aos", "se", "como", "qro", "quero",
            "guarda", "guardam", "armazena", "contem", "possui",
        }
    )
    _DOMAIN_HINT_PATTERNS = (
        r"(?:monte|crie|gera|gere|elabore|escreva|construa|construir|ajuste|corrija|refine)\s+"
        r"(?:uma\s+)?(?:consulta|query|sql)\s+(?:de|sobre|para|com|que)\s+(.+?)(?:\?|$)",
        r"(?:consulta|query|sql)\s+(?:de|sobre|para|com|que)\s+(.+?)(?:\?|$)",
        r"(?:preciso|quero)\s+(?:de\s+)?(?:uma\s+)?(?:consulta|query|sql)\s+(?:de|sobre|para|que)\s+(.+?)(?:\?|$)",
        r"(?:use\s+)?sql\s+para\s+(?:construir\s+)?(?:uma\s+)?(?:query|consulta)\s+(?:que\s+)?(.+?)(?:\?|$)",
    )

    @classmethod
    def is_custom_sql_authoring(cls, message: str | None) -> bool:
        if not ChatSqlIntentService.is_authoring_request(message):
            return False

        if ChatSqlIntentService.should_auto_execute_sql(message):
            return False

        from app.domain.services.chat_sql_inventory_query_service import (
            ChatSqlInventoryQueryService,
        )
        from app.domain.services.chat_sql_production_query_service import (
            ChatSqlProductionQueryService,
        )

        for resolver in (ChatSqlInventoryQueryService, ChatSqlProductionQueryService):
            resolution = resolver.resolve(message)

            if resolution and resolution.mode == "execute":
                return False

        return True

    @classmethod
    def agent_actions_available(cls, workspace_context: dict | None) -> bool:
        """Prefetch/execução de schema SQL exige agente com actions — chat base não chama API."""
        ctx = workspace_context or {}
        allowed = ctx.get("allowedActionIds") or ctx.get("allowed_action_ids") or []

        return bool(ctx.get("actionsEnabled")) and bool(allowed)

    @classmethod
    def should_prefetch_schema(
        cls,
        *,
        message: str,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        if not cls.agent_actions_available(workspace_context):
            return False

        if not cls.is_custom_sql_authoring(message):
            return False

        skills = (workspace_context or {}).get("skills") or {}
        sql_authoring = skills.get("sqlAuthoring")

        if sql_authoring is None:
            sql_authoring = ChatDomainConfigService.chat_default_sql_authoring_skill_enabled()

        if not sql_authoring:
            return False

        if cls._has_recent_system_metadata(previous_messages):
            return False

        table_name = cls.extract_table_name(message)

        if table_name:
            return True

        return bool(
            cls.extract_table_domain_entity(message) or cls.extract_domain_hint(message)
        )

    @classmethod
    def extract_table_names(cls, message: str | None) -> list[str]:
        primary = cls.extract_table_name(message)

        if primary:
            tables = [primary]
        else:
            tables = []

        raw = str(message or "")
        seen = {item.upper() for item in tables}

        for token in cls._TABLE_CODE_RE.findall(raw):
            candidate = str(token).upper()

            if not re.fullmatch(r"[A-Z]{2,4}\d{0,4}", candidate):
                continue

            if not re.search(r"\d", candidate):
                continue

            if candidate in seen:
                continue

            seen.add(candidate)
            tables.append(candidate)

        return tables[:3]

    @classmethod
    def plan_schema_prefetch(
        cls,
        selection_service,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
    ) -> list[dict]:
        if not selection_service or not allowed_action_ids:
            return []

        planned: list[dict] = []
        table_names = cls.extract_table_names(message)
        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        wants_relations = any(
            term in normalized
            for term in ("relacion", "relacionar", "join", "ligar", "associar", "chave estrangeira", "fk ")
        )

        for table_name in table_names:
            prompt = (
                f"relacionamentos da tabela {table_name}"
                if wants_relations
                else f"colunas da tabela {table_name}"
            )
            selected = selection_service.select_system_metadata(
                prompt,
                allowed_action_ids,
            )

            if selected and not cls._contains_same_action(planned, selected):
                planned.append(selected)

        if planned:
            return planned[:3]

        domain = cls.extract_table_domain_entity(message) or cls.extract_domain_hint(message)

        if not domain:
            return []

        search_message = f"qual a tabela de {domain}"
        selected = selection_service.select_system_metadata(
            search_message,
            allowed_action_ids,
        )

        if selected:
            planned.append(selected)

        return planned

    @classmethod
    def build_follow_up_suggestions(
        cls,
        *,
        message: str,
        tool_calls: list | None,
    ) -> list[dict[str, str]]:
        if not cls.is_custom_sql_authoring(message) and not cls._has_system_metadata_tool(
            tool_calls
        ):
            return []

        chips = list((_content().get("sqlAuthoringChips") or {}).get("default") or [])
        queries = _content().get("sqlAuthoringQueries") or {}
        table_name = cls.extract_table_name(message) or cls._table_from_tool_calls(tool_calls)
        suggestions: list[dict[str, str]] = []

        for label in chips[:6]:
            template = str(queries.get(label) or label).strip()

            if not template:
                continue

            query = template.replace("{{tableName}}", table_name or "SB1")
            suggestions.append({"label": str(label), "query": query})

        return suggestions

    @classmethod
    def extract_table_name(cls, message: str | None) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        raw = str(message or "")

        for pattern in (
            r"\btabela\s+([a-z]{2,4}\d{0,4})\b",
            r"\bcolunas?\s+(?:da|de)\s+([a-z]{2,4}\d{0,4})\b",
            r"\b(?:join|from)\s+([a-z]{2,4}\d{0,4})\b",
        ):
            match = re.search(pattern, normalized, flags=re.IGNORECASE)

            if match and cls._is_table_name_candidate(match.group(1)):
                return match.group(1).upper()

        for token in cls._TABLE_CODE_RE.findall(raw):
            candidate = str(token).upper()

            if not re.fullmatch(r"[A-Z]{2,4}\d{0,4}", candidate):
                continue

            if not re.search(r"\d", candidate):
                continue

            return candidate

        return None

    @classmethod
    def _is_table_name_candidate(cls, token: str | None) -> bool:
        candidate = str(token or "").strip().lower()

        if not candidate:
            return False

        # Códigos com dígito (SB1, SA1010) são sempre tabela; palavras funcionais não.
        if any(char.isdigit() for char in candidate):
            return True

        return candidate not in cls._TABLE_NAME_STOPWORDS

    @classmethod
    def extract_table_domain_entity(cls, message: str | None) -> str | None:
        """Entidade semântica após «tabela de …» (ex.: produtos, clientes)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        match = re.search(
            r"\btabela de ([a-z0-9][a-z0-9\s]{1,58}?)(?:,|\s+grupo|\s+onde|\s+com|\?|$)",
            normalized,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        entity = match.group(1).strip(" .,")

        if len(entity) < 3 or entity in cls._TABLE_NAME_STOPWORDS:
            return None

        return entity[:120]

    @classmethod
    def extract_domain_hint(cls, message: str | None) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        for pattern in cls._DOMAIN_HINT_PATTERNS:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)

            if not match:
                continue

            hint = match.group(1).strip(" .?,")

            if len(hint) >= 3:
                return hint[:120]

        return None

    @classmethod
    def _has_recent_system_metadata(cls, previous_messages: list[Any] | None) -> bool:
        assistant_turns = 0

        for item in reversed(previous_messages or []):
            role = getattr(item, "role", None) or (item.get("role") if isinstance(item, dict) else None)

            if role != "assistant":
                continue

            assistant_turns += 1

            if assistant_turns > 2:
                break

            metadata = getattr(item, "metadata", None) or (
                item.get("metadata") if isinstance(item, dict) else None
            )

            if not isinstance(metadata, dict):
                continue

            for call in metadata.get("toolCalls") or []:
                if cls._is_system_metadata_call(call):
                    return True

        return False

    @classmethod
    def _has_system_metadata_tool(cls, tool_calls: list | None) -> bool:
        return any(cls._is_system_metadata_call(call) for call in (tool_calls or []))

    @classmethod
    def _is_system_metadata_call(cls, call: Any) -> bool:
        if not isinstance(call, dict):
            return False

        path = str(call.get("path") or (call.get("metadata") or {}).get("path") or "").lower()

        return "/system/tables" in path or "/system/columns" in path

    @classmethod
    def _table_from_tool_calls(cls, tool_calls: list | None) -> str | None:
        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            args = call.get("arguments") or {}
            parameters = args.get("parameters") or {}

            if isinstance(parameters, dict):
                for key in ("tableName", "table_name", "table"):
                    raw = parameters.get(key)

                    if raw:
                        return str(raw).upper()

            metadata = call.get("metadata") or {}
            path = str(metadata.get("path") or "")

            match = re.search(r"/system/tables/([A-Za-z0-9]+)", path, flags=re.IGNORECASE)

            if match:
                return match.group(1).upper()

        return None

    @classmethod
    def _contains_same_action(cls, planned: list[dict], candidate: dict) -> bool:
        candidate_id = ((candidate.get("arguments") or {}).get("actionId"))

        for item in planned:
            action_id = ((item.get("arguments") or {}).get("actionId"))

            if action_id and action_id == candidate_id:
                return True

        return False
