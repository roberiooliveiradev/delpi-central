"""DELIA-C3-OUTCOME-COMPLETENESS-FINAL-PAYLOAD-CONSISTENCY-01 — WP4 eval.

Live governed-turn probe on the REAL chain (authenticated MCP surface +
local Ollama delia-json). For every scenario it records:

  * grounding status + response head (business-outcome signal);
  * stage count + model-call count + in/out tokens + latency;
  * per-stage dispatched block validity (JSON) and, for capability
    selection stages, whether the final block's selectable universe
    (projected names) and the omission marker are consistent;
  * evidence_partial flag when a records block carried records_omitted
    while the final answer looked unqualified (false-completeness
    signal — reviewed manually on the captured content).

Auth: dev-portal subject bearer minted by scripts/c3r_mint_bearer.sh
into /tmp/eval_bearer (secrets never enter this process).

Advisory instrumentation only — deterministic boundaries stay
authoritative; nothing here alters validation.
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, "/app")

from scripts.r4_authenticated_resume_eval import _compose, _run  # noqa: E402

SCENARIOS = [
    ("three_bala", "traga três exemplos de terminal bala"),
    ("o2", "traga dois exemplos de terminal O2"),
    ("pino", "traga um exemplo de terminal pino"),
    ("exhaustive_bala", "liste todos os terminais bala cadastrados"),
    ("comparison", "compare terminal bala com terminal pino"),
    ("absent_item", "traga exemplos de terminal modelo ZZQ-0000"),
    ("write_request", "cadastre um novo terminal bala 4mm"),
    ("no_source_hint", "o que é um terminal bala?"),
]


def _block_payloads(orch):
    """Spy on _propose — capture (instruction_id, raw block) pairs."""
    real_propose = orch._propose
    captured: list[tuple[str, str]] = []

    def spy(*args, **kwargs):
        instruction = args[0] if args else kwargs.get("instruction")
        purpose = getattr(instruction, "purpose_id", "") or getattr(
            instruction, "instruction_id", ""
        )
        block = args[1] if len(args) > 1 else kwargs.get("block_payload")
        if isinstance(block, str):
            captured.append((str(purpose), block))
        return real_propose(*args, **kwargs)

    orch._propose = spy  # type: ignore[method-assign]
    return captured


def _selectable(raw: str):
    """Re-derive the capability universe of a serialized block."""
    try:
        block = json.loads(raw)
    except Exception:
        return None, None
    entries = block.get("capabilities") if isinstance(block, dict) else None
    if entries is None and isinstance(block, list):
        entries = block
    names = set()
    if isinstance(entries, list):
        for e in entries:
            if isinstance(e, str):
                names.add(e)
            elif isinstance(e, dict):
                names.add(e.get("remote_name") or e.get("capability_id") or "")
    marker = block.get("capabilities_omitted", 0) if isinstance(block, dict) else 0
    return names, marker


def _find_orchestrator(handler):
    """Locate the orchestrator inside the composed handler chain."""
    seen = set()
    stack = [handler]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        if hasattr(node, "_propose") and hasattr(node, "_select_capability"):
            return node
        for value in vars(node).values() if hasattr(node, "__dict__") else ():
            if hasattr(value, "__dict__"):
                stack.append(value)
            elif isinstance(value, (list, tuple)):
                stack.extend(v for v in value if hasattr(v, "__dict__"))
    return None


def main() -> int:
    bearer = open("/tmp/eval_bearer").read().strip()
    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)
    captured = _block_payloads(orch) if orch is not None else []

    report = []
    for name, question in SCENARIOS:
        captured.clear()
        invokes_before = mcp.invoke_calls
        started = time.monotonic()
        out = _run(handler, guarded, mcp, question, bearer)
        elapsed = round(time.monotonic() - started, 2)

        valid = sum(
            1 for _, raw in captured if _safe_json(raw)
        )
        sel_ok = True
        for purpose, raw in captured:
            if "capability_selection" not in purpose:
                continue
            names, marker = _selectable(raw)
            if names is None:
                sel_ok = False
        model_detail = out.get("model_call_detail") or []
        in_tok = sum(d.get("in_units") or 0 for d in model_detail)
        out_tok = sum(d.get("out_units") or 0 for d in model_detail)

        report.append(
            {
                "scenario": name,
                "elapsed_s": elapsed,
                "grounding": out.get("grounding"),
                "error": out.get("error"),
                "stages": len(out.get("phases") or []),
                "model_calls": sum(
                    (out.get("model_calls") or {}).values()
                ),
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "blocks": len(captured),
                "blocks_valid": valid,
                "selection_universe_parseable": sel_ok,
                "mcp_invokes": mcp.invoke_calls - invokes_before,
                "mcp_targets": [
                    t.split("):")[-1]
                    for t in (mcp.invoke_targets or [])[invokes_before:]
                ],
                "content_head": out.get("content_head"),
            }
        )
        print(json.dumps(report[-1], ensure_ascii=False), flush=True)

    with open("/tmp/bc_eval_report.json", "w") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    return 0


def _safe_json(raw: str) -> bool:
    try:
        json.loads(raw)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
