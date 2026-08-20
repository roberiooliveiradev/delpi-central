from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SubpluginStatus = Literal["active", "coming_soon"]


@dataclass(frozen=True)
class Subplugin:
    id: str
    label: str
    description: str
    icon: str
    route: str
    status: SubpluginStatus
    permission: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "icon": self.icon,
            "route": self.route,
            "status": self.status,
            "permission": self.permission,
        }
