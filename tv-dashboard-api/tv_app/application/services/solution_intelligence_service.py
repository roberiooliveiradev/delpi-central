"""Solution intelligence — bounded gap classification on TV route misses.

Contract (roadmap §39/§40):
- Consulted ONLY after a TV route search miss — a hit never touches Core.
- Input: the existing route-search business phrase (smallest sufficient
  input; never transcripts, slide content, or datasets).
- Output: a typed gapClassification plus bounded safe-projection
  candidates — KNOWLEDGE, never executable capability. A candidate is
  never an operationId, URL, or allowlist entry.
- Epistemics: solution identity from the Core registry = FACT;
  query→solution association = INFERRED; nothing here is authorization.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

GAP_CLASSIFICATIONS = frozenset(
    {
        "TV_ROUTE_FOUND",
        "SOLUTION_FOUND_NO_TV_ROUTE",
        "SOLUTION_FOUND_ACCESS_RESTRICTED",
        "NO_SOLUTION_EVIDENCE",
        "AMBIGUOUS_SOLUTIONS",
        "CONTRACT_GAP",
    }
)

_NOT_AUTHORITY_NOTE = (
    "Core solution metadata — knowledge, not authorization. `accessible` "
    "reports the user's effective access; it never grants it, and a "
    "solution here is never an executable TV data route."
)

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")
_MAX_CANDIDATES = 5


def _normalize(text: str) -> list[str]:
    nfkd = unicodedata.normalize("NFKD", str(text or "").lower())
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    return _TOKEN_RE.findall(ascii_text)


def _candidate(raw: dict[str, Any]) -> dict[str, Any]:
    """Bounded safe summary — never carries executable identifiers."""
    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "category": raw.get("category"),
        "accessible": bool(raw.get("accessible")),
        "epistemic": "INFERRED",
    }


def _match_score(query_tokens: list[str], solution: dict[str, Any]) -> int:
    """Deterministic token overlap over safe canonical fields."""
    haystack = " ".join(
        str(solution.get(field) or "")
        for field in ("id", "name", "description", "category")
    )
    hay_tokens = set(_normalize(haystack))
    return sum(1 for token in query_tokens if token in hay_tokens)


class SolutionIntelligenceService:
    """Classify the ecosystem gap behind a TV route-search miss."""

    def classify(self, query: str, solutions: list[dict[str, Any]]) -> dict[str, Any]:
        tokens = _normalize(query)
        scored = [
            (score, solution)
            for solution in solutions
            if (score := _match_score(tokens, solution)) > 0
        ]
        scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("id"))))
        candidates = [_candidate(s) for _, s in scored[:_MAX_CANDIDATES]]

        if not candidates:
            gap = "NO_SOLUTION_EVIDENCE"
        elif len(candidates) > 1:
            gap = "AMBIGUOUS_SOLUTIONS"
        elif not candidates[0]["accessible"]:
            gap = "SOLUTION_FOUND_ACCESS_RESTRICTED"
        else:
            gap = "SOLUTION_FOUND_NO_TV_ROUTE"

        return {
            "gapClassification": gap,
            "authority": "core_solution_registry",
            "executionAuthority": "tv_data_route_allowlist",
            "candidates": candidates,
            "note": _NOT_AUTHORITY_NOTE,
        }

    @staticmethod
    def route_found() -> dict[str, Any]:
        """Typed outcome on a TV route hit — resolved before any lookup."""
        return {
            "gapClassification": "TV_ROUTE_FOUND",
            "authority": "core_solution_registry",
            "executionAuthority": "tv_data_route_allowlist",
            "candidates": [],
            "note": _NOT_AUTHORITY_NOTE,
        }

    @staticmethod
    def contract_gap(error_kind: str | None = None) -> dict[str, Any]:
        """Fail-closed envelope when the Core lookup cannot conclude."""
        return {
            "gapClassification": "CONTRACT_GAP",
            "authority": "core_solution_registry",
            "executionAuthority": "tv_data_route_allowlist",
            "candidates": [],
            "reason": error_kind or "unavailable",
            "note": _NOT_AUTHORITY_NOTE,
        }
