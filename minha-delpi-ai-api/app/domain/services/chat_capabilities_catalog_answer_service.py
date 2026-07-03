"""Resposta direta do catálogo de capacidades — bundle ``capabilities``."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_action_label_service import ChatActionLabelService
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_onboarding_profile_service import ChatOnboardingProfileService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("capabilities")


def _sections() -> dict[str, Any]:
    return _content().get("sections") or {}


def _skills_texts() -> dict[str, Any]:
    return _content().get("skills") or {}


def _catalog_texts() -> dict[str, Any]:
    return _content().get("catalog") or {}


@lru_cache(maxsize=1)
def _path_rules() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    rules = _content().get("pathRules") or []
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
    default = _content().get("pathRuleDefault") or {}

    if not isinstance(default, dict):
        return "Outras APIs", ("consulta conforme rota habilitada", "dados operacionais autorizados")

    category = str(default.get("category") or "Outras APIs")
    examples = tuple(str(item) for item in (default.get("examples") or ()))

    return category, examples


@lru_cache(maxsize=1)
def _common_chat_examples() -> tuple[str, ...]:
    return tuple(str(item) for item in (_content().get("commonExamples") or ()))


@lru_cache(maxsize=1)
def _self_help_agent_context() -> dict[str, Any]:
    return _content().get("selfHelpAgentContext") or {}


class ChatCapabilitiesCatalogAnswerService:
    @classmethod
    def build_direct_answer(
        cls,
        *,
        workspace_context: dict,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
    ) -> str | None:
        content = _content()
        sections = _sections()
        lines: list[str] = []

        context_intro = cls.self_help_context_intro(workspace_context)

        if context_intro:
            lines.extend([context_intro, ""])

        lines.extend(
            [
                str(content.get("intro") or "Posso ajudar você nestes formatos:"),
                "",
                str(
                    sections.get("alwaysAvailableTitle")
                    or "**Sempre disponíveis (chat comum e agentes)**"
                ),
            ]
        )

        for tool in sections.get("platformTools") or []:
            if isinstance(tool, dict) and tool.get("description"):
                lines.append(f"- {tool['description']}")

        for item in sections.get("alwaysAvailableItems") or []:
            lines.append(f"- {item}")

        skills = workspace_context.get("skills") or {}
        skill_lines = cls.format_skills_section(skills, workspace_context.get("allowedActionIds"))

        if skill_lines:
            lines.extend(
                [
                    "",
                    str(sections.get("skillsTitle") or "**Skills (comportamento do assistente)**"),
                ]
            )
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
            lines.extend(cls.format_action_catalog(action_catalog, allowed))
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

        lines.extend(cls.format_business_suggestions(content))

        return "\n".join(lines)

    @classmethod
    def self_help_context_intro(cls, workspace_context: dict) -> str | None:
        contexts = _self_help_agent_context()
        user_activated = bool(workspace_context.get("userActivatedAgent"))
        agent = workspace_context.get("agent") or {}
        agent_name = str(agent.get("name") or "").strip()
        agent_category = str(agent.get("category") or "").strip()
        agent_description = str(agent.get("description") or "").strip()

        if not user_activated or not agent_name:
            return str(contexts.get("common") or "").strip() or None

        active_template = str(contexts.get("agentActive") or "").strip()

        if active_template:
            profile_hint = ""

            if agent_category:
                profile_id = ChatOnboardingProfileService.infer_profile_from_agent(
                    agent_name=agent_name,
                    agent_category=agent_category,
                )
                profile_hint = str((contexts.get(profile_id or "") or "")).strip()

            return active_template.format(
                agent_name=agent_name,
                agent_description=agent_description
                or profile_hint
                or "agente especializado nesta conversa",
            )

        profile_id = ChatOnboardingProfileService.infer_profile_from_agent(
            agent_name=agent_name,
            agent_category=agent_category,
        )
        intro = str((contexts.get(profile_id or "") or "")).strip()

        if intro:
            return intro

        return str(contexts.get("engineering") or "").strip() or None

    @classmethod
    def format_business_suggestions(cls, content: dict) -> list[str]:
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
    def format_skills_section(
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
    def format_action_catalog(cls, catalog: list[dict], allowed_ids: list[str]) -> list[str]:
        catalog_texts = _catalog_texts()
        allowed_set = set(allowed_ids)
        by_category: dict[str, list[dict]] = {}

        for action in catalog:
            action_id = str(action.get("actionId") or "").strip()

            if action_id not in allowed_set:
                continue

            path = str(action.get("path") or "")
            category, _examples = cls.resolve_path_rule(path)
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

            return [
                str(
                    empty
                    or "- Nenhuma action detalhada no catálogo; verifique a configuração do agente."
                )
            ]

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

        return "\n".join(lines)

    @classmethod
    def build_action_routes_answer(
        cls,
        *,
        workspace_context: dict,
        allowed_action_ids: list[str] | None = None,
        action_catalog: list[dict] | None = None,
        max_items: int = 80,
    ) -> str | None:
        from app.domain.services.chat_action_label_service import ChatActionLabelService

        content = _content().get("actionRoutesAnswer") or {}
        allowed = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]
        catalog = action_catalog if isinstance(action_catalog, list) else []

        if not allowed or not catalog:
            empty = str(content.get("empty") or "").strip()
            return empty or None

        allowed_set = set(allowed)
        routes: list[dict[str, str]] = []

        for action in catalog:
            if not isinstance(action, dict):
                continue

            action_id = str(action.get("actionId") or "").strip()

            if action_id not in allowed_set:
                continue

            path = str(action.get("path") or "").strip()
            method = str(action.get("method") or "GET").upper()
            summary = ChatActionLabelService.humanize(
                path=path,
                method=method,
                summary=str(
                    action.get("summary") or action.get("description") or action_id
                ).strip(),
                action_id=action_id,
            )

            if not path:
                continue

            routes.append(
                {
                    "method": method,
                    "path": path,
                    "summary": summary,
                }
            )

        if not routes:
            empty = str(content.get("empty") or "").strip()
            return empty or None

        routes.sort(key=lambda item: (item["path"], item["method"]))

        agent = workspace_context.get("agent") or {}
        agent_name = str(agent.get("name") or "").strip()
        total = len(routes)
        shown = routes[:max_items]

        if agent_name:
            title = str(
                content.get("titleWithAgent")
                or "**Rotas das actions habilitadas — agente {agent_name} ({count}):**"
            ).format(agent_name=agent_name, count=str(total))
        else:
            title = str(
                content.get("titleWithoutAgent")
                or "**Rotas das actions OpenAPI habilitadas nesta sessão ({count}):**"
            ).format(count=str(total))

        route_line = str(
            content.get("routeLine") or "- `{method} {path}` — {summary}"
        )
        lines = [title, ""]

        for item in shown:
            lines.append(
                route_line.format(
                    method=item["method"],
                    path=item["path"],
                    summary=item["summary"],
                )
            )

        if total > len(shown):
            lines.append("")
            lines.append(
                str(
                    content.get("truncatedNotice")
                    or "_Mostrando as primeiras {shown} de {total} rotas._"
                ).format(shown=str(len(shown)), total=str(total))
            )

        portal_hint = str(content.get("portalHint") or "").strip()

        if portal_hint:
            lines.extend(["", portal_hint])

        return "\n".join(lines).strip()

    @classmethod
    def resolve_path_rule(cls, path: str) -> tuple[str, tuple[str, ...]]:
        lowered = path.lower()

        for token, category, examples in _path_rules():
            if token in lowered:
                return category, examples

        return _path_rule_default()
