"""Vocabulário e padrões — refinamento operacional (via content loader)."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_operational_refinement.chat_operational_refinement_content_service import (
    ChatOperationalRefinementContentService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class _LazyPattern:
    def __init__(self, key: str) -> None:
        self._key = key

    def __get__(self, _obj: Any, _owner: type | None = None) -> re.Pattern[str]:
        return ChatOperationalRefinementContentService.compile_pattern(self._key)


class _LazyPatternList:
    def __init__(self, key: str) -> None:
        self._key = key

    def __get__(
        self, _obj: Any, _owner: type | None = None
    ) -> tuple[re.Pattern[str], ...]:
        return ChatOperationalRefinementContentService.compile_pattern_list(self._key)


class _LazyTerms:
    def __init__(self, key: str) -> None:
        self._key = key

    def __get__(self, _obj: Any, _owner: type | None = None) -> tuple[str, ...]:
        return ChatOperationalRefinementContentService.terms(self._key)


class ChatOperationalRefinementVocabulary:
    FILTER_TERMS = _LazyTerms("filter")
    BRANCH_RE = _LazyPattern("branch")
    WAREHOUSE_RE = _LazyPattern("warehouse")
    NEXT_PAGE_TERMS = _LazyTerms("nextPage")
    PREV_PAGE_TERMS = _LazyTerms("prevPage")
    DEPTH_INCREASE_TERMS = _LazyTerms("depthIncrease")
    MAX_DEPTH_RE = _LazyPattern("maxDepth")
    MORE_RESULTS_TERMS = _LazyTerms("moreResults")
    PAGE_SIZE_PATTERNS = _LazyPatternList("pageSize")
    PAGE_NUMBER_RE = _LazyPattern("pageNumber")
    STOCK_RESET_TERMS = _LazyTerms("stockReset")

    @classmethod
    @lru_cache(maxsize=1)
    def paginated_path_fragments(cls) -> tuple[str, ...]:
        return OperationalRouteRegistryService.paginated_path_fragments()
