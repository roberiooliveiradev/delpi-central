from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class FinancialIndicatorsSources:
    sheet_id: str
    tabs: Dict[str, str]

    def gid_for(self, tab_name: str) -> str:
        gid = self.tabs.get(tab_name)
        if not gid:
            raise ValueError(f"gid não configurado para a aba '{tab_name}'")
        return gid