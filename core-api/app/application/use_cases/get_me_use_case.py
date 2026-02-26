# app/application/use_cases/get_me_use_case.py

from dataclasses import dataclass
from typing import List


@dataclass
class MeDTO:
    id: str
    name: str
    email: str
    is_superadmin: bool
    permissions: List[str]


class GetMeUseCase:
    def execute(self, user, permissions: List[str]) -> MeDTO:
        return MeDTO(
            id=str(user.id),
            name=user.name,
            email=user.email,
            is_superadmin=bool(user.is_superadmin),
            permissions=permissions,
        )