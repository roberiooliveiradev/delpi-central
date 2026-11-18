"""#852 — converte snapshot reconciliado do owner LNF em fonte de data do OTD.

Nunca conecta diretamente ao PostgreSQL de Controladoria. Com flag desligada,
a SQL original de VW_PONTUALIDADE_FORNECEDORES permanece 100% inalterada.
Com flag ligada, falha de transporte/snapshot NÃO vira falsamente "nota ausente".
"""
from __future__ import annotations

import json
import os
from app.application.services.supplies.physical_otd_gate import physical_receipts_enabled
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import requests

from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_DEFAULT_URL = "http://controllership-finance-api:8000"
_MAX_ROWS = 10000
# O schema operacional LNF nasceu em 2026; períodos anteriores usam ERP.
_LNF_MIN_DATE = "2026-01-01"


class PhysicalOtdSourceUnavailable(RuntimeError):
    """Alerta operacional: não é permitido ignorar uma falha do feed LNF."""


@dataclass(frozen=True)
class PhysicalOtdSource:
    cte: str
    params: tuple[str, str, str]

    def inject(self, query: str) -> str:
        return "WITH " + self.cte + "\n" + query


def _iso(value: str | None, *, default: str) -> str:
    if not value:
        return default
    normalized = QueryBuilder().convert_date_to_protheus(value)
    return datetime.strptime(normalized, "%Y%m%d").date().isoformat()


def _series(value: Any) -> str:
    data = str(value or "").strip().upper()
    if data.isdigit():
        return data.lstrip("0") or "0"
    return data


def _validate_rows(data: Any, *, branch: str | None) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or data.get("complete") is not True:
        raise PhysicalOtdSourceUnavailable("Snapshot LNF incompleto")
    raw = data.get("items")
    if not isinstance(raw, list) or len(raw) > _MAX_ROWS:
        raise PhysicalOtdSourceUnavailable("Snapshot LNF inválido ou truncado")
    seen: set[tuple[str, str, str, str, str]] = set()
    result = []
    for item in raw:
        if not isinstance(item, dict):
            raise PhysicalOtdSourceUnavailable("Linha LNF inválida")
        b = str(item.get("branch_code") or "").strip()
        supplier = str(item.get("supplier_code") or "").strip()
        store = str(item.get("supplier_store") or "").strip()
        document = str(item.get("document_match_key") or "").strip()
        series = _series(item.get("series"))
        try:
            received = date.fromisoformat(str(item["received_date"]))
            recno = int(item.get("sf1_recno") or 0)
        except (ValueError, TypeError, KeyError) as exc:
            raise PhysicalOtdSourceUnavailable("Data/chave LNF inválida") from exc
        if (
            b not in {"01", "02"} or (branch is not None and b != branch)
            or len(document) != 9 or not document.isdigit()
            or not supplier or not store or recno < 1
            or len(series) > 3
        ):
            raise PhysicalOtdSourceUnavailable("Identidade fiscal LNF inválida")
        key = (b, supplier, store, document, series)
        if key in seen:
            raise PhysicalOtdSourceUnavailable("Identidade fiscal LNF duplicada")
        seen.add(key)
        result.append({
            "branch_code": b,
            "supplier_code": supplier,
            "supplier_store": store,
            "document_match_key": document,
            "series": series,
            "sf1_recno": recno,
            "received_date": received.isoformat(),
        })
    return result


# A expressão de série replica series_match_key (0001 === 1), sem CAST
# que poderia igualar séries alfanuméricas indevidamente.
_D1_SERIES = """
    CASE WHEN LTRIM(RTRIM(D1.D1_SERIE)) <> ''
                   AND LTRIM(RTRIM(D1.D1_SERIE)) NOT LIKE '%[^0-9]%'
         THEN CONVERT(VARCHAR(10), TRY_CONVERT(INT, LTRIM(RTRIM(D1.D1_SERIE))))
         ELSE UPPER(LTRIM(RTRIM(ISNULL(D1.D1_SERIE, ''))))
    END
"""

