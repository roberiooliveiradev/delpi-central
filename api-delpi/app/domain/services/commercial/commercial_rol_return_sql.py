"""Predicado SQL canônico de devolução no ROL (SD1).

Regra homologada vs resumo de vendas (ago/2026):
- CFOP de retorno de venda ``1201`` / ``2201``; ou
- ``D1_TIPO = 'D'`` **somente** quando o TES gera duplicata (``F4_DUPLIC = 'S'``).

Exclui movimentos de estoque/beneficiamento (ex.: TES «ENTRADA MAT FALTANTE»
com ``F4_DUPLIC = N``) que não entram no faturamento comercial.
"""

from __future__ import annotations


class CommercialRolReturnSql:
    SALES_RETURN_CFOPS = ("1201", "2201")

    @staticmethod
    def tes_join(
        *,
        d1_alias: str = "D1",
        f4_alias: str = "F4D",
        with_nolock: bool = False,
    ) -> str:
        """LEFT JOIN SF4 pelo TES da linha SD1 (filial da linha ou TES global)."""
        lock = " WITH (NOLOCK)" if with_nolock else ""
        return f"""
                LEFT JOIN SF4010 {f4_alias}{lock}
                    ON  {f4_alias}.D_E_L_E_T_ = ''
                    AND {f4_alias}.F4_CODIGO = {d1_alias}.D1_TES
                    AND (
                            {f4_alias}.F4_FILIAL = {d1_alias}.D1_FILIAL
                         OR {f4_alias}.F4_FILIAL = ''
                         OR {f4_alias}.F4_FILIAL IS NULL
                    )
        """

    @staticmethod
    def sales_return_predicate(
        *,
        d1_alias: str = "D1",
        f4_alias: str = "F4D",
    ) -> str:
        """Predicado WHERE/AND para linha SD1 contar como devolução de venda no ROL."""
        cfops = ", ".join(f"'{code}'" for code in CommercialRolReturnSql.SALES_RETURN_CFOPS)
        return f"""(
                        {d1_alias}.D1_CF IN ({cfops})
                        OR (
                            {d1_alias}.D1_TIPO = 'D'
                            AND ISNULL({f4_alias}.F4_DUPLIC, '') = 'S'
                        )
                    )"""
