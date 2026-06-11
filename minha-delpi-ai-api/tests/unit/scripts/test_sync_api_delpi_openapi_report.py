"""Validação de exit code do sync OpenAPI pós-deploy."""

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "sync_api_delpi_openapi",
    _ROOT / "scripts" / "sync_api_delpi_openapi.py",
)
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MOD)

_report_is_successful = _MOD._report_is_successful


def test_report_successful_with_import():
    report = {
        "import": {"found": True, "actionsImported": 42},
        "actionsInDatabase": 42,
    }
    assert _report_is_successful(report, skip_import=False) is True


def test_report_fails_when_provider_missing():
    report = {
        "import": {"found": False},
        "actionsInDatabase": 0,
    }
    assert _report_is_successful(report, skip_import=False) is False


def test_report_successful_when_skip_import_and_actions_exist():
    report = {"actionsInDatabase": 10}
    assert _report_is_successful(report, skip_import=True) is True
