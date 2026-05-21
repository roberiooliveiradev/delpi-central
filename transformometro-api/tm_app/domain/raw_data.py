from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TransformometroRawData:
    processos: list[dict] = field(default_factory=list)
    revisoes: list[dict] = field(default_factory=list)
    medicoes: list[dict] = field(default_factory=list)
    investimentos: list[dict] = field(default_factory=list)
    recursos_compartilhados: list[dict] = field(default_factory=list)
    revisao_recursos_compartilhados: list[dict] = field(default_factory=list)
