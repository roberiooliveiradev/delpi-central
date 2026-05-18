from dataclasses import asdict, dataclass


@dataclass
class CommercialRolSeriesPointDto:
    periodo: str
    sort_key: str
    date_start: str
    date_end: str
    rol_matrix: float
    rol_branch: float


@dataclass
class CommercialRolSeriesResponse:
    granularity: str
    truncated: bool
    points: list[CommercialRolSeriesPointDto]

    def to_dict(self) -> dict:
        return {
            "granularity": self.granularity,
            "truncated": self.truncated,
            "points": [asdict(point) for point in self.points],
        }
