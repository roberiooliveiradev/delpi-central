"""Normalização dos contratos dataCommentary e dataAnswer — Playbook 13."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)

_ALERT_LEVELS = ("ok", "attention", "critical", "unknown")
_RISK_LEVELS = ("ok", "attention", "critical", "undefined")
_ALERT_TO_RISK = {
    "ok": "ok",
    "attention": "attention",
    "critical": "critical",
    "unknown": "undefined",
}
_RISK_TO_ALERT = {value: key for key, value in _ALERT_TO_RISK.items()}


class ChatHumanizedDataResponseService:
    @classmethod
    def normalize(cls, commentary: dict[str, Any] | None, *, profile_key: str = "") -> dict[str, Any] | None:
        if not isinstance(commentary, dict):
            return None

        normalized = dict(commentary)
        profile = str(profile_key or commentary.get("profileKey") or "").strip()

        highlights = cls._clean_lines(commentary.get("highlights"))
        attention = cls._clean_lines(commentary.get("attention"))
        narrative = str(commentary.get("narrativeInsight") or "").strip()
        limitations = cls._clean_lines(commentary.get("limitations"))

        alert_level = cls._resolve_alert_level(commentary, attention=attention, highlights=highlights)
        summary = cls._resolve_summary(commentary, highlights=highlights, narrative=narrative)
        interpretation = cls._resolve_interpretation(
            commentary,
            highlights=highlights,
            narrative=narrative,
        )
        empty_result = bool(commentary.get("emptyResult"))

        if empty_result:
            next_action = ""
            recommendations: list[dict[str, str]] = []
            attention = []
            limitations = []
        else:
            next_action = cls._resolve_next_action(
                commentary,
                profile_key=profile,
                alert_level=alert_level,
            )
            recommendations = cls._build_recommendations(commentary, profile_key=profile)

            if not limitations:
                limitations = cls._default_limitations(commentary)

        normalized["alertLevel"] = alert_level
        normalized["summary"] = summary
        normalized["interpretation"] = interpretation
        normalized["nextAction"] = next_action
        normalized["facts"] = cls._build_facts(highlights)
        normalized["analysis"] = (
            []
            if empty_result
            else cls._build_analysis(commentary, highlights=highlights, attention=attention)
        )
        normalized["recommendations"] = recommendations
        normalized["limitations"] = limitations
        normalized["attention"] = attention
        normalized["emptyResult"] = empty_result
        normalized["readingLayer"] = ChatHumanizedDataResponseContentService.get_node("readingLayers") or {}

        if profile:
            normalized["profileKey"] = profile

        return normalized

    @classmethod
    def render_quick_layer_markdown(cls, commentary: dict[str, Any] | None) -> str:
        if not isinstance(commentary, dict):
            return ""

        summary = str(commentary.get("summary") or "").strip()
        interpretation = str(commentary.get("interpretation") or "").strip()
        next_action = str(commentary.get("nextAction") or "").strip()
        alert_level = str(commentary.get("alertLevel") or "unknown").strip().lower()

        if alert_level not in _ALERT_LEVELS:
            alert_level = "unknown"

        parts: list[str] = [
            "<!-- section:summary -->",
            ChatHumanizedDataResponseContentService.get("sections", "summaryHeader"),
            "",
        ]

        if summary and interpretation and interpretation not in summary:
            parts.append(
                ChatHumanizedDataResponseContentService.format(
                    "summaryTemplates",
                    "withInterpretation",
                    summary=summary,
                    interpretation=interpretation,
                )
            )
        elif summary:
            parts.append(
                ChatHumanizedDataResponseContentService.format(
                    "summaryTemplates",
                    "summaryOnly",
                    summary=summary,
                )
            )

        alert_line = ChatHumanizedDataResponseContentService.get(
            "alertLevelLines",
            alert_level,
            default="",
        )

        if alert_line:
            parts.extend(["", alert_line])

        if next_action:
            parts.extend(
                [
                    "",
                    ChatHumanizedDataResponseContentService.get(
                        "sections",
                        "nextActionHeader",
                    ),
                    "",
                    next_action,
                ]
            )

        return "\n".join(part for part in parts if part is not None).strip()

    @classmethod
    def to_data_answer(
        cls,
        commentary: dict[str, Any] | None,
        *,
        profile_key: str = "",
    ) -> dict[str, Any] | None:
        if not isinstance(commentary, dict):
            return None

        profile = str(profile_key or commentary.get("profileKey") or "").strip()
        normalized = (
            commentary
            if commentary.get("facts") is not None and commentary.get("summary")
            else cls.normalize(commentary, profile_key=profile)
        )

        if not normalized:
            return None

        alert_level = str(normalized.get("alertLevel") or "unknown").strip().lower()
        risk_level = _ALERT_TO_RISK.get(alert_level, "undefined")

        if risk_level not in _RISK_LEVELS:
            risk_level = "undefined"

        empty_result = bool(normalized.get("emptyResult") or commentary.get("emptyResult"))

        return {
            "summary": {
                "answer": str(normalized.get("summary") or "").strip(),
                "meaning": str(normalized.get("interpretation") or "").strip(),
                "riskLevel": risk_level,
                "nextAction": "" if empty_result else str(normalized.get("nextAction") or "").strip(),
                "attention": [] if empty_result else cls._clean_lines(normalized.get("attention")),
            },
            "facts": normalized.get("facts") or [],
            "analysis": [] if empty_result else (normalized.get("analysis") or []),
            "hypotheses": cls._clean_hypotheses(commentary.get("hypotheses")),
            "recommendations": (
                []
                if empty_result
                else cls._build_structured_recommendations(
                    normalized,
                    profile_key=profile,
                )
            ),
            "limitations": [] if empty_result else (normalized.get("limitations") or []),
            "derivedMetrics": cls._clean_derived_metrics(commentary.get("derivedMetrics")),
            "visualHints": cls._clean_string_list(commentary.get("visualHints")),
            "anomalies": cls._clean_anomalies(commentary.get("anomalies")),
            "profileKey": profile,
            "emptyResult": empty_result,
        }

    @classmethod
    def to_commentary_mirror(cls, data_answer: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(data_answer, dict):
            return None

        summary = data_answer.get("summary")

        if isinstance(summary, str) and summary.strip():
            summary = {"answer": summary.strip()}

        if not isinstance(summary, dict):
            return None

        risk_level = str(summary.get("riskLevel") or "undefined").strip().lower()
        alert_level = _RISK_TO_ALERT.get(risk_level, "unknown")

        highlights = [
            str(item.get("text") or "").strip()
            for item in (data_answer.get("facts") or [])
            if isinstance(item, dict) and str(item.get("text") or "").strip()
        ]

        recommendations = [
            {
                "text": str(item.get("label") or item.get("text") or "").strip(),
                **(
                    {"intent": str(item.get("query") or item.get("intent") or "").strip()}
                    if isinstance(item, dict)
                    and str(item.get("query") or item.get("intent") or "").strip()
                    else {}
                ),
            }
            for item in (data_answer.get("recommendations") or [])
            if str(
                (item.get("label") if isinstance(item, dict) else item) or ""
            ).strip()
        ]

        answer = str(summary.get("answer") or "").strip()
        meaning = str(summary.get("meaning") or "").strip()

        empty_result = bool(data_answer.get("emptyResult"))

        return {
            "profileKey": str(data_answer.get("profileKey") or "").strip(),
            "summary": answer,
            "interpretation": meaning,
            "alertLevel": alert_level,
            "nextAction": "" if empty_result else str(summary.get("nextAction") or "").strip(),
            "attention": [] if empty_result else cls._clean_lines(summary.get("attention")),
            "highlights": highlights,
            "summaryLines": [answer] if answer else highlights[:4],
            "facts": data_answer.get("facts") or [],
            "analysis": [] if empty_result else (data_answer.get("analysis") or []),
            "recommendations": [] if empty_result else recommendations,
            "limitations": [] if empty_result else (data_answer.get("limitations") or []),
            "anomalies": data_answer.get("anomalies") or [],
            "visualHints": data_answer.get("visualHints") or [],
            "emptyResult": empty_result,
            "readingLayer": ChatHumanizedDataResponseContentService.get_node("readingLayers") or {},
        }

    @classmethod
    def resolve_commentary_from_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        data_answer = metadata.get("dataAnswer")

        if isinstance(data_answer, dict):
            mirror = cls.to_commentary_mirror(data_answer)

            if mirror:
                return mirror

        commentary = metadata.get("dataCommentary")

        if isinstance(commentary, dict):
            return commentary

        return None

    @classmethod
    def _resolve_alert_level(
        cls,
        commentary: dict[str, Any],
        *,
        attention: list[str],
        highlights: list[str],
    ) -> str:
        explicit = str(commentary.get("alertLevel") or "").strip().lower()

        if explicit in _ALERT_LEVELS:
            return explicit

        combined = " ".join(highlights + attention).casefold()

        if any(
            token in combined
            for token in (
                "sem estrutura",
                "negativo",
                "bloqueio",
                "sem saldo",
                "crítico",
                "critico",
            )
        ):
            return "critical"

        if attention:
            return "attention"

        if highlights:
            return "ok"

        return "unknown"

    @classmethod
    def _resolve_summary(
        cls,
        commentary: dict[str, Any],
        *,
        highlights: list[str],
        narrative: str,
    ) -> str:
        explicit = str(commentary.get("summary") or "").strip()

        if explicit:
            return explicit

        if narrative:
            return narrative

        if highlights:
            return highlights[0]

        return ""

    @classmethod
    def _resolve_interpretation(
        cls,
        commentary: dict[str, Any],
        *,
        highlights: list[str],
        narrative: str,
    ) -> str:
        explicit = str(commentary.get("interpretation") or "").strip()

        if explicit:
            return explicit

        extras = highlights[1:3]

        if extras:
            return " ".join(extras).strip()

        if narrative and highlights and narrative != highlights[0]:
            return narrative

        return ""

    @classmethod
    def _resolve_next_action(
        cls,
        commentary: dict[str, Any],
        *,
        profile_key: str,
        alert_level: str,
    ) -> str:
        del alert_level
        explicit = str(commentary.get("nextAction") or "").strip()

        if explicit:
            return explicit

        recommendations = cls._build_recommendations(commentary, profile_key=profile_key)

        if recommendations:
            first = recommendations[0]
            text = str(first.get("text") or "").strip()

            if text:
                return text

        if profile_key:
            action = ChatHumanizedDataResponseContentService.get(
                "nextActions",
                profile_key,
                default="",
            )

            if action:
                return action

        # Próximos passos ficam nos chips de interatividade — não inventar
        # bullet genérico na prosa (evita «Próximos passos» duplicado).
        return ""

    @classmethod
    def _build_facts(cls, highlights: list[str]) -> list[dict[str, str]]:
        return [{"text": line} for line in highlights[:6]]

    @classmethod
    def _build_analysis(
        cls,
        commentary: dict[str, Any],
        *,
        highlights: list[str],
        attention: list[str],
    ) -> list[dict[str, str]]:
        existing = commentary.get("analysis")

        if isinstance(existing, list) and existing:
            return [
                {"text": str(item.get("text") or item).strip()}
                for item in existing
                if str(item.get("text") if isinstance(item, dict) else item or "").strip()
            ]

        analysis: list[dict[str, str]] = []

        for line in highlights[1:4]:
            analysis.append({"text": line})

        for line in attention[:2]:
            analysis.append({"text": line})

        return analysis

    @classmethod
    def _build_recommendations(
        cls,
        commentary: dict[str, Any],
        *,
        profile_key: str,
    ) -> list[dict[str, str]]:
        existing = commentary.get("recommendations")

        if isinstance(existing, list) and existing:
            return [
                {
                    "text": str(item.get("text") or item).strip(),
                    **({"intent": str(item.get("intent")).strip()} if isinstance(item, dict) and item.get("intent") else {}),
                }
                for item in existing
                if str(item.get("text") if isinstance(item, dict) else item or "").strip()
            ]

        texts = ChatHumanizedDataResponseContentService.list(
            "recommendations",
            profile_key,
        )

        return [{"text": text} for text in texts if str(text).strip()]

    @classmethod
    def _build_structured_recommendations(
        cls,
        commentary: dict[str, Any],
        *,
        profile_key: str,
    ) -> list[dict[str, str]]:
        existing = commentary.get("recommendations")

        if isinstance(existing, list) and existing:
            structured: list[dict[str, str]] = []

            for item in existing:
                if not isinstance(item, dict):
                    text = str(item or "").strip()

                    if text:
                        structured.append({"label": text, "query": text, "reason": ""})

                    continue

                label = str(item.get("label") or item.get("text") or "").strip()
                query = str(item.get("query") or item.get("intent") or label).strip()
                reason = str(item.get("reason") or "").strip()

                if label:
                    structured.append({"label": label, "query": query, "reason": reason})

            if structured:
                return structured

        queries = ChatHumanizedDataResponseContentService.recommendation_queries(profile_key)

        if queries:
            return queries

        texts = cls._build_recommendations(commentary, profile_key=profile_key)

        return [
            {
                "label": text,
                "query": text,
                "reason": "",
            }
            for item in texts
            for text in [str(item.get("text") or "").strip()]
            if text
        ]

    @classmethod
    def _default_limitations(cls, commentary: dict[str, Any]) -> list[str]:
        limitations: list[str] = []

        if commentary.get("paginated"):
            limitations.append(
                ChatHumanizedDataResponseContentService.get(
                    "limitations",
                    "pagination",
                )
            )

        if commentary.get("periodScoped"):
            limitations.append(
                ChatHumanizedDataResponseContentService.get(
                    "limitations",
                    "periodOnly",
                )
            )

        return [line for line in limitations if line]

    @classmethod
    def _clean_lines(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []

        return [str(line).strip() for line in value if str(line or "").strip()]

    @classmethod
    def _clean_string_list(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []

        return [str(item).strip() for item in value if str(item or "").strip()]

    @classmethod
    def _clean_hypotheses(cls, value: object) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []

        hypotheses: list[dict[str, str]] = []

        for item in value:
            if isinstance(item, dict):
                text = str(item.get("text") or "").strip()

                if text:
                    hypotheses.append({"text": text})

                continue

            text = str(item or "").strip()

            if text:
                hypotheses.append({"text": text})

        return hypotheses

    @classmethod
    def _clean_derived_metrics(cls, value: object) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []

        metrics: list[dict[str, str]] = []

        for item in value:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            metric_value = str(item.get("value") or "").strip()

            if label:
                metrics.append({"label": label, "value": metric_value})

        return metrics

    @classmethod
    def _clean_anomalies(cls, value: object) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        anomalies: list[dict[str, Any]] = []

        for item in value:
            if not isinstance(item, dict):
                continue

            anomaly_type = str(item.get("type") or "").strip()

            if anomaly_type:
                anomalies.append(dict(item))

        return anomalies

    @classmethod
    def apply_empty_result_contract(
        cls,
        commentary: dict[str, Any] | None,
        *,
        rows: list | None,
        metadata: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Mark empty list results and strip spurious attention / next steps."""
        if not isinstance(commentary, dict):
            return commentary

        anomalies = commentary.get("anomalies") if isinstance(commentary.get("anomalies"), list) else []
        has_empty_anomaly = any(
            isinstance(item, dict) and str(item.get("type") or "").strip() == "empty_list"
            for item in anomalies
        )
        is_empty_rows = isinstance(rows, list) and len(rows) == 0

        if not has_empty_anomaly and not is_empty_rows:
            return commentary

        profile = str(commentary.get("profileKey") or "").strip()

        # Perfis ricos (factory_status, stock, …) já montam commentary próprio —
        # não substituir por emptyResult genérico quando há highlights/summary reais.
        if profile and profile not in {"generic_list", "kpi_summary"}:
            return cls._strip_redundant_empty_list_attention(commentary)

        updated = dict(commentary)
        entity = cls._resolve_empty_entity(metadata, data)
        code = cls._resolve_product_code(metadata, data)
        message = cls._empty_result_message(profile_key=profile, entity=entity, code=code)

        updated["emptyResult"] = True
        updated["summary"] = message
        updated["highlights"] = [message]
        updated["summaryLines"] = [message]
        updated["interpretation"] = ""
        updated["narrativeInsight"] = ""
        updated["nextAction"] = ""
        updated["attention"] = []
        updated["recommendations"] = []
        updated["limitations"] = []
        updated["analysis"] = []
        updated["facts"] = [{"text": message}]

        return cls.normalize(updated, profile_key=profile) or updated

    @classmethod
    def _strip_redundant_empty_list_attention(
        cls,
        commentary: dict[str, Any],
    ) -> dict[str, Any]:
        """Remove attention lines that only restate empty_list when profile already spoke."""
        anomalies = commentary.get("anomalies") if isinstance(commentary.get("anomalies"), list) else []
        has_empty = any(
            isinstance(item, dict) and str(item.get("type") or "").strip() == "empty_list"
            for item in anomalies
        )

        if not has_empty:
            return commentary

        highlights = cls._clean_lines(commentary.get("highlights"))
        summary = str(commentary.get("summary") or "").strip()

        if not highlights and not summary:
            return commentary

        empty_phrase = ChatHumanizedDataResponseContentService.get(
            "anomalies",
            "empty_list",
            default="",
        ).split("{")[0].strip().casefold()
        attention = [
            line
            for line in cls._clean_lines(commentary.get("attention"))
            if empty_phrase not in line.casefold()
            and "não há registros" not in line.casefold()
            and "nao ha registros" not in line.casefold()
        ]
        updated = dict(commentary)
        updated["attention"] = attention
        return updated

    @classmethod
    def _empty_result_message(
        cls,
        *,
        profile_key: str,
        entity: str,
        code: str,
    ) -> str:
        for_product = ""

        if code:
            for_product = ChatHumanizedDataResponseContentService.format(
                "emptyResult",
                "forProductSuffix",
                code=code,
                default=f" para o produto {code}",
            )

        by_entity = ChatHumanizedDataResponseContentService.get_mapping("emptyResult", "byEntity")
        template = str(by_entity.get(entity) or "").strip() if entity else ""

        if not template:
            by_profile = ChatHumanizedDataResponseContentService.get_mapping(
                "emptyResult",
                "byProfile",
            )
            template = str(by_profile.get(profile_key) or "").strip()

        if not template:
            template = ChatHumanizedDataResponseContentService.get(
                "emptyResult",
                "generic",
                default="Nenhum registro encontrado{forProduct}.",
            )

        return template.replace("{forProduct}", for_product)

    @classmethod
    def _resolve_empty_entity(
        cls,
        metadata: dict[str, Any] | None,
        data: dict[str, Any] | None,
    ) -> str:
        meta = metadata if isinstance(metadata, dict) else {}
        response_meta = meta.get("apiDelpiResponseMeta")

        if isinstance(response_meta, dict):
            entity = str(response_meta.get("entity") or "").strip()

            if entity:
                return entity

        path = str(meta.get("path") or "").strip().lower()

        if "/outbound-invoice" in path:
            return "product_outbound_invoice_items"

        if "/inbound-invoice" in path:
            return "product_inbound_invoice_items"

        if "/internal-movement" in path:
            return "product_internal_movements"

        if path.rstrip("/").endswith("/sales") or "/sales/" in path:
            return "product_sales"

        if path.rstrip("/").endswith("/purchases") or "/purchases/" in path:
            return "product_purchases"

        _ = data
        return ""

    @classmethod
    def _resolve_product_code(
        cls,
        metadata: dict[str, Any] | None,
        data: dict[str, Any] | None,
    ) -> str:
        meta = metadata if isinstance(metadata, dict) else {}
        payload = data if isinstance(data, dict) else {}

        for key in ("productCode", "code"):
            value = str(meta.get(key) or "").strip()

            if value:
                return value

        product = payload.get("product")

        if isinstance(product, dict):
            for key in ("product_code", "code", "B1_COD"):
                value = str(product.get(key) or "").strip()

                if value:
                    return value

        for key in ("product_code", "code", "B1_COD"):
            value = str(payload.get(key) or "").strip()

            if value:
                return value

        path = str(meta.get("path") or "")
        parts = [part for part in path.split("/") if part]

        if len(parts) >= 2 and parts[0] == "products":
            candidate = parts[1]

            if candidate not in {"directives", "analyser"} and candidate.isalnum():
                return candidate

        return ""
