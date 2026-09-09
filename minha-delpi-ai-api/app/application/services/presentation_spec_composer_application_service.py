"""Shadow / canary LLM composer for PresentationSpec (application layer)."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from app.domain.entities.presentation_spec import (
    PRESENTATION_SPEC_JSON_SCHEMA,
    PresentationSpec,
)
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.presentation_spec_validator_service import (
    PresentationSpecValidatorService,
)

logger = logging.getLogger(__name__)

_CANARY_ENV = "PRESENTATION_COMPOSER_CANARY"
_SHADOW_ENV = "PRESENTATION_COMPOSER_SHADOW"


class PresentationSpecComposerApplicationService:
    """Optional LLM proposal — never receives raw payload rows."""

    def __init__(self, llm: LlmGatewayPort | None = None) -> None:
        self._llm = llm

    @classmethod
    def shadow_enabled(cls) -> bool:
        return str(os.getenv(_SHADOW_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def canary_enabled(cls) -> bool:
        return str(os.getenv(_CANARY_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}

    def compose(
        self,
        *,
        intent: dict[str, Any],
        profile: dict[str, Any],
        user_message_excerpt: str | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        if self._llm is None:
            return {
                "ok": False,
                "reason": "llm_unavailable",
                "latencyMs": 0,
            }

        from app.domain.services.presentation_composer_prompt_content_service import (
            PresentationComposerPromptContentService,
        )

        prompt = self._build_prompt(intent=intent, profile=profile, excerpt=user_message_excerpt)
        messages = [
            {
                "role": "system",
                "content": PresentationComposerPromptContentService.system_prompt(),
            },
            {"role": "user", "content": prompt},
        ]

        raw = ""
        repair_used = False
        try:
            raw = self._llm.generate(messages)
        except Exception as exc:  # noqa: BLE001 — bounded fallback
            logger.warning("presentation_composer_llm_failed: %s", exc)
            return {
                "ok": False,
                "reason": "llm_error",
                "latencyMs": round((time.perf_counter() - started) * 1000, 2),
            }

        parsed = self._parse_json(raw)
        if not parsed:
            repaired = self._repair_once(
                messages,
                previous=raw,
                errors=["invalid_json"],
            )
            repair_used = True
            if repaired:
                raw = repaired
                parsed = self._parse_json(raw)
        if not parsed:
            return {
                "ok": False,
                "reason": "invalid_json",
                "latencyMs": round((time.perf_counter() - started) * 1000, 2),
                "repairUsed": repair_used,
            }

        # Rebuild a minimal profile-like object for validator membership.
        from app.domain.services.presentation_data_profile_builder_service import (
            PresentationDataProfileBuilderService,
        )

        # Profile already has field stats — reconstruct from profile dict fields.
        rows = self._synthetic_rows_from_profile(profile)
        data_profile = PresentationDataProfileBuilderService.build(
            rows,
            label_bundle=profile.get("resolvedFieldLabels"),
        )
        validation = PresentationSpecValidatorService.validate(
            parsed,
            profile=data_profile,
            user_explicit=True,
        )
        if not validation.ok and not repair_used:
            repaired = self._repair_once(
                messages,
                previous=json.dumps(parsed, ensure_ascii=False),
                errors=validation.errors,
            )
            repair_used = True
            if repaired:
                reparsed = self._parse_json(repaired)
                if reparsed:
                    parsed = reparsed
                    validation = PresentationSpecValidatorService.validate(
                        parsed,
                        profile=data_profile,
                        user_explicit=True,
                    )
        if validation.ok and validation.spec is not None:
            from app.domain.services.presentation_soft_preference_service import (
                PresentationSoftPreferenceService,
            )

            softened = PresentationSoftPreferenceService.apply(
                validation.spec,
                profile=data_profile,
            )
            if softened is not None:
                from dataclasses import replace

                validation.spec = replace(softened, provenance="COMPOSER")
        latency = round((time.perf_counter() - started) * 1000, 2)
        return {
            "ok": validation.ok,
            "reason": None if validation.ok else "validation_failed",
            "errors": validation.errors,
            "spec": validation.spec.as_dict() if validation.spec else None,
            "latencyMs": latency,
            "repairUsed": repair_used,
            "schemaVersion": PRESENTATION_SPEC_JSON_SCHEMA.get("properties", {})
            .get("version", {})
            .get("const"),
        }

    def apply_shadow_or_canary(self, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return
        summary = metadata.get("presentationIntelligence")
        intent = metadata.get("presentationIntent")
        profile = metadata.get("presentationDataProfile")
        if not isinstance(summary, dict) or not isinstance(profile, dict):
            return

        from app.domain.services.presentation_intelligence_orchestrator_service import (
            PresentationIntelligenceOrchestratorService,
        )

        constraints = metadata.get("presentationConstraints")
        invoke = PresentationIntelligenceOrchestratorService.should_invoke_composer(
            summary,
            intent if isinstance(intent, dict) else None,
            profile=profile,
            constraints=constraints if isinstance(constraints, dict) else None,
        )
        shadow_on = self.shadow_enabled()
        canary_on = self.canary_enabled()
        metadata["presentationComposerPolicy"] = {
            "invoke": invoke,
            "bindConfidence": summary.get("bindConfidence"),
            "needsComposer": summary.get("needsComposer"),
            "specApplied": summary.get("specApplied"),
            "shadowEnabled": shadow_on,
            "canaryEnabled": canary_on,
        }
        if not invoke:
            metadata["presentationComposerPolicy"]["decision"] = "skip"
            return

        if not (shadow_on or canary_on):
            metadata["presentationComposerPolicy"]["decision"] = "invoke_flag_off"
            return

        metadata["presentationComposerPolicy"]["decision"] = "invoke"
        result = self.compose(
            intent=intent if isinstance(intent, dict) else {},
            profile=profile,
            user_message_excerpt=str(metadata.get("userMessage") or "")[:400],
        )
        latency_ms = result.get("latencyMs")
        repair_used = bool(result.get("repairUsed"))
        spec_summary = self._spec_summary(result.get("spec"))
        metadata["presentationComposerPolicy"]["latencyMs"] = latency_ms
        metadata["presentationComposerPolicy"]["repairUsed"] = repair_used
        metadata["presentationComposerShadow"] = {
            "ok": result.get("ok"),
            "reason": result.get("reason"),
            "errors": result.get("errors"),
            "latencyMs": latency_ms,
            "repairUsed": repair_used,
            "specSummary": spec_summary,
        }
        if canary_on and result.get("ok") and result.get("spec"):
            metadata["presentationComposerAuthoritative"] = True
            metadata["presentationComposerSpec"] = result["spec"]
            metadata["presentationComposerPolicy"]["fallback"] = False
        else:
            # Keep deterministic Spec; composer failure never clears slots.
            metadata["presentationComposerPolicy"]["fallback"] = True
            metadata["presentationComposerPolicy"]["fallbackReason"] = (
                result.get("reason") or "composer_not_authoritative"
            )
    @classmethod
    def finalize_presentation_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        llm: LlmGatewayPort | None = None,
    ) -> None:
        """Application entry: domain finalize + optional shadow/canary composer."""
        from app.domain.services.chat_presentation_render_pipeline_service import (
            ChatPresentationRenderPipelineService,
        )
        from app.domain.services.presentation_intelligence_orchestrator_service import (
            PresentationIntelligenceOrchestratorService,
        )

        ChatPresentationRenderPipelineService.finalize(metadata)

        if not (cls.shadow_enabled() or cls.canary_enabled()):
            return

        service = cls(llm=llm)
        service.apply_shadow_or_canary(metadata)
        if metadata.get("presentationComposerAuthoritative") and metadata.get(
            "presentationComposerSpec"
        ):
            user_message = metadata.get("userMessage") or metadata.get("originalUserMessage")
            PresentationIntelligenceOrchestratorService.apply_before_render_plan(
                metadata,
                user_message=str(user_message) if user_message else None,
                composer_enabled=True,
                composer_spec=metadata.get("presentationComposerSpec"),
            )
            from app.domain.services.chat_presentation_render_plan_service import (
                ChatPresentationRenderPlanService,
            )

            ChatPresentationRenderPlanService.build(metadata)

    def _repair_once(
        self,
        messages: list[dict[str, str]],
        *,
        previous: str,
        errors: list[str],
    ) -> str | None:
        if self._llm is None:
            return None
        from app.domain.services.presentation_composer_prompt_content_service import (
            PresentationComposerPromptContentService,
        )

        repair_messages = list(messages) + [
            {
                "role": "user",
                "content": PresentationComposerPromptContentService.repair_prompt(
                    errors=errors,
                    previous=previous,
                ),
            }
        ]
        try:
            return self._llm.generate(repair_messages)
        except Exception as exc:  # noqa: BLE001
            logger.warning("presentation_composer_repair_failed: %s", exc)
            return None

    @classmethod
    def _build_prompt(
        cls,
        *,
        intent: dict[str, Any],
        profile: dict[str, Any],
        excerpt: str | None,
    ) -> str:
        return json.dumps(
            cls.build_compose_payload(
                intent=intent,
                profile=profile,
                excerpt=excerpt,
            ),
            ensure_ascii=False,
        )

    @classmethod
    def build_compose_payload(
        cls,
        *,
        intent: dict[str, Any],
        profile: dict[str, Any],
        excerpt: str | None,
    ) -> dict[str, Any]:
        """Prompt shape for LLM — profile stats only; never raw rows or sensitive keys."""
        sensitive_keys = {
            str(item.get("key") or "").strip()
            for item in (profile.get("fields") or [])
            if isinstance(item, dict) and item.get("sensitive") and str(item.get("key") or "").strip()
        }
        safe_fields = []
        for item in profile.get("fields") or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if not key or key in sensitive_keys or item.get("sensitive"):
                continue
            safe_fields.append(
                {
                    "key": key,
                    "semanticType": item.get("semanticType"),
                    "cardinalityBand": item.get("cardinalityBand"),
                    "displayLabel": item.get("displayLabel"),
                    "isDimensionCandidate": item.get("isDimensionCandidate"),
                    "isMeasureCandidate": item.get("isMeasureCandidate"),
                }
            )

        def _safe_candidates(values: Any) -> list[str]:
            if not isinstance(values, list):
                return []
            return [
                str(item).strip()
                for item in values
                if str(item or "").strip() and str(item).strip() not in sensitive_keys
            ]

        from app.domain.services.presentation_composer_policy_service import (
            PresentationComposerPolicyService,
        )
        from app.domain.services.presentation_composer_prompt_content_service import (
            PresentationComposerPromptContentService,
        )

        excerpt_limit = PresentationComposerPolicyService.max_user_excerpt_chars()
        palettes = PresentationComposerPromptContentService.allowed_palette_families()
        rules = PresentationComposerPromptContentService.rules()
        return {
            "intent": intent if isinstance(intent, dict) else {},
            "dimensionCandidates": _safe_candidates(profile.get("dimensionCandidates")),
            "measureCandidates": _safe_candidates(profile.get("measureCandidates")),
            "fields": safe_fields,
            "userExcerpt": str(excerpt or "")[:excerpt_limit],
            "allowedPaletteFamilies": palettes
            or [
                "brand",
                "sequential-blue",
                "cool",
                "warm",
                "diverging-status",
                "status",
            ],
            "rules": rules
            or [
                "encoding.field must be in candidates",
                "heatmap requires x,y discriminant + color measure",
                "labels map keys must match field keys",
                "paletteFamily semantic only",
                "never invent hex CSS or JavaScript",
            ],
            "knobsByView": PresentationComposerPromptContentService.knobs_by_view(),
        }
    @classmethod
    def _spec_summary(cls, spec: dict[str, Any] | None) -> dict[str, Any] | None:
        """Telemetry-safe Spec digest — no rows, no prompt."""
        if not isinstance(spec, dict):
            return None
        fields = spec.get("fields")
        encoding = spec.get("encoding") if isinstance(spec.get("encoding"), dict) else {}
        return {
            "view": spec.get("view"),
            "mark": spec.get("mark"),
            "provenance": spec.get("provenance"),
            "paletteFamily": spec.get("paletteFamily"),
            "fieldCount": len(fields) if isinstance(fields, list) else None,
            "encodingFieldCount": len(encoding),
        }

    @classmethod
    def _parse_json(cls, raw: str) -> dict[str, Any] | None:
        text = str(raw or "").strip()
        if not text:
            return None
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if fence:
            text = fence.group(1)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                return None
            try:
                payload = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return payload if isinstance(payload, dict) else None

    @classmethod
    def _synthetic_rows_from_profile(cls, profile: dict[str, Any]) -> list[dict[str, Any]]:
        """Build minimal rows for validator membership without real payload."""
        fields = profile.get("fields") or []
        if not isinstance(fields, list) or not fields:
            return []
        row: dict[str, Any] = {}
        for item in fields:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if not key:
                continue
            semantic = item.get("semanticType")
            if semantic == "quantitative":
                row[key] = 1
            elif semantic == "boolean":
                row[key] = False
            else:
                row[key] = f"{key}_a"
        # Duplicate rows with varied categories when possible.
        rows = [dict(row)]
        alt = dict(row)
        for item in fields:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "")
            if item.get("isDimensionCandidate") and isinstance(alt.get(key), str):
                alt[key] = f"{key}_b"
        rows.append(alt)
        return rows
