from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TransformaMaisRawData:
    processos: List[dict]
    revisoes: List[dict]
    medicoes: List[dict]
    investimentos: List[dict]
    recursos_compartilhados: List[dict]
    revisao_recursos_compartilhados: List[dict]