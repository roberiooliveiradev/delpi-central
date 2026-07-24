"""Catálogo SI → rotas TV (meta / realizado) + audience + baseline patch.

Uso:
  python scripts/sync_si_indicator_tv_catalog.py --check
  python scripts/sync_si_indicator_tv_catalog.py --write
  python scripts/sync_si_indicator_tv_catalog.py --write --sync-artifacts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = API_ROOT / "app" / "content" / "si_indicator_tv_catalog.json"
AUDIENCE_PATH = API_ROOT / "app" / "content" / "tv_route_audience.json"
BASELINE_PATH = API_ROOT / "app" / "content" / "openapi_baseline.json"
PARAM_LOCALE_PATH = API_ROOT / "app" / "content" / "openapi_param_locale.json"
INVENTORY_PATH = API_ROOT / "app" / "content" / "openapi_operation_id_inventory.json"
TESTS_SUPPORT_OPS = (
    API_ROOT / "tests" / "support" / "si_indicator_tv_operation_ids.py"
)

_REQUIRED_KEYS = ("indicatorId", "sourceKey", "name", "departmentId")
_ALLOWED_DEPARTMENTS = frozenset(
    {
        "financial",
        "hr",
        "commercial",
        "production",
        "quality",
        "supplies",
        "engineering",
    }
)

_SI_PARAM_NAMES = ("competence", "start_date", "end_date", "branch")


def _load_si_param_locale() -> dict[str, Any]:
    """xDelpi.params no shape canônico: params.<name>.locale.{en,pt-BR}.

    Fonte única: openapi_param_locale.json (sem duplicar textos no script).
    """
    payload = json.loads(PARAM_LOCALE_PATH.read_text(encoding="utf-8"))
    params = payload.get("params") if isinstance(payload, dict) else None
    if not isinstance(params, dict):
        raise RuntimeError("openapi_param_locale.json sem objeto params")
    out: dict[str, Any] = {}
    for name in _SI_PARAM_NAMES:
        entry = params.get(name)
        if not isinstance(entry, dict):
            raise RuntimeError(f"openapi_param_locale.json sem params.{name}")
        locale = entry.get("locale")
        if not isinstance(locale, dict):
            raise RuntimeError(f"openapi_param_locale.json params.{name} sem locale")
        out[name] = {"locale": locale}
    return out


_PARAM_LOCALE = _load_si_param_locale()


def load_catalog(path: Path = CATALOG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_catalog(payload: dict) -> list[str]:
    errors: list[str] = []
    indicators = payload.get("indicators")
    if not isinstance(indicators, list) or not indicators:
        return ["indicators deve ser lista não vazia"]

    seen_ids: set[str] = set()
    for index, item in enumerate(indicators):
        if not isinstance(item, dict):
            errors.append(f"indicators[{index}] deve ser objeto")
            continue
        for key in _REQUIRED_KEYS:
            if not str(item.get(key) or "").strip():
                errors.append(f"indicators[{index}].{key} obrigatório")
        iid = str(item.get("indicatorId") or "").strip()
        if iid in seen_ids:
            errors.append(f"indicatorId duplicado: {iid}")
        seen_ids.add(iid)
        dept = str(item.get("departmentId") or "").strip()
        if dept and dept not in _ALLOWED_DEPARTMENTS:
            errors.append(f"departmentId inválido em {iid}: {dept}")
    return errors


def indicator_snake(indicator_id: str) -> str:
    return str(indicator_id or "").strip().replace("-", "_")


def operation_id_for(indicator_id: str, kind: str) -> str:
    return f"get_si_indicator_{indicator_snake(indicator_id)}_{kind}"


def path_for(indicator_id: str, kind: str) -> str:
    return f"/dashboard/indicators/{indicator_id}/{kind}"


def locale_labels(name: str, kind: str) -> dict[str, Any]:
    suffix_pt = "realizado" if kind == "realized" else "meta"
    suffix_en = "actual" if kind == "realized" else "goal"
    label_pt = f"{name} — {suffix_pt}"
    label_en = f"{name} — {suffix_en}"
    if kind == "realized":
        desc_pt = f"Valor realizado do indicador SI «{name}» (visão IGD)."
        desc_en = f"Actual value for SI indicator «{name}» (IGD view)."
        when_pt = f"Usar no card KPI do realizado de {name}."
        when_en = f"Use as a KPI card for the actual {name}."
    else:
        desc_pt = f"Meta (comparable goal) do indicador SI «{name}» (visão IGD)."
        desc_en = f"Goal (comparable) for SI indicator «{name}» (IGD view)."
        when_pt = f"Usar no card KPI da meta de {name}."
        when_en = f"Use as a KPI card for the {name} goal."
    return {
        "en": {
            "summary": label_en,
            "description": desc_en,
            "whenToUse": when_en,
            "label": label_en,
        },
        "pt-BR": {
            "summary": label_pt,
            "description": desc_pt,
            "whenToUse": when_pt,
            "label": label_pt,
        },
    }


def _audience_entry(*, name: str, kind: str, department_id: str) -> dict[str, Any]:
    labels = locale_labels(name, kind)
    return {
        "category": department_id,
        "locale": {
            "en": {
                "summary": labels["en"]["summary"],
                "description": labels["en"]["description"],
                "whenToUse": labels["en"]["whenToUse"],
                "label": labels["en"]["label"],
            },
            "pt-BR": {
                "summary": labels["pt-BR"]["summary"],
                "description": labels["pt-BR"]["description"],
                "whenToUse": labels["pt-BR"]["whenToUse"],
                "label": labels["pt-BR"]["label"],
            },
        },
    }


def sync_audience(catalog: dict) -> int:
    audience = json.loads(AUDIENCE_PATH.read_text(encoding="utf-8"))
    routes = audience.setdefault("routes", {})
    count = 0
    for item in catalog.get("indicators") or []:
        iid = str(item.get("indicatorId") or "").strip()
        name = str(item.get("name") or "").strip()
        dept = str(item.get("departmentId") or "").strip()
        for kind in ("realized", "meta"):
            op_id = operation_id_for(iid, kind)
            routes[op_id] = _audience_entry(name=name, kind=kind, department_id=dept)
            count += 1
    AUDIENCE_PATH.write_text(
        json.dumps(audience, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return count


def _baseline_operation(*, indicator_id: str, name: str, kind: str, department_id: str) -> dict[str, Any]:
    op_id = operation_id_for(indicator_id, kind)
    labels = locale_labels(name, kind)
    entity = (
        "dashboard_si_indicator_realized"
        if kind == "realized"
        else "dashboard_si_indicator_meta"
    )
    return {
        "method": "GET",
        "path": path_for(indicator_id, kind),
        "operationId": op_id,
        "summary": labels["en"]["summary"],
        "tags": ["Dashboard"],
        "deprecated": False,
        "parameters": [
            {
                "name": "competence",
                "required": False,
                "description": "Reference month as YYYY-MM.",
                "type": "string",
            },
            {
                "name": "start_date",
                "required": False,
                "description": "Period start (YYYY-MM-DD).",
                "type": "string",
                "format": "date",
            },
            {
                "name": "end_date",
                "required": False,
                "description": "Period end (YYYY-MM-DD).",
                "type": "string",
                "format": "date",
            },
            {
                "name": "branch",
                "required": False,
                "description": "TOTVS branch code (01/02) when applicable.",
                "type": "string",
            },
        ],
        "xDelpi": {
            "entity": entity,
            "shape": "scalar",
            "category": department_id,
            "locale": labels,
            "params": _PARAM_LOCALE,
            "tv": {
                "whenToUse": labels["pt-BR"]["whenToUse"],
                "description": labels["pt-BR"]["description"],
                "label": labels["pt-BR"]["label"],
            },
            "presentationStrategy": "as_delivered",
        },
        "description": labels["en"]["description"],
    }


def sync_baseline(catalog: dict) -> int:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    operations = baseline.get("operations")
    if not isinstance(operations, list):
        raise RuntimeError("openapi_baseline.json sem lista operations")

    wanted: dict[str, dict[str, Any]] = {}
    for item in catalog.get("indicators") or []:
        iid = str(item.get("indicatorId") or "").strip()
        name = str(item.get("name") or "").strip()
        dept = str(item.get("departmentId") or "").strip()
        for kind in ("realized", "meta"):
            op = _baseline_operation(
                indicator_id=iid, name=name, kind=kind, department_id=dept
            )
            wanted[op["operationId"]] = op

    kept: list[dict[str, Any]] = []
    seen: set[str] = set()
    for op in operations:
        if not isinstance(op, dict):
            continue
        op_id = str(op.get("operationId") or "").strip()
        if op_id.startswith("get_si_indicator_"):
            continue
        kept.append(op)
        if op_id:
            seen.add(op_id)

    for op_id, op in sorted(wanted.items()):
        kept.append(op)
        seen.add(op_id)

    baseline["operations"] = kept
    baseline["operation_count"] = len(kept)
    BASELINE_PATH.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(wanted)


def sync_inventory(catalog: dict) -> int:
    if not INVENTORY_PATH.is_file():
        return 0
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    items = inventory.get("operations")
    if not isinstance(items, list):
        items = inventory.get("items")
    if not isinstance(items, list):
        return 0

    existing_ids = {
        str(row.get("operationId") or "").strip()
        for row in items
        if isinstance(row, dict)
    }
    added = 0
    for item in catalog.get("indicators") or []:
        iid = str(item.get("indicatorId") or "").strip()
        for kind in ("realized", "meta"):
            op_id = operation_id_for(iid, kind)
            if op_id in existing_ids:
                continue
            items.append(
                {
                    "operationId": op_id,
                    "path": path_for(iid, kind),
                    "method": "GET",
                    "tag": "Dashboard",
                    "stable": True,
                }
            )
            existing_ids.add(op_id)
            added += 1

    key = "operations" if "operations" in inventory else "items"
    inventory[key] = items
    inventory["operationCount"] = len(items)
    inventory["stableCount"] = sum(
        1 for row in items if isinstance(row, dict) and row.get("stable")
    )
    INVENTORY_PATH.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return added


def sync_test_operation_ids(catalog: dict) -> int:
    """Gera literals em tests/ para audit_route_test_coverage (substring)."""
    lines = [
        '"""operationIds SI TV — gerado por sync_si_indicator_tv_catalog.py."""',
        "",
        "SI_INDICATOR_TV_OPERATION_IDS: tuple[str, ...] = (",
    ]
    count = 0
    for item in catalog.get("indicators") or []:
        iid = str(item.get("indicatorId") or "").strip()
        for kind in ("realized", "meta"):
            op_id = operation_id_for(iid, kind)
            lines.append(f'    "{op_id}",')
            count += 1
    lines.append(")")
    lines.append("")
    TESTS_SUPPORT_OPS.parent.mkdir(parents=True, exist_ok=True)
    TESTS_SUPPORT_OPS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--sync-artifacts",
        action="store_true",
        help="Atualiza tv_route_audience, openapi_baseline e inventory a partir do catálogo",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not CATALOG_PATH.is_file():
        print(f"Catálogo ausente: {CATALOG_PATH}", file=sys.stderr)
        return 1

    payload = load_catalog()
    errors = validate_catalog(payload)
    report: dict[str, Any] = {
        "path": str(CATALOG_PATH),
        "indicatorCount": len(payload.get("indicators") or []),
        "routeCount": len(payload.get("indicators") or []) * 2,
        "errors": errors,
        "ok": not errors,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"si_indicator_tv_catalog: {report['indicatorCount']} indicadores "
            f"→ {report['routeCount']} rotas"
        )
        for err in errors:
            print(f"  ERR {err}", file=sys.stderr)

    if args.write and not errors:
        CATALOG_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Gravado {CATALOG_PATH}")

    if args.sync_artifacts and not errors:
        audience_n = sync_audience(payload)
        baseline_n = sync_baseline(payload)
        inventory_n = sync_inventory(payload)
        test_ops_n = sync_test_operation_ids(payload)
        print(
            f"Artifacts: audience={audience_n} baseline={baseline_n} "
            f"inventory_added={inventory_n} test_ops={test_ops_n}"
        )

    if args.check and errors:
        return 1
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
