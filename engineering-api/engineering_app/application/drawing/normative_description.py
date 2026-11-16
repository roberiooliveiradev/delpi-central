"""G24 — Reusable normative technical-description evaluation (PI/MP).

Evaluates ONE description from ONE source (DRAWING | TOTVS | CANDIDATE)
against the governed DELPI norms, returning per-rule explainable
results. Deterministic first; it never fabricates fields, never
extends a norm beyond its ratified scope and never approves anything —
all findings are DRAFT/CANDIDATE pending Engineering review.

Norm sources (corpus governed knowledge V2, freeze-002):
  * api-delpi/docs/api/padroes-totvs/codigos-intermediarios-pi.md
  * api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md
"""

from __future__ import annotations

import re
from typing import Any

from .description_rules import (
    _PI_ISOLATION,
    is_pi50_code,
    parse_pi50_segments,
)

NORMATIVE_CONTRACT_VERSION = "normative_description.v1"

# Norm identity is pinned by content hash of the governed source doc
# (freeze davi-governed-knowledge-freeze-002). Rules never originate
# from this code — the norm doc is the authority; this is the engine.
NORM_REFS: dict[str, dict[str, str]] = {
    "PI_50XX": {
        "owner": "ENGENHARIA",
        "ref": "codigos-intermediarios-pi.md",
        "sha256": "ee81169ff50de767f6cbe7f84eedec993add0dd5b105b41e4805f8b966baf269",
        "applicability": "intermediate products, family 50xx",
    },
    "MP_CABLES_1001_1005": {
        "owner": "ENGENHARIA",
        "ref": "normas-tecnicas-descricao-materias-primas.md#1001-1005",
        "sha256": "66aa9c13e5666fc1e515ec743a925c322467578384ab90140290339e54424bd2",
        "applicability": "cables, groups 1001-1005",
    },
    "MP_TERMINAL_1008": {
        "owner": "ENGENHARIA",
        "ref": "normas-tecnicas-descricao-materias-primas.md#1008",
        "sha256": "66aa9c13e5666fc1e515ec743a925c322467578384ab90140290339e54424bd2",
        "applicability": "terminals FASTON/BANDEIRA, group 1008",
    },
    "MP_ISOLATOR_1009": {
        "owner": "ENGENHARIA",
        "ref": "normas-tecnicas-descricao-materias-primas.md#1009",
        "sha256": "66aa9c13e5666fc1e515ec743a925c322467578384ab90140290339e54424bd2",
        "applicability": "isolators, group 1009",
    },
}

_RULE_STATUS = (
    "PASS", "VIOLATION_CANDIDATE", "WARNING",
    "INCONCLUSIVE", "NOT_APPLICABLE", "OWNER_BLOCKED",
)
_SOURCES = ("DRAWING", "TOTVS", "CANDIDATE")

# Norm-documented color codes (PI norm, page 6) — closed table.
_PI_COLORS = {
    "AZUL", "BRAN", "LARA", "MARR", "ROSA", "VERD", "VIOL",
    "AMAR", "CINZ", "LILA", "PRET", "ROXO", "VERM",
}
# MP norm color convention: abbreviation of 1st and last letter
# (Preto=PT). Tokens below are the only observed/standard set; a
# non-matching token is INCONCLUSIVE, never fabricated.
_CABLE_MATERIALS = {
    "PVC", "XLPE", "SILICONE", "EPR", "PP", "ESPECIAL", "TEFLON",
}
_CABLE_CERTS = {"NBR", "IEC", "UL", "CSA", "ABNT", "ROHS", "CE", "VDE"}
_TERMINAL_TYPES = {"FASTON", "BANDEIRA"}
_TERMINAL_BATH = {"ESTANHADO", "NIQUELADO"}
_TERMINAL_PACK = {"GRANEL", "FITADO", "BLISTER"}
_ISOLATOR_MATERIALS = {"NYLON", "POLIPROPILENO", "PVC", "POLIURETANO"}
_ISOLATOR_ORIENT = {"RETO", "90"}
_ISOLATOR_CERTS = {"UL", "ROHS", "IEC", "ABNT", "DIN", "V2"}

