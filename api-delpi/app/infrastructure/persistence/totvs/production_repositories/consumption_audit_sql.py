"""SQL read-only da Auditoria de Consumo OP × operação (GLPI #1353).

Cada builder devolve uma consulta ``SELECT`` parametrizada — o repositório
amarrado executa com ``?`` placeholders; nenhum valor do chamador entra no
texto SQL. Grão canônico: filial × OP (11 posições) × operação × componente.
"""

from __future__ import annotations

from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)


def order_sql() -> str:
    """SC2 + SB1 da OP — identidade, quantidades e datas do contrato."""
    return """
        SELECT TOP 1
            RTRIM(LTRIM(OP.C2_FILIAL)) AS branch,
            RTRIM(LTRIM(OP.C2_OP)) AS production_order,
            RTRIM(LTRIM(OP.C2_NUM)) AS order_number,
            RTRIM(LTRIM(OP.C2_ITEM)) AS order_item,
            RTRIM(LTRIM(OP.C2_SEQUEN)) AS order_sequence,
            RTRIM(LTRIM(OP.C2_PRODUTO)) AS product_code,
            RTRIM(LTRIM(P.B1_DESC)) AS product_description,
            RTRIM(LTRIM(P.B1_TIPO)) AS product_type,
            RTRIM(LTRIM(OP.C2_UM)) AS unit_of_measure,
            CAST(OP.C2_QUANT AS FLOAT) AS planned_quantity,
            CAST(OP.C2_QUJE AS FLOAT) AS produced_quantity,
            RTRIM(LTRIM(OP.C2_STATUS)) AS status,
            RTRIM(LTRIM(OP.C2_PRIOR)) AS priority,
            RTRIM(LTRIM(OP.C2_TPOP)) AS order_type,
            RTRIM(LTRIM(OP.C2_LOCAL)) AS warehouse,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(OP.C2_EMISSAO, ''), 112), 23)
                AS emission_date,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(OP.C2_DATPRI, ''), 112), 23)
                AS planned_start_date,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(OP.C2_DATPRF, ''), 112), 23)
                AS due_date,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(OP.C2_DATRF, ''), 112), 23)
                AS finished_at
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(OP.C2_OP)) = ?
          AND OP.C2_FILIAL = ?
        """


def family_orders_sql() -> str:
    """OPs do mesmo ``C2_NUM`` na filial — família PA/PI para related_orders."""
    return """
        SELECT
            RTRIM(LTRIM(OP.C2_OP)) AS production_order,
            RTRIM(LTRIM(OP.C2_ITEM)) AS order_item,
            RTRIM(LTRIM(OP.C2_SEQUEN)) AS order_sequence,
            RTRIM(LTRIM(OP.C2_PRODUTO)) AS product_code,
            RTRIM(LTRIM(P.B1_TIPO)) AS product_type,
            CAST(OP.C2_QUANT AS FLOAT) AS planned_quantity,
            CAST(OP.C2_QUJE AS FLOAT) AS produced_quantity,
            RTRIM(LTRIM(OP.C2_STATUS)) AS status
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND OP.C2_FILIAL = ?
          AND OP.C2_NUM = ?
          AND RTRIM(LTRIM(OP.C2_OP)) <> ?
        ORDER BY OP.C2_ITEM ASC, OP.C2_SEQUEN ASC
        """


def commitments_sql() -> str:
    """Empenhos SD4 agregados por operação × componente × origem.

    ``D4_OPORIG`` entra no GROUP BY: quando o componente do empenho é um
    intermediário produzido por outra OP, a origem precisa permanecer visível
    para rastreabilidade (nunca somada como consumo desta OP).
    """
    return """
        SELECT
            RTRIM(LTRIM(RE.D4_OPERAC)) AS operation,
            RTRIM(LTRIM(RE.D4_COD)) AS component_code,
            RTRIM(LTRIM(P.B1_DESC)) AS component_description,
            RTRIM(LTRIM(P.B1_UM)) AS unit_of_measure,
            RTRIM(LTRIM(P.B1_TIPO)) AS component_type,
            NULLIF(RTRIM(LTRIM(RE.D4_OPORIG)), '') AS origin_order,
            CAST(SUM(RE.D4_QTDEORI) AS FLOAT) AS original_quantity,
            CAST(SUM(RE.D4_QUANT) AS FLOAT) AS open_quantity,
            CAST(SUM(
                CASE WHEN RE.D4_QTDEORI > RE.D4_QUANT
                     THEN RE.D4_QTDEORI - RE.D4_QUANT ELSE 0 END
            ) AS FLOAT) AS derived_consumed_quantity,
            COUNT(*) AS commitment_lines
        FROM SD4010 RE WITH (NOLOCK)
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = RE.D4_COD
           AND P.D_E_L_E_T_ = ''
        WHERE RE.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(RE.D4_OP)) = ?
          AND RE.D4_FILIAL = ?
        GROUP BY
            RE.D4_OPERAC,
            RE.D4_COD,
            P.B1_DESC,
            P.B1_UM,
            P.B1_TIPO,
            RE.D4_OPORIG
        ORDER BY RE.D4_OPERAC ASC, RE.D4_COD ASC
        """


