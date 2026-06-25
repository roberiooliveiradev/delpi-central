"""Gate PAC Onda 1 — rotas na api-delpi."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_audit_module():
    path = Path(__file__).resolve().parents[3] / "scripts" / "audit_api_delpi_pac_onda1.py"
    spec = importlib.util.spec_from_file_location("audit_api_delpi_pac_onda1", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_onda1_operation_ids_present_in_openapi_contracts():
    audit = _load_audit_module()
    contracts_path = (
        Path(__file__).resolve().parents[3]
        / "app/content/pt-BR/assistant/openapi_operation_contracts.json"
    )
    payload = json.loads(contracts_path.read_text(encoding="utf-8"))

    assert isinstance(payload, dict)

    missing = [op for op in audit.ONDA1_OPERATION_IDS if op not in payload]

    assert missing == []


def test_audit_api_delpi_pac_onda1_validates_synthetic_schema():
    audit = _load_audit_module()
    contracts_path = (
        Path(__file__).resolve().parents[3]
        / "app/content/pt-BR/assistant/openapi_operation_contracts.json"
    )
    operations = json.loads(contracts_path.read_text(encoding="utf-8"))

    paths = {path: {} for path in audit.ONDA1_REQUIRED_OPENAPI_PATHS}

    for operation_id in audit.ONDA1_OPERATION_IDS:
        contract = operations[operation_id]
        paths[f"/quality/action-plans/__audit__/{operation_id}"] = {
            "get": {
                "operationId": operation_id,
                "x-delpi": {
                    "entity": contract["entity"],
                    "shape": contract["shape"],
                    "presentation": {"strategy": "as_delivered"},
                },
            }
        }

    report = audit.validate({"paths": paths})

    assert report["missingOperationIds"] == []
    assert report["missingXDelpi"] == []
    assert report["contractMismatches"] == []
