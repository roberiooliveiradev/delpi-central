from dataclasses import asdict, dataclass


@dataclass
class ProductionOeeSeriesPointDto:
    periodo: str
    sort_key: str
    start_date: str
    end_date: str
    oee_filial_01: float | None
    oee_filial_02: float | None


@dataclass
class ProductionOeeSeriesResponse:
    granularity: str
    truncated: bool
    branch: str | None
    points: list[ProductionOeeSeriesPointDto]

    def to_dict(self) -> dict:
        return {
            "granularity": self.granularity,
            "truncated": self.truncated,
            "branch": self.branch,
            "points": [asdict(point) for point in self.points],
        }
