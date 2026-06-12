from __future__ import annotations

import re
from typing import Any

from maint_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository
from maint_app.application.list_query import ListQuery, build_order_clause

_CODIGO_PATTERN = re.compile(r"^[0-9]{2}$")


def normalize_codigo_filial(value: str) -> str:
    codigo = str(value).strip()
    if not _CODIGO_PATTERN.match(codigo):
        raise ValueError("Código da filial deve ter exatamente 2 dígitos numéricos.")
    return codigo


class FilialRepository(PluginBaseRepository):
    _LIST_QUERY = """
        SELECT
            filial_id,
            codigo_filial,
            nome_filial,
            status_filial,
            data_criacao,
            data_alteracao
        FROM maintenance.filiais
        WHERE excluido = FALSE
    """

    def list(self, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        rows, _total = self.list_paged(
            include_inactive=include_inactive,
            query=ListQuery(page=1, page_size=10_000, sort_by="codigo", sort_dir="asc"),
        )
        return rows

    def list_paged(
        self,
        *,
        include_inactive: bool,
        query: ListQuery,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        where = ["excluido = FALSE"]
        params: list[Any] = []
        if not include_inactive:
            where.append("status_filial = 'ativo'")
        if search and search.strip():
            where.append("(codigo_filial ILIKE %s OR nome_filial ILIKE %s)")
            term = f"%{search.strip()}%"
            params.extend([term, term])

        where_sql = " AND ".join(where)
        sort_columns = {
            "codigo": "codigo_filial",
            "nome": "nome_filial",
            "status": "status_filial",
        }
        order = build_order_clause(query.sort_by, query.sort_dir, sort_columns, "codigo")
        select_sql = f"""
            SELECT
                filial_id,
                codigo_filial,
                nome_filial,
                status_filial,
                data_criacao,
                data_alteracao
            FROM maintenance.filiais
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM maintenance.filiais
            WHERE {where_sql}
        """
        return self.fetch_paged(
            select_sql=select_sql,
            count_sql=count_sql,
            params=tuple(params),
            page=query.page,
            page_size=query.page_size,
        )

    def get(self, filial_ref: str) -> dict[str, Any] | None:
        ref = str(filial_ref).strip()
        if ref.isdigit() and len(ref) != 2:
            return self.fetch_one(
                f"{self._LIST_QUERY} AND filial_id = %s",
                (int(ref),),
            )
        codigo = normalize_codigo_filial(ref.zfill(2) if ref.isdigit() and len(ref) == 1 else ref)
        return self.fetch_one(
            f"{self._LIST_QUERY} AND codigo_filial = %s",
            (codigo,),
        )

    def list_active_codigos(self) -> set[str]:
        return {str(row["codigo_filial"]) for row in self.list(include_inactive=False)}

    def list_for_options(self) -> list[dict[str, Any]]:
        return [
            {
                "id": row["codigo_filial"],
                "label": row["nome_filial"],
                "filial_id": row["filial_id"],
                "codigo_filial": row["codigo_filial"],
                "status_filial": row["status_filial"],
            }
            for row in self.list(include_inactive=False)
        ]

    def count_operational_links(self, codigo_filial: str) -> int:
        codigo = normalize_codigo_filial(codigo_filial)
        row = self.fetch_one(
            """
            SELECT (
                (SELECT COUNT(*)::int FROM maintenance.reposicoes
                 WHERE filial = %s AND excluido = FALSE)
                +
                (SELECT COUNT(*)::int FROM maintenance.motivos
                 WHERE filial = %s AND excluido = FALSE)
                +
                (SELECT COUNT(*)::int FROM maintenance.status_peca
                 WHERE filial = %s AND excluido = FALSE)
            ) AS total
            """,
            (codigo, codigo, codigo),
        )
        return int((row or {}).get("total") or 0)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        codigo = normalize_codigo_filial(data["codigo_filial"])
        if self.get(codigo):
            raise ValueError(f"Filial com código '{codigo}' já existe.")

        status = str(data.get("status_filial", "ativo")).strip().lower()
        if status not in {"ativo", "inativo"}:
            raise ValueError("Status deve ser 'ativo' ou 'inativo'.")

        row = self.execute_returning_one(
            """
            INSERT INTO maintenance.filiais (codigo_filial, nome_filial, status_filial)
            VALUES (%s, %s, %s)
            RETURNING filial_id, codigo_filial, nome_filial, status_filial, data_criacao, data_alteracao
            """,
            (codigo, str(data["nome_filial"]).strip(), status),
        )
        if row is None:
            raise RuntimeError("Falha ao criar filial.")
        return row

    def update(self, filial_ref: str, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.get(filial_ref)
        if not existing:
            return None

        status = str(data.get("status_filial", existing["status_filial"])).strip().lower()
        if status not in {"ativo", "inativo"}:
            raise ValueError("Status deve ser 'ativo' ou 'inativo'.")

        return self.execute_returning_one(
            """
            UPDATE maintenance.filiais SET
                nome_filial = %s,
                status_filial = %s,
                data_alteracao = NOW()
            WHERE filial_id = %s AND excluido = FALSE
            RETURNING filial_id, codigo_filial, nome_filial, status_filial, data_criacao, data_alteracao
            """,
            (
                str(data["nome_filial"]).strip(),
                status,
                existing["filial_id"],
            ),
        )

    def soft_delete(self, filial_ref: str) -> bool:
        existing = self.get(filial_ref)
        if not existing:
            return False

        codigo = str(existing["codigo_filial"])
        if self.count_operational_links(codigo) > 0:
            raise ValueError(
                "Não é possível excluir filial com dados operacionais. "
                "Desative a filial ou remova motivos, status e reposições."
            )

        row = self.execute_returning_one(
            """
            UPDATE maintenance.filiais
            SET excluido = TRUE, data_alteracao = NOW()
            WHERE filial_id = %s AND excluido = FALSE
            RETURNING filial_id
            """,
            (existing["filial_id"],),
        )
        return row is not None
