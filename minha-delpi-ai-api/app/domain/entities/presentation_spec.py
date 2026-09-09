"""PresentationSpec / PresentationIntent — gramática visual declarativa v1.x (additive)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PRESENTATION_SPEC_VERSION = 1

SUPPORTED_VIEWS = frozenset({"table", "chart", "kpi", "text", "tree", "dashboard", "auto"})
SUPPORTED_MARKS = frozenset(
    {
        "bar",
        "line",
        "area",
        "horizontal_bar",
        "donut",
        "pie",
        "grouped_bar",
        "stacked_bar",
        "combo",
        "scatter",
        "histogram",
        "heatmap",
        "gauge",
        "multi_line",
    }
)
SUPPORTED_PALETTE_FAMILIES = frozenset(
    {
        "brand",
        "sequential-blue",
        "cool",
        "warm",
        "diverging-status",
        "status",
    }
)
SUPPORTED_FORMATS = frozenset(
    {
        "currency",
        "percentage",
        "integer",
        "decimal",
        "date",
        "datetime",
        "duration",
        "quantity",
    }
)
SUPPORTED_ENCODING_CHANNELS = frozenset({"x", "y", "color", "size", "theta"})
SUPPORTED_TABLE_DENSITIES = frozenset({"compact", "comfortable"})
SUPPORTED_DASHBOARD_PANEL_PRESENTATIONS = frozenset({"kpi", "chart", "table"})
SUPPORTED_TEXT_SECTION_MARKERS = frozenset(
    {
        "summary",
        "highlights",
        "attention",
        "narrative",
        "details",
        "next_steps",
    }
)
SUPPORTED_PROSE_DENSITIES = frozenset({"compact", "comfortable", "verbose"})


@dataclass(frozen=True)
class PresentationIntent:
    """Intenção visual pré-execução (conceitos, não keys reais)."""

    view: str | None = None
    mark: str | None = None
    dimension_concepts: tuple[str, ...] = ()
    measure_concept: str | None = None
    palette_family: str | None = None
    sort_concept: str | None = None
    locale: str = "pt-BR"

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"locale": self.locale}
        if self.view:
            payload["view"] = self.view
        if self.mark:
            payload["mark"] = self.mark
        if self.dimension_concepts:
            payload["dimensionConcepts"] = list(self.dimension_concepts)
        if self.measure_concept:
            payload["measureConcept"] = self.measure_concept
        if self.palette_family:
            payload["paletteFamily"] = self.palette_family
        if self.sort_concept:
            payload["sortConcept"] = self.sort_concept
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> PresentationIntent:
        if not isinstance(payload, dict):
            return cls()
        dims = payload.get("dimensionConcepts") or payload.get("dimension_concepts") or []
        return cls(
            view=_norm_token(payload.get("view")),
            mark=_norm_token(payload.get("mark") or payload.get("chartType")),
            dimension_concepts=tuple(
                str(item).strip() for item in dims if str(item or "").strip()
            ),
            measure_concept=_norm_token(
                payload.get("measureConcept") or payload.get("measure_concept")
            ),
            palette_family=_norm_token(
                payload.get("paletteFamily") or payload.get("palette_family")
            ),
            sort_concept=_norm_token(
                payload.get("sortConcept") or payload.get("sort_concept")
            ),
            locale=str(payload.get("locale") or "pt-BR"),
        )


@dataclass(frozen=True)
class EncodingChannel:
    field: str
    type: str | None = None
    scale: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"field": self.field}
        if self.type:
            payload["type"] = self.type
        if self.scale:
            payload["scale"] = self.scale
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> EncodingChannel | None:
        if not isinstance(payload, dict):
            return None
        field_name = str(payload.get("field") or "").strip()
        if not field_name:
            return None
        return cls(
            field=field_name,
            type=_norm_token(payload.get("type")),
            scale=_norm_token(payload.get("scale")),
        )


@dataclass(frozen=True)
class PresentationTableSpec:
    density: str | None = None
    hidden_fields: tuple[str, ...] = ()
    emphasis_rules: tuple[dict[str, Any], ...] = ()
    role: str | None = None
    title: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.density:
            payload["density"] = self.density
        if self.hidden_fields:
            payload["hiddenFields"] = list(self.hidden_fields)
        if self.emphasis_rules:
            payload["emphasisRules"] = [dict(rule) for rule in self.emphasis_rules]
        if self.role:
            payload["role"] = self.role
        if self.title:
            payload["title"] = self.title
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> PresentationTableSpec | None:
        if not isinstance(payload, dict) or not payload:
            return None
        hidden = payload.get("hiddenFields") or payload.get("hidden_fields") or []
        rules = payload.get("emphasisRules") or payload.get("emphasis_rules") or []
        return cls(
            density=_norm_token(payload.get("density")),
            hidden_fields=tuple(
                str(item).strip() for item in hidden if str(item or "").strip()
            ),
            emphasis_rules=tuple(
                dict(item) for item in rules if isinstance(item, dict)
            ),
            role=_norm_token(payload.get("role")),
            title=str(payload.get("title") or "").strip() or None,
        )


@dataclass(frozen=True)
class PresentationChartSpec:
    top_n: int | None = None
    aggregation: str | None = None
    series_roles: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.top_n is not None:
            payload["topN"] = self.top_n
        if self.aggregation:
            payload["aggregation"] = self.aggregation
        if self.series_roles:
            payload["seriesRoles"] = dict(self.series_roles)
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> PresentationChartSpec | None:
        if not isinstance(payload, dict) or not payload:
            return None
        top_n_raw = payload.get("topN") if "topN" in payload else payload.get("top_n")
        top_n: int | None = None
        if top_n_raw is not None:
            try:
                top_n = int(top_n_raw)
            except (TypeError, ValueError):
                top_n = None
        roles_raw = payload.get("seriesRoles") or payload.get("series_roles") or {}
        series_roles = {
            str(key).strip(): str(value).strip()
            for key, value in dict(roles_raw).items()
            if str(key).strip() and str(value or "").strip()
        }
        return cls(
            top_n=top_n,
            aggregation=_norm_token(payload.get("aggregation")),
            series_roles=series_roles,
        )


@dataclass(frozen=True)
class PresentationKpiSpec:
    measure_fields: tuple[str, ...] = ()
    card_order: tuple[str, ...] = ()
    tones: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.measure_fields:
            payload["measureFields"] = list(self.measure_fields)
        if self.card_order:
            payload["cardOrder"] = list(self.card_order)
        if self.tones:
            payload["tones"] = list(self.tones)
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> PresentationKpiSpec | None:
        if not isinstance(payload, dict) or not payload:
            return None
        measures = payload.get("measureFields") or payload.get("measure_fields") or []
        order = payload.get("cardOrder") or payload.get("card_order") or []
        tones = payload.get("tones") or []
        return cls(
            measure_fields=tuple(
                str(item).strip() for item in measures if str(item or "").strip()
            ),
            card_order=tuple(
                str(item).strip() for item in order if str(item or "").strip()
            ),
            tones=tuple(str(item).strip() for item in tones if str(item or "").strip()),
        )


@dataclass(frozen=True)
class PresentationTreeSpec:
    level_fields: tuple[str, ...] = ()
    max_depth: int | None = None
    default_expanded_depth: int | None = None
    label_field: str | None = None
    badge_field: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.level_fields:
            payload["levelFields"] = list(self.level_fields)
        if self.max_depth is not None:
            payload["maxDepth"] = self.max_depth
        if self.default_expanded_depth is not None:
            payload["defaultExpandedDepth"] = self.default_expanded_depth
        if self.label_field:
            payload["labelField"] = self.label_field
        if self.badge_field:
            payload["badgeField"] = self.badge_field
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> PresentationTreeSpec | None:
        if not isinstance(payload, dict) or not payload:
            return None
        levels = payload.get("levelFields") or payload.get("level_fields") or []
        return cls(
            level_fields=tuple(
                str(item).strip() for item in levels if str(item or "").strip()
            ),
            max_depth=_optional_int(payload.get("maxDepth") or payload.get("max_depth")),
            default_expanded_depth=_optional_int(
                payload.get("defaultExpandedDepth")
                or payload.get("default_expanded_depth")
            ),
            label_field=str(
                payload.get("labelField") or payload.get("label_field") or ""
            ).strip()
            or None,
            badge_field=str(
                payload.get("badgeField") or payload.get("badge_field") or ""
            ).strip()
            or None,
        )


@dataclass(frozen=True)
class PresentationDashboardPanelSpec:
    id: str
    presentation: str
    role: str | None = None
    fields: tuple[str, ...] = ()
    measures: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "presentation": self.presentation,
        }
        if self.role:
            payload["role"] = self.role
        if self.fields:
            payload["fields"] = list(self.fields)
        if self.measures:
            payload["measures"] = list(self.measures)
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> PresentationDashboardPanelSpec | None:
        if not isinstance(payload, dict):
            return None
        panel_id = str(payload.get("id") or "").strip()
        presentation = _norm_token(payload.get("presentation")) or ""
        if not panel_id or not presentation:
            return None
        fields = payload.get("fields") or []
        measures = payload.get("measures") or []
        return cls(
            id=panel_id,
            presentation=presentation,
            role=_norm_token(payload.get("role")),
            fields=tuple(str(item).strip() for item in fields if str(item or "").strip()),
            measures=tuple(
                str(item).strip() for item in measures if str(item or "").strip()
            ),
        )


@dataclass(frozen=True)
class PresentationDashboardSpec:
    panels: tuple[PresentationDashboardPanelSpec, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.panels:
            payload["panels"] = [panel.as_dict() for panel in self.panels]
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> PresentationDashboardSpec | None:
        if not isinstance(payload, dict) or not payload:
            return None
        panels_raw = payload.get("panels") or []
        panels: list[PresentationDashboardPanelSpec] = []
        for item in panels_raw:
            parsed = PresentationDashboardPanelSpec.from_dict(item)
            if parsed:
                panels.append(parsed)
        return cls(panels=tuple(panels))


@dataclass(frozen=True)
class PresentationTextSpec:
    section_plan: tuple[str, ...] = ()
    prose_density: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.section_plan:
            payload["sectionPlan"] = list(self.section_plan)
        if self.prose_density:
            payload["proseDensity"] = self.prose_density
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> PresentationTextSpec | None:
        if not isinstance(payload, dict) or not payload:
            return None
        plan = payload.get("sectionPlan") or payload.get("section_plan") or []
        return cls(
            section_plan=tuple(
                str(item).strip() for item in plan if str(item or "").strip()
            ),
            prose_density=_norm_token(
                payload.get("proseDensity") or payload.get("prose_density")
            ),
        )


@dataclass(frozen=True)
class PresentationDeliverySpec:
    prefer_canvas: bool | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.prefer_canvas is not None:
            payload["preferCanvas"] = bool(self.prefer_canvas)
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> PresentationDeliverySpec | None:
        if not isinstance(payload, dict) or not payload:
            return None
        if "preferCanvas" not in payload and "prefer_canvas" not in payload:
            return None
        raw = (
            payload.get("preferCanvas")
            if "preferCanvas" in payload
            else payload.get("prefer_canvas")
        )
        return cls(prefer_canvas=bool(raw))


@dataclass(frozen=True)
class PresentationSpec:
    """Proposta declarativa validável — nunca contrato de entrega MFE."""

    version: int = PRESENTATION_SPEC_VERSION
    view: str = "auto"
    mark: str | None = None
    encoding: dict[str, EncodingChannel] = field(default_factory=dict)
    fields: tuple[str, ...] = ()
    sort_field: str | None = None
    sort_direction: str | None = None
    labels: dict[str, str] = field(default_factory=dict)
    formats: dict[str, str] = field(default_factory=dict)
    palette_family: str | None = None
    legend_visible: bool | None = None
    provenance: str = "DETERMINISTIC"
    table: PresentationTableSpec | None = None
    chart: PresentationChartSpec | None = None
    kpi: PresentationKpiSpec | None = None
    tree: PresentationTreeSpec | None = None
    dashboard: PresentationDashboardSpec | None = None
    text: PresentationTextSpec | None = None
    delivery: PresentationDeliverySpec | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "version": self.version,
            "view": self.view,
            "provenance": self.provenance,
        }
        if self.mark:
            payload["mark"] = self.mark
        if self.encoding:
            payload["encoding"] = {
                channel: item.as_dict() for channel, item in self.encoding.items()
            }
        if self.fields:
            payload["fields"] = [{"field": key} for key in self.fields]
        if self.sort_field:
            payload["sort"] = {
                "field": self.sort_field,
                "direction": self.sort_direction or "desc",
            }
        if self.labels:
            payload["labels"] = dict(self.labels)
        if self.formats:
            payload["formats"] = dict(self.formats)
        if self.palette_family:
            payload["paletteFamily"] = self.palette_family
        if self.legend_visible is not None:
            payload["legend"] = {"visible": self.legend_visible}
        if self.table is not None:
            table_payload = self.table.as_dict()
            if table_payload:
                payload["table"] = table_payload
        if self.chart is not None:
            chart_payload = self.chart.as_dict()
            if chart_payload:
                payload["chart"] = chart_payload
        if self.kpi is not None:
            kpi_payload = self.kpi.as_dict()
            if kpi_payload:
                payload["kpi"] = kpi_payload
        if self.tree is not None:
            tree_payload = self.tree.as_dict()
            if tree_payload:
                payload["tree"] = tree_payload
        if self.dashboard is not None:
            dashboard_payload = self.dashboard.as_dict()
            if dashboard_payload:
                payload["dashboard"] = dashboard_payload
        if self.text is not None:
            text_payload = self.text.as_dict()
            if text_payload:
                payload["text"] = text_payload
        if self.delivery is not None:
            delivery_payload = self.delivery.as_dict()
            if delivery_payload:
                payload["delivery"] = delivery_payload
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> PresentationSpec | None:
        if not isinstance(payload, dict):
            return None
        encoding_raw = payload.get("encoding") if isinstance(payload.get("encoding"), dict) else {}
        encoding: dict[str, EncodingChannel] = {}
        for channel, value in encoding_raw.items():
            token = str(channel or "").strip().lower()
            if token not in SUPPORTED_ENCODING_CHANNELS:
                continue
            parsed = EncodingChannel.from_dict(value)
            if parsed:
                encoding[token] = parsed

        fields_raw = payload.get("fields") or []
        fields: list[str] = []
        for item in fields_raw:
            if isinstance(item, dict):
                key = str(item.get("field") or "").strip()
            else:
                key = str(item or "").strip()
            if key:
                fields.append(key)

        sort_raw = payload.get("sort") if isinstance(payload.get("sort"), dict) else {}
        legend_raw = payload.get("legend") if isinstance(payload.get("legend"), dict) else {}
        labels = {
            str(key).strip(): str(value).strip()
            for key, value in dict(payload.get("labels") or {}).items()
            if str(key).strip() and str(value or "").strip()
        }
        formats = {
            str(key).strip(): str(value).strip()
            for key, value in dict(payload.get("formats") or {}).items()
            if str(key).strip() and str(value or "").strip()
        }

        return cls(
            version=int(payload.get("version") or PRESENTATION_SPEC_VERSION),
            view=_norm_token(payload.get("view")) or "auto",
            mark=_norm_token(payload.get("mark") or payload.get("chartType")),
            encoding=encoding,
            fields=tuple(fields),
            sort_field=str(sort_raw.get("field") or "").strip() or None,
            sort_direction=_norm_token(sort_raw.get("direction")),
            labels=labels,
            formats=formats,
            palette_family=_norm_token(
                payload.get("paletteFamily") or payload.get("palette_family")
            ),
            legend_visible=(
                bool(legend_raw.get("visible"))
                if "visible" in legend_raw
                else None
            ),
            provenance=str(payload.get("provenance") or "DETERMINISTIC").upper(),
            table=PresentationTableSpec.from_dict(payload.get("table")),
            chart=PresentationChartSpec.from_dict(payload.get("chart")),
            kpi=PresentationKpiSpec.from_dict(payload.get("kpi")),
            tree=PresentationTreeSpec.from_dict(payload.get("tree")),
            dashboard=PresentationDashboardSpec.from_dict(payload.get("dashboard")),
            text=PresentationTextSpec.from_dict(payload.get("text")),
            delivery=PresentationDeliverySpec.from_dict(payload.get("delivery")),
        )


def _norm_token(value: Any) -> str | None:
    token = str(value or "").strip().lower()
    return token or None


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


_FIELD_REF = {
    "type": "string",
    "minLength": 1,
    "maxLength": 128,
}

# JSON Schema (structured outputs / contract tests) — additionalProperties false.
PRESENTATION_SPEC_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["version", "view"],
    "properties": {
        "version": {"type": "integer", "const": PRESENTATION_SPEC_VERSION},
        "view": {"type": "string", "enum": sorted(SUPPORTED_VIEWS)},
        "mark": {"type": ["string", "null"], "enum": sorted(SUPPORTED_MARKS) + [None]},
        "encoding": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                channel: {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["field"],
                    "properties": {
                        "field": {"type": "string", "minLength": 1, "maxLength": 128},
                        "type": {"type": ["string", "null"]},
                        "scale": {"type": ["string", "null"]},
                    },
                }
                for channel in sorted(SUPPORTED_ENCODING_CHANNELS)
            },
        },
        "fields": {
            "type": "array",
            "maxItems": 32,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field"],
                "properties": {"field": {"type": "string", "minLength": 1, "maxLength": 128}},
            },
        },
        "sort": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "field": {"type": "string"},
                "direction": {"type": "string", "enum": ["asc", "desc"]},
            },
        },
        "labels": {
            "type": "object",
            "additionalProperties": {"type": "string", "maxLength": 120},
            "maxProperties": 64,
        },
        "formats": {
            "type": "object",
            "additionalProperties": {
                "type": "string",
                "enum": sorted(SUPPORTED_FORMATS),
            },
            "maxProperties": 64,
        },
        "paletteFamily": {
            "type": ["string", "null"],
            "enum": sorted(SUPPORTED_PALETTE_FAMILIES) + [None],
        },
        "legend": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"visible": {"type": "boolean"}},
        },
        "provenance": {"type": "string"},
        "table": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "density": {
                    "type": ["string", "null"],
                    "enum": sorted(SUPPORTED_TABLE_DENSITIES) + [None],
                },
                "hiddenFields": {
                    "type": "array",
                    "maxItems": 32,
                    "items": dict(_FIELD_REF),
                },
                "emphasisRules": {
                    "type": "array",
                    "maxItems": 16,
                    "items": {"type": "object"},
                },
                "role": {"type": ["string", "null"], "maxLength": 64},
                "title": {"type": ["string", "null"], "maxLength": 120},
            },
        },
        "chart": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "topN": {"type": ["integer", "null"], "minimum": 1, "maximum": 100},
                "aggregation": {"type": ["string", "null"], "maxLength": 32},
                "seriesRoles": {
                    "type": "object",
                    "additionalProperties": {"type": "string", "maxLength": 64},
                    "maxProperties": 16,
                },
            },
        },
        "kpi": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "measureFields": {
                    "type": "array",
                    "maxItems": 8,
                    "items": dict(_FIELD_REF),
                },
                "cardOrder": {
                    "type": "array",
                    "maxItems": 8,
                    "items": dict(_FIELD_REF),
                },
                "tones": {
                    "type": "array",
                    "maxItems": 8,
                    "items": {"type": "string", "maxLength": 32},
                },
            },
        },
        "tree": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "levelFields": {
                    "type": "array",
                    "maxItems": 8,
                    "items": dict(_FIELD_REF),
                },
                "maxDepth": {"type": ["integer", "null"], "minimum": 1, "maximum": 12},
                "defaultExpandedDepth": {
                    "type": ["integer", "null"],
                    "minimum": 0,
                    "maximum": 12,
                },
                "labelField": {"type": ["string", "null"], "maxLength": 128},
                "badgeField": {"type": ["string", "null"], "maxLength": 128},
            },
        },
        "dashboard": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "panels": {
                    "type": "array",
                    "maxItems": 6,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "presentation"],
                        "properties": {
                            "id": {"type": "string", "minLength": 1, "maxLength": 64},
                            "presentation": {
                                "type": "string",
                                "enum": sorted(SUPPORTED_DASHBOARD_PANEL_PRESENTATIONS),
                            },
                            "role": {"type": ["string", "null"], "maxLength": 64},
                            "fields": {
                                "type": "array",
                                "maxItems": 16,
                                "items": dict(_FIELD_REF),
                            },
                            "measures": {
                                "type": "array",
                                "maxItems": 8,
                                "items": dict(_FIELD_REF),
                            },
                        },
                    },
                }
            },
        },
        "text": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "sectionPlan": {
                    "type": "array",
                    "maxItems": 8,
                    "items": {
                        "type": "string",
                        "enum": sorted(SUPPORTED_TEXT_SECTION_MARKERS),
                    },
                },
                "proseDensity": {
                    "type": ["string", "null"],
                    "enum": sorted(SUPPORTED_PROSE_DENSITIES) + [None],
                },
            },
        },
        "delivery": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "preferCanvas": {"type": "boolean"},
            },
        },
    },
}

PRESENTATION_INTENT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "view": {"type": ["string", "null"], "enum": sorted(SUPPORTED_VIEWS) + [None]},
        "mark": {"type": ["string", "null"], "enum": sorted(SUPPORTED_MARKS) + [None]},
        "dimensionConcepts": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "maxLength": 80},
        },
        "measureConcept": {"type": ["string", "null"], "maxLength": 80},
        "paletteFamily": {
            "type": ["string", "null"],
            "enum": sorted(SUPPORTED_PALETTE_FAMILIES) + [None],
        },
        "sortConcept": {"type": ["string", "null"], "maxLength": 80},
        "locale": {"type": "string", "default": "pt-BR"},
    },
}
