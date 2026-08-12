"""Convenções Delpi — materiais de terceiros / beneficiamento (SB6).

Doc: api-delpi/docs/api/padroes-totvs/materiais-terceiros-sb6.md
"""

from __future__ import annotations

# SB6.B6_PODER3 — origem vs retorno (não confundir com B6_TPCF).
SB6_PODER3_REMESSA = "R"
SB6_PODER3_RETORNO = "D"

# SB6.B6_TIPO — material de terceiro em poder da empresa.
SB6_TIPO_TERCEIRO_NA_EMPRESA = "D"

# Relacionar remessa ↔ retornos só por filial + produto + identidade.
# Não usar B6_TPCF nem B6_IDENTB6 como chave.
SB6_SHIPMENT_KEY_FIELDS = ("B6_FILIAL", "B6_PRODUTO", "B6_IDENT")

# Status da remessa na view (PT) e na API (EN).
VIEW_SHIPMENT_STATUS_COMPLETED = "CONCLUIDO"
VIEW_SHIPMENT_STATUS_PARTIAL = "PARCIAL"
VIEW_SHIPMENT_STATUS_NO_RETURN = "SEM RETORNO"

API_SHIPMENT_STATUS_COMPLETED = "completed"
API_SHIPMENT_STATUS_PARTIAL = "partial"
API_SHIPMENT_STATUS_NO_RETURN = "no_return"

VIEW_TO_API_SHIPMENT_STATUS = {
    VIEW_SHIPMENT_STATUS_COMPLETED: API_SHIPMENT_STATUS_COMPLETED,
    VIEW_SHIPMENT_STATUS_PARTIAL: API_SHIPMENT_STATUS_PARTIAL,
    VIEW_SHIPMENT_STATUS_NO_RETURN: API_SHIPMENT_STATUS_NO_RETURN,
}

API_TO_VIEW_SHIPMENT_STATUS = {
    value: key for key, value in VIEW_TO_API_SHIPMENT_STATUS.items()
}

API_SHIPMENT_STATUS_VALUES = (
    API_SHIPMENT_STATUS_COMPLETED,
    API_SHIPMENT_STATUS_PARTIAL,
    API_SHIPMENT_STATUS_NO_RETURN,
)

# Tolerância de auditoria (float residual do Protheus).
CONTROL_DIFFERENCE_TOLERANCE = 0.000001

# Produto fictício de teste — ocultar por configuração, nunca na view.
DEFAULT_IGNORED_TEST_PRODUCTS = ("99999999",)

VIEW_NAME = "dbo.VW_PD3_BENEF_RETORNOS"
