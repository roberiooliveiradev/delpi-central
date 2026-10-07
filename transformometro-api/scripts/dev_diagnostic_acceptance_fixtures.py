#!/usr/bin/env python3
"""Deterministic Diagnostic acceptance fixtures — LOCAL DEV ONLY.

Strategy: stable semantic marker -> runtime discovery -> canonical create.
Acceptance fixtures are Diagnostics whose ``problem_statement`` starts with
``[ACCEPTANCE-FIXTURE]``; they are discovered at runtime via the canonical
``GET /transformometro/revisions/{id}/diagnostics`` route, so no hardcoded UUIDs are needed.

Idempotent: a second run finds the markers and creates nothing.
Cleanup: fixtures are identifiable by the marker prefix; they are read/mutate
safe acceptance data, isolated by marker — never delete business data.

Usage (local only, authenticated dev user via infra/scripts/get-dev-token.sh):

    TOKEN="$(bash infra/scripts/get-dev-token.sh)" \
    python3 transformometro-api/scripts/dev_diagnostic_acceptance_fixtures.py \
        --base-url http://localhost \
        --revision-id <dev revision uuid>

Creates on the given revision (if absent):
    [ACCEPTANCE-FIXTURE] baseline   — empty Diagnostic (finding/hypothesis source)
    [ACCEPTANCE-FIXTURE] populated  — Diagnostic with finding + hypothesis +
                                    validated conclusion designated as root cause
Discovery also reports whether the revision has zero non-fixture Diagnostics
(the ZERO case is any revision without Diagnostics — nothing is created there).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

MARKER = "[ACCEPTANCE-FIXTURE]"
API = "/apps/transformometro-api"


def _guard_local(base_url: str) -> None:
    if not base_url.startswith(("http://localhost", "http://127.0.0.1")):
        raise SystemExit(
            f"FAIL CLOSED: acceptance fixtures só rodam em localhost dev "
            f"(recebido: {base_url})"
        )


def _req(token: str, base: str, method: str, path: str,
         body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base + API + path, data=data, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-transformometro-client-id": "dev-acceptance-fixtures",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def _commit(token: str, base: str, handle: str) -> tuple[int, dict]:
    return _req(token, base, "POST", "/transformometro/governed-proposals/commit",
                {"proposal_handle": handle, "confirmation": True})


def _prepare_commit(token: str, base: str, diag_id: str, action: str,
                    payload: dict) -> dict:
    s, p = _req(token, base, "POST",
                f"/transformometro/diagnostics/{diag_id}/prepare",
                {"action": action, "payload": payload})
    if s != 200:
        raise SystemExit(f"prepare {action} falhou: {s} {str(p)[:200]}")
    handle = p["data"]["proposal_handle"]
    s, c = _commit(token, base, handle)
    if s != 200:
        raise SystemExit(f"commit {action} falhou: {s} {str(c)[:200]}")
    return c["data"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base-url", default="http://localhost")
    ap.add_argument("--revision-id", required=True,
                    help="dev revision uuid that will hold fixture Diagnostics")
    args = ap.parse_args()
    _guard_local(args.base_url)
    token = os.environ.get("TOKEN") or os.environ.get("ACCESS_TOKEN")
    if not token:
        raise SystemExit("Defina TOKEN (bash infra/scripts/get-dev-token.sh)")

    base = args.base_url
    rev = args.revision_id

    s, lst = _req(token, base, "GET",
                  f"/transformometro/revisions/{rev}/diagnostics")
    if s != 200:
        raise SystemExit(f"list falhou: {s} {str(lst)[:200]}")
    items = lst["data"].get("items") or lst["data"].get("diagnostics") or []
    fixtures = {d["problem_statement"]: d["diagnostic_id"]
                for d in items
                if str(d.get("problem_statement", "")).startswith(MARKER)}
    print(f"[fixtures] revision {rev}: {len(items)} diagnostics, "
          f"{len(fixtures)} acceptance fixtures")

    def ensure(statement: str) -> str:
        if statement in fixtures:
            print(f"[fixtures] exists: {statement[:50]}")
            return fixtures[statement]
        s, p = _req(token, base, "POST",
                    f"/transformometro/revisions/{rev}/diagnostics/prepare",
                    {"problem_statement": statement})
        if s != 200:
            raise SystemExit(f"prepare create falhou: {s} {str(p)[:200]}")
        d = p["data"]
        diag_id = (d.get("exact_change") or {}).get("diagnostic_id") \
            or (d.get("data") or {}).get("diagnostic_id") \
            or d.get("diagnostic_id")
        s, c = _commit(token, base, d["proposal_handle"])
        if s != 200:
            raise SystemExit(f"commit create falhou: {s} {str(c)[:200]}")
        print(f"[fixtures] created: {statement[:50]} -> {diag_id}")
        return diag_id

    baseline_id = ensure(f"{MARKER} baseline — controlada")
    populated_id = ensure(f"{MARKER} populated — estado completo")

    def _get(diag_id: str) -> dict:
        s, d = _req(token, base, "GET",
                    f"/transformometro/diagnostics/{diag_id}")
        if s != 200:
            raise SystemExit(f"get falhou: {s} {str(d)[:200]}")
        return d["data"]["diagnostic"]

    # Populate state-aware: aplica somente os passos faltantes.
    diag = _get(populated_id)
    if not diag.get("findings"):
        _prepare_commit(token, base, populated_id, "add_finding",
                        {"statement": f"{MARKER} achado observado",
                         "epistemic_state": "OBSERVED"})
        diag = _get(populated_id)
    marker_hyp = next(
        (h for h in diag.get("hypotheses", [])
         if str(h.get("statement", "")).startswith(MARKER)), None)
    if not marker_hyp:
        _prepare_commit(token, base, populated_id, "add_hypothesis",
                        {"statement": f"{MARKER} hipótese causal"})
        diag = _get(populated_id)
        marker_hyp = next(
            h for h in diag["hypotheses"]
            if str(h.get("statement", "")).startswith(MARKER))
    hyp_id = marker_hyp["hypothesis_id"]
    if marker_hyp.get("lifecycle") != "VALIDATED":
        _prepare_commit(token, base, populated_id, "validate_hypothesis",
                        {"hypothesis_id": hyp_id})
    marker_concl = next(
        (c for c in diag.get("conclusions", [])
         if str(c.get("statement", "")).startswith(MARKER)), None)
    if not marker_concl:
        _prepare_commit(token, base, populated_id, "add_conclusion",
                        {"statement": f"{MARKER} conclusão",
                         "rationale": "fixture controlada de aceitação",
                         "hypothesis_ids": [hyp_id],
                         "root_cause_hypothesis_id": hyp_id})
        diag = _get(populated_id)
        marker_concl = next(
            c for c in diag["conclusions"]
            if str(c.get("statement", "")).startswith(MARKER))
    if marker_concl.get("lifecycle") != "VALIDATED":
        _prepare_commit(token, base, populated_id, "validate_conclusion",
                        {"conclusion_id": marker_concl["conclusion_id"]})
    print("[fixtures] populated: finding+hypothesis(VALIDATED)+"
          "conclusion(VALIDATED,root_cause) garantidos")

    print(f"[fixtures] DONE baseline={baseline_id} populated={populated_id}")
    print("[fixtures] ZERO case: use qualquer revision dev sem Diagnostics "
          "(nada é criado para esse caso).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
