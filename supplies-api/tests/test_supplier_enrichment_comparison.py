"""S1 unit tests — supplier enrichment comparison engine.

All fixtures are synthetic. No real CNPJ/CPF, no network, no Protheus.
"""

from __future__ import annotations

import pytest

from app.domain.exceptions import (
    EnrichmentIdentityMismatchError,
    EnrichmentUnsupportedDocumentError,
)
from app.domain.supplier_enrichment import (
    CNPJ_SA2_MAPPING_V1,
    ComparisonState,
    EligibilityState,
    FieldDecisionState,
)
from app.domain.supplier_enrichment.comparison import compare_supplier_snapshots
from app.domain.supplier_enrichment.models import (
    CanonicalSupplierSnapshot,
    ExternalRegistrySnapshot,
    SupplierRef,
)

# Synthetic test-only values — not real registry data.
TAX_ID = "11222333000144"
OTHER_TAX_ID = "99888777000155"

BASE_EXTERNAL_FIELDS = {
    "company.tax_id": TAX_ID,
    "company.legal_name": "ACME BRASIL LTDA",
    "company.trade_name": "ACME",
    "company.registration_status": "ATIVA",
    "company.main_cnae": "2511-0/00",
    "company.legal_nature": "206-2",
    "company.opening_date": "2001-03-15",
    "address.street": "RUA DAS FLORES, 100",
    "address.district": "CENTRO",
    "address.postal_code": "89010000",
    "address.city": "BLUMENAU",
    "address.state": "SC",
    "address.ibge_city_code": "4202404",
    "contact.area_code": "47",
    "contact.phone": "33221100",
    "contact.email": "contato@acme.example",
}

BASE_CANONICAL_FIELDS = {
    "supplier_name": "ACME BRASIL LTDA",
    "supplier_short_name": "ACME",
    "address": "RUA DAS FLORES, 100",
    "district": "CENTRO",
    "postal_code": "89010000",
    "city": "BLUMENAU",
    "state": "SC",
    "city_code": "02404",
    "area_code": "47",
    "phone": "4733221100",
    "email": "contato@acme.example",
    "registration_status": "ATIVA",
    "main_cnae": "2511-0/00",
    "legal_nature": "206-2",
    "opening_date": "2001-03-15",
}

# Sentinel — simulate an external payload where the key is absent (vs empty).
ABSENT = object()


def canonical(**overrides) -> CanonicalSupplierSnapshot:
    fields = dict(BASE_CANONICAL_FIELDS)
    fields.update(overrides.pop("fields", {}))
    return CanonicalSupplierSnapshot(
        supplier=overrides.pop("supplier", SupplierRef(code="003878", store="01")),
        tax_id=overrides.pop("tax_id", TAX_ID),
        person_type=overrides.pop("person_type", "J"),
        fields=fields,
        baseline_reference=overrides.pop("baseline_reference", None),
    )


def external(**overrides) -> ExternalRegistrySnapshot:
    fields = dict(BASE_EXTERNAL_FIELDS)
    for key, value in overrides.pop("fields", {}).items():
        if value is ABSENT:
            fields.pop(key, None)
        else:
            fields[key] = value
    return ExternalRegistrySnapshot(
        tax_id=overrides.pop("tax_id", TAX_ID),
        source_id=overrides.pop("source_id", "synthetic-registry"),
        retrieved_at=overrides.pop("retrieved_at", "2026-10-21T12:00:00Z"),
        fields=fields,
        source_reference=overrides.pop("source_reference", "req-synthetic-1"),
    )


def proposal_for(review, field_key):
    for proposal in review.comparison.proposals:
        if proposal.field_key == field_key:
            return proposal
    raise AssertionError(f"no proposal for {field_key}")


CC2_INDEX = {("SC", "blumenau"): "02404"}


