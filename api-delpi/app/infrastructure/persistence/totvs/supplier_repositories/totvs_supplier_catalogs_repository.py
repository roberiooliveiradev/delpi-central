"""Catálogos TOTVS de apoio ao cadastro de fornecedores (SA2) — read-only.

Allowlist fechada por catálogo; cada entrada aponta a fonte canônica
comprovada no dicionário SX3 (X3_F3/X3_CBOX) em DELPI_TST01:

- ``states``               → SX5 tabela '12'  (A2_EST)
- ``countries``            → SYA010           (A2_PAIS,   YA_CODGI)
- ``bacen-countries``      → CCH010           (A2_CODPAIS, CCH_CODIGO)
- ``payment-conditions``   → SE4010           (A2_COND,   E4_CODIGO)
- ``payment-methods``      → SX5 tabela '58'  (A2_FORMPAG, X5_CHAVE)
- ``financial-natures``    → SED010           (A2_NATUREZ, ED_CODIGO)
- ``accounting-accounts``  → CT1010           (A2_CONTA,  CT1_CONTA)
- ``municipalities``       → CC2010           (A2_COD_MUN, CC2_EST+CC2_CODMUN)

Todas as consultas são parametrizadas, limitadas e excluem registros
logicamente removidos (``D_E_L_E_T_ = ''``). Registros são compartilhados
entre filiais (filial em branco); SED também admite a filial '01' observada
no ambiente.
"""

from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository

SUPPLIER_CATALOG_KINDS: tuple[str, ...] = (
    "states",
    "countries",
    "bacen-countries",
    "payment-conditions",
    "payment-methods",
    "financial-natures",
    "accounting-accounts",
    "municipalities",
)

# Catálogo exige a UF corrente para filtrar (CC2_EST + CC2_CODMUN).
_STATE_DEPENDENT_CATALOGS = frozenset({"municipalities"})

_MAX_LIMIT = 500
_DEFAULT_LIMIT = 100
_CI_AI = "COLLATE Latin1_General_CI_AI"

_SOURCES: dict[str, dict[str, str]] = {
    "states": {
        "select": "X5_CHAVE AS code, RTRIM(X5_DESCRI) AS label, 0 AS disabled",
        "from": "SX5010",
        "where": "X5_TABELA = '12' AND X5_FILIAL = ''",
        "code_col": "X5_CHAVE",
        "label_col": "X5_DESCRI",
        "order": "X5_CHAVE",
    },
    "countries": {
        "select": "YA_CODGI AS code, RTRIM(YA_DESCR) AS label, 0 AS disabled",
        "from": "SYA010",
        "where": "YA_FILIAL = ''",
        "code_col": "YA_CODGI",
        "label_col": "YA_DESCR",
        "order": "YA_DESCR",
    },
    "bacen-countries": {
        "select": "CCH_CODIGO AS code, RTRIM(CCH_PAIS) AS label, 0 AS disabled",
        "from": "CCH010",
        "where": "CCH_FILIAL = ''",
        "code_col": "CCH_CODIGO",
        "label_col": "CCH_PAIS",
        "order": "CCH_PAIS",
    },
    "payment-conditions": {
        "select": (
            "RTRIM(E4_CODIGO) AS code, RTRIM(E4_DESCRI) AS label, "
            "CASE WHEN RTRIM(E4_MSBLQL) = '1' THEN 1 ELSE 0 END AS disabled"
        ),
        "from": "SE4010",
        "where": "E4_FILIAL = ''",
        "code_col": "E4_CODIGO",
        "label_col": "E4_DESCRI",
        "order": "E4_CODIGO",
    },
    "payment-methods": {
        "select": "X5_CHAVE AS code, RTRIM(X5_DESCRI) AS label, 0 AS disabled",
        "from": "SX5010",
        "where": "X5_TABELA = '58' AND X5_FILIAL = ''",
        "code_col": "X5_CHAVE",
        "label_col": "X5_DESCRI",
        "order": "X5_CHAVE",
    },
    "financial-natures": {
        "select": "RTRIM(ED_CODIGO) AS code, RTRIM(ED_DESCRIC) AS label, 0 AS disabled",
        "from": "SED010",
        "where": "ED_FILIAL IN ('', '01')",
        "code_col": "ED_CODIGO",
        "label_col": "ED_DESCRIC",
        "order": "ED_CODIGO",
    },
    "accounting-accounts": {
        "select": "RTRIM(CT1_CONTA) AS code, RTRIM(CT1_DESC01) AS label, 0 AS disabled",
        "from": "CT1010",
        "where": "CT1_FILIAL = ''",
        "code_col": "CT1_CONTA",
        "label_col": "CT1_DESC01",
        "order": "CT1_CONTA",
    },
    "municipalities": {
        "select": "CC2_CODMUN AS code, RTRIM(CC2_MUN) AS label, 0 AS disabled",
        "from": "CC2010",
        "where": "CC2_FILIAL = ''",
        "code_col": "CC2_CODMUN",
        "label_col": "CC2_MUN",
        "order": "CC2_MUN",
        "state_col": "CC2_EST",
    },
}


def catalog_requires_state(catalog: str) -> bool:
    return catalog in _STATE_DEPENDENT_CATALOGS


class TotvsSupplierCatalogsRepository(BaseRepository):
    """Consultas read-only aos catálogos SA2 (allowlist ``_SOURCES``)."""

    def list_catalog_items(
        self,
        catalog: str,
        *,
        query: str | None = None,
        state: str | None = None,
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

        state_col = source.get("state_col")
        if state_col is not None:
            uf = (state or "").strip().upper()
            where.append(f"{state_col} = ?")
            params.append(uf)

        q = (query or "").strip()
        if q:
            where.append(
                f"({source['code_col']} LIKE ? "
                f"OR {source['label_col']} {_CI_AI} LIKE ?)"
            )
            params.extend([f"{q}%", f"%{q}%"])

        sql = f"""
            SELECT TOP ({limit + 1})
                {source['select']}
            FROM {source['from']}
            WHERE {' AND '.join(where)}
            ORDER BY {source['order']}, {source['code_col']}
        """

        with self as repo:
            rows = repo.execute_query(sql, tuple(params))

        items = [
            {
                "code": (row.get("code") or "").rstrip(),
                "label": (row.get("label") or "").strip(),
                "disabled": bool(row.get("disabled")),
            }
            for row in rows[:limit]
            if (row.get("code") or "").strip()
        ]
        return items, len(rows) > limit
