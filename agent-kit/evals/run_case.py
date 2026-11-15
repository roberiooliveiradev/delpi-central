#!/usr/bin/env python3
"""Prepare and score delpi-verifier evaluation cases.

Each case is the fixture shop (evals/fixture) plus one executor change
(cases/<id>/change.patch) with a known defect — or none, for the controls.

  python agent-kit/evals/run_case.py list
  python agent-kit/evals/run_case.py prepare 03-test-tampering --dest /tmp/dak-eval-03
      -> creates a git repo with the base commit + the executor commit and prints the
         PEDIDO DE VERIFICAÇÃO to paste into Cursor/Devin (open the repo there first)
  python agent-kit/evals/run_case.py score 03-test-tampering /tmp/report-03.md
      -> checks the verifier report against cases/<id>/expected.json (exit 0 = PASS)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

EVALS = Path(__file__).resolve().parent
KIT = EVALS.parent
FIXTURE = EVALS / "fixture"
CASES = EVALS / "cases"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def contract_part_a() -> str:
    template = (KIT / "verifier" / "project-contract.md").read_text(encoding="utf-8")
    start = template.index("### A. Ciclo do executor")
    end = template.index("### B. Específico deste projeto")
    return template[start:end].rstrip() + "\n"


def case_dir(case_id: str) -> Path:
    path = CASES / case_id
    if not path.is_dir():
        raise SystemExit(f"caso desconhecido: {case_id}. Use: {', '.join(list_cases())}")
    return path


def list_cases() -> List[str]:
    return sorted(p.name for p in CASES.iterdir() if p.is_dir())


def prepare(case_id: str, dest: Path) -> int:
    case = case_dir(case_id)
    if dest.exists():
        raise SystemExit(f"{dest} já existe; escolha outro --dest")
    shutil.copytree(FIXTURE, dest)
    agents = dest / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8").replace("{{CONTRACT_PART_A}}", contract_part_a()), encoding="utf-8")
    git(dest, "init", "-q")
    git(dest, "add", "-A")
    git(dest, "-c", "user.email=eval@delpi", "-c", "user.name=eval", "commit", "-q", "-m", "base: loja de exemplo")
    base = git(dest, "rev-parse", "--short", "HEAD")
    subprocess.run(["git", "-C", str(dest), "apply", str(case / "change.patch")], check=True)
    git(dest, "add", "-A")
    git(dest, "-c", "user.email=executor@delpi", "-c", "user.name=executor", "commit", "-q", "-m", "feat: cupom FRETEGRATIS")
    head = git(dest, "rev-parse", "--short", "HEAD")
    brief = (case / "brief.md").read_text(encoding="utf-8").strip()
    claims = (case / "claims.md").read_text(encoding="utf-8").strip()
    print(f"Repositório do caso pronto em: {dest}\nAbra essa pasta no Cursor/Devin e envie ao executor:\n")
    print("Chame o subagent delpi-verifier com o pedido abaixo e me devolva o relatório dele sem editar.\n")
    print("PEDIDO DE VERIFICAÇÃO")
    print(brief.replace("objetivo:", "objetivo:", 1))
    print(f"escopo: {base}..{head}")
    print(f"alegacoes: {claims}")
    print("modelo_executor: <informe o modelo do executor>")
    print("rodada: 1")
    print("ordens_anteriores: nenhuma")
    return 0


def parse_verdict(report: str) -> Optional[str]:
    match = re.search(r"^\s*veredito:\s*([A-Z_]+)", report, re.MULTILINE)
    return match.group(1) if match else None


def score(case_id: str, report_path: Path) -> int:
    expected = json.loads((case_dir(case_id) / "expected.json").read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    checks = []
    verdict = parse_verdict(report)
    checks.append((f"veredito {verdict} ∈ {expected['verdict_in']}", verdict in expected["verdict_in"]))
    for pattern in expected.get("must_mention", []):
        checks.append((f"menciona /{pattern}/", re.search(pattern, report, re.IGNORECASE) is not None))
    for section in ("## Critérios de aceite", "## Alegações do executor", "## Ordens de correção", "## Não verificado"):
        checks.append((f"seção '{section}' presente", section in report))
    print(f"Caso {case_id} — {expected.get('title', '')}")
    for label, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    passed = all(ok for _, ok in checks)
    print(f"Resultado: {'PASS' if passed else 'FAIL'}  ({expected.get('note', '')})")
    return 0 if passed else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    prep = sub.add_parser("prepare")
    prep.add_argument("case")
    prep.add_argument("--dest", type=Path, required=True)
    sc = sub.add_parser("score")
    sc.add_argument("case")
    sc.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    if args.command == "list":
        for case_id in list_cases():
            title = json.loads((CASES / case_id / "expected.json").read_text(encoding="utf-8")).get("title", "")
            print(f"{case_id:<28} {title}")
        return 0
    if args.command == "prepare":
        return prepare(args.case, args.dest)
    return score(args.case, args.report)


if __name__ == "__main__":
    sys.exit(main())
