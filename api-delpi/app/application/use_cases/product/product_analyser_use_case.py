# app/application/use_cases/products/product_analyser_use_case.py
from app.application.dto.product.product_analyser_request import ProductAnalyserRequest
from app.application.dto.product.list_product_structured_request import ListProductStructureRequest
from app.application.dto.product.list_product_guide_request import ListProductGuideRequest
from app.application.dto.product.list_product_inspection_request import ListProductInspectionRequest
from app.application.dto.product.list_products_requests import ListProductsRequest

from app.application.use_cases.product.search_products_use_case import SearchProductsUseCase
from app.application.use_cases.product.list_product_structure_use_case import ListProductStructureUseCase
from app.application.use_cases.product.list_product_guide_use_case import ListProductGuideUseCase
from app.application.use_cases.product.list_product_inspection_use_case import ListProductInspectionUseCase
from app.application.services.product.protheus_field_normalizer import narrow_product_fields
from app.application.services.product.product_playbook_service import attach_pa_reference

SUMMARY_PAGE_SIZE = 3
SUMMARY_MAX_DEPTH = 2


class ProductAnalyserUseCase:

    def __init__(
        self,
        search_products_use_case: SearchProductsUseCase,
        structure_use_case: ListProductStructureUseCase,
        guide_use_case: ListProductGuideUseCase,
        inspection_use_case: ListProductInspectionUseCase
    ):
        self.search_products_use_case = search_products_use_case
        self.structure_use_case = structure_use_case
        self.guide_use_case = guide_use_case
        self.inspection_use_case = inspection_use_case

    def execute(self, dto: ProductAnalyserRequest):
        view = (dto.view or "full").strip().lower()
        is_summary = view == "summary"

        product_page = self.search_products_use_case.execute(
            ListProductsRequest(
                code=dto.code,
                page=1,
                page_size=1,
            )
        )

        product = None

        if product_page.items:
            p = product_page.items[0]
            product = p.to_dict() if hasattr(p, "to_dict") else vars(p)
            if is_summary:
                product = narrow_product_fields(product, view="summary")

        if is_summary:
            structure = self.structure_use_case.execute(
                ListProductStructureRequest(
                    code=dto.code,
                    page=1,
                    page_size=SUMMARY_PAGE_SIZE,
                    max_depth=SUMMARY_MAX_DEPTH,
                )
            )
            guide = self.guide_use_case.execute(
                ListProductGuideRequest(
                    code=dto.code,
                    page=1,
                    page_size=SUMMARY_PAGE_SIZE,
                )
            )
            inspection = self.inspection_use_case.execute(
                ListProductInspectionRequest(
                    code=dto.code,
                    page=1,
                    page_size=SUMMARY_PAGE_SIZE,
                )
            )
        else:
            structure = self.structure_use_case.execute(
                ListProductStructureRequest(
                    code=dto.code,
                    page=None,
                    page_size=None,
                    max_depth=None,
                )
            )
            guide = self.guide_use_case.execute(
                ListProductGuideRequest(
                    code=dto.code,
                    page=None,
                    page_size=None,
                )
            )
            inspection = self.inspection_use_case.execute(
                ListProductInspectionRequest(
                    code=dto.code,
                    page=None,
                    page_size=None,
                )
            )

        payload = {
            "product": product,
            "structure": structure,
            "guide": guide,
            "inspection": inspection,
        }

        return attach_pa_reference(payload, product)