def movements_sql() -> str:
    """Linhas SD3 da OP — grão por linha; documento nunca é chave de OP."""
    return """
        SELECT
            RTRIM(LTRIM(D3.D3_DOC)) AS document,
            RTRIM(LTRIM(D3.D3_COD)) AS component_code,
            RTRIM(LTRIM(D3.D3_CF)) AS cf,
            RTRIM(LTRIM(D3.D3_TM)) AS tm,
            CAST(D3.D3_QUANT AS FLOAT) AS quantity,
            RTRIM(LTRIM(D3.D3_UM)) AS unit_of_measure,
            RTRIM(LTRIM(D3.D3_LOCAL)) AS warehouse,
            RTRIM(LTRIM(ISNULL(D3.D3_ESTORNO, ''))) AS reversed_flag,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(D3.D3_EMISSAO, ''), 112), 23)
                AS issue_date
        FROM SD3010 D3 WITH (NOLOCK)
        WHERE D3.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(D3.D3_OP)) = ?
          AND D3.D3_FILIAL = ?
        ORDER BY D3.D3_DOC ASC, D3.D3_COD ASC
        """


def appointments_sql() -> str:
    """Apontamentos SH6 da OP — fonte de execução (qualquer canal)."""
    return """
        SELECT
            RTRIM(LTRIM(H6.H6_OPERAC)) AS operation,
            RTRIM(LTRIM(H6.H6_TIPO)) AS appointment_type,
            RTRIM(LTRIM(H6.H6_PRODUTO)) AS product_code,
            CAST(H6.H6_QTDPROD AS FLOAT) AS reported_quantity,
            CAST(H6.H6_QTDPERD AS FLOAT) AS lost_quantity,
            RTRIM(LTRIM(H6.H6_IDENT)) AS appointment_id,
            RTRIM(LTRIM(H6.H6_RECURSO)) AS resource,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(H6.H6_DTAPONT, ''), 112), 23)
                AS reported_at,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(H6.H6_DATAINI, ''), 112), 23)
                AS started_on,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(H6.H6_DATAFIN, ''), 112), 23)
                AS ended_on,
            RTRIM(LTRIM(H6.H6_HORAINI)) AS start_time,
            RTRIM(LTRIM(H6.H6_HORAFIN)) AS end_time
        FROM SH6010 H6 WITH (NOLOCK)
        WHERE H6.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(H6.H6_OP)) = ?
          AND H6.H6_FILIAL = ?
        ORDER BY H6.H6_OPERAC ASC, H6.H6_DTAPONT ASC, H6.H6_HORAINI ASC
        """


def operation_events_sql() -> str:
    """Eventos HZA010 — canal coletor; status 1 em curso / 2 encerrado com
    apontamento / 3 descartado (doc canônica apontamento-operacao-hza)."""
    return """
        SELECT
            RTRIM(LTRIM(HZA.HZA_OPERAC)) AS operation,
            RTRIM(LTRIM(HZA.HZA_STATUS)) AS status,
            RTRIM(LTRIM(HZA.HZA_TPTRNS)) AS transaction_type,
            RTRIM(LTRIM(HZA.HZA_IDAPON)) AS appointment_ref,
            RTRIM(LTRIM(HZA.HZA_RECUR)) AS resource,
            RTRIM(LTRIM(HZA.HZA_SEQ)) AS sequence,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(HZA.HZA_DTINI, ''), 112), 23)
                AS started_on,
            RTRIM(LTRIM(HZA.HZA_HRINI)) AS start_time,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(HZA.HZA_DTFIM, ''), 112), 23)
                AS ended_on,
            RTRIM(LTRIM(HZA.HZA_HRFIM)) AS end_time
        FROM HZA010 HZA WITH (NOLOCK)
        WHERE HZA.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(HZA.HZA_OP)) = ?
          AND HZA.HZA_FILIAL = ?
        ORDER BY HZA.HZA_OPERAC ASC, HZA.HZA_SEQ ASC
        """


