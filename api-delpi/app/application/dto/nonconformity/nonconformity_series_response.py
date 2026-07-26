from dataclasses import asdict, dataclass


@dataclass
class NonconformitySeriesPointDto:
    periodo: str
    sort_key: str
    start_date: str
    end_date: str
    value: float
    registros: int


@dataclass
class NonconformitySeriesResponse:
    type: str
    granularity: str
    truncated: bool
    points: list[NonconformitySeriesPointDto]

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "granularity": self.granularity,
            "truncated": self.truncated,
            "points": [asdict(point) for point in self.points],
        }
