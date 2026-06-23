from __future__ import annotations


class CommercialProposalAcceptanceDateService:
    """Data de aceite da proposta (Dt.Ass.Prop. / AD1_DTASSI) no TOTVS."""

    @staticmethod
    def sql_acceptance_date_expression(
        dtassi_ref: str,
        dtfim_ref: str,
    ) -> str:
        return f"""
            CASE
                WHEN {dtassi_ref} IS NOT NULL
                 AND RTRIM(CAST({dtassi_ref} AS VARCHAR(20))) <> ''
                THEN {dtassi_ref}
                ELSE {dtfim_ref}
            END
        """.strip()

    @staticmethod
    def sql_acceptance_date_for_alias(ad1_alias: str) -> str:
        return CommercialProposalAcceptanceDateService.sql_acceptance_date_expression(
            f"{ad1_alias}.AD1_DTASSI",
            f"{ad1_alias}.AD1_DTFIM",
        )
