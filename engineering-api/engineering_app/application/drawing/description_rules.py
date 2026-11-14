"""Technical description validators — MP (groups 1001-1025) and
intermediate products 50xx (Documento 69 §7-§8).

Scope honesty: implements the structural, verifiable parts of the
authorized norms (prefix↔group coherence, color abbreviation shape,
canonical segment layout for 50xx, isolation codes CA-CV, 4-letter
colors, mm/decape/terminal segments). It does NOT fabricate field-level
norm content that lives in `Normas_Tecnicas_DELPI.md` — fields the norm
does not structurally define yield INCONCLUSIVE, never invented FAILs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_MP_GROUPS: dict[str, str] = {
    "1001": "CABO", "1002": "CABO", "1003": "CABO", "1004": "CABO",
    "1005": "CABO", "1006": "CABO", "1007": "CABO", "1008": "TERM",
    "1009": "ISOLADOR|INSERTO|CONECTOR",
    "1011": "ETIQUETA|ANILHA|CARTÃO|CARTAO", "1012": "TUBO",
    "1013": "TERMOENCOLHIVEL", "1015": "PRENSA", "1016": "RESISTOR",
    "1025": "TERMISTOR", "1050": "TERMOENCOLHIVEL",
}
_MP_SHORT_COLORS = {
    "PT", "BN", "AZ", "VD", "VM", "AM", "LR", "CZ", "RS", "BR",
    "VDAR", "MRBN", "AZMA", "VDRS", "PTBN",
}
_PI_FAMILY = re.compile(r"^50\d{2}")
_PI_CODE_SHAPE = re.compile(
    r"^(50\d{2})\s?(\d{3,4})\s?(CA|CB|CF|CT|CV)?(\d[\d,\.]*)?\s*"
    r"([A-Z]{4})?\s*-?\s*(\d{3,5})?\s*(/\s*\d{1,2}\s*/\s*\d{1,2})?\s*"
    r"-?\s*(\d{2,4}-\d{2,4})?",
    re.IGNORECASE,
)
_PI_ISOLATION = {"CA": "PVC", "CB": "EPR", "CF": "Silicone",
                 "CT": "Teflon", "CV": "Especial"}
_PI_COLOR_4 = re.compile(r"^[A-Z]{4}$")
_PRODUCT_CODE = re.compile(r"^(\d{4})")


@dataclass
class DescriptionCheck:
    key: str
    status: str  # PASS | WARNING | INCONCLUSIVE | NOT_APPLICABLE
    summary: str


def validate_mp_description(
    product_code: str, description: str | None
) -> DescriptionCheck:
    """Structural MP description check against group conventions."""
    code = (product_code or "").strip()
    desc = (description or "").strip()
    group = (_PRODUCT_CODE.match(code) or [None, ""])[1] or ""
    if group not in _MP_GROUPS:
        return DescriptionCheck(
            key="mp_description",
            status="NOT_APPLICABLE",
            summary=(
                f"Grupo '{group or 'desconhecido'}' fora de 1001–1025 — "
                "regra de descrição MP não aplicável."
            ),
        )
    if not desc:
        return DescriptionCheck(
            key="mp_description",
            status="INCONCLUSIVE",
            summary="Descrição cadastral ausente — verificação impossível.",
        )
    findings: list[str] = []
    expected = _MP_GROUPS[group].split("|")
    upper = desc.upper()
    if not any(token in upper for token in expected):
        findings.append(
            f"prefixo esperado para grupo {group} "
            f"({'/'.join(expected)}) não encontrado"
        )
    color_tokens = [
        t for t in re.findall(r"\b[A-Z]{2,4}\b", upper)
        if t in _MP_SHORT_COLORS
    ]
    summary = (
        f"Estrutura grupo {group}: campos verificáveis ok; "
        f"cores abreviadas reconhecidas: {', '.join(color_tokens) or '—'}."
        if not findings
        else "Desvios estruturais: " + "; ".join(findings)
    )
    return DescriptionCheck(
        key="mp_description",
        status="WARNING" if findings else "PASS",
        summary=summary + " Verificação limitada a estrutura — "
        "campos normativos detalhados em Normas_Tecnicas_DELPI.md.",
    )


# Segment grammar PI 50xx (doc 69 §8 / R3-B):
#   {family}{seq} {ISO}{gauge}{COLOR4}-{len}/{decE}/{decD}-{termEtermD}-{isoEisoD}
# Prefixo concatenado é a forma canônica: "CA22VERM" = CA(PVC)+22+VERM.
_PI_COMPOSITE = re.compile(
    r"(CA|CB|CF|CT|CV)\s*([0-9][0-9,.]*)?\s*([A-Z]{4})?"
    r"(-\s*\d{3,5})?\s*(/\s*\d{1,2}\s*/\s*\d{1,2})?\s*"
    r"(-\s*\d{2,4}\s*-\s*\d{2,4})?",
    re.IGNORECASE,
)


def validate_pi_description(
    product_code: str, description: str | None
) -> DescriptionCheck:
    """50xx intermediate canonical segment check (concatenated prefix)."""
    code = (product_code or "").strip()
    desc = (description or "").strip()
    if not _PI_FAMILY.match(code):
        return DescriptionCheck(
            key="pi_description",
            status="NOT_APPLICABLE",
            summary="Código fora da família 50xx.",
        )
    if not desc:
        return DescriptionCheck(
            key="pi_description",
            status="INCONCLUSIVE",
            summary="Descrição cadastral ausente — verificação impossível.",
        )
    upper = desc.upper()
    match = _PI_COMPOSITE.search(upper)
    found_isolation = match.group(1).upper() if match else None
    found_gauge = (match.group(2) or "").strip() if match else ""
    found_color = (match.group(3) or "").upper() if match else ""
    found_length = bool(match and match.group(4))
    segments: dict[str, str | bool] = {
        "family": code[:4],
        "isolation": found_isolation or "absent",
        "gauge": found_gauge or "absent",
        "color4": found_color or "absent",
        "length_mm": "present" if found_length else "absent",
        "decape": "present" if match and match.group(5) else "absent",
        "terminals": "present" if match and match.group(6) else "absent",
    }
    findings: list[str] = []
    if not found_isolation:
        findings.append(
            "segmento isolação CA/CB/CF/CT/CV ausente ou inválido"
        )
    else:
        # Isolation invalid only if a *different* 2-letter token appears
        # where isolation should be — CA/CB/CF/CT/CV are the valid set.
        if found_isolation not in _PI_ISOLATION:
            findings.append(f"isolação '{found_isolation}' inválida")
    if not found_gauge:
        findings.append("bitola não identificada junto à isolação")
    if not found_color:
        findings.append("cor de 4 letras ausente no segmento concatenado")
    if not found_length:
        findings.append("comprimento (mm) não identificado")
    status = "WARNING" if findings else "PASS"
    return DescriptionCheck(
        key="pi_description",
        status=status,
        summary=(
            f"Família {code[:4]}: segmentos={segments}; "
            + ("ausências: " + "; ".join(findings) if findings else
               "segmentos canônicos identificados (prefixo concatenado).")
        ),
    )