def allocations_sql() -> str:
    """Linhas SH8010 — alocação/cadastro da operação. Presença observada como
    alocação pendente; semântica final de remoção pendente com o PCP."""
    return """
        SELECT
            RTRIM(LTRIM(H8.H8_OPER)) AS operation,
            RTRIM(LTRIM(H8.H8_CTRAB)) AS work_center,
            RTRIM(LTRIM(H8.H8_RECURSO)) AS resource,
            RTRIM(LTRIM(H8.H8_STATUS)) AS status,
            CAST(H8.H8_QUANT AS FLOAT) AS quantity,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(H8.H8_DTINI, ''), 112), 23)
                AS scheduled_start,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(H8.H8_DTFIM, ''), 112), 23)
                AS scheduled_end,
            RTRIM(LTRIM(H8.H8_HRINI)) AS scheduled_start_time,
            RTRIM(LTRIM(H8.H8_HRFIM)) AS scheduled_end_time
        FROM SH8010 H8 WITH (NOLOCK)
        WHERE H8.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(H8.H8_OP)) = ?
          AND H8.H8_FILIAL = ?
        ORDER BY H8.H8_OPER ASC
        """


def routing_sql() -> str:
    """Roteiro SG2 do produto — operações planejadas e centros de trabalho."""
    return """
        SELECT
            RTRIM(LTRIM(G2.G2_FILIAL)) AS branch,
            RTRIM(LTRIM(G2.G2_OPERAC)) AS operation,
            RTRIM(LTRIM(G2.G2_CTRAB)) AS work_center,
            RTRIM(LTRIM(G2.G2_RECURSO)) AS resource
        FROM SG2010 G2 WITH (NOLOCK)
        WHERE G2.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(G2.G2_PRODUTO)) = ?
          AND G2.G2_FILIAL IN ('', ?)
        ORDER BY G2.G2_OPERAC ASC
        """


def bom_components_sql() -> str:
    """Componentes SG1 vigentes na data de referência (``structure_as_of``).

    O parâmetro de referência aparece duas vezes no filtro de vigência —
    ``(ini, fim)`` — e é sempre o último parâmetro da consulta.
    """
    validity = ProductBomValidityFilterService.validity_filter_sql(
        alias="G1",
        reference_param="?",
    )
    return f"""
        SELECT
            RTRIM(LTRIM(G1.G1_FILIAL)) AS branch,
            RTRIM(LTRIM(G1.G1_COMP)) AS component_code,
            RTRIM(LTRIM(P.B1_DESC)) AS component_description,
            RTRIM(LTRIM(P.B1_UM)) AS unit_of_measure,
            RTRIM(LTRIM(P.B1_TIPO)) AS component_type,
            CAST(G1.G1_QUANT AS FLOAT) AS quantity_per_unit,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(G1.G1_INI, ''), 112), 23)
                AS valid_from,
            CONVERT(VARCHAR(10), CONVERT(DATE, NULLIF(G1.G1_FIM, ''), 112), 23)
                AS valid_to
        FROM SG1010 G1 WITH (NOLOCK)
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = G1.G1_COMP
           AND P.D_E_L_E_T_ = ''
        WHERE G1.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(G1.G1_COD)) = ?
          AND G1.G1_FILIAL IN ('', ?)
          {validity}
        ORDER BY G1.G1_COMP ASC
        """


def product_metadata_sql(count: int) -> str:
    """Metadados SB1 (tipo/UM/descrição) de um lote de códigos."""
    if count < 1:
        raise ValueError("count deve ser pelo menos 1.")
    placeholders = ", ".join(["?"] * count)
    return f"""
        SELECT
            RTRIM(LTRIM(P.B1_COD)) AS code,
            RTRIM(LTRIM(P.B1_DESC)) AS description,
            RTRIM(LTRIM(P.B1_UM)) AS unit_of_measure,
            RTRIM(LTRIM(P.B1_TIPO)) AS product_type
        FROM SB1010 P WITH (NOLOCK)
        WHERE P.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(P.B1_COD)) IN ({placeholders})
        """


def parent_consumers_sql() -> str:
    """OPs cujo empenho aponta esta OP como produtora do intermediário
    (``D4_OPORIG`` = esta OP) — vínculo pai provado em A1."""
    return """
        SELECT DISTINCT
            RTRIM(LTRIM(RE.D4_OP)) AS production_order,
            RTRIM(LTRIM(RE.D4_COD)) AS component_code
        FROM SD4010 RE WITH (NOLOCK)
        WHERE RE.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(RE.D4_OPORIG)) = ?
          AND RE.D4_FILIAL = ?
        ORDER BY production_order ASC
        """