class TestIdentity:
    def test_case_e_foreign_cnpj_blocks_comparison(self):
        with pytest.raises(EnrichmentIdentityMismatchError):
            compare_supplier_snapshots(
                canonical(), external(tax_id=OTHER_TAX_ID)
            )

    def test_case_f_cpf_supplier_not_supported(self):
        with pytest.raises(EnrichmentUnsupportedDocumentError):
            compare_supplier_snapshots(
                canonical(person_type="F", tax_id="12345678901"),
                external(tax_id="12345678901"),
            )

    def test_non_j_person_type_not_supported(self):
        with pytest.raises(EnrichmentUnsupportedDocumentError):
            compare_supplier_snapshots(canonical(person_type="X"), external())

    def test_external_non_cnpj_document_mismatch(self):
        with pytest.raises(EnrichmentIdentityMismatchError):
            compare_supplier_snapshots(
                canonical(), external(tax_id="12345678901")
            )

    def test_supplier_ref_normalized_and_validated(self):
        assert SupplierRef(code="3878", store="1").code == "003878"
        assert SupplierRef(code="3878", store="1").store == "01"
        with pytest.raises(ValueError):
            SupplierRef(code="1234567", store="01")
        with pytest.raises(ValueError):
            SupplierRef(code="", store="01")


class TestComparisonStates:
    def test_case_a_all_equal_gives_match(self):
        review = compare_supplier_snapshots(canonical(), external())
        name = proposal_for(review, "supplier_name")
        assert name.comparison is ComparisonState.MATCH
        assert name.eligibility is EligibilityState.NOT_APPLICABLE
        assert review.comparison.summary["eligible_to_apply"] == 0

    def test_case_b_name_difference_is_eligible(self):
        ext = external(fields={"company.legal_name": "ACME BRASIL INDUSTRIA LTDA"})
        review = compare_supplier_snapshots(canonical(), ext)
        name = proposal_for(review, "supplier_name")
        assert name.comparison is ComparisonState.DIFFERENT
        assert name.eligibility is EligibilityState.ELIGIBLE_TO_APPLY
        assert name.suggested_value == "ACME BRASIL INDUSTRIA LTDA"
        assert name.current_value == "ACME BRASIL LTDA"

    def test_case_c_source_missing_never_clears_current(self):
        ext = external(
            fields={"address.street": ABSENT, "address.district": ""}
        )
        review = compare_supplier_snapshots(canonical(), ext)
        street = proposal_for(review, "address")
        district = proposal_for(review, "district")
        assert street.comparison is ComparisonState.SOURCE_MISSING
        assert street.eligibility_reason == "source_field_absent"
        assert street.eligibility is EligibilityState.NOT_APPLICABLE
        assert street.suggested_value is None
        assert street.current_value == "RUA DAS FLORES, 100"
        assert district.eligibility_reason == "source_field_empty"

    def test_case_d_current_missing_is_fillable(self):
        can = canonical(fields={"district": None})
        review = compare_supplier_snapshots(can, external())
        district = proposal_for(review, "district")
        assert district.comparison is ComparisonState.CURRENT_MISSING
        assert district.eligibility is EligibilityState.ELIGIBLE_TO_APPLY
        assert district.suggested_value == "CENTRO"

    def test_case_g_oversized_name_not_eligible(self):
        ext = external(fields={"company.legal_name": "A" * 51})
        review = compare_supplier_snapshots(canonical(), ext)
        name = proposal_for(review, "supplier_name")
        assert name.comparison is ComparisonState.DIFFERENT
        assert name.eligibility is EligibilityState.PENDING_VALIDATION
        assert name.eligibility_reason == "exceeds_sa2_limit"
        assert name.suggested_value == "A" * 51  # never truncated silently

    def test_case_i_tax_id_is_protected(self):
        ext = external(fields={"company.tax_id": TAX_ID})
        review = compare_supplier_snapshots(canonical(), ext)
        tax = proposal_for(review, "tax_id")
        assert tax.comparison is ComparisonState.PROTECTED
        assert tax.eligibility is EligibilityState.PROTECTED
        assert tax.suggested_value is None


