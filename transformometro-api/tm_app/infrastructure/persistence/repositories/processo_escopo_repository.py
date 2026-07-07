from __future__ import annotations

import json
from typing import Any

from tm_app.domain.services.processo_escopo_service import (
    ProcessoEscopoDomainError,
    validate_processo_escopo,
)
from tm_app.domain.services.processo_instancia_service import validate_instancia_par
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from tm_app.infrastructure.persistence.repositories.filial_repository import FilialRepository
from tm_app.infrastructure.persistence.repositories.setor_repository import SetorRepository


class ProcessoEscopoRepository(PluginBaseRepository):
    @staticmethod
    def _normalize_refs(values: list[str] | None) -> list[str]:
        if not values:
            return []
        deduped: list[str] = []
        seen: set[str] = set()
        for raw in values:
            ref = str(raw or "").strip()
            if not ref:
                continue
            key = ref.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(ref)
        return deduped

    @staticmethod
    def _parse_json_list(value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, str):
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        return []

    def _load_todas_filiais(self, processo_id: str) -> bool:
        row = self.fetch_one(
            """
            SELECT todas_filiais_ativas
            FROM transformometro.processos
            WHERE processo_id = %s::uuid AND deletado = FALSE
            """,
            (processo_id,),
        )
        return bool((row or {}).get("todas_filiais_ativas"))

    def get_escopo(self, processo_id: str) -> dict[str, Any]:
        todas_filiais_ativas = self._load_todas_filiais(processo_id)
        filiais = self.fetch_all(
            """
            SELECT
                f.filial_id,
                f.codigo_filial,
                f.nome_filial
            FROM transformometro.processo_filiais pf
            JOIN transformometro.filiais f
                ON f.filial_id = pf.filial_id AND f.deletado = FALSE
            WHERE pf.processo_id = %s::uuid
            ORDER BY f.codigo_filial ASC
            """,
            (processo_id,),
        )
        setores = self.fetch_all(
            """
            SELECT
                s.setor_id,
                s.codigo_setor,
                s.nome_setor
            FROM transformometro.processo_setores ps
            JOIN transformometro.setores s
                ON s.setor_id = ps.setor_id AND s.deletado = FALSE
            WHERE ps.processo_id = %s::uuid
            ORDER BY s.codigo_setor ASC
            """,
            (processo_id,),
        )
        filial_ids = [str(row.get("codigo_filial") or "") for row in filiais if row.get("codigo_filial")]
        setor_ids = [str(row.get("codigo_setor") or "") for row in setores if row.get("codigo_setor")]
        return {
            "todas_filiais_ativas": todas_filiais_ativas,
            "filial_ids": filial_ids,
            "setor_ids": setor_ids,
            "filiais": filiais,
            "setores": setores,
        }

    def enrich_row(self, row: dict[str, Any]) -> dict[str, Any]:
        if not row or not row.get("processo_id"):
            return row
        escopo = self.get_escopo(str(row["processo_id"]))
        row.update(escopo)
        if escopo["filial_ids"]:
            row["filial_id"] = escopo["filial_ids"][0]
        else:
            row.pop("filial_id", None)
        if escopo["setor_ids"]:
            row["setor_id"] = escopo["setor_ids"][0]
        else:
            row.pop("setor_id", None)
        return row

    def _resolve_filiais(self, filial_refs: list[str]) -> list[dict[str, Any]]:
        filial_repo = FilialRepository(connection=self._connection)
        resolved: list[dict[str, Any]] = []
        for codigo in filial_refs:
            filial = filial_repo.get(codigo)
            if not filial:
                raise ProcessoEscopoDomainError(f"Unidade inválida: {codigo}.")
            resolved.append(filial)
        return resolved

    def _resolve_setores(
        self,
        setor_refs: list[str],
        *,
        filial_codigos: list[str],
        todas_filiais_ativas: bool,
    ) -> list[dict[str, Any]]:
        if not setor_refs:
            return []
        setor_repo = SetorRepository(connection=self._connection)
        resolved: list[dict[str, Any]] = []
        for setor_codigo in setor_refs:
            if not todas_filiais_ativas:
                if not filial_codigos:
                    raise ProcessoEscopoDomainError(
                        "Unidade obrigatória para validar departamentos."
                    )
                if not any(
                    setor_repo.is_active_for_filial(setor_codigo, filial_codigo)
                    for filial_codigo in filial_codigos
                ):
                    validate_instancia_par(
                        setor_ativo_na_filial=False,
                        filial_codigo=filial_codigos[0],
                        setor_codigo=setor_codigo,
                    )
            setor = setor_repo.get(setor_codigo)
            if not setor:
                raise ProcessoEscopoDomainError(f"Departamento inválido: {setor_codigo}.")
            resolved.append(setor)
        return resolved

    def save_escopo(
        self,
        processo_id: str,
        *,
        todas_filiais_ativas: bool,
        filial_ids: list[str] | None,
        setor_ids: list[str] | None,
        auto_commit: bool = True,
    ) -> dict[str, Any]:
        filial_refs = self._normalize_refs(filial_ids)
        setor_refs = self._normalize_refs(setor_ids)
        validate_processo_escopo(
            todas_filiais_ativas=todas_filiais_ativas,
            filial_ids=filial_refs,
            setor_ids=setor_refs,
        )

        if not filial_refs and not setor_refs and not todas_filiais_ativas:
            self.execute(
                """
                UPDATE transformometro.processos
                SET todas_filiais_ativas = FALSE, updated_at = NOW()
                WHERE processo_id = %s::uuid AND deletado = FALSE
                """,
                (processo_id,),
                auto_commit=False,
            )
            self.execute(
                "DELETE FROM transformometro.processo_filiais WHERE processo_id = %s::uuid",
                (processo_id,),
                auto_commit=False,
            )
            self.execute(
                "DELETE FROM transformometro.processo_setores WHERE processo_id = %s::uuid",
                (processo_id,),
                auto_commit=auto_commit,
            )
            return self.get_escopo(processo_id)

        filiais = [] if todas_filiais_ativas else self._resolve_filiais(filial_refs)
        setores = self._resolve_setores(
            setor_refs,
            filial_codigos=filial_refs,
            todas_filiais_ativas=todas_filiais_ativas,
        )

        self.execute(
            """
            UPDATE transformometro.processos
            SET todas_filiais_ativas = %s, updated_at = NOW()
            WHERE processo_id = %s::uuid AND deletado = FALSE
            """,
            (todas_filiais_ativas, processo_id),
            auto_commit=False,
        )
        self.execute(
            "DELETE FROM transformometro.processo_filiais WHERE processo_id = %s::uuid",
            (processo_id,),
            auto_commit=False,
        )
        self.execute(
            "DELETE FROM transformometro.processo_setores WHERE processo_id = %s::uuid",
            (processo_id,),
            auto_commit=False,
        )
        for filial in filiais:
            self.execute(
                """
                INSERT INTO transformometro.processo_filiais (processo_id, filial_id)
                VALUES (%s::uuid, %s::uuid)
                ON CONFLICT (processo_id, filial_id) DO NOTHING
                """,
                (processo_id, filial["filial_id"]),
                auto_commit=False,
            )
        for setor in setores:
            self.execute(
                """
                INSERT INTO transformometro.processo_setores (processo_id, setor_id)
                VALUES (%s::uuid, %s::uuid)
                ON CONFLICT (processo_id, setor_id) DO NOTHING
                """,
                (processo_id, setor["setor_id"]),
                auto_commit=False,
            )
        if auto_commit:
            self.commit()
        return self.get_escopo(processo_id)
