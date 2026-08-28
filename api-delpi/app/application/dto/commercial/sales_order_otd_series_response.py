from dataclasses import asdict, dataclass


@dataclass
class SalesOrderOtdSeriesPointDto:
    periodo: str
    sort_key: str
    start_date: str
    end_date: str
    otd_filial_01: float | None
    otd_filial_02: float | None
    total_qty: float | None = None
    fulfilled_qty: float | None = None
    fulfillment_pct: float | None = None
    otd_pct: float | None = None
    total_lines: int | None = None
    unit: str | None = None
    mixed_units: bool = False


@dataclass
class SalesOrderOtdSeriesResponse:
    granularity: str
    truncated: bool
    branch: str | None
    points: list[SalesOrderOtdSeriesPointDto]

    def to_dict(self) -> dict:
        return {
            "granularity": self.granularity,
            "truncated": self.truncated,
            "branch": self.branch,
            "points": [asdict(point) for point in self.points],
        }
