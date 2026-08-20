from __future__ import annotations

from production_control_app.domain.services.production_order_key import (
    ORDER_NUMBER_LENGTH,
    conjunto_key_from_order,
    order_belongs_to_conjunto,
)


def test_conjunto_key_is_c2_num_prefix() -> None:
    assert ORDER_NUMBER_LENGTH == 6
    assert conjunto_key_from_order("10840401003") == "108404"
    assert conjunto_key_from_order("10840402001") == "108404"
    assert conjunto_key_from_order("108404") == "108404"
    assert conjunto_key_from_order("10840") is None
    assert conjunto_key_from_order("") is None


def test_order_belongs_to_conjunto_by_prefix() -> None:
    assert order_belongs_to_conjunto("10840401003", "108404") is True
    assert order_belongs_to_conjunto("10840402001", "108404") is True
    assert order_belongs_to_conjunto("10840501001", "108404") is False
    assert order_belongs_to_conjunto("10840401003", "10840") is False
    assert order_belongs_to_conjunto("10840401003", "1084040") is False
