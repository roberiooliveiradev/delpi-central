"""Orquestra Presentation Intelligence (profile → labels → intent → bind → validate → compile).

Domain-pure quanto a regras; composição LLM fica em application (shadow/canary).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.domain.entities.presentation_spec import PresentationSpec
from app.domain.services.chat_field_label_resolution_pipeline_service import (
    ChatFieldLabelResolutionPipelineService,
)
from app.domain.services.chat_presentation_field_normalization_service import (
    ChatPresentationFieldNormalizationService,
)
from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)
from app.domain.services.presentation_deterministic_intent_binder_service import (
    PresentationDeterministicIntentBinderService,
)
from app.domain.services.presentation_constraints_extractor_service import (
    PresentationConstraintsExtractorService,
)
from app.domain.services.presentation_intent_extractor_service import (
    PresentationIntentExtractorService,
)
from app.domain.services.presentation_spec_compiler_service import (
    PresentationSpecCompilerService,
)
from app.domain.services.presentation_spec_validator_service import (
    PresentationSpecValidatorService,
)

logger = logging.getLogger(__name__)

# Confidence below this → optional composer may help (HIPOTESE_A_VALIDAR).
_BIND_CONFIDENCE_THRESHOLD = 0.72


class PresentationIntelligenceOrchestratorService:
    @classmethod
    def apply_before_render_plan(
        cls,
        metadata: dict[str, Any],
        *,
        user_message: str | None = None,
        openapi_field_meta: dict[str, dict[str, Any]] | None = None,
        composer_spec: PresentationSpec | dict[str, Any] | None = None,
        composer_enabled: bool = False,
    ) -> dict[str, Any]:
        """Mutates metadata; returns observability summary."""
        if not isinstance(metadata, dict):
            return {"skipped": True}

        started = time.perf_counter()
        rows = cls._extract_rows(metadata)
        if not rows:
            return {"skipped": True, "reason": "no_tabular_rows"}

        field_keys = cls._collect_keys(metadata, rows)

        path = str(metadata.get("path") or "")
        try:
            bundle = ChatFieldLabelResolutionPipelineService.resolve(
                field_keys,
                path=path,
                openapi_labels=cls._openapi_titles(openapi_field_meta),
                enable_discovery=False,
            )
        except Exception:
            from app.domain.entities.field_label_bundle import FieldLabelBundle
            from app.domain.services.external_actions.external_action_column_label_service import (
                ExternalActionColumnLabelService,
            )

            labels = {
                key: ExternalActionColumnLabelService._humanize_field_key(key)
                for key in field_keys
            }
            bundle = FieldLabelBundle(
                labels=labels,
                formats={},
                source_by_key={key: "DETERMINISTIC_HUMANIZER" for key in field_keys},
            )
        metadata["resolvedFieldLabels"] = bundle.as_metadata()

        profile = PresentationDataProfileBuilderService.build(
            rows,
            label_bundle=bundle.as_metadata(),
            openapi_field_meta=openapi_field_meta,
        )
        metadata["presentationDataProfile"] = profile.as_dict()

        constraints = metadata.get("presentationConstraints")
        if not isinstance(constraints, dict) or not constraints:
            extracted = PresentationConstraintsExtractorService.extract(user_message)
            if extracted:
                constraints = extracted
                metadata["presentationConstraints"] = dict(extracted)

        requested = None
        decision = metadata.get("presentationDecision")
        if isinstance(decision, dict):
            requested = decision.get("requestedPresentation") or decision.get("selected")
        requested = requested or metadata.get("requestedPresentation")

        intent = PresentationIntentExtractorService.extract(
            user_message,
            requested_presentation=str(requested) if requested else None,
        )
        metadata["presentationIntent"] = intent.as_dict()

        spec, confidence = PresentationDeterministicIntentBinderService.bind(
            intent,
            profile,
            openapi_field_meta=openapi_field_meta,
        )

        composer_invoked = False
        composer_reason = None
        if composer_spec and composer_enabled:
            composer_invoked = True
            composer_reason = "provided_shadow_or_canary"
            candidate = (
                composer_spec
                if isinstance(composer_spec, PresentationSpec)
                else PresentationSpec.from_dict(composer_spec)
            )
            if candidate is not None:
                from dataclasses import replace

                spec = replace(candidate, provenance="COMPOSER")
                confidence = max(confidence, 0.8)

        unmet_intent = None
        validation = None
        if spec is not None:
            validation = PresentationSpecValidatorService.validate(
                spec,
                profile=profile,
                user_explicit=bool(intent.mark or intent.dimension_concepts),
            )
            if validation.ok and validation.spec:
                PresentationSpecCompilerService.compile_into_metadata(
                    metadata,
                    spec=validation.spec,
                    profile=profile,
                    unmet_intent=validation.unmet_intent,
                )
            else:
                unmet_intent = validation.unmet_intent
                if unmet_intent:
                    decision = metadata.setdefault("presentationDecision", {})
                    if isinstance(decision, dict):
                        decision["unmetIntent"] = unmet_intent
        elif intent.mark == "heatmap":
            unmet_intent = "heatmap_not_materializable"
            decision = metadata.setdefault("presentationDecision", {})
            if isinstance(decision, dict):
                decision["unmetIntent"] = unmet_intent

        # Ensure labels applied even without spec (P0).
        try:
            ChatPresentationFieldNormalizationService.normalize_metadata(
                metadata,
                path=path,
                openapi_labels=cls._openapi_titles(openapi_field_meta),
                enable_discovery=False,
            )
        except Exception:
            logger.debug("presentation_label_normalize_skipped", exc_info=True)

        applied_spec = validation.spec if validation and validation.ok else None
        if isinstance(constraints, dict) and constraints.get("preferCanvas"):
            from app.domain.services.presentation_compilers.presentation_delivery_compiler_service import (
                PresentationDeliveryCompilerService,
            )

            PresentationDeliveryCompilerService.apply(metadata, spec=applied_spec)

        decision = metadata.get("presentationDecision")
        final_unmet = unmet_intent
        if isinstance(decision, dict):
            decision_unmet = str(decision.get("unmetIntent") or "").strip()
            if decision_unmet:
                final_unmet = decision_unmet

        from app.domain.services.presentation_unmet_intent_notice_service import (
            PresentationUnmetIntentNoticeService,
        )

        PresentationUnmetIntentNoticeService.apply(
            metadata,
            unmet_intent=final_unmet,
        )

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        summary = {
            "profileHash": profile.profile_hash,
            "bindConfidence": confidence,
            "composerInvoked": composer_invoked,
            "composerReason": composer_reason,
            # Composer only when we could not already apply a valid deterministic spec.
            "needsComposer": not (validation and validation.ok)
            and confidence < _BIND_CONFIDENCE_THRESHOLD
            and cls._looks_ambiguous(intent, profile),
            "specApplied": bool(validation and validation.ok),
            "unmetIntent": final_unmet,
            "presentation_profile_build_ms": elapsed_ms,
            "dimensionCandidates": list(profile.dimension_candidates),
            "measureCandidates": list(profile.measure_candidates),
        }
        if isinstance(constraints, dict) and constraints:
            summary["constraintsPresent"] = True
        metadata["presentationIntelligence"] = summary
        logger.info(
            "presentation_intelligence_applied",
            extra={
                "profileHash": profile.profile_hash,
                "bindConfidence": confidence,
                "composerInvoked": composer_invoked,
                "specApplied": summary["specApplied"],
                "latencyMs": elapsed_ms,
            },
        )
        return summary

    @classmethod
    def should_invoke_composer(
        cls,
        summary: dict[str, Any] | None,
        intent: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> bool:
        from app.domain.services.presentation_composer_policy_service import (
            PresentationComposerPolicyService,
        )

        return PresentationComposerPolicyService.should_invoke(
            summary=summary,
            intent=intent,
            profile=profile,
            constraints=constraints,
        )

    @classmethod
    def _looks_ambiguous(cls, intent: Any, profile: Any) -> bool:
        dims = len(getattr(profile, "dimension_candidates", ()) or ())
        measures = len(getattr(profile, "measure_candidates", ()) or ())
        if dims >= 2 and measures >= 2:
            return True
        if getattr(intent, "mark", None) == "heatmap" and dims >= 2:
            return True
        if getattr(intent, "dimension_concepts", None) or getattr(intent, "measure_concept", None):
            return True
        if getattr(intent, "palette_family", None):
            return True
        return False

    @classmethod
    def _extract_rows(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("chartPresentation", "tablePresentation", "presentation"):
            presentation = metadata.get(key)
            if not isinstance(presentation, dict):
                continue
            if presentation.get("type") == "chart":
                data = presentation.get("data")
                if isinstance(data, list):
                    return [row for row in data if isinstance(row, dict)]
            if presentation.get("type") == "table":
                rows = presentation.get("rows")
                if isinstance(rows, list):
                    return [row for row in rows if isinstance(row, dict)]
        tables = metadata.get("tablePresentations")
        if isinstance(tables, list) and tables and isinstance(tables[0], dict):
            rows = tables[0].get("rows")
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
        return []

    @classmethod
    def _collect_keys(
        cls,
        metadata: dict[str, Any],
        rows: list[dict[str, Any]],
    ) -> list[str]:
        keys: list[str] = []
        seen: set[str] = set()
        if rows:
            for key in rows[0].keys():
                token = str(key).strip()
                if token and token not in seen:
                    seen.add(token)
                    keys.append(token)
        for key in ChatPresentationFieldNormalizationService.collect_field_keys(metadata):
            token = str(key).strip()
            if token and token not in seen:
                seen.add(token)
                keys.append(token)
        return keys

    @classmethod
    def _openapi_titles(
        cls,
        openapi_field_meta: dict[str, dict[str, Any]] | None,
    ) -> dict[str, str] | None:
        if not openapi_field_meta:
            return None
        labels: dict[str, str] = {}
        for key, meta in openapi_field_meta.items():
            if not isinstance(meta, dict):
                continue
            title = str(meta.get("title") or "").strip()
            if title:
                labels[key] = title
        return labels or None
