from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tm_app.domain.raw_data import TransformometroRawData
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardDataRepository,
)


@dataclass(frozen=True)
class EntitySpec:
    bundle_key: str
    table: str
    pk: str
    columns: tuple[str, ...]
    fk_checks: tuple[tuple[str, str, str], ...] = ()


ENTITY_SPECS: tuple[EntitySpec, ...] = (
    EntitySpec(
        "setores",
        "transformometro.setores",
        "setor_id",
        (
            "setor_id",
            "nome_setor",
            "status_setor",
            "created_at",
            "updated_at",
            "deletado",
        ),
    ),
    EntitySpec(
        "processos",
        "transformometro.processos",
        "processo_id",
        (
            "processo_id",
            "codigo_processo",
            "nome_processo",
            "descricao_processo",
            "filial_id",
            "setor_id",
            "gestor_responsavel",
            "objetivo_processo",
            "status_processo",
            "familia_processo",
            "agrupador_ferramenta",
            "created_at",
            "updated_at",
            "deletado",
        ),
        (("setor_id", "setores", "setor_id"),),
    ),
    EntitySpec(
        "recursos_compartilhados",
        "transformometro.recursos_compartilhados",
        "recurso_compartilhado_id",
        (
            "recurso_compartilhado_id",
            "codigo_recurso",
            "nome_recurso",
            "categoria_recurso",
            "fornecedor",
            "tipo_custo",
            "recorrencia",
            "valor_total_recorrente",
            "data_inicio_vigencia",
            "data_fim_vigencia",
            "centro_custo",
            "criterio_rateio",
            "status_recurso",
            "observacoes",
            "base_competencia",
            "created_at",
            "updated_at",
            "deletado",
        ),
    ),
    EntitySpec(
        "revisoes",
        "transformometro.revisoes",
        "revisao_id",
        (
            "revisao_id",
            "processo_id",
            "versao_revisao",
            "chave_unica_processo_revisao",
            "descricao_revisao",
            "motivo_revisao",
            "cenario_tipo",
            "data_implantacao",
            "data_inicio_vigencia",
            "data_fim_vigencia",
            "revisao_ativa",
            "observacoes",
            "status_aprovacao",
            "aprovado_em",
            "aprovado_por_email",
            "motivo_rejeicao",
            "created_at",
            "updated_at",
            "deletado",
        ),
        (("processo_id", "processos", "processo_id"),),
    ),
    EntitySpec(
        "medicoes",
        "transformometro.medicoes",
        "medicao_id",
        (
            "medicao_id",
            "revisao_id",
            "volume_mensal",
            "tempo_medio_execucao_min",
            "tempo_retrabalho_min",
            "percentual_retrabalho",
            "percentual_erro",
            "quantidade_erros_mes",
            "custo_hora_mao_obra",
            "custo_unitario_erro",
            "custo_unitario_retrabalho",
            "custo_outros_desperdicios",
            "base_referencia_mes",
            "observacoes",
            "created_at",
            "updated_at",
            "deletado",
        ),
        (("revisao_id", "revisoes", "revisao_id"),),
    ),
    EntitySpec(
        "investimentos",
        "transformometro.investimentos",
        "investimento_id",
        (
            "investimento_id",
            "revisao_id",
            "tipo_investimento",
            "categoria_investimento",
            "descricao_item",
            "quantidade",
            "valor_unitario",
            "valor_total",
            "data_investimento",
            "recorrencia",
            "meses_vigencia",
            "centro_custo",
            "observacoes",
            "created_at",
            "updated_at",
            "deletado",
        ),
        (("revisao_id", "revisoes", "revisao_id"),),
    ),
    EntitySpec(
        "recurso_custos",
        "transformometro.recurso_custos",
        "recurso_custo_id",
        (
            "recurso_custo_id",
            "recurso_compartilhado_id",
            "valor_mensal",
            "data_inicio_vigencia",
            "data_fim_vigencia",
            "observacoes",
            "created_at",
            "updated_at",
            "deletado",
        ),
        (("recurso_compartilhado_id", "recursos_compartilhados", "recurso_compartilhado_id"),),
    ),
    EntitySpec(
        "revisao_recursos_compartilhados",
        "transformometro.revisao_recursos_compartilhados",
        "vinculo_id",
        (
            "vinculo_id",
            "revisao_id",
            "recurso_compartilhado_id",
            "data_inicio_uso",
            "data_fim_uso",
            "ativo",
            "peso_rateio",
            "observacoes",
            "created_at",
            "updated_at",
            "deletado",
        ),
        (
            ("revisao_id", "revisoes", "revisao_id"),
            ("recurso_compartilhado_id", "recursos_compartilhados", "recurso_compartilhado_id"),
        ),
    ),
)