_CABLE_GROUP = re.compile(r"^100[1-5]$")
_GROUP = re.compile(r"^(\d{4})")
_TEMP = re.compile(r"\b\d{2,3}(?:/\d{2,3})?\s*°?C\b")
_AWG = re.compile(r"\b(\d{1,2})\s*AWG\b")
_MM2 = re.compile(r"\b\d+([,.]\d+)?\s*MM2\b")
_MM_BARE = re.compile(r"\b\d+([,.]\d+)?\s*-\s*\d+([,.]\d+)?\s*MM\b")
_VOLT = re.compile(r"\b\d{2,4}(?:/\d{2,4})?\s*V\b")
_COLOR_ABBR = re.compile(r"\b(PT|BN|AZ|VD|VM|AM|LR|CZ|RS|BR|AL)\b")
_DIM_PAIR = re.compile(r"\b\d+([,.]\d+)?\s*[Xx]\s*\d+([,.]\d+)?\b")
_RANGE_MM2 = re.compile(r"\b\d+([,.]\d+)?\s*-\s*\d+([,.]\d+)?\s*(MM2|MM)\b")
_SERIE = re.compile(r"\b\d[,.]\d\b")


def _attr(name: str, raw: str | None, method: str,
         state: str, value: Any = None, unit: str | None = None) -> dict:
    return {
        "name": name,
        "raw_span": raw,
        "normalized_value": value if value is not None else raw,
        "unit": unit,
        "extraction_method": method,
        "state": state,  # EXTRACTED | ABSENT | AMBIGUOUS
    }


def _rule(rule_id: str, requirement: str, applicable: bool,
          status: str, observed: Any, expected: Any = None,
          reason: str | None = None) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "requirement": requirement,
        "applicable": applicable,
        "status": status,
        "observed": observed,
        "expected": expected,
        "reason": reason,
    }


def _evaluate_pi50(desc: str) -> dict[str, Any]:
    seg = parse_pi50_segments(desc)
    attrs: list[dict] = []
    rules: list[dict[str, Any]] = []
    if not seg:
        upper = (desc or "").upper()
        partial = re.search(r"(CA|CB|CF|CT|CV)", upper)
        attrs.append(_attr(
            "canonical_form", (desc or "")[:40],
            "pi50_strict_grammar", "AMBIGUOUS"))
        rules.append(_rule(
            "PI50-STRUCT-01", "canonical PI 50xx grammar "
            "ISO+gauge+COLOR4-LEN/decE/decD-TERM-TERM",
            True, "INCONCLUSIVE", desc,
            "ISO{gauge}{COLOR4}-{len}/{decE}/{decD}-{termEisoE}-{termDisoD}",
            "grammar not fully matched"
            + (f" — isolation-like token '{partial.group(1)}' present"
               if partial else "")))
        return attrs, rules
    for k in ("isolation_prefix", "gauge", "color", "length_mm",
              "decape_left_mm", "decape_right_mm", "terminal_left",
              "isolator_left", "terminal_right", "isolator_right"):
        attrs.append(_attr(k, str(seg.get(k)), "pi50_grammar", "EXTRACTED",
                           seg.get(k)))
    iso = seg["isolation_prefix"]
    rules.append(_rule(
        "PI50-ISO-01", "isolation code in {CA,CB,CF,CT,CV}", True,
        "PASS", iso, sorted(_PI_ISOLATION),
        f"material: {seg['isolation_material']}"))
    color = seg["color"]
    if color in _PI_COLORS:
        rules.append(_rule(
            "PI50-COLOR-01", "color is a documented 4-letter code", True,
            "PASS", color, sorted(_PI_COLORS)))
    else:
        rules.append(_rule(
            "PI50-COLOR-01", "color is a documented 4-letter code", True,
            "OWNER_BLOCKED", color, sorted(_PI_COLORS),
            "compound/undocumented color code — D2 alias pending "
            "Engineering ratification (e.g. MABR)"))
    rules.append(_rule(
        "PI50-GAUGE-01", "gauge segment present (AWG or mm2)", True,
        "PASS", seg["gauge"]))
    rules.append(_rule(
        "PI50-LEN-01", "cable length segment in mm", True,
        "PASS", seg["length_mm"], unit := "mm"))
    rules.append(_rule(
        "PI50-DECAPE-01", "left/right stripping segments in mm", True,
        "PASS", [seg["decape_left_mm"], seg["decape_right_mm"]],
        unit := "mm"))
    rules.append(_rule(
        "PI50-TERM-01", "left/right terminal+isolator code pairs", True,
        "PASS", [seg["terminal_left"], seg["isolator_left"],
                 seg["terminal_right"], seg["isolator_right"]],
        reason="structure only — physical position vs BOM requires "
               "authorized association (D4 pending)"))
    return attrs, rules