# Espelha a DEFINIÇÃO REAL da dbo.VW_PONTUALIDADE_FORNECEDORES (auditada em
# 18/11/2026) e preserva o grão SD1×SC7. A view original não publica série.
# Recebimento de nota de beneficiamento (F1_TIPO=B, partido SA1) não é
# inferido pela identidade de SA2; nesses casos conserva-se a data ERP.
_PHYSICAL_CTE = """
LNF_RECEIPTS AS (
    SELECT branch_code, supplier_code, supplier_store,
           document_match_key, series, sf1_recno, received_date
      FROM OPENJSON(CAST(? AS NVARCHAR(MAX)))
      WITH (
         branch_code VARCHAR(2) '$.branch_code',
         supplier_code VARCHAR(6) '$.supplier_code',
         supplier_store VARCHAR(2) '$.supplier_store',
         document_match_key VARCHAR(9) '$.document_match_key',
         series VARCHAR(3) '$.series',
         sf1_recno INT '$.sf1_recno',
         received_date DATE '$.received_date'
      )
),
OTD_EFFECTIVE AS (
    SELECT
        SC7.C7_FILIAL AS FILIAL,
        D1.D1_FORNECE AS FORNECEDOR,
        D1.D1_LOJA AS LOJA,
        SA2.A2_NOME AS NOME_FORNECEDOR,
        D1.D1_DOC AS DOCUMENTO,
        SC7.C7_NUM AS NUMERO_PEDIDO,
        SC7.C7_ITEM AS ITEM_PEDIDO,
        SC7.C7_PRODUTO AS PRODUTO,
        SB1.B1_DESC AS DESCRICAO_PRODUTO,
        SB1.B1_TIPO AS TIPO_PRODUTO,
        SC7.C7_QUANT AS QUANTIDADE,
        CONVERT(date, SC7.C7_EMISSAO, 112) AS DT_EMISSAO_PC,
        CONVERT(date, SC7.C7_DATPRF, 112) AS DT_ENTREGA,
        CONVERT(date, D1.D1_DTDIGIT, 112) AS DT_DIGITACAO_ERP,
        COALESCE(LNF.received_date, CONVERT(date, D1.D1_DTDIGIT, 112))
            AS DT_DIGITACAO,
        CONVERT(date, D1.D1_EMISSAO, 112) AS DT_EMISSAO_NF,
        DATEDIFF(
            DAY,
            COALESCE(LNF.received_date, CONVERT(date, D1.D1_DTDIGIT, 112)),
            CONVERT(date, SC7.C7_DATPRF, 112)
        ) AS DIAS,
        CASE WHEN LNF.received_date IS NULL
             THEN 'erp_digitacao' ELSE 'lnf_fisico' END AS RECEIPT_SOURCE
    FROM SC7010 SC7 WITH (NOLOCK)
    INNER JOIN SD1010 D1 WITH (NOLOCK)
        ON D1.D1_FILIAL = SC7.C7_FILIAL
       AND D1.D1_PEDIDO = SC7.C7_NUM
       AND D1.D1_ITEMPC = SC7.C7_ITEM
       AND D1.D1_COD = SC7.C7_PRODUTO
       AND D1.D1_FORNECE = SC7.C7_FORNECE
       AND D1.D1_LOJA = SC7.C7_LOJA
       AND D1.D_E_L_E_T_ = ''
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC7.C7_PRODUTO AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = D1.D1_FORNECE
       AND SA2.A2_LOJA = D1.D1_LOJA
       AND SA2.D_E_L_E_T_ = ''
    LEFT JOIN LNF_RECEIPTS LNF
        ON LNF.branch_code = RTRIM(D1.D1_FILIAL)
       AND LNF.supplier_code = RTRIM(D1.D1_FORNECE)
       AND LNF.supplier_store = RTRIM(D1.D1_LOJA)
       AND LNF.document_match_key = RIGHT('000000000' + RTRIM(D1.D1_DOC), 9)
       AND LNF.series = """ + _D1_SERIES + """
       AND RTRIM(D1.D1_DOC) <> ''
       AND RTRIM(D1.D1_DOC) NOT LIKE '%[^0-9]%'
    WHERE SC7.D_E_L_E_T_ = ''
      AND (SB1.B1_TIPO = 'MP' OR SC7.C7_PRODUTO LIKE '3019%')
      AND (
          D1.D1_DTDIGIT BETWEEN ? AND ?
          OR LNF.received_date IS NOT NULL
      )
)
"""


def build_physical_source(
    rows: list[dict[str, Any]], *, start_date: str | None, end_date: str | None
) -> PhysicalOtdSource:
    start = _iso(start_date, default="1900-01-01")
    end = _iso(end_date, default="9999-12-31")
    # Não renderizar JSON como SQL literal. Payload sempre vinculado por ODBC.
    return PhysicalOtdSource(
        cte=_PHYSICAL_CTE,
        params=(json.dumps(rows, ensure_ascii=True, separators=(",", ":")),
                start.replace("-", ""), end.replace("-", "")),
    )


def resolve_physical_source(
    repository: Any, *, branch: str | None,
    start_date: str | None, end_date: str | None,
) -> PhysicalOtdSource | None:
    if not physical_receipts_enabled():
        return None
    key = (branch, start_date, end_date)
    if getattr(repository, "_physical_otd_source_key", None) == key:
        return repository._physical_otd_source_value
    token = (os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN") or "").strip()
    if not token:
        raise PhysicalOtdSourceUnavailable("Token de integração LNF não configurado")
    # Buscar as duas origens temporais para incluir viradas de mês. Na consulta
    # efetiva o período é novamente filtrado APÓS a substituição da data.
    physical_start = max(
        _iso(start_date, default=_LNF_MIN_DATE), _LNF_MIN_DATE
    )
    physical_end = _iso(end_date, default=date.today().isoformat())
    if physical_end < physical_start:
        # Período anterior à existência do LNF, ou janela futura ainda vazia.
        # O SQL continua apurando o universo fiscal, sem chamadas desnecessárias.
        source = build_physical_source(
            [], start_date=start_date, end_date=end_date
        )
        repository._physical_otd_source_key = key
        repository._physical_otd_source_value = source
        return source
    params = {
        "start_date": physical_start,
        "end_date": physical_end,
    }
    if branch:
        params["branch"] = branch
    url = (os.getenv("OTD_LNF_BASE_URL") or _DEFAULT_URL).rstrip("/")
    try:
        response = requests.get(
            url + "/internal/otd-receipts",
            params=params,
            headers={"X-Delpi-Service-Token": token},
            timeout=(3, 15),
        )
        response.raise_for_status()
        rows = _validate_rows(response.json(), branch=branch)
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise PhysicalOtdSourceUnavailable("Feed de recebimento LNF indisponível") from exc
    source = build_physical_source(rows, start_date=start_date, end_date=end_date)
    repository._physical_otd_source_key = key
    repository._physical_otd_source_value = source
    return source
