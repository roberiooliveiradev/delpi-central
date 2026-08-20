"""Auto-detecção de ambiguidade no pipeline de desenho — sinais, policies e ask-user."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


class ChatDrawingAmbiguityIntelligenceService:
    """Estágio central: detectar incerteza própria, suspender asserções e pedir ajuda."""

    @classmethod
    def _node(cls, *path: str) -> Any:
        return ChatDrawingValidationContentService.get_node(
            "ambiguityIntelligence",
            *path,
        )

    @classmethod
    def _detectors(cls) -> dict[str, Any]:
        node = cls._node("detectors")
        return node if isinstance(node, dict) else {}

    @classmethod
    def _policy_for_kind(cls, kind: str) -> dict[str, Any]:
        node = cls._node("policies", kind)
        return node if isinstance(node, dict) else {}

    @classmethod
    def _kind_meta(cls, kind: str) -> dict[str, Any]:
        node = cls._node("kinds", kind)
        return node if isinstance(node, dict) else {}

    @classmethod
    def collect_signals(
        cls,
        *,
        pdf_extract: dict[str, Any] | None = None,
        items: list[dict[str, Any]] | None = None,
        extraction_confidence: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []
        signals.extend(cls._detect_conflicting_dimension_notes(pdf_extract))
        signals.extend(
            cls._detect_low_confidence(
                items or [],
                extraction_confidence,
                pdf_extract=pdf_extract,
            )
        )
        signals.extend(
            cls._detect_asserted_ok_under_ambiguity(
                items or [],
                signals,
            )
        )
        return signals

    @classmethod
    def collect_pdf_signals(
        cls,
        pdf_extract: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        return cls._detect_conflicting_dimension_notes(pdf_extract)

    @classmethod
    def should_withhold(
        cls,
        assertion_id: str,
        *,
        pdf_extract: dict[str, Any] | None = None,
        signals: list[dict[str, Any]] | None = None,
    ) -> bool:
        active = signals if signals is not None else cls.collect_pdf_signals(pdf_extract)

        for signal in active:
            policy = cls._policy_for_kind(str(signal.get("kind") or ""))
            withheld = policy.get("withholdAssertions") or []

            if assertion_id in {str(value) for value in withheld}:
                return True

        return False

    @classmethod
    def apply(
        cls,
        items: list[dict[str, Any]],
        signals: list[dict[str, Any]],
        *,
        pdf_extract: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        adjusted = [deepcopy(item) for item in items if isinstance(item, dict)]

        for signal in signals:
            kind = str(signal.get("kind") or "")
            policy = cls._policy_for_kind(kind)
            adjusted = cls._ensure_pending_item(
                adjusted,
                signal,
                policy,
                pdf_extract=pdf_extract,
            )
            adjusted = cls._enrich_items_for_signal(adjusted, signal, policy)
            adjusted = cls._suppress_ok_under_signal(adjusted, signal, policy)

        return adjusted, signals

    @classmethod
    def format_ask_user(
        cls,
        item: dict[str, Any],
        *,
        compact: bool = False,
    ) -> str | None:
        if item.get("ambiguitySuppressed"):
            return None

        ambiguity = item.get("ambiguity")

        if not isinstance(ambiguity, dict):
            return None

        if compact:
            text = ChatDrawingValidationContentService.format(
                "ambiguityIntelligence",
                "askUserCompact",
                whyEscalated=str(ambiguity.get("whyEscalated") or "").strip(),
                systemDidNot=str(ambiguity.get("systemDidNot") or "").strip(),
                askUser=str(ambiguity.get("askUser") or "").strip(),
            ).strip()
            return text or None

        return cls._format_envelope_from_parts(ambiguity) or None

    @classmethod
    def _detect_conflicting_dimension_notes(
        cls,
        pdf_extract: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not isinstance(pdf_extract, dict) or not pdf_extract:
            return []

        from app.domain.services.chat_drawing_dimensions_extraction_service import (
            ChatDrawingDimensionsExtractionService,
        )

        haystack = cls._dimension_note_haystack(pdf_extract)

        if not ChatDrawingDimensionsExtractionService.detect_ambiguous_dimension_notes(
            haystack
        ):
            return []

        detector = cls._detectors().get("conflicting_dimension_notes") or {}
        evidence = (
            ChatDrawingDimensionsExtractionService.summarize_ambiguous_dimension_notes(
                haystack
            )
            or ChatDrawingValidationContentService.evidence("pendingPdf")
        )

        return [
            cls._build_signal(
                detector_id="conflicting_dimension_notes",
                detector=detector if isinstance(detector, dict) else {},
                evidence=evidence,
            )
        ]

    @classmethod
    def _detect_low_confidence(
        cls,
        items: list[dict[str, Any]],
        extraction_confidence: dict[str, Any] | None,
        *,
        pdf_extract: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        from app.domain.services.chat_drawing_extraction_user_escalation_service import (
            ChatDrawingExtractionUserEscalationService,
        )

        detector = cls._detectors().get("extraction_below_threshold") or {}

        if not isinstance(detector, dict):
            return []

        meets = True

        if isinstance(extraction_confidence, dict):
            meets = bool(extraction_confidence.get("meetsThreshold", True))

        escalate = ChatDrawingExtractionUserEscalationService.allows_user_escalation(
            pdf_extract=pdf_extract,
            meets_threshold=meets,
        )

        if not escalate:
            return []

        template_key = str(detector.get("templateKey") or "extraction_confidence")
        pending_confidence = any(
            str(item.get("templateKey") or "") == template_key
            and str(item.get("status") or "") == "pending"
            for item in items
            if isinstance(item, dict)
        )

        if meets and not pending_confidence:
            return []

        score = None
        threshold = None

        if isinstance(extraction_confidence, dict):
            score = extraction_confidence.get("scorePercent")
            threshold = extraction_confidence.get("thresholdPercent")

        evidence_parts = []

        if score is not None and threshold is not None:
            evidence_parts.append(f"score={score}% limiar={threshold}%")

        after_llm = ChatDrawingExtractionUserEscalationService.used_llm_solve(pdf_extract)

        return [
            cls._build_signal(
                detector_id="extraction_below_threshold",
                detector=detector,
                evidence="; ".join(evidence_parts) if evidence_parts else None,
                after_llm=after_llm,
            )
        ]

    @classmethod
    def _detect_asserted_ok_under_ambiguity(
        cls,
        items: list[dict[str, Any]],
        parent_signals: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        detector = cls._detectors().get("asserted_ok_under_ambiguity") or {}

        if not isinstance(detector, dict):
            return []

        parent_ids = {
            str(value)
            for value in (detector.get("parentDetectorIds") or [])
            if str(value).strip()
        }
        parents = [
            signal
            for signal in parent_signals
            if str(signal.get("detectorId") or "") in parent_ids
        ]

        if not parents:
            return []

        kind = str(parents[0].get("kind") or "")
        policy = cls._policy_for_kind(kind)
        suppress_keys = {
            str(value)
            for value in (policy.get("suppressTemplateKeysWhenOk") or [])
            if str(value).strip()
        }

        if not suppress_keys:
            return []

        has_ok = any(
            str(item.get("templateKey") or "") in suppress_keys
            and str(item.get("status") or "") == "ok"
            for item in items
            if isinstance(item, dict)
        )

        if not has_ok:
            return []

        return [
            cls._build_signal(
                detector_id="asserted_ok_under_ambiguity",
                detector=detector,
                evidence=str(parents[0].get("evidence") or ""),
            )
        ]

    @classmethod
    def _build_signal(
        cls,
        *,
        detector_id: str,
        detector: dict[str, Any],
        evidence: str | None = None,
        after_llm: bool = False,
    ) -> dict[str, Any]:
        kind = str(detector.get("kind") or "")
        kind_meta = cls._kind_meta(kind)
        title = str(kind_meta.get("title") or kind)
        why_key = "whyEscalatedAfterLlm" if after_llm else "whyEscalated"
        ask_key = "askUserAfterLlm" if after_llm else "askUser"
        why = str(
            detector.get(why_key) or detector.get("whyEscalated") or ""
        ).strip()
        system_did_not = str(detector.get("systemDidNot") or "").strip()
        ask_user = str(
            detector.get(ask_key)
            or detector.get("askUser")
            or kind_meta.get("defaultAskUser")
            or ""
        ).strip()
        resolve_hint = str(
            ChatDrawingValidationContentService.get(
                "ambiguityIntelligence",
                "defaultResolveHint",
            )
            or ""
        ).strip()
        policy = cls._policy_for_kind(kind)

        ambiguity = {
            "kind": kind,
            "title": title,
            "whyEscalated": why,
            "systemDidNot": system_did_not,
            "askUser": ask_user,
            "resolveHint": resolve_hint,
            "detectorId": detector_id,
            "scope": str(detector.get("scope") or ""),
            "templateKey": str(detector.get("templateKey") or ""),
            "withheld": [
                str(value)
                for value in (policy.get("withholdAssertions") or [])
                if str(value).strip()
            ],
        }

        return {
            "kind": kind,
            "scope": ambiguity["scope"],
            "detectorId": detector_id,
            "evidence": evidence,
            "withheld": ambiguity["withheld"],
            "templateKey": ambiguity["templateKey"],
            "ambiguity": ambiguity,
        }

    @classmethod
    def _format_envelope_from_parts(cls, ambiguity: dict[str, Any]) -> str:
        parts_cfg = cls._node("askUserEnvelopeParts")
        parts_cfg = parts_cfg if isinstance(parts_cfg, dict) else {}
        chunks: list[str] = []

        for key in ("title", "whyEscalated", "systemDidNot", "askUser", "resolveHint"):
            template = str(parts_cfg.get(key) or "").strip()
            value = str(ambiguity.get(key) or "").strip()

            if not value:
                continue

            if template:
                try:
                    chunks.append(template.format(**{key: value}))
                except (KeyError, ValueError):
                    chunks.append(value)
            else:
                chunks.append(value)

        return " ".join(chunks).strip()

    @classmethod
    def _ensure_pending_item(
        cls,
        items: list[dict[str, Any]],
        signal: dict[str, Any],
        policy: dict[str, Any],
        *,
        pdf_extract: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not policy.get("createPending"):
            return items

        template_key = str(signal.get("templateKey") or "").strip()

        if not template_key:
            return items

        for item in items:
            if str(item.get("templateKey") or "") == template_key:
                return items

        pdf_evidence = str(signal.get("evidence") or "").strip() or (
            ChatDrawingValidationContentService.evidence("pendingPdf")
        )
        item = ChatDrawingValidationContentService.item_from_template(
            template_key,
            status="pending",
            pdf_evidence=pdf_evidence,
            api_evidence=ChatDrawingValidationContentService.evidence("dash"),
        )
        item["ambiguity"] = dict(signal.get("ambiguity") or {})
        item["recommendation"] = cls.format_ask_user(item) or item.get("recommendation")
        items.append(item)
        return items

    @classmethod
    def _enrich_items_for_signal(
        cls,
        items: list[dict[str, Any]],
        signal: dict[str, Any],
        policy: dict[str, Any],
    ) -> list[dict[str, Any]]:
        template_key = str(signal.get("templateKey") or "").strip()
        enrich_keys = {
            str(value)
            for value in (policy.get("enrichTemplateKeys") or [])
            if str(value).strip()
        }

        if template_key:
            enrich_keys.add(template_key)

        if not enrich_keys:
            return items

        ambiguity = dict(signal.get("ambiguity") or {})
        envelope = cls._format_envelope_from_parts(ambiguity)

        for item in items:
            key = str(item.get("templateKey") or "")

            if key not in enrich_keys:
                continue

            if str(item.get("status") or "") not in {"pending", "error", "incomplete"}:
                if key != template_key:
                    continue

            item["ambiguity"] = ambiguity

            if envelope:
                item["recommendation"] = envelope

        return items

    @classmethod
    def _dimension_note_haystack(cls, pdf_extract: dict[str, Any]) -> str:
        from app.domain.services.chat_drawing_patterns_service import (
            ChatDrawingPatternsService,
        )

        parts: list[str] = []
        dimensions = pdf_extract.get("dimensions")

        if isinstance(dimensions, dict):
            for key in ("notesText", "rawText"):
                value = dimensions.get(key)

                if value:
                    parts.append(str(value))

        source_metadata = pdf_extract.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            for key in ChatDrawingPatternsService.pdf_haystack_source_metadata_keys():
                value = source_metadata.get(key)

                if value:
                    parts.append(str(value))

        full_text = pdf_extract.get("fullText")

        if full_text:
            parts.append(str(full_text))

        return "\n".join(parts)

    @classmethod
    def _suppress_ok_under_signal(
        cls,
        items: list[dict[str, Any]],
        signal: dict[str, Any],
        policy: dict[str, Any],
    ) -> list[dict[str, Any]]:
        suppress_keys = {
            str(value)
            for value in (policy.get("suppressTemplateKeysWhenOk") or [])
            if str(value).strip()
        }

        if not suppress_keys:
            return items

        status = str(policy.get("suppressStatus") or "not_applicable")
        recommendation = ChatDrawingValidationContentService.get(
            "ambiguityIntelligence",
            "suppressedOkRecommendation",
        )

        for item in items:
            if str(item.get("templateKey") or "") not in suppress_keys:
                continue

            if str(item.get("status") or "") != "ok":
                continue

            item["status"] = status
            item["recommendation"] = recommendation or item.get("recommendation")
            item["ambiguitySuppressed"] = True
            item.pop("ambiguity", None)

        return items