class TestMunicipalityGroup:
    def test_case_h_unconciliated_municipality_pending(self):
        can = canonical(fields={"city": "TIMBO", "city_code": "08202", "state": "SC"})
        review = compare_supplier_snapshots(
            can, external(), municipality_index=CC2_INDEX
        )
        city = proposal_for(review, "city")
        city_code = proposal_for(review, "city_code")
        # External BLUMENAU conciliates to canonical code 02404.
        assert city.comparison is ComparisonState.DIFFERENT
        assert city.eligibility is EligibilityState.ELIGIBLE_TO_APPLY
        assert city_code.eligibility is EligibilityState.ELIGIBLE_TO_APPLY
        assert city_code.suggested_value == "02404"

    def test_municipality_without_index_is_pending(self):
        can = canonical(fields={"city": "TIMBO", "city_code": "08202", "state": "SC"})
        review = compare_supplier_snapshots(can, external())
        for key in ("state", "city", "city_code"):
            prop = proposal_for(review, key)
            if prop.comparison in (
                ComparisonState.DIFFERENT,
                ComparisonState.CURRENT_MISSING,
            ):
                assert prop.eligibility is EligibilityState.PENDING_VALIDATION
                assert prop.eligibility_reason in (
                    "municipality_reconciliation_unavailable",
                    "municipality_not_conciliated",
                )

    def test_municipality_not_in_index_is_pending(self):
        can = canonical(fields={"city": "TIMBO", "city_code": "08202", "state": "SC"})
        review = compare_supplier_snapshots(
            can, external(), municipality_index={("SP", "sao paulo"): "07108"}
        )
        city = proposal_for(review, "city")
        assert city.eligibility is EligibilityState.PENDING_VALIDATION
        assert city.eligibility_reason == "municipality_not_conciliated"

    def test_municipality_source_incomplete_is_pending(self):
        can = canonical(fields={"city": "TIMBO", "city_code": "08202", "state": "SC"})
        ext = external(fields={"address.ibge_city_code": ABSENT})
        review = compare_supplier_snapshots(
            can, ext, municipality_index=CC2_INDEX
        )
        city = proposal_for(review, "city")
        assert city.eligibility is EligibilityState.PENDING_VALIDATION
        assert city.eligibility_reason == "municipality_source_incomplete"


class TestNormalization:
    def test_cosmetic_differences_match(self):
        can = canonical(fields={"supplier_name": "acme   brasil  ltda"})
        review = compare_supplier_snapshots(can, external())
        assert proposal_for(review, "supplier_name").comparison is ComparisonState.MATCH

    def test_accents_do_not_create_difference(self):
        can = canonical(fields={"district": "SÃO  PAULO"})
        ext = external(fields={"address.district": "Sao Paulo"})
        review = compare_supplier_snapshots(can, ext)
        assert proposal_for(review, "district").comparison is ComparisonState.MATCH

    def test_postal_code_normalized_to_digits(self):
        can = canonical(fields={"postal_code": "89010-000"})
        review = compare_supplier_snapshots(can, external())
        assert proposal_for(review, "postal_code").comparison is ComparisonState.MATCH

    def test_email_casefold_match(self):
        can = canonical(fields={"email": "CONTATO@ACME.EXAMPLE"})
        review = compare_supplier_snapshots(can, external())
        assert proposal_for(review, "email").comparison is ComparisonState.MATCH


