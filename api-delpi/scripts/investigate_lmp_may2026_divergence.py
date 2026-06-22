#!/usr/bin/env python3
"""Investiga divergência dashboard LMP maio/2026 vs controle interno (17 pastas)."""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.composition.engineering_composer import (
    build_engineering_get_lmp_history_events_use_case,
    build_engineering_get_lmp_use_case,
    build_engineering_list_lmps_dashboard_use_case,
)
from app.interface.http.routes.engineering.lmp_route_helpers import (
    build_get_lmp_history_request,
    build_get_lmp_request,
    build_list_lmp_request,
)

PERIOD_START = "2026-05-01"
PERIOD_END = "2026-05-31"

_DATA_PATH = Path(__file__).resolve().parent / "data" / "lmp_may2026_internal_control_ovs.json"


def _load_internal_control_rows() -> list[dict[str, Any]]:
    rows = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    for row in rows:
        open_raw = row["abertura"].replace("-", "")
        ov_raw = (row.get("ov") or "").strip()
        ovs = [part.strip() for part in ov_raw.split(",") if part.strip()]
        entry: dict[str, Any] = {
            "item": row["item"],
            "code": row["lmp_ano"],
            "ov": ov_raw,
            "ovs": ovs,
            "client": row["cliente"],
            "open": open_raw,
            "ovs_fonte": row.get("ovs_fonte"),
            "observacao": row.get("observacao"),
        }
        ref_match = re.search(r"\b(\d{8})\b", row["cliente"])
        if ref_match:
            entry["ref"] = ref_match.group(1)
        out.append(entry)
    return out


INTERNAL_CONTROL = _load_internal_control_rows()

HYPOTHESIS_MAP = {row["code"]: row["ovs"] for row in INTERNAL_CONTROL}

# OVs no dashboard maio sem pasta no controle (000102 e 000061 também mapeadas acima)
EXTRAS_IN_DASHBOARD = ["000087", "003561", "002871", "003578", "000120"]


def _fmt_date(raw: str | None) -> str:
    if not raw or len(raw) != 8:
        return raw or ""
    return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]}"


def _anchor_events(history: dict[str, Any]) -> list[dict[str, Any]]:
    items = history.get("items") or []
    anchors = []
    for ev in items:
        stage = (ev.get("stage_code") or "").strip()
        process = (ev.get("process_code") or "").strip()
        if stage in ("000003", "000012") and process in ("000002", "000003"):
            anchors.append(
                {
                    "revision": ev.get("revision"),
                    "process": process,
                    "stage": stage,
                    "stage_label": ev.get("stage_label"),
                    "start": ev.get("start_date"),
                    "end": ev.get("end_date"),
                    "is_engineering": ev.get("is_engineering"),
                }
            )
    return anchors


def _first_eng_event(history: dict[str, Any]) -> dict[str, Any] | None:
    items = history.get("items") or []
    eng = [ev for ev in items if ev.get("is_engineering") and ev.get("start_date")]
    if not eng:
        return None
    eng.sort(key=lambda e: (e.get("start_date") or "", e.get("start_time") or ""))
    ev = eng[0]
    return {
        "start": ev.get("start_date"),
        "stage_label": ev.get("stage_label"),
        "revision": ev.get("revision"),
    }


def _in_period(date_raw: str | None) -> bool:
    if not date_raw or len(date_raw) != 8:
        return False
    start = PERIOD_START.replace("-", "")
    end = PERIOD_END.replace("-", "")
    return start <= date_raw <= end


