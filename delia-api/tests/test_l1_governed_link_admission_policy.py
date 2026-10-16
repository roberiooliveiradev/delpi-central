"""L1 governed-link admission policy probes (proposal — not runtime).

DELIA-UX-CONVERSATION-MARKDOWN-B2-L1-BINDING-INVENTORY-01 / docs 84 §2.4 / doc 90.

These probes encode the Product Master L1 decision as an executable
policy table. They do NOT wire presentation.v2, ConversationMarkdown,
or any emission path. A fixture with a synthetic allowlist proves
admission rules; it does NOT prove a real Domain→capability→structured
binding exists (that remains PARTIAL / TO_INVENTORY — see doc 90).
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import pytest

# ---------------------------------------------------------------------------
# Proposed admission policy (documentation-executable; not imported by app)
# ---------------------------------------------------------------------------

_MAX_HREF_CHARS = 2000
_FORBIDDEN_SCHEMES = frozenset(
    {
        "javascript",
        "data",
        "blob",
        "attachment",
        "file",
        "mailto",
        "http",  # B2 emission: https only for external
    }
)
_SENSITIVE_QUERY_KEYS = frozenset(
    {"token", "access_token", "refresh_token", "code", "password", "secret"}
)


@dataclass(frozen=True, slots=True)
class GovernedLinkBinding:
    """Synthetic allowlist entry — stands in for a future published binding."""

    owner_id: str
    capability_id: str
    field: str
    field_semantics: str
    disclosure_allowed: bool
    destination_kind: str  # "external_https" | "internal_portal"


# Allowlist is empty in production reality — one synthetic entry proves
# positive admission WHEN a binding is declared. Negatives prove that
# undeclared fields never admit.
_SYNTHETIC_ALLOWLIST: frozenset[tuple[str, str, str]] = frozenset(
    {
        ("api-delpi.mural_acessos", "synth.list_mural_links", "url"),
    }
)


def _has_binding(owner_id: str, capability_id: str, field: str) -> bool:
    return (owner_id, capability_id, field) in _SYNTHETIC_ALLOWLIST


def _reject_credentials_or_sensitive_query(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        return True
    if not parsed.query:
        return False
    for part in parsed.query.split("&"):
        key = part.split("=", 1)[0].strip().lower()
        if key in _SENSITIVE_QUERY_KEYS:
            return True
    return False


def admit_governed_link(
    *,
    owner_id: str | None,
    capability_id: str | None,
    field: str | None,
    field_semantics: str | None,
    href: object,
    disclosure_allowed: bool,
    source_kind: str,
) -> str:
    """Return admission outcome code for a candidate link field.

    Outcomes:
      admit_external | admit_internal | inert_label | reject_neutral
    """
    # Untrusted / non-contract sources never admit
    if source_kind in {
        "model_prose",
        "mcp_metadata",
        "tool_schema_name",
        "source_ref",
        "entity_ref",
        "workspace_entity_ref",
        "owner_hint",
        "generic_field_name",
    }:
        return "inert_label"

    if not owner_id or not capability_id or not field:
        return "inert_label"
    if field_semantics != "published_navigable_destination":
        return "inert_label"
    if not disclosure_allowed:
        return "inert_label"
    if not _has_binding(owner_id, capability_id, field):
        return "inert_label"

    if not isinstance(href, str) or not href.strip():
        return "inert_label"
    href = href.strip()
    if len(href) > _MAX_HREF_CHARS:
        return "inert_label"

    # Protocol-relative / ambiguous
    if href.startswith("//"):
        return "inert_label"

    # Internal portal path
    if href.startswith("/") and not href.startswith("//"):
        if "?" in href:
            q = href.split("?", 1)[1]
            for part in q.split("&"):
                key = part.split("=", 1)[0].strip().lower()
                if key in _SENSITIVE_QUERY_KEYS:
                    return "inert_label"
        return "admit_internal"

    parsed = urlparse(href)
    scheme = (parsed.scheme or "").lower()
    if scheme in _FORBIDDEN_SCHEMES or scheme == "":
        return "inert_label"
    if scheme != "https":
        return "inert_label"
    if not (parsed.netloc or "").strip():
        return "inert_label"
    if _reject_credentials_or_sensitive_query(href):
        return "inert_label"
    return "admit_external"


# ---------------------------------------------------------------------------
# Positive — only when synthetic binding + published semantics align
# ---------------------------------------------------------------------------


def test_positive_synthetic_binding_admits_https_external() -> None:
    assert (
        admit_governed_link(
            owner_id="api-delpi.mural_acessos",
            capability_id="synth.list_mural_links",
            field="url",
            field_semantics="published_navigable_destination",
            href="https://intranet.delpi.local/rh",
            disclosure_allowed=True,
            source_kind="capability_structured",
        )
        == "admit_external"
    )


def test_positive_synthetic_binding_admits_internal_portal_path() -> None:
    assert (
        admit_governed_link(
            owner_id="api-delpi.mural_acessos",
            capability_id="synth.list_mural_links",
            field="url",
            field_semantics="published_navigable_destination",
            href="/apps/mural-acessos/hubs/h1",
            disclosure_allowed=True,
            source_kind="capability_structured",
        )
        == "admit_internal"
    )


# ---------------------------------------------------------------------------
# Negatives — generic names / untrusted sources / hostile schemes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    ["url", "href", "link", "page_url", "imageUrl", "publicUrl"],
)
def test_generic_field_name_alone_never_admits(field: str) -> None:
    assert (
        admit_governed_link(
            owner_id=None,
            capability_id=None,
            field=field,
            field_semantics=None,
            href="https://evil.example/x",
            disclosure_allowed=True,
            source_kind="generic_field_name",
        )
        == "inert_label"
    )


@pytest.mark.parametrize(
    "source_kind",
    [
        "model_prose",
        "mcp_metadata",
        "tool_schema_name",
        "source_ref",
        "entity_ref",
        "workspace_entity_ref",
        "owner_hint",
    ],
)
def test_untrusted_sources_never_admit(source_kind: str) -> None:
    assert (
        admit_governed_link(
            owner_id="api-delpi.mural_acessos",
            capability_id="synth.list_mural_links",
            field="url",
            field_semantics="published_navigable_destination",
            href="https://intranet.delpi.local/rh",
            disclosure_allowed=True,
            source_kind=source_kind,
        )
        == "inert_label"
    )


@pytest.mark.parametrize(
    "href",
    [
        "javascript:alert(1)",
        "data:text/html,hi",
        "blob:https://x/y",
        "attachment:1",
        "file:///etc/passwd",
        "mailto:a@b.c",
        "http://insecure.example/x",  # http forbidden at emission (B2)
        "//evil.example/x",
        "./relative",
        "../escape",
        "#hash-only",
        "https://user:pass@evil.example/x",
        "https://evil.example/x?token=sekrit",
        "https://evil.example/x?access_token=sekrit",
        "",
        None,
    ],
)
def test_hostile_or_invalid_href_inert(href: object) -> None:
    assert (
        admit_governed_link(
            owner_id="api-delpi.mural_acessos",
            capability_id="synth.list_mural_links",
            field="url",
            field_semantics="published_navigable_destination",
            href=href,
            disclosure_allowed=True,
            source_kind="capability_structured",
        )
        == "inert_label"
    )


def test_missing_disclosure_inert() -> None:
    assert (
        admit_governed_link(
            owner_id="api-delpi.mural_acessos",
            capability_id="synth.list_mural_links",
            field="url",
            field_semantics="published_navigable_destination",
            href="https://intranet.delpi.local/rh",
            disclosure_allowed=False,
            source_kind="capability_structured",
        )
        == "inert_label"
    )


def test_unknown_owner_capability_inert() -> None:
    assert (
        admit_governed_link(
            owner_id="unknown.owner",
            capability_id="unknown.cap",
            field="url",
            field_semantics="published_navigable_destination",
            href="https://intranet.delpi.local/rh",
            disclosure_allowed=True,
            source_kind="capability_structured",
        )
        == "inert_label"
    )


def test_wrong_semantics_inert() -> None:
    assert (
        admit_governed_link(
            owner_id="api-delpi.mural_acessos",
            capability_id="synth.list_mural_links",
            field="url",
            field_semantics="image_asset_locator",
            href="https://intranet.delpi.local/rh",
            disclosure_allowed=True,
            source_kind="capability_structured",
        )
        == "inert_label"
    )


def test_real_world_gap_no_production_allowlist_entry() -> None:
    """Inventory fact: production allowlist is empty outside the synthetic
    probe entry. A real mural capability id is NOT registered — so a
    field that merely looks like the Domain API shape stays inert.
    """
    assert (
        admit_governed_link(
            owner_id="api-delpi.mural_acessos",
            capability_id="list_mural_acessos_links",  # real OpenAPI oid
            field="url",
            field_semantics="published_navigable_destination",
            href="https://intranet.delpi.local/rh",
            disclosure_allowed=True,
            source_kind="capability_structured",
        )
        == "inert_label"
    )
