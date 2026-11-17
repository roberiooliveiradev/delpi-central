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
        "sha256": "c40413d2b23684e44409e867aea3f46157da57ad722c3d4c0c6f49844cd414fe",
        "applicability": "cables, groups 1001-1005",
    },
    "MP_TERMINAL_1008": {
        "owner": "ENGENHARIA",
        "ref": "normas-tecnicas-descricao-materias-primas.md#1008",
        "sha256": "c40413d2b23684e44409e867aea3f46157da57ad722c3d4c0c6f49844cd414fe",
        "applicability": "terminals group 1008 — subtype dispatched "
                        "(PINO|FORQUILHA|ILHOS/TUBULAR|LINGUETA|"
                        "FASTON/BANDEIRA|OLHAL/ANZOL|generic|LUVA/EMENDA)",
    },
    "MP_1009": {
        "owner": "ENGENHARIA",
        "ref": "normas-tecnicas-descricao-materias-primas.md#1009",
        "sha256": "c40413d2b23684e44409e867aea3f46157da57ad722c3d4c0c6f49844cd414fe",
        "applicability": "group 1009 — subtype dispatched "
                        "(ISOLADOR | INSERTO | CONECTOR)",
    },
    "MP_ISOLATOR_1009": {
        "owner": "ENGENHARIA",
        "ref": "normas-tecnicas-descricao-materias-primas.md#1009-isoladores",
        "sha256": "c40413d2b23684e44409e867aea3f46157da57ad722c3d4c0c6f49844cd414fe",
        "applicability": "isolators, group 1009",
    },
    "MP_INSERT_1009": {
        "owner": "ENGENHARIA",
        "ref": "normas-tecnicas-descricao-materias-primas.md#1009-inserto",
        "sha256": "c40413d2b23684e44409e867aea3f46157da57ad722c3d4c0c6f49844cd414fe",
        "applicability": "insertos, group 1009",
    },
    "MP_CONNECTOR_1009": {
        "owner": "ENGENHARIA",
        "ref": "normas-tecnicas-descricao-materias-primas.md#1009-conectores",
        "sha256": "c40413d2b23684e44409e867aea3f46157da57ad722c3d4c0c6f49844cd414fe",
        "applicability": "conectores, group 1009",
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
_TERMINAL_BATH_NU = _TERMINAL_BATH | {"NU"}
_TERMINAL_PACK = {"GRANEL", "FITADO", "BLISTER"}
# CARRETEL is ratified by the norm revision (PR #238) only for the
# generic 1008 structure — recognized lexically everywhere; only the
# generic evaluator passes allow_carretel=True (G25-L2-B).
_TERMINAL_PACK_RECOGNIZED = _TERMINAL_PACK | {"CARRETEL"}
# 1008 subtype markers documented in the norm sections (ILHÓS→ILHOS
# accent-normalized); a TIPO outside this set falls to the documented
# generic structure ("uso geral não cobertos por outras normas 1008").
_1008_TYPE_TOKENS = {
    "PINO", "FORQUILHA", "ILHOS", "TUBULAR", "LINGUETA",
    "FASTON", "BANDEIRA", "OLHAL", "ANZOL", "LUVA", "EMENDA",
}
_PINO_VARIANTS = {"RETO", "CURVO", "DUPLO"}
_ISOLATOR_MATERIALS = {"NYLON", "POLIPROPILENO", "PVC", "POLIURETANO"}
_ISOLATOR_ORIENT = {"RETO", "90"}
_ISOLATOR_CERTS = {"UL", "ROHS", "IEC", "ABNT", "DIN", "V2"}
# 1009 · Inserto (norm: tipos documentados; bitola explicitamente opcional)
_INSERT_TYPES = {
    "MACHO", "FEMEA", "FÊMEA", "MODULO", "MÓDULO", "CEGO", "FALSO",
    "BLINDADO",
}
_INSERT_OBS = {"CRIMP", "SCREW"}
# 1009 · Conectores (tipos do documento normativo)
_CONNECTOR_TYPES = {"MODULAR", "PORTA SOQUETE", "RETO", "ANGULAR"}
_CONNECTOR_OBS = {"C/SELO", "C/TRAVA", "CHAVEAMENTO"}
_1009_CERTS = {"UL", "ROHS", "IEC", "ABNT", "DIN", "CSA", "V2"}

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
# AWG ranges like 18-22AWG / 20-14AWG — documented for cables
# (1001-1005), 1009 Inserto and, since PR #238, the generic 1008
# structure; other 1008 structures stay INCONCLUSIVE (G25-L2-B).
_GAUGE_AWG_RANGE = re.compile(r"\b\d{1,2}\s*-\s*\d{1,2}\s*AWG\b")
_COMP_MM = re.compile(r"\bCOMP\s+\d+[,.]?\d*\s*MM\b")
_SCREW_M = re.compile(r"\bM\d+\b")
_BARE_MM = re.compile(r"\b\d+[,.]\d+\s*MM\b")
_TERM_CERT = re.compile(r"\b(ROHS|UL|IEC|ABNT|NBR|DIN\d*|CSA)\b")
_SERIE = re.compile(r"\b\d[,.]\d\b")
_WAYS = re.compile(r"\b\d+\s*(?:POLOS?|VIAS)\b")
_INSERT_SERIE = re.compile(r"\bHAN\s+([A-Z0-9]+)\b")


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
    awg = _GAUGE_AWG_RANGE.search(up)
    bath = next((b for b in _TERMINAL_BATH if b in tokens), None)
    iso = ("C/ISOLACAO" if "C/ISOLACAO" in up.replace("Ç", "C")
           else "S/ISOLACAO" if "S/ISOLACAO" in up.replace("Ç", "C")
           else None)
    pack = next((p for p in _TERMINAL_PACK_RECOGNIZED
                 if p in tokens), None)
    attrs += [
        _attr("terminal_type", ttype, "vocab", "EXTRACTED" if ttype else "ABSENT"),
        _attr("dimensions", dim.group(0) if dim else None, "regex", "EXTRACTED" if dim else "ABSENT", unit="mm"),
        _attr("gauge_range", (rng or awg).group(0) if (rng or awg) else None, "regex", "EXTRACTED" if (rng or awg) else "ABSENT", unit="AWG" if (awg and not rng) else None),
        _attr("plating", bath, "vocab", "EXTRACTED" if bath else "ABSENT"),
        _attr("insulation_flag", iso, "vocab", "EXTRACTED" if iso else "ABSENT"),
        _attr("packaging", pack, "vocab", "EXTRACTED" if pack else "ABSENT"),
    ]
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
    elif awg:
        rng_status = "INCONCLUSIVE"
        rng_reason = ("AWG range recognized — AWG is not documented "
                      "for 1008 structures; pending Engineering "
                      "ratification (not normalized to MM2)")
    else:
        rng_status, rng_reason = "INCONCLUSIVE", None
    rules.append(_rule(
        "MP-1008-RANGE", "gauge range in MM2 (e.g. 0,50-1,50MM2)", True,
        rng_status, (rng or awg).group(0) if (rng or awg) else None,
        "x,x-y,yMM2", rng_reason))
    rules.append(_rule(
        "MP-1008-BATH", "plating (ESTANHADO, NIQUELADO)", True,
        "PASS" if bath else "INCONCLUSIVE",
        bath, sorted(_TERMINAL_BATH)))
    rules.append(_rule(
        "MP-1008-ISO", "insulation flag C/ISOLACAO or S/ISOLACAO", True,
        "PASS" if iso else "INCONCLUSIVE", iso))
    rules.append(_t_pack_rule("MP-1008-PACK", pack))
    return attrs, rules


# ---- group 1008 subtype machinery (G25-L2) -------------------------

def _t_norm(up: str) -> str:
    for a, b in (("Ç", "C"), ("Ó", "O"), ("Ô", "O"), ("Í", "I"),
                 ("Â", "A"), ("Ã", "A"), ("À", "A"), ("Ê", "E")):
        up = up.replace(a, b)
    return up


def _t_tokens(up: str) -> list[str]:
    return [t for t in _t_norm(up).split() if t]


def _t_gauge(up: str) -> tuple[re.Match | None, re.Match | None,
                               re.Match | None]:
    """Return (mm_range, single_mm2, awg_range). Range checked first so
    a range is never misread as a single value."""
    return (_RANGE_MM2.search(up), _MM2.search(up),
            _GAUGE_AWG_RANGE.search(up))


def _t_gauge_rule(rule_id: str, rng: re.Match | None,
                  single: re.Match | None,
                  awg: re.Match | None = None,
                  *, allow_single: bool,
                  allow_awg: bool = False) -> dict:
    req = ("gauge range in MM2 or AWG (e.g. 0,50-1,50MM2 / 18-22AWG)"
           if allow_awg else
           "gauge range in MM2 (e.g. 0,50-1,50MM2)")
    if rng and rng.group(3) == "MM2":
        return _rule(rule_id, req, True, "PASS", rng.group(0),
                     "x,x-y,yMM2")
    if rng:
        return _rule(rule_id, req, True, "WARNING", rng.group(0),
                     "x,x-y,yMM2",
                     "unit 'MM' — norm expects 'MM2'; MM is not "
                     "silently normalized to MM2 (D3 pending)")
    if awg:
        # AWG is ratified only where the norm revision states it
        # (1008 generic structure, PR #238) — allow_awg is scoped to
        # that evaluator; other 1008 structures stay INCONCLUSIVE.
        # Never converted to mm2.
        if allow_awg:
            return _rule(rule_id, req, True, "PASS", awg.group(0),
                         "x,x-y,yMM2 or NN-NNAWG")
        return _rule(rule_id, req, True, "INCONCLUSIVE", awg.group(0),
                     "x,x-y,yMM2",
                     "AWG range recognized — AWG is not ratified for "
                     "this 1008 structure; pending Engineering "
                     "ratification (not normalized to MM2)")
    if single:
        if allow_single:
            return _rule(rule_id, "gauge in MM2 (range or single, "
                         "both documented)", True, "PASS",
                         single.group(0), "x,xMM2 or x,x-y,yMM2")
        return _rule(rule_id, req, True, "INCONCLUSIVE", single.group(0),
                     "x,x-y,yMM2",
                     "single MM2 present — norm documents a range")
    return _rule(rule_id, req, True, "INCONCLUSIVE", None,
                 "x,x-y,yMM2")


def _t_pack_rule(rule_id: str, pack: str | None,
                 *, allow_carretel: bool = False) -> dict:
    vocab = (_TERMINAL_PACK | ({"CARRETEL"} if allow_carretel else set()))
    req = ("packaging (GRANEL, FITADO, BLISTER"
           + (" or CARRETEL" if allow_carretel else "") + ")")
    if pack in vocab:
        return _rule(rule_id, req, True, "PASS", pack, sorted(vocab))
    if pack == "CARRETEL":
        return _rule(rule_id, req, True, "INCONCLUSIVE", pack,
                     sorted(vocab),
                     "packaging 'CARRETEL' recognized — not ratified "
                     "for this 1008 structure (PR #238 scope: generic "
                     "structure only)")
    return _rule(rule_id, req, True, "INCONCLUSIVE", pack, sorted(vocab))


def _t_common(up: str, *, bath_vocab: set[str],
              iso_vocab: tuple[str, ...]) -> dict[str, Any]:
    tokens = set(_t_tokens(up))
    bath = next((b for b in bath_vocab
                 if re.search(rf"\b{re.escape(b)}\b", up)), None)
    iso = next((i for i in iso_vocab
                if re.search(rf"\b{re.escape(i)}\b", up)), None)
    pack = next((p for p in _TERMINAL_PACK_RECOGNIZED
                 if p in tokens), None)
    certs = _TERM_CERT.findall(up)
    comp = _COMP_MM.search(up)
    return {"bath": bath, "iso": iso, "pack": pack,
            "certs": sorted(set(certs)), "comp": comp, "tokens": tokens}


def _t_obs(up: str, consumed: list) -> str | None:
    """Residual free-text observations: alphabetic tokens not consumed
    by typed fields, vocab or certifications."""
    rem = up
    for c in consumed:
        if c is None:
            continue
        if hasattr(c, "group"):
            rem = rem.replace(c.group(0), " ", 1)
        else:
            rem = re.sub(rf"(?<!\S){re.escape(str(c))}(?!\S)",
                         " ", rem, count=1)
    for c in _TERM_CERT.findall(up):
        rem = re.sub(rf"\b{re.escape(c)}\b", " ", rem, count=1)
    rem = _t_norm(rem)
    residual = [t for t in re.findall(r"[A-Z]{2,}", rem)
                if t not in _TERMINAL_PACK_RECOGNIZED]
    return ",".join(residual) or None


def _t_obs_cert_rules(rid: str, obs: str | None, certs: list) -> list:
    """OBS/NORMAS are documented fields the official examples tolerate
    omitting — absence is NOT_APPLICABLE, never a false violation."""
    return [
        _rule(f"{rid}-OBS", "observations (free text, omissible)", True,
              "PASS" if obs else "NOT_APPLICABLE", obs,
              reason=None if obs else "no observation field present"),
        _rule(f"{rid}-CERT", "norms/certs (RoHS, UL, IEC, ABNT, DIN)",
              True, "PASS" if certs else "NOT_APPLICABLE", certs,
              reason=None if certs else
              "no cert field present — tolerated by official examples"),
    ]


def _t_bath_iso_pack_rules(rid: str, c: dict[str, Any], *,
                           bath_vocab: set[str],
                           iso_vocab: tuple[str, ...]) -> list:
    return [
        _rule(f"{rid}-BATH", "plating (ESTANHADO, NIQUELADO"
              + (", NU" if "NU" in bath_vocab else "") + ")", True,
              "PASS" if c["bath"] else "INCONCLUSIVE",
              c["bath"], sorted(bath_vocab)),
        _rule(f"{rid}-ISO", "insulation flag "
              + "/".join(iso_vocab), True,
              "PASS" if c["iso"] else "INCONCLUSIVE", c["iso"]),
        _t_pack_rule(f"{rid}-PACK", c["pack"]),
    ]


def _eval_pino_1008(desc: str) -> dict[str, Any]:
    """1008 · PINO — TERM. PINO VARIANTE BITOLA COMP BANHO ISO EMB OBS CERT."""
    up = desc.upper()
    tokens = set(_t_tokens(up))
    variant = next((v for v in _PINO_VARIANTS if v in tokens), None)
    rng, single, awg = _t_gauge(up)
    c = _t_common(up, bath_vocab=_TERMINAL_BATH,
                  iso_vocab=("C/ISOLACAO", "S/ISOLACAO"))
    obs = _t_obs(up, [rng, single, awg, c["comp"], variant, "PINO", "TERM.",
                      "TERM", c["bath"], c["iso"], c["pack"]])
    attrs = [
        _attr("terminal_type", "PINO", "item_type", "EXTRACTED", "PINO"),
        _attr("variant", variant, "vocab", "EXTRACTED" if variant else "ABSENT"),
        _attr("gauge", (rng or single or awg).group(0) if (rng or single or awg) else None, "regex", "EXTRACTED" if (rng or single or awg) else "ABSENT", unit="AWG" if (awg and not (rng or single)) else None),
        _attr("pin_length", c["comp"].group(0) if c["comp"] else None, "regex", "EXTRACTED" if c["comp"] else "ABSENT", unit="mm"),
        _attr("plating", c["bath"], "vocab", "EXTRACTED" if c["bath"] else "ABSENT"),
        _attr("insulation_flag", c["iso"], "vocab", "EXTRACTED" if c["iso"] else "ABSENT"),
        _attr("packaging", c["pack"], "vocab", "EXTRACTED" if c["pack"] else "ABSENT"),
        _attr("observations", obs, "residual", "EXTRACTED" if obs else "ABSENT"),
        _attr("certifications", ",".join(c["certs"]) or None, "vocab", "EXTRACTED" if c["certs"] else "ABSENT"),
    ]
    rules = [
        _rule("MP-1008P-TYPE", "type PINO", True, "PASS", "PINO"),
        _rule("MP-1008P-VARIANT", "variant RETO|CURVO|DUPLO", True,
              "PASS" if variant else "INCONCLUSIVE",
              variant, sorted(_PINO_VARIANTS)),
        _t_gauge_rule("MP-1008P-GAUGE", rng, single, awg, allow_single=True),
        _rule("MP-1008P-LENGTH", "pin length COMP x,xxMM", True,
              "PASS" if c["comp"] else "INCONCLUSIVE",
              c["comp"].group(0) if c["comp"] else None),
    ]
    rules += _t_bath_iso_pack_rules(
        "MP-1008P", c, bath_vocab=_TERMINAL_BATH,
        iso_vocab=("C/ISOLACAO", "S/ISOLACAO"))
    rules += _t_obs_cert_rules("MP-1008P", obs, c["certs"])
    return attrs, rules


def _eval_eyelet_1008(desc: str) -> dict[str, Any]:
    """1008 · ILHOS/TUBULAR — TERM. TIPO BITOLA COMP BANHO ISO EMB OBS NORMAS."""
    up = desc.upper()
    rng, single, awg = _t_gauge(up)
    c = _t_common(up, bath_vocab=_TERMINAL_BATH,
                  iso_vocab=("C/ISOLACAO", "S/ISOLACAO"))
    ttype = _t_tokens(up)[1]
    obs = _t_obs(up, [rng, single, awg, c["comp"], ttype, "TERM.", "TERM",
                      c["bath"], c["iso"], c["pack"]])
    attrs = [
        _attr("terminal_type", ttype, "item_type", "EXTRACTED", ttype),
        _attr("gauge", (rng or single or awg).group(0) if (rng or single or awg) else None, "regex", "EXTRACTED" if (rng or single or awg) else "ABSENT", unit="AWG" if (awg and not (rng or single)) else None),
        _attr("barrel_length", c["comp"].group(0) if c["comp"] else None, "regex", "EXTRACTED" if c["comp"] else "ABSENT", unit="mm"),
        _attr("plating", c["bath"], "vocab", "EXTRACTED" if c["bath"] else "ABSENT"),
        _attr("insulation_flag", c["iso"], "vocab", "EXTRACTED" if c["iso"] else "ABSENT"),
        _attr("packaging", c["pack"], "vocab", "EXTRACTED" if c["pack"] else "ABSENT"),
        _attr("observations", obs, "residual", "EXTRACTED" if obs else "ABSENT"),
        _attr("certifications", ",".join(c["certs"]) or None, "vocab", "EXTRACTED" if c["certs"] else "ABSENT"),
    ]
    rules = [
        _rule("MP-1008I-TYPE", "type ILHOS or TUBULAR", True,
              "PASS", ttype, ["ILHOS", "TUBULAR"]),
        _t_gauge_rule("MP-1008I-GAUGE", rng, single, awg, allow_single=False),
        _rule("MP-1008I-LENGTH", "barrel length COMP x,xxMM", True,
              "PASS" if c["comp"] else "INCONCLUSIVE",
              c["comp"].group(0) if c["comp"] else None),
    ]
    rules += _t_bath_iso_pack_rules(
        "MP-1008I", c, bath_vocab=_TERMINAL_BATH,
        iso_vocab=("C/ISOLACAO", "S/ISOLACAO"))
    rules += _t_obs_cert_rules("MP-1008I", obs, c["certs"])
    return attrs, rules


def _eval_lingueta_1008(desc: str) -> dict[str, Any]:
    """1008 · LINGUETA — TERM. LINGUETA LARGxTAB BITOLA BANHO ISO EMB OBS CERT."""
    up = desc.upper()
    dim = _DIM_PAIR.search(up)
    rng, single, awg = _t_gauge(up)
    c = _t_common(up, bath_vocab=_TERMINAL_BATH,
                  iso_vocab=("C/ISOLACAO", "S/ISOLACAO"))
    obs = _t_obs(up, [dim, rng, single, awg, "LINGUETA", "TERM.", "TERM",
                      c["bath"], c["iso"], c["pack"]])
    attrs = [
        _attr("terminal_type", "LINGUETA", "item_type", "EXTRACTED", "LINGUETA"),
        _attr("dimensions", dim.group(0) if dim else None, "regex", "EXTRACTED" if dim else "ABSENT", unit="mm"),
        _attr("gauge", (rng or single or awg).group(0) if (rng or single or awg) else None, "regex", "EXTRACTED" if (rng or single or awg) else "ABSENT", unit="AWG" if (awg and not (rng or single)) else None),
        _attr("plating", c["bath"], "vocab", "EXTRACTED" if c["bath"] else "ABSENT"),
        _attr("insulation_flag", c["iso"], "vocab", "EXTRACTED" if c["iso"] else "ABSENT"),
        _attr("packaging", c["pack"], "vocab", "EXTRACTED" if c["pack"] else "ABSENT"),
        _attr("observations", obs, "residual", "EXTRACTED" if obs else "ABSENT"),
        _attr("certifications", ",".join(c["certs"]) or None, "vocab", "EXTRACTED" if c["certs"] else "ABSENT"),
    ]
    rules = [
        _rule("MP-1008L-TYPE", "type LINGUETA", True, "PASS", "LINGUETA"),
        _rule("MP-1008L-DIM", "width x tab (e.g. 6,30X0,80)", True,
              "PASS" if dim else "INCONCLUSIVE",
              dim.group(0) if dim else None),
        _t_gauge_rule("MP-1008L-GAUGE", rng, single, awg, allow_single=False),
    ]
    rules += _t_bath_iso_pack_rules(
        "MP-1008L", c, bath_vocab=_TERMINAL_BATH,
        iso_vocab=("C/ISOLACAO", "S/ISOLACAO"))
    rules += _t_obs_cert_rules("MP-1008L", obs, c["certs"])
    return attrs, rules


def _ring_dims(up: str) -> dict[str, Any]:
    """Positional M-screw / int-diam / ext-diam shared by FORQUILHA
    and OLHAL/ANZOL (norm order: M# → D.INT → BITOLA → D.EXT → COMP)."""
    screw = _SCREW_M.search(up)
    rng = _RANGE_MM2.search(up)
    comp = _COMP_MM.search(up)
    comp_span = comp.span() if comp else (len(up), len(up))
    bare = [m for m in _BARE_MM.finditer(up)
            if not (comp_span[0] <= m.start() < comp_span[1])]
    dint = dext = None
    if rng:
        before = [m for m in bare if m.end() <= rng.start()]
        after = [m for m in bare if m.start() >= rng.end()]
        dint = before[-1] if before else None
        dext = after[0] if after else None
    return {"screw": screw, "gauge": rng, "dint": dint, "dext": dext,
            "comp": comp}


def _ring_1008(desc: str, rid: str, ttype: str) -> dict[str, Any]:
    """Shared evaluator body for FORQUILHA (1008F) and OLHAL/ANZOL
    (1008O) — identical documented field sequence."""
    up = desc.upper()
    d = _ring_dims(up)
    rng_single = _MM2.search(up) if not d["gauge"] else None
    rng_awg = _GAUGE_AWG_RANGE.search(up) if not d["gauge"] else None
    c = _t_common(up, bath_vocab=_TERMINAL_BATH,
                  iso_vocab=("C/ISOLACAO", "S/ISOLACAO"))
    obs = _t_obs(up, [d["screw"], d["dint"], d["gauge"], rng_single,
                      rng_awg, d["dext"], d["comp"], ttype, "TERM.", "TERM",
                      c["bath"], c["iso"], c["pack"]])
    attrs = [
        _attr("terminal_type", ttype, "item_type", "EXTRACTED", ttype),
        _attr("screw", d["screw"].group(0) if d["screw"] else None, "regex", "EXTRACTED" if d["screw"] else "ABSENT"),
        _attr("inner_diameter", d["dint"].group(0) if d["dint"] else None, "regex", "EXTRACTED" if d["dint"] else "ABSENT", unit="mm"),
        _attr("gauge", (d["gauge"] or rng_single or rng_awg).group(0)
              if (d["gauge"] or rng_single or rng_awg) else None,
              "regex",
              "EXTRACTED" if (d["gauge"] or rng_single or rng_awg)
              else "ABSENT",
              unit="AWG" if (rng_awg and not (d["gauge"] or rng_single))
              else None),
        _attr("outer_diameter", d["dext"].group(0) if d["dext"] else None, "regex", "EXTRACTED" if d["dext"] else "ABSENT", unit="mm"),
        _attr("length", d["comp"].group(0) if d["comp"] else None, "regex", "EXTRACTED" if d["comp"] else "ABSENT", unit="mm"),
        _attr("plating", c["bath"], "vocab", "EXTRACTED" if c["bath"] else "ABSENT"),
        _attr("insulation_flag", c["iso"], "vocab", "EXTRACTED" if c["iso"] else "ABSENT"),
        _attr("packaging", c["pack"], "vocab", "EXTRACTED" if c["pack"] else "ABSENT"),
        _attr("observations", obs, "residual", "EXTRACTED" if obs else "ABSENT"),
        _attr("certifications", ",".join(c["certs"]) or None, "vocab", "EXTRACTED" if c["certs"] else "ABSENT"),
    ]
    rules = [
        _rule(f"{rid}-TYPE", f"type {ttype}", True, "PASS", ttype),
        _rule(f"{rid}-SCREW", "screw size (e.g. M3, M4)", True,
              "PASS" if d["screw"] else "INCONCLUSIVE",
              d["screw"].group(0) if d["screw"] else None),
        _rule(f"{rid}-DINT", "inner diameter x,xxMM before gauge",
              True, "PASS" if d["dint"] else "INCONCLUSIVE",
              d["dint"].group(0) if d["dint"] else None, "x,xxMM"),
        _t_gauge_rule(f"{rid}-GAUGE", d["gauge"], rng_single,
                      rng_awg, allow_single=False),
        _rule(f"{rid}-DEXT", "outer diameter x,xxMM after gauge",
              True, "PASS" if d["dext"] else "INCONCLUSIVE",
              d["dext"].group(0) if d["dext"] else None, "x,xxMM"),
        _rule(f"{rid}-LENGTH", "length COMP x,xxMM", True,
              "PASS" if d["comp"] else "INCONCLUSIVE",
              d["comp"].group(0) if d["comp"] else None),
    ]
    rules += _t_bath_iso_pack_rules(
        rid, c, bath_vocab=_TERMINAL_BATH,
        iso_vocab=("C/ISOLACAO", "S/ISOLACAO"))
    rules += _t_obs_cert_rules(rid, obs, c["certs"])
    return attrs, rules


def _eval_generic_1008(desc: str) -> dict[str, Any]:
    """1008 · genérico — TERM. TIPO BITOLA BANHO EMB OBS NORMAS
    (fallback documentado p/ tipos fora das outras seções 1008)."""
    up = desc.upper()
    toks = _t_tokens(up)
    ttype = toks[1] if len(toks) > 1 else None
    rng, single, awg = _t_gauge(up)
    c = _t_common(up, bath_vocab=_TERMINAL_BATH_NU,
                  iso_vocab=())
    obs = _t_obs(up, [rng, single, awg, ttype, "TERM.", "TERM",
                      c["bath"], c["pack"]])
    attrs = [
        _attr("terminal_type", ttype, "item_type", "EXTRACTED" if ttype else "ABSENT"),
        _attr("gauge", (rng or single or awg).group(0) if (rng or single or awg) else None, "regex", "EXTRACTED" if (rng or single or awg) else "ABSENT", unit="AWG" if (awg and not (rng or single)) else None),
        _attr("plating", c["bath"], "vocab", "EXTRACTED" if c["bath"] else "ABSENT"),
        _attr("packaging", c["pack"], "vocab", "EXTRACTED" if c["pack"] else "ABSENT"),
        _attr("observations", obs, "residual", "EXTRACTED" if obs else "ABSENT"),
        _attr("certifications", ",".join(c["certs"]) or None, "vocab", "EXTRACTED" if c["certs"] else "ABSENT"),
    ]
    rules = [
        _rule("MP-1008G-TYPE", "terminal type (free technical type, "
              "e.g. BALA)", True,
              "PASS" if ttype else "INCONCLUSIVE", ttype),
        _t_gauge_rule("MP-1008G-GAUGE", rng, single, awg,
                      allow_single=False, allow_awg=True),
        _rule("MP-1008G-BATH", "plating (ESTANHADO, NIQUELADO, NU)",
              True, "PASS" if c["bath"] else "INCONCLUSIVE",
              c["bath"], sorted(_TERMINAL_BATH_NU)),
        _t_pack_rule("MP-1008G-PACK", c["pack"], allow_carretel=True),
    ]
    rules += _t_obs_cert_rules("MP-1008G", obs, c["certs"])
    return attrs, rules


def _eval_luva_1008(desc: str) -> dict[str, Any]:
    """1008 · LUVA/EMENDA — TERM. TIPO BITOLA COMP BANHO ISO EMB OBS CERT.
    NU is documented both for BANHO and ISOLAÇÃO (positional)."""
    up = desc.upper()
    ttype = _t_tokens(up)[1]
    rng, single, awg = _t_gauge(up)
    comp = _COMP_MM.search(up)
    tokens = set(_t_tokens(up))
    bath = next((b for b in _TERMINAL_BATH if b in tokens), None)
    iso = ("C/ISOLACAO" if "C/ISOLACAO" in _t_norm(up)
           else "S/ISOLACAO" if "S/ISOLACAO" in _t_norm(up)
           else None)
    nus = [m.start() for m in re.finditer(r"\bNU\b", up)]
    if bath is None and nus:
        bath = "NU"
        nus.pop(0)
    if iso is None and nus:
        iso = "NU"
    pack = next((p for p in _TERMINAL_PACK_RECOGNIZED
                 if p in tokens), None)
    certs = sorted(set(_TERM_CERT.findall(up)))
    obs = _t_obs(up, [rng, single, awg, comp, ttype, "TERM.", "TERM",
                      bath, iso, pack])
    attrs = [
        _attr("terminal_type", ttype, "item_type", "EXTRACTED", ttype),
        _attr("gauge", (rng or single or awg).group(0) if (rng or single or awg) else None, "regex", "EXTRACTED" if (rng or single or awg) else "ABSENT", unit="AWG" if (awg and not (rng or single)) else None),
        _attr("length", comp.group(0) if comp else None, "regex", "EXTRACTED" if comp else "ABSENT", unit="mm"),
        _attr("plating", bath, "vocab", "EXTRACTED" if bath else "ABSENT"),
        _attr("insulation_flag", iso, "vocab", "EXTRACTED" if iso else "ABSENT"),
        _attr("packaging", pack, "vocab", "EXTRACTED" if pack else "ABSENT"),
        _attr("observations", obs, "residual", "EXTRACTED" if obs else "ABSENT"),
        _attr("certifications", ",".join(certs) or None, "vocab", "EXTRACTED" if certs else "ABSENT"),
    ]
    rules = [
        _rule("MP-1008E-TYPE", "type LUVA or EMENDA", True,
              "PASS", ttype, ["LUVA", "EMENDA"]),
        _t_gauge_rule("MP-1008E-GAUGE", rng, single, awg, allow_single=False),
        _rule("MP-1008E-LENGTH", "length COMP x,xxMM", True,
              "PASS" if comp else "INCONCLUSIVE",
              comp.group(0) if comp else None),
        _rule("MP-1008E-BATH", "plating (ESTANHADO, NU, NIQUELADO)",
              True, "PASS" if bath else "INCONCLUSIVE",
              bath, sorted(_TERMINAL_BATH_NU)),
        _rule("MP-1008E-ISO", "insulation C/ISOLACAO | S/ISOLACAO | NU",
              True, "PASS" if iso else "INCONCLUSIVE", iso),
        _t_pack_rule("MP-1008E-PACK", pack),
    ]
    rules += _t_obs_cert_rules("MP-1008E", obs, certs)
    return attrs, rules


def _eval_forquilha_1008(desc: str) -> dict[str, Any]:
    return _ring_1008(desc, "MP-1008F", "FORQUILHA")


def _eval_olhal_1008(desc: str) -> dict[str, Any]:
    ttype = _t_tokens(desc.upper())[1]
    return _ring_1008(desc, "MP-1008O", ttype)


_1008_SUBTYPES = {
    "PINO": _eval_pino_1008,
    "FORQUILHA": _eval_forquilha_1008,
    "ILHOS": _eval_eyelet_1008,
    "TUBULAR": _eval_eyelet_1008,
    "LINGUETA": _eval_lingueta_1008,
    "FASTON": _eval_terminal_1008,
    "BANDEIRA": _eval_terminal_1008,
    "OLHAL": _eval_olhal_1008,
    "ANZOL": _eval_olhal_1008,
    "LUVA": _eval_luva_1008,
    "EMENDA": _eval_luva_1008,
}


def _eval_1008(desc: str) -> dict[str, Any]:
    """Group 1008 dispatcher — selects the evaluator by the documented
    TERM. <TIPO> marker. Unknown TIPO falls to the documented generic
    structure; absent/contradictory subtype evidence → INCONCLUSIVE,
    never the FASTON/BANDEIRA evaluator."""
    up = desc.upper() if desc else ""
    toks = _t_tokens(up)
    prefix_rule = _rule(
        "MP-1008-PREFIX", "prefix TERM.", True,
        "PASS" if toks and toks[0] in ("TERM.", "TERM") else "VIOLATION_CANDIDATE",
        toks[0] if toks else None, "TERM.")
    if not toks or toks[0] not in ("TERM.", "TERM"):
        sub_rule = _rule(
            "MP-1008-SUBTYPE", "TIPO token identifies the 1008 "
            "structure", True, "INCONCLUSIVE", None,
            sorted(_1008_TYPE_TOKENS) + ["<generic>"],
            "no TERM. prefix — subtype not identifiable")
        return [_attr("subtype", None, "item_prefix", "ABSENT")], \
            [prefix_rule, sub_rule]
    ttype = toks[1] if len(toks) > 1 else None
    known = [t for t in toks[1:] if t in _1008_TYPE_TOKENS]
    if len(set(known)) > 1 or (ttype is None) or \
            (ttype not in _1008_TYPE_TOKENS and known):
        sub_rule = _rule(
            "MP-1008-SUBTYPE", "TIPO token identifies the 1008 "
            "structure", True, "INCONCLUSIVE", ttype,
            sorted(_1008_TYPE_TOKENS) + ["<generic>"],
            "absent/contradictory subtype evidence — no evaluator "
            "applied arbitrarily")
        return [_attr("subtype", ttype, "item_type", "AMBIGUOUS")], \
            [prefix_rule, sub_rule]
    if ttype in _1008_TYPE_TOKENS:
        subtype_name = ttype
        evaluator = _1008_SUBTYPES[ttype]
        sub_status = "PASS"
        sub_reason = None
    else:
        subtype_name = "GENERIC"
        evaluator = _eval_generic_1008
        sub_status = "PASS"
        sub_reason = ("TIPO not in the specific 1008 sections — "
                      "documented generic structure applies")
    attrs, rules = evaluator(desc)
    attrs.insert(0, _attr("subtype", subtype_name, "item_type", "EXTRACTED"))
    sub_rule = _rule(
        "MP-1008-SUBTYPE", "TIPO token identifies the 1008 structure",
        True, sub_status, ttype, sorted(_1008_TYPE_TOKENS) + ["<generic>"],
        sub_reason)
    return attrs, [prefix_rule, sub_rule] + rules


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


def _eval_insert_1009(desc: str) -> dict[str, Any]:
    """1009 · Inserto — INSERTO + TIPO + VIAS/POLOS + LINHA/SÉRIE +
    BITOLA (opcional) + OBS + NORMAS."""
    up = desc.upper()
    attrs: list[dict] = []
    rules: list[dict[str, Any]] = []
    tokens = set(re.findall(r"[A-ZÀ-Ú]{2,}", up))
    ttype = next((t for t in _INSERT_TYPES if t in tokens), None)
    ways = _WAYS.search(up)
    serie = _INSERT_SERIE.search(up)
    gauge = (_RANGE_MM2.search(up) or _GAUGE_AWG_RANGE.search(up)
             or _MM2.search(up) or _AWG.search(up))
    obs = next((o for o in _INSERT_OBS if re.search(rf"\b{o}\b", up)), None)
    certs = sorted(c for c in _1009_CERTS
                   if re.search(rf"\b{c}\b", up))
    attrs += [
        _attr("insert_type", ttype, "vocab", "EXTRACTED" if ttype else "ABSENT"),
        _attr("ways", ways.group(0) if ways else None, "regex", "EXTRACTED" if ways else "ABSENT"),
        _attr("serie", serie.group(0) if serie else None, "regex", "EXTRACTED" if serie else "ABSENT"),
        _attr("gauge", gauge.group(0) if gauge else None, "regex", "EXTRACTED" if gauge else "ABSENT"),
        _attr("observations", obs, "vocab", "EXTRACTED" if obs else "ABSENT"),
        _attr("certifications", ",".join(certs) or None, "vocab", "EXTRACTED" if certs else "ABSENT"),
    ]
    rules.append(_rule(
        "MP-1009I-PREFIX", "prefix ITEM = INSERTO", True,
        "PASS" if up.strip().startswith("INSERTO") else "VIOLATION_CANDIDATE",
        up.split()[0] if up.strip() else None, "INSERTO"))
    rules.append(_rule(
        "MP-1009I-TYPE", "type MACHO|FEMEA|MODULO|CEGO|FALSO|BLINDADO",
        True, "PASS" if ttype else "INCONCLUSIVE",
        ttype, sorted(_INSERT_TYPES)))
    rules.append(_rule(
        "MP-1009I-WAYS", "number of ways/poles (e.g. 10 POLOS, 3 VIAS)",
        True, "PASS" if ways else "INCONCLUSIVE",
        ways.group(0) if ways else None))
    rules.append(_rule(
        "MP-1009I-SERIE", "line/series (e.g. HAN D, HAN E, HAN 1A)",
        True, "PASS" if serie else "INCONCLUSIVE",
        serie.group(0) if serie else None))
    # bitola explicitly OPTIONAL in the norm — absence is never a violation
    rules.append(_rule(
        "MP-1009I-GAUGE", "gauge optional (e.g. 0,14-2,5MM2; 20-14AWG)",
        bool(gauge), "PASS" if gauge else "NOT_APPLICABLE",
        gauge.group(0) if gauge else None,
        reason=None if gauge else
        "optional per norm — absence is not a deviation"))
    rules.append(_rule(
        "MP-1009I-CERT", "norms/certs (RoHS, UL, IEC, DIN, UL/CSA)",
        True, "PASS" if certs else "INCONCLUSIVE", certs))
    return attrs, rules


def _eval_connector_1009(desc: str) -> dict[str, Any]:
    """1009 · Conectores — CONECTOR + TIPO + Nº VIAS + COR + OBS + NORMAS."""
    up = desc.upper()
    attrs: list[dict] = []
    rules: list[dict[str, Any]] = []
    ttype = next((t for t in _CONNECTOR_TYPES if t in up), None)
    ways = _WAYS.search(up)
    color = _COLOR_ABBR.search(up)
    obs = next((o for o in _CONNECTOR_OBS if o in up), None)
    certs = sorted(c for c in _1009_CERTS
                   if re.search(rf"\b{c}\b", up))
    attrs += [
        _attr("connector_type", ttype, "vocab", "EXTRACTED" if ttype else "ABSENT"),
        _attr("ways", ways.group(0) if ways else None, "regex", "EXTRACTED" if ways else "ABSENT"),
        _attr("color", color.group(1) if color else None, "regex", "EXTRACTED" if color else "ABSENT"),
        _attr("observations", obs, "vocab", "EXTRACTED" if obs else "ABSENT"),
        _attr("certifications", ",".join(certs) or None, "vocab", "EXTRACTED" if certs else "ABSENT"),
    ]
    rules.append(_rule(
        "MP-1009C-PREFIX", "prefix ITEM = CONECTOR", True,
        "PASS" if up.strip().startswith("CONECTOR") else "VIOLATION_CANDIDATE",
        up.split()[0] if up.strip() else None, "CONECTOR"))
    rules.append(_rule(
        "MP-1009C-TYPE", "type MODULAR|PORTA SOQUETE|RETO|ANGULAR",
        True, "PASS" if ttype else "INCONCLUSIVE",
        ttype, sorted(_CONNECTOR_TYPES)))
    rules.append(_rule(
        "MP-1009C-WAYS", "number of ways (e.g. 3 VIAS, 6 VIAS)",
        True, "PASS" if ways else "INCONCLUSIVE",
        ways.group(0) if ways else None))
    rules.append(_rule(
        "MP-1009C-COLOR", "color abbreviation (PT, AL, ...)", True,
        "PASS" if color else "INCONCLUSIVE",
        color.group(1) if color else None))
    rules.append(_rule(
        "MP-1009C-CERT", "norms/certs (RoHS, UL, V2, IEC, ABNT, DIN)",
        True, "PASS" if certs else "INCONCLUSIVE", certs))
    return attrs, rules


# First ITEM word is the normative subtype marker — each 1009
# structure fixes its own prefix (ISOLADOR | INSERTO | CONECTOR).
_1009_SUBTYPES = {
    "ISOLADOR": _eval_isolator_1009,
    "INSERTO": _eval_insert_1009,
    "CONECTOR": _eval_connector_1009,
}
_1009_RULESET = {
    "ISOLADOR": "MP_ISOLATOR_1009",
    "INSERTO": "MP_INSERT_1009",
    "CONECTOR": "MP_CONNECTOR_1009",
}


def _eval_1009(desc: str) -> dict[str, Any]:
    """Group 1009 dispatcher — picks the evaluator by the ITEM prefix.

    An absent/unknown subtype NEVER falls through to the isolator
    rules: it yields an explicit INCONCLUSIVE instead.
    """
    first = (desc or "").strip().split()[0].upper() if desc else ""
    subtype = first if first in _1009_SUBTYPES else None
    if subtype is None:
        return [
            _attr("subtype", first or None, "item_prefix", "AMBIGUOUS")], [
            _rule(
                "MP-1009-SUBTYPE",
                "ITEM prefix identifies subtype "
                "(ISOLADOR|INSERTO|CONECTOR)",
                True, "INCONCLUSIVE", first or None,
                sorted(_1009_SUBTYPES),
                "subtype not identified — no evaluator applied "
                "arbitrarily")]
    attrs, rules = _1009_SUBTYPES[subtype](desc)
    attrs.insert(0, _attr("subtype", subtype, "item_prefix", "EXTRACTED"))
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
        return "MP_TERMINAL_1008", _eval_1008, None
    if group == "1009":
        return "MP_1009", _eval_1009, None
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
    if norm_key == "MP_1009":
        st = next((a["normalized_value"] for a in attrs
                   if a["name"] == "subtype"), None)
        result["applied_ruleset"] = NORM_REFS.get(
            _1009_RULESET.get(st, "MP_1009"))
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
    pi_code: str | None = None,
    mp_code: str | None = None,
    pi_source: str | None = None,
    mp_source: str | None = None,
    occurrence_id: str | None = None,
) -> dict[str, Any]:
    """Coherence PI x child MP descriptions — candidates only.

    Only compares attributes with proven presence in BOTH texts; the
    norm matrix authorizes isolation-material, gauge and color checks
    as candidates. Position/side is never inferred (D4 pending).

    G24-R1: the source of each description is explicit
    (``source_pair``); a missing input yields ``INCONCLUSIVE`` for
    that pair and is never filled from the other source.
    """
    pair = {"pi": pi_source, "mp": mp_source}
    comparison_type = (
        "CROSS_SOURCE"
        if pi_source and mp_source and pi_source != mp_source
        else "SAME_SOURCE"
    )

    def _wrap(checks: list[dict[str, Any]], status: str,
              reason: str | None = None) -> dict[str, Any]:
        for c in checks:
            c["source_pair"] = dict(pair)
            c["comparison_type"] = comparison_type
        return {
            "comparison_type": comparison_type,
            "source_pair": pair,
            "pi_code": pi_code,
            "mp_code": mp_code,
            "occurrence_id": occurrence_id,
            "status": status,
            "checks": checks,
            "review_status": "PENDING_ENGINEERING",
            "reason": reason or "candidates only — no automatic NC",
        }

    if not (pi_description or "").strip() or not any(
            (d or "").strip() for d in mp_descriptions):
        missing = []
        if not (pi_description or "").strip():
            missing.append(f"PI description absent in {pi_source or '?'}")
        if not any((d or "").strip() for d in mp_descriptions):
            missing.append(f"MP description absent in {mp_source or '?'}")
        return _wrap(
            [], "INCONCLUSIVE",
            "; ".join(missing)
            + " — absence is never filled from the other source")
    seg = parse_pi50_segments(pi_description)
    if not seg:
        return _wrap(
            [], "INCONCLUSIVE",
            "PI description outside the canonical grammar")
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
    return _wrap(checks, worst)
