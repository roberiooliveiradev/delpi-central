"""Use case SB1 identity lookup — orquestra repositório e classificador."""

from __future__ import annotations

from app.application.dto.product.sb1_identity_lookup_request import (
    Sb1IdentityLookupItem,
    Sb1IdentityLookupRequest,
)
from app.application.use_cases.product.sb1_identity_lookup_use_case import (
    Sb1IdentityLookupUseCase,
)


class _FakeRepo:
    def __init__(self, by_code=None, by_ref=None):
        self.by_code = by_code or []
        self.by_ref = by_ref or []
        self.code_calls: list[list[str]] = []
        self.ref_calls: list[list[str]] = []

    def lookup_products_by_codes(self, codes: list[str]):
        self.code_calls.append(list(codes))
        return [row for row in self.by_code if row["product_code"] in codes]

    def lookup_products_by_customer_references(self, references: list[str]):
        self.ref_calls.append(list(references))
        return [
            row for row in self.by_ref if row["customer_reference"] in references
        ]


def test_batch_dedupes_codes_and_references() -> None:
    repo = _FakeRepo(
        by_code=[
            {
                "product_code": "A1",
                "customer_reference": "R1",
                "description": "One",
                "product_type": "PA",
                "unit": "UN",
                "group_code": "01",
                "blocked_flag": "2",
            }
        ],
        by_ref=[
            {
                "product_code": "A1",
                "customer_reference": "R1",
                "description": "One",
                "product_type": "PA",
                "unit": "UN",
                "group_code": "01",
                "blocked_flag": "2",
            }
        ],
    )
    use_case = Sb1IdentityLookupUseCase(repository=repo)  # type: ignore[arg-type]
    result = use_case.execute(
        Sb1IdentityLookupRequest(
            branch="02",
            items=(
                Sb1IdentityLookupItem("1", "A1", "R1"),
                Sb1IdentityLookupItem("2", "A1", "R1"),
            ),
        )
    )
    assert len(repo.code_calls[0]) == 1
    assert len(repo.ref_calls[0]) == 1
    assert result["summary"]["confirmed"] == 2
    assert result["side_effects"] is False


def test_ambiguous_counted() -> None:
    repo = _FakeRepo(
        by_ref=[
            {
                "product_code": "A1",
                "customer_reference": "R1",
                "description": "One",
                "product_type": "PA",
                "unit": "UN",
                "group_code": "01",
                "blocked_flag": "2",
            },
            {
                "product_code": "A2",
                "customer_reference": "R1",
                "description": "Two",
                "product_type": "PA",
                "unit": "UN",
                "group_code": "01",
                "blocked_flag": "2",
            },
        ]
    )
    use_case = Sb1IdentityLookupUseCase(repository=repo)  # type: ignore[arg-type]
    result = use_case.execute(
        Sb1IdentityLookupRequest(
            branch="02",
            items=(Sb1IdentityLookupItem("1", None, "R1"),),
        )
    )
    assert result["summary"]["ambiguous"] == 1
    assert result["results"][0]["verified_product_code"] is None
