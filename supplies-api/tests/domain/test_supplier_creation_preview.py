"""Domain rules — supplier creation preview (X4.UX-R1.S1)."""

from __future__ import annotations

from app.domain.supplier_creation.preview import (
    DuplicateStatus,
    build_creation_suggestions,
    classify_duplicate,
    is_valid_cnpj,
    mask_tax_id,
)


class TestCnpjValidation:
    def test_valid_cnpjs_pass(self):
        assert is_valid_cnpj("00000000000191")
        assert is_valid_cnpj("11222333000181")
        assert is_valid_cnpj("60701190000104")

    def test_wrong_check_digits_rejected(self):
        assert not is_valid_cnpj("00000000000192")
        assert not is_valid_cnpj("12345678000196")

    def test_length_and_shape_rejected(self):
        assert not is_valid_cnpj("123")
        assert not is_valid_cnpj("")
        assert not is_valid_cnpj("1234567800019A")

    def test_repeated_digits_rejected(self):
        assert not is_valid_cnpj("11111111111111")


class TestMaskTaxId:
    def test_masks_middle_and_check_digits(self):
        assert mask_tax_id("12345678000196") == "12.***.***/0001-**"

    def test_non_cnpj_fully_masked(self):
        assert mask_tax_id("123") == "***"


class TestClassifyDuplicate:
    def test_zero_total_is_clear(self):
        assert classify_duplicate(0) is DuplicateStatus.CLEAR

    def test_positive_total_is_possible_match(self):
        assert classify_duplicate(2) is DuplicateStatus.POSSIBLE_MATCH

    def test_no_result_is_inconclusive_never_clear(self):
        assert classify_duplicate(None) is DuplicateStatus.INCONCLUSIVE


class TestBuildCreationSuggestions:
    def _fields(self):
        return {
            "company.tax_id": "12345678000196",
            "company.legal_name": "EMPRESA   EXEMPLO  LTDA",
            "company.trade_name": "EXEMPLO",
            "address.street": "RUA DAS FLORES, 100",
            "address.district": "CENTRO",
            "address.postal_code": "89.012-000",
            "address.state": "sc",
            "address.city": "BLUMENAU",
            "address.ibge_city_code": "00024",
            "contact.email": "compras@exemplo.com.br",
            "contact.phone": "(47) 99999-0000",
            "contact.area_code": "47",
            "company.registration_status": "ATIVA",
            "company.main_cnae": "4711302",
            "company.legal_nature": "206-2",
            "company.opening_date": "2010-01-15",
        }

    def test_suggests_mapped_comparable_fields(self):
        keys = {s.field_key for s in build_creation_suggestions(self._fields())}
        assert {
            "supplier_name",
            "supplier_short_name",
            "address",
            "district",
            "postal_code",
            "state",
            "city",
            "city_code",
        } <= keys

    def test_never_suggests_identity_or_protected(self):
        keys = {s.field_key for s in build_creation_suggestions(self._fields())}
        assert "tax_id" not in keys

    def test_contact_fields_never_suggested_even_when_present(self):
        keys = {s.field_key for s in build_creation_suggestions(self._fields())}
        assert "email" not in keys
        assert "phone" not in keys
        assert "area_code" not in keys

    def test_information_only_fields_not_suggested(self):
        keys = {s.field_key for s in build_creation_suggestions(self._fields())}
        assert "registration_status" not in keys
        assert "main_cnae" not in keys
        assert "legal_nature" not in keys
        assert "opening_date" not in keys

    def test_trade_name_marked_not_applicable(self):
        by_key = {
            s.field_key: s for s in build_creation_suggestions(self._fields())
        }
        assert by_key["supplier_short_name"].applicable is False
        assert by_key["supplier_name"].applicable is True

    def test_normalization_for_display(self):
        by_key = {
            s.field_key: s for s in build_creation_suggestions(self._fields())
        }
        assert by_key["supplier_name"].suggested_value == "EMPRESA EXEMPLO LTDA"
        assert by_key["postal_code"].suggested_value == "89012000"
        assert by_key["state"].suggested_value == "SC"

    def test_truncates_to_sa2_max_length(self):
        fields = {"company.legal_name": "X" * 80}
        by_key = {
            s.field_key: s for s in build_creation_suggestions(fields)
        }
        assert len(by_key["supplier_name"].suggested_value) == 50

    def test_missing_source_values_absent_not_emptied(self):
        fields = {"company.legal_name": "ACME", "address.district": None}
        keys = {s.field_key for s in build_creation_suggestions(fields)}
        assert "district" not in keys
        assert "supplier_name" in keys
