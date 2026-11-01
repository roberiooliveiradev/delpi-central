#!/usr/bin/env python3
"""Emit auditable eval artifacts from a local_orchestration runs.json —
one .json + one .md per scenario plus a human-review index (Doc 211 §13/15)."""
import json
import sys
from pathlib import Path

OWNER = {}
for i, spec in enumerate(("caio", "clara", "suri", "eva", "teo", "vista", "davi")):
    for n in range(1 + i * 4, 5 + i * 4):
        OWNER[f"cmp_{n:02d}"] = spec


def _load_questions() -> dict[str, str]:
    """Extract verbatim questions from the DOC211_CORPUS block embedded
    in the eval harness (single source — never retyped)."""
    import re
    src = Path(__file__).with_name(
        "local_orchestration_reliability_eval.py"
    ).read_text(encoding="utf-8")
    return {
        m.group(1): m.group(2)
        for m in re.finditer(
            r'_x\("(cmp_\d+)", "(.*?)",\s*\n\s*"composite"', src, re.S
        )
    }


def main() -> None:
    runs_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(runs_path.read_text())
    runs = data.get("runs", data if isinstance(data, list) else [])
    questions = _load_questions()
    index = []
    for r in runs:
        sid = r.get("scenario") or r.get("sid") or "unknown"
        cid = sid.upper().replace("_", "-")
        cls = r.get("classification", {})
        outcome = cls.get("outcome") or r.get("outcome") or "UNKNOWN"
        first = cls.get("first_divergent") or r.get("first_divergent") or ""
        invokes = r.get("invokes", [])
        caps = [i.get("capability_id") for i in invokes if i.get("capability_id")]
        content = r.get("content") or "NO_FINAL_RESPONSE"
        payload = {
            "scenario_id": cid,
            "specialist": OWNER.get(sid, "?"),
            "run_number": r.get("run", 0),
            "question_full_text": questions.get(sid, ""),
            "outcome": outcome,
            "first_divergence": first,
            "capabilities_invoked": caps,
            "invoke_statuses": [
                {
                    "capability_id": i.get("capability_id"),
                    "status": i.get("status"),
                    "args": i.get("args"),
                }
                for i in invokes
            ],
            "response_full_text": content,
            "grounding": str(r.get("grounding", "")),
            "limitations": r.get("limitations", []),
            "elapsed_ms": r.get("elapsed_ms"),
            "error": r.get("error"),
        }
        (out_dir / f"{cid}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        cap_lines = [f"- `{c}`" for c in caps] or ["- (nenhuma)"]
        md = [
            f"# {cid} — {payload['specialist'].upper()}",
            "",
            f"**Outcome:** {outcome}   **First divergence:** {first or '—'}   "
            f"**Elapsed:** {payload['elapsed_ms']} ms",
            "",
            "## Pergunta original",
            "",
            questions.get(sid, "(question unavailable)"),
            "",
            "## Capabilities invocadas",
            "",
            *cap_lines,
            "",
            "## Resposta integral da DÉLIA",
            "",
            content,
        ]
        (out_dir / f"{cid}.md").write_text("\n".join(md), encoding="utf-8")
        index.append(
            {
                "scenario_id": cid,
                "specialist": payload["specialist"],
                "outcome": outcome,
                "first_divergence": first,
                "capabilities": caps,
                "elapsed_ms": payload["elapsed_ms"],
                "response_file": f"{cid}.md",
            }
        )
    (out_dir.parent / "scenario-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2)
    )
    counts = {}
    for e in index:
        counts[e["outcome"]] = counts.get(e["outcome"], 0) + 1
    print(json.dumps({"scenarios": len(index), "outcomes": counts}))


if __name__ == "__main__":
    main()
