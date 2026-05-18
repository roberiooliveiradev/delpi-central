from dataclasses import asdict, dataclass


@dataclass
class QualityBranchesResponse:
    branches: list[str]

    def to_dict(self) -> dict:
        return asdict(self)
