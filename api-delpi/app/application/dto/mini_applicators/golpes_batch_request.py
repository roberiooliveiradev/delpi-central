from __future__ import annotations

from pydantic import BaseModel, Field


class GolpesBatchItem(BaseModel):
    codigo_ferramenta: str = Field(..., min_length=1, max_length=50)
    data_inicial: str = Field(..., min_length=1)
    data_final: str = Field(..., min_length=1)


class GolpesBatchRequest(BaseModel):
    filial: str = Field(..., pattern=r"^(01|02)$")
    items: list[GolpesBatchItem] = Field(default_factory=list)
