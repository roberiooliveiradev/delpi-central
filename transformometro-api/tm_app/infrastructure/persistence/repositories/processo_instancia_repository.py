from __future__ import annotations

from typing import Any

from tm_app.domain.services.processo_instancia_service import (
    ProcessoInstanciaDomainError,
    validate_instancia_par,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from tm_app.infrastructure.persistence.repositories.filial_repository import FilialRepository
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository
from tm_app.infrastructure.persistence.repositories.setor_repository import SetorRepository


class ProcessoInstanciaRepository(PluginBaseRepository):
    _SELECT = """
        SELECT
            pi.instancia_id,
            pi.processo_id,
            pi.filial_id,
            f.codigo_filial,
            f.nome_filial,
            pi.setor_id,
            s.codigo_setor,
            s.nome_setor,
            pi.rotulo_instancia,
            pi.status_instancia,
            pi.created_at,
            pi.updated_at
        FROM transformometro.processo_instancias pi
        JOIN transformometro.filiais f ON f.filial_id = pi.filial_id
        JOIN transformometro.setores s ON s.setor_id = pi.setor_id
        WHERE pi.deletado = FALSE
          AND f.deletado = FALSE
          AND s.deletado = FALSE
    """

    def list_by_processo(self, processo_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"{self._SELECT} AND pi.processo_id = %s::uuid ORDER BY f.codigo_filial, s.codigo_setor",
            (processo_id,),
        )

    def get(self, instancia_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"{self._SELECT} AND pi.instancia_id = %s::uuid",
            (instancia_id,),
        )

    def get_by_processo(self, processo_id: str) -> dict[str, Any] | None:
        rows = self.list_by_processo(processo_id)
        return rows[0] if rows else None

    def ensure_from_processo(self, processo_id: str) -> dict[str, Any]:
        existing = self.get_by_processo(processo_id)
        if existing:
            return existing

        processo = ProcessoRepository(connection=self._connection).get(processo_id)
        if not processo:
            raise ProcessoInstanciaDomainError("Processo não encontrado.")

        filial_codigo = str(processo["filial_id"])
        setor_codigo = str(processo["setor_id"])
        if not SetorRepository(connection=self._connection).is_active_for_filial(
            setor_codigo, filial_codigo
        ):
            validate_instancia_par(
                setor_ativo_na_filial=False,
                filial_codigo=filial_codigo,
                setor_codigo=setor_codigo,
            )

        filial = FilialRepository(connection=self._connection).get(filial_codigo)
        setor = SetorRepository(connection=self._connection).get(setor_codigo)
        if not filial or not setor:
            raise ProcessoInstanciaDomainError("Filial ou setor do processo não encontrado no catálogo.")

        return self.create(
            {
                "processo_id": processo_id,
                "filial_id": filial_codigo,
                "setor_id": setor_codigo,
            }
        )

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        processo_id = str(data["processo_id"])
        filial_codigo = str(data["filial_id"])
        setor_codigo = str(data["setor_id"])

        if not ProcessoRepository(connection=self._connection).get(processo_id):
            raise ProcessoInstanciaDomainError("Processo não encontrado.")

        if not SetorRepository(connection=self._connection).is_active_for_filial(
            setor_codigo, filial_codigo
        ):
            validate_instancia_par(
                setor_ativo_na_filial=False,
                filial_codigo=filial_codigo,
                setor_codigo=setor_codigo,
            )

        filial = FilialRepository(connection=self._connection).get(filial_codigo)
        setor = SetorRepository(connection=self._connection).get(setor_codigo)
        if not filial or not setor:
            raise ProcessoInstanciaDomainError("Filial ou setor inválido.")

        existing = self.fetch_one(
            """
            SELECT instancia_id::text AS instancia_id
            FROM transformometro.processo_instancias
            WHERE processo_id = %s::uuid
              AND filial_id = %s::uuid
              AND setor_id = %s::uuid
              AND deletado = FALSE
            """,
            (processo_id, filial["filial_id"], setor["setor_id"]),
        )
        if existing:
            row = self.get(str(existing["instancia_id"]))
            if row is None:
                raise RuntimeError("Instância existente não pôde ser carregada.")
            return row

        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.processo_instancias (
                processo_id, filial_id, setor_id, rotulo_instancia, status_instancia
            )
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s)
            RETURNING instancia_id
            """,
            (
                processo_id,
                filial["filial_id"],
                setor["setor_id"],
                data.get("rotulo_instancia"),
                data.get("status_instancia", "ativo"),
            ),
            auto_commit=True,
        )
        if row is None:
            raise RuntimeError("Falha ao criar instância operacional.")
        created = self.get(str(row["instancia_id"]))
        if created is None:
            raise RuntimeError("Falha ao carregar instância criada.")
        return created