def _eval_cable(desc: str) -> dict[str, Any]:
    up = desc.upper()
    attrs: list[dict] = []
    rules: list[dict[str, Any]] = []
    tokens = set(re.findall(r"[A-ZÀ-Ú]{2,}", up)) | set(
        re.findall(r"[A-Z]+\d+", up))
    material = next((m for m in _CABLE_MATERIALS if m in tokens), None)
    temp = _TEMP.search(up)
    awg = _AWG.search(up)
    mm2 = _MM2.search(up)
    color = _COLOR_ABBR.search(up)
    volt = _VOLT.search(up)
    certs = sorted(c for c in _CABLE_CERTS if c in tokens or
                   re.search(rf"\b{c}\b", up))
    attrs += [
        _attr("material", material, "vocab", "EXTRACTED" if material else "ABSENT"),
        _attr("temperature", temp.group(0) if temp else None, "regex", "EXTRACTED" if temp else "ABSENT"),
        _attr("gauge", (awg or mm2).group(0) if (awg or mm2) else None, "regex", "EXTRACTED" if (awg or mm2) else "ABSENT", unit="AWG" if awg else "mm2" if mm2 else None),
        _attr("color", color.group(1) if color else None, "regex", "EXTRACTED" if color else "ABSENT"),
        _attr("voltage", volt.group(0) if volt else None, "regex", "EXTRACTED" if volt else "ABSENT"),
        _attr("certifications", ",".join(certs) or None, "vocab", "EXTRACTED" if certs else "ABSENT"),
    ]
    rules.append(_rule(
        "MP-CABO-PREFIX", "prefix ITEM = CABO", True,
        "PASS" if up.strip().startswith("CABO") else "VIOLATION_CANDIDATE",
        up.split()[0] if up.strip() else None, "CABO"))
    rules.append(_rule(
        "MP-CABO-MATERIAL", "insulation material from datasheet vocab",
        True, "PASS" if material else "INCONCLUSIVE",
        material, sorted(_CABLE_MATERIALS)))
    rules.append(_rule(
        "MP-CABO-GAUGE", "section in mm2 or AWG", True,
        "PASS" if (awg or mm2) else "INCONCLUSIVE",
        (awg or mm2).group(0) if (awg or mm2) else None, "mm2 or AWG"))
    rules.append(_rule(
        "MP-CABO-COLOR", "color as first+last letter abbreviation", True,
        "PASS" if color else "INCONCLUSIVE",
        color.group(1) if color else None, "PT,BN,AZ,VD,VM,AM,LR,CZ,RS,BR,AL"))
    rules.append(_rule(
        "MP-CABO-TEMP", "working temperature (°C)", True,
        "PASS" if temp else "INCONCLUSIVE",
        temp.group(0) if temp else None))
    rules.append(_rule(
        "MP-CABO-VOLT", "voltage class (V)", True,
        "PASS" if volt else "INCONCLUSIVE",
        volt.group(0) if volt else None))
    rules.append(_rule(
        "MP-CABO-CERT", "certification/norm tokens (NBR, IEC, UL...)",
        True, "PASS" if certs else "INCONCLUSIVE", certs))
    return attrs, rules