def _investigate_ov(
    sale_number: str,
    *,
    get_uc,
    hist_uc,
    dashboard_item: dict[str, Any] | None,
) -> dict[str, Any]:
    branch = (dashboard_item or {}).get("branch")
    detail = None
    history = None
    errors: list[str] = []

    for br in ([branch] if branch else ["01", "02"]):
        try:
            req = build_get_lmp_request(
                sale_number,
                date_start=PERIOD_START,
                date_end=PERIOD_END,
                branch=br,
            )
            detail = get_uc.execute(req)
            hist_req = build_get_lmp_history_request(
                sale_number,
                date_start=PERIOD_START,
                date_end=PERIOD_END,
                branch=br,
            )
            history = hist_uc.execute(hist_req)
            branch = br
            break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"filial {br}: {exc}")

    first_eng = _first_eng_event(history) if history else None
    anchors = _anchor_events(history) if history else []
    anchor_start = (dashboard_item or {}).get("start_date") or (detail or {}).get("start_date")
    anchor_end = (dashboard_item or {}).get("end_date") or (detail or {}).get("end_date")

    inclusion_reason = []
    if _in_period(anchor_start):
        inclusion_reason.append("anchor_no_mes")
    if first_eng and _in_period(first_eng.get("start")):
        inclusion_reason.append("first_eng_no_mes")
    if not inclusion_reason:
        inclusion_reason.append("desconhecido")

    products = []
    if detail:
        for p in detail.get("list_products") or []:
            code = (p.get("product_code") or p.get("code") or "").strip()
            if code:
                products.append(code)

    return {
        "sale_number": sale_number,
        "branch": branch,
        "description": (detail or dashboard_item or {}).get("sale_description", ""),
        "listing_kind": (detail or dashboard_item or {}).get("listing_kind"),
        "anchor_start": anchor_start,
        "anchor_start_fmt": _fmt_date(anchor_start),
        "anchor_end": anchor_end,
        "anchor_end_fmt": _fmt_date(anchor_end),
        "control_open_mismatch_days": None,
        "first_eng": first_eng,
        "inclusion_reason": inclusion_reason,
        "anchor_events_count": len(anchors),
        "last_anchor": anchors[-1] if anchors else None,
        "products": products[:8],
        "engineering_status": (detail or dashboard_item or {}).get("engineering_status"),
        "qtd_pi": (detail or dashboard_item or {}).get("qtd_pi"),
        "errors": errors,
    }


