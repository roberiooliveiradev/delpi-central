"""Constantes — especialista SQL avançado."""

from __future__ import annotations

import re

SQL_BLOCK_RE = re.compile(r"```sql\s*[\s\S]*?```", flags=re.IGNORECASE)
