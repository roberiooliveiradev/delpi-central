# tm_app/application/product_guide/product_guide_registry.py
"""Versioned Product Usage Registry — loads ``product_guide_v1`` files.

Content lives in ``tm_app/content/product_guides/*.json`` — adding a topic
is content + validation, not code. The registry validates every guide at
load (fail-closed) and enforces cross-references:

- unique ids;
- ``related_topics`` must resolve to known guide ids;
- ``capability_refs`` must resolve to known capability ids when a
  capability-id provider is supplied (avoids circular authority — the
  catalog stays the owner of capability identity).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from tm_app.application.product_guide.product_guide_schema import (
    parse_product_guide,
    ProductGuideValidationError,
)

CONTENT_DIR = (
    Path(__file__).resolve().parents[2] / "content" / "product_guides"
)
REGISTRY_VERSION = "product-guide-registry-v1"


def _default_capability_ids() -> frozenset[str]:
    """Known capability ids from the live catalog (lazy — avoids cycles)."""
    from tm_app.application.gpt_actions.capability_descriptors import (
        build_capability_surface_catalog,
    )

    surface = build_capability_surface_catalog()
    ids: set[str] = set()
    for bucket in ("entities", "workflows", "analyses"):
        for item in surface.get(bucket) or ():
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
    return frozenset(ids)


class ProductGuideRegistry:
    def __init__(
        self,
        *,
        content_dir: Path | None = None,
        capability_ids: Callable[[], frozenset[str]] | None = None,
    ) -> None:
        self._dir = content_dir or CONTENT_DIR
        self._capability_ids = capability_ids or _default_capability_ids
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
