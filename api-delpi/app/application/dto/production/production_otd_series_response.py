from dataclasses import asdict, dataclass


@dataclass
class ProductionOtdSeriesPointDto:
    periodo: str
    sort_key: str
    start_date: str
    end_date: str
    otd_filial_01: float | None
    otd_filial_02: float | None


@dataclass
class ProductionOtdSeriesResponse:
    granularity: str
    truncated: bool
    branch: str | None
    points: list[ProductionOtdSeriesPointDto]

    def to_dict(self) -> dict:
        return {
            "granularity": self.granularity,
            "truncated": self.truncated,
            "branch": self.branch,
            "points": [asdict(point) for point in self.points],
        }
