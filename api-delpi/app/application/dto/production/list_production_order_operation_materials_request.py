from dataclasses import dataclass

from app.domain.totvs.protheus_branches import normalize_branch_code


@dataclass(frozen=True)
class ListProductionOrderOperationMaterialsRequest:
    production_order: str
    operation: str
    branch: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", normalize_branch_code(self.branch))
