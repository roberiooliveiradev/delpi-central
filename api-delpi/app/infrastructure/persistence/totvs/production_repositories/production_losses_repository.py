from app.domain.services.production.production_loss_type_filter_service import (
    ProductionLossTypeFilterService,
)
from app.domain.ports.production.production_losses_repository_port import (
    ProductionLossesRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class ProductionLossesRepository(
    BaseRepository,
    ProductionLossesRepositoryPort,
):
    def _base_filters(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        loss_type: str,
    ) -> tuple[str, list]:
        loss_clause, loss_params = ProductionLossTypeFilterService.sql_in_clause(loss_type)
        branch_filter = "AND BC.BC_FILIAL = ?" if branch else ""
        params = [date_start, date_end_exclusive, *loss_params]
        if branch:
            params.append(branch)

        where = f"""
            BC.D_E_L_E_T_ = ''
            AND SB1.D_E_L_E_T_ = ''
            AND BC.BC_DATA >= ?
            AND BC.BC_DATA < ?
            AND SB1.B1_TIPO = 'MP'
            AND {loss_clause}
            {branch_filter}
        """
        return where, params

    def fetch_loss_records(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
        loss_type: str,
    ) -> list[dict]:
        where, params = self._base_filters(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            loss_type=loss_type,
        )

        sql = f"""
        SELECT TOP {int(limit)}
            BC.BC_FILIAL AS branch,
            BC.BC_DATA AS loss_date,
            BC.BC_OP AS production_order,
            BC.BC_OPERAC AS operation,
            BC.BC_PRODUTO AS material_code,
            SB1.B1_DESC AS description,
            BC.BC_TIPO AS loss_type,
            BC.BC_QUANT AS loss_qty,
            BC.BC_MOTIVO AS reason,
            BC.BC_RECURSO AS resource,
            BC.BC_SEQSD3 AS sd3_sequence,
            BC.BC_IDENSH6 AS appointment_id
        FROM SBC010 BC WITH (NOLOCK)
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = BC.BC_PRODUTO
        WHERE {where}
        ORDER BY BC.BC_QUANT DESC, BC.BC_DATA DESC, BC.BC_PRODUTO ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    def fetch_top_materials(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
        loss_type: str,
    ) -> list[dict]:
        where, params = self._base_filters(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            loss_type=loss_type,
        )

        sql = f"""
        SELECT TOP {int(limit)}
            BC.BC_FILIAL AS branch,
            BC.BC_PRODUTO AS material_code,
            SB1.B1_DESC AS description,
            BC.BC_TIPO AS loss_type,
            SUM(BC.BC_QUANT) AS total_loss_qty,
            COUNT(*) AS occurrence_count
        FROM SBC010 BC WITH (NOLOCK)
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = BC.BC_PRODUTO
        WHERE {where}
        GROUP BY
            BC.BC_FILIAL,
            BC.BC_PRODUTO,
            SB1.B1_DESC,
            BC.BC_TIPO
        ORDER BY total_loss_qty DESC, BC.BC_PRODUTO ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))
