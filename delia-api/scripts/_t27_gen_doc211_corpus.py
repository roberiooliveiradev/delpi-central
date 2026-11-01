#!/usr/bin/env python3
"""Extract the 28 verbatim composite questions from doc 211 and emit
the DOC211_CORPUS block for local_orchestration_reliability_eval.py."""
import re
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / (
    "docs/12-roadmap-e-evolucao/delia/corrections/"
    "mcp-contextual-intelligence-orchestration/"
    "211-personalized-mcp-composite-evaluation-question-bank.md"
)

text = DOC.read_text(encoding="utf-8")
blocks = re.findall(
    r"### (CMP-\d+) — [^\n]+\n\n\*\*Pergunta integral para a DÉLIA:\*\*\n\n((?:> .*\n)+)",
    text,
)
assert len(blocks) == 28, f"expected 28, got {len(blocks)}"

OWNER = {
    "CMP-01": "caio", "CMP-02": "caio", "CMP-03": "caio", "CMP-04": "caio",
    "CMP-05": "clara", "CMP-06": "clara", "CMP-07": "clara", "CMP-08": "clara",
    "CMP-09": "suri", "CMP-10": "suri", "CMP-11": "suri", "CMP-12": "suri",
    "CMP-13": "eva", "CMP-14": "eva", "CMP-15": "eva", "CMP-16": "eva",
    "CMP-17": "teo", "CMP-18": "teo", "CMP-19": "teo", "CMP-20": "teo",
    "CMP-21": "vista", "CMP-22": "vista", "CMP-23": "vista", "CMP-24": "vista",
    "CMP-25": "davi", "CMP-26": "davi", "CMP-27": "davi", "CMP-28": "davi",
}
CAPS = {
    "caio": "CAIO_CAPS", "clara": "CLARA_CAPS", "suri": "SURI_CAPS",
    "eva": "EVA_CAPS", "teo": "TEO_CAPS", "vista": "VISTA_READ_CAPS",
    "davi": "DAVI_CAPS",
}

lines = ["# Doc 211 corpus — 28 composite READ-only questions (verbatim).", "DOC211_CORPUS = ["]
for cid, qblock in blocks:
    question = " ".join(l[2:].strip() for l in qblock.splitlines()).strip()
    esc = question.replace("\\", "\\\\").replace('"', '\\"')
    owner = OWNER[cid]
    sid = "cmp_" + cid.split("-")[1]
    lines.append(
        f'    _x("{sid}", "{esc}",'
    )
    lines.append(
        f'       "composite", True, "any_read",'
    )
    lines.append(
        f'       allowed_caps={CAPS[owner]},'
    )
    lines.append(
        f'       expected={{"want_owner": "{owner}",'
        f' "require_business_result": True}}),'
    )
lines.append("]")
Path("/tmp/doc211_corpus.txt").write_text("\n".join(lines), encoding="utf-8")
print("wrote", len(blocks), "scenarios")
for cid, _ in blocks:
    print(cid, "->", "cmp_" + cid.split("-")[1], OWNER[cid])
