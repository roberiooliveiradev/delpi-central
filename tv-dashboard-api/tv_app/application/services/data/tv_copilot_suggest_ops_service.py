"""NL → ops tipadas do copiloto TV (determinístico, catálogo-driven; sem LLM no BFF)."""

from __future__ import annotations

import copy
import re
import uuid
from typing import Any

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
_QUOTED_RE = re.compile(
    r'"([^"]+)"'
    r"|'([^']+)'"
    r"|\u201c([^\u201d]+)\u201d"
    r"|«([^»]+)»"
)
_HEX_RE = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
_KPI_INTENT_MARKERS = frozenset(
    {"kpi", "indicador", "adicione um kpi", "adicionar kpi", "criar kpi", "crie um kpi"}
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
        prefer_kpi = cls._message_asks_kpi(normalized)
        placeholders = cls._build_placeholders(
            message=message,
            host=host,
            normalized=normalized,
            prefer_kpi=prefer_kpi,
        )
        max_ops = TvCopilotContentService.setting_int("maxSuggestOps", 5)

        scored: list[tuple[float, dict[str, Any]]] = []
        for cap in TvCopilotContentService.capabilities():
            score = cls._score_capability(cap, normalized)
            if score <= 0:
                continue
            scored.append((score, cap))

        scored.sort(key=lambda item: (-item[0], str(item[1].get("key") or "")))

        composites = [
            (score, cap)
            for score, cap in scored
            if bool(cap.get("isComposite"))
        ]
        if composites and placeholders.get("operationId"):
            top: list[tuple[float, dict[str, Any]]] = [composites[0]]
        else:
            top = [
                (score, cap)
                for score, cap in scored
                if not bool(cap.get("isComposite"))
            ][: max(1, max_ops)]
            if not top and composites:
                top = [composites[0]]

        ops: list[dict[str, Any]] = []
        matched_keys: list[str] = []
        skipped_need_color = False
        skipped_need_operation = False

        for _score, cap in top:
            key = str(cap.get("key") or cap.get("op") or "").strip()
            if key:
                matched_keys.append(key)

            required = cap.get("requiresFilledPlaceholders")
            if isinstance(required, list):
                missing = [
                    str(name)
                    for name in required
                    if not str(placeholders.get(str(name)) or "").strip()
                ]
                if missing:
                    if "backgroundColor" in missing:
                        skipped_need_color = True
                    continue

            if bool(cap.get("isComposite")) and not placeholders.get("operationId"):
                skipped_need_operation = True
                continue

            templates = cls._templates_for_capability(cap)
            for template in templates:
                filled = cls._fill_template(template, placeholders)
                if not isinstance(filled, dict) or not filled:
                    continue
                if cls._is_op_incomplete(filled):
                    if filled.get("op") == "patch_native_config":
                        skipped_need_color = True
                    if filled.get("op") == "upsert_data_source":
                        skipped_need_operation = True
                    continue
                ops.append(filled)

        if not ops:
            if skipped_need_color:
                reason = TvCopilotContentService.message("suggestNeedColor")
            elif skipped_need_operation:
                reason = TvCopilotContentService.message("suggestNeedOperationId")
            else:
                reason = TvCopilotContentService.message("suggestNoMatch")
            return {
                "catalogVersion": catalog_version,
                "ops": [],
                "matchedCapabilityKeys": matched_keys,
                "reason": reason,
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
    def _templates_for_capability(cls, cap: dict[str, Any]) -> list[dict[str, Any]]:
        multi = cap.get("payloadTemplates")
        if isinstance(multi, list) and multi:
            return [item for item in multi if isinstance(item, dict)]
        single = cap.get("payloadTemplate")
        if isinstance(single, dict):
            return [single]
        op_name = str(cap.get("op") or "").strip()
        if op_name:
            return [{"op": op_name}]
        return []

    @classmethod
    def _message_asks_kpi(cls, normalized: str) -> bool:
        for marker in _KPI_INTENT_MARKERS:
            if marker in normalized:
                return True
        return False

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
    def _normalize_hex(cls, raw: str) -> str:
        token = str(raw or "").strip().lstrip("#")
        if len(token) == 3:
            token = "".join(ch * 2 for ch in token)
        if len(token) != 6:
            return ""
        try:
            int(token, 16)
        except ValueError:
            return ""
        return f"#{token.lower()}"

    @classmethod
    def _extract_background_color(cls, message: str, normalized: str) -> str:
        hex_match = _HEX_RE.search(str(message or ""))
        if hex_match:
            normalized_hex = cls._normalize_hex(hex_match.group(0))
            if normalized_hex:
                return normalized_hex

        vocab = TvCopilotContentService.color_vocabulary()
        for name, value in sorted(vocab.items(), key=lambda item: -len(item[0])):
            if name and name in normalized:
                hex_value = (
                    cls._normalize_hex(value)
                    if str(value).startswith("#")
                    else str(value).strip()
                )
                if hex_value.startswith("#"):
                    return hex_value
                normalized_hex = cls._normalize_hex(hex_value)
                if normalized_hex:
                    return normalized_hex
        return ""

    @classmethod
    def _new_id(cls, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:10]}"

    @classmethod
    def _resolve_operation_id(
        cls,
        *,
        normalized: str,
        host: dict[str, Any],
        prefer_kpi: bool,
    ) -> tuple[str, str]:
        from_host = str(host.get("operationId") or "").strip()
        if from_host:
            route = TvDataRouteCatalogService().get_route(from_host)
            label = ""
            if isinstance(route, dict):
                label = str(route.get("label") or from_host).strip()
            return from_host, label or from_host

        hints = TvCopilotContentService.nl_route_hints()
        for alias, operation_id in sorted(hints.items(), key=lambda item: -len(item[0])):
            if alias and alias in normalized:
                op_id = str(operation_id or "").strip()
                if not op_id:
                    continue
                route = TvDataRouteCatalogService().get_route(op_id)
                if not route:
                    continue
                label = str(route.get("label") or op_id).strip()
                return op_id, label

        best_id = ""
        best_label = ""
        best_score = 0.0
        for route in TvDataRouteCatalogService().list_routes():
            if not isinstance(route, dict):
                continue
            op_id = str(route.get("operationId") or "").strip()
            if not op_id:
                continue
            score = cls._score_route(route, normalized, prefer_kpi=prefer_kpi)
            if score > best_score:
                best_score = score
                best_id = op_id
                best_label = str(route.get("label") or op_id).strip()

        if best_score >= 4.0:
            return best_id, best_label
        return "", ""

    @classmethod
    def _score_route(
        cls,
        route: dict[str, Any],
        normalized: str,
        *,
        prefer_kpi: bool,
    ) -> float:
        score = 0.0
        op_id = str(route.get("operationId") or "").strip().lower()
        label = str(route.get("label") or "").strip().lower()
        when_to_use = str(route.get("whenToUse") or "").strip().lower()
        description = str(route.get("description") or "").strip().lower()
        haystacks = [op_id, label, when_to_use, description]
        aliases = route.get("labelAliases")
        if isinstance(aliases, list):
            haystacks.extend(
                str(item).strip().lower() for item in aliases if str(item).strip()
            )

        tokens = [
            tok
            for tok in re.split(r"[^a-z0-9áéíóúãõâêôç_+-]+", normalized)
            if len(tok) >= 3
        ]
        for token in tokens:
            for hay in haystacks:
                if not hay:
                    continue
                if token == hay or token in hay or hay in token:
                    score += 2.0 + min(len(token), 24) / 12.0
                    break

        if prefer_kpi:
            modes = route.get("allowedDisplayModes") or []
            mode_set = {
                str(item).strip().lower()
                for item in modes
                if str(item or "").strip()
            }
            if "kpi" in mode_set or "auto" in mode_set:
                score += 3.0
            if str(route.get("metaShape") or "").strip().lower() == "scalar":
                score += 2.0
        return score

    @classmethod
    def _build_placeholders(
        cls,
        *,
        message: str,
        host: dict[str, Any],
        normalized: str,
        prefer_kpi: bool,
    ) -> dict[str, str]:
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
        operation_id, route_label = cls._resolve_operation_id(
            normalized=normalized,
            host=host,
            prefer_kpi=prefer_kpi,
        )
        background_color = cls._extract_background_color(message, normalized)
        return {
            "quoted": quoted,
            "selectedBlockId": cls._first_selected_block_id(host),
            "slideId": str(host.get("slideId") or "").strip(),
            "playlistId": str(host.get("playlistId") or "").strip(),
            "sectionId": str(host.get("sectionId") or "").strip(),
            "dataSourceId": str(host.get("dataSourceId") or "").strip(),
            "operationId": operation_id,
            "routeLabel": route_label,
            "presetKey": str(host.get("presetKey") or "").strip(),
            "backgroundColor": background_color,
            "newDataSourceId": cls._new_id("ds"),
            "newVisualId": cls._new_id("viz"),
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
    def _is_op_incomplete(cls, op: dict[str, Any]) -> bool:
        name = str(op.get("op") or "").strip()
        if name == "patch_native_config":
            patch = op.get("patch")
            if not isinstance(patch, dict) or not patch:
                return True
            if "background" in patch:
                background = patch.get("background")
                if not isinstance(background, dict):
                    return True
                if not str(background.get("value") or "").strip():
                    return True
                if not str(background.get("type") or "").strip():
                    return True
            return False
        if name == "upsert_data_source":
            return not str(op.get("operationId") or "").strip()
        if name == "bind_visual":
            return not (
                str(op.get("visualId") or "").strip()
                and str(op.get("dataSourceId") or "").strip()
            )
        if name == "delete_block":
            return not str(op.get("blockId") or "").strip()
        if name == "add_slide_from_preset":
            return not str(op.get("presetKey") or "").strip()
        if name == "upsert_block":
            block = op.get("block")
            if not isinstance(block, dict) or not block:
                return True
            block_type = str(block.get("type") or "").strip()
            if block_type == "text" and not str(block.get("content") or "").strip():
                return True
            return False
        return False

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
