"""Valida PresentationSpec contra profile + candidate membership."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import (
    PRESENTATION_SPEC_VERSION,
    SUPPORTED_DASHBOARD_PANEL_PRESENTATIONS,
    SUPPORTED_FORMATS,
    SUPPORTED_MARKS,
    SUPPORTED_PALETTE_FAMILIES,
    SUPPORTED_PROSE_DENSITIES,
    SUPPORTED_TABLE_DENSITIES,
    SUPPORTED_TEXT_SECTION_MARKERS,
    SUPPORTED_VIEWS,
    PresentationDashboardSpec,
    PresentationKpiSpec,
    PresentationSpec,
    PresentationTableSpec,
    PresentationTextSpec,
    PresentationTreeSpec,
)

MAX_SPEC_FIELDS = 32
MAX_KPI_CARDS = 8
MAX_DASHBOARD_PANELS = 6
MAX_TREE_DEPTH = 12
MAX_TREE_LEVELS = 8

# Hex / CSS / JS / markup — Spec is semantic-only (D1).
_FORBIDDEN_STYLE_RE = re.compile(
    r"("
    r"\#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b|"
    r"\brgba?\s*\(|"
    r"\bhsla?\s*\(|"
    r"\b\d+(?:\.\d+)?(?:px|em|rem|vw|vh)\b|"
    r"javascript\s*:|"
    r"<\s*script\b|"
    r"\bexpression\s*\(|"
    r"\burl\s*\("
    r")",
    re.IGNORECASE,
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

        style_errors = cls._forbidden_style_errors(spec)
        if style_errors:
            return PresentationSpecValidationResult(
                ok=False,
                errors=style_errors,
                unmet_intent="forbidden_presentation_style",
            )

        cap_errors = cls._cap_errors(spec)
        if cap_errors:
            return PresentationSpecValidationResult(
                ok=False,
                errors=cap_errors,
                unmet_intent="spec_cap_exceeded",
            )

        nested_errors = cls._nested_contract_errors(spec)
        if nested_errors:
            return PresentationSpecValidationResult(
                ok=False,
                errors=nested_errors,
                unmet_intent="invalid_nested_spec",
            )

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

        nested_membership = cls._nested_membership_errors(spec, known_keys)
        errors.extend(nested_membership)

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
            if not error.startswith("unsupported_palette")
            and not error.startswith("unsupported_format")
            and not error.startswith("nested.")
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
            table=cls._clean_table(spec.table, known_keys),
            kpi=cls._clean_kpi(spec.kpi, known_keys),
            tree=cls._clean_tree(spec.tree, known_keys),
            dashboard=cls._clean_dashboard(spec.dashboard, known_keys),
            text=cls._clean_text(spec.text),
        )

        if cleaned.mark == "heatmap" and not cls._heatmap_ok(cleaned, profile):
            return PresentationSpecValidationResult(
                ok=False,
                errors=errors + ["heatmap_incoherent_after_clean"],
                field_errors=field_errors,
            )

        return PresentationSpecValidationResult(ok=True, spec=cleaned, errors=errors, field_errors=field_errors)

    @classmethod
    def _cap_errors(cls, spec: PresentationSpec) -> list[str]:
        errors: list[str] = []
        if len(spec.fields) > MAX_SPEC_FIELDS:
            errors.append(f"cap.fields:{len(spec.fields)}>{MAX_SPEC_FIELDS}")
        if spec.kpi is not None:
            if len(spec.kpi.measure_fields) > MAX_KPI_CARDS:
                errors.append(
                    f"cap.kpi.measureFields:{len(spec.kpi.measure_fields)}>{MAX_KPI_CARDS}"
                )
            if len(spec.kpi.card_order) > MAX_KPI_CARDS:
                errors.append(
                    f"cap.kpi.cardOrder:{len(spec.kpi.card_order)}>{MAX_KPI_CARDS}"
                )
            if len(spec.kpi.tones) > MAX_KPI_CARDS:
                errors.append(f"cap.kpi.tones:{len(spec.kpi.tones)}>{MAX_KPI_CARDS}")
        if spec.dashboard is not None and len(spec.dashboard.panels) > MAX_DASHBOARD_PANELS:
            errors.append(
                f"cap.dashboard.panels:{len(spec.dashboard.panels)}>{MAX_DASHBOARD_PANELS}"
            )
        if spec.tree is not None:
            if len(spec.tree.level_fields) > MAX_TREE_LEVELS:
                errors.append(
                    f"cap.tree.levelFields:{len(spec.tree.level_fields)}>{MAX_TREE_LEVELS}"
                )
            if spec.tree.max_depth is not None and spec.tree.max_depth > MAX_TREE_DEPTH:
                errors.append(f"cap.tree.maxDepth:{spec.tree.max_depth}>{MAX_TREE_DEPTH}")
            if (
                spec.tree.default_expanded_depth is not None
                and spec.tree.default_expanded_depth > MAX_TREE_DEPTH
            ):
                errors.append(
                    f"cap.tree.defaultExpandedDepth:{spec.tree.default_expanded_depth}>{MAX_TREE_DEPTH}"
                )
        return errors

    @classmethod
    def _nested_contract_errors(cls, spec: PresentationSpec) -> list[str]:
        errors: list[str] = []
        if spec.table is not None and spec.table.density and spec.table.density not in SUPPORTED_TABLE_DENSITIES:
            errors.append(f"table.unsupported_density:{spec.table.density}")
        if spec.text is not None:
            if spec.text.prose_density and spec.text.prose_density not in SUPPORTED_PROSE_DENSITIES:
                errors.append(f"text.unsupported_proseDensity:{spec.text.prose_density}")
            for marker in spec.text.section_plan:
                if marker not in SUPPORTED_TEXT_SECTION_MARKERS:
                    errors.append(f"text.unsupported_sectionPlan:{marker}")
        if spec.dashboard is not None:
            for panel in spec.dashboard.panels:
                if panel.presentation not in SUPPORTED_DASHBOARD_PANEL_PRESENTATIONS:
                    errors.append(
                        f"dashboard.panel.unsupported_presentation:{panel.presentation}"
                    )
        return errors

    @classmethod
    def _nested_membership_errors(
        cls,
        spec: PresentationSpec,
        known_keys: set[str],
    ) -> list[str]:
        if not known_keys:
            return []
        errors: list[str] = []
        if spec.table is not None:
            for key in spec.table.hidden_fields:
                if key not in known_keys:
                    errors.append(f"nested.table.hiddenFields.unknown:{key}")
        if spec.kpi is not None:
            for key in (*spec.kpi.measure_fields, *spec.kpi.card_order):
                if key not in known_keys:
                    errors.append(f"nested.kpi.unknown:{key}")
        if spec.tree is not None:
            for key in (
                *spec.tree.level_fields,
                *(
                    [spec.tree.label_field]
                    if spec.tree.label_field
                    else []
                ),
                *([spec.tree.badge_field] if spec.tree.badge_field else []),
            ):
                if key not in known_keys:
                    errors.append(f"nested.tree.unknown:{key}")
        if spec.dashboard is not None:
            for panel in spec.dashboard.panels:
                for key in (*panel.fields, *panel.measures):
                    if key not in known_keys:
                        errors.append(f"nested.dashboard.{panel.id}.unknown:{key}")
        return errors

    @classmethod
    def _forbidden_style_errors(cls, spec: PresentationSpec) -> list[str]:
        errors: list[str] = []
        for path, value in cls._iter_string_leaves(spec.as_dict()):
            if _FORBIDDEN_STYLE_RE.search(value):
                errors.append(f"forbidden_style:{path}")
        return errors

    @classmethod
    def _iter_string_leaves(
        cls,
        payload: Any,
        *,
        prefix: str = "spec",
    ) -> list[tuple[str, str]]:
        leaves: list[tuple[str, str]] = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                leaves.extend(cls._iter_string_leaves(value, prefix=f"{prefix}.{key}"))
        elif isinstance(payload, list):
            for index, value in enumerate(payload):
                leaves.extend(cls._iter_string_leaves(value, prefix=f"{prefix}[{index}]"))
        elif isinstance(payload, str):
            leaves.append((prefix, payload))
        return leaves

    @classmethod
    def _clean_table(
        cls,
        block: PresentationTableSpec | None,
        known_keys: set[str],
    ) -> PresentationTableSpec | None:
        if block is None:
            return None
        hidden = tuple(key for key in block.hidden_fields if key in known_keys)
        density = block.density if block.density in SUPPORTED_TABLE_DENSITIES else None
        cleaned = PresentationTableSpec(
            density=density,
            hidden_fields=hidden,
            emphasis_rules=block.emphasis_rules,
            role=block.role,
            title=block.title,
        )
        return cleaned if cleaned.as_dict() else None

    @classmethod
    def _clean_kpi(
        cls,
        block: PresentationKpiSpec | None,
        known_keys: set[str],
    ) -> PresentationKpiSpec | None:
        if block is None:
            return None
        cleaned = PresentationKpiSpec(
            measure_fields=tuple(key for key in block.measure_fields if key in known_keys),
            card_order=tuple(key for key in block.card_order if key in known_keys),
            tones=block.tones,
        )
        return cleaned if cleaned.as_dict() else None

    @classmethod
    def _clean_tree(
        cls,
        block: PresentationTreeSpec | None,
        known_keys: set[str],
    ) -> PresentationTreeSpec | None:
        if block is None:
            return None
        cleaned = PresentationTreeSpec(
            level_fields=tuple(key for key in block.level_fields if key in known_keys),
            max_depth=block.max_depth,
            default_expanded_depth=block.default_expanded_depth,
            label_field=block.label_field if block.label_field in known_keys else None,
            badge_field=block.badge_field if block.badge_field in known_keys else None,
        )
        return cleaned if cleaned.as_dict() else None

    @classmethod
    def _clean_dashboard(
        cls,
        block: PresentationDashboardSpec | None,
        known_keys: set[str],
    ) -> PresentationDashboardSpec | None:
        if block is None:
            return None
        panels = []
        for panel in block.panels:
            if panel.presentation not in SUPPORTED_DASHBOARD_PANEL_PRESENTATIONS:
                continue
            panels.append(
                replace(
                    panel,
                    fields=tuple(key for key in panel.fields if key in known_keys),
                    measures=tuple(key for key in panel.measures if key in known_keys),
                )
            )
        cleaned = PresentationDashboardSpec(panels=tuple(panels))
        return cleaned if cleaned.as_dict() else None

    @classmethod
    def _clean_text(cls, block: PresentationTextSpec | None) -> PresentationTextSpec | None:
        if block is None:
            return None
        cleaned = PresentationTextSpec(
            section_plan=tuple(
                marker
                for marker in block.section_plan
                if marker in SUPPORTED_TEXT_SECTION_MARKERS
            ),
            prose_density=(
                block.prose_density
                if block.prose_density in SUPPORTED_PROSE_DENSITIES
                else None
            ),
        )
        return cleaned if cleaned.as_dict() else None

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