def _eval_terminal_1008(desc: str) -> dict[str, Any]:
    up = desc.upper()
    attrs: list[dict] = []
    rules: list[dict[str, Any]] = []
    tokens = set(re.findall(r"[A-ZÀ-Ú/]{2,}", up))
    ttype = next((t for t in _TERMINAL_TYPES if t in tokens), None)
    dim = _DIM_PAIR.search(up)
    rng = _RANGE_MM2.search(up)
    bath = next((b for b in _TERMINAL_BATH if b in tokens), None)
    iso = ("C/ISOLACAO" if "C/ISOLACAO" in up.replace("Ç", "C")
           else "S/ISOLACAO" if "S/ISOLACAO" in up.replace("Ç", "C")
           else None)
    pack = next((p for p in _TERMINAL_PACK if p in tokens), None)
    attrs += [
        _attr("terminal_type", ttype, "vocab", "EXTRACTED" if ttype else "ABSENT"),
        _attr("dimensions", dim.group(0) if dim else None, "regex", "EXTRACTED" if dim else "ABSENT", unit="mm"),
        _attr("gauge_range", rng.group(0) if rng else None, "regex", "EXTRACTED" if rng else "ABSENT"),
        _attr("plating", bath, "vocab", "EXTRACTED" if bath else "ABSENT"),
        _attr("insulation_flag", iso, "vocab", "EXTRACTED" if iso else "ABSENT"),
        _attr("packaging", pack, "vocab", "EXTRACTED" if pack else "ABSENT"),
    ]
    rules.append(_rule(
        "MP-1008-PREFIX", "prefix TERM.", True,
        "PASS" if up.strip().startswith("TERM") else "VIOLATION_CANDIDATE",
        up.split()[0] if up.strip() else None, "TERM."))
    rules.append(_rule(
        "MP-1008-TYPE", "type FASTON or BANDEIRA", True,
        "PASS" if ttype else "INCONCLUSIVE",
        ttype, sorted(_TERMINAL_TYPES)))
    rules.append(_rule(
        "MP-1008-DIM", "width x tab dimensions (e.g. 6,30X0,80)", True,
        "PASS" if dim else "INCONCLUSIVE",
        dim.group(0) if dim else None))
    if rng and rng.group(3) == "MM2":
        rng_status = "PASS"
        rng_reason = None
    elif rng:
        rng_status = "WARNING"
        rng_reason = ("unit 'MM' — norm expects 'MM2'; MM is not "
                      "silently normalized to MM2 (D3 pending)")
    else:
        rng_status, rng_reason = "INCONCLUSIVE", None
    rules.append(_rule(
        "MP-1008-RANGE", "gauge range in MM2 (e.g. 0,50-1,50MM2)", True,
        rng_status, rng.group(0) if rng else None, "x,x-y,yMM2",
        rng_reason))
    rules.append(_rule(
        "MP-1008-BATH", "plating (ESTANHADO, NIQUELADO)", True,
        "PASS" if bath else "INCONCLUSIVE",
        bath, sorted(_TERMINAL_BATH)))
    rules.append(_rule(
        "MP-1008-ISO", "insulation flag C/ISOLACAO or S/ISOLACAO", True,
        "PASS" if iso else "INCONCLUSIVE", iso))
    rules.append(_rule(
        "MP-1008-PACK", "packaging (GRANEL, FITADO, BLISTER)", True,
        "PASS" if pack else "INCONCLUSIVE",
        pack, sorted(_TERMINAL_PACK)))
    return attrs, rules


