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

    # Chaves exatas de agregação/contagem (COUNT(*) AS TOTAL) — nunca moeda.
    _EXACT_QUANTITY_KEYS = frozenset(
        {
            "total",
            "count",
            "cnt",
            "n",
            "registros",
            "row_count",
            "total_registros",
            "records",
        }
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

    _ALLOWED_FIELD_FORMATS = frozenset(
        {
            "currency",
            "percent",
            "date",
            "quantity",
            "days",
            "boolean",
        }
    )
    _NUMERIC_FIELD_FORMATS = frozenset(
        {
            "currency",
            "percent",
            "quantity",
            "days",
        }
    )
    _BOOLEAN_EXACT_KEYS = frozenset(
        {
            "active",
            "blocked",
            "enabled",
            "flag",
            "inactive",
        }
    )

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
            else self.label_for(
                normalized_key,
                schema_labels=schema_labels,
                enable_discovery=False,
            )
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
        enable_discovery: bool = False,
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

        del profile_name  # preferredColumns is order-only; not a translation catalog

        if schema_labels:
            schema_label = schema_labels.get(token)

            if isinstance(schema_label, str) and schema_label.strip():
                return schema_label.strip()

        return None

    def resolve_field_labels(
        self,
        keys: list[str],
        *,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        enable_discovery: bool = False,
        existing_labels: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Cascata: OpenAPI/meta → humanize → discovery (web+LLM). Sem catálogo JSON."""
        return self.resolve_field_label_bundle(
            keys,
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
            enable_discovery=enable_discovery,
            existing_labels=existing_labels,
        ).labels

    def resolve_field_label_bundle(
        self,
        keys: list[str],
        *,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        schema_formats: dict[str, str] | None = None,
        enable_discovery: bool = False,
        openapi_labels: dict[str, str] | None = None,
        existing_labels: dict[str, str] | None = None,
    ):
        """Resolve labels + formats com `sourceByKey` canônico (§26-R)."""
        from app.domain.entities.field_label_bundle import (
            FieldLabelBundle,
            canonicalize_label_source,
        )

        ordered: list[str] = []
        seen: set[str] = set()

        for raw in keys:
            token = str(raw or "").strip()
            if not token or token in seen:
                continue
            seen.add(token)
            ordered.append(token)

        if not ordered:
            return FieldLabelBundle()

        label_map: dict[str, str] = {}
        source_by_key: dict[str, str] = {}
        pending_discovery: list[str] = []
        _ = profile_name

        materialized = {
            str(token).strip(): str(value).strip()
            for token, value in (existing_labels or {}).items()
            if str(token or "").strip() and str(value or "").strip()
        }

        for key in ordered:
            label, source = self._resolve_catalog_label_with_source(
                key,
                schema_labels=schema_labels,
                openapi_labels=openapi_labels,
            )
            if label:
                label_map[key] = label
                source_by_key[key] = canonicalize_label_source(source or "meta")
                continue
            existing = materialized.get(key)
            if existing:
                label_map[key] = existing
                source_by_key[key] = canonicalize_label_source("discovery")
                continue
            pending_discovery.append(key)
            label_map[key] = self._humanize_field_key(key)
            source_by_key[key] = canonicalize_label_source("humanize")

        if enable_discovery and pending_discovery:
            discovered = PresentationColumnLabelDiscoveryService.resolve_labels(
                pending_discovery,
                path=path,
                schema_labels=schema_labels,
                profile_labels=None,
                fields=None,
            )
            pending_set = set(pending_discovery)
            for key, label in discovered.items():
                if key not in pending_set:
                    continue
                if str(label or "").strip():
                    label_map[key] = str(label).strip()
                    source_by_key[key] = canonicalize_label_source("discovery")

        formats: dict[str, str] = {}
        for key in ordered:
            fmt = self.resolve_field_format(key, schema_formats=schema_formats)
            if fmt:
                formats[key] = fmt

        return FieldLabelBundle(
            labels=label_map,
            formats=formats,
            source_by_key=source_by_key,
        )

    def _resolve_catalog_label_with_source(
        self,
        key: str,
        *,
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        openapi_labels: dict[str, str] | None = None,
    ) -> tuple[str | None, str | None]:
        token = str(key or "").strip()
        if not token:
            return None, None

        del profile_name

        if schema_labels:
            schema_label = schema_labels.get(token)
            if isinstance(schema_label, str) and schema_label.strip():
                openapi_hit = (
                    isinstance(openapi_labels, dict)
                    and str(openapi_labels.get(token) or "").strip() == schema_label.strip()
                )
                return schema_label.strip(), "openapi" if openapi_hit else "meta"

        if openapi_labels:
            openapi_label = openapi_labels.get(token)
            if isinstance(openapi_label, str) and openapi_label.strip():
                return openapi_label.strip(), "openapi"

        return None, None

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

        del profile_name, profile_label, fields, snake_key

        if cls()._resolve_catalog_label(
            token,
            schema_labels=schema_labels,
        ):
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

        if isinstance(value, str):
            text = value.strip()

            if field_format == "boolean":
                mapped = self._format_boolean_token(text)

                if mapped is not None:
                    return mapped

            if field_format in self._NUMERIC_FIELD_FORMATS:
                parsed = self._parse_numeric_string(
                    text,
                    allow_integer=field_format != "currency",
                )

                if parsed is not None:
                    return self.format_field_value(
                        key,
                        parsed,
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

        if field_format == "boolean":
            mapped = self._format_boolean_token(text)

            if mapped is not None:
                return mapped

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
        responses = response_schema.get("responses")
        if not isinstance(responses, dict):
            responses = response_schema

        for status_code, response in responses.items():
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
                    self._collect_schema_property_labels(
                        schema,
                        labels,
                        document_root=response_schema,
                    )

        return labels

    def resolve_schema_formats(self, response_schema: dict | None) -> dict[str, str]:
        if not isinstance(response_schema, dict):
            return {}

        formats: dict[str, str] = {}
        responses = response_schema.get("responses")
        if not isinstance(responses, dict):
            responses = response_schema

        for status_code, response in responses.items():
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
                    self._collect_schema_property_formats(
                        schema,
                        formats,
                        document_root=response_schema,
                    )

        return formats

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

    def order_keys_with_preferred_hints(
        self,
        present_keys: list[str],
        *,
        profile_name: str | None = None,
        sample_row: dict[str, Any] | None = None,
    ) -> list[str]:
        """Ordena chaves com preferredColumns como hints — nunca como allowlist."""
        ordered: list[str] = []
        present = [str(key).strip() for key in present_keys if str(key or "").strip()]
        present = self.drop_redundant_presentation_alias_keys(
            present,
            sample_row=sample_row,
        )
        present_set = set(present)

        for key in self.column_order_hints(profile_name):
            if key in present_set and key not in ordered:
                ordered.append(key)

        for key in present:
            if key not in ordered:
                ordered.append(key)

        return ordered

    def drop_redundant_presentation_alias_keys(
        self,
        keys: list[str],
        *,
        sample_row: dict[str, Any] | None = None,
    ) -> list[str]:
        """Remove aliases espelhados quando o canônico já está presente (e valores iguais)."""
        aliases = (_column_labels_content().get("redundantPresentationAliases") or {})
        if not isinstance(aliases, dict) or not aliases:
            return keys

        present = {str(key).strip() for key in keys if str(key or "").strip()}
        drop: set[str] = set()

        for alias_raw, canonical_raw in aliases.items():
            alias = str(alias_raw or "").strip()
            canonical = str(canonical_raw or "").strip()
            if not alias or not canonical or alias not in present or canonical not in present:
                continue
            if isinstance(sample_row, dict) and alias in sample_row and canonical in sample_row:
                if sample_row.get(alias) != sample_row.get(canonical):
                    continue
            drop.add(alias)

        if not drop:
            return keys

        return [key for key in keys if str(key).strip() not in drop]

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
            enable_discovery=False,
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
        ordered_keys = self.order_keys_with_preferred_hints(
            discovered,
            profile_name=resolved_profile,
            sample_row=dict_items[0],
        )

        label_map = self.resolve_field_labels(
            ordered_keys,
            path=path,
            profile_name=label_hints_profile,
            schema_labels=schema_labels,
            enable_discovery=True,
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

        if lowered in cls._EXACT_QUANTITY_KEYS:
            return "quantity"

        if (
            lowered.endswith("_percent")
            or lowered.endswith("_pct")
            or lowered.endswith("_percentage")
        ):
            return "percent"

        if lowered.endswith("_date") or lowered.endswith("_at"):
            return "date"

        if cls._infer_boolean_format(lowered):
            return "boolean"

        for field_format, tokens in cls._FIELD_FORMAT_TOKENS.items():
            if any(token in lowered for token in tokens):
                return field_format

        return None

    @classmethod
    def _infer_boolean_format(cls, lowered: str) -> bool:
        token = str(lowered or "").strip().lower()

        if not token:
            return False

        if token in cls._BOOLEAN_EXACT_KEYS:
            return True

        if "mandatory" in token:
            return True

        if token.endswith("_indicator") or token.endswith("_flag"):
            return True

        if token.endswith("_active") or token.startswith("active_"):
            return True

        return False

    @staticmethod
    def _format_boolean_token(text: str) -> str | None:
        token = str(text or "").strip().lower()

        if token in {"s", "sim", "true", "y", "yes", "1"}:
            return "Sim"

        if token in {"n", "nao", "não", "false", "no", "0"}:
            return "Não"

        return None

    @staticmethod
    def _parse_numeric_string(text: str, *, allow_integer: bool = True) -> float | None:
        stripped = str(text or "").strip()

        if not stripped:
            return None

        if re.fullmatch(r"-?\d+", stripped):
            if not allow_integer:
                return None

            return float(stripped)

        if re.fullmatch(r"-?\d+\.\d+", stripped):
            return float(stripped)

        if re.fullmatch(r"-?\d{1,3}(\.\d{3})+,\d+", stripped):
            return float(stripped.replace(".", "").replace(",", "."))

        if re.fullmatch(r"-?\d+,\d+", stripped):
            return float(stripped.replace(",", "."))

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

        # Alias SQL / token ALL CAPS (`CODIGO`, `GRUPO`): não tratar como camelCase
        # — o lookbehind `(?=[A-Z])` inseria espaço entre cada letra («C O D I G O»).
        if re.fullmatch(r"[A-Z][A-Z0-9]*", normalized):
            return normalized.capitalize() if normalized.isalpha() else normalized

        spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", normalized)
        parts = [part for part in spaced.split() if part]

        if not parts:
            return normalized

        return " ".join(part.capitalize() for part in parts)

    @staticmethod
    def _follow_local_schema_ref(
        node: dict,
        document_root: dict | None,
        *,
        seen: tuple[str, ...] = (),
    ) -> dict:
        if not isinstance(node, dict):
            return {}

        ref = node.get("$ref")
        if not isinstance(ref, str) or not ref.startswith("#/"):
            return node

        if ref in seen or not isinstance(document_root, dict):
            return node

        current: object = document_root
        for part in ref[2:].split("/"):
            token = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or token not in current:
                return node
            current = current[token]

        if not isinstance(current, dict):
            return node

        return ExternalActionColumnLabelService._follow_local_schema_ref(
            current,
            document_root,
            seen=seen + (ref,),
        )

    def _collect_schema_property_labels(
        self,
        schema: dict,
        labels: dict[str, str],
        *,
        depth: int = 0,
        document_root: dict | None = None,
    ) -> None:
        if depth > 8 or not isinstance(schema, dict):
            return

        root = document_root if isinstance(document_root, dict) else schema
        schema = self._follow_local_schema_ref(schema, root)

        properties = schema.get("properties")

        if isinstance(properties, dict):
            for key, spec in properties.items():
                if not isinstance(spec, dict):
                    continue

                spec = self._follow_local_schema_ref(spec, root)

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
                            document_root=root,
                        )
                elif spec.get("type") == "object" or spec.get("properties"):
                    self._collect_schema_property_labels(
                        spec,
                        labels,
                        depth=depth + 1,
                        document_root=root,
                    )

        items = schema.get("items")

        if isinstance(items, dict):
            self._collect_schema_property_labels(
                items,
                labels,
                depth=depth + 1,
                document_root=root,
            )

    def _collect_schema_property_formats(
        self,
        schema: dict,
        formats: dict[str, str],
        *,
        depth: int = 0,
        document_root: dict | None = None,
    ) -> None:
        if depth > 8 or not isinstance(schema, dict):
            return

        root = document_root if isinstance(document_root, dict) else schema
        schema = self._follow_local_schema_ref(schema, root)

        properties = schema.get("properties")

        if isinstance(properties, dict):
            for key, spec in properties.items():
                if not isinstance(spec, dict):
                    continue

                spec = self._follow_local_schema_ref(spec, root)
                field_format = self._format_from_property_spec(spec)

                if field_format:
                    formats[str(key)] = field_format

                if spec.get("type") == "array":
                    items = spec.get("items")

                    if isinstance(items, dict):
                        self._collect_schema_property_formats(
                            items,
                            formats,
                            depth=depth + 1,
                            document_root=root,
                        )
                elif spec.get("type") == "object" or spec.get("properties"):
                    self._collect_schema_property_formats(
                        spec,
                        formats,
                        depth=depth + 1,
                        document_root=root,
                    )

        items = schema.get("items")

        if isinstance(items, dict):
            self._collect_schema_property_formats(
                items,
                formats,
                depth=depth + 1,
                document_root=root,
            )

    @classmethod
    def _format_from_property_spec(cls, spec: dict) -> str | None:
        if not isinstance(spec, dict):
            return None

        for extra_key in ("x-dataType", "x-format"):
            raw = spec.get(extra_key)

            if isinstance(raw, str) and raw.strip().lower() in cls._ALLOWED_FIELD_FORMATS:
                return raw.strip().lower()

        fmt = spec.get("format")

        if isinstance(fmt, str):
            token = fmt.strip().lower()

            if token in cls._ALLOWED_FIELD_FORMATS:
                return token

            if token in {"date", "date-time"}:
                return "date"

        if spec.get("type") == "boolean":
            return "boolean"

        return None

    def infer_column_type(self, key: str) -> str | None:
        return self.resolve_field_format(key)

    def enrich_column(self, key: str, label: str) -> dict:
        return self.enrich_column_def(key, label=label)

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
