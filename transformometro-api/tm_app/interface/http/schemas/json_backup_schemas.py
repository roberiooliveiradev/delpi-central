from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ImportMode = Literal["replace", "merge"]


class JsonImportBody(BaseModel):
    mode: ImportMode = Field(
        ...,
        description="replace: apaga cadastro e importa tudo; merge: upsert por ID sem apagar o restante.",
    )
    data: dict[str, Any] = Field(..., description="Pacote JSON exportado pelo Transformômetro.")
