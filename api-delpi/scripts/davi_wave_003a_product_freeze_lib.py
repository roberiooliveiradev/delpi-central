#!/usr/bin/env python3
"""DAVI Wave 3A Product Engineering/Planning — evidence freeze helpers (no runtime mutation)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

TASK_ID = "DAVI-CAPABILITY-EXPANSION-WAVE-003A-FREEZE"
IMPLEMENTATION_TASK_ID = "DAVI-CAPABILITY-EXPANSION-WAVE-003A"
INVENTORY_STEM = "davi-capability-wave-003a-inventory"
FREEZE_STEM = "davi-capability-wave-003a-freeze"
ARTIFACT_CLASS = "EVIDENCE_NOT_RUNTIME_AUTHORITY"

CURRENT_ELIGIBLE = [
    "search_products",
    "get_product_stock",
    "get_product_suppliers",
    "get_product_customers",
    "get_product_purchases",
    "get_product_structure",
    "get_product_production_status",
    "get_product_factory_status",
    "get_product_structure_exclusivity",
    "get_product_shipping_status",
    "get_product_pricing",
    "get_product_purchase_price_history",
    "get_product_last_purchase",
]
MCP_TOOLS = [
    "search_products",
    "discover_delpi_information",
    "execute_delpi_information",
]
WAVE3A_OPS = (
    "get_product_guide",
    "get_product_parents",
    "get_product_raw_material_set_shortages",
)
REQUIRED_FREEZE_FIELDS = (
    "capabilityId",
    "businessName",
    "businessNeed",
    "status",
    "canonicalOperations",
    "canonicalUseCases",
    "readPrepareAct",
    "technicalOwner",
    "businessOwner",
    "sourceOfTruth",
    "backendAuthz",
    "approvedInputFields",
    "requiredInputFields",
    "optionalInputFields",
    "approvedResponseFields",
    "responseShape",
    "projectionMode",
    "branchSemantics",
    "pagination",
    "limits",
    "completeness",
    "provenance",
    "semanticAliasesPtBr",
    "semanticAliasesEn",
    "runtimeRisk",
    "observability",
    "negativeAuthzPlan",
    "liveAcceptancePlan",
    "openGaps",
)

_API_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _API_ROOT.parent
_EVIDENCE = _API_ROOT / "docs" / "integrations" / "evidence"


def git_sha(ref: str = "HEAD") -> str:
    return subprocess.check_output(
        ["git", "rev-parse", ref], cwd=str(_REPO_ROOT), text=True
    ).strip()


def inventory_path() -> Path:
    return _EVIDENCE / f"{INVENTORY_STEM}.json"


def freeze_path() -> Path:
    return _EVIDENCE / f"{FREEZE_STEM}.json"


def load_inventory() -> dict[str, Any]:
    return json.loads(inventory_path().read_text(encoding="utf-8"))


def load_freeze() -> dict[str, Any]:
    return json.loads(freeze_path().read_text(encoding="utf-8"))


def candidate_records() -> list[dict[str, Any]]:
    return list(load_inventory()["candidates"])


def frozen_records() -> list[dict[str, Any]]:
    return [c for c in candidate_records() if c["status"] == "FROZEN_FOR_IMPLEMENTATION"]


def deferred_records() -> list[dict[str, Any]]:
    return [c for c in candidate_records() if c["status"] == "DEFER"]


def openapi_operation_ids() -> set[str]:
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    found: set[str] = set()
    for op in baseline.get("operations") or []:
        if isinstance(op, dict) and op.get("operationId"):
            found.add(str(op["operationId"]))
    for item in (baseline.get("paths") or {}).values():
        if not isinstance(item, dict):
            continue
        for op in item.values():
            if isinstance(op, dict) and op.get("operationId"):
                found.add(str(op["operationId"]))
    return found


def openapi_operation_methods() -> dict[str, str]:
    """Map operationId → HTTP method (lowercase) from baseline operations list."""
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    found: dict[str, str] = {}
    for op in baseline.get("operations") or []:
        if not isinstance(op, dict) or not op.get("operationId"):
            continue
        method = str(op.get("method") or op.get("httpMethod") or "").lower()
        if not method:
            continue
        found[str(op["operationId"])] = method
    return found


def validate_source() -> dict[str, Any]:
    allow = json.loads(
        (_API_ROOT / "app/content/davi_external_read_allowlist.json").read_text(
            encoding="utf-8"
        )
    )
    routes = (_API_ROOT / "app/interface/http/routes/product_routes.py").read_text(
        encoding="utf-8"
    )
    ops = openapi_operation_ids()
    eligible_ids = [
        o.get("operationId")
        for o in (allow.get("operations") or [])
        if isinstance(o, dict)
    ]
    guide_authz = bool(
        re.search(
            r'@router\.get\("/\{code\}/guide".*?@require_permission\(API_DELPI_ACCESS\)',
            routes,
            re.S,
        )
    )
    parents_authz = bool(
        re.search(
            r'@router\.get\("/\{code\}/parents".*?@require_permission\(API_DELPI_ACCESS\)',
            routes,
            re.S,
        )
    )
    shortages_authz = bool(
        re.search(
            r"raw-material-set-shortages.*?@require_permission\(API_DELPI_ACCESS\)",
            routes,
            re.S,
        )
    )
    shortages_gate = "raw_material_set_shortage_branch_error" in routes
    ok = (
        allow.get("version") == 8
        and len(eligible_ids) == 15
        and set(CURRENT_ELIGIBLE) <= set(eligible_ids)
        and all(op in ops for op in WAVE3A_OPS)
        and "get_product_guide" in eligible_ids
        and "get_product_parents" in eligible_ids
        and "get_product_raw_material_set_shortages" not in eligible_ids
        and guide_authz
        and parents_authz
        and shortages_authz
        and shortages_gate
    )
    return {
        "ok": ok,
        "allowlistVersion": allow.get("version"),
        "eligibleCount": len(eligible_ids),
        "eligibleIds": eligible_ids,
        "openapiPresent": {op: op in ops for op in WAVE3A_OPS},
        "authz": {
            "get_product_guide": guide_authz,
            "get_product_parents": parents_authz,
            "get_product_raw_material_set_shortages": shortages_authz,
            "shortagesBranchGate": shortages_gate,
        },
    }


def guide_uc_default_max_depth() -> int | None:
    text = (
        _API_ROOT
        / "app/application/use_cases/product/list_product_guide_use_case.py"
    ).read_text(encoding="utf-8")
    m = re.search(r"max_depth = dto\.max_depth or (\d+)", text)
    return int(m.group(1)) if m else None


def parents_uc_default_max_depth() -> int | None:
    text = (
        _API_ROOT
        / "app/application/use_cases/product/list_product_parents_use_case.py"
    ).read_text(encoding="utf-8")
    m = re.search(r"max_depth = request\.max_depth or (\d+)", text)
    return int(m.group(1)) if m else None


def shortages_has_pagination() -> bool:
    text = (
        _API_ROOT
        / "app/application/use_cases/product/get_product_raw_material_set_shortages_use_case.py"
    ).read_text(encoding="utf-8")
    return "page" in text and "page_size" in text
