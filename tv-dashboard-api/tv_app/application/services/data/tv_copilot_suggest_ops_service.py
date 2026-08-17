"""NL → ops tipadas do copiloto TV (determinístico, catálogo-driven; sem LLM no BFF)."""

from __future__ import annotations

import copy
import json
import re
import uuid
from typing import Any

from tv_app.application.services.data.tv_copilot_command_recognition_service import (
    TvCopilotCommandRecognitionService,
)
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
        """Fachada pública: sempre devolve um plano validado pelo contrato."""
        from tv_app.application.services.data.tv_copilot_command_planner_service import (
            TvCopilotCommandPlannerService,
        )

        plan = TvCopilotCommandPlannerService.plan(
            message=message,
            host_context=host_context,
        )
        return TvCopilotCommandPlannerService.to_suggest_payload(plan)

    @classmethod
    def materialize(
        cls,
        *,
        message: str,
        host_context: dict | None,
        authorization: str | None = None,
        user: Any | None = None,
    ) -> dict[str, Any]:
        """Materializa capability → ops; o planner valida target e política."""
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
        ranked_routes = cls._rank_operation_candidates(
            normalized=normalized,
            host=host,
            prefer_kpi=prefer_kpi,
            message=message,
        )
        placeholders = cls._build_placeholders(
            message=message,
            host=host,
            normalized=normalized,
            prefer_kpi=prefer_kpi,
            ranked_routes=ranked_routes,
        )
        max_ops = TvCopilotContentService.setting_int("maxSuggestOps", 5)
        destructive_intent = cls._has_destructive_intent(normalized)

        # Resume estruturado: «adicione no slide as fontes: op1, op2»
        explicit_ids = cls._extract_explicit_operation_ids(message)
        if explicit_ids:
            ops = cls._ops_for_explicit_operation_ids(explicit_ids)
            if ops:
                return {
                    "catalogVersion": catalog_version,
                    "ops": ops,
                    "matchedCapabilityKeys": ["create_data_source"],
                    "clarificationKey": None,
                    "candidates": [],
                    "reason": TvCopilotContentService.message(
                        "suggestOk", count=len(ops)
                    ),
                }

        scored: list[tuple[float, dict[str, Any]]] = []
        for cap in TvCopilotContentService.capabilities():
            score = cls._score_capability(
                cap, normalized, destructive_intent=destructive_intent
            )
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

        # Pedido de modelo/fonte com várias rotas próximas → seleção interativa.
        if cls._should_offer_route_selection(top, ranked_routes, placeholders):
            candidates = cls._candidate_payloads(ranked_routes)
            try:
                from tv_app.application.services.data.tv_catalog_selection_evidence_service import (
                    TvCatalogSelectionEvidenceService,
                )

                candidates = TvCatalogSelectionEvidenceService.enrich(
                    candidates,
                    authorization=authorization,
                    user=user,
                )
            except Exception:  # noqa: BLE001
                pass
            reason = TvCopilotContentService.message(
                "suggestNeedRouteSelection",
                count=len(candidates),
            )
            return {
                "catalogVersion": catalog_version,
                "ops": [],
                "matchedCapabilityKeys": [
                    str(cap.get("key") or "")
                    for _score, cap in top
                    if str(cap.get("key") or "").strip()
                ],
                "clarificationKey": "suggestNeedRouteSelection",
                "candidates": candidates,
                "reason": reason,
            }

        ops: list[dict[str, Any]] = []
        matched_keys: list[str] = []
        clarification_keys: list[str] = []

        def note_clarification(message_key: str | None) -> None:
            key = str(message_key or "").strip()
            if key and key not in clarification_keys:
                clarification_keys.append(key)

        for _score, cap in top:
            key = str(cap.get("key") or cap.get("op") or "").strip()
            if key:
                matched_keys.append(key)

            cap_clarify = str(cap.get("clarificationMessageKey") or "").strip()

            required = cap.get("requiresFilledPlaceholders")
            if isinstance(required, list):
                missing = [
                    str(name)
                    for name in required
                    if not str(placeholders.get(str(name)) or "").strip()
                ]
                if missing:
                    mapped = cls._clarification_for_placeholders(missing)
                    note_clarification(mapped or cap_clarify)
                    continue

            if bool(cap.get("isComposite")) and not placeholders.get("operationId"):
                note_clarification(
                    cap_clarify
                    or TvCopilotContentService.placeholder_clarifications().get(
                        "operationId"
                    )
                )
                continue

            templates = cls._templates_for_capability(cap)
            for template in templates:
                filled = cls._fill_template(template, placeholders)
                if not isinstance(filled, dict) or not filled:
                    continue
                filled = cls._enrich_filled_op(filled, placeholders)
                incomplete_field = cls._incomplete_op_field(filled)
                if incomplete_field:
                    mapped = TvCopilotContentService.op_field_clarifications().get(
                        incomplete_field
                    )
                    note_clarification(mapped or cap_clarify)
                    continue
                # Pedido de filial sem valor resolvido → clarifica (não inventa).
                if key == "update_data_source" and "filial" in normalized:
                    params = filled.get("params")
                    if not (
                        isinstance(params, dict) and "branch" in params
                    ):
                        note_clarification("suggestNeedBranchParam")
                        continue
                ops.append(filled)

        if not ops:
            if clarification_keys:
                reason = TvCopilotContentService.message(clarification_keys[0])
            elif matched_keys:
                reason = TvCopilotContentService.message("suggestIncompleteGeneric")
            else:
                reason = TvCopilotContentService.message("suggestNoMatch")
            return {
                "catalogVersion": catalog_version,
                "ops": [],
                "matchedCapabilityKeys": matched_keys,
                "clarificationKey": clarification_keys[0] if clarification_keys else None,
                "candidates": [],
                "reason": reason,
            }

        return {
            "catalogVersion": catalog_version,
            "ops": ops,
            "matchedCapabilityKeys": matched_keys,
            "clarificationKey": None,
            "candidates": [],
            "reason": TvCopilotContentService.message(
                "suggestOk", count=len(ops)
            ),
        }

    @classmethod
    def _clarification_for_placeholders(cls, missing: list[str]) -> str | None:
        mapping = TvCopilotContentService.placeholder_clarifications()
        for name in missing:
            key = mapping.get(str(name).strip())
            if key:
                return key
        return None

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
        single = str(host.get("selectedBlockId") or "").strip()
        if single:
            return single
        # Host pode enviar só o foco (contrato buildTvDashboardHostContext).
        return str(host.get("focusBlockId") or "").strip()

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
    def _host_data_sources(cls, host: dict[str, Any]) -> list[dict[str, str]]:
        raw = host.get("dataSources")
        out: list[dict[str, str]] = []
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                sid = str(item.get("id") or "").strip()
                op_id = str(item.get("operationId") or item.get("operation_id") or "").strip()
                if not sid or not op_id:
                    continue
                label = str(item.get("label") or "").strip() or op_id
                out.append({"id": sid, "operationId": op_id, "label": label})
        return out

    @classmethod
    def _resolve_data_source_id(
        cls,
        *,
        host: dict[str, Any],
        normalized: str,
        operation_id: str,
    ) -> str:
        selected = str(
            host.get("selectedDataSourceId") or host.get("dataSourceId") or ""
        ).strip()
        if selected:
            return selected

        sources = cls._host_data_sources(host)
        if not sources:
            return ""

        if operation_id:
            for item in sources:
                if item["operationId"] == operation_id:
                    return item["id"]

        for item in sources:
            label = item["label"].lower()
            op_id = item["operationId"].lower()
            if label and label in normalized:
                return item["id"]
            # match short alias tokens from operation id
            short = op_id.replace("get_", "").replace("_", " ")
            if short and short in normalized:
                return item["id"]

        if len(sources) == 1:
            return sources[0]["id"]
        return ""

    @classmethod
    def _resolve_selected_visual_id(cls, host: dict[str, Any]) -> str:
        visual = str(host.get("selectedVisualId") or "").strip()
        if visual:
            return visual
        focus_type = str(host.get("focusBlockType") or "").strip()
        if focus_type in {"kpi_view", "chart_view", "table_view"}:
            return str(host.get("focusBlockId") or "").strip() or cls._first_selected_block_id(
                host
            )
        return ""

    @classmethod
    def _extract_params(cls, normalized: str) -> dict[str, Any]:
        params: dict[str, Any] = {}
        hints = TvCopilotContentService.param_hints()
        for _name, spec in hints.items():
            if not isinstance(spec, dict):
                continue
            param_key = str(spec.get("paramKey") or "").strip()
            if not param_key:
                continue
            patterns = spec.get("patterns")
            if not isinstance(patterns, list):
                continue
            for pattern in sorted(
                patterns,
                key=lambda item: -len(str((item or {}).get("markers") or "")),
            ):
                if not isinstance(pattern, dict):
                    continue
                markers = pattern.get("markers")
                if not isinstance(markers, list):
                    continue
                for marker in sorted(
                    (str(m).strip().lower() for m in markers if str(m).strip()),
                    key=len,
                    reverse=True,
                ):
                    if marker in normalized:
                        params[param_key] = pattern.get("value", "")
                        break
                if param_key in params:
                    break
        return params

    @classmethod
    def _extract_transform_steps(cls, normalized: str) -> list[dict[str, Any]]:
        steps: list[dict[str, Any]] = []
        for hint in TvCopilotContentService.transform_step_hints():
            markers = hint.get("markers")
            step = hint.get("step")
            if not isinstance(markers, list) or not isinstance(step, dict):
                continue
            for marker in sorted(
                (str(m).strip().lower() for m in markers if str(m).strip()),
                key=len,
                reverse=True,
            ):
                if marker in normalized:
                    steps.append(copy.deepcopy(step))
                    break
        return steps

    @classmethod
    def _extract_field_labels(cls, message: str, quoted: str) -> dict[str, str]:
        """Ex.: renomeie o campo \"value\" para \"OEE\" — usa aspas na mensagem."""
        raw = str(message or "")
        matches = list(_QUOTED_RE.finditer(raw))
        if len(matches) < 2:
            return {}
        values: list[str] = []
        for match in matches[:2]:
            for group in match.groups():
                if group is not None and str(group).strip():
                    values.append(str(group).strip())
                    break
        if len(values) < 2:
            return {}
        return {values[0]: values[1]}

    @classmethod
    def _extract_explicit_operation_ids(cls, message: str) -> list[str]:
        """Resume structured_action: «adicione no slide as fontes: id1, id2»."""
        raw = str(message or "")
        lower = raw.lower()
        marker = "fontes:"
        idx = lower.rfind(marker)
        if idx < 0:
            marker = "fonte:"
            idx = lower.rfind(marker)
        if idx < 0:
            return []
        tail = raw[idx + len(marker) :]
        parts = re.split(r"[,;\s]+", tail)
        out: list[str] = []
        seen: set[str] = set()
        for part in parts:
            op_id = str(part or "").strip().strip("«»\"'")
            if not op_id or op_id in seen:
                continue
            if not TvDataRouteCatalogService().get_route(op_id):
                continue
            seen.add(op_id)
            out.append(op_id)
        return out

    @classmethod
    def _ops_for_explicit_operation_ids(
        cls,
        operation_ids: list[str],
    ) -> list[dict[str, Any]]:
        ops: list[dict[str, Any]] = []
        for op_id in operation_ids:
            route = TvDataRouteCatalogService().get_route(op_id) or {}
            label = str(route.get("label") or op_id).strip()
            ops.append(
                {
                    "op": "upsert_data_source",
                    "operationId": op_id,
                    "params": {},
                    "blockId": cls._new_id("ds"),
                    "label": label,
                }
            )
        return ops

    @classmethod
    def _should_offer_route_selection(
        cls,
        top: list[tuple[float, dict[str, Any]]],
        ranked_routes: list[dict[str, Any]],
        placeholders: dict[str, str],
    ) -> bool:
        if len(ranked_routes) < 2:
            return False
        # Já há operationId único resolvido e capability não é só create_data_source?
        keys = {
            str(cap.get("key") or "").strip()
            for _score, cap in top
            if str(cap.get("key") or "").strip()
        }
        data_source_keys = {
            "create_data_source",
            "add_kpi_from_route",
            "add_chart_from_route",
            "add_table_from_route",
            "update_data_source",
        }
        if not (keys & data_source_keys):
            return False
        # create_data_source / model requests prefer selection when rivals exist.
        if "create_data_source" in keys:
            return True
        # Composites: só se não houver vencedor único preenchido.
        return not str(placeholders.get("operationId") or "").strip()

    @classmethod
    def _candidate_payloads(
        cls,
        ranked_routes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in ranked_routes:
            op_id = str(row.get("operationId") or "").strip()
            if not op_id:
                continue
            out.append(
                {
                    "operationId": op_id,
                    "id": op_id,
                    "label": str(row.get("label") or op_id).strip(),
                    "score": row.get("score"),
                    "reason": str(row.get("reason") or "").strip() or None,
                    "path": str(row.get("path") or "").strip() or None,
                    "suggestedDisplayModes": row.get("suggestedDisplayModes")
                    or row.get("allowedDisplayModes"),
                }
            )
        return out

    @classmethod
    def _rank_operation_candidates(
        cls,
        *,
        normalized: str,
        host: dict[str, Any],
        prefer_kpi: bool,
        message: str,
    ) -> list[dict[str, Any]]:
        """Rankeia rotas allowlisted; gap alto → 1 vencedor; gap baixo → top-N."""
        limit = TvCopilotContentService.setting_int("routeCandidateLimit", 5)
        min_score = TvCopilotContentService.setting_float("routeCandidateMinScore", 4.0)
        gap_threshold = TvCopilotContentService.setting_float(
            "routeCandidateScoreGap", 2.5
        )

        # Preferir ranking do chat base (S2S) quando disponível.
        ai_ranked = cls._rank_via_ai_suggest(message=message, limit=limit)
        if ai_ranked:
            return cls._apply_gap_policy(
                ai_ranked,
                gap_threshold=gap_threshold,
                min_score=0.0,
            )

        scored: list[dict[str, Any]] = []
        hints = TvCopilotContentService.nl_route_hints()
        hint_boost_ids: set[str] = set()
        for alias, operation_id in sorted(hints.items(), key=lambda item: -len(item[0])):
            if alias and alias in normalized:
                op_id = str(operation_id or "").strip()
                if op_id:
                    hint_boost_ids.add(op_id)

        from_host = str(host.get("operationId") or "").strip()
        if from_host:
            route = TvDataRouteCatalogService().get_route(from_host)
            if isinstance(route, dict):
                return [
                    {
                        **route,
                        "operationId": from_host,
                        "label": str(route.get("label") or from_host).strip(),
                        "score": 100.0,
                        "reason": "host",
                    }
                ]

        for route in TvDataRouteCatalogService().list_routes():
            if not isinstance(route, dict):
                continue
            op_id = str(route.get("operationId") or "").strip()
            if not op_id:
                continue
            score = cls._score_route(route, normalized, prefer_kpi=prefer_kpi)
            if op_id in hint_boost_ids:
                score += 6.0
            if score <= 0:
                continue
            scored.append(
                {
                    **route,
                    "operationId": op_id,
                    "label": str(route.get("label") or op_id).strip(),
                    "score": round(score, 4),
                    "reason": "local_rank",
                }
            )

        scored.sort(
            key=lambda item: (
                -float(item.get("score") or 0),
                str(item.get("operationId") or ""),
            )
        )
        return cls._apply_gap_policy(
            scored[: max(limit * 2, limit)],
            gap_threshold=gap_threshold,
            min_score=min_score,
            limit=limit,
        )

    @classmethod
    def _rank_via_ai_suggest(
        cls,
        *,
        message: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        try:
            from tv_app.application.services.data.tv_data_route_suggest_service import (
                TvDataRouteSuggestService,
            )
            from tv_app.infrastructure.gateways.minha_delpi_ai_client import (
                MinhaDelpiAiClient,
            )

            # Copiloto precisa de resposta rápida; Assistente modal mantém timeout longo.
            service = TvDataRouteSuggestService(
                TvDataRouteCatalogService(),
                ai_client=MinhaDelpiAiClient(timeout_seconds=2.0),
            )
            result = service.suggest(query=message, limit=limit)
        except Exception:
            return []
        if not isinstance(result, dict) or result.get("degraded"):
            return []
        suggestions = result.get("suggestions")
        if not isinstance(suggestions, list) or not suggestions:
            return []
        out: list[dict[str, Any]] = []
        for row in suggestions:
            if not isinstance(row, dict):
                continue
            op_id = str(row.get("operationId") or "").strip()
            if not op_id:
                continue
            score_raw = row.get("score")
            try:
                score = float(score_raw) if score_raw is not None else 0.0
            except (TypeError, ValueError):
                score = 0.0
            out.append(
                {
                    **row,
                    "operationId": op_id,
                    "label": str(row.get("label") or op_id).strip(),
                    "score": score,
                    "reason": str(row.get("reason") or "ai_suggest").strip(),
                }
            )
        return out

    @classmethod
    def _apply_gap_policy(
        cls,
        ranked: list[dict[str, Any]],
        *,
        gap_threshold: float,
        min_score: float,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if not ranked:
            return []
        cap = limit or TvCopilotContentService.setting_int("routeCandidateLimit", 5)
        filtered = [
            row
            for row in ranked
            if float(row.get("score") or 0) >= min_score or min_score <= 0
        ]
        if not filtered:
            filtered = list(ranked[:cap])
        if len(filtered) == 1:
            return filtered[:1]
        top = float(filtered[0].get("score") or 0)
        second = float(filtered[1].get("score") or 0)
        if top - second >= gap_threshold and top >= min_score:
            return filtered[:1]
        return filtered[:cap]

    @classmethod
    def _resolve_operation_id(
        cls,
        *,
        normalized: str,
        host: dict[str, Any],
        prefer_kpi: bool,
        ranked_routes: list[dict[str, Any]] | None = None,
        message: str = "",
    ) -> tuple[str, str]:
        ranked = ranked_routes
        if ranked is None:
            ranked = cls._rank_operation_candidates(
                normalized=normalized,
                host=host,
                prefer_kpi=prefer_kpi,
                message=message or normalized,
            )
        if len(ranked) == 1:
            op_id = str(ranked[0].get("operationId") or "").strip()
            label = str(ranked[0].get("label") or op_id).strip()
            return op_id, label
        # Múltiplos candidatos: não preencher placeholder (força seleção).
        if len(ranked) > 1:
            return "", ""
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
        ranked_routes: list[dict[str, Any]] | None = None,
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
            ranked_routes=ranked_routes,
            message=message,
        )
        background_color = cls._extract_background_color(message, normalized)
        default_text = TvCopilotContentService.setting_str(
            "defaultTextBlockContent", ""
        )
        text_content = quoted if quoted else default_text
        data_source_id = cls._resolve_data_source_id(
            host=host,
            normalized=normalized,
            operation_id=operation_id,
        )
        selected_visual_id = cls._resolve_selected_visual_id(host)
        params = cls._extract_params(normalized)
        transform_steps = cls._extract_transform_steps(normalized)
        field_labels = cls._extract_field_labels(message, quoted)
        return {
            "quoted": quoted,
            "textContent": text_content,
            "selectedBlockId": cls._first_selected_block_id(host),
            "selectedVisualId": selected_visual_id,
            "slideId": str(host.get("slideId") or "").strip(),
            "playlistId": str(host.get("playlistId") or "").strip(),
            "sectionId": str(host.get("sectionId") or "").strip(),
            "dataSourceId": data_source_id,
            "operationId": operation_id,
            "routeLabel": route_label,
            "presetKey": str(host.get("presetKey") or "").strip(),
            "backgroundColor": background_color,
            "paramsJson": json.dumps(params, ensure_ascii=False) if params else "",
            "transformStepsJson": (
                json.dumps(transform_steps, ensure_ascii=False) if transform_steps else ""
            ),
            "fieldLabelsJson": (
                json.dumps(field_labels, ensure_ascii=False) if field_labels else ""
            ),
            "branchParam": str(params.get("branch", "")) if "branch" in params else "",
            "newDataSourceId": cls._new_id("ds"),
            "newVisualId": cls._new_id("viz"),
            "newTextBlockId": cls._new_id("txt"),
            "title": quoted or default_title,
            "name": quoted or default_playlist,
            "sectionName": quoted or default_section,
        }

    @classmethod
    def _enrich_filled_op(
        cls,
        op: dict[str, Any],
        placeholders: dict[str, str],
    ) -> dict[str, Any]:
        name = str(op.get("op") or "").strip()
        if name == "upsert_data_source":
            params_raw = str(placeholders.get("paramsJson") or "").strip()
            if params_raw:
                try:
                    parsed = json.loads(params_raw)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, dict) and parsed:
                    base = op.get("params") if isinstance(op.get("params"), dict) else {}
                    op["params"] = {**base, **parsed}
            labels_raw = str(placeholders.get("fieldLabelsJson") or "").strip()
            if labels_raw:
                try:
                    labels = json.loads(labels_raw)
                except json.JSONDecodeError:
                    labels = None
                if isinstance(labels, dict) and labels:
                    op["fieldLabels"] = {
                        str(k): str(v)
                        for k, v in labels.items()
                        if str(k).strip() and str(v).strip()
                    }
        elif name == "set_data_transform":
            steps_raw = str(placeholders.get("transformStepsJson") or "").strip()
            if steps_raw:
                try:
                    steps = json.loads(steps_raw)
                except json.JSONDecodeError:
                    steps = None
                if isinstance(steps, list):
                    op["steps"] = steps
        return op

    @classmethod
    def _action_terms_for_capability(cls, cap: dict[str, Any]) -> list[str]:
        raw_terms = cap.get("actionTerms")
        if isinstance(raw_terms, list) and raw_terms:
            terms = [str(item).strip().lower() for item in raw_terms if str(item).strip()]
        else:
            terms = TvCopilotContentService.action_terms_for_set(
                str(cap.get("actionTermSet") or "any")
            )
        if cls._is_destructive_capability(cap):
            return terms
        # Verbo de remoção não reforça capability construtiva («apague» ≠ criar texto).
        destructive = set(TvCopilotContentService.destructive_action_terms())
        return [term for term in terms if term not in destructive]

    @classmethod
    def _is_destructive_capability(cls, cap: dict[str, Any]) -> bool:
        """Polaridade da capability: declarada no catálogo ou inferida pela op ``delete_*``."""
        declared = str(cap.get("intentPolarity") or "").strip().lower()
        if declared in {"destructive", "constructive"}:
            return declared == "destructive"
        return str(cap.get("op") or "").strip().startswith("delete_")

    @classmethod
    def _has_destructive_intent(cls, normalized: str) -> bool:
        for term in TvCopilotContentService.destructive_action_terms():
            if cls._marker_hit(term, normalized):
                return True
        return False

    @classmethod
    def _marker_hit(cls, needle: str, haystack: str) -> bool:
        return TvCopilotCommandRecognitionService.marker_hit(needle, haystack)

    @classmethod
    def _score_capability(
        cls,
        cap: dict[str, Any],
        normalized: str,
        *,
        destructive_intent: bool = False,
    ) -> float:
        # Pedido de remoção só concorre com capability destrutiva (e vice-versa):
        # evita «apague a caixa de texto» virar criação de texto vazio.
        if destructive_intent != cls._is_destructive_capability(cap):
            return 0.0

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
    def _incomplete_op_field(cls, op: dict[str, Any]) -> str | None:
        """Retorna chave `op.campo` incompleta, ou None se a op está pronta.

        Texto vazio em bloco `text` é permitido (caixa em branco no slide).
        """
        name = str(op.get("op") or "").strip()
        if name == "patch_native_config":
            patch = op.get("patch")
            if not isinstance(patch, dict) or not patch:
                return "patch_native_config.patch"
            if "background" in patch:
                background = patch.get("background")
                if not isinstance(background, dict):
                    return "patch_native_config.background"
                if not str(background.get("value") or "").strip():
                    return "patch_native_config.background"
                if not str(background.get("type") or "").strip():
                    return "patch_native_config.background"
            return None
        if name == "upsert_data_source":
            if not str(op.get("operationId") or "").strip():
                return "upsert_data_source.operationId"
            if not str(op.get("blockId") or "").strip():
                return "upsert_data_source.blockId"
            return None
        if name == "set_data_transform":
            if not str(op.get("blockId") or "").strip():
                return "set_data_transform.blockId"
            steps = op.get("steps")
            if not isinstance(steps, list) or not steps:
                return "set_data_transform.steps"
            return None
        if name == "bind_visual":
            if not str(op.get("visualId") or "").strip():
                return "bind_visual.visualId"
            if not str(op.get("dataSourceId") or "").strip():
                return "bind_visual.dataSourceId"
            return None
        if name == "delete_block":
            if not str(op.get("blockId") or "").strip():
                return "delete_block.blockId"
            return None
        if name == "add_slide_from_preset":
            if not str(op.get("presetKey") or "").strip():
                return "add_slide_from_preset.presetKey"
            return None
        if name == "update_slide":
            if "title" in op and not str(op.get("title") or "").strip():
                return "update_slide.title"
            return None
        if name == "reorder_slides":
            items = op.get("items")
            if not isinstance(items, list) or not items:
                return "reorder_slides.items"
            return None
        if name == "upsert_block":
            block = op.get("block")
            if not isinstance(block, dict) or not block:
                return "upsert_block.block"
            return None
        return None

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
