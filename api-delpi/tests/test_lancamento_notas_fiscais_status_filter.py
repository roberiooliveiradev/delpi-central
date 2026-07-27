from app.domain.services.lancamento_notas_fiscais.fiscal_normalization import (
    LIST_STATUS_FILTER_OPEN,
    NON_TERMINAL_STATUSES,
    resolve_list_status_filter,
)


def test_resolve_list_status_filter_open() -> None:
    assert resolve_list_status_filter(LIST_STATUS_FILTER_OPEN) == tuple(
        sorted(NON_TERMINAL_STATUSES)
    )
    assert resolve_list_status_filter("OPEN") == ("blocked", "in_progress", "pending")


def test_resolve_list_status_filter_single() -> None:
    assert resolve_list_status_filter("pending") == ("pending",)
    assert resolve_list_status_filter("posted") == ("posted",)


def test_resolve_list_status_filter_empty() -> None:
    assert resolve_list_status_filter(None) is None
    assert resolve_list_status_filter("") is None
    assert resolve_list_status_filter("  ") is None


def test_resolve_list_status_filter_invalid() -> None:
    try:
        resolve_list_status_filter("unknown")
        raise AssertionError("esperava ValueError")
    except ValueError as exc:
        assert "status inválido" in str(exc)
