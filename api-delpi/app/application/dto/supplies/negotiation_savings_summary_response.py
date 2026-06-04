from dataclasses import dataclass, field


@dataclass
class NegotiationSavingsBranchSummary:
    branch: str
    total_savings: float | None

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "total_savings": self.total_savings,
        }


@dataclass
class NegotiationSavingsEntry:
    branch: str
    date: str
    savings_amount: float

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "date": self.date,
            "savings_amount": self.savings_amount,
        }


@dataclass
class NegotiationSavingsSummaryResponse:
    start_date: str | None
    end_date: str | None
    branch: str | None
    total_savings: float | None
    branches: list[NegotiationSavingsBranchSummary] = field(default_factory=list)
    entries: list[NegotiationSavingsEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "branch": self.branch,
            "total_savings": self.total_savings,
            "summary": {
                "total_savings": self.total_savings,
            },
            "branches": [item.to_dict() for item in self.branches],
            "entries": [item.to_dict() for item in self.entries],
        }
