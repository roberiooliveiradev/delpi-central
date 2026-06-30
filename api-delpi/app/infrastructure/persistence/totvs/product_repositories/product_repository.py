# app/infrastructure/persistence/totvs/product_repositories/product_repository.py

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.domain.entities.product.product import Product
from app.application.models.page import Page
from app.infrastructure.persistence.totvs.pagination import paginate
from app.domain.ports.product.product_query_repository_port import ProductQueryRepositoryPort


class ProductRepository(BaseRepository, ProductQueryRepositoryPort):

    def search_products(
        self,
        code=None,
        group=None,
        description=None,
        customer_reference=None,
        page=1,
        page_size=50,
        sort=None,
        direction="asc"
    ) -> Page[Product]:

        paging = paginate(page, page_size)

        where_clauses = ["SB1.D_E_L_E_T_ = ''"]
        where_params = []

        # -----------------------------
        # CODE
        # -----------------------------

        if code:
            where_clauses.append("SB1.B1_COD LIKE ?")
            where_params.append(f"{code}%")

        # -----------------------------
        # GROUP
        # -----------------------------

        if group:
            where_clauses.append("SB1.B1_GRUPO = ?")
            where_params.append(group)

        # -----------------------------
        # CUSTOMER REFERENCE (B1_REFEREN)
        # -----------------------------

        if customer_reference:
            ref_clean = customer_reference.strip()
            where_clauses.append("SB1.B1_REFEREN COLLATE Latin1_General_CI_AI LIKE ?")
            where_params.append(f"{ref_clean}%")

        # -----------------------------
        # DESCRIPTION SEARCH
        # -----------------------------

        score_sql = "0"
        score_params = []

        if description:

            desc_clean = description.strip()
            terms = [t for t in desc_clean.split() if t]

            desc_where = []

            for t in terms:
                desc_where.append(
                    "SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ?"
                )
                where_params.append(f"{t}%")

            where_clauses.append("(" + " OR ".join(desc_where) + ")")

            score_parts = []

            score_parts.append(
                "CASE WHEN SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ? THEN 100 ELSE 0 END"
            )
            score_params.append(f"{desc_clean}%")

            for t in terms:
                score_parts.append(
                    "CASE WHEN SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ? THEN 20 ELSE 0 END"
                )
                score_params.append(f"{t}%")

            score_sql = " + ".join(score_parts)

        where_clause = " AND ".join(where_clauses)

        # -----------------------------
        # SORT
        # -----------------------------

        sortable_fields = {
            "code": "SB1.B1_COD",
            "description": "SB1.B1_DESC",
            "group_code": "SB1.B1_GRUPO"
        }

        sort_column = sortable_fields.get(sort, None)

        direction = "DESC" if str(direction).lower() == "desc" else "ASC"

        if sort_column:
            order_clause = f"{sort_column} {direction}"
        elif customer_reference:
            order_clause = """
                CASE
                    WHEN SB1.B1_TIPO = 'PA' AND SB1.B1_COD LIKE '9026%' THEN 0
                    WHEN SB1.B1_TIPO = 'PA' THEN 1
                    ELSE 2
                END,
                SB1.B1_REFEREN,
                SB1.B1_COD
            """
        else:
            order_clause = "relevance_score DESC, SB1.B1_DESC, SB1.B1_COD"

        # -----------------------------
        # COUNT
        # -----------------------------

        count_sql = f"""
        SELECT COUNT(*) as total
        FROM SB1010 SB1
        WHERE {where_clause}
        """

        # -----------------------------
        # DATA
        # -----------------------------

        sql = f"""
        SELECT
            SB1.B1_COD AS code,
            SB1.B1_DESC AS description,
            SB1.B1_GRUPO AS group_code,

            -- =====================
            -- IDENTIFICAÇÃO
            -- =====================
            SB1.B1_GRUPO     AS group_code,
            SB1.B1_COD       AS code,
            SB1.B1_DESC      AS description,
            SB1.B1_TIPO      AS type,
            SB1.B1_SUBGRUP   AS subgroup,
            SB1.B1_CODANT    AS previous_code,
            SB1.B1_ATIVO     AS active,
            SB1.B1_MSBLQL   AS blocked,

            -- =====================
            -- COMERCIAL
            -- =====================
            SB1.B1_REFEREN   AS customer_reference,
            SB1.B1_REFCANT   AS customer_reference_old,
            SB1.B1_PRV1      AS sale_price,
            SB1.B1_CONTRAT   AS contractual_product,
            SB1.B1_CLASSVE   AS sales_class,

            -- =====================
            -- ENGENHARIA / PRODUÇÃO
            -- =====================
            SB1.B1_CODDES    AS drawing_code,
            SB1.B1_UM        AS unit,
            SB1.B1_SEGUM     AS secondary_unit,
            SB1.B1_CONV      AS conversion_factor,
            SB1.B1_TIPCONV   AS conversion_type,
            SB1.B1_TPMAT     AS material_type,
            SB1.B1_LINHA     AS production_line,
            SB1.B1_TIPODEC   AS operation_decimal_type,
            SB1.B1_REVATU    AS current_revision,
            SB1.B1_UREV      AS last_revision_date,
            SB1.B1_PESO      AS net_weight,

            -- =====================
            -- ESTOQUE / LOGÍSTICA
            -- =====================
            SB1.B1_LOCPAD    AS default_warehouse,
            SB1.B1_QE        AS package_quantity,
            SB1.B1_CODBAR    AS barcode,
            SB1.B1_EMBDELP   AS customer_packaging,
            SB1.B1_PRODSBP   AS make_or_buy,

            -- =====================
            -- COMPRAS
            -- =====================
            SB1.B1_UCOM      AS last_purchase_date,
            SB1.B1_UPRC      AS last_purchase_price,
            SB1.B1_TIPE      AS lead_time_type,
            SB1.B1_SOLICIT   AS requester_restriction,

            -- =====================
            -- CUSTOS
            -- =====================
            SB1.B1_CUSTD     AS standard_cost,
            SB1.B1_UCALSTD   AS standard_cost_date,
            SB1.B1_MCUSTD   AS cost_currency,
            SB1.B1_DATREF   AS cost_reference_date,
            SB1.B1_DESPIMP  AS import_expense,

            -- =====================
            -- FISCAL / TRIBUTÁRIO
            -- =====================
            SB1.B1_POSIPI   AS ncm_ipi_position,
            SB1.B1_ORIGEM   AS origin,
            SB1.B1_IMPORT   AS imported_product,
            SB1.B1_GRTRIB   AS tax_group,
            SB1.B1_TE       AS entry_tes,
            SB1.B1_TS       AS exit_tes,
            SB1.B1_PICM     AS icms_rate,
            SB1.B1_IPI      AS ipi_rate,
            SB1.B1_PIS      AS pis_incidence,
            SB1.B1_PPIS     AS pis_percent,
            SB1.B1_COFINS   AS cofins_incidence,
            SB1.B1_PCOFINS  AS cofins_percent,
            SB1.B1_CSLL     AS csll_incidence,
            SB1.B1_INSS     AS inss_incidence,
            SB1.B1_RETOPER  AS retention_by_operation,
            SB1.B1_ANUENTE  AS customs_authority,
            SB1.B1_MIDIA    AS media_product,
            SB1.B1_QTMIDIA  AS media_quantity,
            SB1.B1_GRPTI    AS intelligent_tes_group,

            -- =====================
            -- QUALIDADE / PCP
            -- =====================
            SB1.B1_YHOHS    AS rohs_indicator,
            SB1.B1_RASTRO   AS traceability,
            SB1.B1_GARANT   AS warranty_product,
            SB1.B1_MRP      AS mrp_considered,
            SB1.B1_FLAGSUG  AS suggestion_flag,
            SB1.B1_CPOTENC  AS power_control,

            -- =====================
            -- CONTÁBIL
            -- =====================
            SB1.B1_CONTA    AS accounting_account,
            SB1.B1_CC       AS cost_center,
            SB1.B1_APROPRI  AS appropriation_type,

            -- =====================
            -- SISTEMA / CONTROLES DELPI
            -- =====================
            SB1.B1_CONINI   AS initial_consumption_date,
            SB1.B1_USERLGI  AS created_by,
            SB1.B1_USERLGA  AS updated_by,
            SB1.B1_YSC      AS mandatory_cc_sc,
            SB1.B1_YPC      AS mandatory_cc_pc,
            SB1.B1_YPV      AS mandatory_cc_pv,
            SB1.B1_YMI      AS mandatory_cc_mi,
            SB1.B1_YNFE     AS mandatory_cc_nfe,
            SB1.B1_YVLPC    AS approval_validation,
            SB1.B1_YCAT     AS delpi_category,
            SB1.B1_ZDLPSEG  AS delpi_segment,

            ({score_sql}) AS relevance_score
        FROM SB1010 SB1
        WHERE {where_clause}
        ORDER BY {order_clause}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:

            total_row = repo.execute_one(
                count_sql,
                tuple(where_params)
            )

            total = int(total_row["total"]) if total_row else 0

            rows = repo.execute_query(
                sql,
                tuple(score_params + where_params + [paging["offset"], paging["page_size"]])
            )

        products = [
            Product(**{k: v for k, v in row.items() if k != "relevance_score"})
            for row in rows
        ]

        return Page(
            items=products,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"]
        )

    def fetch_product_by_code(self, code: str) -> dict | None:
        sql = """
        SELECT TOP 1
            SB1.B1_COD AS product_code,
            SB1.B1_DESC AS description,
            SB1.B1_TIPO AS product_type,
            SB1.B1_UM AS unit,
            SB1.B1_GRUPO AS group_code,
            SB1.B1_REFEREN AS customer_reference
        FROM SB1010 SB1 WITH (NOLOCK)
        WHERE SB1.D_E_L_E_T_ = ''
          AND SB1.B1_COD = ?
        """
        with self as repo:
            return repo.execute_one(sql, (code,))

    def fetch_product_by_customer_reference(self, reference: str) -> dict | None:
        sql = """
        SELECT TOP 1
            SB1.B1_COD AS product_code,
            SB1.B1_DESC AS description,
            SB1.B1_TIPO AS product_type,
            SB1.B1_UM AS unit,
            SB1.B1_GRUPO AS group_code,
            SB1.B1_REFEREN AS customer_reference
        FROM SB1010 SB1 WITH (NOLOCK)
        WHERE SB1.D_E_L_E_T_ = ''
          AND SB1.B1_REFEREN = ?
        ORDER BY
            CASE
                WHEN SB1.B1_TIPO = 'PA' AND SB1.B1_COD LIKE '9026%' THEN 0
                WHEN SB1.B1_TIPO = 'PA' THEN 1
                ELSE 2
            END,
            SB1.B1_COD
        """
        with self as repo:
            return repo.execute_one(sql, (reference,))
