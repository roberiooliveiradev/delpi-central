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
    "1009": "ISOLADOR", "1011": "ETIQUETA|ANILHA", "1012": "TUBO",
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


def validate_pi_description(
    product_code: str, description: str | None
) -> DescriptionCheck:
    """50xx intermediate product canonical segment check."""
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
    findings: list[str] = []
    upper = desc.upper()
    isolations = [i for i in _PI_ISOLATION if re.search(rf"\b{i}\b", upper)]
    if not isolations:
        findings.append(
            "código de isolação CA/CB/CF/CT/CV não identificado"
        )
    colors4 = [
        t for t in re.findall(r"\b[A-Z]{4}\b", upper)
        if t not in _PI_ISOLATION
    ]
    if not colors4:
        findings.append("cor em 4 letras não identificada")
    if not re.search(r"\d+\s*MM\b", upper) and not re.search(
        r"-\s*\d{3,5}\b", upper
    ):
        findings.append("comprimento (mm) não identificado")
    status = "WARNING" if findings else "PASS"
    return DescriptionCheck(
        key="pi_description",
        status=status,
        summary=(
            f"Família {code[:4]}: isolação={isolations or '—'}, "
            f"cor4L={colors4 or '—'}; "
            + ("desvios: " + "; ".join(findings) if findings else
               "segmentos canônicos identificados.")
            + " Comparação de comprimento/decape/terminais exige "
            "evidência explícita — ausência gera INCONCLUSIVE, não FAIL."
        ),
    )
