"""Constantes compartilhadas da chave de ordem de produção Protheus."""

from app.domain.production.machine_load_scope import (
    MOTHER_ORDER_KEY_PREFIX_LENGTH as MACHINE_LOAD_PREFIX_LENGTH,
)
from app.domain.production.machine_load_scope import (
    MOTHER_ORDER_SEQUENCE as MACHINE_LOAD_MOTHER_SEQUENCE,
)
from app.domain.production.production_appointments.production_appointments_scope import (
    MOTHER_OP_SUFFIX,
)
from app.domain.totvs.protheus_production_orders import (
    MOTHER_ORDER_KEY_PREFIX_LENGTH,
    MOTHER_ORDER_SEQUENCE,
    ORDER_KEY_LENGTH,
    mother_order_key_sql,
)
from app.infrastructure.persistence.totvs.production_repositories.production_pa_sql_filters import (
    SC2_MOTHER_OP_SEQUENCE_SQL,
)


def test_order_key_has_eleven_positions() -> None:
    assert ORDER_KEY_LENGTH == 11
    assert MOTHER_ORDER_KEY_PREFIX_LENGTH == 8
    assert MOTHER_ORDER_SEQUENCE == "001"


def test_mother_order_key_sql_derives_sequence_001() -> None:
    assert mother_order_key_sql("OA.H8_OP") == "LEFT(OA.H8_OP, 8) + '001'"


def test_consumers_share_the_canonical_constant() -> None:
    assert MOTHER_OP_SUFFIX == MOTHER_ORDER_SEQUENCE
    assert MACHINE_LOAD_MOTHER_SEQUENCE == MOTHER_ORDER_SEQUENCE
    assert MACHINE_LOAD_PREFIX_LENGTH == MOTHER_ORDER_KEY_PREFIX_LENGTH
    assert f"'{MOTHER_ORDER_SEQUENCE}'" in SC2_MOTHER_OP_SEQUENCE_SQL
