from __future__ import annotations

from app.application.dto.product.product_raw_material_set_shortage_request import (
    ProductRawMaterialSetShortageRequest,
)
from app.application.use_cases.product.get_product_raw_material_set_shortages_use_case import (
    GetProductRawMaterialSetShortagesUseCase,
)


class _FakeRepo:
    def fetch_product(self, code: str):
        if code != "90263114":
            return None
        return {
            "product_code": "90263114",
            "product_description": "CHICOTE",
            "product_type": "PA",
            "unit": "PC",
        }

    def fetch_raw_material_bom(self, code: str, *, max_depth: int):
        return [
            {
                "product_code": "10080001",
                "product_description": "CABO",
                "unit": "KG",
                "secondary_unit": "",
                "conversion_factor": None,
                "conversion_type": "",
                "bom_level": 1,
                "structure_quantity": 1.0,
            }
        ]

    def fetch_open_mother_orders(self, *, code: str, branch: str):
        return [
            {
                "branch": branch,
                "production_order": "24608101001",
                "order_number": "246081",
                "order_item": "01",
                "product_code": code,
                "product_description": "CHICOTE",
                "planned_start_date": "2026-09-12",
                "due_date": "2026-09-20",
                "planned_quantity": 10.0,
                "produced_quantity": 0.0,
                "open_quantity": 10.0,
                "observation": "",
            }
        ]

    def fetch_committed_product_codes_for_mother_orders(
        self, *, branch: str, mother_orders: list[str]
    ):
        assert mother_orders == ["24608101001"]
        return ["10080001"]

    def fetch_mp_stock(self, *, branch: str, product_codes: list[str]):
        return [
            {
                "product_code": "10080001",
                "product_description": "CABO",
                "unit": "KG",
                "secondary_unit": "",
                "conversion_factor": None,
                "conversion_type": "",
                "available_stock": 10.0,
                "safety_stock": 2.0,
            }
        ]

    def fetch_open_purchase_orders(self, *, branch: str, product_codes: list[str]):
        return []

    def fetch_open_commitments(self, *, branch: str, product_codes: list[str]):
        return [
            {
                "warehouse": "01",
                "unit": "KG",
                "open_quantity": 12.0,
                "commitment_date": "2026-09-12",
                "production_order": "24608101003",
                "finished_production_order": "24608101001",
                "finished_product_code": "90263114",
                "product_code": "10080001",
            }
        ]


class _FakeRepoWithSubstitute(_FakeRepo):
    def fetch_raw_material_bom(self, code: str, *, max_depth: int):
        return [
            {
                "product_code": "10080001",
                "product_description": "CABO ORIGINAL",
                "unit": "KG",
                "secondary_unit": "",
                "conversion_factor": None,
                "conversion_type": "",
                "bom_level": 1,
                "structure_quantity": 1.0,
            }
        ]

    def fetch_committed_product_codes_for_mother_orders(
        self, *, branch: str, mother_orders: list[str]
    ):
        return ["10080099"]

    def fetch_mp_stock(self, *, branch: str, product_codes: list[str]):
        assert "10080001" in product_codes
        assert "10080099" in product_codes
        return [
            {
                "product_code": "10080001",
                "product_description": "CABO ORIGINAL",
                "unit": "KG",
                "available_stock": 0.0,
                "safety_stock": 0.0,
            },
            {
                "product_code": "10080099",
                "product_description": "CABO SUBSTITUTO",
                "unit": "KG",
                "available_stock": 50.0,
                "safety_stock": 0.0,
            },
        ]

    def fetch_open_commitments(self, *, branch: str, product_codes: list[str]):
        return [
            {
                "warehouse": "01",
                "unit": "KG",
                "open_quantity": 5.0,
                "commitment_date": "2026-09-12",
                "production_order": "24608101003",
                "finished_production_order": "24608101001",
                "finished_product_code": "90263114",
                "product_code": "10080099",
            }
        ]


def test_use_case_returns_none_when_product_missing() -> None:
    result = GetProductRawMaterialSetShortagesUseCase(_FakeRepo()).execute(
        ProductRawMaterialSetShortageRequest(code="00000000", branch="01")
    )
    assert result is None


def test_use_case_pegs_shortage_from_dump() -> None:
    result = GetProductRawMaterialSetShortagesUseCase(_FakeRepo()).execute(
        ProductRawMaterialSetShortageRequest(code="90263114", branch="01")
    )
    assert result is not None
    assert result["branch"] == "01"
    assert result["summary"]["at_risk_set_count"] == 1
    assert result["sets"][0]["status"] == "shortage"


def test_use_case_includes_sd4_substitute_and_skips_uncommitted_bom() -> None:
    result = GetProductRawMaterialSetShortagesUseCase(_FakeRepoWithSubstitute()).execute(
        ProductRawMaterialSetShortageRequest(code="90263114", branch="01")
    )
    assert result is not None
    first = result["sets"][0]
    assert first["status"] == "ok"
    assert [m["product_code"] for m in first["materials"]] == ["10080099"]
    assert first["planned_without_commitment"] == []
    assert "10080001" not in [m["product_code"] for m in first["materials"]]
