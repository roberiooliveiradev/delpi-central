from __future__ import annotations

import time

from delpi_auth.request_context import (
    get_request_authorization,
    set_request_authorization,
)

from financial_app.application.services.parallel_block_runner import run_named_callables


def test_runner_executes_independent_loaders_in_parallel() -> None:
    sleep_s = 0.08

    def slow(value: str):
        def _load() -> str:
            time.sleep(sleep_s)
            return value

        return _load

    started = time.monotonic()
    result = run_named_callables(
        {"a": slow("A"), "b": slow("B"), "c": slow("C")},
        max_workers=3,
    )
    elapsed = time.monotonic() - started

    assert result == {"a": "A", "b": "B", "c": "C"}
    assert elapsed < sleep_s * 2


def test_runner_propagates_request_authorization_to_workers() -> None:
    set_request_authorization("Bearer parallel-token")
    seen: dict[str, str | None] = {}

    def read_auth() -> str:
        seen["auth"] = get_request_authorization()
        return "ok"

    result = run_named_callables(
        {"one": read_auth, "two": read_auth},
        max_workers=2,
    )

    assert result == {"one": "ok", "two": "ok"}
    assert seen["auth"] == "Bearer parallel-token"


def test_runner_stays_sequential_when_max_workers_is_one() -> None:
    order: list[str] = []

    def first() -> str:
        order.append("first")
        return "1"

    def second() -> str:
        order.append("second")
        return "2"

    result = run_named_callables(
        {"first": first, "second": second},
        max_workers=1,
    )

    assert result == {"first": "1", "second": "2"}
    assert order == ["first", "second"]
