from __future__ import annotations


class ProductionAppointmentsListSearchService:
    """Texto livre opcional nas listagens paginadas de apontamentos (lista e by-op)."""

    _MAX_TERM_LEN = 80

    @classmethod
    def normalize_term(cls, search: str | None) -> str | None:
        term = (search or "").strip()
        if not term or len(term) > cls._MAX_TERM_LEN:
            return None
        return term

    @classmethod
    def clause_for_appointment_row(cls, search: str | None) -> tuple[str, list[str]]:
        """Filtro OR sobre colunas visíveis da lista de apontamentos.

        Requer ``LEFT JOIN SYS_USR U`` (operador) nas queries que usam o clause.
        """
        term = cls.normalize_term(search)
        if not term:
            return "", []

        pattern = f"%{term}%"
        clauses = [
            "LTRIM(RTRIM(SH6.H6_OPERADO)) LIKE ?",
            "LTRIM(RTRIM(ISNULL(U.USR_NOME, ''))) COLLATE Latin1_General_CI_AI LIKE ?",
            "LTRIM(RTRIM(SH6.H6_OPERAC)) LIKE ?",
            "LTRIM(RTRIM(SH6.H6_RECURSO)) LIKE ?",
            "LTRIM(RTRIM(ISNULL(SH1.H1_DESCRI, ''))) COLLATE Latin1_General_CI_AI LIKE ?",
            "LTRIM(RTRIM(SH6.H6_OP)) LIKE ?",
            "LTRIM(RTRIM(SH6.H6_PRODUTO)) LIKE ?",
            "LTRIM(RTRIM(ISNULL(SB1.B1_TIPO, ''))) LIKE ?",
            "LTRIM(RTRIM(ISNULL(SB1.B1_DESC, ''))) COLLATE Latin1_General_CI_AI LIKE ?",
            "LTRIM(RTRIM(SH1.H1_CTRAB)) LIKE ?",
            "LTRIM(RTRIM(ISNULL(HB.HB_NOME, ''))) COLLATE Latin1_General_CI_AI LIKE ?",
            "LTRIM(RTRIM(SH6.H6_DTAPONT)) LIKE ?",
        ]
        return f"({' OR '.join(clauses)})", [pattern] * len(clauses)

    @classmethod
    def clause_for_by_op_row(cls, search: str | None) -> tuple[str, list[str]]:
        """Filtro OR sobre colunas da agregação por OP."""
        term = cls.normalize_term(search)
        if not term:
            return "", []

        pattern = f"%{term}%"
        clauses = [
            "LTRIM(RTRIM(SH6.H6_OP)) LIKE ?",
            "LTRIM(RTRIM(SH6.H6_PRODUTO)) LIKE ?",
            "LTRIM(RTRIM(ISNULL(SB1.B1_TIPO, ''))) LIKE ?",
            "LTRIM(RTRIM(ISNULL(SB1.B1_DESC, ''))) COLLATE Latin1_General_CI_AI LIKE ?",
        ]
        return f"({' OR '.join(clauses)})", [pattern] * len(clauses)
