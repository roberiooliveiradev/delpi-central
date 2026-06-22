#!/usr/bin/env python3
"""Inventário de services domain/application — playbook 20.

Lista módulos sem referência estática para REVISÃO MANUAL.
Não autoriza remoção: validar fluxo (send/stream/simulate/skill/CI) antes de deletar — ver playbook §8.5.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
DOMAIN_SERVICES = APP / "domain/services"
APPLICATION_SERVICES = APP / "application/services"
BASELINE_PATH = ROOT / "docs/architecture/services-inventory-baseline.json"

LINE_THRESHOLD = 1200

DOMAIN_APPLICATION_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+app\.application\.",
    re.MULTILINE,
)

CONTENT_LOADER_SUFFIXES = ("_content_service", "_patterns_service")


def list_service_modules(base: Path) -> list[tuple[str, Path]]:
    modules: list[tuple[str, Path]] = []
    for path in sorted(base.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(APP.parent)
        mod = str(rel.with_suffix("")).replace("/", ".")
        modules.append((mod, path))
    return modules


def count_lines(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def classify_module(mod: str) -> str:
    name = mod.lower()
    if "_content_service" in name or name.endswith("_patterns_service"):
        return "content_loader"
    if "_intent_service" in name:
        return "intent"
    if "direct_answer" in name:
        return "direct_answer"
    if "_presenter" in name:
        return "presenter"
    if "_route_selection" in name:
        return "route_selection"
    if "llm_synthesis" in name:
        return "llm_synthesis"
    if name.startswith("chat_drawing") or "drawing_" in name:
        return "drawing"
    if "pdf" in name or "document_vision" in name:
        return "pdf_vision"
    if "presentation" in name:
        return "presentation"
    if "sql" in name:
        return "sql"
    if "web_search" in name:
        return "web_search"
    if "email" in name:
        return "email"
    if "memory" in name or "context" in name:
        return "memory_context"
    if "operational" in name or "external_action" in name:
        return "operational"
    if "turn_preparation" in name or "turn_completion" in name or "/chat_turn/" in name:
        return "turn"
    if "tool_context" in name:
        return "tool_context"
    if "admin" in name or "audit" in name or "metrics" in name:
        return "admin_metrics"
    if "knowledge" in name:
        return "knowledge"
    if "interactivity" in name or "follow_up" in name:
        return "interactivity"
    if "attachment" in name or "canvas" in name:
        return "attachments"
    if "onboarding" in name or "help" in name:
        return "help_onboarding"
    return "other"


def collect_sources() -> dict[Path, str]:
    sources: dict[Path, str] = {}
    for path in APP.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        sources[path] = path.read_text(encoding="utf-8", errors="replace")
    scripts_dir = ROOT / "scripts"
    if scripts_dir.is_dir():
        for path in scripts_dir.rglob("*.py"):
            sources[path] = path.read_text(encoding="utf-8", errors="replace")
    tests_dir = ROOT / "tests"
    if tests_dir.is_dir():
        for path in tests_dir.rglob("*.py"):
            sources[path] = path.read_text(encoding="utf-8", errors="replace")
    return sources


def count_module_refs(mod: str, sources: dict[Path, str], self_path: Path) -> dict[str, int]:
    short = mod.split(".")[-1]
    parent = ".".join(mod.split(".")[:-1])
    patterns = [
        f"from {mod} import",
        f"import {mod}",
        f"from {parent} import {short}",
    ]
    counts = {"app": 0, "scripts": 0, "tests": 0}
    for path, text in sources.items():
        if path == self_path:
            continue
        hits = sum(text.count(p) for p in patterns)
        if hits == 0:
            continue
        rel = str(path.relative_to(ROOT))
        if rel.startswith("scripts/"):
            counts["scripts"] += hits
        elif rel.startswith("tests/"):
            counts["tests"] += hits
        else:
            counts["app"] += hits
    return counts


def domain_application_violations() -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path in sorted(DOMAIN_SERVICES.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if DOMAIN_APPLICATION_PATTERN.search(text):
            violations.append({"file": str(path.relative_to(ROOT))})
    return violations


def content_loaders_in_application(modules: list[tuple[str, Path]]) -> list[str]:
    return [
        mod
        for mod, _ in modules
        if any(suffix in mod for suffix in CONTENT_LOADER_SUFFIXES)
    ]


def build_report() -> dict:
    sources = collect_sources()
    layers: dict[str, list[dict]] = {"domain": [], "application": []}

    for layer_name, base in (
        ("domain", DOMAIN_SERVICES),
        ("application", APPLICATION_SERVICES),
    ):
        for mod, path in list_service_modules(base):
            refs = count_module_refs(mod, sources, path)
            total_refs = sum(refs.values())
            lines = count_lines(path)
            layers[layer_name].append(
                {
                    "module": mod,
                    "file": str(path.relative_to(ROOT)),
                    "lines": lines,
                    "category": classify_module(mod),
                    "refs": refs,
                    "refsTotal": total_refs,
                    "unreferencedStatically": total_refs == 0,
                    "largeFile": lines > LINE_THRESHOLD,
                }
            )

    summary: dict[str, dict] = {}
    for layer_name, items in layers.items():
        cats: dict[str, int] = defaultdict(int)
        for item in items:
            cats[item["category"]] += 1
        summary[layer_name] = {
            "moduleCount": len(items),
            "categories": dict(sorted(cats.items(), key=lambda kv: -kv[1])),
            "unreferencedStatically": sum(1 for i in items if i["unreferencedStatically"]),
            "largeFiles": [i["module"] for i in items if i["largeFile"]],
        }

    return {
        "layers": layers,
        "summary": summary,
        "domainApplicationViolations": domain_application_violations(),
        "contentLoadersInApplication": content_loaders_in_application(
            list_service_modules(APPLICATION_SERVICES),
        ),
        "thresholds": {"largeFileLines": LINE_THRESHOLD},
    }


def print_summary(report: dict) -> None:
    for layer in ("domain", "application"):
        s = report["summary"][layer]
        print(f"\n=== {layer.upper()} ({s['moduleCount']} modules) ===")
        print(f"Sem ref estática (revisar fluxo antes de remover): {s['unreferencedStatically']}")
        print(f"Large files (>{LINE_THRESHOLD} lines): {len(s['largeFiles'])}")
        top_cats = list(s["categories"].items())[:8]
        print("Top categories:", ", ".join(f"{k}={v}" for k, v in top_cats))

    violations = report["domainApplicationViolations"]
    print(f"\nDomain → application imports: {len(violations)}")
    for v in violations[:10]:
        print(f"  {v['file']}")
    if len(violations) > 10:
        print(f"  ... +{len(violations) - 10} more")

    loaders = report["contentLoadersInApplication"]
    if loaders:
        print(f"\n*ContentService in application ({len(loaders)}):")
        for mod in loaders:
            print(f"  {mod}")

    unreferenced = [
        i
        for layer in report["layers"].values()
        for i in layer
        if i["unreferencedStatically"]
    ]
    if unreferenced:
        print(
            f"\nSem ref estática ({len(unreferenced)}) — NÃO remover sem validar fluxo (playbook §8.5):"
        )
        for item in sorted(unreferenced, key=lambda x: x["module"])[:20]:
            print(f"  {item['module']} ({item['lines']} lines)")
        if len(unreferenced) > 20:
            print(f"  ... +{len(unreferenced) - 20} more")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="Imprime resumo legível")
    parser.add_argument("--json", action="store_true", help="Imprime JSON completo")
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help=f"Grava baseline em {BASELINE_PATH.relative_to(ROOT)}",
    )
    args = parser.parse_args()

    report = build_report()

    if args.write_baseline:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Baseline written: {BASELINE_PATH}")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.summary or not args.write_baseline:
        print_summary(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