def _eval_isolator_1009(desc: str) -> dict[str, Any]:
    up = desc.upper()
    attrs: list[dict] = []
    rules: list[dict[str, Any]] = []
    tokens = set(re.findall(r"[A-ZÀ-Ú]{2,}\d*|\d+°", up))
    material = next((m for m in _ISOLATOR_MATERIALS if m in tokens), None)
    orient = ("RETO" if "RETO" in tokens
              else "90" if "90°" in up or "90" in tokens else None)
    serie = _SERIE.search(up)
    color = _COLOR_ABBR.search(up)
    certs = sorted(c for c in _ISOLATOR_CERTS
                   if re.search(rf"\b{c}\b", up))
    attrs += [
        _attr("material", material, "vocab", "EXTRACTED" if material else "ABSENT"),
        _attr("orientation", orient, "vocab", "EXTRACTED" if orient else "ABSENT"),
        _attr("serie", serie.group(0) if serie else None, "regex", "EXTRACTED" if serie else "ABSENT"),
        _attr("color", color.group(1) if color else None, "regex", "EXTRACTED" if color else "ABSENT"),
        _attr("certifications", ",".join(certs) or None, "vocab", "EXTRACTED" if certs else "ABSENT"),
    ]
    rules.append(_rule(
        "MP-1009-PREFIX", "prefix ISOLADOR", True,
        "PASS" if up.strip().startswith("ISOLADOR") else "VIOLATION_CANDIDATE",
        up.split()[0] if up.strip() else None, "ISOLADOR"))
    rules.append(_rule(
        "MP-1009-MATERIAL", "material (NYLON, POLIPROPILENO, PVC)", True,
        "PASS" if material else "INCONCLUSIVE",
        material, sorted(_ISOLATOR_MATERIALS)))
    rules.append(_rule(
        "MP-1009-ORIENT", "orientation RETO or 90°", True,
        "PASS" if orient else "INCONCLUSIVE", orient, ["RETO", "90°"]))
    rules.append(_rule(
        "MP-1009-SERIE", "series (e.g. 6,3 / 4,8 / 2,8)", True,
        "PASS" if serie else "INCONCLUSIVE",
        serie.group(0) if serie else None))
    rules.append(_rule(
        "MP-1009-COLOR", "color abbreviation (PT, AL, ...)", True,
        "PASS" if color else "INCONCLUSIVE",
        color.group(1) if color else None,
        reason="literal abbreviation only — PRETA↔PT equivalence "
               "requires ratified alias (D2 pending)" if color else None))
    rules.append(_rule(
        "MP-1009-CERT", "norms/certs (UL94 V2, RoHS, IEC, ABNT)", True,
        "PASS" if certs else "INCONCLUSIVE", certs))
    return attrs, rules


def resolve_applicability(product_code: str, product_type: str) -> tuple:
    """Return (norm_key, evaluator | None, status_reason).

    Fail-closed: uncovered groups are NOT_APPLICABLE; groups under an
    owner-pending decision (e.g. 1038 cables — D1) are OWNER_BLOCKED.
    """
    code = (product_code or "").strip()
    if is_pi50_code(code):
        return "PI_50XX", _evaluate_pi50, None
    group = (_GROUP.match(code) or [None, ""])[1] or ""
    if _CABLE_GROUP.match(group):
        return "MP_CABLES_1001_1005", _eval_cable, None
    if group == "1008":
        return "MP_TERMINAL_1008", _eval_terminal_1008, None
    if group == "1009":
        return "MP_ISOLATOR_1009", _eval_isolator_1009, None
    if group == "1038":
        return "MP_CABLES_1001_1005", None, (
            "group 1038 looks cable-like but norm 1001-1005 was NOT "
            "extended to it — extension pending Engineering (D1)")
    if group:
        return None, None, (
            f"group {group} has no ratified normative rule set")
    return None, None, "product group not identifiable"


