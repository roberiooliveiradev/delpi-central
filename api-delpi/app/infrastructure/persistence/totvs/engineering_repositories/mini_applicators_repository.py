from __future__ import annotations

from app.application.dto.mini_applicators.list_ferramentas_request import (
    ListMiniApplicatorsFerramentasRequest,
)
from app.application.models.page import Page
from app.domain.entities.mini_applicators.mini_applicator_tool import MiniApplicatorTool
from app.domain.ports.mini_applicators.mini_applicators_repository_port import (
    MiniApplicatorsRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.engineering_repositories.mini_applicators_query_parts import (
    bloqueado_filter_sql,
    codigo_filter_sql,
    codigo_prefix_pattern,
    is_protheus_product_blocked,
)
from app.infrastructure.persistence.totvs.protheus_datetime import (
    parse_protheus_period_end,
    parse_protheus_period_start,
)


class MiniApplicatorsRepository(BaseRepository, MiniApplicatorsRepositoryPort):
    _GROUP_CODES = ("23", "24")

    def list_ferramentas(
        self,
        request: ListMiniApplicatorsFerramentasRequest,
    ) -> Page[MiniApplicatorTool]:
        paging = paginate(request.page, request.page_size)

        where_clauses = [
            "SB1.D_E_L_E_T_ = ''",
            "SB1.B1_GRUPO IN (?, ?)",
        ]
        params: list = list(self._GROUP_CODES)

        if request.codigo:
            pattern = codigo_prefix_pattern(request.codigo)
            where_clauses.append(codigo_filter_sql())
            params.extend([pattern, pattern])

        if request.descricao:
            desc_clean = request.descricao.strip()
            terms = [term for term in desc_clean.split() if term]
            desc_where = []
            for term in terms:
                desc_where.append("SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ?")
                params.append(f"%{term}%")
            where_clauses.append("(" + " OR ".join(desc_where) + ")")

        if not request.incluir_bloqueados:
            where_clauses.append(bloqueado_filter_sql())

        where_sql = " AND ".join(where_clauses)
        sort_columns = {
            "codigo": "RTRIM(LTRIM(SB1.B1_COD))",
            "descricao": "SB1.B1_DESC",
        }
        sort_key = (request.sort_by or "codigo").strip().lower()
        sort_column = sort_columns.get(sort_key, sort_columns["codigo"])
        sort_direction = "DESC" if str(request.sort_dir or "asc").lower() == "desc" else "ASC"

        count_query = f"""
            SELECT COUNT(1) AS total
            FROM SB1010 SB1 WITH (NOLOCK)
            WHERE {where_sql}
        """

        list_query = f"""
            SELECT
                SB1.R_E_C_N_O_ AS id,
                RTRIM(SB1.B1_COD) AS codigo,
                RTRIM(SB1.B1_DESC) AS descricao,
                RTRIM(SB1.B1_GRUPO) AS grupo,
                SB1.B1_MSBLQL AS bloqueado_raw
            FROM SB1010 SB1 WITH (NOLOCK)
            WHERE {where_sql}
            ORDER BY {sort_column} {sort_direction}
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self:
            total = int(self.execute_scalar(count_query, tuple(params)) or 0)
            rows = self.execute_query(
                list_query,
                tuple(params + [paging["offset"], paging["page_size"]]),
            )

        items = [
            MiniApplicatorTool(
                id=int(row["id"]),
                codigo=str(row["codigo"]),
                descricao=str(row["descricao"]),
                grupo=str(row.get("grupo") or ""),
                bloqueado=is_protheus_product_blocked(row.get("bloqueado_raw")),
            )
            for row in rows
        ]

        return Page(
            items=items,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"],
        )

    def get_ferramenta(self, codigo: str) -> MiniApplicatorTool | None:
        query = """
            SELECT
                SB1.R_E_C_N_O_ AS id,
                RTRIM(SB1.B1_COD) AS codigo,
                RTRIM(SB1.B1_DESC) AS descricao,
                RTRIM(SB1.B1_GRUPO) AS grupo
            FROM SB1010 SB1 WITH (NOLOCK)
            WHERE SB1.D_E_L_E_T_ = ''
              AND SB1.B1_GRUPO IN (?, ?)
              AND SB1.B1_COD = ?
        """

        with self:
            row = self.execute_one(query, (*self._GROUP_CODES, codigo.strip()))

        if not row:
            return None

        return MiniApplicatorTool(
            id=int(row["id"]),
            codigo=str(row["codigo"]),
            descricao=str(row["descricao"]),
            grupo=str(row.get("grupo") or ""),
        )

    def list_pecas(self, codigo_ferramenta: str, *, filial: str = "01") -> list[dict]:
        """Peças 3019* presentes na árvore vigente (mesma regra de list_componentes)."""
        seen: set[str] = set()
        pecas: list[dict] = []
        for row in self.list_componentes(
            codigo_ferramenta=codigo_ferramenta,
            filial=filial,
        ):
            codigo = str(row.get("codigo") or "").strip()
            if not codigo or codigo in seen or not codigo.startswith("3019"):
                continue
            seen.add(codigo)
            pecas.append(
                {
                    "codigo": codigo,
                    "descricao": str(row.get("descricao") or ""),
                    "grupo": "3019",
                }
            )
        return sorted(pecas, key=lambda item: item["codigo"])

    def get_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        data_inicial: str,
        data_final: str,
    ) -> dict:
        data_ini, hora_ini = parse_protheus_period_start(data_inicial)
        data_fim, hora_fim = parse_protheus_period_end(data_final)
        query = """
            SELECT CAST(
                SUM(
                    CASE
                        WHEN SD4.D4_QTDEORI > SD4.D4_QUANT
                        THEN SD4.D4_QTDEORI - SD4.D4_QUANT
                        ELSE SD4.D4_QTDEORI
                    END
                ) AS BIGINT
            ) AS total_golpes
            FROM SD4010 AS SD4 WITH (NOLOCK)
            INNER JOIN SHY010 AS SHY WITH (NOLOCK)
                ON SHY.HY_FILIAL = SD4.D4_FILIAL
               AND SHY.HY_OP = SD4.D4_OP
               AND SHY.HY_ROTEIRO = SD4.D4_ROTEIRO
               AND SHY.HY_OPERAC = SD4.D4_OPERAC
            INNER JOIN SH4010 AS SH4 WITH (NOLOCK)
                ON SHY.HY_FERRAM = SH4.H4_CODIGO
            INNER JOIN SB1010 AS SB1 WITH (NOLOCK)
                ON SD4.D4_COD = SB1.B1_COD
            WHERE SD4.D_E_L_E_T_ = ''
              AND SD4.D4_FILIAL = ?
              AND SHY.D_E_L_E_T_ = ''
              AND SHY.HY_FILIAL = ?
              AND SH4.D_E_L_E_T_ = ''
              AND SH4.H4_FILIAL = ?
              AND SB1.D_E_L_E_T_ = ''
              AND SB1.B1_GRUPO = '1008'
              AND SH4.H4_CODIGO = ?
              AND EXISTS (
                SELECT 1
                FROM SH6010 AS SH6 WITH (NOLOCK)
                WHERE SH6.D_E_L_E_T_ = ''
                  AND SH6.H6_TIPO = 'P'
                  AND SH6.H6_FILIAL = SD4.D4_FILIAL
                  AND SH6.H6_OP = SD4.D4_OP
                  AND SH6.H6_OPERAC = SD4.D4_OPERAC
                  AND (
                      (SH6.H6_DATAINI > ?)
                      OR (SH6.H6_DATAINI = ? AND SH6.H6_HORAINI >= ?)
                  )
                  AND (
                      (SH6.H6_DATAINI < ?)
                      OR (SH6.H6_DATAINI = ? AND SH6.H6_HORAINI <= ?)
                  )
              )
        """
        params = (
            filial.strip(),
            filial.strip(),
            filial.strip(),
            codigo_ferramenta.strip(),
            data_ini,
            data_ini,
            hora_ini,
            data_fim,
            data_fim,
            hora_fim,
        )
        with self:
            total = self.execute_scalar(query, params)
        return {
            "codigo_ferramenta": codigo_ferramenta.strip(),
            "filial": filial.strip(),
            "data_inicial": data_inicial,
            "data_final": data_final,
            "total_golpes": int(total or 0),
        }

    def list_componentes(self, *, codigo_ferramenta: str, filial: str) -> list[dict]:
        query = """
WITH EstruturaCTE AS (
    SELECT
        0 AS NIVEL,
        CAST(NULL AS VARCHAR(50)) AS COD_PAI,
        CAST(RTRIM(LTRIM(?)) AS VARCHAR(50)) AS COD_COMPONENTE,
        CAST('000' AS VARCHAR(MAX)) AS PATH
    UNION ALL
    SELECT
        E.NIVEL + 1 AS NIVEL,
        CAST(RTRIM(LTRIM(G1.G1_COD)) AS VARCHAR(50)) AS COD_PAI,
        CAST(RTRIM(LTRIM(G1.G1_COMP)) AS VARCHAR(50)) AS COD_COMPONENTE,
        CAST(E.PATH + '.' + RIGHT('000' + CAST(
            ROW_NUMBER() OVER (PARTITION BY G1.G1_COD ORDER BY G1.G1_COMP) AS VARCHAR(3)
        ), 3) AS VARCHAR(MAX)) AS PATH
    FROM SG1010 AS G1
    INNER JOIN EstruturaCTE AS E
        ON RTRIM(LTRIM(G1.G1_COD)) = RTRIM(LTRIM(E.COD_COMPONENTE))
    WHERE G1.D_E_L_E_T_ = ''
      AND (
            RTRIM(LTRIM(G1.G1_FIM)) = ''
            OR RTRIM(LTRIM(G1.G1_FIM)) > CONVERT(CHAR(8), GETDATE(), 112)
          )
)
SELECT
    C.R_E_C_N_O_ AS id,
    E.NIVEL AS nivel,
    RTRIM(LTRIM(E.COD_COMPONENTE)) AS codigo,
    RTRIM(LTRIM(C.B1_DESC)) AS descricao,
    RTRIM(LTRIM(C.B1_UM)) AS unidade,
    ISNULL((
        SELECT SUM(B2_QATU)
        FROM SB2010 AS S1
        WHERE RTRIM(LTRIM(S1.B2_COD)) = RTRIM(LTRIM(C.B1_COD))
          AND RTRIM(LTRIM(S1.B2_LOCAL)) = '01'
          AND S1.D_E_L_E_T_ = ''
          AND S1.B2_FILIAL = ?
    ), 0) AS estoque_local_01,
    ISNULL((
        SELECT SUM(B2_QATU)
        FROM SB2010 AS S2
        WHERE RTRIM(LTRIM(S2.B2_COD)) = RTRIM(LTRIM(C.B1_COD))
          AND RTRIM(LTRIM(S2.B2_LOCAL)) = '99'
          AND S2.D_E_L_E_T_ = ''
          AND S2.B2_FILIAL = ?
    ), 0) AS estoque_local_99
FROM EstruturaCTE AS E
INNER JOIN SB1010 AS C
    ON RTRIM(LTRIM(E.COD_COMPONENTE)) = RTRIM(LTRIM(C.B1_COD))
WHERE C.D_E_L_E_T_ = ''
  AND E.NIVEL > 0
ORDER BY E.PATH
OPTION (MAXRECURSION 100)
"""
        codigo = codigo_ferramenta.strip()
        filial_code = filial.strip()
        with self:
            rows = self.execute_query(query, (codigo, filial_code, filial_code))

        return [
            {
                "id": int(row["id"]),
                "nivel": int(row["nivel"]),
                "codigo": str(row["codigo"]),
                "descricao": str(row["descricao"]),
                "unidade": str(row.get("unidade") or ""),
                "estoque_local_01": float(row.get("estoque_local_01") or 0),
                "estoque_local_99": float(row.get("estoque_local_99") or 0),
            }
            for row in rows
        ]
