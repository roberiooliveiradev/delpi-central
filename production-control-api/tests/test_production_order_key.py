from __future__ import annotations

from production_control_app.domain.services.production_order_key import (
    ORDER_NUMBER_LENGTH,
    PACKAGE_KEY_LENGTH,
    conjunto_key_from_order,
    order_belongs_to_conjunto,
    order_belongs_to_package,
    package_key_from_order,
)


def test_conjunto_key_is_c2_num_prefix() -> None:
    assert ORDER_NUMBER_LENGTH == 6
    assert conjunto_key_from_order("10840401003") == "108404"
    assert conjunto_key_from_order("10840402001") == "108404"
    assert conjunto_key_from_order("108404") == "108404"
    assert conjunto_key_from_order("10840") is None
    assert conjunto_key_from_order("") is None


def test_package_key_is_num_plus_item() -> None:
    assert PACKAGE_KEY_LENGTH == 8
    assert package_key_from_order("10840401003") == "10840401"
    assert package_key_from_order("10840401002") == "10840401"
    assert package_key_from_order("10840402001") == "10840402"
    assert package_key_from_order("10840401") == "10840401"
    assert package_key_from_order("1084040") is None


def test_order_belongs_to_conjunto_by_prefix() -> None:
    assert order_belongs_to_conjunto("10840401003", "108404") is True
    assert order_belongs_to_conjunto("10840402001", "108404") is True
    assert order_belongs_to_conjunto("10840501001", "108404") is False
    assert order_belongs_to_conjunto("10840401003", "10840") is False
    assert order_belongs_to_conjunto("10840401003", "1084040") is False


def test_order_belongs_to_package_excludes_other_item() -> None:
    assert order_belongs_to_package("10840401001", "10840401") is True
    assert order_belongs_to_package("10840401002", "10840401") is True
    assert order_belongs_to_package("10840402001", "10840401") is False
    assert order_belongs_to_package("10840401001", "108404") is False
