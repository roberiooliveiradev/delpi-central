"""Tradução de colunas operacionais — conteúdo editável + OpenAPI responseSchema."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.presentation_column_label_discovery_service import (
    PresentationColumnLabelDiscoveryService,
)


def invalidate_column_label_cache() -> None:
    _column_labels_content.cache_clear()


@lru_cache(maxsize=1)
def _column_labels_content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("column_labels")


class ExternalActionColumnLabelService:
    """Resolve labels de campos para tabelas do presenter operacional."""

    _NESTED_HIERARCHY_SKIP_KEYS = frozenset(
        {"parents", "children", "components", "child", "childs"}
    )

    _FIELD_FORMAT_TOKENS: dict[str, tuple[str, ...]] = {
        "currency": (
            "revenue",
            "receita",
            "rol",
            "cost",
            "custo",
            "price",
            "preco",
            "saving",
            "economia",
            "investment",
            "balance",
            "saldo",
            "icms",
            "pis",
            "cofins",
            "iss",
            "ipi",
            "devolv",
            "tax",
            "imposto",
            "valor",
            "amount",
            "ebitda_value",
            "fixed_cost",
            "cpv_total",
            "stock_value",
            "savings",
            "depreciation",
        ),
        "percent": (
            "_pct",
            "_percent",
            "percentage",
            "taxa",
            "rate",
            "margem",
            "margin",
            "otd",
            "giro",
            "eficiencia",
            "yield",
            "turnover",
            "absenteeism",
            "satisfaction",
            "completion",
        ),
        "date": (
            "_date",
            "date_start",
            "date_end",
            "start_date",
            "end_date",
            "registered_date",
            "measurement_date",
            "data_limite",
        ),
        "quantity": (
            "qtd",
            "qty",
            "quantity",
            "_count",
            "_lines",
            "_months",
            "registros",
            "points",
            "kaizens",
            "reviews",
            "pdis",
            "lmps",
            "proposals",
            "movements",
            "hours_saved",
            "solutions",
        ),
        "days": (
            "_days",
            "pmr_days",
            "lead_time",
            "dias_uteis",
        ),
    }

    def enrich_column_def(
        self,
        key: str,
        *,
        label: str | None = None,
        schema_labels: dict[str, str] | None = None,
        schema_formats: dict[str, str] | None = None,
    ) -> dict[str, str]:
        normalized_key = str(key or "").strip()

        if not normalized_key:
            return {"key": "", "label": ""}

        resolved_label = (
            str(label).strip()
            if isinstance(label, str) and label.strip()
            else self.label_for(normalized_key, schema_labels=schema_labels)
        )
        column: dict[str, str] = {
            "key": normalized_key,
            "label": resolved_label,
        }
        field_format = self.resolve_field_format(
            normalized_key,
            schema_formats=schema_formats,
        )

        if field_format:
            column["dataType"] = field_format

        return column

    def label_for(
        self,
        key: str,
        *,
        schema_labels: dict[str, str] | None = None,
        path: str = "",
        profile_name: str | None = None,
        enable_discovery: bool = True,
    ) -> str:
        token = str(key or "").strip()

        if not token:
            return ""

        return self.resolve_field_labels(
            [token],
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
            enable_discovery=enable_discovery,
        ).get(token, self._humanize_field_key(token))

    def _resolve_catalog_label(
        self,
        key: str,
        *,
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
    ) -> str | None:
        token = str(key or "").strip()

        if not token:
            return None

        if profile_name:
            hinted = self.column_label_hints(profile_name).get(token)

            if str(hinted or "").strip():
                return str(hinted).strip()

        if schema_labels:
            schema_label = schema_labels.get(token)

            if isinstance(schema_label, str) and schema_label.strip():
                return schema_label.strip()

        content = _column_labels_content()
        fields = content.get("fields") or {}
        configured = fields.get(token)

        if isinstance(configured, str) and configured.strip():
            return configured.strip()

        snake_key = self._snake_case_key(token)

        if snake_key != token:
            configured = fields.get(snake_key)

            if isinstance(configured, str) and configured.strip():
                return configured.strip()

        return None

    def resolve_field_labels(
        self,
        keys: list[str],
        *,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        enable_discovery: bool = True,
    ) -> dict[str, str]:
        """Cascata canônica R17: catálogo → humanize → discovery (web+LLM)."""
        ordered: list[str] = []
        seen: set[str] = set()

        for raw in keys:
            token = str(raw or "").strip()

            if not token or token in seen:
                continue

            seen.add(token)
            ordered.append(token)

        if not ordered:
            return {}

        profile_hints = self.column_label_hints(profile_name) if profile_name else {}
        label_map: dict[str, str] = {}
        pending_discovery: list[str] = []

        for key in ordered:
            catalog = self._resolve_catalog_label(
                key,
                profile_name=profile_name,
                schema_labels=schema_labels,
            )

            if catalog:
                label_map[key] = catalog
                continue

            pending_discovery.append(key)
            label_map[key] = self._humanize_field_key(key)

        if enable_discovery and pending_discovery:
            catalog_fields = (_column_labels_content().get("fields") or {})
            discovered = PresentationColumnLabelDiscoveryService.resolve_labels(
                pending_discovery,
                path=path,
                schema_labels=schema_labels,
                profile_labels=profile_hints,
                fields=catalog_fields,
            )

            for key, label in discovered.items():
                if str(label or "").strip():
                    label_map[key] = str(label).strip()

        return label_map

    @classmethod
    def is_catalog_field_resolved(
        cls,
        key: str,
        *,
        schema_labels: dict[str, str] | None = None,
        profile_name: str | None = None,
        profile_label: str | None = None,
        fields: dict[str, str] | None = None,
        snake_key: str | None = None,
    ) -> bool:
        token = str(key or "").strip()

        if not token:
            return True

        if str(profile_label or "").strip():
            return True

        if cls()._resolve_catalog_label(
            token,
            profile_name=profile_name,
            schema_labels=schema_labels,
        ):
            return True

        catalog = fields or {}

        if str(catalog.get(token) or "").strip():
            return True

        if snake_key and snake_key != token and str(catalog.get(snake_key) or "").strip():
            return True

        return False

    def is_catalog_label_resolved(
        self,
        key: str,
        *,
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
    ) -> bool:
        return self.is_catalog_field_resolved(
            key,
            profile_name=profile_name,
            schema_labels=schema_labels,
        )

    def resolve_field_format(
        self,
        key: str,
        *,
        schema_formats: dict[str, str] | None = None,
    ) -> str | None:
        normalized_key = str(key or "").strip()

        if not normalized_key:
            return None

        if schema_formats:
            configured = schema_formats.get(normalized_key)

            if isinstance(configured, str) and configured.strip():
                return configured.strip()

            snake_key = self._snake_case_key(normalized_key)

            if snake_key != normalized_key:
                configured = schema_formats.get(snake_key)

                if isinstance(configured, str) and configured.strip():
                    return configured.strip()

        content = _column_labels_content()
        formats = content.get("fieldFormats") or {}
        configured = formats.get(normalized_key)

        if isinstance(configured, str) and configured.strip():
            return configured.strip()

        snake_key = self._snake_case_key(normalized_key)

        if snake_key != normalized_key:
            configured = formats.get(snake_key)

            if isinstance(configured, str) and configured.strip():
                return configured.strip()

        return self._infer_field_format(normalized_key)

    @classmethod
    def unwrap_nested_scalar(cls, value: object) -> object:
        """Extrai escalar de envelopes aninhados (ex.: realized/goals.consolidated)."""
        if not isinstance(value, dict) or not value:
            return value

        preferred_keys = (
            "consolidated",
            "value",
            "amount",
            "total",
            "score",
            "realized",
        )

        for key in preferred_keys:
            if key not in value:
                continue

            nested = value.get(key)

            if isinstance(nested, dict):
                return cls.unwrap_nested_scalar(nested)

            return nested

        if len(value) == 1:
            sole = next(iter(value.values()))

            if isinstance(sole, dict):
                return cls.unwrap_nested_scalar(sole)

            return sole

        return value

    def format_field_value(
        self,
        key: str,
        value: object,
        *,
        schema_formats: dict[str, str] | None = None,
    ) -> str:
        if value is None:
            return "—"

        if isinstance(value, bool):
            return "Sim" if value else "Não"

        if isinstance(value, (list, dict)):
            unwrapped = self.unwrap_nested_scalar(value)

            if unwrapped is not value and not isinstance(unwrapped, (list, dict)):
                return self.format_field_value(
                    key,
                    unwrapped,
                    schema_formats=schema_formats,
                )

            if isinstance(value, dict):
                parts: list[str] = []

                for nested_key, nested_value in value.items():
                    label = str(nested_key or "").strip() or "—"
                    parts.append(
                        f"{label}: {self.format_field_value(key, nested_value, schema_formats=schema_formats)}"
                    )

                return "; ".join(parts) if parts else "—"

            if isinstance(value, list):
                if not value:
                    return "—"

                return "; ".join(
                    self.format_field_value(key, item, schema_formats=schema_formats)
                    for item in value
                )

            return str(value)

        field_format = self.resolve_field_format(
            key,
            schema_formats=schema_formats,
        )

        if isinstance(value, (int, float)):
            number = float(value)

            if field_format == "currency":
                return f"R$ {self._format_br_number(number)}"

            if field_format == "percent":
                return f"{self._format_br_number(number)}%"

            if field_format == "quantity":
                if number == int(number):
                    return f"{int(number):,}".replace(",", ".")
                return self._format_br_number(number)

            if field_format == "days":
                if number == int(number):
                    return f"{int(number)} dias"
                return f"{self._format_br_number(number)} dias"

            if number == int(number):
                return f"{int(number):,}".replace(",", ".")

            return self._format_br_number(number)

        text = str(value).strip()

        if field_format == "date" and text:
            # Já no padrão de exibição BR (ex.: LMP dd/mm/yyyy).
            if re.match(r"^\d{2}/\d{2}/\d{4}$", text):
                return text

            if len(text) == 8 and text.isdigit():
                return f"{text[6:8]}/{text[4:6]}/{text[0:4]}"

            if re.match(r"^\d{4}-\d{2}-\d{2}", text):
                parts = text[:10].split("-")

                if len(parts) == 3:
                    return f"{parts[2]}/{parts[1]}/{parts[0]}"

        return text

    def merge_meta_field_formats(
        self,
        schema_formats: dict[str, str] | None,
        data,
    ) -> dict[str, str]:
        formats = dict(schema_formats or {})
        payload = data if isinstance(data, dict) else {}
        meta = payload.get("meta")

        if not isinstance(meta, dict):
            return formats

        configured = meta.get("fieldFormats")

        if not isinstance(configured, dict):
            return formats

        for key, value in configured.items():
            if isinstance(key, str) and isinstance(value, str) and value.strip():
                formats[key] = value.strip()

        return formats

    def kv_table_column_defs(self) -> list[dict[str, str]]:
        cfg = (_column_labels_content().get("presenter") or {}).get("kvTableColumns") or {}

        return [
            {"key": "campo", "label": str(cfg.get("field") or "Campo")},
            {"key": "valor", "label": str(cfg.get("value") or "Valor")},
        ]

    def product_profile_field_keys(self, *, extended: bool = False) -> list[str]:
        presenter = _column_labels_content().get("presenter") or {}
        keys_cfg = presenter.get("productProfileKeys") or {}
        variant = "extended" if extended else "standard"
        raw = keys_cfg.get(variant) or keys_cfg.get("standard") or []

        return [str(key).strip() for key in raw if str(key).strip()]

    def build_kv_profile_rows(
        self,
        product: dict,
        *,
        extended: bool = False,
        skip_empty: bool = True,
        schema_labels: dict[str, str] | None = None,
        path: str = "",
        profile_name: str | None = None,
    ) -> list[dict[str, object]]:
        if not isinstance(product, dict):
            return []

        keys = self.product_profile_field_keys(extended=extended)
        label_map = self.resolve_field_labels(
            keys,
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
        )
        rows: list[dict[str, object]] = []

        for key in keys:
            value = product.get(key)

            if skip_empty and value in (None, ""):
                continue

            rows.append(
                {
                    "campo": label_map.get(key) or self._humanize_field_key(key),
                    "valor": value,
                }
            )

        return rows

    def format_collection_total(self, total: object) -> str:
        presenter = _column_labels_content().get("presenter") or {}
        template = str(presenter.get("collectionTotalValue") or "{total} registro(s)")

        return template.replace("{total}", str(total))

    def fixed_table_columns(
        self,
        table_id: str,
        *,
        schema_labels: dict[str, str] | None = None,
    ) -> list[dict[str, str]]:
        """Compat: defs de coluna a partir de `tableProfiles` (hints de ordem/rotulo)."""
        hints = self.column_order_hints(table_id)

        if not hints:
            return []

        columns: list[dict[str, str]] = []

        for key in hints:
            label = self.resolve_label_for_column(
                key,
                profile_name=table_id,
                schema_labels=schema_labels,
            )
            columns.append(self.enrich_column(key, label))

        return columns

    def markdown_column_pairs(
        self,
        table_id: str,
        *,
        schema_labels: dict[str, str] | None = None,
    ) -> list[tuple[str, str]]:
        return [
            (column["key"], column["label"])
            for column in self.fixed_table_columns(
                table_id,
                schema_labels=schema_labels,
            )
        ]

    def merge_meta_field_labels(
        self,
        schema_labels: dict[str, str] | None,
        data,
    ) -> dict[str, str]:
        labels = dict(schema_labels or {})
        payload = data if isinstance(data, dict) else {}
        meta = payload.get("meta")

        if not isinstance(meta, dict):
            return labels

        fields = meta.get("fields")

        if not isinstance(fields, dict):
            return labels

        for key, value in fields.items():
            if isinstance(key, str) and isinstance(value, str) and value.strip():
                labels[key] = value.strip()

        return labels

    def resolve_schema_labels(self, response_schema: dict | None) -> dict[str, str]:
        if not isinstance(response_schema, dict):
            return {}

        labels: dict[str, str] = {}

        for status_code, response in response_schema.items():
            if not str(status_code).startswith(("2", "default")):
                continue

            if not isinstance(response, dict):
                continue

            content = response.get("content") or {}

            if not isinstance(content, dict):
                continue

            for media in content.values():
                if not isinstance(media, dict):
                    continue

                schema = media.get("schema")

                if isinstance(schema, dict):
                    self._collect_schema_property_labels(schema, labels)

        return labels

    def detect_table_profile(self, row: dict, *, path: str = "") -> str | None:
        if not isinstance(row, dict):
            return None

        content = _column_labels_content()
        profiles = content.get("tableProfiles") or {}
        priority = content.get("profilePriority") or list(profiles.keys())
        lowered_path = str(path or "").lower()

        for profile_name in priority:
            profile = profiles.get(profile_name)

            if not isinstance(profile, dict):
                continue

            detect = profile.get("detect") or {}

            if not self._profile_matches(row, detect, lowered_path):
                continue

            return str(profile_name)

        return None

    def preferred_columns(
        self,
        profile_name: str,
        row: dict,
        *,
        schema_labels: dict[str, str] | None = None,
    ) -> list[tuple[str, str]]:
        if not isinstance(row, dict):
            return []

        columns: list[tuple[str, str]] = []

        for key in self.column_order_hints(profile_name):
            if key not in row:
                continue

            label = self.resolve_label_for_column(
                key,
                profile_name=profile_name,
                schema_labels=schema_labels,
            )
            columns.append((key, label))

        return columns

    def column_order_hints(self, profile_name: str | None) -> list[str]:
        token = str(profile_name or "").strip()

        if not token:
            return []

        content = _column_labels_content()
        profile = (content.get("tableProfiles") or {}).get(token) or {}
        configured = profile.get("preferredColumns") or []
        hints: list[str] = []

        for item in configured:
            if isinstance(item, (list, tuple)) and len(item) >= 1:
                key = str(item[0]).strip()
            elif isinstance(item, str) and item.strip():
                key = item.strip()
            else:
                continue

            if key and key not in hints:
                hints.append(key)

        if hints:
            return hints

        return []

    def column_label_hints(self, profile_name: str | None) -> dict[str, str]:
        token = str(profile_name or "").strip()

        if not token:
            return {}

        content = _column_labels_content()
        profile = (content.get("tableProfiles") or {}).get(token) or {}
        configured = profile.get("preferredColumns") or []
        labels: dict[str, str] = {}

        for item in configured:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                key = str(item[0]).strip()
                label = str(item[1]).strip()

                if key and label:
                    labels[key] = label

        return labels

    def resolve_label_for_column(
        self,
        key: str,
        *,
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        path: str = "",
    ) -> str:
        return self.resolve_field_labels(
            [key],
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
        ).get(str(key or "").strip(), self._humanize_field_key(str(key or "")))

    def resolve_columns_for_items(
        self,
        items: list[dict[str, Any]],
        *,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        skip_keys: frozenset[str] | None = None,
    ) -> list[dict[str, str]]:
        dict_items = [item for item in items if isinstance(item, dict)]

        if not dict_items:
            return []

        skipped = skip_keys or (frozenset({"_detailMeta"}) | self._NESTED_HIERARCHY_SKIP_KEYS)
        discovered: list[str] = []
        present: set[str] = set()

        for item in dict_items:
            for key in item:
                token = str(key or "").strip()

                if not token or token.startswith("_") or token in skipped:
                    continue

                if token not in present:
                    present.add(token)
                    discovered.append(token)

        resolved_profile = profile_name

        if not resolved_profile:
            resolved_profile = self.detect_table_profile(dict_items[0], path=path)

        label_hints_profile = resolved_profile
        ordered_keys: list[str] = []

        for key in self.column_order_hints(resolved_profile):
            if key in present and key not in ordered_keys:
                ordered_keys.append(key)

        for key in discovered:
            if key not in ordered_keys:
                ordered_keys.append(key)

        profile_hints = self.column_label_hints(resolved_profile)
        label_map = self.resolve_field_labels(
            ordered_keys,
            path=path,
            profile_name=label_hints_profile,
            schema_labels=schema_labels,
        )

        columns: list[dict[str, str]] = []

        for key in ordered_keys:
            columns.append(self.enrich_column(key, label_map[key]))

        return columns

    def _profile_matches(
        self,
        row: dict,
        detect: dict,
        lowered_path: str,
    ) -> bool:
        path_contains = detect.get("pathContains") or []

        if path_contains and not any(token in lowered_path for token in path_contains):
            return False

        any_keys = detect.get("anyKeys") or []

        if any_keys and any(key in row for key in any_keys):
            exclude_if = detect.get("excludeIfAnyKeys") or []

            if exclude_if and any(key in row for key in exclude_if):
                return False

            return True

        for group in detect.get("anyKeyGroups") or []:
            if not isinstance(group, (list, tuple)):
                continue

            if all(key in row for key in group):
                return True

        exclude_if = detect.get("excludeIfAnyKeys") or []

        if exclude_if and any(key in row for key in exclude_if):
            return False

        required_all = detect.get("allKeys") or []

        if required_all and all(key in row for key in required_all):
            return True

        return False

    @classmethod
    def _infer_field_format(cls, key: str) -> str | None:
        lowered = str(key or "").strip().lower()

        if not lowered:
            return None

        if (
            lowered.endswith("_percent")
            or lowered.endswith("_pct")
            or lowered.endswith("_percentage")
        ):
            return "percent"

        if lowered.endswith("_date") or lowered.endswith("_at"):
            return "date"

        for field_format, tokens in cls._FIELD_FORMAT_TOKENS.items():
            if any(token in lowered for token in tokens):
                return field_format

        return None

    @staticmethod
    def _format_br_number(value: float) -> str:
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return formatted

    @staticmethod
    def _snake_case_key(key: str) -> str:
        normalized = str(key or "").strip()

        if not normalized:
            return ""

        step_one = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", normalized)
        step_two = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step_one)

        return step_two.replace("-", "_").lower()

    @staticmethod
    def _humanize_field_key(key: str) -> str:
        normalized = str(key or "").strip()

        if not normalized:
            return ""

        if "_" in normalized:
            parts = [part for part in normalized.split("_") if part]

            return " ".join(part.capitalize() for part in parts)

        spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", normalized)
        parts = [part for part in spaced.split() if part]

        if not parts:
            return normalized

        return " ".join(part.capitalize() for part in parts)

    def _collect_schema_property_labels(
        self,
        schema: dict,
        labels: dict[str, str],
        *,
        depth: int = 0,
    ) -> None:
        if depth > 8 or not isinstance(schema, dict):
            return

        properties = schema.get("properties")

        if isinstance(properties, dict):
            for key, spec in properties.items():
                if not isinstance(spec, dict):
                    continue

                title = spec.get("title") or spec.get("x-label") or spec.get("x-ptLabel")

                if isinstance(title, str) and title.strip():
                    labels[str(key)] = title.strip()

                if spec.get("type") == "array":
                    items = spec.get("items")

                    if isinstance(items, dict):
                        self._collect_schema_property_labels(
                            items,
                            labels,
                            depth=depth + 1,
                        )
                elif spec.get("type") == "object":
                    self._collect_schema_property_labels(
                        spec,
                        labels,
                        depth=depth + 1,
                    )

        items = schema.get("items")

        if isinstance(items, dict):
            self._collect_schema_property_labels(items, labels, depth=depth + 1)

    _COLUMN_TYPE_MAP: dict[str, tuple[str, ...]] = {
        "currency": (
            "valor", "preco", "price", "custo", "cost", "total", "revenue",
            "faturamento", "receita", "vlr", "vl_", "last_purchase_price",
            "standard_cost", "unit_price", "net_value", "gross_value",
        ),
        "percent": (
            "pct", "percent", "taxa", "rate", "margem", "margin", "otd",
            "giro", "eficiencia", "yield",
        ),
        "date": (
            "data", "date", "emissao", "criacao", "atualizacao", "inicio",
            "fim", "vencimento", "dt_", "created", "updated", "last_revision",
        ),
        "quantity": (
            "qtd", "quantidade", "qty", "quantity", "saldo", "disponivel",
            "reservado", "estoque", "volume", "current_quantity",
            "available_quantity", "committed_quantity", "reserved_quantity",
        ),
    }

    def infer_column_type(self, key: str) -> str | None:
        lowered = key.lower()

        for data_type, tokens in self._COLUMN_TYPE_MAP.items():
            if any(token in lowered for token in tokens):
                return data_type

        return None

    def enrich_column(self, key: str, label: str) -> dict:
        col = {"key": key, "label": label}
        data_type = self.infer_column_type(key)

        if data_type:
            col["dataType"] = data_type

        return col

    @staticmethod
    def format_num(value) -> str:
        try:
            num = float(value)

            if num == int(num):
                abs_formatted = f"{abs(int(num)):,}".replace(",", ".")

                if num < 0:
                    return f"-{abs_formatted}"

                return abs_formatted

            return ExternalActionColumnLabelService._format_br_number(num)
        except (ValueError, TypeError):
            return str(value)
