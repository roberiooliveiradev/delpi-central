# app/application/use_cases/products/get_product_pricing_use_case.py
from app.domain.ports.product.product_pricing_repository_port import ProductPricingRepositoryPort
from app.application.dto.product.get_product_pricing_request import GetProductPricingRequest


class GetProductPricingUseCase:

    def __init__(
        self,
        repository: ProductPricingRepositoryPort
    ):
        self.repository = repository

    def execute(
        self,
        dto: GetProductPricingRequest
    ):

        pricing = self.repository.get_product_pricing(
            code=dto.code
        )

        if not pricing:
            return {
                "success": False,
                "message": f"Product {dto.code} not found"
            }

        return {
            "product": {
                "code": pricing.product_code,
                "description": pricing.product_description,
                "unit": pricing.unit
            },
            "prices": [
                p.__dict__
                for p in pricing.prices
            ]
        }