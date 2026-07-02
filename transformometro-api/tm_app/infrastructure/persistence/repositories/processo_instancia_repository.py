from __future__ import annotations

import json
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
            pi.todas_filiais_ativas,
            f.codigo_filial,
            f.nome_filial,
            pi.rotulo_instancia,
            pi.status_instancia,
            pi.created_at,
            pi.updated_at,
            COALESCE(
                json_agg(
                    json_build_object(
                        'setor_id', s.setor_id,
                        'codigo_setor', s.codigo_setor,
                        'nome_setor', s.nome_setor
                    )
                    ORDER BY s.codigo_setor
                ) FILTER (WHERE s.setor_id IS NOT NULL),
                '[]'::json
            ) AS setores
        FROM transformometro.processo_instancias pi
        LEFT JOIN transformometro.filiais f
            ON f.filial_id = pi.filial_id AND f.deletado = FALSE
        LEFT JOIN transformometro.processo_instancia_setores pis
            ON pis.instancia_id = pi.instancia_id
        LEFT JOIN transformometro.setores s
            ON s.setor_id = pis.setor_id AND s.deletado = FALSE
        WHERE pi.deletado = FALSE
    """

    _GROUP_BY = """
        GROUP BY
            pi.instancia_id,
            pi.processo_id,
            pi.filial_id,
            pi.todas_filiais_ativas,
            f.codigo_filial,
            f.nome_filial,
            pi.rotulo_instancia,
            pi.status_instancia,
            pi.created_at,
            pi.updated_at
    """

    @staticmethod
    def _normalize_setor_refs(data: dict[str, Any]) -> list[str]:
        refs: list[str] = []
        raw_ids = data.get("setor_ids")
        if isinstance(raw_ids, list):
            refs.extend(str(item).strip() for item in raw_ids if str(item).strip())
        single = str(data.get("setor_id") or "").strip()
        if single:
            refs.append(single)
        deduped: list[str] = []
        seen: set[str] = set()
        for ref in refs:
            key = ref.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(ref)
        return deduped

    @staticmethod
    def _parse_setores(value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, str):
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        return []

    @classmethod
    def _enrich_row(cls, row: dict[str, Any]) -> dict[str, Any]:
        setores = cls._parse_setores(row.get("setores"))
        row["setores"] = setores
        if setores:
            first = setores[0]
            row["setor_id"] = first.get("setor_id")
            row["codigo_setor"] = first.get("codigo_setor")
            row["nome_setor"] = first.get("nome_setor")
        else:
            row.pop("setor_id", None)
            row.pop("codigo_setor", None)
            row.pop("nome_setor", None)
        row["setor_ids"] = [
            str(item.get("codigo_setor") or item.get("setor_id") or "")
            for item in setores
            if item.get("codigo_setor") or item.get("setor_id")
        ]
        return row

    def list_by_processo(self, processo_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            f"""
            {self._SELECT}
              AND pi.processo_id = %s::uuid
            {self._GROUP_BY}
            ORDER BY f.codigo_filial NULLS LAST, pi.created_at ASC
            """,
            (processo_id,),
        )
        return [self._enrich_row(row) for row in rows]

    def get(self, instancia_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"""
            {self._SELECT}
              AND pi.instancia_id = %s::uuid
            {self._GROUP_BY}
            """,
            (instancia_id,),
        )
        return self._enrich_row(row) if row else None

    def get_by_processo(self, processo_id: str) -> dict[str, Any] | None:
        rows = self.list_by_processo(processo_id)
        return rows[0] if rows else None

    def ensure_from_processo(self, processo_id: str) -> dict[str, Any]:
        existing = self.get_by_processo(processo_id)
        if existing:
            return existing

        raise ProcessoInstanciaDomainError(
            "Processo sem instância operacional. Cadastre uma instância em "
            "POST /processos/{id}/instancias."
        )

    def _resolve_filial(
        self,
        *,
        filial_codigo: str | None,
        todas_filiais_ativas: bool,
    ) -> dict[str, Any] | None:
        if todas_filiais_ativas:
            return None
        if not filial_codigo:
            raise ProcessoInstanciaDomainError(
                "Informe filial_id ou marque todas_filiais_ativas."
            )
        filial = FilialRepository(connection=self._connection).get(filial_codigo)
        if not filial:
            raise ProcessoInstanciaDomainError("Unidade inválida.")
        return filial

    def _resolve_setores(
        self,
        setor_refs: list[str],
        *,
        filial_codigo: str | None,
        todas_filiais_ativas: bool,
    ) -> list[dict[str, Any]]:
        if not setor_refs:
            raise ProcessoInstanciaDomainError("Informe ao menos um setor (setor_ids).")

        setor_repo = SetorRepository(connection=self._connection)
        resolved: list[dict[str, Any]] = []
        for setor_codigo in setor_refs:
            if not todas_filiais_ativas:
                if not filial_codigo:
                    raise ProcessoInstanciaDomainError("Unidade obrigatória para validar setores.")
                if not setor_repo.is_active_for_filial(setor_codigo, filial_codigo):
                    validate_instancia_par(
                        setor_ativo_na_filial=False,
                        filial_codigo=filial_codigo,
                        setor_codigo=setor_codigo,
                    )
            setor = setor_repo.get(setor_codigo)
            if not setor:
                raise ProcessoInstanciaDomainError(f"Setor inválido: {setor_codigo}.")
            resolved.append(setor)
        return resolved

    def _find_existing(
        self,
        *,
        processo_id: str,
        filial_uuid: str | None,
        todas_filiais_ativas: bool,
    ) -> dict[str, Any] | None:
        if todas_filiais_ativas:
            row = self.fetch_one(
                """
                SELECT instancia_id::text AS instancia_id
                FROM transformometro.processo_instancias
                WHERE processo_id = %s::uuid
                  AND todas_filiais_ativas = TRUE
                  AND deletado = FALSE
                """,
                (processo_id,),
            )
        else:
            row = self.fetch_one(
                """
                SELECT instancia_id::text AS instancia_id
                FROM transformometro.processo_instancias
                WHERE processo_id = %s::uuid
                  AND filial_id = %s::uuid
                  AND deletado = FALSE
                """,
                (processo_id, filial_uuid),
            )
        if not row:
            return None
        return self.get(str(row["instancia_id"]))

    def _attach_setores(
        self,
        instancia_id: str,
        setores: list[dict[str, Any]],
        *,
        auto_commit: bool,
    ) -> None:
        for setor in setores:
            self.execute_returning_one(
                """
                INSERT INTO transformometro.processo_instancia_setores (instancia_id, setor_id)
                VALUES (%s::uuid, %s::uuid)
                ON CONFLICT (instancia_id, setor_id) DO NOTHING
                RETURNING instancia_id
                """,
                (instancia_id, setor["setor_id"]),
                auto_commit=auto_commit,
            )

    def create(self, data: dict[str, Any], *, auto_commit: bool = True) -> dict[str, Any]:
        processo_id = str(data["processo_id"])
        todas_filiais_ativas = bool(data.get("todas_filiais_ativas"))
        filial_codigo = str(data.get("filial_id") or "").strip() or None
        setor_refs = self._normalize_setor_refs(data)

        if not ProcessoRepository(connection=self._connection).get(processo_id):
            raise ProcessoInstanciaDomainError("Processo não encontrado.")

        filial = self._resolve_filial(
            filial_codigo=filial_codigo,
            todas_filiais_ativas=todas_filiais_ativas,
        )
        setores = self._resolve_setores(
            setor_refs,
            filial_codigo=filial_codigo,
            todas_filiais_ativas=todas_filiais_ativas,
        )

        existing = self._find_existing(
            processo_id=processo_id,
            filial_uuid=str(filial["filial_id"]) if filial else None,
            todas_filiais_ativas=todas_filiais_ativas,
        )
        if existing:
            self._attach_setores(
                str(existing["instancia_id"]),
                setores,
                auto_commit=auto_commit,
            )
            if data.get("rotulo_instancia"):
                self.execute_returning_one(
                    """
                    UPDATE transformometro.processo_instancias
                    SET rotulo_instancia = %s,
                        updated_at = NOW()
                    WHERE instancia_id = %s::uuid
                    RETURNING instancia_id
                    """,
                    (data.get("rotulo_instancia"), existing["instancia_id"]),
                    auto_commit=auto_commit,
                )
            loaded = self.get(str(existing["instancia_id"]))
            if loaded is None:
                raise RuntimeError("Instância existente não pôde ser carregada.")
            return loaded

        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.processo_instancias (
                processo_id,
                filial_id,
                todas_filiais_ativas,
                rotulo_instancia,
                status_instancia
            )
            VALUES (%s::uuid, %s::uuid, %s, %s, %s)
            RETURNING instancia_id
            """,
            (
                processo_id,
                filial["filial_id"] if filial else None,
                todas_filiais_ativas,
                data.get("rotulo_instancia"),
                data.get("status_instancia", "ativo"),
            ),
            auto_commit=False,
        )
        if row is None:
            raise RuntimeError("Falha ao criar instância operacional.")

        instancia_id = str(row["instancia_id"])
        self._attach_setores(instancia_id, setores, auto_commit=False)

        if auto_commit:
            self._connection.commit()

        created = self.get(instancia_id)
        if created is None:
            raise RuntimeError("Falha ao carregar instância criada.")
        return created

    def count_revisoes(self, instancia_id: str) -> int:
        row = self.fetch_one(
            """
            SELECT COUNT(*)::int AS total
            FROM transformometro.revisoes
            WHERE instancia_id = %s::uuid
              AND deletado = FALSE
            """,
            (instancia_id,),
        )
        return int((row or {}).get("total") or 0)

    def _sync_setores(
        self,
        instancia_id: str,
        setores: list[dict[str, Any]],
        *,
        auto_commit: bool,
    ) -> None:
        keep_ids = {str(setor["setor_id"]) for setor in setores}
        if not keep_ids:
            raise ProcessoInstanciaDomainError("A instância deve manter ao menos um setor.")

        existing_rows = self.fetch_all(
            """
            SELECT setor_id::text AS setor_id
            FROM transformometro.processo_instancia_setores
            WHERE instancia_id = %s::uuid
            """,
            (instancia_id,),
        )
        existing_ids = {str(row["setor_id"]) for row in existing_rows}
        remove_ids = existing_ids - keep_ids
        if remove_ids:
            self.execute(
                """
                DELETE FROM transformometro.processo_instancia_setores
                WHERE instancia_id = %s::uuid
                  AND setor_id = ANY(%s::uuid[])
                """,
                (instancia_id, list(remove_ids)),
                auto_commit=auto_commit,
            )
        add_setores = [setor for setor in setores if str(setor["setor_id"]) not in existing_ids]
        if add_setores:
            self._attach_setores(instancia_id, add_setores, auto_commit=auto_commit)

    def update(self, instancia_id: str, data: dict[str, Any], *, auto_commit: bool = True) -> dict[str, Any]:
        existing = self.get(instancia_id)
        if not existing:
            raise ProcessoInstanciaDomainError("Instância não encontrada.")

        setor_refs = self._normalize_setor_refs(data)
        existing_todas = bool(existing.get("todas_filiais_ativas"))

        # Escopo alvo: usa o que veio no payload; sem chave, mantém o atual.
        if data.get("todas_filiais_ativas") is None:
            target_todas = existing_todas
        else:
            target_todas = bool(data.get("todas_filiais_ativas"))
        filial_atual = str(existing.get("codigo_filial") or existing.get("filial_id") or "").strip() or None
        target_filial_codigo = (
            None if target_todas else (str(data.get("filial_id") or "").strip() or filial_atual)
        )
        scope_changed = bool(data.get("scope_changed"))

        target_filial: dict[str, Any] | None = None
        if not target_todas:
            target_filial = self._resolve_filial(
                filial_codigo=target_filial_codigo,
                todas_filiais_ativas=False,
            )

        if scope_changed:
            conflito = self._find_existing(
                processo_id=str(existing["processo_id"]),
                filial_uuid=str(target_filial["filial_id"]) if target_filial else None,
                todas_filiais_ativas=target_todas,
            )
            if conflito and str(conflito["instancia_id"]) != str(instancia_id):
                raise ProcessoInstanciaDomainError(
                    "Já existe uma instância deste processo para o escopo de destino."
                )

        setores = self._resolve_setores(
            setor_refs,
            filial_codigo=target_filial_codigo,
            todas_filiais_ativas=target_todas,
        )

        self.execute_returning_one(
            """
            UPDATE transformometro.processo_instancias
            SET rotulo_instancia = %s,
                status_instancia = %s,
                todas_filiais_ativas = %s,
                filial_id = %s::uuid,
                updated_at = NOW()
            WHERE instancia_id = %s::uuid
              AND deletado = FALSE
            RETURNING instancia_id
            """,
            (
                data.get("rotulo_instancia"),
                data.get("status_instancia", existing.get("status_instancia") or "ativo"),
                target_todas,
                target_filial["filial_id"] if target_filial else None,
                instancia_id,
            ),
            auto_commit=False,
        )
        self._sync_setores(instancia_id, setores, auto_commit=False)

        if auto_commit:
            self._connection.commit()

        updated = self.get(instancia_id)
        if updated is None:
            raise RuntimeError("Falha ao carregar instância atualizada.")
        return updated

    def soft_delete(self, instancia_id: str, *, auto_commit: bool = True) -> bool:
        existing = self.get(instancia_id)
        if not existing:
            return False
        if self.count_revisoes(instancia_id) > 0:
            raise ProcessoInstanciaDomainError(
                "Não é possível excluir instância com revisões. Remova as revisões antes."
            )
        row = self.execute_returning_one(
            """
            UPDATE transformometro.processo_instancias
            SET deletado = TRUE,
                updated_at = NOW()
            WHERE instancia_id = %s::uuid
              AND deletado = FALSE
            RETURNING instancia_id
            """,
            (instancia_id,),
            auto_commit=auto_commit,
        )
        return row is not None
