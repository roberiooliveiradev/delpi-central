import importlib.util
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "import_access_csv.py"
_spec = importlib.util.spec_from_file_location("import_access_csv", _SCRIPTS)
_module = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_module)


def test_parse_datetime_accepts_common_formats():
    assert _module._parse_datetime("2026-06-12 10:00:00") == datetime(2026, 6, 12, 10, 0, 0)
    assert _module._parse_datetime("15/01/2026") == datetime(2026, 1, 15, 0, 0, 0)
    assert _module._parse_datetime(None) is None


def test_parse_datetime_rejects_invalid():
    with pytest.raises(ValueError, match="Data inválida"):
        _module._parse_datetime("invalid-date")


def test_import_reposicoes_dry_run_counts_rows(tmp_path: Path):
    csv_path = tmp_path / "repos.csv"
    csv_path.write_text(
        "Filial,CodigoFerramenta,CodigoPeca,DataReposicao,Golpes,Motivo\n"
        "01,23-001,P001,2026-06-01 10:00:00,50,DESGASTE\n",
        encoding="utf-8",
    )
    repo = MagicMock()
    count = _module.import_reposicoes(repo, csv_path, filial="01", dry_run=True)
    assert count == 1
    repo.execute.assert_not_called()
