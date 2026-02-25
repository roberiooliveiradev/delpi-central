from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class Product(BaseModel):
    code: str
    description: str
    group_code: Optional[str] = None
    components: Optional[List["Product"]] = None

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True
    )

class ProductSearchRequest(BaseModel):
    page: int = 1
    page_size: int = 50
    code: Optional[str] = None
    description: Optional[str] = None
    group: Optional[str] = None
