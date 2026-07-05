"""Delegate — especialista SQL avançado."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from app.domain.services.chat_message_normalization_service import ChatMessageNormalizationService
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_intent_vocabulary_service import ChatSqlIntentVocabularyService
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prompt_service import (
    ChatAdvancedSqlSpecialistPromptService,
)

from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_constants import (
    SQL_BLOCK_RE as _SQL_BLOCK_RE,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_facade_access import (
    sql_specialist_service,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_types import (
    SqlSpecialistMode,
    _interactivity_content,
)



class ChatAdvancedSqlSpecialistSchemaPrefetchService:
    _CLIENT_PRESENTATION_KEYS = (
        "presentation",
        "tablePresentation",
        "textPresentation",
        "treePresentation",
        "chartPresentation",
        "presentationDecision",
        "dataCoverageNotice",
        "renderPlan",
    )

    @classmethod
    def is_table_search_prefetch_path(cls, path: str | None) -> bool:
        return "/system/tables/search" in str(path or "").lower()

    @classmethod
    def is_schema_prefetch_path(cls, path: str | None) -> bool:
        lowered = str(path or "").lower()

        return "/system/tables" in lowered and (
            "/columns" in lowered or "/schema" in lowered or "/relations" in lowered
        )

    @classmethod
    def is_system_table_metadata_path(cls, path: str | None) -> bool:
        return cls.is_table_search_prefetch_path(path) or cls.is_schema_prefetch_path(path)

    @classmethod
    def should_treat_schema_as_internal(cls, message: str | None, *, path: str | None) -> bool:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        path_str = str(path or "")

        if cls.is_table_search_prefetch_path(path_str):
            return ChatSqlIntentService.is_authoring_request(message)

        if not cls.is_schema_prefetch_path(path_str):
            return False

        if ChatSqlIntentService.is_authoring_request(message):
            return True

        mode = sql_specialist_service().classify_mode(message)

        return mode in {
            "create",
            "review",
            "explain",
            "optimize",
            "incremental_edit",
            "schema_explore",
        }

    @classmethod
    def turn_has_only_sql_schema_prefetch(cls, tool_calls: list | None) -> bool:
        if not isinstance(tool_calls, list):
            return False

        successful_external: list[dict] = []

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata") or {}

            if not metadata.get("ok"):
                continue

            status_code = metadata.get("statusCode")

            try:
                if not (200 <= int(status_code) < 300):
                    continue
            except (TypeError, ValueError):
                continue

            successful_external.append(tool_call)

        if not successful_external:
            return False

        return all(
            (tool_call.get("metadata") or {}).get("sqlSchemaPrefetch")
            for tool_call in successful_external
        )

    @classmethod
    def _strip_client_presentation_from_metadata(cls, metadata: dict) -> dict:
        cleaned = dict(metadata)

        for key in cls._CLIENT_PRESENTATION_KEYS:
            cleaned.pop(key, None)

        return cleaned

    @classmethod
    def annotate_schema_prefetch_tool_metadata(
        cls,
        message: str | None,
        metadata: dict | None,
    ) -> dict:
        meta = dict(metadata or {})

        if not sql_specialist_service().should_treat_schema_as_internal(message, path=str(meta.get("path") or "")):
            return meta

        meta["sqlSchemaPrefetch"] = True
        meta["suppressClientPresentation"] = True
        meta["preferredFormat"] = "text"
        meta["currentMessage"] = str(message or "")

        return cls._strip_client_presentation_from_metadata(meta)

    @classmethod
    def strip_schema_catalog_presentations(cls, result: dict) -> dict:
        updated = dict(result)
        tool_calls = updated.get("toolCalls")

        if not isinstance(tool_calls, list):
            return updated

        stripped_calls: list[dict] = []

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                stripped_calls.append(tool_call)
                continue

            item = dict(tool_call)
            metadata = dict(item.get("metadata") or {})

            if (
                metadata.get("sqlSchemaPrefetch")
                or metadata.get("suppressClientPresentation")
                or sql_specialist_service().is_schema_prefetch_path(str(metadata.get("path") or ""))
            ):
                for key in (
                    "presentation",
                    "tablePresentation",
                    "textPresentation",
                    "treePresentation",
                    "chartPresentation",
                    "presentationDecision",
                ):
                    metadata.pop(key, None)

                metadata["suppressClientPresentation"] = True
                metadata.pop("dataCoverageNotice", None)
                metadata["humanizedSummary"] = {
                    "titulo": ChatSqlIntentVocabularyService.text(
                        "advancedSqlSpecialist",
                        "schemaExplore",
                        "internalTitle",
                    ),
                    "linhas": list(
                        ChatSqlIntentVocabularyService.terms(
                            "advancedSqlSpecialist",
                            "schemaExplore",
                            "internalLines",
                        )
                    ),
                }

            item["metadata"] = metadata
            stripped_calls.append(item)

        updated["toolCalls"] = stripped_calls

        return updated

    @classmethod
    def sanitize_tool_calls_for_client(cls, tool_calls: list | None) -> list:
        if not isinstance(tool_calls, list):
            return []

        return sql_specialist_service().strip_schema_catalog_presentations({"toolCalls": tool_calls}).get(
            "toolCalls",
            [],
        )

    @classmethod
    def compact_schema_prefetch_context(
        cls,
        *,
        message: str | None,
        data: object,
        metadata: dict | None,
    ) -> dict[str, object]:
        path = str((metadata or {}).get("path") or "")

        if cls.is_table_search_prefetch_path(path):
            return cls._compact_table_search_prefetch_context(data=data)

        table_match = re.search(r"/system/tables/([A-Za-z0-9]+)", path, flags=re.IGNORECASE)
        table_name = table_match.group(1).upper() if table_match else "tabela"

        if "/relations" in path.lower():
            from app.domain.services.chat_sql_schema_discovery_service import (
                ChatSqlSchemaDiscoveryService,
            )

            payload = data.get("data") if isinstance(data, dict) and "data" in data else data
            relations = ChatSqlSchemaDiscoveryService._parse_relation_results(
                payload if isinstance(payload, dict) else {}
            )
            relation_lines = [
                (
                    f"{item['sourceTable']}.{item['sourceField']} → "
                    f"{item['targetTable']}.{item['targetField']}"
                )
                for item in relations[:10]
                if isinstance(item, dict)
            ]
            example_sql = ChatAdvancedSqlSpecialistPromptService._example_join_sql_for_tables([table_name, "SA1", "SC5"])

            return {
                "titulo": ChatSqlIntentVocabularyService.format(
                    "advancedSqlSpecialist",
                    "schemaRelations",
                    "userTitle",
                    table_name=table_name,
                ),
                "linhas": [
                    ChatSqlIntentVocabularyService.format(
                        "advancedSqlSpecialist",
                        "schemaRelations",
                        "tableLine",
                        table_name=table_name,
                        count=str(len(relation_lines)),
                    ),
                    *(
                        [
                            ChatSqlIntentVocabularyService.text(
                                "advancedSqlSpecialist",
                                "schemaRelations",
                                "fkPrefix",
                            )
                            + line
                            for line in relation_lines
                        ]
                        if relation_lines
                        else [
                            ChatSqlIntentVocabularyService.text(
                                "advancedSqlSpecialist",
                                "schemaRelations",
                                "noFkFallback",
                            )
                        ]
                    ),
                    ChatSqlIntentVocabularyService.text(
                        "advancedSqlSpecialist",
                        "schemaRelations",
                        "deliveryHint",
                    ),
                    *(
                        [
                            ChatSqlIntentVocabularyService.text(
                                "advancedSqlSpecialist",
                                "schemaRelations",
                                "examplePrefix",
                            )
                            + example_sql
                        ]
                        if example_sql
                        else []
                    ),
                ],
            }

        columns = cls._extract_column_names_from_schema_payload(data)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        prioritized: list[str] = []

        for token in ("a1_cod", "a1_nome", "d_e_l_e_t_", "cod", "nome", "ativo"):
            for column in columns:
                if token in column.lower() and column not in prioritized:
                    prioritized.append(column)

        for column in columns:
            if column not in prioritized:
                prioritized.append(column)

            if len(prioritized) >= 12:
                break

        active_hint = (
            ChatSqlIntentVocabularyService.text(
                "advancedSqlSpecialist",
                "schemaExplore",
                "activeFilterHint",
            )
            if "ativ" in normalized
            else ChatSqlIntentVocabularyService.text(
                "advancedSqlSpecialist",
                "schemaExplore",
                "defaultDeleteHint",
            )
        )

        return {
            "titulo": ChatSqlIntentVocabularyService.format(
                "advancedSqlSpecialist",
                "schemaExplore",
                "userTitle",
                table_name=table_name,
            ),
            "linhas": [
                ChatSqlIntentVocabularyService.format(
                    "advancedSqlSpecialist",
                    "schemaExplore",
                    "columnCountLine",
                    table_name=table_name,
                    count=str(len(columns)),
                ),
                ChatSqlIntentVocabularyService.format(
                    "advancedSqlSpecialist",
                    "schemaExplore",
                    "columnsLine",
                    columns=", ".join(prioritized) if prioritized else "validar no SX3",
                ),
                active_hint,
                ChatSqlIntentVocabularyService.text(
                    "advancedSqlSpecialist",
                    "schemaExplore",
                    "deliveryHint",
                ),
                ChatSqlIntentVocabularyService.text(
                    "advancedSqlSpecialist",
                    "schemaExplore",
                    "columnNamesHint",
                ),
                ChatSqlIntentVocabularyService.text(
                    "advancedSqlSpecialist",
                    "schemaExplore",
                    "noMetadataOnlyHint",
                ),
            ],
        }

    @classmethod
    def _compact_table_search_prefetch_context(cls, *, data: object) -> dict[str, object]:
        payload = data.get("data") if isinstance(data, dict) and "data" in data else data
        candidates: list[str] = []

        if isinstance(payload, dict):
            raw_results = payload.get("results") or payload.get("items") or []

            if isinstance(raw_results, list):
                for item in raw_results[:8]:
                    if not isinstance(item, dict):
                        continue

                    arquivo = str(item.get("X2_ARQUIVO") or item.get("x2_arquivo") or "").strip()
                    nome = str(item.get("X2_NOME") or item.get("x2_nome") or "").strip()
                    chave = str(item.get("X2_CHAVE") or item.get("x2_chave") or "").strip()

                    if arquivo and nome:
                        candidates.append(f"{arquivo} — {nome}")
                    elif chave and nome:
                        candidates.append(f"{chave} — {nome}")
                    elif arquivo:
                        candidates.append(arquivo)

        return {
            "titulo": ChatSqlIntentVocabularyService.text(
                "advancedSqlSpecialist",
                "schemaTableSearch",
                "userTitle",
            ),
            "linhas": [
                ChatSqlIntentVocabularyService.format(
                    "advancedSqlSpecialist",
                    "schemaTableSearch",
                    "resultsLine",
                    tables=", ".join(candidates)
                    if candidates
                    else ChatSqlIntentVocabularyService.text(
                        "advancedSqlSpecialist",
                        "schemaTableSearch",
                        "emptyFallback",
                    ),
                ),
                ChatSqlIntentVocabularyService.text(
                    "advancedSqlSpecialist",
                    "schemaTableSearch",
                    "hintLine",
                ),
                ChatSqlIntentVocabularyService.text(
                    "advancedSqlSpecialist",
                    "schemaExplore",
                    "deliveryHint",
                ),
                ChatSqlIntentVocabularyService.text(
                    "advancedSqlSpecialist",
                    "schemaExplore",
                    "noMetadataOnlyHint",
                ),
            ],
        }

