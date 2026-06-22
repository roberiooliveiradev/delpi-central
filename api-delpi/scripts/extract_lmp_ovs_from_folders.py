#!/usr/bin/env python3
"""Extrai códigos OV dos RQ-060 em pastas LMP Ano (controle interno maio/2026).

Uso:
  pip install python-docx
  python extract_lmp_ovs_from_folders.py "/mnt/x/ENGENHARIA/1 LMP's/LMP 2026"

Saída: JSON com OVs por pasta (campo OV do RQ-060 + números 6 dígitos no texto).
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

INTERNAL_CONTROL = [
    {"code": "070 26", "client": "flextronic", "open": "20260504"},
    {"code": "071 26", "client": "3RHO", "open": "20260504"},
    {"code": "072 26", "client": "WEG Linhares", "open": "20260506", "ref": "19381065"},
    {"code": "073 26", "client": "Wanke", "open": "20260508"},
    {"code": "074 26", "client": "Weg Motores", "open": "20260508"},
    {"code": "075 26", "client": "WEG Linhares", "open": "20260512", "ref": "90264221"},
    {"code": "076 26", "client": "WEG Linhares", "open": "20260513", "ref": "19373355"},
    {"code": "077 26", "client": "WEG Linhares", "open": "20260514", "ref": "90263991"},
    {"code": "078 26", "client": "Buhler", "open": "20260514"},
    {"code": "079 26", "client": "WEG Linhares", "open": "20260515", "ref": "90264229"},
    {"code": "080 26", "client": "WEG Linhares", "open": "20260519"},
    {"code": "081 26", "client": "WEG Linhares", "open": "20260520"},
    {"code": "082 26", "client": "WEG Linhares", "open": "20260522"},
    {"code": "083 26", "client": "WEG Energia", "open": "20260525"},
    {"code": "084 26", "client": "WEG Energia", "open": "20260525"},
    {"code": "085 26", "client": "WEG Energia", "open": "20260525"},
    {"code": "086 26", "client": "WEG Linhares", "open": "20260525"},
]

OV_PATTERN = re.compile(r"\b(\d{6})\b")
LMP_FOLDER_PATTERN = re.compile(r"LMP\s*(\d{3})\s*26", re.I)


def _docx_plaintext(path: Path) -> str:
    """Lê texto de .docx sem python-docx (zip + document.xml)."""
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    parts = []
    for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
        if node.text:
            parts.append(node.text)
        if node.tail:
            parts.append(node.tail)
    return " ".join(parts)


def _find_folder(base: Path, lmp_code: str) -> Path | None:
    num = lmp_code.split()[0]  # "073"
    for candidate in base.iterdir():
        if not candidate.is_dir():
            continue
        m = LMP_FOLDER_PATTERN.search(candidate.name)
        if m and m.group(1) == num:
            return candidate
    return None


def _find_rq060(folder: Path) -> list[Path]:
    hits: list[Path] = []
    for path in folder.rglob("*"):
        if path.suffix.lower() != ".docx":
            continue
        name = path.name.upper()
        if "RQ-060" in name or "RQ060" in name or "ANÁLISE CRÍTICA" in name or "ANALISE CRITICA" in name:
            hits.append(path)
    return hits


def _extract_ovs(text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for m in OV_PATTERN.finditer(text):
        ov = m.group(1)
        if ov not in seen:
            seen.add(ov)
            ordered.append(ov)
    return ordered


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(f"Uso: {sys.argv[0]} <base_lmp_2026>")
    base = Path(sys.argv[1])
    if not base.is_dir():
        raise SystemExit(f"Pasta não encontrada: {base}")

    report: list[dict] = []
    all_ovs: set[str] = set()

    for row in INTERNAL_CONTROL:
        folder = _find_folder(base, row["code"])
        entry: dict = {**row, "folder_path": str(folder) if folder else None, "rq060_files": [], "ovs": [], "error": None}
        if not folder:
            entry["error"] = "pasta_nao_encontrada"
            report.append(entry)
            continue

        rq_files = _find_rq060(folder)
        entry["rq060_files"] = [str(p.relative_to(folder)) for p in rq_files]
        if not rq_files:
            entry["error"] = "rq060_nao_encontrado"
            report.append(entry)
            continue

        ovs: list[str] = []
        for doc in rq_files:
            try:
                text = _docx_plaintext(doc)
            except Exception as exc:  # noqa: BLE001
                entry.setdefault("read_errors", []).append(f"{doc.name}: {exc}")
                continue
            ovs.extend(_extract_ovs(text))
        # dedupe preserving order
        deduped: list[str] = []
        seen: set[str] = set()
        for ov in ovs:
            if ov not in seen:
                seen.add(ov)
                deduped.append(ov)
        entry["ovs"] = deduped
        all_ovs.update(deduped)
        report.append(entry)

    out = {
        "base_path": str(base),
        "folder_count": len(INTERNAL_CONTROL),
        "folders_with_ovs": sum(1 for r in report if r.get("ovs")),
        "unique_ovs": sorted(all_ovs),
        "unique_ov_count": len(all_ovs),
        "items": report,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
