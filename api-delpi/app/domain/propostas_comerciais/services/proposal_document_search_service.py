from __future__ import annotations

import re


class ProposalDocumentSearchService:
    """Builds the WHERE clause/params for listing proposal documents (ADY010).

    Searchable fields mirror the legacy client-side criteria plus customer code:
    proposal number, opportunity (with ``OV`` prefix normalization), customer
    code and customer/prospect name (SA1/SUS via the canonical list joins).
    """

    _MAX_TERM_LEN = 80
    _OV_PREFIX = re.compile(r"^OV\s*(\d+)$", re.IGNORECASE)

    @classmethod
    def clause(cls, search: str | None) -> tuple[str, list[str]]:
        term = (search or "").strip()
        if not term or len(term) > cls._MAX_TERM_LEN:
            return "", []

        pattern = f"%{term}%"
        clauses = [
            "ADY.ADY_PROPOS LIKE ?",
            "ADY.ADY_OPORTU LIKE ?",
            "ADY.ADY_CLIENT LIKE ?",
            "A1.A1_NOME COLLATE Latin1_General_CI_AI LIKE ?",
            "A1.A1_NREDUZ COLLATE Latin1_General_CI_AI LIKE ?",
            "SUS.US_NOME COLLATE Latin1_General_CI_AI LIKE ?",
        ]
        params: list[str] = [pattern] * len(clauses)

        ov_match = cls._OV_PREFIX.match(term)
        if ov_match:
            clauses.append("ADY.ADY_OPORTU LIKE ?")
            params.append(f"%{ov_match.group(1)}%")

        return f"AND ({' OR '.join(clauses)})", params
