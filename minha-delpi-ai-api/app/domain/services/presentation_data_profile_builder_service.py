"""Constrói PresentationDataProfile a partir de rows tabulares + labels resolvidos."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.domain.entities.presentation_data_profile import (
    PresentationDataProfile,
    PresentationFieldProfile,
)

_SAMPLE_CAP = 24

_TEMPORAL_HINTS = (
    "period",
    "periodo",
    "período",
    "month",
    "mes",
    "mês",
    "year",
    "ano",
    "date",
    "data",
    "week",
    "semana",
    "day",
    "dia",
    "timestamp",
    "created_at",
    "updated_at",
    "hora",
    "time",
)

_IDENTIFIER_HINTS = (
    "code",
    "codigo",
    "código",
    "id",
    "sku",
    "serial",
    "lote",
    "batch",
    "op",
    "order",
    "pedido",
)

_MEASURE_HINTS = (
    "qty",
    "qtd",
    "quantity",
    "quantidade",
    "amount",
    "valor",
    "price",
    "preco",
    "preço",
    "rate",
    "taxa",
    "pct",
    "percent",
    "total",
    "sum",
    "avg",
    "efficiency",
    "eficiencia",
    "eficiência",
)

_SENSITIVE_HINTS = (
    "cpf",
    "cnpj",
    "email",
    "password",
    "senha",
    "token",
    "secret",
    "card",
    "telefone",
    "phone",
    "rg",
)

# Bands: constant=1, low<=12, medium<=64, high>64 (HIPOTESE — medido em F0 corpus)
_LOW_MAX = 12
_MEDIUM_MAX = 64


class PresentationDataProfileBuilderService:
    @classmethod
    def build(
        cls,
        rows: list[dict[str, Any]] | None,
        *,
        label_bundle: dict[str, Any] | None = None,
        openapi_field_meta: dict[str, dict[str, Any]] | None = None,
    ) -> PresentationDataProfile:
        safe_rows = [row for row in (rows or []) if isinstance(row, dict)]
        sample = safe_rows[:_SAMPLE_CAP]
        labels = {}
        formats = {}
        sources = {}
        if isinstance(label_bundle, dict):
            labels = dict(label_bundle.get("labels") or {})
            formats = dict(label_bundle.get("formats") or {})
            sources = dict(label_bundle.get("sourceByKey") or {})

        if not sample:
            return PresentationDataProfile(
                row_count=0,
                sampled_row_count=0,
                profile_hash=cls._hash({"rowCount": 0}),
                resolved_field_labels=dict(label_bundle or {}),
            )

        keys = list(sample[0].keys())
        fields: list[PresentationFieldProfile] = []

        for key in keys:
            fields.append(
                cls._profile_field(
                    key,
                    sample,
                    row_count=len(safe_rows),
                    labels=labels,
                    formats=formats,
                    sources=sources,
                    openapi_meta=(openapi_field_meta or {}).get(key),
                )
            )

        dimension_candidates = tuple(
            item.key
            for item in fields
            if item.is_dimension_candidate and not item.is_constant
        )
        measure_candidates = tuple(
            item.key for item in fields if item.is_measure_candidate
        )
        temporal_candidates = tuple(
            item.key for item in fields if item.semantic_type == "temporal"
        )

        profile = PresentationDataProfile(
            row_count=len(safe_rows),
            sampled_row_count=len(sample),
            fields=tuple(fields),
            dimension_candidates=dimension_candidates,
            measure_candidates=measure_candidates,
            temporal_candidates=temporal_candidates,
            profile_hash="",
            resolved_field_labels=dict(label_bundle or {}),
        )
        return PresentationDataProfile(
            row_count=profile.row_count,
            sampled_row_count=profile.sampled_row_count,
            fields=profile.fields,
            dimension_candidates=profile.dimension_candidates,
            measure_candidates=profile.measure_candidates,
            temporal_candidates=profile.temporal_candidates,
            profile_hash=cls._hash(profile.as_dict()),
            resolved_field_labels=profile.resolved_field_labels,
        )

    @classmethod
    def _profile_field(
        cls,
        key: str,
        sample: list[dict[str, Any]],
        *,
        row_count: int,
        labels: dict[str, str],
        formats: dict[str, str],
        sources: dict[str, str],
        openapi_meta: dict[str, Any] | None,
    ) -> PresentationFieldProfile:
        values = [row.get(key) for row in sample]
        non_null = [value for value in values if value is not None and value != ""]
        null_rate = 1.0 - (len(non_null) / max(len(sample), 1))
        unique = {cls._normalize_value(value) for value in non_null}
        cardinality = len(unique)
        is_constant = cardinality <= 1
        primitive = cls._primitive_type(non_null[0] if non_null else None)
        semantic = cls._semantic_type(
            key,
            primitive=primitive,
            cardinality=cardinality,
            openapi_meta=openapi_meta,
            sample_values=non_null[:5],
        )
        band = cls._cardinality_band(cardinality, is_constant=is_constant)
        sensitive = cls._is_sensitive(key)
        is_measure = (
            semantic == "quantitative"
            and not is_constant
            and not sensitive
        )
        is_dimension = (
            semantic in {"nominal", "ordinal", "identifier", "temporal"}
            and not is_constant
            and not sensitive
        )
        if semantic == "identifier" and cardinality > _MEDIUM_MAX:
            # High-cardinality IDs are poor heatmap/legend dims.
            is_dimension = False

        min_value = None
        max_value = None
        if primitive == "number" and non_null:
            nums = [float(value) for value in non_null if cls._is_number(value)]
            if nums:
                min_value = min(nums)
                max_value = max(nums)

        return PresentationFieldProfile(
            key=key,
            primitive_type=primitive,
            semantic_type=semantic,
            cardinality=cardinality if row_count <= _SAMPLE_CAP else max(cardinality, 0),
            cardinality_band=band,
            null_rate=round(null_rate, 4),
            is_constant=is_constant,
            is_dimension_candidate=is_dimension,
            is_measure_candidate=is_measure,
            sensitive=sensitive,
            display_label=str(labels.get(key) or "").strip() or None,
            format=str(formats.get(key) or "").strip() or None,
            label_source=cls._normalize_label_source(sources.get(key)),
            min_value=min_value,
            max_value=max_value,
        )

    @classmethod
    def _semantic_type(
        cls,
        key: str,
        *,
        primitive: str,
        cardinality: int,
        openapi_meta: dict[str, Any] | None,
        sample_values: list[Any],
    ) -> str:
        token = str(key or "").lower()
        openapi_format = str((openapi_meta or {}).get("format") or "").lower()
        if openapi_format in {"date", "date-time", "time"}:
            return "temporal"
        if primitive == "boolean":
            return "boolean"
        if any(hint in token for hint in _TEMPORAL_HINTS) or openapi_format:
            if any(hint in token for hint in _TEMPORAL_HINTS):
                return "temporal"
        if primitive == "number":
            if any(hint in token for hint in _TEMPORAL_HINTS) and "year" in token:
                return "ordinal"
            if any(hint in token for hint in _MEASURE_HINTS) or cardinality > 1:
                return "quantitative"
            return "quantitative"
        if primitive == "string":
            if any(hint in token for hint in _IDENTIFIER_HINTS):
                return "identifier"
            if cls._samples_look_temporal(sample_values):
                return "temporal"
            return "nominal"
        return "unknown"

    @classmethod
    def _samples_look_temporal(cls, values: list[Any]) -> bool:
        hits = 0
        for value in values:
            text = str(value or "")
            if re.search(r"\d{4}-\d{2}", text) or re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", text):
                hits += 1
        return hits >= max(1, len(values) // 2) if values else False

    @classmethod
    def _cardinality_band(cls, cardinality: int, *, is_constant: bool) -> str:
        if is_constant or cardinality <= 1:
            return "constant"
        if cardinality <= _LOW_MAX:
            return "low"
        if cardinality <= _MEDIUM_MAX:
            return "medium"
        return "high"

    @classmethod
    def _primitive_type(cls, value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return "number"
        if isinstance(value, str):
            return "string"
        if value is None:
            return "null"
        return "unknown"

    @classmethod
    def _is_number(cls, value: Any) -> bool:
        try:
            float(value)
            return not isinstance(value, bool)
        except (TypeError, ValueError):
            return False

    @classmethod
    def _normalize_value(cls, value: Any) -> str:
        if isinstance(value, float):
            return f"{value:.6g}"
        return str(value).strip()

    @classmethod
    def _is_sensitive(cls, key: str) -> bool:
        token = str(key or "").lower()
        return any(hint in token for hint in _SENSITIVE_HINTS)

    @classmethod
    def _normalize_label_source(cls, raw: str | None) -> str | None:
        from app.domain.entities.field_label_bundle import canonicalize_label_source

        token = canonicalize_label_source(raw)
        return token or None

    @classmethod
    def _hash(cls, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()[:24]
