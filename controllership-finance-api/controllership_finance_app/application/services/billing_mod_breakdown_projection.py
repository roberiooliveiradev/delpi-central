"""R09 governed projection — billing × MOD breakdown (doc 142/143/144).

The BFF attaches the historical-parity evidence block and the mandatory
officiality markers. Nothing here recomputes Protheus data: values come
verbatim from the api-delpi producer; the evidence is a static reference
to the documented Gate-042 measurement (it is NOT a live parity score —
other competences have no measured baseline).
"""

from __future__ import annotations

from typing import Any

OFFICIALITY_OPERATIONAL_VIEW = "operational_view"
OFFICIAL_PARITY_PENDING = "pending"

# Gate-042 deterministic comparison (doc 144 §E) — historical evidence
# for competence 2026-09 only, never a dynamic score.
_PARITY_EVIDENCE_2026_09 = {
    "scope": {
        "referencePeriod": "2026-09",
        "branches": ["01", "02"],
        "artifact": "Fat x MOD.xlsb (DLP204)",
        "measuredAt": "2026-11-01",
        "gate": "G042 (doc 144)",
        "homologationStatus": "pending (DR-3, Controladoria)",
    },
    "metrics": {
        "artifactLines": 4476,
        "calculatedLines": 4659,
        "matchedKeys": 3694,
        "keyCoveragePct": 82.5,
        "qtdFatCorrectPct": 99.6,
        "stdTimeCorrectPct": 82.2,
        "hoursCorrectPct": 81.9,
        "missingLines": 782,
        "extraLines": 965,
    },
    "semantics": (
        "Historical point-in-time comparison between the reconstructed "
        "engine and the DLP204 artifact for 2026-09; not a live score "
        "and not extendable to other competences."
    ),
}

_LIMITATIONS = (
    "A seleção do roteiro congelado (última OP com SHY) pode divergir "
    "do snapshot histórico usado pelo DLP204 — divergências residuais "
    "de roteiro, quantidade e horas foram medidas e têm owner.",
    "A taxa histórica de MOD não foi localizada (BZ_CUSTD rejeitado, "
    "SP ausente): costUnit/costTotal/costProduct são ausência tipada, "
    "nunca zero.",
    "Paridade oficial pendente de homologação item a item pela "
    "Controladoria (DR-3). Esta é uma visão operacional, não o "
    "relatório oficial.",
)


def build_billing_mod_breakdown_projection(data: dict[str, Any]) -> dict:
    """Merge producer payload with the governed officiality + evidence.

    ``data`` is the raw ``data`` node from the api-delpi envelope. The
    parity evidence is attached only for the measured competence — for
    any other period the consumer sees the block explicitly marked as
    reference-only (it is the same static evidence, labeled by scope).
    """
    projected = dict(data)
    projected["officiality"] = OFFICIALITY_OPERATIONAL_VIEW
    projected["officialParity"] = OFFICIAL_PARITY_PENDING
    projected["parityEvidence"] = dict(_PARITY_EVIDENCE_2026_09)
    limitations = list(_LIMITATIONS)
    limitations.extend(data.get("limitations") or [])
    projected["limitations"] = limitations
    return projected
