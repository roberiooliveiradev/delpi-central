"""Regras declarativas de seções humanizadas — Playbook 12 R4."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationSectionRulesService:
    _SCOPE = "scope"
    _PROFILE = "profile"
    _GUIDE = "guide"
    _INSPECTION = "inspection"
    _STRUCTURE = "structure"
    _HIGHLIGHTS = "highlights"
    _ATTENTION = "attention"

    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        plan: dict[str, Any],
        stack_config: dict[str, Any],
        *,
        path: str,
        entity: str | None = None,
    ) -> dict[str, Any]:
        rules = stack_config.get("sectionRules")

        if not isinstance(rules, dict) or not rules.get("enabled"):
            return plan

        visibility = cls.resolve_visibility(metadata, rules.get("visibility") or {})
        presentation_profile = str(
            rules.get("presentationProfile")
            or plan.get("presentationProfileKey")
            or ""
        ).strip()

        plan["presentationProfile"] = presentation_profile or plan.get("presentationProfile")
        plan["humanizedSections"] = True
        plan["sectionVisibility"] = visibility
        plan["sectionFraming"] = cls.build_framing(
            metadata,
            visibility,
            rules.get("framing") or {},
            path=path,
        )

        template = str(rules.get("narrativeOrder") or "operational_with_tail").strip()
        explicit_slots = rules.get("narrativeOrderSlots")

        if isinstance(explicit_slots, list) and explicit_slots:
            inline_config = {
                "slotSources": rules.get("narrativeSlotSources") or {},
                "planFlags": rules.get("narrativePlanFlags") or {},
            }
            plan["narrativeOrder"] = cls._resolve_narrative_from_template_config(
                inline_config,
                explicit_slots,
                visibility,
                metadata,
                plan,
            )
        else:
            plan["narrativeOrder"] = cls.resolve_narrative_order(
                template,
                visibility,
                metadata,
                plan,
            )

        return plan

    @classmethod
    def resolve_visibility(
        cls,
        metadata: dict[str, Any],
        rules: dict[str, Any],
    ) -> dict[str, bool]:
        resolved: dict[str, bool] = {}
        markdown = cls._text_markdown(metadata)

        for section, spec in rules.items():
            if spec is False:
                resolved[str(section)] = False
                continue

            if spec is True:
                resolved[str(section)] = True
                continue

            if not isinstance(spec, (str, dict)):
                continue

            resolved[str(section)] = cls._evaluate_visibility_rule(metadata, markdown, spec)

        return resolved

    @classmethod
    def build_framing(
        cls,
        metadata: dict[str, Any],
        visibility: dict[str, bool],
        framing_rules: dict[str, Any],
        *,
        path: str,
    ) -> dict[str, str]:
        if not framing_rules:
            return {}

        source = str(framing_rules.get("source") or "product_operational.sectionFraming").strip()
        bundle = cls._load_framing_source(source)
        variant = cls._resolve_framing_variant(framing_rules, path)
        path_fragment = str(variant.get("pathFragment") or framing_rules.get("pathFragment") or "").strip()
        code = cls._product_code_from_path(metadata, path_fragment) if path_fragment else ""
        section_keys = variant.get("sections") if isinstance(variant.get("sections"), dict) else framing_rules.get("sections")

        if not isinstance(section_keys, dict):
            return {}

        result: dict[str, str] = {}

        for section, key_spec in section_keys.items():
            if not visibility.get(str(section)):
                continue

            text = cls._resolve_framing_text(bundle, key_spec, code=code)
            if text:
                result[str(section)] = text

        return result

    @classmethod
    def resolve_narrative_order(
        cls,
        template: str,
        visibility: dict[str, bool],
        metadata: dict[str, Any],
        plan: dict[str, Any],
    ) -> list[str]:
        token = str(template or "").strip().lower()
        config = ChatPresentationVocabularyService.narrative_order_template(token)

        if not config:
            config = ChatPresentationVocabularyService.narrative_order_template(
                "operational_with_tail",
            )

        slots = config.get("slots") or ["lead"]

        return cls._resolve_narrative_from_template_config(
            config,
            slots,
            visibility,
            metadata,
            plan,
        )

    @classmethod
    def _resolve_narrative_from_template_config(
        cls,
        config: dict[str, Any],
        slots: list[Any],
        visibility: dict[str, bool],
        metadata: dict[str, Any],
        plan: dict[str, Any],
    ) -> list[str]:
        slot_sources = config.get("slotSources") if isinstance(config.get("slotSources"), dict) else {}
        plan_flags = config.get("planFlags") if isinstance(config.get("planFlags"), dict) else {}
        order: list[str] = []

        for slot in slots:
            token = str(slot or "").strip()

            if not token:
                continue

            if not cls._narrative_slot_visible(
                token,
                slot_sources,
                plan_flags,
                visibility,
                metadata,
                plan,
            ):
                continue

            if token not in order:
                order.append(token)

        return order or ["lead"]

    @classmethod
    def _narrative_slot_visible(
        cls,
        slot: str,
        slot_sources: dict[str, Any],
        plan_flags: dict[str, Any],
        visibility: dict[str, bool],
        metadata: dict[str, Any],
        plan: dict[str, Any],
    ) -> bool:
        if slot == "lead":
            return True

        flag_key = str(plan_flags.get(slot) or "").strip()

        if flag_key and not bool(plan.get(flag_key)):
            return False

        if slot == "highlights":
            return bool(visibility.get(cls._HIGHLIGHTS))

        if slot == "attention":
            return bool(visibility.get(cls._ATTENTION))

        if slot == "profileTables":
            return bool(visibility.get(cls._PROFILE))

        sources = slot_sources.get(slot)

        if slot == "operationalTables":
            keys = sources if isinstance(sources, list) else ["guide", "inspection", "structure"]
            return any(bool(visibility.get(str(key))) for key in keys)

        if slot == "tailVisuals":
            keys = sources if isinstance(sources, list) else ["auto_tail"]

            if "auto_tail" in keys:
                return cls._should_include_tail_visuals(metadata, visibility)

            if "presentation_slots" in keys:
                return any(
                    cls._slot_has_type(metadata, presentation_type)
                    for presentation_type in ("chart", "tree", "kpi")
                )

            return any(bool(visibility.get(str(key))) for key in keys)

        return bool(visibility.get(slot))

    @classmethod
    def _resolve_explicit_narrative_order(
        cls,
        slots: list[Any],
        visibility: dict[str, bool],
        metadata: dict[str, Any],
        plan: dict[str, Any],
    ) -> list[str]:
        return cls._resolve_narrative_from_template_config(
            {},
            slots,
            visibility,
            metadata,
            plan,
        )

    @classmethod
    def _evaluate_visibility_rule(
        cls,
        metadata: dict[str, Any],
        markdown: str,
        spec: str | dict[str, Any],
    ) -> bool:
        if isinstance(spec, str):
            kind = spec.strip().lower()

            if kind == "markdown":
                return bool(markdown.strip())

            if kind == "highlights":
                return cls._has_highlights_generic(markdown)

            if kind == "highlights_strict":
                return cls._has_highlights(markdown)

            if kind == "attention":
                return cls._has_attention_generic(markdown)

            if kind == "attention_strict":
                return cls._has_attention(markdown)

            if kind == "profile_table":
                return cls._has_profile_table(metadata)

            if kind == "operational_tables":
                return cls._has_operational_tables(metadata)

            if kind == "tree":
                return cls._has_tree(metadata)

            if kind == "visual_panels":
                return cls._slot_has_type(metadata, "kpi") or cls._slot_has_type(metadata, "chart")

            return False

        if not isinstance(spec, dict):
            return False

        kind = str(spec.get("kind") or spec.get("type") or "").strip().lower()
        token_key = str(spec.get("tableTitleTokens") or spec.get("group") or "").strip()

        if kind in {"table_title_tokens", "tabletitletokens"} and token_key:
            return cls._has_table_with_tokens(
                metadata,
                ChatPresentationVocabularyService.table_title_tokens(token_key),
            )

        if kind in {"tree_or_table_title_tokens", "treeortabletitletokens"} and token_key:
            return cls._has_tree(metadata) or cls._has_table_with_tokens(
                metadata,
                ChatPresentationVocabularyService.table_title_tokens(token_key),
            )

        return False

    @classmethod
    def _resolve_framing_variant(cls, framing_rules: dict[str, Any], path: str) -> dict[str, Any]:
        variants = framing_rules.get("pathVariants")

        if not isinstance(variants, dict):
            return {}

        lowered = str(path or "").lower()

        for fragment, variant in variants.items():
            token = str(fragment or "").strip().lower()

            if token and token != "default" and token in lowered and isinstance(variant, dict):
                return variant

        default = variants.get("default")

        return dict(default) if isinstance(default, dict) else {}

    @classmethod
    def _resolve_framing_text(
        cls,
        bundle: dict[str, str],
        key_spec: Any,
        *,
        code: str,
    ) -> str:
        if isinstance(key_spec, str):
            return str(bundle.get(key_spec) or "")

        if not isinstance(key_spec, dict):
            return ""

        with_code = str(key_spec.get("withCode") or "").strip()
        generic = str(key_spec.get("generic") or "").strip()

        if code and with_code:
            template = bundle.get(with_code, "")

            return template.format(code=code) if template else str(bundle.get(generic) or "")

        return str(bundle.get(generic) or "")

    @classmethod
    def _load_framing_source(cls, source: str) -> dict[str, str]:
        token = str(source or "").strip()

        if token == "product_operational.sectionFraming":
            from app.domain.services.chat_product_operational_content_service import (
                ChatProductOperationalContentService,
            )

            return ChatProductOperationalContentService.get_mapping(
                "presentation",
                "sectionFraming",
            )

        if token.startswith("presenter_content."):
            parts = token.split(".", 1)
            key = parts[1] if len(parts) > 1 else "stackSectionFraming"

            resolved = ChatAssistantContentService.get("presenter_content", key)

            return dict(resolved) if isinstance(resolved, dict) else {}

        return {}

    @classmethod
    def _has_operational_tables(cls, metadata: dict[str, Any]) -> bool:
        count = 0

        for key in ("tablePresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "table":
                rows = presentation.get("rows") or []

                if rows:
                    count += 1

        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for presentation in bulk:
                if not isinstance(presentation, dict) or presentation.get("type") != "table":
                    continue

                rows = presentation.get("rows") or []

                if rows:
                    count += 1

        return count >= 1

    @classmethod
    def _should_include_tail_visuals(
        cls,
        metadata: dict[str, Any],
        visibility: dict[str, bool],
    ) -> bool:
        if visibility.get(cls._STRUCTURE):
            return True

        return any(
            cls._slot_has_type(metadata, presentation_type)
            for presentation_type in ("kpi", "tree", "chart", "dashboard")
        )

    @classmethod
    def _slot_has_type(cls, metadata: dict[str, Any], presentation_type: str) -> bool:
        token = str(presentation_type or "").strip().lower()

        for key in ("kpiPresentation", "chartPresentation", "dashboardPresentation", "treePresentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and str(presentation.get("type") or "").strip().lower() == token:
                return True

        primary = metadata.get("presentation")

        return (
            isinstance(primary, dict)
            and str(primary.get("type") or "").strip().lower() == token
        )

    @classmethod
    def _product_code_from_path(cls, metadata: dict[str, Any], path_fragment: str) -> str:
        fragment = str(path_fragment or "").strip()

        if not fragment:
            match = re.search(r"/products/([^/]+)/analyser", str(metadata.get("path") or ""), re.I)
            return match.group(1).strip() if match else ""

        match = re.search(
            rf"/products/([^/]+){re.escape(fragment)}",
            str(metadata.get("path") or ""),
            re.I,
        )

        return match.group(1).strip() if match else ""

    @classmethod
    def _has_table_with_tokens(cls, metadata: dict[str, Any], title_tokens: tuple[str, ...]) -> bool:
        for presentation in cls._table_presentations(metadata):
            title = str(presentation.get("title") or "").strip().lower()

            if any(token in title for token in title_tokens):
                return cls._table_has_rows(presentation)

        return False

    @classmethod
    def _has_highlights_generic(cls, markdown: str) -> bool:
        marker = cls._highlights_header()

        return marker in markdown and cls._has_highlights(markdown)

    @classmethod
    def _has_attention_generic(cls, markdown: str) -> bool:
        marker = cls._attention_header_prefix()

        return marker in markdown and cls._has_attention(markdown)

    @classmethod
    def _highlights_header(cls) -> str:
        return ChatAssistantContentService.get(
            "presenter_content",
            "analyserMarkdown",
            "highlightsHeader",
            default="**Destaques**",
        )

    @classmethod
    def _attention_header_prefix(cls) -> str:
        return ChatAssistantContentService.get(
            "presenter_content",
            "analyserMarkdown",
            "attentionHeaderPrefix",
            default="**Pontos de atenção",
        )

    @classmethod
    def _has_highlights(cls, markdown: str) -> bool:
        marker = cls._highlights_header()

        if marker not in markdown:
            return False

        block = markdown.split(marker, 1)[-1]
        stop_tokens = (cls._attention_header_prefix(), "###", "**Plano", "**Roteiro")

        for token in stop_tokens:
            if token in block:
                block = block.split(token, 1)[0]

        bullets = [
            line.strip()
            for line in block.splitlines()
            if line.strip().startswith("-") or line.strip().startswith("*")
        ]

        substantive = [
            line
            for line in bullets
            if len(line) > 2
            and not ChatPresentationVocabularyService.absence_insight_pattern().search(line)
        ]

        return bool(substantive)

    @classmethod
    def _has_attention(cls, markdown: str) -> bool:
        marker = cls._attention_header_prefix()

        if marker not in markdown:
            return False

        block = markdown.split(marker, 1)[-1]
        numbered = re.findall(r"^\s*\d+\.\s+\S", block, flags=re.MULTILINE)

        return bool(numbered)

    @classmethod
    def _has_profile_table(cls, metadata: dict[str, Any]) -> bool:
        profile = metadata.get("profileTablePresentation")

        if isinstance(profile, dict) and profile.get("type") == "table":
            return cls._table_has_rows(profile)

        for presentation in cls._table_presentations(metadata):
            title = str(presentation.get("title") or "").strip().lower()

            if any(
                title.startswith(prefix)
                for prefix in ChatPresentationVocabularyService.profile_table_title_prefixes()
            ):
                return cls._table_has_rows(presentation)

            if any(token in title for token in ChatPresentationVocabularyService.profile_table_title_tokens()):
                return cls._table_has_rows(presentation)

        return False

    @classmethod
    def _has_tree(cls, metadata: dict[str, Any]) -> bool:
        for key in ("treePresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "tree":
                return True

        return False

    @classmethod
    def _table_presentations(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = []
        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            tables.extend(item for item in bundled if isinstance(item, dict))

        for key in ("tablePresentation", "profileTablePresentation", "inspectionTablePresentation"):
            item = metadata.get(key)

            if isinstance(item, dict) and item.get("type") == "table":
                tables.append(item)

        return tables

    @classmethod
    def _table_has_rows(cls, presentation: dict[str, Any]) -> bool:
        rows = presentation.get("rows")

        return isinstance(rows, list) and bool(rows)

    @classmethod
    def _text_markdown(cls, metadata: dict[str, Any]) -> str:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return ""

        return str(text_presentation.get("markdown") or "").strip()
