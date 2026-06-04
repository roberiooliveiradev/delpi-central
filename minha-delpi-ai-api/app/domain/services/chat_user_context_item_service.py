"""Contexto livre adicionado pelo usuário — classificação automática e injeção no prompt."""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from app.domain.services.chat_manual_context_pin_service import ChatManualContextPinService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_snapshot_operational_focus import (
    ChatSnapshotOperationalFocus,
)

_MAX_CONTENT_CHARS = 12_000
_MAX_PROMPT_CHARS = 4_000
_MAX_LABEL_CHARS = 56

_BRANCH_RE = re.compile(
    r"\bfilial\s*[:\s]?\s*(\d{1,4})\b",
    re.IGNORECASE,
)
_WAREHOUSE_RE = re.compile(
    r"\barmaz[eé]m\s*[:\s]?\s*(\d{1,4}|[A-Z]{1,6})\b",
    re.IGNORECASE,
)
_TABLE_ROW_RE = re.compile(r"^\s*\|.+\|\s*$", re.MULTILINE)

_USER_CONTEXT_PROMPT_MARKER = "Contexto adicionado pelo usuário"
_USER_CONTEXT_SECTION_END_RE = re.compile(
    r"^(?:Memória ativa|Preferências|Resolução de referências|Assunto:|Contexto comprimido)",
    re.IGNORECASE | re.MULTILINE,
)


_CONVERSATION_KINDS = frozenset({"question", "answer", "turn"})
_CONTEXT_CHIP_KIND = "context"
_ENTITY_ITEM_KINDS = frozenset({"product", "branch", "warehouse"})
_OPERATIONAL_FROM_CONTEXT_KEYS = frozenset({"productCode", "branch", "warehouse"})
_PRESERVED_ENTITY_KEYS = frozenset(
    {
        "period",
        "orderId",
        "lastSqlSnippet",
        "lastAttachmentName",
        "productCodeSource",
    }
)


