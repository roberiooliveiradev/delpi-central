from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class RecursoRepository(PluginBaseRepository):
    def next_codigo(self) -> str:
        row = self.fetch_one(
            """
            SELECT COALESCE(
                MAX(CAST(SUBSTRING(codigo_recurso FROM 4) AS INTEGER)), 0
            ) + 1 AS seq
            FROM transformometro.recursos_compartilhados
            WHERE codigo_recurso ~ '^RC-[0-9]+$'
            """
        )
        seq = int((row or {}).get("seq") or 1)
        return f"RC-{seq:04d}"

    def list(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM transformometro.recursos_compartilhados
            WHERE deletado = FALSE
            ORDER BY nome_recurso ASC
            """
        )

    def get(self, recurso_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT * FROM transformometro.recursos_compartilhados
            WHERE recurso_compartilhado_id = %s AND deletado = FALSE
            """,
            (recurso_id,),
        )

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        codigo = data.get("codigo_recurso") or self.next_codigo()
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.recursos_compartilhados (
                codigo_recurso, nome_recurso, categoria_recurso, fornecedor,
                tipo_custo, recorrencia, valor_total_recorrente,
                data_inicio_vigencia, data_fim_vigencia, centro_custo,
                criterio_rateio, escopo_recurso, base_competencia, status_recurso, observacoes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                codigo,
                data["nome_recurso"],
                data.get("categoria_recurso"),
                data.get("fornecedor"),
                data["tipo_custo"],
                data["recorrencia"],
                data.get("valor_total_recorrente", 0),
                data.get("data_inicio_vigencia"),
                data.get("data_fim_vigencia"),
                data.get("centro_custo"),
                data.get("criterio_rateio", "igualitario"),
                data.get("escopo_recurso", "empresa"),
                data.get("base_competencia", "mensal_cheio"),
                data.get("status_recurso", "ativo"),
                data.get("observacoes"),
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao criar recurso.")
        return row

    def update(self, recurso_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        return self.execute_returning_one(
            """
            UPDATE transformometro.recursos_compartilhados SET
                nome_recurso = %s,
                categoria_recurso = %s,
                fornecedor = %s,
                tipo_custo = %s,
                recorrencia = %s,
                valor_total_recorrente = %s,
                data_inicio_vigencia = %s,
                data_fim_vigencia = %s,
                centro_custo = %s,
                criterio_rateio = %s,
                escopo_recurso = %s,
                base_competencia = %s,
                status_recurso = %s,
                observacoes = %s,
                updated_at = NOW()
            WHERE recurso_compartilhado_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (
                data["nome_recurso"],
                data.get("categoria_recurso"),
                data.get("fornecedor"),
                data["tipo_custo"],
                data["recorrencia"],
                data.get("valor_total_recorrente", 0),
                data.get("data_inicio_vigencia"),
                data.get("data_fim_vigencia"),
                data.get("centro_custo"),
                data.get("criterio_rateio", "igualitario"),
                data.get("escopo_recurso", "empresa"),
                data.get("base_competencia", "mensal_cheio"),
                data.get("status_recurso", "ativo"),
                data.get("observacoes"),
                recurso_id,
            ),
        )

    def soft_delete(self, recurso_id: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.recursos_compartilhados
            SET deletado = TRUE, updated_at = NOW()
            WHERE recurso_compartilhado_id = %s AND deletado = FALSE
            RETURNING recurso_compartilhado_id
            """,
            (recurso_id,),
        )
        return row is not None


class VinculoRepository(PluginBaseRepository):
    _VINCULO_SELECT = """
            SELECT
                v.vinculo_id,
                v.revisao_id,
                v.recurso_compartilhado_id,
                v.data_inicio_uso,
                v.data_fim_uso,
                v.ativo,
                v.peso_rateio,
                v.observacoes,
                v.created_at,
                v.updated_at,
                r.codigo_recurso,
                r.nome_recurso,
                r.categoria_recurso,
                r.fornecedor,
                r.tipo_custo,
                r.recorrencia,
                r.valor_total_recorrente,
                r.data_inicio_vigencia AS recurso_data_inicio_vigencia,
                r.data_fim_vigencia AS recurso_data_fim_vigencia,
                r.centro_custo,
                r.criterio_rateio,
                r.base_competencia,
                r.status_recurso,
                r.observacoes AS recurso_observacoes
            FROM transformometro.revisao_recursos_compartilhados v
            JOIN transformometro.recursos_compartilhados r
              ON r.recurso_compartilhado_id = v.recurso_compartilhado_id
    """

    def list_by_revisao(self, revisao_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            {self._VINCULO_SELECT}
            WHERE v.revisao_id = %s AND v.deletado = FALSE AND r.deletado = FALSE
            ORDER BY r.nome_recurso ASC
            """,
            (revisao_id,),
        )

    def list_by_recurso(self, recurso_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                v.vinculo_id,
                v.revisao_id,
                v.recurso_compartilhado_id,
                v.data_inicio_uso,
                v.data_fim_uso,
                v.ativo,
                v.peso_rateio,
                v.observacoes,
                v.created_at,
                v.updated_at,
                r.codigo_recurso,
                r.nome_recurso,
                r.categoria_recurso,
                r.fornecedor,
                r.tipo_custo,
                r.recorrencia,
                r.valor_total_recorrente,
                r.data_inicio_vigencia AS recurso_data_inicio_vigencia,
                r.data_fim_vigencia AS recurso_data_fim_vigencia,
                r.centro_custo,
                r.criterio_rateio,
                r.base_competencia,
                r.status_recurso,
                r.observacoes AS recurso_observacoes,
                rv.versao_revisao,
                rv.cenario_tipo,
                rv.revisao_ativa,
                rv.data_inicio_vigencia AS revisao_data_inicio_vigencia,
                rv.data_implantacao AS revisao_data_implantacao,
                rv.data_fim_vigencia AS revisao_data_fim_vigencia,
                p.processo_id,
                p.codigo_processo,
                p.nome_processo,
                f.codigo_filial AS filial_id,
                setores.nomes AS setor_id,
                p.status_processo,
                p.familia_processo,
                p.gestor_responsavel
            FROM transformometro.revisao_recursos_compartilhados v
            JOIN transformometro.recursos_compartilhados r
              ON r.recurso_compartilhado_id = v.recurso_compartilhado_id
             AND r.deletado = FALSE
            JOIN transformometro.revisoes rv
              ON rv.revisao_id = v.revisao_id
             AND rv.deletado = FALSE
            JOIN transformometro.processos p
              ON p.processo_id = rv.processo_id
             AND p.deletado = FALSE
            LEFT JOIN transformometro.processo_instancias pi
              ON pi.instancia_id = rv.instancia_id
             AND pi.deletado = FALSE
            LEFT JOIN transformometro.filiais f
              ON f.filial_id = pi.filial_id
            LEFT JOIN LATERAL (
                SELECT string_agg(s.nome_setor, ', ' ORDER BY s.nome_setor) AS nomes
                FROM transformometro.processo_instancia_setores pis
                JOIN transformometro.setores s ON s.setor_id = pis.setor_id
                WHERE pis.instancia_id = pi.instancia_id
            ) setores ON TRUE
            WHERE v.recurso_compartilhado_id = %s
              AND v.deletado = FALSE
            ORDER BY v.ativo DESC, p.codigo_processo ASC, rv.data_inicio_vigencia DESC
            """,
            (recurso_id,),
        )

    def get(self, vinculo_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            {self._VINCULO_SELECT}
            WHERE v.vinculo_id = %s AND v.deletado = FALSE AND r.deletado = FALSE
            """,
            (vinculo_id,),
        )

    def create(self, data: dict[str, Any], *, auto_commit: bool = True) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.revisao_recursos_compartilhados (
                revisao_id, recurso_compartilhado_id,
                data_inicio_uso, data_fim_uso, ativo, peso_rateio, observacoes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                data["revisao_id"],
                data["recurso_compartilhado_id"],
                data.get("data_inicio_uso"),
                data.get("data_fim_uso"),
                data.get("ativo", True),
                data.get("peso_rateio"),
                data.get("observacoes"),
            ),
            auto_commit=auto_commit,
        )
        if row is None:
            raise RuntimeError("Falha ao criar vínculo.")
        return self.get(str(row["vinculo_id"])) or row

    def update(self, vinculo_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.revisao_recursos_compartilhados SET
                data_inicio_uso = %s,
                data_fim_uso = %s,
                ativo = %s,
                peso_rateio = %s,
                observacoes = %s,
                updated_at = NOW()
            WHERE vinculo_id = %s AND deletado = FALSE
            RETURNING vinculo_id
            """,
            (
                data.get("data_inicio_uso"),
                data.get("data_fim_uso"),
                data.get("ativo", True),
                data.get("peso_rateio"),
                data.get("observacoes"),
                vinculo_id,
            ),
        )
        if row is None:
            return None
        return self.get(vinculo_id)

    def soft_delete(self, vinculo_id: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.revisao_recursos_compartilhados
            SET deletado = TRUE, updated_at = NOW()
            WHERE vinculo_id = %s AND deletado = FALSE
            RETURNING vinculo_id
            """,
            (vinculo_id,),
        )
        return row is not None
