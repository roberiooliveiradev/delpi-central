# app/application/use_cases/products/list_product_inspection_use_case.py
from app.domain.ports.product_inspection_repository_port import ProductInspectionRepositoryPort
from app.application.dto.list_product_inspection_request import ListProductInspectionRequest


class ListProductInspectionUseCase:

    def __init__(self, repository: ProductInspectionRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductInspectionRequest):

        inspections = self.repository.list_inspections(
            code=dto.code,
            max_depth=dto.max_depth
        )
        
        data = [
            {
                "product_code": i.product_code,
                "bom_level": i.bom_level,
                "has_inspection": i.has_inspection,
                "header": i.header,
                "measurable_tests": i.measurable_tests,
                "textual_tests": i.textual_tests,
            }
            for i in inspections
        ]

        return {
            "total": len(data),
            "data": data
        }