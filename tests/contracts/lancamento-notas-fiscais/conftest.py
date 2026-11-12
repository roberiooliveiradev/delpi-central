from __future__ import annotations

import pytest

from lnf_contract.guard import ProductionTargetError, assert_not_production, base_url
from lnf_contract.report import flush


def pytest_sessionstart(session: pytest.Session) -> None:
    url = base_url()
    if url:
        try:
            assert_not_production(url)
        except ProductionTargetError as exc:
            raise pytest.UsageError(str(exc)) from exc


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    flush()
