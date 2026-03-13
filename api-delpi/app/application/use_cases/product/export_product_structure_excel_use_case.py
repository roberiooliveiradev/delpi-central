# app/application/use_cases/products/export_product_structure_excel_use_case.py
from app.domain.ports.product.product_structure_repository_port import ProductStructureRepositoryPort
from app.application.services.bom_tree_builder import BomTreeBuilder
from app.application.services.excel_structure_builder import ExcelStructureBuilder
from app.application.dto.product.export_structure_excel_request import ExportStructureExcelRequest


class ExportProductStructureExcelUseCase:

    def __init__(self, repository: ProductStructureRepositoryPort):
        self._repository = repository

    def execute(self, request: ExportStructureExcelRequest):

        rows = self._repository.fetch_structure_rows(
            request.code,
            999
        )

        root = BomTreeBuilder.build(rows, request.code)

        if not root:
            raise Exception("Estrutura não encontrada")

        excel_stream = ExcelStructureBuilder.build(root)

        return excel_stream