SETOR_FILIAIS_BUNDLE_KEY = "setor_filiais"
BUNDLE_KEYS = (*tuple(spec.bundle_key for spec in ENTITY_SPECS), SETOR_FILIAIS_BUNDLE_KEY)


class JsonBackupRepository(PluginBaseRepository):
    def load_export_bundle(self) -> TransformometroRawData:
        return DashboardDataRepository(self._connection).load_raw()

    def fetch_setores(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM transformometro.setores
            WHERE deletado = FALSE
            ORDER BY nome_setor ASC
            """
        )

    def fetch_setor_filiais(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT setor_id, filial_id
            FROM transformometro.setor_filiais
            ORDER BY setor_id ASC, filial_id ASC
            """
        )

    def sync_setor_filiais(
        self,
        rows: list[dict[str, Any]],
        *,
        auto_commit: bool = False,
    ) -> None:
        self.execute("DELETE FROM transformometro.setor_filiais", auto_commit=False)
        for row in rows:
            if not isinstance(row, dict):
                continue
            setor_id = row.get("setor_id")
            filial_id = row.get("filial_id")
            if not setor_id or not filial_id:
                continue
            self.execute(
                """
                INSERT INTO transformometro.setor_filiais (setor_id, filial_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (setor_id, filial_id),
                auto_commit=False,
            )
        if auto_commit:
            self._connection.commit()

    def fetch_rows_by_ids(self, spec: EntitySpec, ids: set[str]) -> list[dict[str, Any]]:
        if not ids:
            return []
        return self.fetch_all(
            f"SELECT * FROM {spec.table} WHERE {spec.pk}::text = ANY(%s)",
            (list(ids),),
        )

    def ensure_bundle_parent_rows(
        self, data: dict[str, list[dict[str, Any]]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Inclui pais referenciados por FK mesmo se deletados (export só traz deletado=false)."""
        processos = list(data.get("processos") or [])
        processo_ids = {
            str(row.get("processo_id"))
            for row in processos
            if isinstance(row, dict) and row.get("processo_id")
        }
        needed_processos: set[str] = set()
        for row in data.get("revisoes") or []:
            if isinstance(row, dict) and row.get("processo_id"):
                needed_processos.add(str(row["processo_id"]))
        missing_processos = needed_processos - processo_ids
        if missing_processos:
            processos.extend(self.fetch_rows_by_ids(
                next(s for s in ENTITY_SPECS if s.bundle_key == "processos"),
                missing_processos,
            ))

        recursos = list(data.get("recursos_compartilhados") or [])
        recurso_ids = {
            str(row.get("recurso_compartilhado_id"))
            for row in recursos
            if isinstance(row, dict) and row.get("recurso_compartilhado_id")
        }
        needed_recursos: set[str] = set()
        for key in ("revisao_recursos_compartilhados", "recurso_custos"):
            for row in data.get(key) or []:
                if isinstance(row, dict) and row.get("recurso_compartilhado_id"):
                    needed_recursos.add(str(row["recurso_compartilhado_id"]))
        missing_recursos = needed_recursos - recurso_ids
        if missing_recursos:
            recursos.extend(self.fetch_rows_by_ids(
                next(s for s in ENTITY_SPECS if s.bundle_key == "recursos_compartilhados"),
                missing_recursos,
            ))

        revisoes = list(data.get("revisoes") or [])
        revisao_ids = {
            str(row.get("revisao_id"))
            for row in revisoes
            if isinstance(row, dict) and row.get("revisao_id")
        }
        needed_revisoes: set[str] = set()
        for key in ("medicoes", "investimentos", "revisao_recursos_compartilhados"):
            for row in data.get(key) or []:
                if isinstance(row, dict) and row.get("revisao_id"):
                    needed_revisoes.add(str(row["revisao_id"]))
        missing_revisoes = needed_revisoes - revisao_ids
        if missing_revisoes:
            revisoes.extend(self.fetch_rows_by_ids(
                next(s for s in ENTITY_SPECS if s.bundle_key == "revisoes"),
                missing_revisoes,
            ))

        setores = list(data.get("setores") or [])
        setor_ids = {
            str(row.get("setor_id"))
            for row in setores
            if isinstance(row, dict) and row.get("setor_id")
        }
        needed_setores: set[str] = set()
        for row in processos:
            if isinstance(row, dict) and row.get("setor_id"):
                needed_setores.add(str(row["setor_id"]))
        missing_setores = needed_setores - setor_ids
        if missing_setores:
            setores.extend(
                self.fetch_rows_by_ids(
                    next(s for s in ENTITY_SPECS if s.bundle_key == "setores"),
                    missing_setores,
                )
            )

        return {
            **data,
            "processos": processos,
            "recursos_compartilhados": recursos,
            "revisoes": revisoes,
            "setores": setores,
        }

    def fetch_existing_ids(self, spec: EntitySpec) -> set[str]:
        rows = self.fetch_all(
            f"SELECT {spec.pk}::text AS id FROM {spec.table} WHERE deletado = FALSE"
        )
        return {str(row["id"]) for row in rows}

    def truncate_cadastral_tables(self) -> None:
        self.execute(
            """
            TRUNCATE TABLE
                transformometro.dashboard_calculos,
                transformometro.revisao_recursos_compartilhados,
                transformometro.recurso_custos,
                transformometro.investimentos,
                transformometro.medicoes,
                transformometro.revisoes,
                transformometro.recursos_compartilhados,
                transformometro.processos,
                transformometro.setor_filiais,
                transformometro.setores
            RESTART IDENTITY CASCADE
            """,
            auto_commit=False,
        )

    def upsert_row(self, spec: EntitySpec, row: dict[str, Any], *, auto_commit: bool = False) -> None:
        values = {col: row.get(col) for col in spec.columns}
        if values.get("deletado") is None:
            values["deletado"] = False

        cols = list(values.keys())
        placeholders = ", ".join(["%s"] * len(cols))
        col_sql = ", ".join(cols)
        update_cols = [c for c in cols if c != spec.pk]
        update_sql = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

        self.execute(
            f"""
            INSERT INTO {spec.table} ({col_sql})
            VALUES ({placeholders})
            ON CONFLICT ({spec.pk}) DO UPDATE SET {update_sql}
            """,
            tuple(values[c] for c in cols),
            auto_commit=auto_commit,
        )

    def insert_row(self, spec: EntitySpec, row: dict[str, Any], *, auto_commit: bool = False) -> None:
        values = {col: row.get(col) for col in spec.columns}
        if values.get("deletado") is None:
            values["deletado"] = False
        cols = list(values.keys())
        placeholders = ", ".join(["%s"] * len(cols))
        col_sql = ", ".join(cols)
        self.execute(
            f"INSERT INTO {spec.table} ({col_sql}) VALUES ({placeholders})",
            tuple(values[c] for c in cols),
            auto_commit=auto_commit,
        )
