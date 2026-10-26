#!/usr/bin/env python3
"""Stage-1 isolation for the catalog presentation name-prior eval
(DELIA-C3-CATALOG-PRESENTATION-NAME-PRIOR-SENSITIVITY-EVAL-01).

Calls ``_select_group`` directly on the composed orchestrator under
instruction v23, varying ONLY non-authoritative presentation fields
of the projected catalog:

  real        — untouched baseline
  neutral     — group display_name → Group A/B/... (canonical
                capability_group_id, owner_ref, source_system,
                capability ids/remote names untouched)
  respforward — display_name ← owner-published responsibility
                excerpt (bounded, no new content)
  reorder     — serialized group list reversed inside the same
                projection (module-function seam, eval only)

For every call the REAL dispatched payload is captured (spy on
``_propose``): hash, chars, JSON validity, group ids present, scope
coverage, omission markers — per WP3 §17.

    python3 scripts/catalog_presentation_probe.py
        → /tmp/catalog_presentation_probe.json
"""

import hashlib
import json
import sys
from dataclasses import replace

sys.path.insert(0, "/app")

from scripts.r4_authenticated_resume_eval import _compose  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    _find_orchestrator,
    _mint_bearer,
)
from app.application.capability_provision import (  # noqa: E402
    orchestration as _orch_mod,
)
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

REPS = 5

# (prompt, expected_family) — record | doc | discovery | none
PROMPTS = [
    ("traga três exemplos de terminal bala", "record"),
    ("consulte o produto de código 10080092", "record"),
    ("me mostra ilhós pra cabo de 4 milímetros", "record"),
    ("busque TERM. BALA 0,50-2,27MM2", "record"),
    ("traga dois exemplos de abraçadeira cadastrados", "record"),
    ("o que é um terminal bala?", "doc"),
    ("como a DELPI denomina terminais de compressão?", "doc"),
    ("o que significa a sigla O2 na nomenclatura?", "doc"),
    (
        "use o mcp davi para descobrir como consultar produtos",
        "discovery",
    ),
    ("mostre terminais", "record"),
    ("bom dia! como vai você?", "none"),
    ("apague o produto de código 10080092", "none"),
]

GROUP_FAMILY = {
    "openapi:delpi": "record",
    "mcp:teo": "doc",
    "mcp:vista": "doc",
    "mcp:davi": "discovery",
}
RECORD_OK = {"record", "discovery"}

VARIANTS = ("real", "neutral", "respforward", "reorder")


def _present(group, variant, idx):
    if variant == "neutral":
        return replace(group, display_name=f"Group {chr(65 + idx)}")
    if variant == "respforward":
        parts = []
        for cap in group.capabilities:
            d = (cap.description or "").strip()
            if d:
                parts.append(d[:60])
            if len("; ".join(parts)) > 80:
                break
        return replace(
            group, display_name=("; ".join(parts)[:80] or "—")
        )
    return group


def _apply(groups, variant):
    if variant == "reorder":
        return dict(groups)  # handled at projection seam below
    return {
        k: _present(g, variant, i)
        for i, (k, g) in enumerate(sorted(groups.items()))
    }


def main() -> int:
    bearer = _mint_bearer()
    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)

    # ---- payload capture seam: record every select_group block
    real_propose = orch._propose  # noqa: SLF001
    captured: list[dict] = []

    def spy(*args, **kwargs):
        purpose = ""
        instr = args[0] if args else kwargs.get("instruction")
        block = args[1] if len(args) > 1 else kwargs.get(
            "block_payload"
        )
        kw_instr_id = kwargs.get("instruction_id", "")
        if kw_instr_id.endswith("select_group"):
            purpose = kw_instr_id
        proposal = real_propose(*args, **kwargs)
        if purpose or (
            kwargs.get("block_tag") == "capability_groups"
        ):
            entry = {}
            if isinstance(block, str):
                entry["payload_sha"] = hashlib.sha256(
                    block.encode()
                ).hexdigest()[:16]
                entry["payload_chars"] = len(block)
                try:
                    parsed = json.loads(block)
                    if isinstance(parsed, dict):
                        glist = parsed.get("capability_groups") or []
                    else:
                        glist = parsed
                    ids = [
                        g.get("capability_group_id")
                        for g in glist
                        if isinstance(g, dict)
                    ]
                    entry["group_ids"] = ids
                    entry["scope_present"] = sum(
                        1
                        for g in glist
                        if isinstance(g, dict) and g.get("scope")
                    )
                    entry["desc_nonempty"] = sum(
                        1
                        for g in glist
                        if isinstance(g, dict)
                        for c in g.get("capabilities", [])
                        if c.get("description")
                    )
                    entry["omitted"] = sum(
                        g.get("capabilities_omitted", 0)
                        for g in glist
                        if isinstance(g, dict)
                    )
                    entry["display_names"] = [
                        g.get("display_name")
                        for g in glist
                        if isinstance(g, dict)
                    ]
                    entry["json_valid"] = True
                except Exception:
                    entry["json_valid"] = False
            captured.append(entry)
        return proposal

    orch._propose = spy  # noqa: SLF001

    # ---- reorder seam at the projection function (eval only):
    real_summaries = _orch_mod._group_summaries

    def summaries_reordered(*args, **kwargs):
        payload = real_summaries(*args, **kwargs)
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            glist = parsed.get("capability_groups")
            if isinstance(glist, list):
                parsed["capability_groups"] = list(reversed(glist))
                return json.dumps(parsed, ensure_ascii=False)
            return payload
        if isinstance(parsed, list):
            return json.dumps(
                list(reversed(parsed)), ensure_ascii=False
            )
        return payload

    binding = bind_subject_bearer(bearer)
    try:
        groups, failures = orch._groups("pres-probe")  # noqa: SLF001
    finally:
        unbind_subject_bearer(binding)
    print(
        "GROUPS:",
        {k: len(g.capabilities) for k, g in groups.items()},
        "failures:", failures,
        flush=True,
    )

    results = []
    for variant in VARIANTS:
        if variant == "reorder":
            _orch_mod._group_summaries = summaries_reordered
            cat = dict(groups)
        else:
            _orch_mod._group_summaries = real_summaries
            cat = _apply(groups, variant)
        for prompt, expected in PROMPTS:
            for rep in range(REPS):
                captured.clear()
                status, key = orch._select_group(  # noqa: SLF001
                    prompt,
                    cat,
                    correlation=f"pres-{variant}-{rep}",
                )
                fam = GROUP_FAMILY.get(key) if key else None
                ok = (
                    (expected == "record" and fam in RECORD_OK)
                    or (expected != "record" and fam == expected)
                    or (expected == "none" and key is None)
                )
                payload = captured[-1] if captured else {}
                results.append(
                    {
                        "variant": variant,
                        "prompt": prompt,
                        "expected_family": expected,
                        "rep": rep,
                        "status": status,
                        "group": key,
                        "family": fam,
                        "ok": ok,
                        "payload": payload,
                    }
                )
                print(
                    json.dumps(results[-1], ensure_ascii=False),
                    flush=True,
                )

    _orch_mod._group_summaries = real_summaries

    with open("/tmp/catalog_presentation_probe.json", "w") as fh:
        json.dump(
            {
                "groups": {
                    k: len(g.capabilities)
                    for k, g in groups.items()
                },
                "results": results,
            },
            fh,
            ensure_ascii=False,
            indent=1,
        )
    print("TOTAL:", len(results), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
