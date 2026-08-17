from dataclasses import asdict, dataclass


@dataclass
class SalesConversionRateSeriesPointDto:
    periodo: str
    sort_key: str
    start_date: str
    end_date: str
    conversion_filial_01: float | None
    conversion_filial_02: float | None
    qtd_proposals_01: int
    qtd_proposals_02: int
    qtd_won_01: int
    qtd_won_02: int


@dataclass
class SalesConversionRateSeriesResponse:
    granularity: str
    truncated: bool
    points: list[SalesConversionRateSeriesPointDto]

    def to_dict(self) -> dict:
        return {
            "granularity": self.granularity,
            "truncated": self.truncated,
            "points": [asdict(point) for point in self.points],
        }
