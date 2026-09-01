"""Respostas grounded de follow-up: challenge, clarify_slot, ack e comparação de período."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_follow_up_turn_content_service import (
    ChatFollowUpTurnContentService,
)
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)


class ChatFollowUpGroundedAnswerService:
    @classmethod
    def _currency_re(cls):
        from app.domain.services.chat_follow_up_turn_content_service import (
            ChatFollowUpTurnContentService,
        )

        return ChatFollowUpTurnContentService.compile_pattern("currencyMetric")

    @classmethod
    def build_challenge_answer(
        cls,
        *,
        workspace_context: dict | None = None,
        tool_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> str | None:
        excerpt = cls._resolve_excerpt(workspace_context, tool_context)
        if not isinstance(excerpt, dict) or not excerpt:
            return None

        title = str(excerpt.get("title") or "").strip() or (
            ChatTurnGroundingContentService.last_result_heading()
        )
        last_action = cls._resolve_last_action(workspace_context)
        params = (
            last_action.get("params")
            if isinstance(last_action, dict) and isinstance(last_action.get("params"), dict)
            else {}
        )
        branch = str(params.get("branch") or "").strip()
        start = str(params.get("start_date") or "").strip()
        end = str(params.get("end_date") or "").strip()

        snapshots = cls._collect_metric_snapshots(
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            tool_context=tool_context,
        )
        # Memória de sessão (KPI cards / prosa) — fallback quando previous_messages não chega.
        memory_snaps = cls._snapshots_from_working_memory(workspace_context)
        if memory_snaps:
            snapshots = list(memory_snaps) + list(snapshots)
        snapshots = cls._infer_branch_from_last_action(snapshots, workspace_context)
        consolidated = cls._pick_snapshot(snapshots, branched=False, prefer_label="ROL")
        branched = cls._pick_snapshot(
            snapshots,
            branched=True,
            prefer_branch=branch,
            prefer_label="ROL",
        )
        if consolidated is None:
            consolidated = cls._metric_from_working_memory_key(
                workspace_context, "lastConsolidatedMetric"
            )
        if branched is None:
            branched = cls._metric_from_working_memory_key(
                workspace_context, "lastBranchMetric"
            )

        parts: list[str] = [
            f"Sobre o último resultado (**{title}**), sua observação faz sentido analisar assim:"
        ]

        contrast = ""
        if consolidated and branched and consolidated.get("value") != branched.get("value"):
            contrast = ChatFollowUpTurnContentService.challenge_contrast_format(
                "consolidatedVsBranchTemplate",
                consolidated=str(consolidated.get("display") or ""),
                branch=str(branched.get("branch") or branch or "").strip() or "—",
                branch_value=str(branched.get("display") or ""),
            )
        elif branch and branch.lower() not in {"all", "todas"}:
            contrast = ChatFollowUpTurnContentService.challenge_contrast_format(
                "branchOnlyTemplate",
                branch=branch,
            )
        else:
            contrast = ChatFollowUpTurnContentService.challenge_contrast_format(
                "consolidatedOnlyTemplate",
            )

        if contrast:
            parts.append(contrast)

        if start and end:
            parts.append(f"Período da última consulta: {start} a {end}.")

        offer = ChatFollowUpTurnContentService.challenge_contrast_format("offerCompare")
        if offer:
            parts.append(offer)

        return "\n\n".join(part for part in parts if part)

    @classmethod
    def build_clarify_answer(
        cls,
        *,
        workspace_context: dict | None = None,
        tool_context: dict | None = None,
    ) -> str | None:
        slot = cls._resolve_clarify_slot(workspace_context, tool_context) or "branch"
        prompt = ChatFollowUpTurnContentService.clarify_slot_prompt(slot)
        return prompt or None

    @classmethod
    def build_revise_ack(
        cls,
        *,
        parameters: dict[str, Any] | None = None,
        last_action: dict[str, Any] | None = None,
        baseline_parameters: dict[str, Any] | None = None,
    ) -> str | None:
        params = dict(parameters or {})
        if not params and isinstance(last_action, dict):
            raw = last_action.get("params")
            if isinstance(raw, dict):
                params = dict(raw)

        parts: list[str] = []
        branch = str(params.get("branch") or "").strip()
        if branch and branch.lower() not in {"all", "todas"}:
            parts.append(ChatFollowUpTurnContentService.revise_ack_branch(branch))

        start = str(params.get("start_date") or "").strip()
        end = str(params.get("end_date") or "").strip()
        baseline = baseline_parameters if isinstance(baseline_parameters, dict) else {}
        baseline_start = str(baseline.get("start_date") or "").strip()
        baseline_end = str(baseline.get("end_date") or "").strip()
        changed = bool(
            start
            and end
            and baseline_start
            and baseline_end
            and (start, end) != (baseline_start, baseline_end)
        )
        if start and end:
            parts.append(
                ChatFollowUpTurnContentService.revise_ack_period(
                    start=start,
                    end=end,
                    changed=changed,
                )
            )

        return " ".join(parts).strip() or None

    @classmethod
    def build_period_compare_answer(
        cls,
        *,
        tool_calls: list | None,
        workspace_context: dict | None = None,
    ) -> str | None:
        """Monta prosa de comparação YoY a partir de dois toolCalls (baseline + prior)."""
        baseline_call, prior_call = cls._split_compare_tool_calls(tool_calls)
        if not baseline_call or not prior_call:
            return None

        baseline_metric = cls._metric_from_tool_call(baseline_call)
        prior_metric = cls._metric_from_tool_call(prior_call)
        if not baseline_metric or not prior_metric:
            return None

        baseline_params = cls._params_from_tool_call(baseline_call)
        prior_params = cls._params_from_tool_call(prior_call)
        period_kind = cls._period_compare_kind(
            workspace_context=workspace_context,
            baseline_params=baseline_params,
            prior_params=prior_params,
        )

        baseline_branch = str(baseline_params.get("branch") or "").strip()
        prior_branch = str(prior_params.get("branch") or "").strip()

        if period_kind == "branch":
            ack = ChatFollowUpTurnContentService.period_compare_branch_ack(
                baseline_branch=baseline_branch,
                compare_branch=prior_branch,
                start=str(baseline_params.get("start_date") or ""),
                end=str(baseline_params.get("end_date") or ""),
            )
            baseline_period_label = ChatFollowUpTurnContentService.period_compare_slot_label(
                "branch",
                "baseline",
                branch=baseline_branch,
            )
            prior_period_label = ChatFollowUpTurnContentService.period_compare_slot_label(
                "branch",
                "prior",
                branch=prior_branch,
            )
        else:
            ack = ChatFollowUpTurnContentService.period_compare_format(
                "ackTemplate",
                baseline_start=str(baseline_params.get("start_date") or ""),
                baseline_end=str(baseline_params.get("end_date") or ""),
                prior_start=str(prior_params.get("start_date") or ""),
                prior_end=str(prior_params.get("end_date") or ""),
            )
            baseline_period_label = ChatFollowUpTurnContentService.period_compare_slot_label(
                period_kind,
                "baseline",
            )
            prior_period_label = ChatFollowUpTurnContentService.period_compare_slot_label(
                period_kind,
                "prior",
            )

        label = str(baseline_metric.get("label") or prior_metric.get("label") or "Indicador")
        baseline_line = ChatFollowUpTurnContentService.period_compare_format(
            "lineTemplate",
            label=label,
            period_label=baseline_period_label or "referência",
            value=str(baseline_metric.get("display") or ""),
        )
        prior_line = ChatFollowUpTurnContentService.period_compare_format(
            "lineTemplate",
            label=label,
            period_label=prior_period_label or "período de comparação",
            value=str(prior_metric.get("display") or ""),
        )

        parts = [p for p in (ack, baseline_line, prior_line) if p]
        delta_line = cls._format_delta_line(baseline_metric, prior_metric)
        if delta_line:
            parts.append(delta_line)

        next_steps = ChatFollowUpTurnContentService.period_compare_next_steps()
        branch = str(baseline_params.get("branch") or prior_params.get("branch") or "").strip()
        if next_steps:
            formatted_steps: list[dict[str, str]] = []
            for item in next_steps[:3]:
                label = item["label"]
                query = item["query"]
                if branch and branch.lower() not in {"all", "todas"}:
                    query = query.replace("filial 01", f"filial {branch}")
                    query = query.replace("filial 02", f"filial {'02' if branch == '01' else '01'}")
                    label = label.replace("01", branch) if "01" in label else label
                formatted_steps.append({"label": label, "query": query})
            next_steps = formatted_steps

        if next_steps:
            parts.append("**Próximos passos**")
            for item in next_steps:
                parts.append(f"- {item['label']}")

        # Espelha sugestões no workspace para a UI de chips, se o pipeline consumir.
        if isinstance(workspace_context, dict) and next_steps:
            workspace_context.setdefault("followUpSuggestions", next_steps)

        return "\n".join(parts) if parts else None

    @classmethod
    def challenge_suggestion_items(cls) -> list[dict[str, str]]:
        return ChatFollowUpTurnContentService.challenge_suggestions()

    @classmethod
    def inject_challenge_prompt_context(
        cls,
        tool_context: dict | None,
        *,
        workspace_context: dict | None = None,
    ) -> dict:
        updated = dict(tool_context or {})
        excerpt = cls._resolve_excerpt(workspace_context, updated)
        instruction = ChatFollowUpTurnContentService.challenge_faithfulness_instruction()
        blocks: list[str] = []

        if instruction:
            blocks.append(instruction)

        if isinstance(excerpt, dict) and excerpt:
            excerpt_block = ChatTurnGroundingContentService.format_excerpt_prompt_block(
                excerpt
            )
            if excerpt_block:
                blocks.append(excerpt_block)

        last_action = cls._resolve_last_action(workspace_context)
        if isinstance(last_action, dict) and last_action:
            params = last_action.get("params") if isinstance(last_action.get("params"), dict) else {}
            blocks.append(
                "Parâmetros da última consulta: "
                + ", ".join(f"{k}={v}" for k, v in params.items() if v not in (None, ""))
            )

        if blocks:
            existing = str(updated.get("analysisContext") or "").strip()
            joined = "\n\n".join(blocks)
            updated["analysisContext"] = (
                f"{existing}\n\n{joined}".strip() if existing else joined
            )
            updated["groundedNarrate"] = True
            updated["followUpChallenge"] = True

        suggestions = cls.challenge_suggestion_items()
        if suggestions:
            updated["followUpSuggestions"] = suggestions

        return updated

    @classmethod
    def _format_delta_line(
        cls,
        baseline: dict[str, Any],
        prior: dict[str, Any],
    ) -> str:
        try:
            base_val = float(baseline.get("value"))
            prior_val = float(prior.get("value"))
        except (TypeError, ValueError):
            return ""

        delta = base_val - prior_val
        if abs(delta) < 0.005:
            phrase = ChatFollowUpTurnContentService.period_compare_format("deltaFlat") or "estável"
            return ChatFollowUpTurnContentService.period_compare_format(
                "deltaTemplate",
                delta=phrase,
                pct="0%",
            )

        abs_display = cls._format_brl(abs(delta))
        if delta > 0:
            phrase = ChatFollowUpTurnContentService.period_compare_format(
                "deltaUp",
                abs_delta=abs_display,
            )
        else:
            phrase = ChatFollowUpTurnContentService.period_compare_format(
                "deltaDown",
                abs_delta=abs_display,
            )

        pct = ""
        if prior_val:
            ratio = (delta / prior_val) * 100.0
            sign = "+" if ratio > 0 else ""
            pct = ChatFollowUpTurnContentService.period_compare_format(
                "pctTemplate",
                sign=sign,
                pct=f"{ratio:.1f}",
            )

        return ChatFollowUpTurnContentService.period_compare_format(
            "deltaTemplate",
            delta=phrase or abs_display,
            pct=pct or "—",
        )

    @classmethod
    def _split_compare_tool_calls(
        cls,
        tool_calls: list | None,
    ) -> tuple[dict | None, dict | None]:
        baseline = None
        prior = None
        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue
            if str(call.get("name") or "") != "execute_external_action":
                continue
            role = cls._compare_role(call)
            if role == "baseline":
                baseline = call
            elif role == "prior":
                prior = call
        if baseline and prior:
            return baseline, prior
        # Fallback: dois ok em sequência com datas distintas
        ok_calls = [
            call
            for call in (tool_calls or [])
            if isinstance(call, dict)
            and str(call.get("name") or "") == "execute_external_action"
            and isinstance(call.get("metadata"), dict)
            and call["metadata"].get("ok")
        ]
        if len(ok_calls) >= 2:
            return ok_calls[0], ok_calls[1]
        return None, None

    @classmethod
    def _compare_role(cls, tool_call: dict) -> str:
        for source in (
            tool_call.get("periodCompareRole"),
            (tool_call.get("arguments") or {}).get("selectionDiagnostics")
            if isinstance(tool_call.get("arguments"), dict)
            else None,
            tool_call.get("metadata") if isinstance(tool_call.get("metadata"), dict) else None,
        ):
            if isinstance(source, dict):
                role = str(source.get("periodCompareRole") or "").strip()
                if role:
                    return role
            elif source:
                role = str(source).strip()
                if role in {"baseline", "prior"}:
                    return role
        return ""

    @classmethod
    def _params_from_tool_call(cls, tool_call: dict) -> dict[str, Any]:
        args = tool_call.get("arguments")
        if isinstance(args, dict) and isinstance(args.get("parameters"), dict):
            return dict(args.get("parameters") or {})
        meta = tool_call.get("metadata")
        if isinstance(meta, dict) and isinstance(meta.get("requestParameters"), dict):
            return dict(meta.get("requestParameters") or {})
        return {}

    @classmethod
    def _period_compare_kind(
        cls,
        *,
        workspace_context: dict | None,
        baseline_params: dict[str, Any],
        prior_params: dict[str, Any],
    ) -> str | None:
        if isinstance(workspace_context, dict):
            grounding = workspace_context.get("turnGrounding")
            follow_up = (
                grounding.get("followUp") if isinstance(grounding, dict) else None
            )
            delta = (
                follow_up.get("slotDelta") if isinstance(follow_up, dict) else None
            )
            if isinstance(delta, dict):
                kind = str(delta.get("period") or "").strip()
                if kind:
                    return kind
                if str(delta.get("compareAxis") or "").strip() == "branch":
                    return "branch"

        baseline_start = str(baseline_params.get("start_date") or "").strip()
        prior_start = str(prior_params.get("start_date") or "").strip()
        baseline_end = str(baseline_params.get("end_date") or "").strip()
        prior_end = str(prior_params.get("end_date") or "").strip()
        baseline_branch = str(baseline_params.get("branch") or "").strip()
        prior_branch = str(prior_params.get("branch") or "").strip()

        if (
            baseline_branch
            and prior_branch
            and baseline_branch != prior_branch
            and baseline_start
            and prior_start
            and baseline_start == prior_start
            and baseline_end == prior_end
        ):
            return "branch"

        if len(baseline_start) >= 10 and len(prior_start) >= 10:
            # DD-MM-YYYY — mesmo mês/dia com ano-1 => YoY
            if (
                baseline_start[:5] == prior_start[:5]
                and baseline_start[6:10].isdigit()
                and prior_start[6:10].isdigit()
                and int(baseline_start[6:10]) - int(prior_start[6:10]) == 1
            ):
                return "previous_year_same_range"
            if baseline_start != prior_start:
                return "previous_period"
        return None

    @classmethod
    def _metric_from_tool_call(cls, tool_call: dict) -> dict[str, Any] | None:
        meta = tool_call.get("metadata") if isinstance(tool_call.get("metadata"), dict) else {}
        kpi = meta.get("kpiPresentation") if isinstance(meta.get("kpiPresentation"), dict) else {}
        cards = kpi.get("cards") if isinstance(kpi.get("cards"), list) else []
        preferred = ChatFollowUpTurnContentService.period_compare_preferred_metric_keys()
        chosen = None
        for key in preferred:
            for card in cards:
                if not isinstance(card, dict):
                    continue
                if str(card.get("key") or "").strip().lower() == key:
                    chosen = card
                    break
            if chosen:
                break
        if chosen is None and cards and isinstance(cards[0], dict):
            chosen = cards[0]
        if chosen is not None:
            raw = chosen.get("value")
            try:
                value = float(raw)
            except (TypeError, ValueError):
                value = None
            if value is not None:
                label = str(chosen.get("label") or chosen.get("key") or "Indicador").strip()
                return {
                    "label": label,
                    "value": value,
                    "display": cls._format_brl(value),
                    "branch": str(cls._params_from_tool_call(tool_call).get("branch") or "").strip(),
                }

        text = str(meta.get("assistantMarkdown") or meta.get("humanizedSummary") or "")
        match = cls._currency_re().search(text)
        if match:
            value = cls._parse_brl(match.group("value"))
            if value is not None:
                return {
                    "label": match.group("label").strip(),
                    "value": value,
                    "display": f"R$ {match.group('value')}",
                    "branch": str(cls._params_from_tool_call(tool_call).get("branch") or "").strip(),
                }
        return None

    @classmethod
    def _metric_from_working_memory_key(
        cls,
        workspace_context: dict | None,
        key: str,
    ) -> dict[str, Any] | None:
        if not isinstance(workspace_context, dict):
            return None
        working = workspace_context.get("workingMemory")
        if not isinstance(working, dict):
            return None
        raw = working.get(key)
        if not isinstance(raw, dict):
            return None
        try:
            value = float(raw.get("value"))
        except (TypeError, ValueError):
            return None
        return {
            "label": str(raw.get("label") or "Indicador").strip(),
            "value": value,
            "display": str(raw.get("display") or cls._format_brl(value)),
            "branch": str(raw.get("branch") or "").strip(),
        }

    @classmethod
    def _snapshots_from_working_memory(
        cls,
        workspace_context: dict | None,
    ) -> list[dict[str, Any]]:
        if not isinstance(workspace_context, dict):
            return []
        working = workspace_context.get("workingMemory")
        if not isinstance(working, dict):
            return []
        raw = working.get("recentMetricSnapshots")
        if not isinstance(raw, list):
            return []
        out: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                value = float(item.get("value"))
            except (TypeError, ValueError):
                continue
            out.append(
                {
                    "label": str(item.get("label") or "Indicador").strip(),
                    "value": value,
                    "display": str(item.get("display") or cls._format_brl(value)),
                    "branch": str(item.get("branch") or "").strip(),
                }
            )
        return out

    @classmethod
    def _collect_metric_snapshots(
        cls,
        *,
        previous_messages: list | None,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> list[dict[str, Any]]:
        snapshots: list[dict[str, Any]] = []

        def _add(metric: dict[str, Any] | None) -> None:
            if not metric:
                return
            snapshots.append(metric)

        if isinstance(tool_context, dict):
            for call in tool_context.get("toolCalls") or []:
                if isinstance(call, dict):
                    _add(cls._metric_from_tool_call(call))

        for message in previous_messages or []:
            role = ""
            content = ""
            meta: dict[str, Any] = {}
            tools: list = []
            if isinstance(message, dict):
                role = str(message.get("role") or "")
                content = str(message.get("content") or "")
                meta = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
                tools = meta.get("toolCalls") or message.get("toolCalls") or []
            else:
                role = str(getattr(message, "role", "") or "")
                content = str(getattr(message, "content", "") or "")
                raw_meta = getattr(message, "metadata", None)
                meta = raw_meta if isinstance(raw_meta, dict) else {}
                tools = meta.get("toolCalls") or getattr(message, "tool_calls", None) or []

            if str(role).strip().lower() != "assistant":
                continue

            message_branch = ""
            for call in tools if isinstance(tools, list) else []:
                if not isinstance(call, dict):
                    continue
                metric = cls._metric_from_tool_call(call)
                _add(metric)
                if metric and metric.get("branch"):
                    message_branch = str(metric.get("branch") or "")
                else:
                    params = cls._params_from_tool_call(call)
                    if params.get("branch"):
                        message_branch = str(params.get("branch") or "")

            if content:
                for match in cls._currency_re().finditer(content):
                    value = cls._parse_brl(match.group("value"))
                    if value is None:
                        continue
                    _add(
                        {
                            "label": match.group("label"),
                            "value": value,
                            "display": f"R$ {match.group('value')}",
                            "branch": message_branch,
                        }
                    )

        # Excerpt / last preview — só como consolidado (sem carimbar filial da lastAction).
        excerpt = cls._resolve_excerpt(workspace_context, tool_context)
        if isinstance(excerpt, dict):
            preview = str(excerpt.get("preview") or "")
            for match in cls._currency_re().finditer(preview):
                value = cls._parse_brl(match.group("value"))
                if value is None:
                    continue
                _add(
                    {
                        "label": match.group("label"),
                        "value": value,
                        "display": f"R$ {match.group('value')}",
                        "branch": "",
                    }
                )

        return cls._infer_branch_from_last_action(snapshots, workspace_context)

    @classmethod
    def _infer_branch_from_last_action(
        cls,
        snapshots: list[dict[str, Any]],
        workspace_context: dict | None,
    ) -> list[dict[str, Any]]:
        """Quando o histórico só tem prosa (sem params), a lastAction.branch marca o ROL mais recente."""
        last_action = cls._resolve_last_action(workspace_context)
        if not isinstance(last_action, dict):
            return snapshots
        params = last_action.get("params") if isinstance(last_action.get("params"), dict) else {}
        branch = str(params.get("branch") or "").strip()
        if not branch or branch.lower() in {"all", "todas"}:
            return snapshots

        has_explicit_branch = any(
            str(item.get("branch") or "").strip()
            and str(item.get("branch") or "").strip().lower() not in {"all", "todas"}
            for item in snapshots
        )
        if has_explicit_branch:
            return snapshots

        # Agrupa por label; se houver ≥2 valores sem filial, o mais antigo = consolidado e o
        # mais recente = filial da lastAction.
        by_label: dict[str, list[int]] = {}
        for idx, item in enumerate(snapshots):
            key = str(item.get("label") or "").strip().lower()
            if not key:
                continue
            by_label.setdefault(key, []).append(idx)

        updated = [dict(item) for item in snapshots]
        for indices in by_label.values():
            if len(indices) < 2:
                continue
            latest_idx = indices[-1]
            updated[latest_idx]["branch"] = branch
        return updated

    @classmethod
    def _pick_snapshot(
        cls,
        snapshots: list[dict[str, Any]],
        *,
        branched: bool,
        prefer_branch: str = "",
        prefer_label: str = "",
    ) -> dict[str, Any] | None:
        prefer = str(prefer_branch or "").strip()
        label = str(prefer_label or "").strip().lower()

        def _matches_label(item: dict[str, Any]) -> bool:
            if not label:
                return True
            return label in str(item.get("label") or "").strip().lower()

        # Pass 1: prefer label + branch constraints
        # Consolidado: mais antigo da thread (total antes dos filtros).
        # Filial: mais recente.
        ordered = snapshots if not branched else list(reversed(snapshots))
        for item in ordered:
            if not _matches_label(item):
                continue
            item_branch = str(item.get("branch") or "").strip()
            is_branch = bool(item_branch) and item_branch.lower() not in {
                "all",
                "todas",
                "consolidated",
            }
            if branched and is_branch:
                if prefer and item_branch != prefer:
                    continue
                return item
            if not branched and not is_branch:
                return item

        # Pass 2: any matching branch constraint
        for item in ordered:
            item_branch = str(item.get("branch") or "").strip()
            is_branch = bool(item_branch) and item_branch.lower() not in {
                "all",
                "todas",
                "consolidated",
            }
            if branched and is_branch:
                if prefer and item_branch != prefer:
                    continue
                return item
            if not branched and not is_branch:
                return item

        if branched:
            for item in reversed(snapshots):
                item_branch = str(item.get("branch") or "").strip()
                if item_branch and item_branch.lower() not in {"all", "todas"}:
                    return item
        return None

    @classmethod
    def _format_brl(cls, value: float) -> str:
        formatted = f"{value:,.2f}"
        return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    @classmethod
    def _parse_brl(cls, raw: str) -> float | None:
        token = str(raw or "").strip()
        if not token:
            return None
        try:
            return float(token.replace(".", "").replace(",", "."))
        except ValueError:
            return None

    @classmethod
    def _resolve_clarify_slot(
        cls,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> str | None:
        for source in (tool_context, workspace_context):
            if not isinstance(source, dict):
                continue
            turn = source.get("turnGrounding")
            if not isinstance(turn, dict):
                continue
            follow_up = turn.get("followUp")
            if isinstance(follow_up, dict) and follow_up.get("clarifySlot"):
                return str(follow_up.get("clarifySlot")).strip() or None
        return None

    @classmethod
    def _resolve_excerpt(
        cls,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> dict[str, Any] | None:
        for source in (tool_context, workspace_context):
            if not isinstance(source, dict):
                continue
            turn = source.get("turnGrounding")
            if isinstance(turn, dict):
                excerpt = turn.get("excerpt")
                if isinstance(excerpt, dict) and excerpt:
                    return excerpt
            working = source.get("workingMemory")
            if isinstance(working, dict):
                excerpt = working.get("lastResultExcerpt")
                if isinstance(excerpt, dict) and excerpt:
                    return excerpt
        return None

    @classmethod
    def _resolve_last_action(
        cls,
        workspace_context: dict | None,
    ) -> dict[str, Any] | None:
        if not isinstance(workspace_context, dict):
            return None
        working = workspace_context.get("workingMemory")
        if isinstance(working, dict) and isinstance(working.get("lastAction"), dict):
            return working.get("lastAction")
        return None
