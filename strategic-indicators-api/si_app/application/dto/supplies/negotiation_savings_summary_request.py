from dataclasses import dataclass


@dataclass
class NegotiationSavingsSummaryRequest:
    start_date: str | None = None
    end_date: str | None = None
    branch: str | None = None
