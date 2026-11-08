"""Contrato interno — projeção MyWEG → Demanda (Etapa 1, sem HTTP público).

Não altera o contrato da carteira Protheus nem o payload de ``GET /demand``.
"""

from __future__ import annotations

from production_control_app.domain.myweg_needs_contract import ALLOWED_BRANCH

SOURCE_MYWEG = "myweg"
DISPLAY_ORDER_MYWEG = "MyWEG"

# Cliente Protheus WEG Linhares (filial DELPI 02).
WEG_LINHARES_CUSTOMER_CODE = "000001"
WEG_LINHARES_CUSTOMER_STORE = "09"
WEG_LINHARES_CUSTOMER_NAME = "WEG Linhares"

DEMAND_SOURCE_BRANCH = ALLOWED_BRANCH  # "02"

# matched_by da política prefer_production_over_sample quando só há amostra 8…
PROVISIONAL_SAMPLE_MATCHED_BY = frozenset(
    {
        "provisional_highest_sample_code_no_production",
        "provisional_sample_code_no_production",
    }
)

LINE_ID_PREFIX = "myweg"
