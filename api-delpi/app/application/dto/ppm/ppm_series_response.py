from dataclasses import asdict, dataclass, field


@dataclass
class PpmSeriesPointDto:
    periodo: str
    sort_key: str
    start_date: str
    end_date: str
    ppm: float
    total_devolvido_un: float
    total_produzido_un: float
    total_produzido_milheiro: float = 0.0
    numerator: dict = field(default_factory=dict)
    denominator: dict = field(default_factory=dict)


@dataclass
class PpmSeriesResponse:
    type: str
    granularity: str
    truncated: bool
    points: list[PpmSeriesPointDto]

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "granularity": self.granularity,
            "truncated": self.truncated,
            "points": [asdict(point) for point in self.points],
        }
