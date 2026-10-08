# tv_app/application/product_guide/product_guide_schema.py
"""Canonical ``product_guide_v1`` contract for TV Dashboard — bounded validation.

A Product Guide is PRODUCT_USAGE_GUIDANCE: it teaches how/when/why to use the
TV Dashboard correctly. It is never domain truth, never authorization, never
execution policy and never method authority. Live contracts (get_catalog /
capability surface), api-delpi/OpenAPI data contracts and authoritative
domain reads always win over guide text.

Pattern proven by TÉO (tm_app.application.product_guide); this implementation
is owned by tv-dashboard-api and validates references existence-deep against
the canonical VISTA registries — never against copied lists.
"""

from __future__ import annotations

from typing import Any, Mapping

PRODUCT_GUIDE_SCHEMA = "product_guide_v1"
PRODUCT_GUIDE_AUTHORITY = "GUIDANCE_NOT_DOMAIN_TRUTH"

GUIDE_SECTIONS = (
    "overview",
    "when_to_use",
    "how_to_use",
    "field_guidance",
    "quality",
    "relationships",
    "all",
)

_MAX_ID_CHARS = 64
_MAX_STRING_CHARS = 600
_MAX_LIST_ITEMS = 24
_MAX_FIELD_GUIDANCE = 24
_MAX_REFS = 24

# Reference namespaces — each validated against a distinct canonical registry:
# - capability_refs: ids inside capability_surface (entities/workflows/analyses)
# - operation_refs: typed mutation ops (presentation_ops_content.json)
# - read_refs: neutral read/analysis tool names (parity_map values)
# - write_refs: governed write envelope names (PREPARE/ACT only)
# ui_refs is intentionally absent in V1: no canonical UI registry exists to
# validate against, so unvalidated path strings are not part of the contract.
REFERENCE_FIELDS = ("capability_refs", "operation_refs", "read_refs", "write_refs")

# Fields the agent receives via `section` filtering. `overview` is the
# default projection; `all` returns the complete validated guide.
_SECTION_FIELDS: dict[str, tuple[str, ...]] = {
    "overview": ("id", "title", "summary", "authority", "purpose"),
    "when_to_use": ("id", "title", "use_when", "do_not_use_when"),
    "how_to_use": ("id", "title", "how_to_use", "agent_guidance"),
    "field_guidance": ("id", "title", "field_guidance"),
    "quality": ("id", "title", "quality_rules", "common_mistakes"),
    "relationships": (
        "id",
        "title",
        "related_topics",
        "capability_refs",
        "operation_refs",
        "read_refs",
        "write_refs",
    ),
}


class ProductGuideValidationError(ValueError):
    """Raised when a guide payload violates the product_guide_v1 contract."""


def _fail(message: str) -> ProductGuideValidationError:
    return ProductGuideValidationError(message)


def _req_string(
    raw: Mapping[str, Any], key: str, max_chars: int = _MAX_STRING_CHARS
) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise _fail(f"{key} is required (non-empty string)")
    value = value.strip()
    if len(value) > max_chars:
        raise _fail(f"{key} exceeds {max_chars} chars")
    return value