def evaluate_description(
    *,
    product_code: str,
    product_type: str,
    description_raw: str | None,
    description_source: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """G24 reusable contract — evaluate ONE description, ONE source."""
    source = (description_source or "").upper()
    norm_key, evaluator, blocked_reason = resolve_applicability(
        product_code, product_type)
    result: dict[str, Any] = {
        "contract_version": NORMATIVE_CONTRACT_VERSION,
        "product_code": product_code,
        "product_type": product_type,
        "description_source": source or "UNKNOWN",
        "description_raw": description_raw,
        "applied_ruleset": (NORM_REFS.get(norm_key) if norm_key else None),
        "extracted_attributes": [],
        "rule_results": [],
        "cross_checks": [],
        "unknowns": [],
        "review_status": "DRAFT/CANDIDATE — Engineering approval required",
        "engine": {"name": "deterministic_rule_engine",
                   "version": NORMATIVE_CONTRACT_VERSION,
                   "ai_used": False},
        "no_business_write": True,
    }
    if source and source not in _SOURCES:
        result["overall_status"] = "OWNER_BLOCKED"
        result["unknowns"].append(
            f"unrecognized description_source '{description_source}'")
        return result
    if blocked_reason and norm_key is None:
        result["overall_status"] = "NOT_APPLICABLE"
        result["unknowns"].append(blocked_reason)
        return result
    if blocked_reason:
        result["applied_ruleset"] = None
        result["overall_status"] = "OWNER_BLOCKED"
        result["unknowns"].append(blocked_reason)
        result["rule_results"].append(_rule(
            "APPLICABILITY-01", "norm applies to this product group",
            False, "OWNER_BLOCKED", (product_code or "")[:4] or None,
            reason=blocked_reason))
        return result
    if not (description_raw or "").strip():
        result["overall_status"] = "INCONCLUSIVE"
        result["unknowns"].append(
            "description absent — no field is fabricated from "
            "another source")
        return result
    attrs, rules = evaluator((description_raw or "").strip())
    result["extracted_attributes"] = attrs
    result["rule_results"] = rules
    statuses = [r["status"] for r in rules if r["applicable"]]
    if "VIOLATION_CANDIDATE" in statuses:
        overall = "VIOLATION_CANDIDATE"
    elif "OWNER_BLOCKED" in statuses:
        overall = "OWNER_BLOCKED"
    elif "WARNING" in statuses:
        overall = "WARNING"
    elif "INCONCLUSIVE" in statuses:
        overall = "INCONCLUSIVE"
    else:
        overall = "PASS"
    result["overall_status"] = overall
    return result


def evaluate_pi_mp_coherence(
    *,
    pi_description: str | None,
    mp_descriptions: list[str],
) -> dict[str, Any]:
    """Coherence PI x child MP descriptions — candidates only.

    Only compares attributes with proven presence in BOTH texts; the
    norm matrix authorizes isolation-material, gauge and color checks
    as candidates. Position/side is never inferred (D4 pending).
    """
    seg = parse_pi50_segments(pi_description)
    if not seg:
        return {
            "status": "INCONCLUSIVE",
            "checks": [],
            "reason": "PI description outside the canonical grammar",
        }
    checks: list[dict[str, Any]] = []
    mp_materials, mp_awgs = set(), set()
    for d in mp_descriptions:
        up = (d or "").upper()
        for m in _CABLE_MATERIALS:
            if re.search(rf"\b{m}\b", up):
                mp_materials.add(m)
        m_awg = _AWG.search(up)
        if m_awg:
            mp_awgs.add(m_awg.group(1))
    if mp_materials:
        match = seg["isolation_material"] in mp_materials
        checks.append(_rule(
            "COH-ISO-MATERIAL",
            "PI isolation material consistent with child cable material",
            True,
            "PASS" if match else "VIOLATION_CANDIDATE",
            {"pi": seg["isolation_material"],
             "mp": sorted(mp_materials)},
            reason=None if match else
            "candidate divergence — not an NC; Engineering review"))
    else:
        checks.append(_rule(
            "COH-ISO-MATERIAL",
            "PI isolation material consistent with child cable material",
            True, "INCONCLUSIVE",
            {"pi": seg["isolation_material"], "mp": None},
            reason="no cable material token found in MP descriptions"))
    if mp_awgs:
        gauge = seg["gauge"].replace(",", ".").rstrip("0").rstrip(".")
        match = gauge in mp_awgs or seg["gauge"] in mp_awgs
        checks.append(_rule(
            "COH-GAUGE", "PI gauge consistent with child cable AWG",
            True, "PASS" if match else "VIOLATION_CANDIDATE",
            {"pi": seg["gauge"], "mp": sorted(mp_awgs)}))
    else:
        checks.append(_rule(
            "COH-GAUGE", "PI gauge consistent with child cable AWG",
            True, "INCONCLUSIVE", {"pi": seg["gauge"], "mp": None}))
    checks.append(_rule(
        "COH-TERM-POSITION",
        "terminal/isolator E/D position vs BOM components", False,
        "NOT_APPLICABLE", None,
        reason="MP code presence does not prove side/assembly — D4 "
               "mapping pending Engineering"))
    worst = next(
        (s for s in ("VIOLATION_CANDIDATE", "INCONCLUSIVE")
         if any(c["status"] == s and c["applicable"] for c in checks)),
        "PASS")
    return {"status": worst, "checks": checks,
            "reason": "candidates only — no automatic NC"}
