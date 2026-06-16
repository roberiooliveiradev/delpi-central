from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductDirectivesRequest:
    identifier: str
    max_depth: Optional[int] = None
    branch: Optional[str] = None