def _opt_string(raw: Mapping[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise _fail(f"{key} must be a string")
    value = value.strip()
    return value or None


def _string_list(
    raw: Mapping[str, Any], key: str, *, required: bool = False
) -> list[str]:
    value = raw.get(key)
    if value is None:
        if required:
            raise _fail(f"{key} is required")
        return []
    if not isinstance(value, (list, tuple)):
        raise _fail(f"{key} must be a list of strings")
    if len(value) > _MAX_LIST_ITEMS:
        raise _fail(f"{key} exceeds {_MAX_LIST_ITEMS} items")
    out = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise _fail(f"{key} entries must be non-empty strings")
        item = item.strip()
        if len(item) > _MAX_STRING_CHARS:
            raise _fail(f"{key} entry exceeds {_MAX_STRING_CHARS} chars")
        out.append(item)
    return out


def _field_guidance(raw: Any) -> list[dict[str, str]]:
    if raw is None:
        return []
    if not isinstance(raw, (list, tuple)) or len(raw) > _MAX_FIELD_GUIDANCE:
        raise _fail("field_guidance must be a bounded list")
    out = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise _fail("field_guidance entries must be objects")
        unknown = set(item) - {"field", "guidance", "contract_ref"}
        if unknown:
            raise _fail(f"field_guidance unknown keys: {sorted(unknown)}")
        field = item.get("field")
        guidance = item.get("guidance")
        if not isinstance(field, str) or not field.strip():
            raise _fail("field_guidance.field is required")
        if not isinstance(guidance, str) or not guidance.strip():
            raise _fail("field_guidance.guidance is required")
        out.append(
            {
                "field": field.strip(),
                "guidance": guidance.strip(),
                **(
                    {"contract_ref": item["contract_ref"].strip()}
                    if isinstance(item.get("contract_ref"), str)
                    and item["contract_ref"].strip()
                    else {}
                ),
            }
        )
    return out


def _source_refs(raw: Any) -> list[dict[str, str]]:
    """Each source ref records where the guidance came from + its class."""
    if raw is None:
        return []
    if not isinstance(raw, (list, tuple)) or len(raw) > _MAX_REFS:
        raise _fail("source_refs must be a bounded list")
    out = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise _fail("source_refs entries must be objects")
        unknown = set(item) - {"ref", "classification"}
        if unknown:
            raise _fail(f"source_refs unknown keys: {sorted(unknown)}")
        ref = item.get("ref")
        classification = item.get("classification")
        if not isinstance(ref, str) or not ref.strip():
            raise _fail("source_refs.ref is required")
        if classification not in ("PROVEN", "INFERRED", "PROPOSED"):
            raise _fail(
                "source_refs.classification must be PROVEN|INFERRED|PROPOSED"
            )
        out.append({"ref": ref.strip(), "classification": classification})
    return out


def parse_product_guide(raw: Any) -> dict[str, Any]:
    """Validate a ``product_guide_v1`` guide payload. Fail-closed."""
    if not isinstance(raw, Mapping):
        raise _fail("product guide must be a JSON object")
    unknown = set(raw) - {
        "schema",
        "id",
        "title",
        "summary",
        "authority",
        "purpose",
        "use_when",
        "do_not_use_when",
        "how_to_use",
        "field_guidance",
        "quality_rules",
        "common_mistakes",
        "related_topics",
        *REFERENCE_FIELDS,
        "source_refs",
        "agent_guidance",
    }
    if unknown:
        raise _fail(f"unknown product guide keys: {sorted(unknown)}")
    if raw.get("schema") != PRODUCT_GUIDE_SCHEMA:
        raise _fail(f"schema must be {PRODUCT_GUIDE_SCHEMA!r}")
    guide_id = _req_string(raw, "id", _MAX_ID_CHARS)
    if not all(ch.isalnum() or ch in "-_" for ch in guide_id):
        raise _fail("id must be alphanumeric/-/_")
    authority = _req_string(raw, "authority", _MAX_ID_CHARS)
    if authority != PRODUCT_GUIDE_AUTHORITY:
        raise _fail(f"authority must be {PRODUCT_GUIDE_AUTHORITY!r}")

    return {
        "schema": PRODUCT_GUIDE_SCHEMA,
        "id": guide_id,
        "title": _req_string(raw, "title"),
        "summary": _req_string(raw, "summary"),
        "authority": authority,
        "purpose": _req_string(raw, "purpose"),
        "use_when": _string_list(raw, "use_when"),
        "do_not_use_when": _string_list(raw, "do_not_use_when"),
        "how_to_use": _string_list(raw, "how_to_use"),
        "field_guidance": _field_guidance(raw.get("field_guidance")),
        "quality_rules": _string_list(raw, "quality_rules"),
        "common_mistakes": _string_list(raw, "common_mistakes"),
        "related_topics": _string_list(raw, "related_topics"),
        "capability_refs": _string_list(raw, "capability_refs"),
        "operation_refs": _string_list(raw, "operation_refs"),
        "read_refs": _string_list(raw, "read_refs"),
        "write_refs": _string_list(raw, "write_refs"),
        "source_refs": _source_refs(raw.get("source_refs")),
        "agent_guidance": _opt_string(raw, "agent_guidance"),
    }


def project_section(guide: dict[str, Any], section: str | None) -> dict[str, Any]:
    """Return the guide filtered to a section. ``None``/``all`` → full guide."""
    if section in (None, "", "all"):
        return guide
    fields = _SECTION_FIELDS.get(section)
    if fields is None:
        raise _fail(
            f"unknown section {section!r}; expected one of {list(GUIDE_SECTIONS)}"
        )
    return {
        k: guide[k]
        for k in fields
        if k in guide and guide[k] not in (None, [], {})
    }