class ChatUserContextItemService:
    @classmethod
    def ingest(
        cls,
        *,
        content: str,
        filename: str | None = None,
        role: str | None = None,
        kind: str | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        raw = str(content or "").strip()

        if not raw and not str(filename or "").strip():
            raise ValueError("Informe texto, tabela ou arquivo para o contexto.")

        if not raw and filename:
            raw = f"Arquivo anexado ao contexto: {filename}"

        normalized_role = str(role or "").strip().lower()
        normalized_kind = str(kind or "").strip().lower()

        if normalized_role == "user" and not normalized_kind:
            normalized_kind = "question"
        elif normalized_role == "assistant" and not normalized_kind:
            normalized_kind = "answer"

        if normalized_kind in _CONVERSATION_KINDS:
            classified = cls._classify_conversation_turn(
                raw,
                kind=normalized_kind,
                role=normalized_role,
            )
        else:
            classified = cls.classify(raw, filename=filename)

        item_id = str(uuid.uuid4())
        message_token = str(message_id or "").strip()[:64]

        item: dict[str, Any] = {
            "id": item_id,
            "kind": classified["kind"],
            "label": classified["label"][:_MAX_LABEL_CHARS],
            "content": raw[:_MAX_CONTENT_CHARS],
            "filename": str(filename).strip()[:240] if filename else None,
            "extractedEntities": classified.get("extractedEntities") or {},
            "source": "user",
        }

        if message_token:
            item["messageId"] = message_token

        if normalized_role in {"user", "assistant"}:
            item["role"] = normalized_role

        return item

    @classmethod
    def ingest_turn(
        cls,
        *,
        question: str,
        answer: str,
        question_message_id: str | None = None,
        answer_message_id: str | None = None,
    ) -> list[dict[str, Any]]:
        question_text = str(question or "").strip()
        answer_text = str(answer or "").strip()

        if not question_text or not answer_text:
            raise ValueError("Informe pergunta e resposta para adicionar ao contexto.")

        return [
            cls.ingest(
                content=question_text,
                role="user",
                kind="question",
                message_id=question_message_id,
            ),
            cls.ingest(
                content=answer_text,
                role="assistant",
                kind="answer",
                message_id=answer_message_id,
            ),
        ]

    @classmethod
    def _classify_conversation_turn(
        cls,
        content: str,
        *,
        kind: str,
        role: str = "",
    ) -> dict[str, Any]:
        text = str(content or "").strip()
        normalized_kind = str(kind or "").strip().lower()

        if normalized_kind == "turn":
            return {
                "kind": "turn",
                "label": cls._conversation_label("Pergunta + resposta", text),
                "extractedEntities": {},
            }

        if normalized_kind == "answer" or role == "assistant":
            return {
                "kind": "answer",
                "label": cls._conversation_label("Resposta", text),
                "extractedEntities": {},
            }

        return {
            "kind": "question",
            "label": cls._conversation_label("Pergunta", text),
            "extractedEntities": {},
        }

    @classmethod
    def _conversation_label(cls, prefix: str, text: str) -> str:
        snippet = " ".join(text.split())

        if not snippet:
            return prefix[:_MAX_LABEL_CHARS]

        if len(snippet) <= 42:
            return f"{prefix}: {snippet}"[:_MAX_LABEL_CHARS]

        return f"{prefix}: {snippet[:39]}…"[:_MAX_LABEL_CHARS]

    @classmethod
    def neutral_entity_label(cls, kind: str, value: str) -> str:
        """Rótulo neutro quando só há o valor (ex.: captura automática sem frase do usuário)."""
        token = str(value or "").strip()

        if not token:
            return "Contexto"

        return token[:_MAX_LABEL_CHARS]

    @classmethod
    def _label_for_context_capture(cls, content: str) -> str:
        """Preserva o que o usuário digitou em itens curtos (ex.: «filial 02», «10080055»)."""
        text = " ".join(str(content or "").split()).strip()

        if not text:
            return "Contexto"

        if len(text) <= _MAX_LABEL_CHARS:
            return text

        snippet = cls._label_from_content(text)

        return snippet or text[:_MAX_LABEL_CHARS]

    @classmethod
    def classify(cls, content: str, *, filename: str | None = None) -> dict[str, Any]:
        text = str(content or "").strip()
        lowered_name = str(filename or "").lower()
        extracted: dict[str, str] = {}

        if lowered_name.endswith((".csv", ".tsv", ".xlsx", ".xls")):
            return {
                "kind": "table",
                "label": cls._label_from_filename(filename) or "Tabela",
                "extractedEntities": extracted,
            }

        if lowered_name.endswith((".txt", ".md", ".json", ".pdf")):
            kind = "file" if lowered_name.endswith(".pdf") else "knowledge"
            return {
                "kind": kind,
                "label": cls._label_from_filename(filename) or "Arquivo",
                "extractedEntities": extracted,
            }

        if cls._looks_like_table(text):
            return {
                "kind": "table",
                "label": cls._label_from_content(text) or "Tabela",
                "extractedEntities": extracted,
            }

        product_code = ChatProductQueryIntentService.extract_product_code(text)

        if product_code:
            extracted["productCode"] = product_code

        branch_match = _BRANCH_RE.search(text)

        if branch_match:
            extracted["branch"] = branch_match.group(1).strip().upper()

        warehouse_match = _WAREHOUSE_RE.search(text)

        if warehouse_match:
            extracted["warehouse"] = warehouse_match.group(1).strip().upper()

        if product_code and len(text) <= 80 and not branch_match and not warehouse_match:
            return {
                "kind": _CONTEXT_CHIP_KIND,
                "label": cls._label_for_context_capture(text),
                "extractedEntities": extracted,
            }

        if branch_match and len(text) <= 60:
            return {
                "kind": _CONTEXT_CHIP_KIND,
                "label": cls._label_for_context_capture(text),
                "extractedEntities": extracted,
            }

        if warehouse_match and len(text) <= 60:
            return {
                "kind": _CONTEXT_CHIP_KIND,
                "label": cls._label_for_context_capture(text),
                "extractedEntities": extracted,
            }

        if any(token in text.lower() for token in ("playbook", "documentação", "política", "norma")):
            return {
                "kind": "knowledge",
                "label": cls._label_from_content(text) or "Conhecimento",
                "extractedEntities": extracted,
            }

        return {
            "kind": "note",
            "label": cls._label_from_content(text) or "Contexto",
            "extractedEntities": extracted,
        }

    @classmethod
    def dedup_key_for_item(cls, item: dict[str, Any]) -> str | None:
        kind = str(item.get("kind") or "").strip().lower()
        message_id = str(item.get("messageId") or "").strip()

        if message_id and kind in _CONVERSATION_KINDS:
            return f"msg:{message_id}:{kind}"

        content = str(item.get("content") or "").strip()
        filename = str(item.get("filename") or "").strip()

        if not content and not filename:
            return None

        fingerprint = f"{kind}:{filename}:{content[:500]}"
        digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:24]

        return f"content:{digest}"

    @classmethod
    def chip_value_for_item(cls, item: dict[str, Any]) -> str:
        stable = cls.dedup_key_for_item(item)

        if stable:
            return stable

        item_id = str(item.get("id") or "").strip()
        label = str(item.get("label") or "Contexto").strip()

        return item_id or label[:120]

    @classmethod
    def _entity_value_for_chip(cls, item: dict[str, Any]) -> str | None:
        """Valor estável para chips com extractedEntities (produto/filial/armazém)."""
        extracted = item.get("extractedEntities") or {}

        for key in ("productCode", "branch", "warehouse"):
            token = str(extracted.get(key) or "").strip()

            if token:
                return token

        return None

    @classmethod
    def chip_kind_for_display(cls, item_kind: str) -> str:
        """Chips na UI usam kind genérico «context», sem product/branch/warehouse."""
        normalized = str(item_kind or "").strip().lower()

        if normalized in _ENTITY_ITEM_KINDS or normalized == _CONTEXT_CHIP_KIND:
            return _CONTEXT_CHIP_KIND

        return normalized or "note"

    @classmethod
    def chip_from_item(cls, item: dict[str, Any]) -> dict[str, str]:
        item_kind = str(item.get("kind") or "note").strip().lower()
        label = str(item.get("label") or "Contexto").strip()
        entity_value = cls._entity_value_for_chip(item)

        if entity_value:
            value = entity_value
        else:
            value = cls.chip_value_for_item(item)

        chip: dict[str, str] = {
            "label": label[:_MAX_LABEL_CHARS],
            "kind": cls.chip_kind_for_display(item_kind),
            "value": value,
        }
        item_id = str(item.get("id") or "").strip()

        if item_id:
            chip["itemId"] = item_id

        return chip

    @classmethod
    def find_duplicate_item_ids(
        cls,
        existing_items: list[dict[str, Any]] | None,
        incoming_items: list[dict[str, Any]],
    ) -> list[str]:
        incoming_keys = {
            key
            for item in incoming_items
            if isinstance(item, dict)
            for key in [cls.dedup_key_for_item(item)]
            if key
        }

        if not incoming_keys:
            return []

        remove_ids: list[str] = []

        for item in existing_items or []:
            if not isinstance(item, dict):
                continue

            key = cls.dedup_key_for_item(item)

            if not key or key not in incoming_keys:
                continue

            item_id = str(item.get("id") or "").strip()

            if item_id:
                remove_ids.append(item_id)

        return remove_ids

    @classmethod
    def chips_from_items(cls, items: list[dict[str, Any]] | None) -> list[dict[str, str]]:
        chips: list[dict[str, str]] = []

        for item in items or []:
            if not isinstance(item, dict):
                continue

            chips.append(cls.chip_from_item(item))

        return chips

    @classmethod
    def merge_items_into_snapshot(cls, snapshot: dict, items: list[dict[str, Any]] | None) -> dict:
        result = dict(snapshot)
        normalized = [item for item in (items or []) if isinstance(item, dict) and item.get("id")]

        if not normalized:
            result.pop("userContextItems", None)
            return cls.sync_operational_focus(result)

        result["userContextItems"] = normalized[-12:]
        return cls.sync_operational_focus(result)

    @classmethod
    def sync_operational_focus(cls, snapshot: dict | None) -> dict:
        """Deriva ``operationalFocus`` (cache) a partir de ``userContextItems`` ou do turno.

        Não é editável pelo usuário — só espelha contexto + sinais do turno (SQL, período).
        """
        result = ChatSnapshotOperationalFocus.normalize(snapshot)
        existing = ChatSnapshotOperationalFocus.get(result)
        items = [
            item
            for item in (result.get("userContextItems") or [])
            if isinstance(item, dict) and item.get("id")
        ]
        derived = cls._resolve_entities_from_items(items, {}) if items else {}
        merged: dict[str, str] = {}

        for key in _PRESERVED_ENTITY_KEYS:
            token = str(existing.get(key) or "").strip()

            if token:
                merged[key] = token

        if items:
            for key in _OPERATIONAL_FROM_CONTEXT_KEYS:
                token = str(derived.get(key) or "").strip()

                if token:
                    merged[key] = token
        else:
            for key in _OPERATIONAL_FROM_CONTEXT_KEYS:
                token = str(existing.get(key) or "").strip()

                if token:
                    merged[key] = token

        return ChatSnapshotOperationalFocus.set(result, merged)

    @classmethod
    def _resolve_entities_from_items(
        cls,
        items: list[dict[str, Any]] | None,
        existing: dict | None = None,
    ) -> dict[str, str]:
        """Extrai chaves operacionais dos itens para compor ``operationalFocus``."""
        entities = dict(existing or {})

        for item in items or []:
            if not isinstance(item, dict):
                continue

            for key, value in (item.get("extractedEntities") or {}).items():
                token = str(value or "").strip()

                if not token:
                    continue

                entity_key = ChatManualContextPinService.entity_key_for_kind(key) or key

                if entity_key in {"productCode", "branch", "warehouse", "period"}:
                    entities[entity_key] = token

        return entities

    @classmethod
    def apply_extracted_entities_to_overlay(cls, overlay: dict, item: dict[str, Any]) -> dict:
        result = dict(overlay)
        items = list(result.get("userContextItems") or [])

        if isinstance(item, dict) and item.get("id"):
            items.append(item)

        result["userContextItems"] = items[-12:]
        return cls.sync_operational_focus(result)

    @classmethod
    def remove_context_items_for_operational_kind(
        cls,
        items: list[dict[str, Any]] | None,
        *,
        kind: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Remove itens cujo ``extractedEntities`` corresponde ao tipo operacional."""
        entity_key = ChatManualContextPinService.entity_key_for_kind(kind)

        if not entity_key:
            return list(items or []), []

        kept: list[dict[str, Any]] = []
        removed_ids: list[str] = []

        for item in items or []:
            if not isinstance(item, dict):
                continue

            extracted = item.get("extractedEntities") or {}
            token = str(extracted.get(entity_key) or "").strip()

            if token:
                item_id = str(item.get("id") or "").strip()

                if item_id:
                    removed_ids.append(item_id)

                continue

            kept.append(item)

        return kept, removed_ids

    @classmethod
    def _product_code_from_item(cls, item: dict[str, Any]) -> str | None:
        extracted = item.get("extractedEntities") or {}
        token = str(extracted.get("productCode") or "").strip()

        if token and ChatProductQueryIntentService.is_plausible_product_code(token):
            return token

        for field in ("content", "label"):
            text = str(item.get(field) or "").strip()

            if not text:
                continue

            code = ChatProductQueryIntentService.extract_product_code(text)

            if code:
                return code

        return None

    @classmethod
    def resolve_product_code_from_items(
        cls,
        items: list[dict[str, Any]] | None,
    ) -> str | None:
        """Último código em foco nos itens de contexto (prioriza source=user)."""
        normalized = [item for item in (items or []) if isinstance(item, dict)]

        if not normalized:
            return None

        for item in reversed(normalized):
            if str(item.get("source") or "").strip().lower() == "user":
                code = cls._product_code_from_item(item)

                if code:
                    return code

        for item in reversed(normalized):
            code = cls._product_code_from_item(item)

            if code:
                return code

        return None

    @classmethod
    def resolve_product_code_from_context_prompt(
        cls,
        conversation_context: str | None,
    ) -> str | None:
        """Extrai o código do bloco de contexto do usuário no prompt (antes do histórico)."""
        raw = str(conversation_context or "")
        marker_index = raw.find(_USER_CONTEXT_PROMPT_MARKER)

        if marker_index < 0:
            return None

        section = raw[marker_index:]
        end_match = _USER_CONTEXT_SECTION_END_RE.search(section)

        if end_match:
            section = section[: end_match.start()]

        item_lines: list[str] = []

        for line in section.splitlines()[1:]:
            stripped = line.strip()

            if not stripped:
                if item_lines:
                    break

                continue

            if stripped.startswith("- ["):
                item_lines.append(stripped)
                continue

            if item_lines:
                break

        if item_lines:
            return ChatProductQueryIntentService.extract_last_product_code(
                "\n".join(item_lines),
            )

        return ChatProductQueryIntentService.extract_last_product_code(section)

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        items = (snapshot or {}).get("userContextItems")

        if not isinstance(items, list) or not items:
            return None

        lines = [
            "Contexto adicionado pelo usuário (priorize nas próximas respostas; "
            "não invente dados além do que está abaixo):"
        ]

        for item in items[-8:]:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "Contexto").strip()
            kind = str(item.get("kind") or "note").strip()
            body = str(item.get("content") or "").strip()

            if not body:
                continue

            snippet = body[:_MAX_PROMPT_CHARS]

            if len(body) > _MAX_PROMPT_CHARS:
                snippet += "…"

            lines.append(f"- [{kind}] {label}: {snippet}")

        return "\n".join(lines) if len(lines) > 1 else None

    @classmethod
    def items_for_usage_view(cls, snapshot: dict | None) -> list[str]:
        items = (snapshot or {}).get("userContextItems")

        if not isinstance(items, list):
            return []

        return [str(item.get("label") or "Contexto").strip() for item in items if isinstance(item, dict)]

    @classmethod
    def entity_context_labels(cls, entities: dict | None) -> list[str]:
        """Legado — preferir ``items_for_usage_view`` com ``userContextItems``."""
        data = entities or {}
        labels: list[str] = []

        code = str(data.get("productCode") or "").strip()
        if code:
            labels.append(code)

        branch = str(data.get("branch") or "").strip()
        if branch:
            labels.append(branch)

        warehouse = str(data.get("warehouse") or "").strip()
        if warehouse:
            labels.append(warehouse)

        period = str(data.get("period") or "").strip()
        if period:
            labels.append(f"Período {period}")

        return labels

    @classmethod
    def auto_items_from_entities(
        cls,
        entities: dict | None,
        existing_items: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Converte o que o chat detectou (código/filial/armazém) em itens de contexto.

        Em vez de tratar o código como "entidade" estruturada, ele entra como
        contexto comum — o LLM infere o foco a partir desse contexto. Itens já
        presentes (mesmo valor) não são duplicados.
        """
        data = entities or {}
        existing_keys: set[str] = set()

        for item in existing_items or []:
            if not isinstance(item, dict):
                continue

            for key, value in (item.get("extractedEntities") or {}).items():
                token = str(value or "").strip()

                if token:
                    existing_keys.add(f"{key}:{token}")

        new_items: list[dict[str, Any]] = []

        def add(kind: str, entity_key: str, value: str, label: str, focus: str) -> None:
            token = str(value or "").strip()

            if not token or f"{entity_key}:{token}" in existing_keys:
                return

            existing_keys.add(f"{entity_key}:{token}")
            new_items.append(
                {
                    "id": f"auto:{entity_key}:{token}"[:64],
                    "kind": kind,
                    "label": label[:_MAX_LABEL_CHARS],
                    "content": focus,
                    "extractedEntities": {entity_key: token},
                    "source": "auto",
                }
            )

        code = str(data.get("productCode") or "").strip()
        source = str(data.get("productCodeSource") or "").strip()

        if code and source in ("tool", "explicit"):
            add(
                _CONTEXT_CHIP_KIND,
                "productCode",
                code,
                code,
                f"Em foco nesta conversa: {code}",
            )

        branch = str(data.get("branch") or "").strip()
        if branch:
            add(
                _CONTEXT_CHIP_KIND,
                "branch",
                branch,
                branch,
                f"Em foco nesta conversa: {branch}",
            )

        warehouse = str(data.get("warehouse") or "").strip()
        if warehouse:
            add(
                _CONTEXT_CHIP_KIND,
                "warehouse",
                warehouse,
                warehouse,
                f"Em foco nesta conversa: {warehouse}",
            )

        return new_items

    @classmethod
    def merge_context_labels(cls, *groups: list[str] | None) -> list[str]:
        """Une listas de rótulos de contexto removendo duplicatas (case-insensitive)."""
        merged: list[str] = []
        seen: set[str] = set()

        for group in groups:
            for label in group or []:
                token = str(label or "").strip()

                if not token:
                    continue

                key = token.casefold()

                if key in seen:
                    continue

                seen.add(key)
                merged.append(token)

        return merged

    @classmethod
    def _looks_like_table(cls, text: str) -> bool:
        rows = _TABLE_ROW_RE.findall(text)

        return len(rows) >= 2

    @classmethod
    def _label_from_content(cls, text: str) -> str | None:
        for line in text.splitlines():
            token = line.strip()

            if not token or token.startswith("|"):
                continue

            return token[:_MAX_LABEL_CHARS]

        return None

    @classmethod
    def _label_from_filename(cls, filename: str | None) -> str | None:
        name = str(filename or "").strip()

        if not name:
            return None

        return name.rsplit("/", 1)[-1][: _MAX_LABEL_CHARS]
