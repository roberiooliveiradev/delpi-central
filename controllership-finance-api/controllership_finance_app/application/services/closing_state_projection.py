"""Governed closing-state projection (R12/R15, doc 129 §2.2).

Composes the api-delpi raw markers (SB9010, SX6 MV_ULMES, TTAT windows)
into independent state nodes — approved semantic (C3-D02=A, doc 89):
never collapse nodes into "closed", never infer execution or human
acceptance. `wizard_lifecycle` stays `unavailable` (E12.5) and
`human_acceptance` `not_informed` (C3-D05). ERP writes are out of scope
by contract (doc 118 §13).
"""

from __future__ import annotations

OFFICIALITY = "technical_markers"

_BASE_LIMITATIONS = (
    "Marcadores técnicos observados — não são homologação humana (G6) "
    "nem prova de execução concluída.",
    "Escritor de SB9/MV_ULMES não auditável (E5) — SX6/SB9 sem TTAT.",
    "Ciclo de vida do wizard indisponível — tabela não identificada "
    "(E12.5); SPs pós-MATA330 ausentes (E4).",
    "Carimbos físicos I_N_S_D_T_/TTAT_DTIME são UTC (-3h local).",
)


def _node(state: str, *, evidence: dict | None = None,
          limitations: list[str] | None = None) -> dict:
    return {
        "state": state,
        "evidenceRefs": evidence or {},
        "limitations": limitations or [],
    }


def build_closing_state_projection(
    *, period: str, reference_date: str, branch_payloads: dict,
) -> dict:
    """api-delpi branch payloads -> governed nodes per branch."""
    if not reference_date:
        return {}
    snapshot_marker = reference_date.replace("-", "")
    branches: dict[str, dict] = {}
    for code, payload in (branch_payloads or {}).items():
        marker = (payload.get("cutoffMarker") or {})
        snap = (payload.get("snapshot") or {})
        evidence = (payload.get("evidence") or {})

        # --- snapshot node -------------------------------------------------
        if snap.get("available"):
            snap_state = "available"
        elif snap.get("lastAvailableDate"):
            snap_state = "missing"
        else:
            snap_state = "unavailable"

        # --- cutoff marker node --------------------------------------------
        ulmes = (marker.get("value") or "").strip() or None
        if ulmes is None:
            cutoff_state = "unavailable"
        elif ulmes >= snapshot_marker:
            cutoff_state = "observed"
        else:
            cutoff_state = "not_advanced"

        # --- cost evidence node (TTAT write windows) -----------------------
        rep = evidence.get("replacementCostWrites") or {}
        mov = evidence.get("movementCostWrites") or {}
        evidence_rows = []
        for row in (rep, mov):
            if row.get("writeCount"):
                evidence_rows.append(
                    {
                        "source": row.get("source"),
                        "writeCount": row.get("writeCount"),
                        "firstAt": row.get("firstAt"),
                        "lastAt": row.get("lastAt"),
                    }
                )
        cost_state = "observed" if evidence_rows else "unavailable"

        branches[code] = {
            "snapshot": _node(
                snap_state,
                evidence={
                    "source": "SB9010.B9_DATA",
                    "date": snap.get("date"),
                    "rowCount": snap.get("rowCount"),
                    "lastAvailableDate": snap.get("lastAvailableDate"),
                },
            ),
            "cutoff_marker": _node(
                cutoff_state,
                evidence={
                    "source": marker.get("source") or "SX6010.MV_ULMES",
                    "value": ulmes,
                    "expectedAtLeast": snapshot_marker,
                },
            ),
            "cost_evidence": _node(
                cost_state,
                evidence={"writes": evidence_rows},
                limitations=[
                    "Evidência de escrita TTAT não prova conclusão da "
                    "rotina — apenas atividade observada na janela."
                ],
            ),
            "wizard_lifecycle": _node(
                "unavailable",
                limitations=[
                    "Tabela do ciclo de vida do wizard não identificada "
                    "(E12.5) — estado nunca inferido."
                ],
            ),
            "human_acceptance": _node(
                "not_informed",
                limitations=[
                    "Homologação é processo humano (C3-D05/G6) — nunca "
                    "derivada de marcadores."
                ],
            ),
        }

    return {
        "period": period,
        "referenceDate": reference_date,
        "officiality": OFFICIALITY,
        "branches": branches,
        "limitations": list(_BASE_LIMITATIONS),
    }
