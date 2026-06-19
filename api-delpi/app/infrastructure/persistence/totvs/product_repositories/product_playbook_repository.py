# app/infrastructure/persistence/totvs/product_repositories/product_playbook_repository.py

from app.domain.ports.product.product_playbook_repository_port import ProductPlaybookRepositoryPort
from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.product_repositories.product_playbook_production_period_sql import (
    PRODUCT_PLAYBOOK_PRODUCTION_ORDER_PERIOD_FILTER_SQL,
)


class ProductPlaybookRepository(BaseRepository, ProductPlaybookRepositoryPort):

    @staticmethod
    def _bom_validity_context(
        reference_date: str | None = None,
    ) -> tuple[str, str, list[str]]:
        if reference_date:
            declare = "DECLARE @DATA_REF VARCHAR(8) = ?;"
            validity = ProductBomValidityFilterService.validity_filter_sql(
                alias="G1",
                reference_param="@DATA_REF",
            )
            return declare, validity, [reference_date]
        validity = ProductBomValidityFilterService.validity_filter_sql_for_today(alias="G1")
        return "", validity, []

    def fetch_product_header(self, code: str) -> dict | None:
        sql = """
        SELECT TOP 1
            B1_COD AS product_code,
            B1_DESC AS description,
            B1_TIPO AS product_type,
            B1_UM AS unit,
            B1_GRUPO AS group_code
        FROM SB1010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
          AND B1_COD = ?
        """
        with self as repo:
            return repo.execute_one(sql, (code,))

    def fetch_structure_with_exclusivity(
        self,
        code: str,
        max_depth: int,
        *,
        reference_date: str | None = None,
    ) -> list[dict]:
        data_ref_declare, bom_validity, prefix_params = self._bom_validity_context(reference_date)
        sql = f"""
        {data_ref_declare}
        DECLARE @PRODUTO VARCHAR(30) = ?;
        DECLARE @MAX_DEPTH INT = ?;

        WITH ESTRUTURA_PRODUTO AS (
            SELECT
                G1.G1_COD   AS parent_code,
                G1.G1_COMP  AS component_code,
                G1.G1_QUANT AS quantity_per,
                CAST(G1.G1_QUANT AS FLOAT) AS accumulated_quantity,
                1           AS level,
                CAST(G1.G1_COD + ' > ' + G1.G1_COMP AS VARCHAR(MAX)) AS path
            FROM SG1010 G1 WITH (NOLOCK)
            WHERE G1.D_E_L_E_T_ = ''
              AND G1.G1_COD = @PRODUTO
              {bom_validity}

            UNION ALL

            SELECT
                G1.G1_COD,
                G1.G1_COMP,
                G1.G1_QUANT,
                CAST(EP.accumulated_quantity * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT),
                EP.level + 1,
                CAST(EP.path + ' > ' + G1.G1_COMP AS VARCHAR(MAX))
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN ESTRUTURA_PRODUTO EP
                ON EP.component_code = G1.G1_COD
            WHERE G1.D_E_L_E_T_ = ''
              AND EP.level < @MAX_DEPTH
              {bom_validity}
        ),

        MATERIAS_PRIMAS_DO_PRODUTO AS (
            SELECT DISTINCT EP.component_code AS raw_material_code
            FROM ESTRUTURA_PRODUTO EP
            INNER JOIN SB1010 SB1 WITH (NOLOCK)
                ON SB1.B1_COD = EP.component_code
               AND SB1.D_E_L_E_T_ = ''
            WHERE SB1.B1_TIPO = 'MP'
        ),

        TODAS_ESTRUTURAS_VALIDAS AS (
            SELECT
                PA.B1_COD  AS finished_product_code,
                PA.B1_DESC AS finished_product_description,
                G1.G1_COD  AS parent_code,
                G1.G1_COMP AS component_code,
                1          AS level
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN SB1010 PA WITH (NOLOCK)
                ON PA.B1_COD = G1.G1_COD
               AND PA.D_E_L_E_T_ = ''
               AND PA.B1_TIPO = 'PA'
               AND PA.B1_COD NOT LIKE '8000%'
               AND PA.B1_COD NOT LIKE '8001%'
            WHERE G1.D_E_L_E_T_ = ''
              {bom_validity}

            UNION ALL

            SELECT
                TE.finished_product_code,
                TE.finished_product_description,
                G1.G1_COD,
                G1.G1_COMP,
                TE.level + 1
            FROM TODAS_ESTRUTURAS_VALIDAS TE
            INNER JOIN SG1010 G1 WITH (NOLOCK)
                ON G1.G1_COD = TE.component_code
               AND G1.D_E_L_E_T_ = ''
              {bom_validity}
            WHERE TE.level < @MAX_DEPTH
        ),

        USO_MP_EM_PA AS (
            SELECT
                TE.component_code AS raw_material_code,
                COUNT(DISTINCT TE.finished_product_code) AS total_valid_finished_products,
                MIN(TE.finished_product_code) AS exclusive_finished_product
            FROM TODAS_ESTRUTURAS_VALIDAS TE
            INNER JOIN MATERIAS_PRIMAS_DO_PRODUTO MP
                ON MP.raw_material_code = TE.component_code
            GROUP BY TE.component_code
        )

        SELECT
            EP.level,
            EP.parent_code,
            PAI.B1_DESC AS parent_description,
            EP.component_code,
            COMP.B1_DESC AS component_description,
            COMP.B1_TIPO AS component_type,
            COMP.B1_UM AS component_unit,
            COMP.B1_GRUPO AS component_group,
            CAST(EP.quantity_per AS VARCHAR(50)) AS quantity_per,
            CAST(EP.accumulated_quantity AS VARCHAR(50)) AS accumulated_quantity,
            CASE
                WHEN COMP.B1_TIPO = 'MP' AND ISNULL(U.total_valid_finished_products, 0) = 1 THEN 'SIM'
                WHEN COMP.B1_TIPO = 'MP' THEN 'NAO'
                ELSE NULL
            END AS exclusive_raw_material,
            CASE
                WHEN COMP.B1_TIPO = 'MP' THEN ISNULL(U.total_valid_finished_products, 0)
                ELSE NULL
            END AS total_valid_finished_products_using_mp,
            EP.path
        FROM ESTRUTURA_PRODUTO EP
        LEFT JOIN SB1010 PAI WITH (NOLOCK)
            ON PAI.B1_COD = EP.parent_code
           AND PAI.D_E_L_E_T_ = ''
        LEFT JOIN SB1010 COMP WITH (NOLOCK)
            ON COMP.B1_COD = EP.component_code
           AND COMP.D_E_L_E_T_ = ''
        LEFT JOIN USO_MP_EM_PA U
            ON U.raw_material_code = EP.component_code
        ORDER BY EP.path
        OPTION (MAXRECURSION 0);
        """
        params = tuple(prefix_params + [code, max_depth])
        with self as repo:
            return repo.execute_batch_query(sql, params)

    def fetch_raw_material_stock(
        self,
        code: str,
        max_depth: int,
        *,
        reference_date: str | None = None,
    ) -> list[dict]:
        data_ref_declare, bom_validity, prefix_params = self._bom_validity_context(reference_date)
        sql = f"""
        {data_ref_declare}
        DECLARE @PRODUTO VARCHAR(30) = ?;
        DECLARE @MAX_DEPTH INT = ?;

        WITH ESTRUTURA AS (
            SELECT
                G1.G1_COD AS parent_code,
                G1.G1_COMP AS component_code,
                CAST(G1.G1_QUANT AS FLOAT) AS accumulated_quantity,
                1 AS level
            FROM SG1010 G1 WITH (NOLOCK)
            WHERE G1.D_E_L_E_T_ = ''
              AND G1.G1_COD = @PRODUTO
              {bom_validity}

            UNION ALL

            SELECT
                G1.G1_COD,
                G1.G1_COMP,
                CAST(E.accumulated_quantity * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT),
                E.level + 1
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN ESTRUTURA E
                ON E.component_code = G1.G1_COD
            WHERE G1.D_E_L_E_T_ = ''
              AND E.level < @MAX_DEPTH
              {bom_validity}
        ),

        MPS AS (
            SELECT DISTINCT
                E.component_code AS raw_material_code,
                SUM(E.accumulated_quantity) AS quantity_required_for_one_pa
            FROM ESTRUTURA E
            INNER JOIN SB1010 SB1 WITH (NOLOCK)
                ON SB1.B1_COD = E.component_code
               AND SB1.D_E_L_E_T_ = ''
               AND SB1.B1_TIPO = 'MP'
            GROUP BY E.component_code
        ),

        ESTOQUE AS (
            SELECT
                B2.B2_COD AS product_code,
                B2.B2_FILIAL AS branch,
                B2.B2_LOCAL AS warehouse,
                SUM(CAST(B2.B2_QATU AS FLOAT)) AS current_quantity,
                SUM(CAST(B2.B2_QEMP AS FLOAT)) AS committed_quantity,
                SUM(CAST(B2.B2_RESERVA AS FLOAT)) AS reserved_quantity,
                SUM(CAST(B2.B2_QATU - B2.B2_QEMP - B2.B2_RESERVA AS FLOAT)) AS available_quantity
            FROM SB2010 B2 WITH (NOLOCK)
            WHERE B2.D_E_L_E_T_ = ''
            GROUP BY B2.B2_COD, B2.B2_FILIAL, B2.B2_LOCAL
        )

        SELECT
            MP.raw_material_code,
            SB1.B1_DESC AS raw_material_description,
            SB1.B1_UM AS unit,
            SB1.B1_GRUPO AS group_code,
            CAST(MP.quantity_required_for_one_pa AS VARCHAR(50)) AS quantity_required_for_one_pa,
            E.branch,
            E.warehouse,
            CAST(ISNULL(E.current_quantity, 0) AS VARCHAR(50)) AS current_quantity,
            CAST(ISNULL(E.committed_quantity, 0) AS VARCHAR(50)) AS committed_quantity,
            CAST(ISNULL(E.reserved_quantity, 0) AS VARCHAR(50)) AS reserved_quantity,
            CAST(ISNULL(E.available_quantity, 0) AS VARCHAR(50)) AS available_quantity,
            CASE
                WHEN ISNULL(E.available_quantity, 0) >= MP.quantity_required_for_one_pa THEN 'SIM'
                ELSE 'NAO'
            END AS has_stock_for_one_pa
        FROM MPS MP
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = MP.raw_material_code
           AND SB1.D_E_L_E_T_ = ''
        LEFT JOIN ESTOQUE E
            ON E.product_code = MP.raw_material_code
        ORDER BY MP.raw_material_code, E.branch, E.warehouse
        OPTION (MAXRECURSION 0);
        """
        params = tuple(prefix_params + [code, max_depth])
        with self as repo:
            return repo.execute_batch_query(sql, params)

    def fetch_production_status(
        self,
        code: str,
        reference_date: str,
        max_depth: int,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
    ) -> list[dict]:
        branch_filter = ""
        params: list = [
            code,
            reference_date,
            max_depth,
            date_start,
            date_end_exclusive,
        ]

        if branch:
            branch_filter = "AND SC2.C2_FILIAL = ?"
            params.append(branch)

        period_filter = PRODUCT_PLAYBOOK_PRODUCTION_ORDER_PERIOD_FILTER_SQL
        bom_validity = ProductBomValidityFilterService.validity_filter_sql(
            alias="G1",
            reference_param="@DATA_REF",
        )

        sql = f"""
        DECLARE @PRODUTO VARCHAR(30) = ?;
        DECLARE @DATA_REF VARCHAR(8) = ?;
        DECLARE @MAX_DEPTH INT = ?;
        DECLARE @DATA_INI VARCHAR(8) = ?;
        DECLARE @DATA_FIM VARCHAR(8) = ?;

        WITH ESTRUTURA AS (
            SELECT
                G1.G1_COD AS parent_code,
                G1.G1_COMP AS component_code,
                CAST(G1.G1_QUANT AS FLOAT) AS quantity_per,
                CAST(G1.G1_QUANT AS FLOAT) AS quantity_required_for_one_pa,
                1 AS level,
                CAST(G1.G1_COD + ' > ' + G1.G1_COMP AS VARCHAR(MAX)) AS path
            FROM SG1010 G1 WITH (NOLOCK)
            WHERE G1.D_E_L_E_T_ = ''
              AND G1.G1_COD = @PRODUTO
              {bom_validity}

            UNION ALL

            SELECT
                G1.G1_COD,
                G1.G1_COMP,
                CAST(G1.G1_QUANT AS FLOAT),
                CAST(E.quantity_required_for_one_pa * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT),
                E.level + 1,
                CAST(E.path + ' > ' + G1.G1_COMP AS VARCHAR(MAX))
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN ESTRUTURA E
                ON E.component_code = G1.G1_COD
            WHERE G1.D_E_L_E_T_ = ''
              AND E.level < @MAX_DEPTH
              {bom_validity}
        ),

        ESCOPO_PRODUCAO AS (
            SELECT
                0 AS level,
                @PRODUTO AS product_code,
                CAST(1 AS FLOAT) AS quantity_required_for_one_pa,
                CAST(@PRODUTO AS VARCHAR(MAX)) AS path

            UNION

            SELECT
                E.level,
                E.component_code,
                E.quantity_required_for_one_pa,
                E.path
            FROM ESTRUTURA E
            INNER JOIN SB1010 SB1 WITH (NOLOCK)
                ON SB1.B1_COD = E.component_code
               AND SB1.D_E_L_E_T_ = ''
            WHERE SB1.B1_TIPO IN ('PI', 'PA')
        ),

        OPS AS (
            SELECT
                EP.level,
                EP.product_code,
                EP.quantity_required_for_one_pa,
                EP.path,
                SC2.C2_FILIAL AS branch,
                SC2.C2_OP AS production_order,
                SC2.C2_NUM AS order_number,
                SC2.C2_ITEM AS order_item,
                SC2.C2_SEQUEN AS order_sequence,
                SC2.C2_PRODUTO AS order_product_code,
                CAST(SC2.C2_QUANT AS FLOAT) AS order_quantity,
                CAST(SC2.C2_QUJE AS FLOAT) AS produced_quantity_sc2,
                SC2.C2_EMISSAO AS issue_date,
                SC2.C2_DATPRI AS planned_start_date,
                SC2.C2_DATPRF AS planned_end_date,
                SC2.C2_DATRF AS actual_end_date,
                SC2.C2_STATUS AS order_status
            FROM ESCOPO_PRODUCAO EP
            LEFT JOIN SC2010 SC2 WITH (NOLOCK)
                ON SC2.C2_PRODUTO = EP.product_code
               AND SC2.D_E_L_E_T_ = ''
               AND SC2.C2_EMISSAO <= @DATA_REF
               {period_filter}
               {branch_filter}
        ),

        APONTAMENTOS AS (
            SELECT
                H6_FILIAL AS branch,
                H6_OP AS production_order,
                H6_PRODUTO AS product_code,
                SUM(CAST(H6_QTDPROD AS FLOAT)) AS reported_quantity,
                SUM(CAST(H6_QTDPERD AS FLOAT)) AS lost_quantity,
                MIN(H6_DATAINI) AS first_start_date,
                MIN(H6_HORAINI) AS first_start_time,
                MAX(H6_DTAPONT) AS last_report_date,
                COUNT(*) AS total_reports
            FROM SH6010 WITH (NOLOCK)
            WHERE D_E_L_E_T_ = ''
              AND H6_DTAPONT <= @DATA_REF
            GROUP BY H6_FILIAL, H6_OP, H6_PRODUTO
        )

        SELECT
            O.level,
            O.product_code,
            SB1.B1_DESC AS description,
            SB1.B1_TIPO AS product_type,
            SB1.B1_UM AS unit,
            CAST(O.quantity_required_for_one_pa AS VARCHAR(50)) AS quantity_required_for_one_pa,
            O.branch,
            O.production_order,
            O.order_number,
            O.order_item,
            O.order_sequence,
            CAST(ISNULL(O.order_quantity, 0) AS VARCHAR(50)) AS order_quantity,
            CAST(ISNULL(O.produced_quantity_sc2, 0) AS VARCHAR(50)) AS produced_quantity_sc2,
            CAST(ISNULL(A.reported_quantity, 0) AS VARCHAR(50)) AS reported_quantity,
            CAST(ISNULL(A.lost_quantity, 0) AS VARCHAR(50)) AS lost_quantity,
            A.first_start_date,
            A.first_start_time,
            A.last_report_date,
            ISNULL(A.total_reports, 0) AS total_reports,
            CASE
                WHEN ISNULL(A.total_reports, 0) > 0 THEN 'SIM'
                WHEN ISNULL(O.produced_quantity_sc2, 0) > 0 THEN 'SIM_SC2'
                ELSE 'NAO'
            END AS production_started,
            CAST(CASE
                WHEN ISNULL(O.order_quantity, 0) > 0
                    THEN (ISNULL(A.reported_quantity, ISNULL(O.produced_quantity_sc2, 0)) / O.order_quantity) * 100
                ELSE 0
            END AS VARCHAR(50)) AS order_production_percent,
            CAST(CASE
                WHEN O.quantity_required_for_one_pa > 0
                    THEN ISNULL(A.reported_quantity, ISNULL(O.produced_quantity_sc2, 0)) / O.quantity_required_for_one_pa
                ELSE 0
            END AS VARCHAR(50)) AS equivalent_in_pa,
            CAST(CASE
                WHEN O.quantity_required_for_one_pa > 0
                    THEN (ISNULL(A.reported_quantity, ISNULL(O.produced_quantity_sc2, 0)) / O.quantity_required_for_one_pa) * 100
                ELSE 0
            END AS VARCHAR(50)) AS percent_for_one_pa,
            O.issue_date,
            O.planned_start_date,
            O.planned_end_date,
            O.actual_end_date,
            O.order_status,
            O.path
        FROM OPS O
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = O.product_code
           AND SB1.D_E_L_E_T_ = ''
        LEFT JOIN APONTAMENTOS A
            ON A.branch = O.branch
           AND A.product_code = O.order_product_code
           AND (
                A.production_order = O.production_order
                OR A.production_order = O.order_number + O.order_item + O.order_sequence
           )
        ORDER BY O.level, O.path, O.branch, O.production_order
        OPTION (MAXRECURSION 0);
        """
        with self as repo:
            return repo.execute_batch_query(sql, tuple(params))

    def fetch_shipping_status(
        self,
        code: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
    ) -> list[dict]:
        branch_filter = ""
        params: list = [code, date_start, date_end_exclusive]

        if branch:
            branch_filter = "AND H6.H6_FILIAL = ?"
            params.append(branch)

        sql = f"""
        DECLARE @PRODUTO VARCHAR(30) = ?;
        DECLARE @DATA_INI VARCHAR(8) = ?;
        DECLARE @DATA_FIM VARCHAR(8) = ?;

        WITH CTS_INSPECAO AS (
            SELECT
                HB_FILIAL AS branch,
                HB_COD AS inspection_work_center,
                HB_NOME AS inspection_work_center_name
            FROM SHB010 WITH (NOLOCK)
            WHERE D_E_L_E_T_ = ''
              AND UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
        ),

        APONTAMENTO_PA_INSPECAO AS (
            SELECT
                H6.H6_FILIAL AS branch,
                H6.H6_PRODUTO AS product_code,
                SB1.B1_DESC AS description,
                SB1.B1_TIPO AS product_type,
                SB1.B1_UM AS unit,
                H6.H6_OP AS production_order,
                H6.H6_OPERAC AS operation,
                H6.H6_RECURSO AS resource_code,
                SH1.H1_DESCRI AS resource_name,
                SH1.H1_CTRAB AS work_center,
                CT.inspection_work_center_name,
                SUM(CAST(H6.H6_QTDPROD AS FLOAT)) AS shipped_quantity,
                SUM(CAST(H6.H6_QTDPERD AS FLOAT)) AS inspection_loss_quantity,
                COUNT(*) AS total_reports,
                MIN(H6.H6_DATAINI) AS first_start_date,
                MIN(H6.H6_HORAINI) AS first_start_time,
                MAX(H6.H6_DATAFIN) AS last_end_date,
                MAX(H6.H6_HORAFIN) AS last_end_time,
                MAX(H6.H6_DTAPONT) AS last_report_date
            FROM SH6010 H6 WITH (NOLOCK)
            INNER JOIN SB1010 SB1 WITH (NOLOCK)
                ON SB1.B1_COD = H6.H6_PRODUTO
               AND SB1.D_E_L_E_T_ = ''
               AND SB1.B1_TIPO = 'PA'
            INNER JOIN SH1010 SH1 WITH (NOLOCK)
                ON SH1.H1_FILIAL = H6.H6_FILIAL
               AND SH1.H1_CODIGO = H6.H6_RECURSO
               AND SH1.D_E_L_E_T_ = ''
            INNER JOIN CTS_INSPECAO CT
                ON CT.branch = H6.H6_FILIAL
               AND CT.inspection_work_center = SH1.H1_CTRAB
            WHERE H6.D_E_L_E_T_ = ''
              AND H6.H6_PRODUTO = @PRODUTO
              AND H6.H6_DTAPONT >= @DATA_INI
              AND H6.H6_DTAPONT < @DATA_FIM
              {branch_filter}
            GROUP BY
                H6.H6_FILIAL,
                H6.H6_PRODUTO,
                SB1.B1_DESC,
                SB1.B1_TIPO,
                SB1.B1_UM,
                H6.H6_OP,
                H6.H6_OPERAC,
                H6.H6_RECURSO,
                SH1.H1_DESCRI,
                SH1.H1_CTRAB,
                CT.inspection_work_center_name
        )

        SELECT
            branch,
            product_code,
            description,
            product_type,
            unit,
            production_order,
            operation,
            resource_code,
            resource_name,
            work_center,
            inspection_work_center_name,
            CAST(shipped_quantity AS VARCHAR(50)) AS shipped_quantity,
            CAST(inspection_loss_quantity AS VARCHAR(50)) AS inspection_loss_quantity,
            total_reports,
            first_start_date,
            first_start_time,
            last_end_date,
            last_end_time,
            last_report_date
        FROM APONTAMENTO_PA_INSPECAO
        ORDER BY branch, production_order, operation, resource_code;
        """
        with self as repo:
            return repo.execute_batch_query(sql, tuple(params))
