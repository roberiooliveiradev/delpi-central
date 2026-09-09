"""Valida PresentationSpec contra profile + candidate membership."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import (
    PRESENTATION_SPEC_VERSION,
    SUPPORTED_FORMATS,
    SUPPORTED_MARKS,
    SUPPORTED_PALETTE_FAMILIES,
    SUPPORTED_VIEWS,
    PresentationSpec,
)


@dataclass
class PresentationSpecValidationResult:
    ok: bool
    spec: PresentationSpec | None = None
    errors: list[str] = field(default_factory=list)
    unmet_intent: str | None = None
    field_errors: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "unmetIntent": self.unmet_intent,
            "fieldErrors": dict(self.field_errors),
            "spec": self.spec.as_dict() if self.spec else None,
        }


class PresentationSpecValidatorService:
    @classmethod
    def validate(
        cls,
        raw: PresentationSpec | dict[str, Any] | None,
        *,
        profile: PresentationDataProfile,
        user_explicit: bool = False,
    ) -> PresentationSpecValidationResult:
        spec = raw if isinstance(raw, PresentationSpec) else PresentationSpec.from_dict(raw)
        if spec is None:
            return PresentationSpecValidationResult(
                ok=False,
                errors=["empty_or_invalid_spec"],
            )

        errors: list[str] = []
        field_errors: dict[str, str] = {}
        known_keys = {item.key for item in profile.fields}
        dim_candidates = set(profile.dimension_candidates)
        measure_candidates = set(profile.measure_candidates)

        if spec.version != PRESENTATION_SPEC_VERSION:
            errors.append(f"unsupported_version:{spec.version}")

        if spec.view not in SUPPORTED_VIEWS:
            errors.append(f"unsupported_view:{spec.view}")

        if spec.mark and spec.mark not in SUPPORTED_MARKS:
            errors.append(f"unsupported_mark:{spec.mark}")
            if user_explicit:
                return PresentationSpecValidationResult(
                    ok=False,
                    errors=errors,
                    unmet_intent=f"mark_unavailable:{spec.mark}",
                )

        if spec.palette_family and spec.palette_family not in SUPPORTED_PALETTE_FAMILIES:
            errors.append(f"unsupported_palette:{spec.palette_family}")
            # Drop invalid palette; keep rest (incl. nested 1.x blocks).
            spec = replace(spec, palette_family=None)

        for fmt in spec.formats.values():
            if fmt not in SUPPORTED_FORMATS:
                errors.append(f"unsupported_format:{fmt}")

        # Labels must never become field identity.
        for channel, encoding in spec.encoding.items():
            if encoding.field not in known_keys:
                field_errors[channel] = f"unknown_field:{encoding.field}"
                errors.append(f"encoding.{channel}.unknown_field")
            # Reject translated identity (label used as field).
            if encoding.field in set(spec.labels.values()):
                field_errors[channel] = "label_used_as_field_identity"
                errors.append(f"encoding.{channel}.label_as_identity")

        for key in spec.fields:
            if key not in known_keys:
                field_errors[key] = "unknown_field"
                errors.append(f"fields.unknown:{key}")

        if spec.sort_field and spec.sort_field not in known_keys:
            errors.append(f"sort.unknown_field:{spec.sort_field}")

        # Whole-spec coherence for heatmap.
        if spec.mark == "heatmap" or (
            spec.view == "chart" and "color" in spec.encoding and "x" in spec.encoding and "y" in spec.encoding
        ):
            heatmap_errors = cls._validate_heatmap(spec, profile)
            if heatmap_errors:
                # Heatmap must be fully valid — reject whole mark binding.
                if user_explicit:
                    return PresentationSpecValidationResult(
                        ok=False,
                        errors=errors + heatmap_errors,
                        unmet_intent="heatmap_not_materializable",
                        field_errors=field_errors,
                    )
                errors.extend(heatmap_errors)
                return PresentationSpecValidationResult(ok=False, errors=errors, field_errors=field_errors)

        # Membership integrity for chart encodings.
        if spec.view == "chart" or spec.mark:
            x = spec.encoding.get("x")
            y = spec.encoding.get("y")
            color = spec.encoding.get("color")
            if x and x.field not in dim_candidates and x.field not in measure_candidates:
                x_profile = profile.field_map().get(x.field)
                if x.field in known_keys and x_profile is not None and x_profile.is_constant:
                    errors.append("encoding.x.constant_dimension")
                    field_errors["x"] = "constant_dimension"
            if y and y.field in known_keys:
                field_profile = profile.field_map().get(y.field)
                if field_profile and field_profile.is_constant and spec.mark == "heatmap":
                    errors.append("encoding.y.constant_dimension")
                    field_errors["y"] = "constant_dimension"
            if color and color.field not in measure_candidates and color.field in known_keys:
                field_profile = profile.field_map().get(color.field)
                if field_profile and not field_profile.is_measure_candidate:
                    errors.append("encoding.color.not_measure")

        hard_errors = [
            error
            for error in errors
            if not error.startswith("unsupported_palette") and not error.startswith("unsupported_format")
        ]
        if hard_errors and (spec.mark == "heatmap" or any("unknown_field" in error for error in hard_errors)):
            return PresentationSpecValidationResult(
                ok=False,
                errors=errors,
                field_errors=field_errors,
                unmet_intent="heatmap_not_materializable" if user_explicit and spec.mark == "heatmap" else None,
            )

        # Soft: drop unknown encodings but keep valid remainder when not heatmap.
        cleaned_encoding = {
            channel: encoding
            for channel, encoding in spec.encoding.items()
            if channel not in field_errors
        }
        cleaned_fields = tuple(key for key in spec.fields if key in known_keys)
        cleaned_formats = {
            key: value
            for key, value in spec.formats.items()
            if value in SUPPORTED_FORMATS and key in known_keys
        }
        cleaned_labels = {
            key: value for key, value in spec.labels.items() if key in known_keys
        }

        cleaned = replace(
            spec,
            version=PRESENTATION_SPEC_VERSION,
            view=spec.view if spec.view in SUPPORTED_VIEWS else "auto",
            mark=spec.mark if spec.mark in SUPPORTED_MARKS else None,
            encoding=cleaned_encoding,
            fields=cleaned_fields,
            sort_field=spec.sort_field if spec.sort_field in known_keys else None,
            sort_direction=spec.sort_direction if spec.sort_direction in {"asc", "desc"} else None,
            labels=cleaned_labels,
            formats=cleaned_formats,
        )

        if cleaned.mark == "heatmap" and not cls._heatmap_ok(cleaned, profile):
            return PresentationSpecValidationResult(
                ok=False,
                errors=errors + ["heatmap_incoherent_after_clean"],
                field_errors=field_errors,
            )

        return PresentationSpecValidationResult(ok=True, spec=cleaned, errors=errors, field_errors=field_errors)

    @classmethod
    def _validate_heatmap(
        cls,
        spec: PresentationSpec,
        profile: PresentationDataProfile,
    ) -> list[str]:
        errors: list[str] = []
        x = spec.encoding.get("x")
        y = spec.encoding.get("y")
        color = spec.encoding.get("color")
        if not x or not y or not color:
            errors.append("heatmap.requires_x_y_color")
            return errors
        field_map = profile.field_map()
        for channel, encoding in (("x", x), ("y", y)):
            item = field_map.get(encoding.field)
            if item is None:
                errors.append(f"heatmap.{channel}.missing")
            elif item.is_constant or item.cardinality <= 1:
                errors.append(f"heatmap.{channel}.not_discriminant")
        color_item = field_map.get(color.field)
        if color_item is None or not color_item.is_measure_candidate:
            errors.append("heatmap.color.not_measure")
        if x and y and x.field == y.field:
            errors.append("heatmap.x_y_same")
        # Cell budget aligned with existing matrix gate (~16x16).
        if x and y:
            x_item = field_map.get(x.field)
            y_item = field_map.get(y.field)
            if x_item and y_item and x_item.cardinality * y_item.cardinality > 256:
                errors.append("heatmap.cell_budget_exceeded")
        return errors

    @classmethod
    def _heatmap_ok(cls, spec: PresentationSpec, profile: PresentationDataProfile) -> bool:
        return not cls._validate_heatmap(spec, profile)
