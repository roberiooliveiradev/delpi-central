from dataclasses import dataclass
from typing import Optional


@dataclass
class ProducedQuantityRequest:
    products: list[str]
    date_start: str
    date_end: str
    branch: Optional[str] = None

    def __post_init__(self) -> None:
        normalized: list[str] = []
        seen: set[str] = set()

        for raw in self.products:
            for part in str(raw or "").split(","):
                code = part.strip()
                if not code or code in seen:
                    continue
                seen.add(code)
                normalized.append(code)

        if not normalized:
            raise ValueError("Informe ao menos um código de produto em product.")

        if not (self.date_start and str(self.date_start).strip()):
            raise ValueError("date_start é obrigatório.")

        if not (self.date_end and str(self.date_end).strip()):
            raise ValueError("date_end é obrigatório.")

        self.products = normalized
