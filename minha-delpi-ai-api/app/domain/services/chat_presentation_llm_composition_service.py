"""Composição de prosa LLM com marcadores → renderPlan intercalado (E18)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_prose_composition_content_service import (
    ChatProseCompositionContentService,
)

logger = logging.getLogger(__name__)

_KIND_TO_SOURCE = {
    "table": "tablePresentations",
    "tree": "treePresentation",
    "chart": "chartPresentation",
    "kpi": "kpiPresentation",
    "dashboard": "dashboardPresentation",
}


@dataclass(frozen=True)
class ProseSegment:
    kind: str  # markdown | component
    text: str = ""
    component_kind: str | None = None
    index: int | None = None


class ChatPresentationLlmCompositionService:
    @classmethod
    def parse_markers(cls, markdown: str | None) -> list[ProseSegment]:
        text = str(markdown or "")
        pattern = ChatProseCompositionContentService.marker_pattern()

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            regex = re.compile(
                r"\[\[(tabela|table|grafico|chart|arvore|árvore|tree|kpi|dashboard)(?::(\d+))?\]\]",
                re.IGNORECASE,
            )

        segments: list[ProseSegment] = []
        cursor = 0

        for match in regex.finditer(text):
            prefix = text[cursor : match.start()]

            if prefix.strip():
                segments.append(ProseSegment(kind="markdown", text=prefix.strip()))
            elif prefix and segments and segments[-1].kind == "markdown":
                segments[-1] = ProseSegment(
                    kind="markdown",
                    text=f"{segments[-1].text}{prefix}".strip(),
                )

            raw_kind = match.group(1)
            canonical = ChatProseCompositionContentService.normalize_marker_kind(raw_kind)
            index_raw = match.group(2)
            index = int(index_raw) if index_raw else None
            segments.append(
                ProseSegment(
                    kind="component",
                    component_kind=canonical or str(raw_kind or "").strip().lower(),
                    index=index,
                )
            )
            cursor = match.end()

        tail = text[cursor:]

        if tail.strip():
            segments.append(ProseSegment(kind="markdown", text=tail.strip()))

        if not segments and text.strip():
            segments.append(ProseSegment(kind="markdown", text=text.strip()))

        return segments

    @classmethod
    def strip_markers(cls, markdown: str | None) -> str:
        text = str(markdown or "")
        pattern = ChatProseCompositionContentService.marker_pattern()

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            regex = re.compile(
                r"\[\[(tabela|table|grafico|chart|arvore|árvore|tree|kpi|dashboard)(?::(\d+))?\]\]",
                re.IGNORECASE,
            )

        cleaned = regex.sub("", text)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()

    @classmethod
    def collect_available_slots(
        cls,
        metadata: dict[str, Any] | None,
        *,
        tool_calls: list | None = None,
    ) -> list[dict[str, Any]]:
        slots: list[dict[str, Any]] = []

        if isinstance(tool_calls, list) and len(tool_calls) > 1:
            for tool_call in tool_calls:
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                meta = tool_call.get("metadata")

                if not isinstance(meta, dict) or not meta.get("ok"):
                    continue

                slots.extend(cls._slots_from_metadata(meta, operation_id=cls._operation_id(meta)))

            if slots:
                return cls._dedupe_slots(slots)

        if isinstance(metadata, dict):
            slots.extend(cls._slots_from_metadata(metadata))

        return cls._dedupe_slots(slots)

    @classmethod
    def resolve_component_ref(
        cls,
        kind: str | None,
        index: int | None,
        metadata: dict[str, Any] | None,
        *,
        tool_calls: list | None = None,
        allowed_kinds: list[str] | None = None,
    ) -> dict[str, Any] | None:
        canonical = ChatProseCompositionContentService.normalize_marker_kind(kind)

        if not canonical:
            return None

        if allowed_kinds is not None and canonical not in {
            str(item).strip().lower() for item in allowed_kinds
        }:
            return None

        slots = [
            slot
            for slot in cls.collect_available_slots(metadata, tool_calls=tool_calls)
            if str(slot.get("kind") or "").strip().lower() == canonical
        ]

        if not slots:
            return None

        if index is None:
            chosen = slots[0]
        else:
            # Markers use 1-based index.
            pos = max(1, int(index)) - 1

            if pos >= len(slots):
                return None

            chosen = slots[pos]

        return {
            "kind": canonical,
            "slot": str(chosen.get("slot") or canonical),
            "source": str(chosen.get("source") or _KIND_TO_SOURCE.get(canonical) or canonical),
            "index": chosen.get("index"),
            "operationId": chosen.get("operationId"),
        }

    @classmethod
    def resolve_policy(
        cls,
        metadata: dict[str, Any] | None,
        *,
        response_mode: str | None = None,
        explicit_format: str | None = None,
    ) -> str:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        explicit = str(
            explicit_format
            or (metadata or {}).get("explicitSessionFormat")
            or ""
        ).strip().lower()

        by_format = ChatProseCompositionContentService.policy_for_explicit_format(explicit)

        if by_format:
            return by_format

        path = str((metadata or {}).get("path") or "").strip() or None
        entity = None
        api_meta = (metadata or {}).get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            entity = str(api_meta.get("entity") or "").strip() or None

        return ChatPresentationProfileService.prose_composition_policy(
            entity=entity,
            path=path,
        )

    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        assistant_markdown: str | None,
        *,
        tool_calls: list | None = None,
        response_mode: str | None = None,
        explicit_format: str | None = None,
    ) -> str:
        """Mescla marcadores no renderPlan; devolve markdown sem marcadores (para exibição)."""
        if not isinstance(metadata, dict):
            return str(assistant_markdown or "").strip()

        policy = cls.resolve_policy(
            metadata,
            response_mode=response_mode,
            explicit_format=explicit_format,
        )
        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            decision = {}
            metadata["presentationDecision"] = decision

        allowed_kinds = cls._resolve_allowed_kinds(
            metadata,
            policy=policy,
            response_mode=response_mode,
            explicit_format=explicit_format,
            tool_calls=tool_calls,
        )
        decision["proseCompositionAllowed"] = ChatProseCompositionContentService.llm_may_emit_markers(
            policy,
        )
        decision["allowedMarkerKinds"] = list(allowed_kinds)
        decision["proseCompositionPolicy"] = policy

        raw = str(assistant_markdown or "").strip()

        if not ChatProseCompositionContentService.llm_may_emit_markers(policy):
            cleaned = cls.strip_markers(raw)
            cls._store_display_markdown(metadata, cleaned)

            return cleaned

        segments = cls.parse_markers(raw)
        max_markers = ChatProseCompositionContentService.max_markers(
            policy,
            response_mode=response_mode,
        )
        render_segments: list[dict[str, Any]] = []
        marker_count = 0
        used_refs: set[tuple[str, int | None]] = set()

        for segment in segments:
            if segment.kind == "markdown":
                if segment.text.strip():
                    render_segments.append(
                        {
                            "kind": "markdown",
                            "slot": "assistantProse",
                            "source": "assistantMessage",
                            "text": segment.text.strip(),
                        }
                    )
                continue

            if marker_count >= max_markers:
                logger.info(
                    "prose_composition_marker_cap_reached policy=%s max=%s",
                    policy,
                    max_markers,
                )
                continue

            ref = cls.resolve_component_ref(
                segment.component_kind,
                segment.index,
                metadata,
                tool_calls=tool_calls,
                allowed_kinds=allowed_kinds,
            )

            if not ref:
                logger.info(
                    "prose_composition_marker_rejected kind=%s index=%s",
                    segment.component_kind,
                    segment.index,
                )
                continue

            ref_key = (str(ref.get("kind")), ref.get("index"))

            if ref_key in used_refs:
                continue

            used_refs.add(ref_key)
            marker_count += 1
            render_segments.append(
                {
                    "kind": ref["kind"],
                    "slot": ref["slot"],
                    "source": ref["source"],
                    **(
                        {"index": ref["index"]}
                        if ref.get("index") is not None
                        else {}
                    ),
                    **(
                        {"operationId": ref["operationId"]}
                        if ref.get("operationId")
                        else {}
                    ),
                }
            )

        cleaned = cls.strip_markers(raw)
        cls._store_display_markdown(metadata, cleaned)

        if marker_count < 1:
            json_result = cls._try_apply_json_fallback(
                metadata,
                raw,
                allowed_kinds=allowed_kinds,
                tool_calls=tool_calls,
                policy=policy,
                response_mode=response_mode,
            )

            if json_result is not None:
                return json_result

        if marker_count >= 1:
            layout_mode = "stack" if marker_count >= 2 or policy.endswith("stack") else "single"
            policy_node = ChatProseCompositionContentService.policy_node(policy)

            if policy_node.get("requireStackLayout"):
                layout_mode = "stack"

            if marker_count >= 2:
                layout_mode = "stack"

            decision["layoutMode"] = layout_mode
            metadata["proseCompositionSource"] = "llm"
            metadata["renderPlan"] = {
                "version": 1,
                "layoutMode": layout_mode,
                "segments": render_segments,
                "proseCompositionSource": "llm",
            }

        return cleaned

    @classmethod
    def _try_apply_json_fallback(
        cls,
        metadata: dict[str, Any],
        raw: str,
        *,
        allowed_kinds: list[str],
        tool_calls: list | None,
        policy: str,
        response_mode: str | None,
    ) -> str | None:
        import json

        text = str(raw or "").strip()

        if not text or "proseComposition" not in text:
            return None

        payload = None
        candidate = text

        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)

        if fence:
            candidate = fence.group(1)
        else:
            start = text.rfind("{")
            end = text.rfind("}")

            if start >= 0 and end > start:
                candidate = text[start : end + 1]

        try:
            payload = json.loads(candidate)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

        if not isinstance(payload, dict):
            return None

        composition = payload.get("proseComposition")

        if not isinstance(composition, dict):
            return None

        raw_segments = composition.get("segments")

        if not isinstance(raw_segments, list) or not raw_segments:
            return None

        max_markers = ChatProseCompositionContentService.max_markers(
            policy,
            response_mode=response_mode,
        )
        render_segments: list[dict[str, Any]] = []
        marker_count = 0
        prose_parts: list[str] = []

        for item in raw_segments:
            if not isinstance(item, dict):
                continue

            kind = str(item.get("kind") or "").strip().lower()

            if kind == "markdown":
                text_part = str(item.get("text") or "").strip()

                if text_part:
                    prose_parts.append(text_part)
                    render_segments.append(
                        {
                            "kind": "markdown",
                            "slot": "assistantProse",
                            "source": "assistantMessage",
                            "text": text_part,
                        }
                    )
                continue

            if marker_count >= max_markers:
                continue

            index_raw = item.get("index")

            try:
                index = int(index_raw) if index_raw not in (None, "") else None
            except (TypeError, ValueError):
                index = None

            ref = cls.resolve_component_ref(
                kind,
                index,
                metadata,
                tool_calls=tool_calls,
                allowed_kinds=allowed_kinds,
            )

            if not ref:
                continue

            marker_count += 1
            render_segments.append(
                {
                    "kind": ref["kind"],
                    "slot": ref["slot"],
                    "source": ref["source"],
                    **({"index": ref["index"]} if ref.get("index") is not None else {}),
                    **({"operationId": ref["operationId"]} if ref.get("operationId") else {}),
                }
            )

        if marker_count < 1:
            return None

        cleaned = "\n\n".join(prose_parts).strip() or cls.strip_markers(text)
        # Remove trailing JSON blob from display prose when it was appended.
        cleaned = re.sub(
            r"\s*\{[^{}]*\"proseComposition\"[^{}]*\}\s*$",
            "",
            cleaned,
            flags=re.DOTALL,
        ).strip() or cleaned
        cls._store_display_markdown(metadata, cleaned)

        layout_mode = "stack" if marker_count >= 2 or str(policy).endswith("stack") else "single"
        decision = metadata.setdefault("presentationDecision", {})
        decision["layoutMode"] = layout_mode
        metadata["proseCompositionSource"] = "llm"
        metadata["renderPlan"] = {
            "version": 1,
            "layoutMode": layout_mode,
            "segments": render_segments,
            "proseCompositionSource": "llm",
        }

        return cleaned

    @classmethod
    def apply_to_tool_calls(
        cls,
        answer: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> str:
        if not isinstance(tool_calls, list) or not tool_calls:
            return str(answer or "").strip()

        primary = None

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok"):
                primary = metadata
                break

        if primary is None:
            return str(answer or "").strip()

        return cls.apply(
            primary,
            answer,
            tool_calls=tool_calls,
            response_mode=response_mode,
            explicit_format=str(primary.get("explicitSessionFormat") or "").strip() or None,
        )

    @classmethod
    def apply_after_deterministic_plan(cls, metadata: dict[str, Any]) -> None:
        """Hook do finalize: anota allowed markers; só reescreve plan se já houver marcadores."""
        if not isinstance(metadata, dict):
            return

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            decision = {}
            metadata["presentationDecision"] = decision

        policy = cls.resolve_policy(metadata)
        allowed = cls._resolve_allowed_kinds(metadata, policy=policy)
        decision["proseCompositionAllowed"] = ChatProseCompositionContentService.llm_may_emit_markers(
            policy,
        )
        decision["allowedMarkerKinds"] = list(allowed)
        decision["proseCompositionPolicy"] = policy

        candidate = ""
        text_presentation = metadata.get("textPresentation")

        if isinstance(text_presentation, dict):
            candidate = str(text_presentation.get("markdown") or "").strip()

        if not candidate:
            candidate = str(metadata.get("assistantMarkdown") or "").strip()

        if candidate and "[[" in candidate:
            cls.apply(metadata, candidate)

    @classmethod
    def _resolve_allowed_kinds(
        cls,
        metadata: dict[str, Any] | None,
        *,
        policy: str,
        response_mode: str | None = None,
        explicit_format: str | None = None,
        tool_calls: list | None = None,
    ) -> list[str]:
        del response_mode

        if not ChatProseCompositionContentService.llm_may_emit_markers(policy):
            return []

        available = {
            str(slot.get("kind") or "").strip().lower()
            for slot in cls.collect_available_slots(metadata, tool_calls=tool_calls)
            if str(slot.get("kind") or "").strip()
        }
        explicit = str(
            explicit_format
            or (metadata or {}).get("explicitSessionFormat")
            or ""
        ).strip().lower()
        forbidden = set(
            ChatProseCompositionContentService.forbidden_markers_for_explicit(explicit)
        )

        return sorted(kind for kind in available if kind not in forbidden)

    @classmethod
    def _slots_from_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        operation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        slots: list[dict[str, Any]] = []
        op = operation_id or cls._operation_id(metadata)

        tables = metadata.get("tablePresentations")

        if isinstance(tables, list):
            for idx, item in enumerate(tables, start=1):
                if isinstance(item, dict):
                    slots.append(
                        {
                            "kind": "table",
                            "slot": f"table:{idx}",
                            "source": "tablePresentations",
                            "index": idx,
                            "operationId": op,
                        }
                    )
        elif isinstance(metadata.get("tablePresentation"), dict):
            slots.append(
                {
                    "kind": "table",
                    "slot": "table",
                    "source": "tablePresentation",
                    "index": 1,
                    "operationId": op,
                }
            )

        for kind, source in (
            ("tree", "treePresentation"),
            ("chart", "chartPresentation"),
            ("kpi", "kpiPresentation"),
            ("dashboard", "dashboardPresentation"),
        ):
            if isinstance(metadata.get(source), dict):
                slots.append(
                    {
                        "kind": kind,
                        "slot": kind,
                        "source": source,
                        "index": 1,
                        "operationId": op,
                    }
                )

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            ptype = ChatProseCompositionContentService.normalize_marker_kind(
                presentation.get("type"),
            )

            if ptype and not any(slot.get("kind") == ptype for slot in slots):
                slots.append(
                    {
                        "kind": ptype,
                        "slot": ptype,
                        "source": "presentation",
                        "index": 1,
                        "operationId": op,
                    }
                )

        plan = metadata.get("renderPlan")

        if isinstance(plan, dict):
            for segment in plan.get("segments") or []:
                if not isinstance(segment, dict):
                    continue

                kind = ChatProseCompositionContentService.normalize_marker_kind(
                    segment.get("kind"),
                )

                if not kind or kind == "markdown":
                    continue

                if any(slot.get("kind") == kind and slot.get("source") == segment.get("source") for slot in slots):
                    continue

                slots.append(
                    {
                        "kind": kind,
                        "slot": str(segment.get("slot") or kind),
                        "source": str(segment.get("source") or _KIND_TO_SOURCE.get(kind) or kind),
                        "index": segment.get("index") or (len([s for s in slots if s.get("kind") == kind]) + 1),
                        "operationId": op,
                    }
                )

        return slots

    @classmethod
    def _dedupe_slots(cls, slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, ...]] = set()
        output: list[dict[str, Any]] = []

        for slot in slots:
            key = (
                slot.get("kind"),
                slot.get("source"),
                slot.get("index"),
                slot.get("operationId"),
            )

            if key in seen:
                continue

            seen.add(key)
            output.append(slot)

        return output

    @classmethod
    def _operation_id(cls, metadata: dict[str, Any]) -> str | None:
        raw = metadata.get("operationId")

        if raw:
            return str(raw).strip() or None

        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict) and api_meta.get("operationId"):
            return str(api_meta.get("operationId")).strip() or None

        return None

    @classmethod
    def _store_display_markdown(cls, metadata: dict[str, Any], cleaned: str) -> None:
        metadata["assistantMarkdown"] = cleaned
        text_presentation = metadata.get("textPresentation")

        if isinstance(text_presentation, dict) and text_presentation.get("markdown"):
            # Mantém archive se já decoupled; não reintroduz prosa template.
            if metadata.get("llmProseDecoupled"):
                return

            text_presentation["markdown"] = cleaned
