from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tm_app.cli.cadastro_json_cli import build_parser, cmd_export, cmd_preview


def test_build_parser_export_requires_output():
    args = build_parser().parse_args(["export", "-o", "/tmp/out.json"])
    assert args.command == "export"
    assert args.output == "/tmp/out.json"


@patch("tm_app.cli.cadastro_json_cli.JsonBackupService")
def test_cmd_export_writes_file(mock_service_cls, tmp_path: Path):
    mock_service = MagicMock()
    mock_service.export_bundle.return_value = {
        "schema_version": "1.1",
        "exported_at": "2026-06-12T00:00:00+00:00",
        "counts": {"processos": 1},
        "processos": [],
    }
    mock_service_cls.return_value = mock_service

    out = tmp_path / "backup.json"
    cmd_export(Namespace(output=str(out)))

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.1"
    mock_service.export_bundle.assert_called_once()


def test_cmd_preview_invalid_exits(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("{}", encoding="utf-8")

    with patch("tm_app.cli.cadastro_json_cli.JsonBackupService") as mock_cls:
        mock_cls.return_value.preview.return_value = {
            "valid": False,
            "errors": ["schema_version inválida."],
        }
        with pytest.raises(SystemExit) as exc:
            cmd_preview(Namespace(input=str(path), mode="replace", format="auto"))
    assert exc.value.code == 1
