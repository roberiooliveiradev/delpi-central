"""R09 Gate 041 — SHY/OP + BZ_CUSTD reverse-engineering probe (read-only).

Runs inside the api-delpi container (pyodbc + pyxlsb). For the artifact
lines the Slice-1 engine misses, this probe tests whether the historical
DLP204 sourced those MOD lines from the frozen-OP route (SHY) rather
than the cadastral route (SG2), and investigates BZ_CUSTD as the MOD
rate source — evidence only, no cost computation is activated.

Usage (container):
    python /tmp/r09_shy_probe.py /tmp/fat_mod.xlsb 2026-09
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict

import pyxlsb

sys.path.insert(0, "/app")

from app.infrastructure.persistence.totvs.base_repository import (
    BaseRepository,
)


def _f(v):
    if v in (None, ""):
        return None
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _load_artifact(path: str) -> list[dict]:
    rows = []
    with pyxlsb.open_workbook(path) as wb:
        for name in wb.sheets:
            branch = "01" if name.endswith("01") else "02"
            with wb.get_sheet(name) as sheet:
                header = None
                for row in sheet.rows():
                    vals = [c.v for c in row]
                    if header is None:
                        if vals and str(vals[0]).strip() == "PA":
                            header = vals
                        continue
                    if not vals or vals[0] in (None, ""):
                        continue
                    rows.append(
                        {
                            "branch": branch,
                            "pa": str(vals[0]).strip(),
                            "level": str(vals[1]).strip(),
                            "mod": str(vals[2]).strip(),
                            "qtdfat": _f(vals[4]),
                            "qty": _f(vals[6]),
                            "custo_unit": _f(vals[7]),
                            "custo_total": _f(vals[8]),
                            "hours": _f(vals[10]),
                        }
                    )
    return rows


def main() -> int:
    artifact = _load_artifact(sys.argv[1])
    period = sys.argv[2]  # '2026-09'
    pstart, pend = period.replace("-", "") + "01", "20260930"

    out = {"shy_probe": [], "bz_probe": {}, "sg2_missing_probe": []}

    with BaseRepository() as r:
        # -- A. SG1 children of a few missing anchors -----------------------
        anchors = {
            ("01", "70260033"),
            ("01", "90264270"),
            ("01", "90350415"),
            ("02", "90480117"),
        }
        for branch, pa in sorted(anchors):
            kids = r.execute_query(
                "SELECT RTRIM(G1_COMP) c, CAST(G1_QUANT AS FLOAT) q "
                "FROM SG1010 WHERE D_E_L_E_T_=' ' AND G1_FILIAL=? "
                "AND G1_COD=?",
                (branch, pa.ljust(15)),
            )
            row = {"pa": pa, "branch": branch, "children": []}
            # include the anchor itself for level-02 diagnosis
            for prod in [pa] + [k["c"] for k in kids]:
                sg2 = r.execute_query(
                    "SELECT RTRIM(G2_OPERAC) op, "
                    "RTRIM(G2_RECURSO) res, "
                    "TRY_CAST(REPLACE(LTRIM(RTRIM(G2_TEMPAD)),',','.') "
                    "AS FLOAT) t "
                    "FROM SG2010 WHERE D_E_L_E_T_=' ' "
                    "AND G2_FILIAL IN ('',?) AND G2_CODIGO='01' "
                    "AND G2_PRODUTO=?",
                    (branch, prod.ljust(15)),
                )
                sc2 = r.execute_query(
                    "SELECT RTRIM(C2_OP) op, RTRIM(C2_NUM) n, "
                    "RTRIM(C2_ITEM) i, RTRIM(C2_SEQUEN) s, "
                    "RTRIM(C2_EMISSAO) e, CAST(C2_QUANT AS FLOAT) q "
                    "FROM SC2010 WHERE D_E_L_E_T_=' ' "
                    "AND C2_FILIAL=? AND C2_PRODUTO=? "
                    "ORDER BY C2_EMISSAO DESC",
                    (branch, prod.ljust(15)),
                )
                shy_ops = []
                for op in sc2[:2]:
                    shy = r.execute_query(
                        "SELECT RTRIM(HY_OPERAC) op, "
                        "RTRIM(HY_RECURSO) res, "
                        "TRY_CAST(REPLACE(LTRIM(RTRIM(HY_TEMPAD)),',','.') "
                        "AS FLOAT) t "
                        "FROM SHY010 WHERE D_E_L_E_T_=' ' "
                        "AND HY_FILIAL=? AND HY_OP=?",
                        (branch, op["op"].ljust(11)),
                    )
                    shy_ops.append(
                        {"c2_op": op["op"], "c2_q": op["q"],
                         "c2_emissao": op["e"], "shy": shy}
                    )
                row["children"].append(
                    {
                        "prod": prod,
                        "sg2_ops": len(sg2),
                        "sg2_res": [o["res"] for o in sg2],
                        "sc2_count": len(sc2),
                        "sc2_top": [
                            {"op": o["op"], "e": o["e"], "q": o["q"]}
                            for o in sc2[:2]
                        ],
                        "shy_per_op": shy_ops,
                    }
                )
            out["sg2_missing_probe"].append(row)

        # -- B. BZ_CUSTD vs artifact rate ----------------------------------
        sample = [a for a in artifact if a["custo_unit"] not in (None, 0)][
            :400
        ]
        mods = sorted({a["mod"] for a in sample})
        bz_rows = {}
        for mod in mods:
            rows = r.execute_query(
                "SELECT RTRIM(BZ_FILIAL) f, RTRIM(BZ_DATREF) d, "
                "CAST(BZ_CUSTD AS FLOAT) c "
                "FROM SBZ010 WHERE D_E_L_E_T_=' ' "
                "AND BZ_COD=? ORDER BY BZ_DATREF DESC",
                (mod.ljust(15),),
            )
            bz_rows[mod] = rows[:3]
        out["bz_probe"] = {
            "mods_checked": len(mods),
            "rows_per_mod": bz_rows,
        }

        # -- C. artifact rate vs BZ as-of ----------------------------------
        compared = []
        for a in sample[:120]:
            rows = r.execute_query(
                "SELECT TOP 1 RTRIM(BZ_FILIAL) f, RTRIM(BZ_DATREF) d, "
                "CAST(BZ_CUSTD AS FLOAT) c "
                "FROM SBZ010 WHERE D_E_L_E_T_=' ' "
                "AND BZ_COD=? AND BZ_FILIAL=? "
                "AND BZ_DATREF <= '20260930' "
                "ORDER BY BZ_DATREF DESC",
                (a["mod"].ljust(15), a["branch"]),
            )
            bz = rows[0]["c"] if rows else None
            compared.append(
                {
                    "pa": a["pa"],
                    "mod": a["mod"],
                    "branch": a["branch"],
                    "art_rate": a["custo_unit"],
                    "bz_asof": bz,
                    "match": (
                        bz is not None
                        and abs(bz - a["custo_unit"]) < 0.02
                    ),
                }
            )
        out["bz_compare"] = compared
        out["bz_match_count"] = sum(1 for c in compared if c["match"])
        out["bz_total"] = len(compared)

    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
