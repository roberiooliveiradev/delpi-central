# tv_app/application/product_guide/product_guide_registry.py
"""Versioned Product Guide Registry — loads ``product_guide_v1`` files.

Content lives in ``tv_app/content/product_guides/*.json`` — adding a topic is
content + validation, not code. The registry validates every guide at load
(fail-closed) and enforces cross-references existence-deep against canonical
registries:

- unique ids; ``id == filename stem``;
- ``related_topics`` must resolve to known guide ids;
- ``capability_refs`` must resolve to ids inside the live capability surface
  (entities/workflows/analyses);
- ``operation_refs`` must resolve to typed ops in
  ``presentation_ops_content.json`` (PresentationMutation vocabulary);
- ``read_refs`` must resolve to neutral read/analysis capability names
  (canonical ``parity_map`` values minus the write envelope);
- ``write_refs`` must resolve to the governed write envelope names
  (``suggest_change`` / ``prepare_change`` / ``commit_proposal``).

Providers are injectable so tests can prove fail-closed behavior without the
live registries; defaults resolve lazily to avoid import cycles — the
catalog/capability surface stays the owner of capability identity.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from tv_app.application.product_guide.product_guide_schema import (
    ProductGuideValidationError,
    parse_product_guide,
)

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content" / "product_guides"
REGISTRY_VERSION = "product-guide-registry-v1"

# The only governed write entry points on the specialist surface — typed ops
# are vocabulary inside prepare_change.ops[], never direct write tools.
WRITE_ENVELOPE_NAMES = frozenset(
    {"suggest_change", "prepare_change", "commit_proposal"}
)


def _default_capability_ids() -> frozenset[str]:
    """Known capability ids from the live surface (lazy — avoids cycles)."""
    from tv_app.application.gpt_actions.capability_surface import (
        build_capability_surface,
    )

    surface = build_capability_surface(transport="mcp")
    ids: set[str] = set()
    for bucket in ("entities", "workflows", "analyses"):
        for item in surface.get(bucket) or ():
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
    return frozenset(ids)


def _default_operation_ids() -> frozenset[str]:
    """Typed mutation vocabulary from the canonical ops catalog."""
    from tv_app.application.services.data.presentation_ops_content_service import (
        PresentationOpsContentService,
    )

    return frozenset(
        str(k) for k in (PresentationOpsContentService.operations() or {})
    )


def _default_neutral_names() -> frozenset[str]:
    """Neutral capability names — canonical ``parity_map`` values."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
    )

    parity = VistaAgentIntelligenceService.document().get("surface_parity") or {}
    mapping = parity.get("parity_map") or {}
    return frozenset(str(v) for v in mapping.values())


class ProductGuideRegistry:
    def __init__(
        self,
        *,
        content_dir: Path | None = None,
        capability_ids: Callable[[], frozenset[str]] | None = None,
        operation_ids: Callable[[], frozenset[str]] | None = None,
        neutral_names: Callable[[], frozenset[str]] | None = None,
    ) -> None:
        self._dir = content_dir or CONTENT_DIR
        self._capability_ids = capability_ids or _default_capability_ids
        self._operation_ids = operation_ids or _default_operation_ids
        self._neutral_names = neutral_names or _default_neutral_names
        self._guides = self._load_all()

    def _load_all(self) -> dict[str, dict[str, Any]]:
        guides: dict[str, dict[str, Any]] = {}
        if not self._dir.is_dir():
            raise ProductGuideValidationError(
                f"product guide content dir missing: {self._dir}"
            )
        for path in sorted(self._dir.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            guide = parse_product_guide(raw)
            if guide["id"] in guides:
                raise ProductGuideValidationError(
                    f"duplicate product guide id: {guide['id']}"
                )
            if guide["id"] != path.stem:
                raise ProductGuideValidationError(
                    f"guide id {guide['id']!r} must match filename {path.stem!r}"
                )
            guides[guide["id"]] = guide
        if not guides:
            raise ProductGuideValidationError("no product guides found")

        known_ids = set(guides)
        known_caps = self._capability_ids()
        known_ops = self._operation_ids()
        neutral = self._neutral_names()
        read_names = neutral - WRITE_ENVELOPE_NAMES
        write_names = neutral & WRITE_ENVELOPE_NAMES
        for guide in guides.values():
            for ref in guide["related_topics"]:
                if ref not in known_ids:
                    raise ProductGuideValidationError(
                        f"{guide['id']}: unknown related_topic {ref!r}"
                    )
            for ref in guide["capability_refs"]:
                if ref not in known_caps:
                    raise ProductGuideValidationError(
                        f"{guide['id']}: unknown capability_ref {ref!r}"
                    )
            for ref in guide["operation_refs"]:
                if ref not in known_ops:
                    raise ProductGuideValidationError(
                        f"{guide['id']}: unknown operation_ref {ref!r}"
                    )
            for ref in guide["read_refs"]:
                if ref not in read_names:
                    raise ProductGuideValidationError(
                        f"{guide['id']}: unknown read_ref {ref!r}"
                    )
            for ref in guide["write_refs"]:
                if ref not in write_names:
                    raise ProductGuideValidationError(
                        f"{guide['id']}: unknown write_ref {ref!r}"
                    )
        return guides

    @property
    def version(self) -> str:
        return REGISTRY_VERSION

    def topic_ids(self) -> list[str]:
        return sorted(self._guides)

    def get(self, topic: str) -> dict[str, Any] | None:
        return self._guides.get(topic)

    def index(self) -> list[dict[str, str]]:
        return [
            {
                "id": g["id"],
                "title": g["title"],
                "summary": g["summary"],
                "authority": g["authority"],
            }
            for g in (self._guides[k] for k in self.topic_ids())
        ]


@lru_cache(maxsize=1)
def get_product_guide_registry() -> ProductGuideRegistry:
    return ProductGuideRegistry()


def clear_product_guide_registry_cache() -> None:
    get_product_guide_registry.cache_clear()
