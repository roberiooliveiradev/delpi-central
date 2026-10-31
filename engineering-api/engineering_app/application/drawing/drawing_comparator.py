"""Multi-source comparison engine (doc 71 G3).

Confronts UNTRUSTED visual observations with (a) the independent
text-layer extraction of the SAME verified document, and (b) official
product/BOM facts — never promoting hypothesis to fact, never declaring
absence from non-observation.
"""

from __future__ import annotations

import re
from typing import Any

from engineering_app.domain.drawing.source_identity import SourceMatch
from engineering_app.domain.drawing.visual_observation import (
    DrawingVisualObservation,
)

_DIGITS = re.compile(r"\d+[\d.,]*")


def _norm(text: str) -> str:
    return " ".join(str(text).upper().split())


def compare_observation_to_text(
    obs: DrawingVisualObservation, text_blob: str
) -> dict[str, Any]:
    """Compare one observation against the text layer of the SAME doc."""
    blob = _norm(text_blob)
    value = _norm(obs.normalized_value or obs.raw_observation)
    result: dict[str, Any] = {
        "observation_id": obs.observation_id,
        "kind": obs.kind,
        "page": obs.page,
        "status": "no_evidence",
        "detail": None,
    }
    if obs.kind == "revision":
        candidates = _DIGITS.findall(value) or [value]
        if any(_norm(c) in blob for c in candidates if c):
            result["status"] = "agreement"
        else:
            # Ausência textual não é contradição (R3-C): revisão pode
            # constar apenas graficamente ou com formatação distinta.
            result["status"] = "not_found_in_text"
            result["detail"] = (
                "revisão observada não localizada na camada de texto — "
                "ausência textual, não contradição"
            )
        return result
    # generic: strong token presence
    tokens = [
        t
        for t in re.split(r"[\s,;:/|()]+", value)
        if len(t) >= 4 or t.isdigit()
    ][:12]
    if not tokens:
        return result
    hits = [t for t in tokens if t in blob]
    coverage = len(hits) / len(tokens)
    if coverage >= 0.6:
        result["status"] = "agreement"
    elif hits:
        result["status"] = "partial"
        result["detail"] = f"{len(hits)}/{len(tokens)} tokens confirmados"
    else:
        # R3-C: nenhum token confirmado != contradição; conflito exige
        # evidências explícitas e comparáveis que se contradigam.
        result["status"] = "not_found_in_text"
        result["detail"] = (
            "nenhum token confirmado na camada de texto — ausência de "
            "texto não é ausência no desenho (indício apenas)"
        )
    return result


_LABEL_ROLES = [
    (re.compile(r"(?i:\bCOD\b)\D{0,15}(\d[0-9A-Z.\-]{4,})"),
     "customer_reference"),
    (re.compile(r"(?i:\bDES\b)\D{0,15}(\d[0-9A-Z.\-]{4,})"),
     "drawing_code"),
    (re.compile(r"(?i:\b(?:PRODUTO|PRODUCT)\b)\D{0,15}(\d[0-9A-Z.\-]{4,})"),
     "product_code"),
    (re.compile(r"(?i:\b(?:REF|REFER[ÊE]NCIA)\b)\D{0,15}(\d[0-9A-Z.\-]{4,})"),
     "customer_reference"),
]


def _label_classified_identifiers(value: str) -> list[dict[str, str]]:
    """Legacy text → typed identifiers by documented labels (R4-A)."""
    out: list[dict[str, str]] = []
    for pattern, role in _LABEL_ROLES:
        for m in pattern.finditer(value):
            v = m.group(1).strip(" .,;:")
            if v:
                out.append({"role": role, "value": v})
    labeled = {i["value"] for i in out}
    for m in _DIGITS.finditer(value):
        v = m.group(0)
        if v not in labeled and len(v) >= 6:
            out.append({"role": "unknown_identifier", "value": v})
    return out


def compare_observation_to_official(
    obs: DrawingVisualObservation,
    *,
    official_code: str,
    official_revision: str | None,
    official_description: str,
    bom_codes: set[str],
) -> dict[str, Any]:
    """Compare one observation against official facts."""
    value = _norm(obs.normalized_value or obs.raw_observation)
    out: dict[str, Any] = {
        "observation_id": obs.observation_id,
        "status": "no_evidence",
        "detail": None,
    }
    if obs.kind == "revision":
        nums = _DIGITS.findall(value)
        rev = nums[0] if nums else value
        if official_revision:
            out["status"] = (
                "agreement" if rev == _norm(official_revision)
                else "conflict"
            )
            if out["status"] == "conflict":
                out["detail"] = (
                    f"revisão observada '{rev}' × oficial "
                    f"'{official_revision}'"
                )
        return out
    if obs.kind == "identification":
        # R4-A: comparar somente identificadores da mesma função —
        # product_code×code, drawing_code×drawing, customer_reference×ref.
        typed = obs.identifiers or _label_classified_identifiers(value)
        role_map = {
            "product_code": official_code,
            "customer_reference": None,  # sem contrato comparável direto
            "drawing_code": bom_codes.pop() if False else None,
        }
        agreements, conflicts, seen_codes = 0, 0, []
        for ident in typed:
            role, val = ident.get("role"), ident.get("value")
            if role == "product_code" and val:
                seen_codes.append(val)
                if val == official_code:
                    agreements += 1
                else:
                    conflicts += 1
            elif role == "drawing_code" and val:
                out.setdefault("typed_results", {})[role] = val
            elif role == "customer_reference" and val:
                out.setdefault("typed_results", {})[role] = val
        if agreements:
            out["status"] = "agreement"
        elif conflicts:
            out["status"] = "conflict"
            out["detail"] = (
                f"product_code observado {seen_codes} × oficial "
                f"{official_code}"
            )
        else:
            out["status"] = "no_evidence"
        return out
    if obs.kind == "bom_item":
        codes = [c for c in _DIGITS.findall(value) if len(c) >= 6]
        if codes and any(c in bom_codes for c in codes):
            out["status"] = "agreement"
        elif codes:
            out["status"] = "possible_divergence"
            out["detail"] = (
                f"códigos {codes} observados não constam na BOM oficial "
                "— indício, exige revisão"
            )
        return out
    return out


def evaluate_source_match(
    observations: list[DrawingVisualObservation],
    *,
    official_hash: str | None,
    official_revision: str | None,
    official_document_ref: str | None,
    official_product_code: str | None,
) -> SourceMatch:
    """Most-conclusive identity across observations carrying identity."""
    best = SourceMatch.UNKNOWN
    rank = {
        SourceMatch.DIFFERENT_DOCUMENT: 3,
        SourceMatch.SAME_DOCUMENT_VERIFIED: 2,
        SourceMatch.POSSIBLE_MATCH: 1,
        SourceMatch.UNKNOWN: 0,
    }
    for obs in observations:
        ident = obs.document_identity
        match = _classify(
            attachment_hash=ident.document_hash,
            attachment_revision=ident.revision,
            attachment_document_ref=ident.document_ref,
            attachment_product_code=ident.product_code,
            official_hash=official_hash,
            official_revision=official_revision,
            official_document_ref=official_document_ref,
            official_product_code=official_product_code,
        )
        if rank[match] > rank[best]:
            best = match
    return best


def _classify(**kw: Any) -> SourceMatch:
    from engineering_app.domain.drawing.source_identity import (
        classify_source_match,
    )

    return classify_source_match(**kw)
