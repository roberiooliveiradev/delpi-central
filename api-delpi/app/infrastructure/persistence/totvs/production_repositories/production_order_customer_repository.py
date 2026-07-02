from app.domain.ports.production.production_order_customer_repository_port import (
    ProductionOrderCustomerRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class ProductionOrderCustomerRepository(
    BaseRepository,
    ProductionOrderCustomerRepositoryPort,
):
    """
    Rastreia o cliente da OP pelo pedido de venda que a gerou.

    Vínculo Protheus: SC2.C2_PEDIDO → SC5.C5_NUM → SA1 (A1_COD/A1_LOJA).
    Só ~2% das OPs têm C2_PEDIDO preenchido (produção majoritariamente para
    estoque), então o retorno costuma ser None e o cliente é editável na UI.
    """

    def fetch_order_customer(
        self,
        *,
        production_order: str,
        branch: str | None = None,
    ) -> dict | None:
        params: list = [production_order]
        branch_filter = ""
        if branch:
            branch_filter = "AND OP.C2_FILIAL = ?"
            params.append(branch)

        sql = f"""
        SELECT TOP 1
            RTRIM(LTRIM(OP.C2_PEDIDO))  AS sales_order,
            RTRIM(LTRIM(OP.C2_ITEMPV))  AS sales_order_item,
            RTRIM(LTRIM(C5.C5_CLIENTE)) AS customer_code,
            RTRIM(LTRIM(C5.C5_LOJACLI)) AS customer_store,
            RTRIM(LTRIM(A1.A1_NOME))    AS customer_name
        FROM SC2010 OP WITH (NOLOCK)
        LEFT JOIN SC5010 C5 WITH (NOLOCK)
            ON C5.D_E_L_E_T_ = ''
           AND C5.C5_FILIAL = OP.C2_FILIAL
           AND RTRIM(LTRIM(C5.C5_NUM)) = RTRIM(LTRIM(OP.C2_PEDIDO))
        LEFT JOIN SA1010 A1 WITH (NOLOCK)
            ON A1.D_E_L_E_T_ = ''
           AND A1.A1_COD = C5.C5_CLIENTE
           AND A1.A1_LOJA = C5.C5_LOJACLI
        WHERE OP.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(OP.C2_OP)) = ?
          AND RTRIM(LTRIM(OP.C2_PEDIDO)) <> ''
          {branch_filter}
        """

        with self as repo:
            row = repo.execute_one(sql, tuple(params))

        if not row or not (row.get("customer_name") or "").strip():
            return None
        return row
