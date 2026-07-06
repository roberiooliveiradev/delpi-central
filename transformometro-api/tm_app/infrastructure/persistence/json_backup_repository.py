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
        "filiais",
        "transformometro.filiais",
        "filial_id",
        (
            "filial_id",
            "codigo_filial",
            "nome_filial",
            "status_filial",
            "created_at",
            "updated_at",
            "deletado",
        ),
    ),
    EntitySpec(
        "setores",
        "transformometro.setores",
        "setor_id",
        (
            "setor_id",
            "codigo_setor",
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
            "gestor_responsavel",
            "objetivo_processo",
            "status_processo",
            "familia_processo",
            "agrupador_ferramenta",
            "created_at",
            "updated_at",
            "deletado",
        ),
    ),
    EntitySpec(
        "processo_instancias",
        "transformometro.processo_instancias",
        "instancia_id",
        (
            "instancia_id",
            "processo_id",
            "filial_id",
            "todas_filiais_ativas",
            "rotulo_instancia",
            "status_instancia",
            "created_at",
            "updated_at",
            "deletado",
        ),
        (
            ("processo_id", "processos", "processo_id"),
            ("filial_id", "filiais", "filial_id"),
        ),
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
            "escopo_recurso",
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
            "instancia_id",
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
PROCESSO_INSTANCIA_SETORES_BUNDLE_KEY = "processo_instancia_setores"
PROCESSO_DIAGRAMAS_BUNDLE_KEY = "processo_diagramas"
INSTANCIA_DIAGRAMA_ESCOPOS_BUNDLE_KEY = "instancia_diagrama_escopos"
REVISAO_DIAGRAMA_OVERLAYS_BUNDLE_KEY = "revisao_diagrama_overlays"
BUNDLE_KEYS = (
    *tuple(spec.bundle_key for spec in ENTITY_SPECS),
    SETOR_FILIAIS_BUNDLE_KEY,
    PROCESSO_INSTANCIA_SETORES_BUNDLE_KEY,
    PROCESSO_DIAGRAMAS_BUNDLE_KEY,
    INSTANCIA_DIAGRAMA_ESCOPOS_BUNDLE_KEY,
    REVISAO_DIAGRAMA_OVERLAYS_BUNDLE_KEY,
)


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

    def fetch_filiais(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM transformometro.filiais
            WHERE deletado = FALSE
            ORDER BY codigo_filial ASC
            """
        )

    def fetch_processo_instancias(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                pi.instancia_id,
                pi.processo_id,
                pi.filial_id,
                pi.todas_filiais_ativas,
                pi.rotulo_instancia,
                pi.status_instancia,
                pi.created_at,
                pi.updated_at,
                pi.deletado
            FROM transformometro.processo_instancias pi
            WHERE pi.deletado = FALSE
            ORDER BY pi.processo_id ASC, pi.created_at ASC
            """
        )

    def fetch_processo_instancia_setores(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                pis.instancia_id,
                pis.setor_id,
                pis.created_at
            FROM transformometro.processo_instancia_setores pis
            JOIN transformometro.processo_instancias pi
                ON pi.instancia_id = pis.instancia_id
            WHERE pi.deletado = FALSE
            ORDER BY pis.instancia_id ASC, pis.setor_id ASC
            """
        )

    def fetch_processo_diagramas(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT processo_id, conteudo, mermaid_cached, created_at, updated_at
            FROM transformometro.processo_diagramas
            ORDER BY processo_id ASC
            """
        )

    def fetch_instancia_diagrama_escopos(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                instancia_id, node_ids, inherit_all, include_boundary_edges,
                created_at, updated_at
            FROM transformometro.instancia_diagrama_escopo
            ORDER BY instancia_id ASC
            """
        )

    def fetch_revisao_diagrama_overlays(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT revisao_id, conteudo, mermaid_cached, created_at, updated_at
            FROM transformometro.revisao_diagrama_overlays
            ORDER BY revisao_id ASC
            """
        )

    def sync_diagram_bundles(
        self,
        payload: dict[str, list[dict[str, Any]]],
        *,
        auto_commit: bool = False,
    ) -> None:
        from tm_app.infrastructure.persistence.repositories.instancia_diagram_escopo_repository import (
            InstanciaDiagramEscopoRepository,
        )
        from tm_app.infrastructure.persistence.repositories.processo_diagram_repository import (
            ProcessoDiagramRepository,
        )
        from tm_app.infrastructure.persistence.repositories.revisao_diagram_overlay_repository import (
            RevisaoDiagramOverlayRepository,
        )

        processo_repo = ProcessoDiagramRepository(connection=self._connection)
        instancia_repo = InstanciaDiagramEscopoRepository(connection=self._connection)
        revisao_repo = RevisaoDiagramOverlayRepository(connection=self._connection)

        for row in payload.get(PROCESSO_DIAGRAMAS_BUNDLE_KEY, []) or []:
            if isinstance(row, dict) and row.get("processo_id"):
                processo_repo.upsert_from_backup(row, auto_commit=False)

        for row in payload.get(INSTANCIA_DIAGRAMA_ESCOPOS_BUNDLE_KEY, []) or []:
            if isinstance(row, dict) and row.get("instancia_id"):
                instancia_repo.upsert_from_backup(row, auto_commit=False)

        for row in payload.get(REVISAO_DIAGRAMA_OVERLAYS_BUNDLE_KEY, []) or []:
            if isinstance(row, dict) and row.get("revisao_id"):
                revisao_repo.upsert_from_backup(row, auto_commit=False)

        if auto_commit:
            self._connection.commit()

    def fetch_setor_filiais(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                s.codigo_setor AS setor_id,
                f.codigo_filial AS filial_id
            FROM transformometro.setor_filiais sf
            JOIN transformometro.setores s ON s.setor_id = sf.setor_id
            JOIN transformometro.filiais f ON f.filial_id = sf.filial_id
            WHERE s.deletado = FALSE AND f.deletado = FALSE
            ORDER BY s.codigo_setor ASC, f.codigo_filial ASC
            """
        )

    def fetch_setores_by_codigos(self, codigos: set[str]) -> list[dict[str, Any]]:
        if not codigos:
            return []
        return self.fetch_all(
            """
            SELECT *
            FROM transformometro.setores
            WHERE codigo_setor = ANY(%s)
            """,
            (list(codigos),),
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
            setor_codigo = row.get("codigo_setor") or row.get("setor_id")
            filial_codigo = row.get("codigo_filial") or row.get("filial_id")
            if not setor_codigo or not filial_codigo:
                continue
            self.execute(
                """
                INSERT INTO transformometro.setor_filiais (setor_id, filial_id)
                SELECT s.setor_id, f.filial_id
                FROM transformometro.setores s
                JOIN transformometro.filiais f ON f.codigo_filial = %s
                WHERE s.codigo_setor = %s
                  AND s.deletado = FALSE
                  AND f.deletado = FALSE
                ON CONFLICT DO NOTHING
                """,
                (str(filial_codigo).strip(), str(setor_codigo).strip()),
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
        setor_codigos = {
            str(row.get("codigo_setor"))
            for row in setores
            if isinstance(row, dict) and row.get("codigo_setor")
        }
        for row in setores:
            if not isinstance(row, dict):
                continue
            sid = row.get("setor_id")
            if sid and len(str(sid)) != 36:
                setor_codigos.add(str(sid))
        needed_setores: set[str] = set()
        for row in processos:
            if isinstance(row, dict) and row.get("setor_id"):
                needed_setores.add(str(row["setor_id"]))
        missing_setores = needed_setores - setor_ids - setor_codigos
        if missing_setores:
            setores.extend(self.fetch_setores_by_codigos(missing_setores))

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
                transformometro.revisao_diagrama_overlays,
                transformometro.instancia_diagrama_escopo,
                transformometro.processo_diagramas,
                transformometro.revisao_recursos_compartilhados,
                transformometro.recurso_custos,
                transformometro.investimentos,
                transformometro.medicoes,
                transformometro.revisoes,
                transformometro.processo_instancia_setores,
                transformometro.processo_instancias,
                transformometro.recursos_compartilhados,
                transformometro.processos,
                transformometro.setor_filiais,
                transformometro.setores,
                transformometro.filiais
            RESTART IDENTITY CASCADE
            """,
            auto_commit=False,
        )

    def upsert_row(self, spec: EntitySpec, row: dict[str, Any], *, auto_commit: bool = False) -> None:
        values = {col: row[col] for col in spec.columns if col in row}
        if "deletado" not in values:
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
        values = {col: row[col] for col in spec.columns if col in row}
        if "deletado" not in values:
            values["deletado"] = False
        cols = list(values.keys())
        placeholders = ", ".join(["%s"] * len(cols))
        col_sql = ", ".join(cols)
        self.execute(
            f"INSERT INTO {spec.table} ({col_sql}) VALUES ({placeholders})",
            tuple(values[c] for c in cols),
            auto_commit=auto_commit,
        )