def main() -> None:
    dash_uc = build_engineering_list_lmps_dashboard_use_case()
    get_uc = build_engineering_get_lmp_use_case()
    hist_uc = build_engineering_get_lmp_history_events_use_case()

    dto = build_list_lmp_request(
        date_start=PERIOD_START,
        date_end=PERIOD_END,
        listing_type="LMP",
        page_size=500,
    )
    dashboard_items = {
        it["sale_number"]: it
        for it in dash_uc.execute_items(dto, status_filter="Todos")["items"]
    }

    may_anchor = [ov for ov, it in dashboard_items.items() if (it.get("start_date") or "") <= "20260531"]
    june_anchor = [ov for ov, it in dashboard_items.items() if (it.get("start_date") or "") > "20260531"]

    all_ovs = sorted(dashboard_items.keys())
    mapped_ovs = {ov for ovs in HYPOTHESIS_MAP.values() for ov in ovs}

    report: dict[str, Any] = {
        "period": {"start": PERIOD_START, "end": PERIOD_END},
        "totals": {
            "dashboard_lmp": len(dashboard_items),
            "may_anchor_only": len(may_anchor),
            "june_anchor_in_may_filter": len(june_anchor),
            "internal_control_folders": len(INTERNAL_CONTROL),
        },
        "categories": {},
        "items": {},
    }

    # Investigate each category
    categories = {
        "A_extras_sem_pasta_controle": EXTRAS_IN_DASHBOARD,
        "B_wanke_multi_ov": ["000088", "000089", "000095", "000102"],
        "C_junho_no_filtro_maio": june_anchor,
        "D_mapeadas_controle": sorted(mapped_ovs),
    }

    for cat, ovs in categories.items():
        report["categories"][cat] = []
        for ov in ovs:
            inv = _investigate_ov(ov, get_uc=get_uc, hist_uc=hist_uc, dashboard_item=dashboard_items.get(ov))
            report["categories"][cat].append(inv)
            report["items"][ov] = inv

    # Missing 072 - search OVs by product refs from control
    import pyodbc
    import os

    missing = []
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={os.environ['DB_HOST']},"
        f"{os.environ['DB_PORT']};DATABASE={os.environ['DB_DATABASE']};"
        f"UID={os.environ['DB_USER']};PWD={os.environ['DB_PASSWORD']};TrustServerCertificate=yes;"
    )
    cur = conn.cursor()
    for row in INTERNAL_CONTROL:
        if row["code"] == "072 26":
            for ref in ("19381065", "19373355"):
                cur.execute(
                    """
                    SELECT DISTINCT ADJ.ADJ_NROPOR, ADJ.ADJ_FILIAL, AD1.AD1_DESCRI
                    FROM ADJ010 ADJ
                    INNER JOIN AD1010 AD1
                      ON AD1.AD1_FILIAL = ADJ.ADJ_FILIAL
                     AND AD1.AD1_NROPOR = ADJ.ADJ_NROPOR
                     AND AD1.D_E_L_E_T_ = ''
                    WHERE ADJ.D_E_L_E_T_ = '' AND ADJ.ADJ_PROD LIKE ?
                    """,
                    ref + "%",
                )
                hits = [(r[0].strip(), r[1].strip(), r[2][:50]) for r in cur.fetchall()]
                missing.append({"ref": ref, "folder": row["code"], "adj_hits": hits})

        ref = row.get("ref")
        if ref:
            cur.execute(
                """
                SELECT DISTINCT ADJ.ADJ_NROPOR, ADJ.ADJ_FILIAL
                FROM ADJ010 ADJ WHERE ADJ.D_E_L_E_T_ = '' AND ADJ.ADJ_PROD LIKE ?
                """,
                ref + "%",
            )
            hits = [(r[0].strip(), r[1].strip()) for r in cur.fetchall()]
            row["adj_ov_hits"] = hits

    report["categories"]["E_pasta_072_ausente"] = missing
    report["internal_refs_adj"] = [
        {k: v for k, v in r.items() if k in ("code", "client", "open", "ref", "adj_ov_hits")}
        for r in INTERNAL_CONTROL
        if r.get("ref")
    ]
    conn.close()

    # Verdict per item
    verdicts = []
    for ov in all_ovs:
        inv = report["items"].get(ov) or _investigate_ov(
            ov, get_uc=get_uc, hist_uc=hist_uc, dashboard_item=dashboard_items.get(ov)
        )
        if ov in EXTRAS_IN_DASHBOARD:
            verdict = "ERRO_REGISTRO_OU_CONTROLE_INCOMPLETO"
            note = "OV LMP válida no Protheus; não consta no controle interno maio/2026"
        elif ov in ("000088", "000089", "000095", "000102"):
            verdict = "REGISTRO_MULTIPLAS_OVS"
            note = "Pasta Wanke (073): RQ-060 cita 000102; Protheus também 088/089/095"
        elif ov in june_anchor:
            if "first_eng_no_mes" in inv["inclusion_reason"] and "anchor_no_mes" not in inv["inclusion_reason"]:
                verdict = "FILTRO_SQL_FIRST_ENG"
                note = "Entrou no mês por OR first_eng; âncora LMP fora de maio — divergência de critério de data"
            else:
                verdict = "FILTRO_SQL_OU_REGISTRO"
                note = "Âncora fora de maio; revisar first_eng e eventos AIJ"
        elif ov not in mapped_ovs:
            verdict = "INVESTIGAR"
            note = "Não mapeada na hipótese inicial"
        else:
            verdict = "ALINHADO_CONTROLE"
            note = "OV esperada no controle interno"

        verdicts.append({"ov": ov, "verdict": verdict, "note": note, **{k: inv[k] for k in ("anchor_start_fmt", "first_eng", "inclusion_reason")}})

    report["verdicts"] = verdicts
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
