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
            where_clauses.append("SB1.B1_COD LIKE ?")
            params.append(f"{request.codigo.strip()}%")

        if request.descricao:
            desc_clean = request.descricao.strip()
            terms = [term for term in desc_clean.split() if term]
            desc_where = []
            for term in terms:
                desc_where.append("SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ?")
                params.append(f"%{term}%")
            where_clauses.append("(" + " OR ".join(desc_where) + ")")

        where_sql = " AND ".join(where_clauses)

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
                RTRIM(SB1.B1_GRUPO) AS grupo
            FROM SB1010 SB1 WITH (NOLOCK)
            WHERE {where_sql}
            ORDER BY SB1.B1_COD
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

    def list_pecas(self, codigo_ferramenta: str) -> list[dict]:
        query = """
            SELECT
                RTRIM(G1.G1_COMP) AS codigo,
                RTRIM(SB1.B1_DESC) AS descricao,
                RTRIM(SB1.B1_GRUPO) AS grupo
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN SB1010 SB1 WITH (NOLOCK)
                ON SB1.B1_COD = G1.G1_COMP
               AND SB1.D_E_L_E_T_ = ''
            WHERE G1.D_E_L_E_T_ = ''
              AND G1.G1_COD = ?
              AND SB1.B1_GRUPO = '3019'
            ORDER BY G1.G1_COMP
        """
        with self:
            return self.execute_query(query, (codigo_ferramenta.strip(),))

    def get_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        data_inicial: str,
        data_final: str,
    ) -> dict:
        query = """
            SELECT COALESCE(SUM(CAST(SH6.H6_QTDPROD AS BIGINT)), 0) AS total_golpes
            FROM SH6010 SH6 WITH (NOLOCK)
            WHERE SH6.D_E_L_E_T_ = ''
              AND SH6.H6_FILIAL = ?
              AND RTRIM(SH6.H6_RECURSO) = ?
              AND SH6.H6_DATAINI >= ?
              AND SH6.H6_DATAINI <= ?
        """
        with self:
            total = self.execute_scalar(
                query,
                (filial.strip(), codigo_ferramenta.strip(), data_inicial, data_final),
            )
        return {
            "codigo_ferramenta": codigo_ferramenta.strip(),
            "filial": filial.strip(),
            "data_inicial": data_inicial,
            "data_final": data_final,
            "total_golpes": int(total or 0),
        }
