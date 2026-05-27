from __future__ import annotations

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


class ChatCapabilitiesService:
    """Responde perguntas sobre o que o chat/agente consegue fazer."""

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
        agent_name = str(agent.get("name") or workspace_context.get("agentKey") or "").strip()
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

        return "\n".join(lines)

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
