"""NL → ops tipadas do copiloto TV (determinístico, catálogo-driven; sem LLM no BFF)."""

from __future__ import annotations

import copy
import re
from typing import Any

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
_QUOTED_RE = re.compile(
    r'"([^"]+)"'
    r"|'([^']+)'"
    r"|\u201c([^\u201d]+)\u201d"
    r"|«([^»]+)»"
)


class TvCopilotSuggestOpsService:
    @classmethod
    def suggest(cls, *, message: str, host_context: dict | None) -> dict[str, Any]:
        catalog_version = TvCopilotContentService.catalog_version()
        normalized = cls._normalize(message)
        if not normalized:
            return {
                "catalogVersion": catalog_version,
                "ops": [],
                "matchedCapabilityKeys": [],
                "reason": TvCopilotContentService.message("suggestEmptyMessage"),
            }

        host = host_context if isinstance(host_context, dict) else {}
        placeholders = cls._build_placeholders(message=message, host=host)
        max_ops = TvCopilotContentService.setting_int("maxSuggestOps", 5)

        scored: list[tuple[float, dict[str, Any]]] = []
        for cap in TvCopilotContentService.capabilities():
            score = cls._score_capability(cap, normalized)
            if score <= 0:
                continue
            scored.append((score, cap))

        scored.sort(key=lambda item: (-item[0], str(item[1].get("key") or "")))
        top = scored[: max(1, max_ops)]

        ops: list[dict[str, Any]] = []
        matched_keys: list[str] = []
        for _score, cap in top:
            key = str(cap.get("key") or cap.get("op") or "").strip()
            if key:
                matched_keys.append(key)
            template = cap.get("payloadTemplate")
            if isinstance(template, dict):
                filled = cls._fill_template(template, placeholders)
                if isinstance(filled, dict) and filled:
                    ops.append(filled)
            else:
                op_name = str(cap.get("op") or "").strip()
                if op_name:
                    ops.append({"op": op_name})

        if not ops:
            return {
                "catalogVersion": catalog_version,
                "ops": [],
                "matchedCapabilityKeys": [],
                "reason": TvCopilotContentService.message("suggestNoMatch"),
            }

        return {
            "catalogVersion": catalog_version,
            "ops": ops,
            "matchedCapabilityKeys": matched_keys,
            "reason": TvCopilotContentService.message(
                "suggestOk", count=len(ops)
            ),
        }

    @classmethod
    def _normalize(cls, message: str) -> str:
        return " ".join(str(message or "").strip().lower().split())

    @classmethod
    def _extract_quoted(cls, message: str) -> str:
        raw = str(message or "")
        match = _QUOTED_RE.search(raw)
        if not match:
            return ""
        for group in match.groups():
            if group is not None and str(group).strip():
                return str(group).strip()
        return ""

    @classmethod
    def _first_selected_block_id(cls, host: dict[str, Any]) -> str:
        raw = host.get("selectedBlockIds")
        if isinstance(raw, list):
            for item in raw:
                value = str(item or "").strip()
                if value:
                    return value
        single = host.get("selectedBlockId")
        return str(single or "").strip()

    @classmethod
    def _build_placeholders(cls, *, message: str, host: dict[str, Any]) -> dict[str, str]:
        quoted = cls._extract_quoted(message)
        default_title = TvCopilotContentService.setting_str(
            "defaultSlideTitle", "Slide personalizado"
        )
        default_playlist = TvCopilotContentService.setting_str(
            "defaultPlaylistName", "Nova programação"
        )
        default_section = TvCopilotContentService.setting_str(
            "defaultSectionName", "Nova seção"
        )
        return {
            "quoted": quoted,
            "selectedBlockId": cls._first_selected_block_id(host),
            "slideId": str(host.get("slideId") or "").strip(),
            "playlistId": str(host.get("playlistId") or "").strip(),
            "sectionId": str(host.get("sectionId") or "").strip(),
            "dataSourceId": str(host.get("dataSourceId") or "").strip(),
            "operationId": str(host.get("operationId") or "").strip(),
            "presetKey": str(host.get("presetKey") or "").strip(),
            "title": quoted or default_title,
            "name": quoted or default_playlist,
            "sectionName": quoted or default_section,
        }

    @classmethod
    def _action_terms_for_capability(cls, cap: dict[str, Any]) -> list[str]:
        raw_terms = cap.get("actionTerms")
        if isinstance(raw_terms, list) and raw_terms:
            return [str(item).strip().lower() for item in raw_terms if str(item).strip()]
        return TvCopilotContentService.action_terms_for_set(
            str(cap.get("actionTermSet") or "any")
        )

    @classmethod
    def _marker_hit(cls, needle: str, haystack: str) -> bool:
        token = str(needle or "").strip().lower()
        if not token:
            return False
        return token in haystack

    @classmethod
    def _score_capability(cls, cap: dict[str, Any], normalized: str) -> float:
        exclude = cap.get("excludeMarkers")
        if isinstance(exclude, list):
            for marker in exclude:
                if cls._marker_hit(str(marker), normalized):
                    return 0.0

        content_markers = cap.get("contentMarkers")
        marker_score = 0.0
        marker_hits = 0
        if isinstance(content_markers, list):
            for marker in content_markers:
                text = str(marker or "").strip().lower()
                if not text:
                    continue
                if cls._marker_hit(text, normalized):
                    marker_hits += 1
                    # Prefer longer / more specific markers.
                    marker_score += 2.0 + min(len(text), 40) / 10.0

        if marker_hits == 0:
            return 0.0

        action_bonus = 0.0
        for term in cls._action_terms_for_capability(cap):
            if cls._marker_hit(term, normalized):
                action_bonus = 1.5
                break

        return marker_score + action_bonus

    @classmethod
    def _fill_string(cls, value: str, placeholders: dict[str, str]) -> str:
        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return placeholders.get(key, "")

        return _PLACEHOLDER_RE.sub(repl, value)

    @classmethod
    def _fill_template(cls, node: Any, placeholders: dict[str, str]) -> Any:
        if isinstance(node, dict):
            out: dict[str, Any] = {}
            for key, value in node.items():
                filled = cls._fill_template(value, placeholders)
                out[key] = filled
            return out
        if isinstance(node, list):
            return [cls._fill_template(item, placeholders) for item in node]
        if isinstance(node, str):
            return cls._fill_string(node, placeholders)
        return copy.deepcopy(node)
