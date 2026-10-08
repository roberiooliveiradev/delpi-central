"""NL → ops tipadas do PresentationMutation (determinístico, catálogo-driven; sem LLM no BFF)."""

from __future__ import annotations

import copy
import json
import re
import uuid
from typing import Any

from tv_app.application.services.data.presentation_command_recognition_service import (
    PresentationCommandRecognitionService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
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


class PresentationSuggestOpsService:
    @classmethod
    def suggest(cls, *, message: str, host_context: dict | None) -> dict[str, Any]:
        """Fachada pública: sempre devolve um plano validado pelo contrato."""
        from tv_app.application.services.data.presentation_command_planner_service import (
            PresentationCommandPlannerService,
        )

        plan = PresentationCommandPlannerService.plan(
            message=message,
            host_context=host_context,
        )
        return PresentationCommandPlannerService.to_suggest_payload(plan)

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
        catalog_version = PresentationOpsContentService.catalog_version()
        normalized = cls._normalize(message)
        if not normalized:
            return {
                "catalogVersion": catalog_version,
                "ops": [],
                "matchedCapabilityKeys": [],
                "reason": PresentationOpsContentService.message("suggestEmptyMessage"),
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
        max_ops = PresentationOpsContentService.setting_int("maxSuggestOps", 5)
        destructive_intent = cls._has_destructive_intent(normalized)

        from tv_app.application.services.data.compound_goal_planner import (
            plan_compound_goals,
        )

        compound = plan_compound_goals(message)
        if compound:
            return {
                "catalogVersion": catalog_version,
                "ops": compound["ops"],
                "matchedCapabilityKeys": compound["matchedCapabilityKeys"],
                "clarificationKey": None,
                "candidates": [],
                "interpretedGoals": compound["interpretedGoals"],
                "ignoredGoals": compound["ignoredGoals"],
                "warnings": compound["warnings"],
                "reason": PresentationOpsContentService.message(
                    "suggestOk", count=len(compound["ops"])
                ),
            }

        from tv_app.application.services.data.safe_auto_fix_service import (
            SafeAutoFixService,
        )

        if (
            SafeAutoFixService.is_layout_review(message)
            and not SafeAutoFixService.asks_new_content(normalized)
        ):
            native = host.get("nativeConfig") if isinstance(host.get("nativeConfig"), dict) else None
            fix_ops = SafeAutoFixService.ops_for(native)
            if fix_ops:
                return {
                    "catalogVersion": catalog_version,
                    "ops": fix_ops,
                    "matchedCapabilityKeys": ["safe_auto_fix"],
                    "clarificationKey": None,
                    "candidates": [],
                    "warnings": [
                        "safe auto-fix changes geometry or chrome only; metric and narrative stay"
                    ],
                    "reason": PresentationOpsContentService.message(
                        "suggestOk", count=len(fix_ops)
                    ),
                }

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
                    "reason": PresentationOpsContentService.message(
                        "suggestOk", count=len(ops)
                    ),
                }

        # Recipes tipadas (tema/layout TV) — owner PresentationRecipeService.
        recipe_ops = cls._ops_from_presentation_recipe(message)
        if recipe_ops:
            return {
                "catalogVersion": catalog_version,
                "ops": recipe_ops,
                "matchedCapabilityKeys": ["presentation_recipe"],
                "clarificationKey": None,
                "candidates": [],
                "reason": PresentationOpsContentService.message(
                    "suggestOk", count=len(recipe_ops)
                ),
            }

        scored: list[tuple[float, dict[str, Any]]] = []
        for cap in PresentationOpsContentService.capabilities():
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
            reason = PresentationOpsContentService.message(
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
                    or PresentationOpsContentService.placeholder_clarifications().get(
                        "operationId"
                    )
                )
                continue

            templates = cls._templates_for_capability(cap)
            for template in templates:
                filled = cls._fill_template(template, placeholders)
                if not isinstance(filled, dict) or not filled:
                    continue
                filled = cls._enrich_filled_op(
                    filled, placeholders, normalized=normalized
                )
                incomplete_field = cls._incomplete_op_field(filled)
                if incomplete_field:
                    mapped = PresentationOpsContentService.op_field_clarifications().get(
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

        # Absoluto vence relativo: «de 48 para 56» / «para 56» materializam o
        # patch exato — manter o bump seria uma segunda mutação aproximada
        # no mesmo alvo.
        if str(placeholders.get("fontSizeAbsolute") or "").strip():
            ops = [op for op in ops if op.get("op") != "bump_font_size"]

        # Anti-ghost: com um ALTER_EXISTING já ancorado no alvo selecionado,
        # um upsert de criação (id gerado + createIfMissing, sem blockId) só
        # pode nascer de colisão de marcador — nunca de intenção declarada.
        if any(
            op.get("op") == "upsert_block"
            and str(op.get("blockId") or "").strip()
            for op in ops
        ):
            ops = [
                op
                for op in ops
                if not (
                    op.get("op") == "upsert_block"
                    and op.get("createIfMissing") is True
                    and not str(op.get("blockId") or "").strip()
                )
            ]

        if not ops:
            if clarification_keys:
                reason = PresentationOpsContentService.message(clarification_keys[0])
            elif matched_keys:
                reason = PresentationOpsContentService.message("suggestIncompleteGeneric")
            else:
                reason = PresentationOpsContentService.message("suggestNoMatch")
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
            "reason": PresentationOpsContentService.message(
                "suggestOk", count=len(ops)
            ),
        }

    @classmethod
    def _clarification_for_placeholders(cls, missing: list[str]) -> str | None:
        mapping = PresentationOpsContentService.placeholder_clarifications()
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
    def _unquoted_text(cls, normalized: str) -> str:
        """Texto normalizado sem literais entre aspas (payload ≠ intenção)."""
        stripped = _QUOTED_RE.sub(" ", str(normalized or ""))
        return " ".join(stripped.split())

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
    def _quoted_values(cls, message: str) -> list[str]:
        values: list[str] = []
        for match in _QUOTED_RE.finditer(str(message or "")):
            for group in match.groups():
                if group is not None and str(group).strip():
                    values.append(str(group).strip())
                    break
        return values

    @classmethod
    def _extract_source_label(cls, message: str) -> str:
        """New visible label for rename: last quoted, or text after «para»."""
        values = cls._quoted_values(message)
        if len(values) >= 2:
            return values[-1]
        if len(values) == 1:
            # Single quote is the new name when message has «para "X"» or «chame … "X"».
            lower = str(message or "").lower()
            if "para" in lower or "chame" in lower or "nome" in lower:
                return values[0]
        raw = str(message or "")
        match = re.search(
            r"\bpara\s+(.+?)(?:\s*,\s*preserv|\s*\.\s*$|\s*$)",
            raw,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            candidate = str(match.group(1) or "").strip().strip("\"'«»")
            # Drop trailing clause fragments.
            candidate = re.split(r"\s*,\s*preserv", candidate, maxsplit=1)[0].strip()
            if candidate:
                return candidate
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
    def _selected_block_type(cls, host: dict[str, Any]) -> str:
        """Tipo real do bloco selecionado — só de grounding do host
        (selectedBlockTypes alinhado a selectedBlockIds, ou focusBlockType
        do focusBlockId). Nunca inferir do substantivo: um type errado
        sobrescreveria o tipo do bloco no merge."""
        block_id = cls._first_selected_block_id(host)
        if not block_id:
            return ""
        raw_ids = host.get("selectedBlockIds")
        raw_types = host.get("selectedBlockTypes")
        if isinstance(raw_ids, list) and isinstance(raw_types, list):
            for index, item in enumerate(raw_ids):
                if str(item or "").strip() == block_id and index < len(raw_types):
                    value = str(raw_types[index] or "").strip()
                    if value:
                        return value
        if str(host.get("focusBlockId") or "").strip() == block_id:
            return str(host.get("focusBlockType") or "").strip()
        return ""

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

        vocab = PresentationOpsContentService.color_vocabulary()
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
        message: str = "",
    ) -> str:
        selected = str(
            host.get("selectedDataSourceId") or host.get("dataSourceId") or ""
        ).strip()
        if selected:
            return selected

        sources = cls._host_data_sources(host)
        if not sources:
            return ""

        # Prefer matching an existing source label cited in the message (rename/deixis).
        quoted_values = cls._quoted_values(message)
        for needle in (v.lower() for v in quoted_values if v):
            for item in sources:
                if str(item.get("label") or "").strip().lower() == needle:
                    return str(item.get("id") or "").strip()

        if normalized:
            for item in sorted(sources, key=lambda row: -len(str(row.get("label") or ""))):
                label = str(item.get("label") or "").strip().lower()
                if label and label in normalized:
                    return str(item.get("id") or "").strip()

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
    def _host_data_models(cls, host: dict[str, Any]) -> list[dict[str, Any]]:
        """Modelos endereçáveis do host context (compact get_playlist_context
        ou payload rico de inspect_data_model repassado pelo caller)."""
        raw = host.get("dataModels")
        out: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                mid = str(item.get("id") or "").strip()
                if not mid:
                    continue
                # Compact rows (só inputCount) não trazem inputs; o caller pode
                # repassar a resposta de inspect_data_model (definition.inputs).
                inputs = item.get("inputs")
                if not isinstance(inputs, list):
                    definition = item.get("definition")
                    if isinstance(definition, dict):
                        inputs = definition.get("inputs")
                if not isinstance(inputs, list):
                    inputs = []
                out.append(
                    {
                        "id": mid,
                        "label": str(item.get("label") or "").strip(),
                        "inputs": inputs,
                    }
                )
        return out

    @classmethod
    def _resolve_model_id(
        cls,
        *,
        host: dict[str, Any],
        normalized: str,
        message: str,
    ) -> str:
        """modelId só de evidência persistida — nunca inferido de labels de
        bloco/campo. Ordem: seleção explícita → focusedBinding → focusedModel
        → label citada → único modelo do slide."""
        for key in ("modelId", "selectedDataModelId", "selectedModelId"):
            selected = str(host.get(key) or "").strip()
            if selected:
                return selected
        focused_binding = host.get("focusedBinding")
        if isinstance(focused_binding, dict):
            bound = str(focused_binding.get("modelId") or "").strip()
            if bound:
                return bound
        focused_model = host.get("focusedModel")
        if isinstance(focused_model, dict):
            bound = str(
                focused_model.get("id") or focused_model.get("modelId") or ""
            ).strip()
            if bound:
                return bound

        models = cls._host_data_models(host)
        if not models:
            block_index = host.get("blockIndex")
            ids: list[str] = []
            if isinstance(block_index, list):
                for item in block_index:
                    if not isinstance(item, dict):
                        continue
                    mid = str(item.get("modelId") or "").strip()
                    if mid and mid not in ids:
                        ids.append(mid)
            return ids[0] if len(ids) == 1 else ""

        for needle in (v.lower() for v in cls._quoted_values(message) if v):
            for item in models:
                if item["label"].lower() == needle:
                    return item["id"]
        if normalized:
            for item in sorted(models, key=lambda row: -len(row["label"])):
                if item["label"] and item["label"].lower() in normalized:
                    return item["id"]
        return models[0]["id"] if len(models) == 1 else ""

    @classmethod
    def _resolve_model_input_id(
        cls,
        *,
        host: dict[str, Any],
        model_id: str,
        normalized: str,
    ) -> str:
        """inputId só quando o host traz inputs (contexto rico ou inspect
        repassado). Compact rows (só inputCount) não resolvem — fail closed."""
        for key in ("inputId", "selectedModelInputId"):
            selected = str(host.get(key) or "").strip()
            if selected:
                return selected
        candidates: list[dict[str, Any]] = []
        focused_model = host.get("focusedModel")
        if isinstance(focused_model, dict):
            fid = str(
                focused_model.get("id") or focused_model.get("modelId") or ""
            ).strip()
            if fid and fid != model_id:
                focused_model = None
        containers = []
        if isinstance(focused_model, dict):
            containers.append(focused_model)
        containers.extend(cls._host_data_models(host))
        for container in containers:
            cid = str(container.get("id") or "").strip()
            if model_id and cid and cid != model_id:
                continue
            inputs = container.get("inputs")
            if not isinstance(inputs, list):
                continue
            candidates.extend(i for i in inputs if isinstance(i, dict))
        if not candidates:
            return ""
        for item in sorted(
            candidates,
            key=lambda row: -len(str(row.get("label") or row.get("queryName") or "")),
        ):
            iid = str(item.get("id") or "").strip()
            label = str(item.get("label") or "").strip().lower()
            query_name = str(item.get("queryName") or "").strip().lower()
            if iid and iid.lower() in normalized:
                return iid
            if label and label in normalized:
                return iid
            if query_name and query_name in normalized:
                return iid
        return candidates[0].get("id", "") if len(candidates) == 1 else ""

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
        hints = PresentationOpsContentService.param_hints()
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
        for hint in PresentationOpsContentService.transform_step_hints():
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
                    # Merge hints need live sourceId/keys from JoinPlan — skip placeholders.
                    serialized = json.dumps(step, ensure_ascii=False)
                    if "{{" in serialized:
                        break
                    steps.append(copy.deepcopy(step))
                    break
        return steps

    @classmethod
    def _extract_format_hint(cls, message: str) -> dict[str, Any] | None:
        from tv_app.application.services.data.display_format_hints_service import (
            DisplayFormatHintsService,
        )

        hint = DisplayFormatHintsService.from_nl(message)
        return hint.to_dict() if hint else None

    @classmethod
    def _ops_from_presentation_recipe(cls, message: str) -> list[dict[str, Any]]:
        from tv_app.application.services.data.presentation_recipe_service import (
            PresentationRecipeService,
        )

        resolved = PresentationRecipeService.resolve_from_nl(message)
        if resolved is None:
            return []
        ops = PresentationRecipeService.ops_for_recipe(resolved.recipe_id)
        ready: list[dict[str, Any]] = []
        for op in ops:
            if cls._incomplete_op_field(op):
                continue
            ready.append(op)
        return ready

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
        limit = PresentationOpsContentService.setting_int("routeCandidateLimit", 5)
        min_score = PresentationOpsContentService.setting_float("routeCandidateMinScore", 4.0)
        gap_threshold = PresentationOpsContentService.setting_float(
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
        hints = PresentationOpsContentService.nl_route_hints()
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

            service = TvDataRouteSuggestService(TvDataRouteCatalogService())
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
        cap = limit or PresentationOpsContentService.setting_int("routeCandidateLimit", 5)
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
        default_title = PresentationOpsContentService.setting_str(
            "defaultSlideTitle", "Slide personalizado"
        )
        default_playlist = PresentationOpsContentService.setting_str(
            "defaultPlaylistName", "Nova programação"
        )
        default_section = PresentationOpsContentService.setting_str(
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
        default_text = PresentationOpsContentService.setting_str(
            "defaultTextBlockContent", ""
        )
        text_content = quoted if quoted else default_text
        data_source_id = cls._resolve_data_source_id(
            host=host,
            normalized=normalized,
            operation_id=operation_id,
            message=message,
        )
        model_id = cls._resolve_model_id(
            host=host,
            normalized=normalized,
            message=message,
        )
        model_input_id = cls._resolve_model_input_id(
            host=host,
            model_id=model_id,
            normalized=normalized,
        )
        selected_visual_id = cls._resolve_selected_visual_id(host)
        params = cls._extract_params(normalized)
        explicit_params = dict(params)
        host_defaults = host.get("playlistDefaults") if isinstance(host.get("playlistDefaults"), dict) else {}
        if "branch" not in params and host_defaults.get("branch") not in (None, ""):
            params["branch"] = host_defaults.get("branch")
        # Default tipado para rotas date_range fechadas — só para criação de
        # fonte/modelo; patch de modelo existente usa explicitParamsJson.
        if "dateRangePreset" not in params and "periodDays" not in params:
            # Só antecipa se o pedido não trouxe datas explícitas.
            if not any(k in params for k in ("start_date", "end_date", "startDate", "endDate")):
                params["dateRangePreset"] = "this_month"
        transform_steps = cls._extract_transform_steps(normalized)
        field_labels = cls._extract_field_labels(message, quoted)
        format_hint = cls._extract_format_hint(message)
        return {
            "quoted": quoted,
            "sourceLabel": cls._extract_source_label(message),
            "textContent": text_content,
            "selectedBlockId": cls._first_selected_block_id(host),
            "selectedBlockType": cls._selected_block_type(host),
            "selectedVisualId": selected_visual_id,
            "slideId": str(host.get("slideId") or "").strip(),
            "playlistId": str(host.get("playlistId") or "").strip(),
            "sectionId": str(host.get("sectionId") or "").strip(),
            "dataSourceId": data_source_id,
            "modelId": model_id,
            "inputId": model_input_id,
            "operationId": operation_id,
            "routeLabel": route_label,
            "presetKey": str(host.get("presetKey") or "").strip(),
            "backgroundColor": background_color,
            "paramsJson": json.dumps(params, ensure_ascii=False) if params else "",
            "explicitParamsJson": (
                json.dumps(explicit_params, ensure_ascii=False)
                if explicit_params
                else ""
            ),
            "transformStepsJson": (
                json.dumps(transform_steps, ensure_ascii=False) if transform_steps else ""
            ),
            "fieldLabelsJson": (
                json.dumps(field_labels, ensure_ascii=False) if field_labels else ""
            ),
            "formatHintJson": (
                json.dumps(format_hint, ensure_ascii=False) if format_hint else ""
            ),
            "branchParam": str(params.get("branch", "")) if "branch" in params else "",
            "selectedBlockIdsJson": cls._selected_block_ids_json(host),
            "alignCommand": cls._extract_align_command(normalized),
            "zOrderCommand": cls._extract_z_order_command(normalized),
            "textCaseMode": cls._extract_text_case_mode(normalized),
            "fontSizeDelta": cls._extract_font_size_delta(normalized),
            "fontSizeAbsolute": cls._extract_font_size_absolute(normalized),
            "fontColor": cls._extract_font_color(message, normalized),
            "blockType": cls._extract_block_type(normalized),
            "newDataSourceId": cls._new_id("ds"),
            "newModelId": cls._new_id("mdl"),
            "newVisualId": cls._new_id("viz"),
            "newTextBlockId": cls._new_id("txt"),
            "title": quoted or default_title,
            "name": quoted or default_playlist,
            "sectionName": quoted or default_section,
        }

    @classmethod
    def _selected_block_ids_json(cls, host: dict[str, Any]) -> str:
        raw = host.get("selectedBlockIds")
        ids: list[str] = []
        if isinstance(raw, list):
            ids = [str(item).strip() for item in raw if str(item or "").strip()]
        if not ids:
            single = cls._first_selected_block_id(host)
            if single:
                ids = [single]
        return json.dumps(ids, ensure_ascii=False) if ids else ""

    @classmethod
    def _extract_align_command(cls, normalized: str) -> str:
        mapping = (
            (("distribuir horizontal", "distribua horizontal", "distribuir na horizontal"), "distribute-h"),
            (("distribuir vertical", "distribua vertical", "distribuir na vertical"), "distribute-v"),
            (("centro vertical", "alinhar ao centro vertical"), "align-center-v"),
            (("alinhar à esquerda", "alinhar a esquerda", "alinhe à esquerda", "alinhe a esquerda", "alinhados à esquerda"), "align-left"),
            (("alinhar à direita", "alinhar a direita", "alinhe à direita", "alinhe a direita", "alinhados à direita"), "align-right"),
            (("alinhar no topo", "alinhar ao topo", "alinhe no topo", "alinhe ao topo"), "align-top"),
            (("alinhar na base", "alinhar embaixo", "alinhe na base", "alinhe embaixo", "alinhar abaixo"), "align-bottom"),
            (("centralizar", "centro horizontal", "alinhar ao centro", "alinhe ao centro"), "align-center-h"),
        )
        for markers, command in mapping:
            if any(cls._marker_hit(marker, normalized) for marker in markers):
                return command
        return ""

    @classmethod
    def _extract_z_order_command(cls, normalized: str) -> str:
        mapping = (
            (("trazer para frente", "traga para frente", "primeiro plano", "para a frente de tudo", "frente de tudo"), "bring-to-front"),
            (("enviar para trás", "enviar ao fundo", "envie para trás", "envie ao fundo", "para o fundo", "atrás de tudo", "atras de tudo"), "send-to-back"),
            (("avançar uma camada", "avance uma camada", "subir uma camada", "suba uma camada", "trazer um nível", "para frente"), "bring-forward"),
            (("recuar uma camada", "recue uma camada", "descer uma camada", "desça uma camada", "enviar um nível", "para trás", "para tras"), "send-backward"),
        )
        for markers, command in mapping:
            if any(cls._marker_hit(marker, normalized) for marker in markers):
                return command
        return ""

    @classmethod
    def _extract_text_case_mode(cls, normalized: str) -> str:
        mapping = (
            (("title case", "cada palavra", "primeira letra de cada palavra", "capitalizar"), "title"),
            (("maiúsculas", "maiusculas", "caixa alta", "em caps", "tudo maiúsculo", "tudo maiusculo", "all caps"), "upper"),
            (("minúsculas", "minusculas", "caixa baixa", "tudo minúsculo", "tudo minusculo"), "lower"),
            (("alternar caixa", "inverter caixa", "toggle"), "toggle"),
            (("sentence case", "primeira letra", "somente a primeira"), "sentence"),
        )
        for markers, mode in mapping:
            if any(cls._marker_hit(marker, normalized) for marker in markers):
                return mode
        return ""

    @classmethod
    def _extract_font_size_delta(cls, normalized: str) -> str:
        increase = (
            "aumentar fonte", "aumente a fonte", "aumentar a fonte",
            "aumenta a fonte", "fonte maior", "letra maior",
            "aumentar o tamanho do texto", "aumente o tamanho",
            "aumentar o tamanho", "aumentar texto", "aumente o texto",
            "aumente a letra", "tamanho maior", "maior",
            "deixe a fonte", "deixar a fonte", "deixe a letra",
            "deixe o texto", "deixe o tamanho", "deixar o tamanho",
        )
        decrease = (
            "diminuir fonte", "diminua a fonte", "diminuir a fonte",
            "diminua o texto", "diminuir o texto", "fonte menor",
            "letra menor", "reduzir fonte", "reduza a fonte",
            "reduzir a fonte", "diminuir o tamanho", "diminua o tamanho",
            "tamanho menor", "menor",
        )
        # Direção primeiro: «deixe a fonte ... menor» não pode virar aumento
        # só porque «deixe a fonte» é marcador de aumento.
        if any(cls._marker_hit(marker, normalized) for marker in decrease):
            return "-1"
        if any(cls._marker_hit(marker, normalized) for marker in increase):
            return "1"
        return ""

    @classmethod
    def _extract_font_size_absolute(cls, normalized: str) -> str:
        """Tamanho absoluto de fonte («de 48 para 56», «para 56», «fonte 56»).

        Só com contexto tipográfico — «mude a filial para 02» não é fonte.
        Valores fora de 8–400 não são tamanho de fonte plausível.
        """
        if not any(
            cls._marker_hit(marker, normalized)
            for marker in ("fonte", "font", "tamanho", "letra")
        ):
            return ""
        patterns = (
            r"\bde\s+[\"'«»“”]?\s*\d{1,3}\s*(?:px|pt)?\s*[\"'«»“”]?\s+para\s+[\"'«»“”]?\s*(\d{1,3})\s*(?:px|pt)?\b",
            r"\bpara\s+[\"'«»“”]?\s*(\d{1,3})\s*(?:px|pt)?\b",
            r"\b(?:fonte|tamanho|letra)\s+(?:de\s+)?[\"'«»“”]?\s*(\d{1,3})\s*(?:px|pt)?\b",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if not match:
                continue
            try:
                value = int(match.group(match.lastindex or 1))
            except (TypeError, ValueError):
                continue
            if 8 <= value <= 400:
                return str(value)
        return ""

    @classmethod
    def _extract_font_color(cls, message: str, normalized: str) -> str:
        """Cor tipográfica do bloco — nunca o fundo do slide (patch_native_config).

        Exige referência explícita a um bloco («cor do título», «cor do bloco
        selecionado»); «mude a cor para azul» sem alvo segue no slide.
        """
        if any(
            cls._marker_hit(marker, normalized)
            for marker in (
                "fundo", "background", "do slide", "da tela",
                "da seção", "da secao", "da programação", "da playlist",
            )
        ):
            return ""
        if not (
            cls._marker_hit("cor", normalized)
            or cls._marker_hit("color", normalized)
        ):
            return ""
        if not any(
            cls._marker_hit(marker, normalized)
            for marker in (
                "do título", "do titulo", "do texto", "da fonte",
                "da letra", "do bloco", "do elemento", "da caixa",
                "do kpi", "selecionado", "selecionada",
            )
        ):
            return ""
        return cls._extract_background_color(message, normalized)

    @classmethod
    def _message_asks_block_text(cls, normalized: str) -> bool:
        """Pedido referencia o texto/conteúdo do bloco (não cor, tamanho ou geometria)."""
        return any(
            cls._marker_hit(marker, normalized)
            for marker in (
                "texto", "título", "titulo", "conteúdo", "conteudo",
                "escreva", "escrever", "diga", "frase", "mensagem",
                "o nome", "o rótulo", "o rotulo",
            )
        )

    @classmethod
    def _extract_block_type(cls, normalized: str) -> str:
        mapping = (
            (("bloco de texto", "caixa de texto", "bloco texto"), "text"),
            (("título", "titulo", "heading"), "heading"),
            (("forma", "retângulo", "retangulo", "círculo", "circulo", "shape"), "shape"),
            (("ícone", "icone", "icon"), "icon"),
            (("imagem", "foto", "image"), "image"),
        )
        for markers, block_type in mapping:
            if any(cls._marker_hit(marker, normalized) for marker in markers):
                return block_type
        return ""

    @classmethod
    def _enrich_filled_op(
        cls,
        op: dict[str, Any],
        placeholders: dict[str, str],
        *,
        normalized: str = "",
    ) -> dict[str, Any]:
        name = str(op.get("op") or "").strip()
        if name == "patch_data_model":
            model_patch: dict[str, Any] = {}
            input_patches: list[dict[str, Any]] = []
            input_id = str(placeholders.get("inputId") or "").strip()
            input_targeted = "input" in normalized or "consulta" in normalized

            quoted = str(placeholders.get("quoted") or "").strip()
            if quoted and (
                cls._marker_hit("renome", normalized)
                or cls._marker_hit("nome do modelo", normalized)
            ):
                model_patch["label"] = quoted

            labels_raw = str(placeholders.get("fieldLabelsJson") or "").strip()
            if labels_raw:
                try:
                    labels = json.loads(labels_raw)
                except json.JSONDecodeError:
                    labels = None
                if isinstance(labels, dict) and labels:
                    model_patch["fieldLabels"] = {
                        str(k): str(v)
                        for k, v in labels.items()
                        if str(k).strip()
                    }

            steps_raw = str(placeholders.get("transformStepsJson") or "").strip()
            steps: list[Any] | None = None
            if steps_raw:
                try:
                    parsed_steps = json.loads(steps_raw)
                except json.JSONDecodeError:
                    parsed_steps = None
                if isinstance(parsed_steps, list) and parsed_steps:
                    steps = parsed_steps
            params_raw = str(placeholders.get("explicitParamsJson") or "").strip()
            params: dict[str, Any] | None = None
            if params_raw:
                try:
                    parsed_params = json.loads(params_raw)
                except json.JSONDecodeError:
                    parsed_params = None
                if isinstance(parsed_params, dict) and parsed_params:
                    params = parsed_params

            input_patch: dict[str, Any] = {}
            if params:
                input_patch["params"] = {"set": params}
            if steps and input_targeted:
                input_patch["transform"] = {"version": 1, "steps": steps}
            if input_patch:
                # Sem inputId resolvido a op fica incompleta → clarificação
                # (fail closed); nunca mirar input por chute.
                input_patch["inputId"] = input_id
                input_patches.append(input_patch)
            elif input_targeted and (params is not None or steps is not None):
                input_patches.append({"inputId": input_id})

            if steps and not input_targeted:
                model_patch["transform"] = {"version": 1, "steps": steps}

            if model_patch:
                op["modelPatch"] = model_patch
            else:
                op.pop("modelPatch", None)
            if input_patches:
                op["inputPatches"] = input_patches
            else:
                op.pop("inputPatches", None)
            return op

        if name == "upsert_data_source":
            # Label-only rename must not inject default params (would force full upsert).
            label_only = bool(str(op.get("label") or "").strip()) and not str(
                op.get("operationId") or ""
            ).strip()
            if label_only:
                op.pop("params", None)
                op.pop("displayMode", None)
                op.pop("dataTransform", None)
                return op
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
        elif name == "create_block":
            # Conteúdo citado explícito → campo content do contrato create_block;
            # sem conteúdo informado o campo é omitido (nunca "" injetado).
            text_content = str(placeholders.get("textContent") or "").strip()
            if text_content:
                op["content"] = text_content
        elif name == "upsert_block":
            if str(op.get("blockId") or "").strip():
                # blockId na raiz = template ALTER_EXISTING (update_block):
                # delta mínimo sobre o bloco existente; o merge canônico do
                # write layer preserva id/type/content/frame/bindings.
                return cls._enrich_alter_existing_block_op(
                    op, placeholders, normalized=normalized
                )
            block = op.get("block") if isinstance(op.get("block"), dict) else None
            if isinstance(block, dict):
                block_type = str(placeholders.get("blockType") or "").strip()
                if block_type and str(block.get("type") or "").strip() == "text":
                    # «crie um novo título» nasce heading, não text.
                    block["type"] = block_type
            format_raw = str(placeholders.get("formatHintJson") or "").strip()
            if format_raw:
                try:
                    format_hint = json.loads(format_raw)
                except json.JSONDecodeError:
                    format_hint = None
                if isinstance(format_hint, dict) and format_hint:
                    from tv_app.application.services.data.display_format_hints_service import (
                        DisplayFormatHintsService,
                    )

                    hint = DisplayFormatHintsService._from_payload(
                        format_hint, source="suggest"
                    )
                    block = op.get("block") if isinstance(op.get("block"), dict) else None
                    if hint and block is not None:
                        block_type = str(block.get("type") or "")
                        if block_type in {"kpi_view", "data_kpi"}:
                            opts = (
                                dict(block["kpiOptions"])
                                if isinstance(block.get("kpiOptions"), dict)
                                else {}
                            )
                            opts.update(hint.kpi_options_patch())
                            block["kpiOptions"] = opts
                            proj = (
                                dict(block["kpiProjection"])
                                if isinstance(block.get("kpiProjection"), dict)
                                else {}
                            )
                            metrics = list(proj.get("metrics") or [])
                            if metrics and isinstance(metrics[0], dict):
                                metrics[0] = {
                                    **metrics[0],
                                    "format": hint.value_format,
                                    "displayFormat": hint.display_format_spec(),
                                }
                                proj["metrics"] = metrics
                            elif not metrics:
                                proj["metrics"] = [
                                    {
                                        "format": hint.value_format,
                                        "displayFormat": hint.display_format_spec(),
                                    }
                                ]
                            block["kpiProjection"] = proj
                        elif block_type in {"chart_view", "data_chart"}:
                            opts = (
                                dict(block["chartOptions"])
                                if isinstance(block.get("chartOptions"), dict)
                                else {}
                            )
                            opts["valueFormat"] = hint.value_format
                            block["chartOptions"] = opts
                            if not isinstance(block.get("chartProjection"), dict):
                                block["chartProjection"] = {}
                        elif block_type in {"table_view", "data_table"}:
                            if not isinstance(block.get("tableProjection"), dict):
                                block["tableProjection"] = {"columns": []}
                            opts = (
                                dict(block["tableOptions"])
                                if isinstance(block.get("tableOptions"), dict)
                                else {}
                            )
                            opts["valueFormat"] = hint.value_format
                            block["tableOptions"] = opts
                        op["block"] = block
        elif name in {"align_blocks", "reorder_block_z", "duplicate_blocks"}:
            ids = op.get("blockIds")
            if not isinstance(ids, list) or not [i for i in ids if str(i or "").strip()]:
                raw = str(placeholders.get("selectedBlockIdsJson") or "").strip()
                if raw:
                    try:
                        parsed = json.loads(raw)
                    except json.JSONDecodeError:
                        parsed = None
                    if isinstance(parsed, list) and parsed:
                        op["blockIds"] = [
                            str(item).strip()
                            for item in parsed
                            if str(item or "").strip()
                        ]
        elif name == "bump_font_size":
            try:
                op["deltaSteps"] = int(op.get("deltaSteps"))
            except (TypeError, ValueError):
                raw = str(placeholders.get("fontSizeDelta") or "").strip()
                if raw:
                    try:
                        op["deltaSteps"] = int(raw)
                    except ValueError:
                        pass
        elif name == "set_display_format":
            fmt = op.get("displayFormat")
            if not (isinstance(fmt, dict) and str(fmt.get("category") or "").strip()):
                hint_raw = str(placeholders.get("formatHintJson") or "").strip()
                if hint_raw:
                    try:
                        hint_payload = json.loads(hint_raw)
                    except json.JSONDecodeError:
                        hint_payload = None
                    if isinstance(hint_payload, dict):
                        from tv_app.application.services.data.display_format_hints_service import (
                            DisplayFormatHintsService,
                        )

                        hint = DisplayFormatHintsService._from_payload(
                            hint_payload, source="suggest"
                        )
                        if hint:
                            op["displayFormat"] = hint.display_format_spec()
        return op

    @classmethod
    def _enrich_alter_existing_block_op(
        cls,
        op: dict[str, Any],
        placeholders: dict[str, str],
        *,
        normalized: str = "",
    ) -> dict[str, Any]:
        """Monta o delta mínimo do ALTER_EXISTING (upsert_block com blockId).

        Só as propriedades pedidas entram no patch — id/type/content/frame/
        bindings e demais style sobrevivem pelo merge canônico do write layer.
        Sem delta suportado o bloco fica vazio → clarificação (fail closed);
        nunca mintar id novo nem createIfMissing.
        """
        target_id = str(op.get("blockId") or "").strip()
        block = op.get("block") if isinstance(op.get("block"), dict) else {}
        if target_id and str(block.get("id") or "").strip() != target_id:
            block["id"] = target_id

        delta: dict[str, Any] = {}
        block_id = str(block.get("id") or target_id).strip()
        if block_id:
            delta["id"] = block_id
        # inputSchema exige block.type; só entra quando o host o grounda —
        # merge reafirma o mesmo valor, nunca troca o tipo.
        block_type = str(placeholders.get("selectedBlockType") or "").strip()
        if block_type:
            delta["type"] = block_type

        style: dict[str, Any] = {}
        size_raw = str(placeholders.get("fontSizeAbsolute") or "").strip()
        if size_raw:
            try:
                style["fontSize"] = int(size_raw)
            except ValueError:
                pass
        font_color = str(placeholders.get("fontColor") or "").strip()
        if font_color:
            style["color"] = font_color
        if style:
            delta["style"] = style

        text_content = str(placeholders.get("textContent") or "").strip()
        if (
            text_content
            and not style
            and cls._message_asks_block_text(normalized)
        ):
            delta["content"] = text_content

        # «id»/«type» sozinhos não são alteração: a capability tipada correta
        # já teria emitido a própria op — aqui só resta clarificar (fail
        # closed), nunca criar bloco novo.
        has_change = bool(style) or "content" in delta
        op["block"] = delta if has_change else {}
        return op

    @classmethod
    def _action_terms_for_capability(cls, cap: dict[str, Any]) -> list[str]:
        raw_terms = cap.get("actionTerms")
        if isinstance(raw_terms, list) and raw_terms:
            terms = [str(item).strip().lower() for item in raw_terms if str(item).strip()]
        else:
            terms = PresentationOpsContentService.action_terms_for_set(
                str(cap.get("actionTermSet") or "any")
            )
        if cls._is_destructive_capability(cap):
            return terms
        # Verbo de remoção não reforça capability construtiva («apague» ≠ criar texto).
        destructive = set(PresentationOpsContentService.destructive_action_terms())
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
        for term in PresentationOpsContentService.destructive_action_terms():
            if cls._marker_hit(term, normalized):
                return True
        return False

    @classmethod
    def _marker_hit(cls, needle: str, haystack: str) -> bool:
        return PresentationCommandRecognitionService.marker_hit(needle, haystack)

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
            # Literais entre aspas são payload, não intenção: «adicione um
            # texto 'teste atualizado'» não pode ativar a exclusão de edição.
            unquoted = cls._unquoted_text(normalized)
            for marker in exclude:
                if cls._marker_hit(str(marker), unquoted):
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
                bg_type = str(background.get("type") or "").strip()
                if not bg_type:
                    return "patch_native_config.background"
                if bg_type == "gradient":
                    if not (
                        str(background.get("from") or "").strip()
                        and str(background.get("to") or "").strip()
                    ):
                        return "patch_native_config.background"
                elif not str(background.get("value") or "").strip():
                    return "patch_native_config.background"
            return None
        if name == "upsert_data_source":
            has_label = bool(str(op.get("label") or "").strip())
            has_op = bool(str(op.get("operationId") or "").strip())
            has_block = bool(str(op.get("blockId") or "").strip())
            # Label-only metadata patch on an existing source (no operationId required).
            if has_label and has_block and not has_op:
                return None
            if not has_op:
                return "upsert_data_source.operationId"
            if not has_block:
                return "upsert_data_source.blockId"
            return None
        if name == "set_data_transform":
            if not str(op.get("blockId") or "").strip():
                return "set_data_transform.blockId"
            steps = op.get("steps")
            if not isinstance(steps, list) or not steps:
                return "set_data_transform.steps"
            return None
        if name == "patch_data_model":
            if not str(op.get("modelId") or "").strip():
                return "patch_data_model.modelId"
            input_patches = op.get("inputPatches")
            if isinstance(input_patches, list):
                for item in input_patches:
                    if not isinstance(item, dict):
                        return "patch_data_model.inputId"
                    if not str(item.get("inputId") or "").strip():
                        return "patch_data_model.inputId"
            has_input_patch = isinstance(input_patches, list) and any(
                isinstance(item, dict)
                and (item.get("params") or "transform" in item)
                for item in input_patches
            )
            model_patch = op.get("modelPatch")
            has_model_patch = isinstance(model_patch, dict) and any(
                key in model_patch
                for key in ("label", "transform", "fieldLabels")
            )
            if not has_input_patch and not has_model_patch:
                return "patch_data_model.patch"
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
        if name in {"align_blocks", "reorder_block_z", "duplicate_blocks"}:
            ids = op.get("blockIds")
            if not isinstance(ids, list) or not [
                item for item in ids if str(item or "").strip()
            ]:
                return f"{name}.blockIds"
            if name != "duplicate_blocks" and not str(op.get("command") or "").strip():
                return f"{name}.command"
            return None
        if name == "bump_font_size":
            if not str(op.get("blockId") or "").strip():
                return "bump_font_size.blockId"
            try:
                int(op.get("deltaSteps"))
            except (TypeError, ValueError):
                return "bump_font_size.deltaSteps"
            return None
        if name == "transform_text_case":
            if not str(op.get("blockId") or "").strip():
                return "transform_text_case.blockId"
            if not str(op.get("mode") or "").strip():
                return "transform_text_case.mode"
            return None
        if name == "create_block":
            if not str(op.get("type") or "").strip():
                return "create_block.type"
            return None
        if name == "set_display_format":
            if not str(op.get("blockId") or "").strip():
                return "set_display_format.blockId"
            target = op.get("target")
            if not isinstance(target, dict) or not (
                str(target.get("owner") or "").strip()
                and str(target.get("field") or "").strip()
            ):
                return "set_display_format.target"
            fmt = op.get("displayFormat")
            if not isinstance(fmt, dict) or not str(fmt.get("category") or "").strip():
                return "set_display_format.displayFormat"
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
