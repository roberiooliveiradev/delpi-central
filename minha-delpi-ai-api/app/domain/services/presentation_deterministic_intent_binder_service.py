"""Binding determinístico: PresentationIntent + DataProfile → PresentationSpec draft."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import (
    EncodingChannel,
    PresentationIntent,
    PresentationSpec,
)
from app.domain.services.presentation_soft_preference_service import (
    PresentationSoftPreferenceService,
)


class PresentationDeterministicIntentBinderService:
    @classmethod
    def bind(
        cls,
        intent: PresentationIntent,
        profile: PresentationDataProfile,
        *,
        openapi_field_meta: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[PresentationSpec | None, float]:
        """Return (spec_or_none, confidence 0..1)."""
        if profile.row_count <= 0 or not profile.fields:
            return None, 0.0

        field_map = profile.field_map()
        labels = dict(profile.resolved_field_labels.get("labels") or {})
        openapi_field_meta = openapi_field_meta or {}

        dims = list(profile.dimension_candidates)
        measures = list(profile.measure_candidates)

        bound_dims: list[str] = []
        for concept in intent.dimension_concepts:
            hit = cls._match_concept(
                concept,
                candidates=dims,
                labels=labels,
                field_map=field_map,
                openapi_field_meta=openapi_field_meta,
            )
            if hit and hit not in bound_dims:
                bound_dims.append(hit)

        measure = None
        if intent.measure_concept:
            measure = cls._match_concept(
                intent.measure_concept,
                candidates=measures,
                labels=labels,
                field_map=field_map,
                openapi_field_meta=openapi_field_meta,
            )
        if not measure and measures:
            measure = measures[0]

        view = intent.view or "auto"
        mark = intent.mark
        confidence = 0.35

        if intent.dimension_concepts:
            confidence += 0.15 * (len(bound_dims) / max(len(intent.dimension_concepts), 1))
        if intent.measure_concept and measure:
            confidence += 0.25
        elif measure and not intent.measure_concept:
            confidence += 0.1
        if mark:
            confidence += 0.15
        if intent.palette_family:
            confidence += 0.05

        # Default chart axes when mark/view chart without explicit dims.
        # Heatmap: also complete a *partial* bind (1 discriminant) from profile defaults.
        if (view == "chart" or mark) and dims:
            if mark == "heatmap" and len(bound_dims) < 2 and len(dims) >= 2:
                for key in cls._default_heatmap_dims(dims):
                    if key not in bound_dims:
                        bound_dims.append(key)
                    if len(bound_dims) >= 2:
                        break
                if not intent.dimension_concepts:
                    confidence = min(confidence, 0.55)
            elif not bound_dims:
                bound_dims = dims[:2]
                confidence = min(confidence, 0.55)

        encoding: dict[str, EncodingChannel] = {}
        if mark == "heatmap":
            if len(bound_dims) >= 2 and measure:
                encoding = {
                    "x": EncodingChannel(field=bound_dims[0], type="nominal"),
                    "y": EncodingChannel(field=bound_dims[1], type="nominal"),
                    "color": EncodingChannel(
                        field=measure,
                        type="quantitative",
                        scale=intent.palette_family or "sequential-blue",
                    ),
                }
                confidence = max(confidence, 0.7)
            else:
                return None, confidence
        elif view == "chart" or mark:
            if bound_dims:
                encoding["x"] = EncodingChannel(field=bound_dims[0], type="nominal")
            if measure:
                encoding["y"] = EncodingChannel(field=measure, type="quantitative")
            if not encoding:
                return None, confidence
        elif view == "table":
            fields = tuple(
                item.key
                for item in profile.fields
                if not item.sensitive
            )[:12]
            draft = PresentationSpec(
                view="table",
                fields=fields,
                labels={key: labels[key] for key in fields if key in labels},
                formats={
                    key: str(item.format)
                    for key, item in field_map.items()
                    if item.format and key in fields
                },
                palette_family=intent.palette_family,
                provenance="DETERMINISTIC",
            )
            return (
                PresentationSoftPreferenceService.apply(draft, profile=profile),
                max(confidence, 0.6),
            )

        if not encoding and view not in {"kpi", "text", "tree", "dashboard"}:
            return None, confidence

        draft = PresentationSpec(
            view="chart" if (view == "chart" or mark) else (view or "auto"),
            mark=mark,
            encoding=encoding,
            labels={
                channel.field: labels[channel.field]
                for channel in encoding.values()
                if channel.field in labels
            },
            formats={
                channel.field: str(field_map[channel.field].format)
                for channel in encoding.values()
                if channel.field in field_map and field_map[channel.field].format
            },
            palette_family=intent.palette_family,
            legend_visible=False if mark == "heatmap" else None,
            provenance="DETERMINISTIC",
        )
        return (
            PresentationSoftPreferenceService.apply(draft, profile=profile),
            min(1.0, confidence),
        )

    @classmethod
    def _default_heatmap_dims(cls, dims: list[str]) -> list[str]:
        """Prefer code-like / matrix-friendly dims over free-text descriptions."""
        preferred_order = (
            "product_code",
            "warehouse",
            "work_center",
            "branch",
            "production_order",
            "shift",
            "machine",
        )
        ranked = [key for key in preferred_order if key in dims]
        for key in dims:
            if key in ranked:
                continue
            # Skip long free-text description fields when better dims exist.
            if key.endswith("_description") or key in {"description", "product_description"}:
                continue
            ranked.append(key)
        if len(ranked) < 2:
            ranked = list(dims)
        return ranked[:2]

    @classmethod
    def _match_concept(
        cls,
        concept: str,
        *,
        candidates: list[str],
        labels: dict[str, str],
        field_map: dict[str, Any],
        openapi_field_meta: dict[str, dict[str, Any]],
    ) -> str | None:
        # Slash inside one matrix axis token = OR aliases for the same slot.
        aliases_or = [
            part.strip()
            for part in re.split(r"\s*/\s*", str(concept or "").strip())
            if part.strip()
        ] or [str(concept or "").strip()]

        for alias in aliases_or:
            hit = cls._match_single_concept(
                alias,
                candidates=candidates,
                labels=labels,
                field_map=field_map,
                openapi_field_meta=openapi_field_meta,
            )
            if hit is None:
                continue
            # Prefer earlier alias on ties; first discriminant hit wins the slot.
            return hit
        return None

    @classmethod
    def _match_single_concept(
        cls,
        concept: str,
        *,
        candidates: list[str],
        labels: dict[str, str],
        field_map: dict[str, Any],
        openapi_field_meta: dict[str, dict[str, Any]],
    ) -> str | None:
        needle = cls._normalize(concept)
        if not needle:
            return None
        aliases = {
            "produto": "product",
            "deposito": "warehouse",
            "armazem": "warehouse",
            "filial": "branch",
            "maquina": "machine",
            "turno": "shift",
            "producao": "output",
            "quantidade planejada": "planned qty",
            "qtd planejada": "planned qty",
        }
        expanded = aliases.get(needle, needle)

        scored: list[tuple[float, str]] = []
        for key in candidates:
            score = 0.0
            key_norm = cls._normalize(key)
            label_norm = cls._normalize(labels.get(key, ""))
            meta = openapi_field_meta.get(key) or {}
            title_norm = cls._normalize(str(meta.get("title") or ""))
            desc_norm = cls._normalize(str(meta.get("description") or ""))

            if needle == key_norm or needle == label_norm or expanded == key_norm:
                score = 1.0
            elif needle in key_norm or key_norm in needle or expanded in key_norm:
                score = 0.85
            elif needle in label_norm or label_norm in needle:
                score = 0.9
            elif title_norm and (
                needle in title_norm or title_norm in needle or expanded in title_norm
            ):
                score = 0.88
            elif desc_norm and (needle in desc_norm or expanded in desc_norm):
                score = 0.75

            needle_tokens = set(needle.split()) | set(expanded.split())
            corpus = set((label_norm or key_norm).split()) | set(desc_norm.split()) | set(
                title_norm.split()
            )
            if needle_tokens and corpus:
                overlap = len(needle_tokens & corpus) / len(needle_tokens)
                score = max(score, 0.55 * overlap)
            compact_needle = needle.replace(" ", "")
            compact_label = (label_norm or key_norm).replace(" ", "")
            compact_expanded = expanded.replace(" ", "")
            if compact_needle and compact_needle[:6] in compact_label:
                score = max(score, 0.8)
            if compact_expanded and compact_expanded[:6] in key_norm.replace(" ", ""):
                score = max(score, 0.82)
            if compact_needle and compact_needle[:6] in key_norm.replace(" ", ""):
                score = max(score, 0.78)

            if score > 0:
                scored.append((score, key))

        if not scored:
            return None
        scored.sort(key=lambda item: (-item[0], item[1]))
        best_score, best_key = scored[0]
        return best_key if best_score >= 0.55 else None

    @classmethod
    def _normalize(cls, value: str) -> str:
        text = str(value or "").strip().lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(char for char in text if not unicodedata.combining(char))
        text = text.replace("_", " ")
        text = re.sub(r"[^a-z0-9 ]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()
