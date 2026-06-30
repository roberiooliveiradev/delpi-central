from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


def _api_delpi_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _templates_dir() -> Path:
    return _api_delpi_root() / "app" / "content" / "templates" / "quality"


def _catalog_path() -> Path:
    return _api_delpi_root() / "app" / "content" / "quality" / "export_templates.json"


@lru_cache(maxsize=1)
def load_export_template_catalog() -> dict[str, Any]:
    path = _catalog_path()
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def list_export_templates() -> list[dict[str, Any]]:
    catalog = load_export_template_catalog()
    items: list[dict[str, Any]] = []
    for entry in catalog.get("templates") or []:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("key") or "").strip()
        if not key:
            continue
        items.append(
            {
                "key": key,
                "label": str(entry.get("label") or key),
                "description": str(entry.get("description") or ""),
                "customer_name_hints": list(entry.get("customerNameHints") or []),
                "customer_codes": list(entry.get("customerCodes") or []),
            }
        )
    return items


def get_export_template_entry(template_key: str) -> dict[str, Any] | None:
    key = (template_key or "").strip()
    if not key:
        return None
    for entry in load_export_template_catalog().get("templates") or []:
        if isinstance(entry, dict) and str(entry.get("key") or "").strip() == key:
            return entry
    return None


def resolve_export_template_path(template_key: str) -> Path:
    entry = get_export_template_entry(template_key)
    if entry is None:
        raise KeyError(f"Template de exportação desconhecido: {template_key}")

    env_override = (os.environ.get("RNC_8D_TEMPLATE_PATH") or "").strip()
    if env_override and template_key == load_export_template_catalog().get("defaultTemplateKey"):
        return Path(env_override)

    filename = str(entry.get("file") or "").strip()
    if not filename:
        raise FileNotFoundError(f"Arquivo do template não configurado: {template_key}")

    path = _templates_dir() / filename
    if path.is_file():
        return path

    fixture = _api_delpi_root() / "tests" / "fixtures" / "quality" / "rnc_8d_template_minimal.xlsx"
    if fixture.is_file():
        return fixture

    raise FileNotFoundError(f"Template 8D não encontrado: {path}")


def resolve_export_template_key_for_plan(
    plan: dict[str, Any],
    *,
    requested_key: str | None = None,
) -> str:
    explicit = (requested_key or "").strip()
    if explicit:
        if get_export_template_entry(explicit) is None:
            raise KeyError(f"Template de exportação desconhecido: {explicit}")
        return explicit

    plan_key = str(plan.get("export_template_key") or "").strip()
    if plan_key:
        if get_export_template_entry(plan_key) is None:
            raise KeyError(f"Template de exportação do plano inválido: {plan_key}")
        return plan_key

    customer_name = str(plan.get("customer_name") or "").casefold()
    customer_code = str(plan.get("customer_code") or "").strip()
    for entry in load_export_template_catalog().get("templates") or []:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("key") or "").strip()
        if not key:
            continue
        codes = {str(code).strip() for code in (entry.get("customerCodes") or []) if str(code).strip()}
        if customer_code and customer_code in codes:
            return key
        hints = [str(hint).casefold() for hint in (entry.get("customerNameHints") or []) if str(hint).strip()]
        if hints and any(hint in customer_name for hint in hints):
            return key

    default_key = str(load_export_template_catalog().get("defaultTemplateKey") or "weg_wfr20997").strip()
    if get_export_template_entry(default_key) is None:
        templates = list_export_templates()
        if not templates:
            raise KeyError("Catálogo de templates 8D vazio.")
        return templates[0]["key"]
    return default_key
