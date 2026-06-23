from __future__ import annotations

from app.domain.services.commercial_proposal_status import _STATUS_LABELS


class CommercialProposalListSearchService:
    _MAX_TERM_LEN = 80

    @classmethod
    def clause_for_latest_row(cls, search: str | None) -> tuple[str, list[str]]:
        term = (search or "").strip()
        if not term or len(term) > cls._MAX_TERM_LEN:
            return "", []

        pattern = f"%{term}%"
        status_codes = cls._matching_status_codes(term)
        clauses = [
            "AD1_FILIAL LIKE ?",
            "AD1_NROPOR LIKE ?",
            "AD1_REVISA LIKE ?",
            "AD1_DESCRI COLLATE Latin1_General_CI_AI LIKE ?",
            "AD1_STATUS LIKE ?",
            "AD1_CODCLI LIKE ?",
            "AD1_LOJCLI LIKE ?",
            "AD1_STAGE LIKE ?",
        ]
        params: list[str] = [pattern] * len(clauses)

        if status_codes:
            placeholders = ",".join("?" for _ in status_codes)
            clauses.append(f"AD1_STATUS IN ({placeholders})")
            params.extend(status_codes)

        return f"AND ({' OR '.join(clauses)})", params

    @staticmethod
    def _matching_status_codes(term: str) -> list[str]:
        normalized = term.casefold()
        matches: list[str] = []
        for code, label in _STATUS_LABELS.items():
            if normalized in label.casefold() or normalized == code.casefold():
                matches.append(code)
        return matches
