"""Tradução de colunas operacionais — conteúdo editável + OpenAPI responseSchema."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


def invalidate_column_label_cache() -> None:
    _column_labels_content.cache_clear()


@lru_cache(maxsize=1)
def _column_labels_content() -> dict[str, Any]:
    return ContentService.load_json("assistant/column_labels")


class ExternalActionColumnLabelService:
    """Resolve labels de campos para tabelas do presenter operacional."""

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
            "discount",
            "desconto",
            "return",
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
    ) -> str:
        normalized_key = str(key or "").strip()

        if not normalized_key:
            return ""

        if schema_labels:
            schema_label = schema_labels.get(normalized_key)

            if isinstance(schema_label, str) and schema_label.strip():
                return schema_label.strip()

        content = _column_labels_content()
        fields = content.get("fields") or {}
        configured = fields.get(normalized_key)

        if isinstance(configured, str) and configured.strip():
            return configured.strip()

        snake_key = self._snake_case_key(normalized_key)

        if snake_key != normalized_key:
            configured = fields.get(snake_key)

            if isinstance(configured, str) and configured.strip():
                return configured.strip()

        return self._humanize_field_key(normalized_key)

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
    ) -> list[dict[str, object]]:
        if not isinstance(product, dict):
            return []

        rows: list[dict[str, object]] = []

        for key in self.product_profile_field_keys(extended=extended):
            value = product.get(key)

            if skip_empty and value in (None, ""):
                continue

            rows.append(
                {
                    "campo": self.label_for(key, schema_labels=schema_labels),
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
        presenter = _column_labels_content().get("presenter") or {}
        tables = presenter.get("fixedTableColumns") or {}
        raw = tables.get(table_id) or []
        columns: list[dict[str, str]] = []

        for column in raw:
            if not isinstance(column, dict):
                continue

            key = str(column.get("key") or "").strip()

            if not key:
                continue

            configured_label = column.get("label")
            label = (
                str(configured_label).strip()
                if isinstance(configured_label, str) and configured_label.strip()
                else self.label_for(key, schema_labels=schema_labels)
            )
            entry: dict[str, str] = {"key": key, "label": label}

            data_type = column.get("dataType")

            if isinstance(data_type, str) and data_type.strip():
                entry["dataType"] = data_type.strip()

            columns.append(entry)

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

        content = _column_labels_content()
        profile = (content.get("tableProfiles") or {}).get(profile_name) or {}
        configured = profile.get("preferredColumns") or []
        columns: list[tuple[str, str]] = []

        for item in configured:
            if isinstance(item, (list, tuple)) and len(item) >= 1:
                key = str(item[0]).strip()
            elif isinstance(item, str) and item.strip():
                key = item.strip()
            else:
                continue

            if key not in row:
                continue

            label = self.label_for(key, schema_labels=schema_labels)
            columns.append((key, label))

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
