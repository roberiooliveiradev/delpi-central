#!/usr/bin/env python3
"""Gate de paginação centralizada na api-delpi.

Uso:
  python scripts/audit_pagination_tiers.py --check
  python scripts/audit_pagination_tiers.py --check-complete
  python scripts/audit_pagination_tiers.py --report

--check            inventário ↔ tiers JSON + factories sane
--check-complete   zero Query literal (page_size/limit/…) + zero envelope ad hoc
                   (allowlist mínima: to_dict wrappers / full-tree scalar)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
HTTP_ROOT = API_ROOT / "app" / "interface" / "http"
CONTENT = API_ROOT / "app" / "content"

INBOUND_INV = CONTENT / "pagination_inbound_inventory.json"
OUTBOUND_INV = CONTENT / "pagination_outbound_inventory.json"
TIERS = CONTENT / "pagination_tiers.json"

_PARAM_QUERY = re.compile(
    r"(page_size|limit|top_limit|history_limit|details_limit)\s*:\s*[^=]+=\s*Query\s*\("
)
_INLINE_PAGINATION = re.compile(r'"pagination"\s*:\s*\{(?!\*\*)')

# Files allowed to keep non-builder pagination construction (none expected after migration).
OUTBOUND_ALLOWLIST: frozenset[str] = frozenset()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_inventory_vs_tiers() -> list[str]:
    errors: list[str] = []
    inbound = _load_json(INBOUND_INV)
    tiers = _load_json(TIERS).get("tiers") or {}
    if inbound.get("count") != len(inbound.get("entries") or []):
        errors.append(
            f"inbound count mismatch: count={inbound.get('count')} entries={len(inbound.get('entries') or [])}"
        )
    for entry in inbound.get("entries") or []:
        tid = entry.get("tierId")
        if tid not in tiers:
            errors.append(f"inbound tier missing in pagination_tiers.json: {tid} ({entry.get('file')})")
            continue
        tier = tiers[tid]
        if tier.get("param") != entry.get("param"):
            errors.append(f"param mismatch for {tid}: tier={tier.get('param')} inv={entry.get('param')}")
        if tier.get("default") != entry.get("defaultResolved"):
            errors.append(
                f"default mismatch for {tid}: tier={tier.get('default')} inv={entry.get('defaultResolved')}"
            )
        if tier.get("le") != entry.get("leResolved"):
            errors.append(f"le mismatch for {tid}: tier={tier.get('le')} inv={entry.get('leResolved')}")
    outbound = _load_json(OUTBOUND_INV)
    if outbound.get("count") != len(outbound.get("entries") or []):
        errors.append(
            f"outbound count mismatch: count={outbound.get('count')} entries={len(outbound.get('entries') or [])}"
        )
    return errors


def check_inbound_literals() -> list[str]:
    hits: list[str] = []
    for path in HTTP_ROOT.rglob("*.py"):
        if path.name == "pagination_query.py":
            continue
        text = path.read_text(encoding="utf-8")
        for match in _PARAM_QUERY.finditer(text):
            line = text[: match.start()].count("\n") + 1
            hits.append(f"{path.relative_to(API_ROOT)}:{line}")
    return hits


def check_outbound_adhoc() -> list[str]:
    hits: list[str] = []
    outbound = _load_json(OUTBOUND_INV)
    for entry in outbound.get("entries") or []:
        rel = entry["file"]
        if rel in OUTBOUND_ALLOWLIST:
            continue
        path = API_ROOT / rel
        if not path.exists():
            hits.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        classification = entry.get("classification")
        if classification in {
            "build_operational_pagination",
            "build_has_next_pagination",
            "build_pagination",
        }:
            # Adapters must ultimately call the builder (directly or via import chain).
            if classification == "build_pagination" and "PaginationEnvelopeBuilder" not in text:
                hits.append(f"{rel}: build_pagination without PaginationEnvelopeBuilder")
            continue
        if "PaginationEnvelopeBuilder" not in text and not re.search(
            r'"pagination"\s*:\s*\w[\w\.]*\.to_dict\(\)', text
        ):
            hits.append(f"{rel}: missing PaginationEnvelopeBuilder / to_dict")
            continue
        for match in _INLINE_PAGINATION.finditer(text):
            # skip if immediately followed by builder on same structural block — already excluded **
            hits.append(f"{rel}: inline pagination dict at offset {match.start()}")
    return hits


def report() -> int:
    inbound = _load_json(INBOUND_INV)
    outbound = _load_json(OUTBOUND_INV)
    tiers = _load_json(TIERS).get("tiers") or {}
    print(f"inbound entries: {inbound.get('count')}")
    print(f"outbound entries: {outbound.get('count')}")
    print(f"tiers: {len(tiers)}")
    print("top inbound tiers:")
    for tid, n in Counter(e["tierId"] for e in inbound["entries"]).most_common(10):
        print(f"  {n:3d}  {tid}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-complete", action="store_true")
    args = parser.parse_args(argv)

    if not any([args.report, args.check, args.check_complete]):
        parser.print_help()
        return 2

    if args.report:
        return report()

    errors: list[str] = []
    if args.check or args.check_complete:
        errors.extend(check_inventory_vs_tiers())

    if args.check_complete:
        literals = check_inbound_literals()
        if literals:
            errors.append(f"literal Query pagination params ({len(literals)}):")
            errors.extend(f"  {h}" for h in literals[:40])
        adhoc = check_outbound_adhoc()
        if adhoc:
            errors.append(f"adhoc pagination envelopes ({len(adhoc)}):")
            errors.extend(f"  {h}" for h in adhoc[:40])

    if errors:
        print("FAIL audit_pagination_tiers:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    mode = "--check-complete" if args.check_complete else "--check"
    print(f"OK audit_pagination_tiers {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
