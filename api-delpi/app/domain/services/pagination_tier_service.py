"""Named pagination tiers — single source for defaults, clamps and caps."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "pagination_tiers.json"


def _as_optional_int(value: Any) -> int | None:
    if value is None or value == "None" or value == "null":
        return None
    return int(value)


@dataclass(frozen=True)
class PaginationTier:
    id: str
    param: str
    default: int | None
    ge: int
    le: int | None
    optional: bool
    description: str = ""


class PaginationTierServiceError(KeyError):
    pass


class PaginationTierService:
    @classmethod
    @lru_cache(maxsize=1)
    def bundle(cls) -> dict[str, Any]:
        payload = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("tiers"), dict):
            raise ValueError("pagination_tiers.json inválido")
        return payload

    @classmethod
    def clear_cache(cls) -> None:
        cls.bundle.cache_clear()

    @classmethod
    def tier_ids(cls) -> tuple[str, ...]:
        return tuple(sorted(cls.bundle()["tiers"].keys()))

    @classmethod
    def get(cls, tier_id: str) -> PaginationTier:
        raw = cls.bundle()["tiers"].get(tier_id)
        if not isinstance(raw, dict):
            raise PaginationTierServiceError(f"Unknown pagination tier: {tier_id}")
        default = raw.get("default")
        le = raw.get("le")
        ge_raw = raw.get("ge")
        return PaginationTier(
            id=str(raw.get("id") or tier_id),
            param=str(raw.get("param") or "page_size"),
            default=_as_optional_int(default),
            ge=int(ge_raw) if ge_raw is not None and ge_raw != "None" else 1,
            le=_as_optional_int(le),
            optional=bool(raw.get("optional")),
            description=str(raw.get("description") or ""),
        )

    @classmethod
    def default(cls, tier_id: str) -> int | None:
        return cls.get(tier_id).default

    @classmethod
    def max_size(cls, tier_id: str) -> int | None:
        return cls.get(tier_id).le

    @classmethod
    def clamp(cls, tier_id: str, value: int | None) -> int | None:
        """Clamp a requested size to the tier bounds.

        Optional tiers: ``None`` stays ``None`` (full result / omit).
        Non-optional tiers: ``None`` becomes the tier default.
        """
        tier = cls.get(tier_id)
        if value is None:
            return None if tier.optional else (tier.default if tier.default is not None else tier.ge)
        size = int(value)
        if size < tier.ge:
            size = tier.ge
        if tier.le is not None and size > tier.le:
            size = tier.le
        return size

    @classmethod
    def require_int(cls, tier_id: str, value: int | None) -> int:
        """Clamp and require a concrete int (non-optional result)."""
        clamped = cls.clamp(tier_id, value)
        if clamped is None:
            tier = cls.get(tier_id)
            if tier.default is not None:
                return int(tier.default)
            raise ValueError(f"Tier {tier_id} produced no concrete page size")
        return int(clamped)
