# app/repositories/product_repository.py
from app.repositories.base_repository import BaseRepository
from app.core.exceptions import BusinessLogicError
from app.utils.logger import log_info, log_error
from typing import Optional, Union
from datetime import datetime
import math
import json

class ProductRepository(BaseRepository):
    """
    Repositório responsável por consultas na tabela SG1010 (estrutura) e SB1010 (produtos).
    """
    
    def _convert_date_to_protheus(self, date_value: Optional[Union[str, datetime]]) -> Optional[str]:
        """
        Converte vários formatos de data para 'YYYYMMDD' (padrão Protheus).

        Formatos aceitos:
        - datetime
        - 'YYYY-MM-DD'
        - 'YYYY/MM/DD'
        - 'DD/MM/YYYY'
        - 'DD-MM-YYYY'
        - 'YYYYMMDD'
        - ISO completo: 'YYYY-MM-DDTHH:MM:SS'
        - ISO com timezone: 'YYYY-MM-DDTHH:MM:SSZ'
        """

        if not date_value:
            return None

        # Caso já seja datetime
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y%m%d")

        if not isinstance(date_value, str):
            return None

        date_value = date_value.strip()

        # Se já estiver no padrão Protheus
        if date_value.isdigit() and len(date_value) == 8:
            return date_value

        # Lista de formatos conhecidos
        known_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y%m%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in known_formats:
            try:
                parsed = datetime.strptime(date_value, fmt)
                return parsed.strftime("%Y%m%d")
            except ValueError:
                continue

        # Tentativa final: ISO 8601 genérico (Python 3.11+ / compatível)
        try:
            parsed = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            return parsed.strftime("%Y%m%d")
        except Exception:
            return None


    def _build_hierarchy(
        self,
        rows: list[dict],
        root_code: str,
        mode: str = "structure"
    ) -> dict:
        """
        Builds a nested JSON hierarchy.

        mode:
            - "structure": component tree (parent → children)
            - "parents": where-used tree (child → parents)
        """
        from collections import defaultdict

        # Each node always has a components list
        nodes = defaultdict(lambda: {"components": []})

        for row in rows:
            if mode == "structure":
                parent_code = row["parent_code"]
                child_code = row["component_code"]
                parent_description = row.get("parent_description") or ""
                child_description = row.get("component_description") or ""
            else:
                # parents (where-used)
                parent_code = row["parent_code"]
                child_code = row["child_code"]
                parent_description = row.get("parent_description") or ""
                child_description = row.get("child_description") or ""

            # -----------------------------
            # Parent node
            # -----------------------------
            nodes[parent_code]["code"] = parent_code
            nodes[parent_code]["description"] = parent_description
            nodes[parent_code]["quantity"] = float(row.get("quantity") or 0)

            # -----------------------------
            # Child node
            # -----------------------------
            nodes[child_code]["code"] = child_code
            nodes[child_code]["description"] = child_description
            nodes[child_code]["quantity"] = float(row.get("quantity") or 0)

            # -----------------------------
            # Relationship direction
            # -----------------------------
            if mode == "structure":
                # parent → components
                nodes[parent_code]["components"].append(nodes[child_code])
            else:
                # child → parents
                nodes[child_code]["components"].append(nodes[parent_code])

        return nodes[root_code]


    def _build_guide_hierarchy(self, rows: list[dict]) -> list[dict]:
        products = {}

        for r in rows:
            product_code = r["product_code"]

            # -----------------------------
            # Product
            # -----------------------------
            if product_code not in products:
                products[product_code] = {
                    "product_code": product_code,
                    "bom_level": r["bom_level"],
                    "operations": {}
                }

            product = products[product_code]

            # -----------------------------
            # Operation
            # -----------------------------
            op_key = (r["route_code"], r["operation_code"])

            if op_key not in product["operations"]:
                product["operations"][op_key] = {
                    "route_code": r["route_code"],
                    "operation_code": r["operation_code"],
                    "operation_description": r["operation_description"],
                    "work_center": r["work_center"],
                    "resource_code": r["resource_code"],
                    "setup_hours": r["setup_hours"],
                    "standard_time_hour_mil": r["standard_time_hour_mil"],
                    "standard_time_hours_piece": r["standard_time_hours_piece"],
                    "standard_time_minutes_piece": r["standard_time_minutes_piece"],
                    "operation_type": r["operation_type"],
                    "mandatory": {
                        "operation": r["mandatory_operation"] == "1",
                        "sequence": r["mandatory_sequence"] == "1",
                        "report": r["mandatory_report"] == "1"
                    },
                    "components": []
                }

            operation = product["operations"][op_key]

            # -----------------------------
            # Component (if exists)
            # -----------------------------
            if r.get("component_code"):
                operation["components"].append({
                    "component_code": r["component_code"],
                    "component_description": r["component_description"],
                    "component_sequence": r["component_sequence"]
                })

        # -----------------------------
        # Normalize dicts to lists
        # -----------------------------
        return [
            {
                "product_code": p["product_code"],
                "bom_level": p["bom_level"],
                "operations": list(p["operations"].values())
            }
            for p in products.values()
        ]


    def get_products_paginated(self, page: int, page_size: int) -> dict:
        offset = (page - 1) * page_size

        sql = f"""
            SELECT
                B1_COD   AS code,
                B1_DESC  AS description,
                B1_PRV1  AS sale_price
            FROM SB1010
            WHERE D_E_L_E_T_ = ''
            ORDER BY B1_COD
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """

        count_sql = """
            SELECT COUNT(*) as total
            FROM SB1010
            WHERE D_E_L_E_T_ = ''
        """

        items = self.execute_query(sql, (offset, page_size))
        total_result = self.execute_one(count_sql, ())

        total = total_result["total"]
        total_pages = math.ceil(total / page_size)

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }


    # -------------------------------
    # 🔹 PRODUCT (SB1010)  
    # -------------------------------
    def get_product_by_code(self, code: str) -> dict:
        log_info(f"Consultando produto {code} no Protheus (SB1010)...")

        sql = """
            SELECT
                -- =====================
                -- IDENTIFICAÇÃO
                -- =====================
                B1_GRUPO     AS group_code,
                B1_COD       AS code,
                B1_DESC      AS description,
                B1_TIPO      AS type,
                B1_SUBGRUP   AS subgroup,
                B1_CODANT    AS previous_code,
                B1_ATIVO     AS active,
                B1_MSBLQL   AS blocked,

                -- =====================
                -- COMERCIAL
                -- =====================
                B1_REFEREN   AS customer_reference,
                B1_REFCANT   AS customer_reference_old,
                B1_PRV1      AS sale_price,
                B1_CONTRAT   AS contractual_product,
                B1_CLASSVE   AS sales_class,

                -- =====================
                -- ENGENHARIA / PRODUÇÃO
                -- =====================
                B1_CODDES    AS drawing_code,
                B1_UM        AS unit,
                B1_SEGUM     AS secondary_unit,
                B1_CONV      AS conversion_factor,
                B1_TIPCONV   AS conversion_type,
                B1_TPMAT     AS material_type,
                B1_LINHA     AS production_line,
                B1_TIPODEC   AS operation_decimal_type,
                B1_REVATU    AS current_revision,
                B1_UREV      AS last_revision_date,
                B1_PESO      AS net_weight,

                -- =====================
                -- ESTOQUE / LOGÍSTICA
                -- =====================
                B1_LOCPAD    AS default_warehouse,
                B1_QE        AS package_quantity,
                B1_CODBAR    AS barcode,
                B1_EMBDELP   AS customer_packaging,
                B1_PRODSBP   AS make_or_buy,

                -- =====================
                -- COMPRAS
                -- =====================
                B1_UCOM      AS last_purchase_date,
                B1_UPRC      AS last_purchase_price,
                B1_TIPE      AS lead_time_type,
                B1_SOLICIT   AS requester_restriction,

                -- =====================
                -- CUSTOS
                -- =====================
                B1_CUSTD     AS standard_cost,
                B1_UCALSTD   AS standard_cost_date,
                B1_MCUSTD   AS cost_currency,
                B1_DATREF   AS cost_reference_date,
                B1_DESPIMP  AS import_expense,

                -- =====================
                -- FISCAL / TRIBUTÁRIO
                -- =====================
                B1_POSIPI   AS ncm_ipi_position,
                B1_ORIGEM   AS origin,
                B1_IMPORT   AS imported_product,
                B1_GRTRIB   AS tax_group,
                B1_TE       AS entry_tes,
                B1_TS       AS exit_tes,
                B1_PICM     AS icms_rate,
                B1_IPI      AS ipi_rate,
                B1_PIS      AS pis_incidence,
                B1_PPIS     AS pis_percent,
                B1_COFINS   AS cofins_incidence,
                B1_PCOFINS  AS cofins_percent,
                B1_CSLL     AS csll_incidence,
                B1_INSS     AS inss_incidence,
                B1_RETOPER  AS retention_by_operation,
                B1_ANUENTE  AS customs_authority,
                B1_MIDIA    AS media_product,
                B1_QTMIDIA  AS media_quantity,
                B1_GRPTI    AS intelligent_tes_group,

                -- =====================
                -- QUALIDADE / PCP
                -- =====================
                B1_YHOHS    AS rohs_indicator,
                B1_RASTRO   AS traceability,
                B1_GARANT   AS warranty_product,
                B1_MRP      AS mrp_considered,
                B1_FLAGSUG  AS suggestion_flag,
                B1_CPOTENC  AS power_control,

                -- =====================
                -- CONTÁBIL
                -- =====================
                B1_CONTA    AS accounting_account,
                B1_CC       AS cost_center,
                B1_APROPRI  AS appropriation_type,

                -- =====================
                -- SISTEMA / CONTROLES DELPI
                -- =====================
                B1_CONINI   AS initial_consumption_date,
                B1_USERLGI  AS created_by,
                B1_USERLGA  AS updated_by,
                B1_YSC      AS mandatory_cc_sc,
                B1_YPC      AS mandatory_cc_pc,
                B1_YPV      AS mandatory_cc_pv,
                B1_YMI      AS mandatory_cc_mi,
                B1_YNFE     AS mandatory_cc_nfe,
                B1_YVLPC    AS approval_validation,
                B1_YCAT     AS delpi_category,
                B1_ZDLPSEG  AS delpi_segment

            FROM SB1010
            WHERE D_E_L_E_T_ = ''
            AND B1_COD = ?
        """

        product = self.execute_one(sql, (code,))

        if not product:
            raise BusinessLogicError(
                f"Produto com código '{code}' não encontrado."
            )

        return {
            "success": True,
            "data": product
        }
    

    # -------------------------------
    # 🔹 SEACH PRODUCTS BY DESCRIPTION 
    # -------------------------------
    def search_by_description(
        self,
        description: str,
        page: int = 1,
        page_size: int = 50,
    ):
        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")
        if not description:
            raise ValueError("Description cannot be empty")

        offset = (page - 1) * page_size
        desc_clean = description.strip()
        terms = [t for t in desc_clean.split() if t]

        # -----------------------------
        # WHERE simples (OR)
        # -----------------------------
        where_clauses = ["SB1.D_E_L_E_T_ = ''"]
        where_terms = []
        params = []

        for t in terms:
            where_terms.append(
                "SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ?"
            )
            params.append(f"%{t}%")

        where_clauses.append("(" + " OR ".join(where_terms) + ")")
        where_sql = " AND ".join(where_clauses)

        # -----------------------------
        # SCORE claro e barato
        # -----------------------------
        score_parts = [
            "CASE WHEN SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ? THEN 50 ELSE 0 END"
        ]
        score_params = [f"%{desc_clean}%"]

        for t in terms:
            score_parts.append(
                "CASE WHEN SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ? THEN 10 ELSE 0 END"
            )
            score_params.append(f"%{t}%")

        score_sql = " + ".join(score_parts)

        # -----------------------------
        # COUNT
        # -----------------------------
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM SB1010 SB1
            WHERE {where_sql}
        """
        total = int(self.execute_one(count_sql, tuple(params))["total"] or 0)

        # -----------------------------
        # DATA
        # -----------------------------
        sql = f"""
            SELECT
                SB1.B1_GRUPO     AS group_code,
                SB1.B1_COD       AS code,
                SB1.B1_DESC      AS description,
                SB1.B1_UM        AS unit,
                SB1.B1_TIPO      AS type,
                SB1.B1_SUBGRUP   AS subgroup,
                SB1.B1_CODANT    AS previous_code,
                SB1.B1_ATIVO     AS active,
                SB1.B1_MSBLQL    AS blocked,
                ({score_sql})    AS relevance_score
            FROM SB1010 SB1
            WHERE {where_sql}
            ORDER BY relevance_score DESC, SB1.B1_DESC, SB1.B1_COD
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(
            sql,
            tuple(score_params + params + [offset, page_size])
        )

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "description": description,
            "results": rows
        }


    # -------------------------------
    # 🔹 STRUCTURE (BOM)
    # -------------------------------
    def list_structure(
        self,
        code: str,
        max_depth: int = 5,
        page: int = 1,
        page_size: int = 100
    ) -> dict:
        """
        Returns the product BOM (structure) in hierarchical format,
        including product type (B1_TIPO) and unit of measure (B1_UM).
        SQL Server compatible.
        """

        data_query = """
            WITH recursive_bom AS (
                SELECT 
                    G1_COD   AS parent_code,
                    G1_COMP  AS component_code,
                    G1_QUANT AS quantity,
                    1        AS bom_level
                FROM SG1010 WITH (NOLOCK)
                WHERE D_E_L_E_T_ = ''
                AND G1_COD = ?
                AND G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

                UNION ALL

                SELECT 
                    c.G1_COD,
                    c.G1_COMP,
                    c.G1_QUANT,
                    p.bom_level + 1
                FROM SG1010 c WITH (NOLOCK)
                INNER JOIN recursive_bom p
                    ON p.component_code = c.G1_COD
                WHERE c.D_E_L_E_T_ = ''
                AND p.bom_level < ?
                AND c.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
            )
            SELECT 
                rb.parent_code,
                parent.B1_DESC AS parent_description,
                parent.B1_TIPO AS parent_type,
                parent.B1_UM   AS parent_unit,

                rb.component_code,
                comp.B1_DESC   AS component_description,
                comp.B1_TIPO   AS component_type,
                comp.B1_UM     AS component_unit,

                rb.quantity,
                rb.bom_level
            FROM recursive_bom rb
            LEFT JOIN SB1010 parent WITH (NOLOCK)
                ON parent.B1_COD = rb.parent_code
            AND parent.D_E_L_E_T_ = ''
            LEFT JOIN SB1010 comp WITH (NOLOCK)
                ON comp.B1_COD = rb.component_code
            AND comp.D_E_L_E_T_ = ''
            ORDER BY
                rb.bom_level,
                rb.parent_code,
                rb.component_code;
        """

        rows = self.execute_query(data_query, (code, max_depth))

        items: dict[str, dict] = {}

        for r in rows:
            component_node = {
                "code": r["component_code"],
                "description": r["component_description"],
                "type": r["component_type"],
                "unit": r["component_unit"],
                "quantity": float(r["quantity"]) if r["quantity"] is not None else 0.0,
                "components": []
            }

            parent_code = r["parent_code"]

            if parent_code not in items:
                items[parent_code] = {
                    "code": parent_code,
                    "description": r["parent_description"],
                    "type": r["parent_type"],
                    "unit": r["parent_unit"],
                    "quantity": 1.0,
                    "components": []
                }

            items[parent_code]["components"].append(component_node)
            items[component_node["code"]] = component_node

        root = items.get(
            code,
            {
                "code": code,
                "description": None,
                "type": None,
                "unit": None,
                "quantity": 1.0,
                "components": []
            }
        )

        # Pagination only at root level
        root_components = root.get("components", [])
        offset = (page - 1) * page_size
        root["components"] = root_components[offset: offset + page_size]

        return {
            "success": True,
            "total": len(root_components),
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(len(root_components) / page_size),
            "data": root
        }


    # -------------------------------
    # 🔹 STRUCTURE (BOM) - FULL
    # -------------------------------
    def list_structure_full(self, code: str) -> dict:
        """
        Returns the full product BOM (structure) in hierarchical format,
        including product type (B1_TIPO) and unit of measure (B1_UM).
        SQL Server compatible.
        """

        data_query = """
            WITH recursive_bom AS (
                SELECT 
                    G1_COD   AS parent_code,
                    G1_COMP  AS component_code,
                    G1_QUANT AS quantity,
                    1        AS bom_level
                FROM SG1010 WITH (NOLOCK)
                WHERE D_E_L_E_T_ = ''
                AND G1_COD = ?
                AND G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

                UNION ALL

                SELECT 
                    c.G1_COD,
                    c.G1_COMP,
                    c.G1_QUANT,
                    p.bom_level + 1
                FROM SG1010 c WITH (NOLOCK)
                INNER JOIN recursive_bom p
                    ON p.component_code = c.G1_COD
                WHERE c.D_E_L_E_T_ = ''
                AND p.bom_level < 50
                AND c.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
            )
            SELECT 
                rb.parent_code,
                parent.B1_DESC AS parent_description,
                parent.B1_TIPO AS parent_type,
                parent.B1_UM   AS parent_unit,

                rb.component_code,
                comp.B1_DESC   AS component_description,
                comp.B1_TIPO   AS component_type,
                comp.B1_UM     AS component_unit,

                rb.quantity,
                rb.bom_level
            FROM recursive_bom rb
            LEFT JOIN SB1010 parent WITH (NOLOCK)
                ON parent.B1_COD = rb.parent_code
            AND parent.D_E_L_E_T_ = ''
            LEFT JOIN SB1010 comp WITH (NOLOCK)
                ON comp.B1_COD = rb.component_code
            AND comp.D_E_L_E_T_ = ''
            ORDER BY
                rb.bom_level,
                rb.parent_code,
                rb.component_code;
        """

        rows = self.execute_query(data_query, (code,))

        # -------------------------------------------------
        # Build hierarchical structure
        # -------------------------------------------------
        items: dict[str, dict] = {}

        for r in rows:
            component_node = {
                "code": r["component_code"],
                "description": r["component_description"],
                "type": r["component_type"],
                "unit": r["component_unit"],
                "quantity": float(r["quantity"]) if r["quantity"] is not None else 0.0,
                "components": []
            }

            parent_code = r["parent_code"]

            if parent_code not in items:
                items[parent_code] = {
                    "code": parent_code,
                    "description": r["parent_description"],
                    "type": r["parent_type"],
                    "unit": r["parent_unit"],
                    "quantity": 1.0,
                    "components": []
                }

            items[parent_code]["components"].append(component_node)
            items[component_node["code"]] = component_node

        root = items.get(
            code,
            {
                "code": code,
                "description": None,
                "type": None,
                "unit": None,
                "quantity": 1.0,
                "components": []
            }
        )

        return {
            "success": True,
            "total": len(root.get("components", [])),
            "page": None,
            "page_size": None,
            "total_pages": None,
            "data": root
        }


    # -------------------------------
    # 🔹 PARENTS (WHERE USED)
    # -------------------------------
    def list_parents(
        self,
        code: str,
        max_depth: int = 10,
        page: int = 1,
        page_size: int = 50
    ) -> dict:
        """
        Returns parent products (WHERE USED) in hierarchical format.
        Includes product type (B1_TIPO) and unit of measure (B1_UM).
        SQL Server compatible.
        Preserves original quantities (G1_QUANT).
        """

        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")
        if not 1 <= max_depth <= 50:
            raise ValueError("max_depth must be between 1 and 50")

        log_info(
            f"Querying parents (WHERE USED) for {code}, "
            f"depth={max_depth}, page={page}, size={page_size}"
        )

        # =====================================================
        # Recursive CTE (no internal pagination)
        # =====================================================
        data_query = """
            WITH recursive_parents AS (
                SELECT 
                    G1_COD   AS parent_code,
                    G1_COMP  AS child_code,
                    G1_QUANT AS quantity,
                    1        AS level
                FROM SG1010 WITH (NOLOCK)
                WHERE D_E_L_E_T_ = ''
                AND G1_COMP = ?

                UNION ALL

                SELECT 
                    c.G1_COD   AS parent_code,
                    c.G1_COMP  AS child_code,
                    c.G1_QUANT AS quantity,
                    p.level + 1 AS level
                FROM SG1010 c WITH (NOLOCK)
                INNER JOIN recursive_parents p
                    ON p.parent_code = c.G1_COMP
                WHERE c.D_E_L_E_T_ = ''
                AND p.level < ?
            )
            SELECT 
                rp.parent_code,
                parent.B1_DESC AS parent_description,
                parent.B1_TIPO AS parent_type,
                parent.B1_UM   AS parent_unit,

                rp.child_code,
                child.B1_DESC  AS child_description,
                child.B1_TIPO  AS child_type,
                child.B1_UM    AS child_unit,

                rp.quantity,
                rp.level
            FROM recursive_parents rp
            LEFT JOIN SB1010 parent WITH (NOLOCK)
                ON parent.B1_COD = rp.parent_code
            AND parent.D_E_L_E_T_ = ''
            LEFT JOIN SB1010 child WITH (NOLOCK)
                ON child.B1_COD = rp.child_code
            AND child.D_E_L_E_T_ = ''
            ORDER BY
                rp.level,
                rp.parent_code,
                rp.child_code;
        """

        rows = self.execute_query(data_query, (code, max_depth))

        # =====================================================
        # Build hierarchical structure (child → parents)
        # =====================================================
        items: dict[str, dict] = {}

        for r in rows:
            parent_node = {
                "code": r["parent_code"],
                "description": r["parent_description"],
                "type": r["parent_type"],
                "unit": r["parent_unit"],
                "quantity": float(r["quantity"]) if r["quantity"] is not None else 0.0,
                "parents": []
            }

            child_code = r["child_code"]

            if child_code not in items:
                items[child_code] = {
                    "code": child_code,
                    "description": r["child_description"],
                    "type": r["child_type"],
                    "unit": r["child_unit"],
                    "quantity": 1.0,
                    "parents": []
                }

            # attach parent to child
            items[child_code]["parents"].append(parent_node)

            # index parent globally
            items[parent_node["code"]] = parent_node

        # =====================================================
        # Root product (queried child)
        # =====================================================
        root = items.get(
            code,
            {
                "code": code,
                "description": None,
                "type": None,
                "unit": None,
                "quantity": 1.0,
                "parents": []
            }
        )

        # Pagination only at first parent level
        root_parents = root.get("parents", [])
        offset = (page - 1) * page_size
        root["parents"] = root_parents[offset: offset + page_size]

        return {
            "success": True,
            "total": len(root_parents),
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(len(root_parents) / page_size),
            "data": root
        }


    # -------------------------------
    # 🔹 SUPPLIERS
    # -------------------------------
    def list_suppliers(
        self,
        code: str,
        page: int = 1,
        page_size: int = 50
    ) -> dict:

        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")

        offset = (page - 1) * page_size

        count_sql = """
            SELECT COUNT(*) AS total
            FROM SA5010
            WHERE D_E_L_E_T_ = ''
            AND A5_PRODUTO = ?
        """

        total = int(self.execute_one(count_sql, (code,))["total"] or 0)

        sql = """
            WITH LAST_PURCHASE AS (
                SELECT
                    C7.C7_PRODUTO   AS product_code,
                    C7.C7_FORNECE   AS supplier_code,
                    C7.C7_LOJA      AS supplier_store,
                    C7.C7_PRECO     AS last_price,
                    C7.C7_EMISSAO   AS last_price_date,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            C7.C7_PRODUTO,
                            C7.C7_FORNECE,
                            C7.C7_LOJA
                        ORDER BY
                            C7.C7_EMISSAO DESC
                    ) AS rn
                FROM SC7010 C7
                WHERE
                    C7.D_E_L_E_T_ = ''
                    AND C7.C7_PRODUTO = ?
            ),

            REAL_LEAD_TIME AS (
                SELECT
                    C7.C7_PRODUTO   AS product_code,
                    C7.C7_FORNECE   AS supplier_code,
                    C7.C7_LOJA      AS supplier_store,
                    COUNT(*)        AS sample_size,
                    AVG(DATEDIFF(DAY, C7.C7_EMISSAO, SD1.D1_EMISSAO)) AS avg_lead_time_days,
                    MIN(DATEDIFF(DAY, C7.C7_EMISSAO, SD1.D1_EMISSAO)) AS min_lead_time_days,
                    MAX(DATEDIFF(DAY, C7.C7_EMISSAO, SD1.D1_EMISSAO)) AS max_lead_time_days
                FROM SC7010 C7
                INNER JOIN SD1010 SD1
                    ON SD1.D1_PEDIDO  = C7.C7_NUM
                AND SD1.D1_FORNECE = C7.C7_FORNECE
                AND SD1.D1_LOJA    = C7.C7_LOJA
                AND SD1.D1_COD     = C7.C7_PRODUTO
                AND SD1.D_E_L_E_T_ = ''
                WHERE
                    C7.D_E_L_E_T_ = ''
                    AND C7.C7_PRODUTO = ?
                GROUP BY
                    C7.C7_PRODUTO,
                    C7.C7_FORNECE,
                    C7.C7_LOJA
            )

            SELECT
                -- Product
                SB1.B1_COD      AS product_code,
                SB1.B1_DESC     AS product_description,
                SB1.B1_UM       AS unit,

                -- Supplier
                SA5.A5_FORNECE  AS supplier_code,
                SA5.A5_LOJA     AS supplier_store,
                SA2.A2_NOME     AS supplier_name,

                -- Supplier product codes
                SA5.A5_CODPRF   AS supplier_part_number,
                SA5.A5_CODPRCA  AS catalog_code,
                SA5.A5_CODBAR   AS barcode,

                -- Lead times
                SA5.A5_LEAD_T           AS registered_lead_time_days,
                RLT.avg_lead_time_days  AS real_avg_lead_time_days,
                RLT.min_lead_time_days  AS real_min_lead_time_days,
                RLT.max_lead_time_days  AS real_max_lead_time_days,
                RLT.sample_size         AS real_lead_time_sample_size,

                -- Last price
                LP.last_price           AS last_price,
                LP.last_price_date      AS last_price_date

            FROM SA5010 SA5
            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = SA5.A5_PRODUTO
            AND SB1.D_E_L_E_T_ = ''

            LEFT JOIN SA2010 SA2
                ON SA2.A2_COD = SA5.A5_FORNECE
            AND SA2.A2_LOJA = SA5.A5_LOJA
            AND SA2.D_E_L_E_T_ = ''

            LEFT JOIN LAST_PURCHASE LP
                ON LP.product_code = SA5.A5_PRODUTO
            AND LP.supplier_code = SA5.A5_FORNECE
            AND LP.supplier_store = SA5.A5_LOJA
            AND LP.rn = 1

            LEFT JOIN REAL_LEAD_TIME RLT
                ON RLT.product_code = SA5.A5_PRODUTO
            AND RLT.supplier_code = SA5.A5_FORNECE
            AND RLT.supplier_store = SA5.A5_LOJA

            WHERE
                SA5.D_E_L_E_T_ = ''
                AND SA5.A5_PRODUTO = ?

            ORDER BY SA5.A5_FORNECE
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(
            sql,
            (code, code, code, offset, page_size)
        )

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "data": rows
        }


    # -------------------------------
    # 🔹 INBOUND INVOICE ITEMS (Notas Fiscais de Entrada)
    # -------------------------------
    def list_inbound_invoice_items(
        self,
        code: str,
        page: int = 1,
        page_size: int = 50,
        issue_date_start: Optional[str] = None,
        issue_date_end: Optional[str] = None,
        supplier: Optional[str] = None,
        branch: Optional[str] = None
    ) -> dict:

        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")

        offset = (page - 1) * page_size

        filters = []
        params = [code]

        if issue_date_start:
            issue_date_start = self._convert_date_to_protheus(issue_date_start)
            filters.append("SD1.D1_EMISSAO >= ?")
            params.append(issue_date_start)

        if issue_date_end:
            issue_date_end = self._convert_date_to_protheus(issue_date_end)
            filters.append("SD1.D1_EMISSAO <= ?")
            params.append(issue_date_end)

        if supplier:
            filters.append("SD1.D1_FORNECE = ?")
            params.append(supplier)

        if branch:
            filters.append("SD1.D1_FILIAL = ?")
            params.append(branch)

        where_extra = " AND " + " AND ".join(filters) if filters else ""

        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM SD1010 SD1
            WHERE SD1.D_E_L_E_T_ = ''
            AND SD1.D1_COD = ? {where_extra}
        """

        total = int(self.execute_one(count_sql, tuple(params))["total"] or 0)

        data_sql = f"""
            SELECT
                SD1.D1_FILIAL    AS branch,
                SD1.D1_DOC       AS invoice_number,
                SD1.D1_SERIE     AS invoice_series,
                SD1.D1_ITEM      AS item,
                SD1.D1_EMISSAO   AS issue_date,

                SD1.D1_COD       AS product_code,
                SB1.B1_DESC      AS product_description,
                SB1.B1_UM        AS unit,

                SD1.D1_FORNECE   AS supplier_code,
                SA2.A2_NOME      AS supplier_name,

                SD1.D1_QUANT     AS quantity,
                CASE 
                    WHEN SD1.D1_QUANT <> 0 
                    THEN SD1.D1_TOTAL / SD1.D1_QUANT 
                    ELSE 0 
                END              AS unit_price,
                SD1.D1_TOTAL     AS total_value

            FROM SD1010 SD1
            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = SD1.D1_COD
            AND SB1.D_E_L_E_T_ = ''
            LEFT JOIN SA2010 SA2
                ON SA2.A2_COD = SD1.D1_FORNECE
            AND SA2.A2_LOJA = SD1.D1_LOJA
            AND SA2.D_E_L_E_T_ = ''
            WHERE SD1.D_E_L_E_T_ = ''
            AND SD1.D1_COD = ? {where_extra}
            ORDER BY SD1.D1_EMISSAO DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(
            data_sql,
            tuple(params + [offset, page_size])
        )

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "filters": {
                "issue_date_start": issue_date_start,
                "issue_date_end": issue_date_end,
                "supplier": supplier,
                "branch": branch
            },
            "data": rows
        }


    # -------------------------------
    # 🔹 OUTBOUND INVOICE ITEMS (Notas Fiscais de Saída)
    # -------------------------------
    def list_outbound_invoice_items(
        self,
        code: str,
        page: int = 1,
        page_size: int = 50,
        issue_date_start: Optional[str] = None,
        issue_date_end: Optional[str] = None,
        customer: Optional[str] = None,
        branch: Optional[str] = None
    ) -> dict:

        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")

        offset = (page - 1) * page_size

        filters = []
        params = [code]

        if issue_date_start:
            issue_date_start = self._convert_date_to_protheus(issue_date_start)
            filters.append("SD2.D2_EMISSAO >= ?")
            params.append(issue_date_start)

        if issue_date_end:
            issue_date_end = self._convert_date_to_protheus(issue_date_end)
            filters.append("SD2.D2_EMISSAO <= ?")
            params.append(issue_date_end)

        if customer:
            filters.append("SD2.D2_CLIENTE = ?")
            params.append(customer)

        if branch:
            filters.append("SD2.D2_FILIAL = ?")
            params.append(branch)

        where_extra = " AND " + " AND ".join(filters) if filters else ""

        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM SD2010 SD2
            WHERE SD2.D_E_L_E_T_ = ''
            AND SD2.D2_COD = ? {where_extra}
        """

        total = int(self.execute_one(count_sql, tuple(params))["total"] or 0)

        data_sql = f"""
            SELECT
                SD2.D2_FILIAL    AS branch,
                SD2.D2_DOC       AS invoice_number,
                SD2.D2_SERIE     AS invoice_series,
                SD2.D2_ITEM      AS item,
                SD2.D2_EMISSAO   AS issue_date,

                SD2.D2_COD       AS product_code,
                SB1.B1_DESC      AS product_description,
                SB1.B1_UM        AS unit,

                SD2.D2_CLIENTE   AS customer_code,
                SA1.A1_NOME      AS customer_name,

                SD2.D2_QUANT     AS quantity,
                SD2.D2_PRCVEN    AS unit_price,
                (SD2.D2_QUANT * SD2.D2_PRCVEN) AS total_value

            FROM SD2010 SD2
            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = SD2.D2_COD
            AND SB1.D_E_L_E_T_ = ''
            LEFT JOIN SA1010 SA1
                ON SA1.A1_COD = SD2.D2_CLIENTE
            AND SA1.A1_LOJA = SD2.D2_LOJA
            AND SA1.D_E_L_E_T_ = ''
            WHERE SD2.D_E_L_E_T_ = ''
            AND SD2.D2_COD = ? {where_extra}
            ORDER BY SD2.D2_EMISSAO DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(
            data_sql,
            tuple(params + [offset, page_size])
        )

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "filters": {
                "issue_date_start": issue_date_start,
                "issue_date_end": issue_date_end,
                "customer": customer,
                "branch": branch
            },
            "data": rows
        }
    

    # -------------------------------
    # 🔹 STOCK + LOCALIZAÇÃO FÍSICA (SB2010 + SBZ010)
    # -------------------------------
    def list_stock(
        self,
        code: str,
        page: int = 1,
        page_size: int = 50,
        branch: Optional[str] = None,
        location: Optional[str] = None
    ) -> dict:

        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")

        offset = (page - 1) * page_size

        filters = [
            "SB2.D_E_L_E_T_ = ''",
            "SB2.B2_COD = ?"
        ]
        params = [code]

        if branch:
            filters.append("SB2.B2_FILIAL = ?")
            params.append(branch)

        if location:
            filters.append("SB2.B2_LOCAL = ?")
            params.append(location)

        where_clause = " AND ".join(filters)

        # -------------------------------
        # TOTAL
        # -------------------------------
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM SB2010 SB2
            WHERE {where_clause}
        """

        total = int(self.execute_one(count_sql, tuple(params))["total"] or 0)

        # -------------------------------
        # DATA
        # -------------------------------
        data_sql = f"""
            SELECT
                SB2.B2_COD      AS product_code,
                SB2.B2_FILIAL   AS branch,
                SB2.B2_LOCAL    AS warehouse,
                SB2.B2_QATU     AS current_quantity,
                SB2.B2_QEMP     AS committed_quantity,
                SB2.B2_RESERVA  AS reserved_quantity,
                (SB2.B2_QATU - SB2.B2_QEMP - SB2.B2_RESERVA) AS available_quantity,

                -- Physical location (SBZ)
                SBZ.BZ_MPLOCAL  AS physical_location,
                SBZ.BZ_LOCPAD   AS default_warehouse,
                SBZ.BZ_CUSTO    AS cost_center,
                SBZ.BZ_GALPAO   AS warehouse_section

            FROM SB2010 SB2
            LEFT JOIN SBZ010 SBZ
                ON  SBZ.BZ_COD    = SB2.B2_COD
                AND SBZ.BZ_FILIAL = SB2.B2_FILIAL

            WHERE {where_clause}
            ORDER BY SB2.B2_FILIAL, SB2.B2_LOCAL
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(
            data_sql,
            tuple(params + [offset, page_size])
        )

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "filters": {
                "branch": branch,
                "location": location
            },
            "data": rows
        }


    # -------------------------------
    # 🔹 GUIDE (SG2010)
    # -------------------------------
    def list_guide(
        self,
        code: str,
        page: int = 1,
        page_size: int = 50,
        branch: Optional[str] = None,
        max_depth: int = 10
    ) -> dict:

        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")

        offset = (page - 1) * page_size

        sg2_filters = ["SG2.D_E_L_E_T_ = ''"]
        sg2_params: list = []

        if branch:
            sg2_filters.append("SG2.G2_FILIAL = ?")
            sg2_params.append(branch)

        where_clause = " AND ".join(sg2_filters)

        count_sql = f"""
            WITH RECURSIVE_BOM AS (
                SELECT
                    G1_COD  AS parent_code,
                    G1_COMP AS product_code,
                    1       AS bom_level
                FROM SG1010
                WHERE D_E_L_E_T_ = ''
                AND G1_COD = ?

                UNION ALL

                SELECT
                    C.G1_COD,
                    C.G1_COMP,
                    B.bom_level + 1
                FROM SG1010 C
                INNER JOIN RECURSIVE_BOM B
                    ON B.product_code = C.G1_COD
                WHERE C.D_E_L_E_T_ = ''
                AND B.bom_level < ?
            ),
            CODES AS (
                SELECT ? AS product_code, 0 AS bom_level
                UNION
                SELECT DISTINCT product_code, bom_level FROM RECURSIVE_BOM
            )
            SELECT COUNT(*) AS total
            FROM SG2010 SG2
            INNER JOIN CODES
                ON CODES.product_code = SG2.G2_PRODUTO
            WHERE {where_clause}
        """

        total = int(
            self.execute_one(
                count_sql,
                tuple([code, max_depth, code] + sg2_params)
            )["total"] or 0
        )

        data_sql = f"""
            WITH RECURSIVE_BOM AS (
                SELECT
                    G1_COD  AS parent_code,
                    G1_COMP AS product_code,
                    1       AS bom_level
                FROM SG1010
                WHERE D_E_L_E_T_ = ''
                AND G1_COD = ?

                UNION ALL

                SELECT
                    C.G1_COD,
                    C.G1_COMP,
                    B.bom_level + 1
                FROM SG1010 C
                INNER JOIN RECURSIVE_BOM B
                    ON B.product_code = C.G1_COD
                WHERE C.D_E_L_E_T_ = ''
                AND B.bom_level < ?
            ),
            CODES AS (
                SELECT ? AS product_code, 0 AS bom_level
                UNION ALL
                SELECT DISTINCT product_code, bom_level FROM RECURSIVE_BOM
            )
            SELECT
                SG2.G2_FILIAL  AS branch,
                SG2.G2_CODIGO  AS route_code,
                SG2.G2_PRODUTO AS product_code,
                SG2.G2_OPERAC  AS operation_code,
                SG2.G2_DESCRI  AS operation_description,

                SG2.G2_RECURSO AS resource_code,
                SG2.G2_CTRAB   AS work_center,

                SG2.G2_SETUP                    AS setup_hours, 
                SG2.G2_TEMPAD                   AS standard_time_hour_mil, 
                SG2.G2_TEMPAD / 1000.0          AS standard_time_hours_piece, 
                (SG2.G2_TEMPAD / 1000.0) * 60   AS standard_time_minutes_piece, 


                SG2.G2_TPOPER  AS operation_type,
                SG2.G2_OPE_OBR AS mandatory_operation,
                SG2.G2_SEQ_OBR AS mandatory_sequence,
                SG2.G2_LAU_OBR AS mandatory_report,

                SGF.GF_COMP    AS component_code,
                SB1.B1_DESC    AS component_description,
                SGF.GF_TRT     AS component_sequence,

                CODES.bom_level AS bom_level

            FROM SG2010 SG2
            INNER JOIN CODES
                ON CODES.product_code = SG2.G2_PRODUTO
            LEFT JOIN SGF010 SGF
                ON SGF.GF_FILIAL  = SG2.G2_FILIAL
            AND SGF.GF_PRODUTO = SG2.G2_PRODUTO
            AND SGF.GF_ROTEIRO = SG2.G2_CODIGO
            AND SGF.GF_OPERAC  = SG2.G2_OPERAC
            AND SGF.D_E_L_E_T_ = ''
            LEFT JOIN SB1010 SB1
                ON SB1.B1_COD = SGF.GF_COMP
            AND SB1.D_E_L_E_T_ = ''
            WHERE {where_clause}
            ORDER BY
                CODES.bom_level,
                SG2.G2_PRODUTO,
                SG2.G2_OPERAC,
                SGF.GF_TRT
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(
            data_sql,
            tuple([code, max_depth, code] + sg2_params + [offset, page_size])
        )

        hierarchy = self._build_guide_hierarchy(rows)

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "filters": {
                "branch": branch,
                "max_depth": max_depth
            },
            "data": hierarchy
        }


    # -------------------------------
    # 🔹 INSPECTION DEFINITION (QP6 / QP7 / QP8)
    # -------------------------------
    def list_inspection_definition(
        self,
        code: str,
        max_depth: int = 10
    ) -> dict:
        """
        Returns the INSPECTION DEFINITION (QP6, QP7, QP8) of a product
        and its components according to SG1010.

        ⚠️ DOES NOT return:
            - inspection history
            - results
            - non-conformities
        """

        # -------------------------------
        # Validations
        # -------------------------------
        if not code:
            raise ValueError("code must be provided")

        if max_depth < 1 or max_depth > 20:
            raise ValueError("max_depth must be between 1 and 20")

        # ============================================================
        # SQL — inspection definition with controlled revision
        # ============================================================
        sql = """
        DECLARE
            @product_code NVARCHAR(20) = ?,
            @max_depth INT = ?;

        -- ============================================================
        -- Product structure (SG1010)
        -- ============================================================
        WITH bom_recursive AS (
            SELECT
                G1.G1_COD  AS root_code,
                G1.G1_COMP AS product_code,
                1          AS bom_level
            FROM SG1010 G1 WITH (NOLOCK)
            WHERE G1.D_E_L_E_T_ = ''
            AND G1.G1_COD = @product_code

            UNION ALL

            SELECT
                B.root_code,
                G1.G1_COMP,
                B.bom_level + 1
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN bom_recursive B
                ON B.product_code = G1.G1_COD
            WHERE G1.D_E_L_E_T_ = ''
            AND B.bom_level < @max_depth
        ),

        product_scope AS (
            SELECT @product_code AS product_code, 0 AS bom_level
            UNION
            SELECT product_code, bom_level FROM bom_recursive
        ),

        -- ============================================================
        -- Active revision per product (QP6)
        -- ============================================================
        active_qp6 AS (
            SELECT
                QP6_PRODUT AS product_code,
                MAX(QP6_REVI) AS revision
            FROM QP6010
            WHERE D_E_L_E_T_ = ''
            GROUP BY QP6_PRODUT
        ),

        -- ============================================================
        -- Products with valid inspection definition
        -- ============================================================
        inspection_scope AS (
            SELECT
                P.product_code AS product_code,
                P.bom_level    AS bom_level,
                R.revision     AS revision
            FROM product_scope P
            INNER JOIN active_qp6 R
                ON R.product_code = P.product_code
        )

        -- ============================================================
        -- Final JSON
        -- ============================================================
        SELECT
        (
            SELECT
                COUNT(*) AS total,
                (
                    SELECT
                        I.product_code,
                        I.bom_level,

                        CASE
                            WHEN EXISTS (
                                SELECT 1
                                FROM QP7010
                                WHERE D_E_L_E_T_ = ''
                                AND QP7_PRODUT = I.product_code
                                AND QP7_REVI = I.revision
                            )
                            OR EXISTS (
                                SELECT 1
                                FROM QP8010
                                WHERE D_E_L_E_T_ = ''
                                AND QP8_PRODUT = I.product_code
                                AND QP8_REVI = I.revision
                            )
                            THEN CAST(1 AS BIT)
                            ELSE CAST(0 AS BIT)
                        END AS has_inspection,

                        -- =========================
                        -- QP6 — Inspection header
                        -- =========================
                        (
                            SELECT
                                QP6.QP6_PRODUT  AS product_code,
                                QP6.QP6_REVI    AS revision,
                                QP6.QP6_REVINV  AS review_invalid,
                                QP6.QP6_DESCPO  AS description,
                                QP6.QP6_DTCAD   AS created_at,
                                QP6.QP6_DTINI   AS start_date,
                                QP6.QP6_CADR    AS created_by,
                                QP6.QP6_PTOLER  AS tolerance_percent,
                                QP6.QP6_TIPO    AS inspection_type,
                                QP6.QP6_DOCOBR  AS requires_document,
                                QP6.QP6_SITPRD  AS product_status,
                                QP6.QP6_DESSTP  AS status_description,
                                QP6.QP6_UNMED1  AS unit
                            FROM QP6010 QP6 WITH (NOLOCK)
                            WHERE QP6.D_E_L_E_T_ = ''
                            AND QP6.QP6_PRODUT = I.product_code
                            AND QP6.QP6_REVI = I.revision
                            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                        ) AS qp6,

                        -- =========================
                        -- QP7 — Measurable tests
                        -- =========================
                        (
                            SELECT
                                QP7.QP7_PRODUT  AS product_code,
                                QP7.QP7_REVI    AS revision,
                                QP7.QP7_ENSAIO  AS test_code,
                                QP7.QP7_LABOR   AS labor,
                                QP7.QP7_SEQLAB  AS sequence,
                                QP7.QP7_UNIMED  AS unit,
                                QP7.QP7_MINMAX  AS min_max_type,
                                QP7.QP7_NOMINA  AS nominal_value,
                                QP7.QP7_LIE     AS lower_spec_limit,
                                QP7.QP7_LSE     AS upper_spec_limit,
                                QP7.QP7_LIC     AS lower_control_limit,
                                QP7.QP7_LSC     AS upper_control_limit,
                                QP7.QP7_CODREC  AS reaction_code,
                                QP7.QP7_OPERAC  AS operation,
                                QP7.QP7_ENSOBR  AS mandatory,
                                QP7.QP7_CERTIF  AS certification
                            FROM QP7010 QP7 WITH (NOLOCK)
                            WHERE QP7.D_E_L_E_T_ = ''
                            AND QP7.QP7_PRODUT = I.product_code
                            AND QP7.QP7_REVI = I.revision
                            FOR JSON PATH
                        ) AS qp7,

                        -- =========================
                        -- QP8 — Textual tests
                        -- =========================
                        (
                            SELECT
                                QP8.QP8_PRODUT  AS product_code,
                                QP8.QP8_REVI    AS revision,
                                QP8.QP8_ENSAIO  AS test_code,
                                QP8.QP8_LABOR   AS labor,
                                QP8.QP8_SEQLAB  AS sequence,
                                QP8.QP8_TEXTO   AS text,
                                QP8.QP8_CODREC  AS reaction_code,
                                QP8.QP8_OPERAC  AS operation,
                                QP8.QP8_ENSOBR  AS mandatory,
                                QP8.QP8_CERTIF  AS certification
                            FROM QP8010 QP8 WITH (NOLOCK)
                            WHERE QP8.D_E_L_E_T_ = ''
                            AND QP8.QP8_PRODUT = I.product_code
                            AND QP8.QP8_REVI = I.revision
                            FOR JSON PATH
                        ) AS qp8

                    FROM inspection_scope I
                    ORDER BY I.bom_level, I.product_code
                    FOR JSON PATH
                ) AS data
            FROM inspection_scope
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        ) AS data;
        """

        # ============================================================
        # Execution
        # ============================================================
        params = (code, max_depth)
        result = self.execute_json(sql, params)

        return {
            "success": True,
            "total": result.get("total", 0),
            "data": result.get("data", [])
        }


    # -------------------------------
    # 🔹 INSPECTION (QP6/QP7/QP8) 
    # -------------------------------
    def list_inspection(
        self,
        code: str,
        page: int = 1,
        page_size: int = 50,
        max_depth: int = 10
    ) -> dict:
        """
        Retorna a estrutura completa de inspeção de um produto (QP6, QP7, QP8)
        incluindo seus componentes da árvore SG1010, em formato JSON hierárquico.

        Args:
            code (str): Código do produto principal.
            page (int): Página da consulta (não aplicável na estrutura hierárquica).
            page_size (int): Tamanho de página (não aplicável neste formato).
            max_depth (int): Profundidade máxima da recursão na SG1010.

        Returns:
            dict: Estrutura JSON completa contendo produto, componentes e inspeções.
        """

        # Validações básicas
        if not code:
            raise ValueError("code must be provided")
        if max_depth < 1 or max_depth > 20:
            raise ValueError("max_depth must be between 1 and 20")

        # ============================================================
        # Query SQL única — retorna JSON hierárquico completo
        # ============================================================
        sql = """
        DECLARE 
            @code NVARCHAR(20) = ?, 
            @depth INT = ?, 
            @offset INT = ?, 
            @page_size INT = ?;

        WITH RECURSIVE_BOM AS (
            SELECT 
                G1_COD AS parentCode,
                G1_COMP AS productCode,
                1 AS level
            FROM SG1010 WITH (NOLOCK)
            WHERE D_E_L_E_T_ = '' AND G1_COD = @code

            UNION ALL

            SELECT 
                C.G1_COD,
                C.G1_COMP,
                P.level + 1
            FROM SG1010 C WITH (NOLOCK)
            INNER JOIN RECURSIVE_BOM P 
                ON P.productCode = C.G1_COD
            WHERE C.D_E_L_E_T_ = '' 
            AND P.level < @depth
        ),
        CODES AS (
            SELECT @code AS productCode, NULL AS parentCode, 0 AS level
            UNION ALL
            SELECT productCode, parentCode, level FROM RECURSIVE_BOM
        ),
        TOTAL AS (
            SELECT COUNT(*) AS totalCount FROM CODES
        )
        SELECT 
            (
                SELECT 
                    (SELECT totalCount FROM TOTAL) AS total, -- total real
                    (
                        SELECT 
                            CODES.productCode AS product,
                            CODES.parentCode,
                            CODES.level,

                            -- =========================
                            -- QP6 (Cabeçalho da Inspeção)
                            -- =========================
                            (
                                SELECT
                                    QP6.QP6_PRODUT,
                                    QP6.QP6_REVI,
                                    QP6.QP6_REVINV,
                                    QP6.QP6_DESCPO,
                                    QP6.QP6_DTCAD,
                                    QP6.QP6_DTINI,
                                    QP6.QP6_CADR,
                                    QP6.QP6_PTOLER,
                                    QP6.QP6_TIPO,
                                    QP6.QP6_DOCOBR,
                                    QP6.QP6_SITPRD,
                                    QP6.QP6_DESSTP,
                                    QP6.QP6_UNMED1
                                FROM QP6010 QP6 WITH (NOLOCK)
                                WHERE QP6.D_E_L_E_T_ = ''
                                AND QP6.QP6_PRODUT = CODES.productCode
                                FOR JSON PATH, INCLUDE_NULL_VALUES
                            ) AS QP6,

                            -- =========================
                            -- QP7 (Ensaios Mensuráveis)
                            -- =========================
                            (
                                SELECT
                                    QP7.QP7_PRODUT,
                                    QP7.QP7_REVI,
                                    QP7.QP7_ENSAIO,
                                    QP7.QP7_LABOR,
                                    QP7.QP7_SEQLAB,
                                    QP7.QP7_UNIMED,
                                    QP7.QP7_MINMAX,
                                    QP7.QP7_NOMINA,
                                    QP7.QP7_LIE,
                                    QP7.QP7_LSE,
                                    QP7.QP7_LIC,
                                    QP7.QP7_LSC,
                                    QP7.QP7_CODREC,
                                    QP7.QP7_OPERAC,
                                    QP7.QP7_ENSOBR,
                                    QP7.QP7_CERTIF
                                FROM QP7010 QP7 WITH (NOLOCK)
                                WHERE QP7.D_E_L_E_T_ = ''
                                AND QP7.QP7_PRODUT = CODES.productCode
                                FOR JSON PATH, INCLUDE_NULL_VALUES
                            ) AS QP7,

                            -- =========================
                            -- QP8 (Ensaios Textuais)
                            -- =========================
                            (
                                SELECT
                                    QP8.QP8_PRODUT,
                                    QP8.QP8_REVI,
                                    QP8.QP8_ENSAIO,
                                    QP8.QP8_LABOR,
                                    QP8.QP8_SEQLAB,
                                    QP8.QP8_TEXTO,
                                    QP8.QP8_CODREC,
                                    QP8.QP8_OPERAC,
                                    QP8.QP8_ENSOBR,
                                    QP8.QP8_CERTIF
                                FROM QP8010 QP8 WITH (NOLOCK)
                                WHERE QP8.D_E_L_E_T_ = ''
                                AND QP8.QP8_PRODUT = CODES.productCode
                                FOR JSON PATH, INCLUDE_NULL_VALUES
                            ) AS QP8

                        FROM CODES
                        ORDER BY CODES.level, CODES.productCode
                        OFFSET @offset ROWS FETCH NEXT @page_size ROWS ONLY
                        FOR JSON PATH, INCLUDE_NULL_VALUES
                    ) AS data
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES
            ) AS data; -- Mantém alias fixo


        """
        # ============================================================
        #  Execução e tratamento do retorno
        # ============================================================
        offset = (page - 1) * page_size
        params = (code, max_depth, offset, page_size)
        result = self.execute_json(sql, params)
        total = result.get("total", 0)
        data_json = result.get("data", [])
        # ============================================================
        #  Monta resposta final
        # ============================================================
        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "data": data_json
        }
    

    # -------------------------------
    # 🔹 CUSTOMERS (SA7010/SA1010) 
    # -------------------------------
    def list_customers(self, code: str, page: int = 1, page_size: int = 50) -> dict:
        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")

        offset = (page - 1) * page_size

        count_sql = """
            SELECT COUNT(*) AS total
            FROM SA7010
            WHERE D_E_L_E_T_ = ''
            AND A7_PRODUTO = ?
        """

        total = int(self.execute_one(count_sql, (code,))["total"] or 0)

        sql = """
            WITH last_sale AS (
                SELECT
                    SD2.D2_COD          AS product_code,
                    SD2.D2_CLIENTE     AS customer_code,
                    SD2.D2_LOJA        AS store,
                    MAX(SD2.D2_EMISSAO) AS last_sale_date,
                    SUM(SD2.D2_QUANT)   AS total_quantity,
                    AVG(SD2.D2_PRCVEN)  AS average_price
                FROM SD2010 SD2
                WHERE SD2.D_E_L_E_T_ = ''
                AND SD2.D2_COD = ?
                GROUP BY
                    SD2.D2_COD,
                    SD2.D2_CLIENTE,
                    SD2.D2_LOJA
            )

            SELECT
                -- Product
                SB1.B1_COD      AS product_code,
                SB1.B1_DESC     AS product_description,
                SB1.B1_UM       AS unit,

                -- Customer
                SA1.A1_COD      AS customer_code,
                SA1.A1_LOJA     AS store,
                SA1.A1_NOME     AS customer_name,
                SA1.A1_MSBLQL   AS blocked,

                -- Product x Customer
                SA7.A7_CODCLI   AS customer_product_code,
                SA7.A7_DESCCLI  AS customer_product_description,

                -- Registered price
                SA7.A7_PRECO01  AS registered_price,
                SA7.A7_DTREF01  AS registered_price_date,

                -- Sales info
                LS.average_price   AS last_sale_price,
                LS.last_sale_date,
                LS.total_quantity

            FROM SA7010 SA7
            INNER JOIN SA1010 SA1
                ON SA1.A1_COD = SA7.A7_CLIENTE
            AND SA1.A1_LOJA = SA7.A7_LOJA
            AND SA1.D_E_L_E_T_ = ''

            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = SA7.A7_PRODUTO
            AND SB1.D_E_L_E_T_ = ''

            LEFT JOIN last_sale LS
                ON LS.product_code = SA7.A7_PRODUTO
            AND LS.customer_code = SA7.A7_CLIENTE
            AND LS.store = SA7.A7_LOJA

            WHERE
                SA7.D_E_L_E_T_ = ''
                AND SA7.A7_PRODUTO = ?

            ORDER BY SA1.A1_NOME
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(sql, (code, code, offset, page_size))

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "data": rows
        }


    # -------------------------------
    # 🔹 PURCHASES (SC7010/SA2010) 
    # -------------------------------
    def list_purchases(self, code: str, page: int = 1, page_size: int = 50) -> dict:
        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")

        offset = (page - 1) * page_size

        count_sql = """
            SELECT COUNT(DISTINCT C7.C7_NUM) AS total
            FROM SC7010 C7
            WHERE C7.D_E_L_E_T_ = ''
            AND C7.C7_PRODUTO = ?
        """

        total = int(self.execute_one(count_sql, (code,))["total"] or 0)

        sql = """
            SELECT
                C7.C7_NUM        AS order_number,
                C7.C7_FILIAL     AS branch,
                C7.C7_EMISSAO    AS issue_date,
                C7.C7_FORNECE    AS supplier_code,
                C7.C7_LOJA       AS store,
                SA2.A2_NOME      AS supplier_name,
                C7.C7_PRODUTO    AS product_code,
                SUM(C7.C7_QUANT) AS ordered_quantity,
                AVG(C7.C7_PRECO) AS unit_price
            FROM SC7010 C7
            LEFT JOIN SA2010 SA2
                ON SA2.A2_COD = C7.C7_FORNECE
            AND SA2.A2_LOJA = C7.C7_LOJA
            AND SA2.D_E_L_E_T_ = ''
            WHERE
                C7.D_E_L_E_T_ = ''
                AND C7.C7_PRODUTO = ?
            GROUP BY
                C7.C7_NUM,
                C7.C7_FILIAL,
                C7.C7_EMISSAO,
                C7.C7_FORNECE,
                C7.C7_LOJA,
                SA2.A2_NOME,
                C7.C7_PRODUTO
            ORDER BY C7.C7_EMISSAO DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(sql, (code, offset, page_size))

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "data": rows
        }



    # -------------------------------
    # 🔹 SALES SUMMARY
    # -------------------------------
    def get_sales_summary(self, code: str) -> dict:
        """
        Consolidated sales summary.
        Base: SD2010
        """

        product_sql = """
            SELECT
                B1_COD  AS product_code,
                B1_DESC AS product_description,
                B1_UM   AS unit
            FROM SB1010
            WHERE D_E_L_E_T_ = ''
            AND B1_COD = ?
        """
        product = self.execute_one(product_sql, (code,))

        sales_sql = """
            SELECT
                SUM(D2_QUANT)          AS total_quantity,
                SUM(D2_TOTAL)          AS total_value,
                AVG(D2_PRCVEN)         AS average_price,
                COUNT(DISTINCT D2_DOC) AS documents,
                MIN(D2_EMISSAO)        AS first_sale_date,
                MAX(D2_EMISSAO)        AS last_sale_date
            FROM SD2010
            WHERE D_E_L_E_T_ = ''
            AND D2_COD = ?
        """

        summary = self.execute_one(sales_sql, (code,))

        return {
            "success": True,
            "product": {
                "code": code,
                "description": product["product_description"] if product else None,
                "unit": product["unit"] if product else None
            },
            "summary": {
                "total_quantity": float(summary["total_quantity"] or 0),
                "total_value": float(summary["total_value"] or 0),
                "average_price": float(summary["average_price"] or 0),
                "documents": int(summary["documents"] or 0),
                "first_sale_date": summary["first_sale_date"],
                "last_sale_date": summary["last_sale_date"]
            }
        }


    def get_sales_open_orders(self, code: str) -> dict:
        """
        Open sales orders (real open quantities).
        Base: SC6010
        """

        sql = """
            SELECT
                SUM(C6_QTDVEN - C6_QTDENT)                 AS open_quantity,
                SUM((C6_QTDVEN - C6_QTDENT) * C6_PRCVEN)   AS open_value,
                COUNT(DISTINCT C6_NUM)                     AS orders
            FROM SC6010
            WHERE D_E_L_E_T_ = ''
            AND C6_PRODUTO = ?
            AND (C6_QTDVEN - C6_QTDENT) > 0
            AND (C6_BLOQUEI IS NULL OR C6_BLOQUEI = '')
            AND (C6_BLQ IS NULL OR C6_BLQ = '')
        """

        row = self.execute_one(sql, (code,))

        return {
            "success": True,
            "open_orders": {
                "quantity": float(row["open_quantity"] or 0),
                "value": float(row["open_value"] or 0),
                "orders": int(row["orders"] or 0)
            }
        }


    def get_sales_billing(self, code: str) -> dict:
        """
        Financial billing summary per product.
        Base: SD2010
        """

        sql = """
            SELECT
                SUM(D2_TOTAL)          AS billed_value,
                COUNT(DISTINCT D2_DOC) AS documents,
                MIN(D2_EMISSAO)        AS first_billing_date,
                MAX(D2_EMISSAO)        AS last_billing_date
            FROM SD2010
            WHERE D_E_L_E_T_ = ''
            AND D2_COD = ?
        """

        row = self.execute_one(sql, (code,))

        return {
            "success": True,
            "billing": {
                "value": float(row["billed_value"] or 0),
                "documents": int(row["documents"] or 0),
                "first_billing_date": row["first_billing_date"],
                "last_billing_date": row["last_billing_date"]
            }
        }


    def get_product_pricing(self, code: str) -> dict:
        """
        Returns product commercial pricing.

        Real bases:
        - DA1010 → product pricing
        - DA0010 → price table description
        - SB1010 → product description and unit
        """

        product_sql = """
            SELECT
                B1_COD  AS product_code,
                B1_DESC AS product_description,
                B1_UM   AS unit
            FROM SB1010
            WHERE D_E_L_E_T_ = ''
            AND B1_COD = ?
        """
        product = self.execute_one(product_sql, (code,))

        if not product:
            return {
                "success": False,
                "message": f"Product {code} not found"
            }

        pricing_sql = """
            SELECT
                DA1.DA1_CODTAB AS table_code,
                DA0.DA0_DESCRI AS table_description,

                DA1.DA1_PRCVEN AS sale_price,
                DA1.DA1_PRCMAX AS max_price,

                DA1.DA1_VLRDES AS discount_value,
                DA1.DA1_PERDES AS discount_percent,

                DA1.DA1_QTDLOT AS lot_quantity,
                DA1.DA1_ESTADO AS state,
                DA1.DA1_TPOPER AS operation_type,
                DA1.DA1_MOEDA  AS currency,

                DA1.DA1_DATVIG AS valid_from,
                DA1.DA1_ATIVO  AS active
            FROM DA1010 DA1
            INNER JOIN DA0010 DA0
                ON DA0.DA0_FILIAL = DA1.DA1_FILIAL
            AND DA0.DA0_CODTAB = DA1.DA1_CODTAB
            AND DA0.D_E_L_E_T_ = ''
            WHERE DA1.D_E_L_E_T_ = ''
            AND DA1.DA1_CODPRO = ?
            ORDER BY DA1.DA1_CODTAB, DA1.DA1_DATVIG DESC
        """

        rows = self.execute_query(pricing_sql, (code,))

        return {
            "success": True,
            "product": {
                "code": product["product_code"],
                "description": product["product_description"],
                "unit": product["unit"]
            },
            "prices": rows
        }


    # -------------------------------
    # 🔹 MOVEMENTS
    # -------------------------------
    def list_internal_movements(
        self,
        code: str,
        page: int = 1,
        page_size: int = 50,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        branch: Optional[str] = None,
        location: Optional[str] = None,
        tm: Optional[str] = None,
        op: Optional[str] = None,
    ) -> dict:

        offset = (page - 1) * page_size

        filters = ["SD3.D_E_L_E_T_ = ''", "SD3.D3_COD = ?"]
        params = [code]

        if date_start:
            date_start = self._convert_date_to_protheus(date_start)
            filters.append("SD3.D3_EMISSAO >= ?")
            params.append(date_start)

        if date_end:
            date_end = self._convert_date_to_protheus(date_end)
            filters.append("SD3.D3_EMISSAO <= ?")
            params.append(date_end)

        if branch:
            filters.append("SD3.D3_FILIAL = ?")
            params.append(branch)

        if location:
            filters.append("SD3.D3_LOCAL = ?")
            params.append(location)

        if tm:
            filters.append("SD3.D3_TM = ?")
            params.append(tm)

        if op:
            filters.append("SD3.D3_OP = ?")
            params.append(op)

        where_clause = " AND ".join(filters)

        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM SD3010 SD3
            WHERE {where_clause}
        """

        total = int(self.execute_one(count_sql, tuple(params))["total"] or 0)

        data_sql = f"""
            SELECT
                SD3.D3_FILIAL   AS branch,
                SD3.D3_LOCAL    AS location,
                SD3.D3_DOC      AS document,
                SD3.D3_EMISSAO  AS issue_date,

                SD3.D3_COD      AS product_code,
                SB1.B1_DESC     AS product_description,
                SB1.B1_UM       AS unit,

                SD3.D3_TM       AS movement_type,
                SD3.D3_CF       AS cf,
                SD3.D3_QUANT    AS quantity,
                SD3.D3_OP       AS production_order,
                SD3.D3_USUARIO  AS user_name

            FROM SD3010 SD3
            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = SD3.D3_COD
            AND SB1.D_E_L_E_T_ = ''

            WHERE {where_clause}
            ORDER BY SD3.D3_EMISSAO DESC, SD3.R_E_C_N_O_ DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        rows = self.execute_query(
            data_sql,
            tuple(params + [offset, page_size])
        )

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "filters": {
                "date_start": date_start,
                "date_end": date_end,
                "branch": branch,
                "location": location,
                "tm": tm,
                "op": op
            },
            "data": rows
        }
