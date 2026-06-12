from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ImportMode = Literal["replace", "merge"]
ImportFormat = Literal["auto", "modern", "legacy"]


class JsonImportBody(BaseModel):
    mode: ImportMode = Field(
        ...,
        description="replace: apaga cadastro e importa tudo; merge: upsert por ID sem apagar o restante.",
    )
    import_format: ImportFormat = Field(
        default="auto",
        description=(
            "auto: detecta legado vs Playbook 18; "
            "legacy: JSON 1.1 com processos.filial_id/setor_id; "
            "modern: backup com filiais, instâncias e revisoes.instancia_id."
        ),
    )
    data: dict[str, Any] = Field(..., description="Pacote JSON exportado pelo Transformômetro.")
