from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransformometroSheetSources:
    sheet_id: str
    tabs: dict[str, str]

    def gid_for(self, tab_name: str) -> str:
        gid = self.tabs.get(tab_name)
        if not gid:
            raise KeyError(f"GID não configurado para aba: {tab_name}")
        return gid
