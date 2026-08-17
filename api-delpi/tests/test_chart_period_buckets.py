from app.application.shared.chart_period_buckets import build_period_buckets
from app.domain.shared.pt_month_labels import format_month_year_chart_label


def test_format_month_year_chart_label_is_pt_br() -> None:
    assert format_month_year_chart_label(2026, 1) == "Jan. de 26"
    assert format_month_year_chart_label(2026, 2) == "Fev. de 26"
    assert format_month_year_chart_label(2026, 5) == "Mai. de 26"
    assert format_month_year_chart_label(2026, 12) == "Dez. de 26"


def test_month_buckets_use_portuguese_abbreviations() -> None:
    result = build_period_buckets(
        start_date="2026-01-01",
        end_date="2026-03-31",
        granularity="month",
    )
    assert result.truncated is False
    assert [bucket.label for bucket in result.buckets] == [
        "Jan. de 26",
        "Fev. de 26",
        "Mar. de 26",
    ]
    # Nunca inglês (strftime %b em LC_TIME=C).
    assert "Feb" not in " ".join(bucket.label for bucket in result.buckets)