class TestEligibilityPolicy:
    def test_short_name_needs_equivalence_rule(self):
        ext = external(fields={"company.trade_name": "ACME NOVA"})
        review = compare_supplier_snapshots(canonical(), ext)
        prop = proposal_for(review, "supplier_short_name")
        assert prop.comparison is ComparisonState.DIFFERENT
        assert prop.eligibility is EligibilityState.PENDING_VALIDATION
        assert prop.eligibility_reason == "equivalence_rule_pending"

    def test_contact_fields_need_trusted_source_policy(self):
        ext = external(fields={"contact.phone": "999887766"})
        review = compare_supplier_snapshots(canonical(), ext)
        prop = proposal_for(review, "phone")
        assert prop.comparison is ComparisonState.DIFFERENT
        assert prop.eligibility is EligibilityState.PENDING_VALIDATION
        assert prop.eligibility_reason == "trusted_source_policy_pending"

    def test_invalid_email_pending(self):
        ext = external(fields={"contact.email": "not-an-email"})
        review = compare_supplier_snapshots(canonical(), ext)
        prop = proposal_for(review, "email")
        assert prop.eligibility is EligibilityState.PENDING_VALIDATION
        assert prop.eligibility_reason == "invalid_suggested_value"

    def test_invalid_postal_code_pending(self):
        ext = external(fields={"address.postal_code": "123"})
        review = compare_supplier_snapshots(canonical(), ext)
        prop = proposal_for(review, "postal_code")
        assert prop.eligibility is EligibilityState.PENDING_VALIDATION
        assert prop.eligibility_reason == "invalid_suggested_value"

    def test_informational_fields_never_eligible(self):
        ext = external(fields={"company.registration_status": "BAIXADA"})
        review = compare_supplier_snapshots(canonical(), ext)
        prop = proposal_for(review, "registration_status")
        assert prop.comparison is ComparisonState.DIFFERENT
        assert prop.eligibility is EligibilityState.NOT_APPLICABLE
        assert prop.eligibility_reason == "informational_only"


class TestMappingBoundaries:
    def test_unmapped_canonical_fields_not_compared(self):
        can = canonical(fields={"payment_condition_code": "001", "extra": "x"})
        review = compare_supplier_snapshots(can, external())
        keys = {p.field_key for p in review.comparison.proposals}
        assert "payment_condition_code" not in keys
        assert "extra" not in keys

    def test_unknown_external_fields_ignored(self):
        ext = external(fields={"rogue.field": "x", "company.evil": "y"})
        review = compare_supplier_snapshots(canonical(), ext)
        assert all(
            p.source_field != "rogue.field" for p in review.comparison.proposals
        )

    def test_case_j_mixed_data_consistent_counts(self):
        can = canonical(
            fields={
                "district": None,
                "city": "TIMBO",
                "city_code": "08202",
                "phone": "99999999",
            }
        )
        ext = external(
            fields={
                "address.street": ABSENT,
                "company.legal_name": "ACME INDUSTRIA E COMERCIO LTDA",
            }
        )
        review = compare_supplier_snapshots(
            can, ext, municipality_index=CC2_INDEX
        )
        summary = review.comparison.summary
        proposals = review.comparison.proposals
        states = {p.comparison for p in proposals}
        assert ComparisonState.MATCH in states
        assert ComparisonState.DIFFERENT in states
        assert ComparisonState.SOURCE_MISSING in states
        assert ComparisonState.CURRENT_MISSING in states
        assert ComparisonState.PROTECTED in states
        assert summary["total_fields"] == len(proposals)
        assert summary["match"] >= 1 and summary["different"] >= 1
        assert summary["source_missing"] == 1
        assert summary["eligible_to_apply"] + summary["pending_validation"] + summary[
            "not_applicable"
        ] + summary["protected"] == len(proposals)


class TestDeterminismAndMetadata:
    def test_same_input_same_output(self):
        first = compare_supplier_snapshots(canonical(), external())
        second = compare_supplier_snapshots(canonical(), external())
        assert first == second

    def test_review_metadata_passthrough(self):
        can = canonical(baseline_reference="baseline-abc")
        ext = external(source_reference="req-9", retrieved_at="2026-10-22T10:00:00Z")
        review = compare_supplier_snapshots(can, ext)
        comp = review.comparison
        assert comp.mapping_version == CNPJ_SA2_MAPPING_V1.version
        assert comp.retrieved_at == "2026-10-22T10:00:00Z"
        assert comp.baseline_reference == "baseline-abc"
        assert comp.source_id == "synthetic-registry"
        assert review.review_id is None
        for proposal in comp.proposals:
            assert proposal.source_reference == "req-9"
            assert proposal.decision is FieldDecisionState.PENDING
            assert proposal.normalization_version == "norm-v1"
