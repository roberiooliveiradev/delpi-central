"""Catálogos TOTVS read-only para o cadastro de produtos da Engenharia (SB1).

Mesmo padrão governado de ``totvs_supplier_catalogs_repository``:
allowlist ``_SOURCES``, consultas parametrizadas, limitadas e excluindo
registros logicamente removidos (``D_E_L_E_T_ = ''``).

- ``product-groups``       → SBM010  (B1_GRUPO, BM_GRUPO + BM_DESC)
- ``units``                → SAH010  (B1_UM, AH_UNIMED + AH_DESCPO)
- ``warehouses``           → NNR010  (B1_LOCPAD, NNR_CODIGO + NNR_DESCRI)
- ``accounting-accounts``  → CT1010  (B1_CONTA, CT1_CONTA + CT1_DESC01)
"""

from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository

PRC_CATALOG_KINDS: tuple[str, ...] = (
    "product-groups",
    "units",
    "warehouses",
    "accounting-accounts",
)

_MAX_LIMIT = 500
_DEFAULT_LIMIT = 200
_CI_AI = "COLLATE Latin1_General_CI_AI"

_SOURCES: dict[str, dict[str, str]] = {
    "product-groups": {
        "select": "RTRIM(BM_GRUPO) AS code, RTRIM(BM_DESC) AS label, 0 AS disabled",
        "from": "SBM010",
        "where": "BM_FILIAL = ''",
        "code_col": "BM_GRUPO",
        "label_col": "BM_DESC",
        "order": "BM_GRUPO",
    },
    "units": {
        "select": "RTRIM(AH_UNIMED) AS code, RTRIM(AH_DESCPO) AS label, 0 AS disabled",
        "from": "SAH010",
        "where": "AH_FILIAL = ''",
        "code_col": "AH_UNIMED",
        "label_col": "AH_DESCPO",
        "order": "AH_UNIMED",
    },
    "warehouses": {
        "select": "RTRIM(NNR_CODIGO) AS code, RTRIM(NNR_DESCRI) AS label, 0 AS disabled",
        "from": "NNR010",
        "where": "NNR_FILIAL = ''",
        "code_col": "NNR_CODIGO",
        "label_col": "NNR_DESCRI",
        "order": "NNR_CODIGO",
    },
    "accounting-accounts": {
        "select": "RTRIM(CT1_CONTA) AS code, RTRIM(CT1_DESC01) AS label, 0 AS disabled",
        "from": "CT1010",
        "where": "CT1_FILIAL = ''",
        "code_col": "CT1_CONTA",
        "label_col": "CT1_DESC01",
        "order": "CT1_CONTA",
    },
}


class PrcCatalogsRepository(BaseRepository):
    """Consultas read-only aos catálogos SB1 (allowlist ``_SOURCES``)."""

    def list_catalog_items(
        self,
        catalog: str,
        *,
        query: str | None = None,
        limit: int = _DEFAULT_LIMIT,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Retorna ``(items, has_more)`` — busca por prefixo de código ou
        trecho da descrição, sempre limitada e parametrizada."""
        source = _SOURCES.get(catalog)
        if source is None:
            raise KeyError(catalog)

        limit = max(1, min(int(limit), _MAX_LIMIT))

        where = [f"{source['from']}.D_E_L_E_T_ = ''", source["where"]]
        params: list[Any] = []

        q = (query or "").strip()
        if q:
            where.append(
                f"({source['code_col']} LIKE ? "
                f"OR {source['label_col']} {_CI_AI} LIKE ?)"
            )
            params.extend([f"{q}%", f"%{q}%"])

        sql = (
            f"SELECT TOP {limit + 1} {source['select']} "
            f"FROM {source['from']} "
            f"WHERE {' AND '.join(where)} "
            f"ORDER BY {source['order']}"
        )
        with self as repo:
            rows = repo.execute_query(sql, tuple(params))
        has_more = len(rows) > limit
        items = rows[:limit]
        return items, has_more
