from dataclasses import dataclass
from typing import Literal, Optional


CatalogView = Literal["by_material", "by_finished_product"]


@dataclass
class ExclusiveRawMaterialCatalogRequest:
    view: CatalogView = "by_material"
    limit: Optional[int] = None
    offset: Optional[int] = None
    max_depth: Optional[int] = None
    include_test_products: bool = False
    finished_product_code: Optional[str] = None
    raw_material_code: Optional[str] = None
    group_code: Optional[str] = None
    legacy: bool = False
