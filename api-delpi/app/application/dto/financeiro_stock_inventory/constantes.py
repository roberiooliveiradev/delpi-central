"""Defaults for the R03/P7 stock-inventory snapshot query (SB9010/SB1010)."""

from __future__ import annotations

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50

REPORT_SCOPE_ALL_PRODUCTS = "all_products"
REPORT_SCOPE_MP_PI_PA = "mp_pi_pa"
REPORT_SCOPES = frozenset({REPORT_SCOPE_ALL_PRODUCTS, REPORT_SCOPE_MP_PI_PA})

# Product types (SB1 B1_TIPO) restricted by the mp_pi_pa view (doc 49 §2).
MP_PI_PA_PRODUCT_TYPES = ("MP", "PI", "PA")

# Operational query statuses (doc 49 §4 / §6.7). ``source_missing`` means the
# SB9 month-end snapshot has no rows for the requested branch(es);
# ``incomplete`` means only part of the expected branches have a snapshot;
# ``no_matching_items`` means the snapshot exists but filters matched no row.
STATUS_AVAILABLE = "available"
STATUS_INCOMPLETE = "incomplete"
STATUS_SOURCE_MISSING = "source_missing"
STATUS_NO_MATCHING_ITEMS = "no_matching_items"

# Paridade com a emissão oficial MATR460 (doc 119 §7): a composição do
# motor (EM ESTOQUE + EM PROCESSO) está provada estruturalmente para a
# competência 09/2026, mas a certificação por competência depende de uma
# emissão oficial comparável — até lá, ``PENDING``. ``TEST_NOT_RUN`` é
# reservado ao estado em que nenhum cálculo chegou a executar
# (``source_missing``).
PARITY_STATUS_PENDING = "PENDING"
PARITY_STATUS_TEST_NOT_RUN = "TEST_NOT_RUN"

PARITY_NOTE_ALL_PRODUCTS = (
    "Motor P7 com a composição oficial (SB9 + MATR989) comprovada para a "
    "competência 09/2026; paridade por competência pendente de homologação "
    "contra nova emissão MATR460."
)
PARITY_NOTE_MP_PI_PA = (
    "Recorte MP/PI/PA aplica somente o filtro canônico B1_TIPO; o mecanismo "
    "oficial de exclusão de saldo em poder de terceiros da emissão resumida "
    "permanece pendente de evidência (E2) e não é aplicado."
)
