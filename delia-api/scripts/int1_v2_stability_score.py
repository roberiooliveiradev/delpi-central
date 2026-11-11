#!/usr/bin/env python3
"""Offline objective rubric scoring for INT-1 v2 stability artifacts.

Experiment-review only — does not change Agent runtime.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def _g(s: str | None) -> str:
    return (s or "").casefold()


def _grounded(run: dict) -> bool:
    g = str(run.get("grounding") or "")
    return "GROUNDED" in g and "NON_" not in g


def _first(run: dict) -> str:
    return str(run.get("first_mcp_target") or "")


def _lim(run: dict) -> str:
    return " ".join(str(x) for x in (run.get("limitations") or []))


def _head(run: dict) -> str:
    return str(run.get("content_head") or "")


def _looks_dashboard_metrics(text: str) -> bool:
    t = _g(text)
    return any(
        k in t
        for k in (
            "economia liquida",
            "solucoes implementadas",
            "horas economizadas",
            "ganho capacidade",
        )
    )


def _looks_structure(text: str) -> bool:
    t = _g(text)
    return any(
        k in t
        for k in (
            "estrutura",
            "componente",
            "árvore",
            "arvore",
            "bom",
            "relação",
            "relacao",
        )
    ) or bool(re.search(r"\b10\d{6}\b", text or ""))


def _looks_process_list(text: str) -> bool:
    t = _g(text)
    return "proc-" in t or "processo" in t


def _looks_playlist(text: str) -> bool:
    return "playlist" in _g(text)


def _looks_description(text: str) -> bool:
    t = _g(text)
    return "descri" in t or "chicote" in t


def _looks_format_catalog(text: str) -> bool:
    t = _g(text)
    if _looks_dashboard_metrics(text):
        return False
    return any(
        k in t
        for k in (
            "formato",
            "visualiza",
            "block_type",
            "catálogo",
            "catalogo",
            "display",
        )
    )


def _is_env_catalog_failure(run: dict, lim: str) -> bool:
    lim_l = lim.casefold()
    if "catalog_failure:mcp_authentication_failed" in lim_l:
        return True
    if "delpi_source_unverified" in lim_l and int(run.get("tool_calls") or 0) == 0:
        return True
    if "falha de autenticação" in lim_l or "falha de autenticacao" in lim_l:
        return True
    return False


def score_run(run: dict) -> dict:
    sid = run["scenario_id"]
    grounded = _grounded(run)
    first = _first(run)
    head = _head(run)
    lim = _lim(run)
    err = run.get("error")
    owner_errs = [e for e in (run.get("owner_errors") or []) if e]

    tool_sel = "INCONCLUSIVE"
    evidence = "INCONCLUSIVE"
    objective = "INCONCLUSIVE"
    args = "VALID" if not owner_errs else "INVALID"
    if not run.get("tool_call_order"):
        args = "NOT_OBSERVED"
    first_div = None
    causal = "UNDETERMINED"
    env_invalid = _is_env_catalog_failure(run, lim)
    if env_invalid:
        return {
            "run_id": run["run_id"],
            "scenario_id": sid,
            "repetition_id": run["repetition_id"],
            "TOOL_SELECTION": "INCONCLUSIVE",
            "ARGUMENT_VALIDITY": "NOT_OBSERVED",
            "OWNER_EVIDENCE": "NONE",
            "GROUNDING": "GROUNDED" if grounded else "NON_GROUNDED",
            "OBJECTIVE_SATISFACTION": "INCONCLUSIVE",
            "FIRST_MATERIAL_DIVERGENCE": "mcp_catalog_or_auth_failure",
            "CAUSAL_HYPOTHESIS": "EVAL_ENVIRONMENT_OR_TRACE",
            "GROUNDED_WITHOUT_OBJECTIVE": False,
            "ENV_INVALID": True,
            "first_mcp_target": first,
            "tool_calls": run.get("tool_calls"),
            "elapsed_s": run.get("elapsed_s"),
            "llm_request_count": (run.get("llm_runs") or {}).get("count"),
        }

    if sid in ("P1_product_structure", "G1_semantic_reword_structure"):
        if first.startswith("davi:"):
            tool_sel = "SUITABLE"
        elif first.startswith("teo:") or first.startswith("vista:"):
            tool_sel = (
                "PARTIALLY_SUITABLE"
                if grounded and _looks_structure(head)
                else "UNSUITABLE"
            )
            first_div = f"first_tool={first}"
        if grounded and _looks_structure(head):
            evidence = "AUTHORITATIVE_RELEVANT"
            objective = (
                "PARTIAL"
                if "owner_result_incomplete" in lim or "coverage_unknown" in lim
                else "SATISFIED"
            )
            causal = (
                "OWNER_CONTRACT_OR_RESULT"
                if "owner_result_incomplete" in lim
                else "UNDETERMINED"
            )
        elif grounded and _looks_description(head) and not _looks_structure(head):
            evidence = "RELATED_INSUFFICIENT"
            objective = "NOT_SATISFIED"
            first_div = first_div or "description_instead_of_structure"
            causal = "INT1_SELECTION"
        elif not grounded:
            evidence = "NONE" if "clarification" in lim else "RELATED_INSUFFICIENT"
            objective = "NOT_SATISFIED"
            causal = "INT1_SELECTION"

    elif sid == "P2_transformation_processes":
        if first.startswith("teo:"):
            tool_sel = "SUITABLE"
        else:
            tool_sel = "UNSUITABLE"
            first_div = f"first_tool={first}"
            causal = "INT1_SELECTION"
        if grounded and _looks_process_list(head) and not _looks_dashboard_metrics(head):
            evidence = "AUTHORITATIVE_RELEVANT"
            objective = "PARTIAL" if "result_truncated" in lim else "SATISFIED"
            if "result_truncated" in lim:
                causal = "INT1_INVESTIGATION_CONTINUITY"
        elif grounded and _looks_dashboard_metrics(head):
            evidence = "RELATED_INSUFFICIENT"
            objective = "NOT_SATISFIED"
            first_div = "dashboard_metrics_for_registry"
            causal = "INT1_SELECTION"
        elif not grounded:
            evidence = "NONE"
            objective = "NOT_SATISFIED"
            if causal == "UNDETERMINED":
                causal = "INT1_SELECTION"

    elif sid == "P3_visualization_formats":
        if first.startswith("vista:"):
            tool_sel = "SUITABLE"
        elif first.startswith("teo:analyze"):
            tool_sel = "UNSUITABLE"
            first_div = f"first_tool={first}"
            causal = "INT1_SELECTION"
        else:
            tool_sel = "PARTIALLY_SUITABLE"
        if grounded and _looks_dashboard_metrics(head):
            evidence = "RELATED_INSUFFICIENT"
            objective = "NOT_SATISFIED"
            first_div = first_div or "dashboard_metrics_as_formats"
            causal = "EVIDENCE_COVERAGE_ASSESSMENT_GAP"
        elif grounded and _looks_format_catalog(head):
            evidence = "AUTHORITATIVE_RELEVANT"
            objective = "PARTIAL" if "coverage_unknown" in lim else "SATISFIED"
        elif grounded and _looks_playlist(head):
            evidence = "RELATED_INSUFFICIENT"
            objective = "NOT_SATISFIED"
            first_div = first_div or "playlist_instead_of_formats"
            causal = "INT1_SELECTION"
        elif not grounded:
            evidence = (
                "DISCOVERY_ONLY"
                if "clarification" in lim or "discovery" in lim.casefold()
                else "NONE"
            )
            objective = "NOT_SATISFIED"
            if causal == "UNDETERMINED":
                causal = "INT1_SELECTION"

    elif sid == "H1_product_description":
        tool_sel = "SUITABLE" if first.startswith("davi:") else "PARTIALLY_SUITABLE"
        if grounded and (_looks_description(head) or "90260921" in head):
            evidence = "AUTHORITATIVE_RELEVANT"
            objective = (
                "SATISFIED"
                if "descri" in _g(head) or "chicote" in _g(head)
                else "PARTIAL"
            )
        elif not grounded:
            evidence = "NONE"
            objective = "NOT_SATISFIED"
            causal = "INT1_SELECTION"

    elif sid == "H2_missing_product_structure":
        tool_sel = (
            "SUITABLE"
            if first.startswith("davi:") or not first
            else "PARTIALLY_SUITABLE"
        )
        if not grounded and (
            "00000000" in head
            or "não encontr" in _g(head)
            or "nao encontr" in _g(head)
            or "not_found" in lim.casefold()
            or "clarification" in lim
            or "uncovered" in lim
        ):
            evidence = "NONE"
            objective = "SATISFIED"
        elif grounded and _looks_structure(head) and "00000000" not in (head + lim):
            evidence = "RELATED_INSUFFICIENT"
            objective = "NOT_SATISFIED"
            first_div = "fabricated_or_wrong_product"
            causal = "INT1_SELECTION"
        elif not grounded:
            evidence = "NONE"
            objective = "SATISFIED"
        else:
            objective = "INCONCLUSIVE"

    elif sid == "H3_vista_playlists":
        if first.startswith("vista:"):
            tool_sel = "SUITABLE"
        else:
            tool_sel = "UNSUITABLE"
            first_div = f"first_tool={first}"
            causal = "INT1_SELECTION"
        if grounded and _looks_playlist(head):
            evidence = "AUTHORITATIVE_RELEVANT"
            objective = (
                "PARTIAL"
                if "coverage_unknown" in lim or "truncat" in lim
                else "SATISFIED"
            )
        elif grounded and _looks_dashboard_metrics(head):
            evidence = "RELATED_INSUFFICIENT"
            objective = "NOT_SATISFIED"
            causal = "EVIDENCE_COVERAGE_ASSESSMENT_GAP"
        elif not grounded:
            evidence = "NONE"
            objective = "NOT_SATISFIED"

    elif sid == "H4_teo_dashboard_summary":
        if "teo:analyze" in first or first.startswith("teo:"):
            tool_sel = "SUITABLE"
        else:
            tool_sel = "UNSUITABLE"
            first_div = f"first_tool={first}"
            causal = "INT1_SELECTION"
        if grounded and (
            _looks_dashboard_metrics(head)
            or "indicador" in _g(head)
            or "resumo" in _g(head)
        ):
            evidence = "AUTHORITATIVE_RELEVANT"
            objective = "PARTIAL" if "result_truncated" in lim else "SATISFIED"
        elif not grounded:
            evidence = "NONE"
            objective = "NOT_SATISFIED"

    if err:
        objective = "INCONCLUSIVE"
        causal = "EVAL_ENVIRONMENT_OR_TRACE"

    grounded_wo = grounded and objective == "NOT_SATISFIED"
    return {
        "run_id": run["run_id"],
        "scenario_id": sid,
        "repetition_id": run["repetition_id"],
        "TOOL_SELECTION": tool_sel,
        "ARGUMENT_VALIDITY": args,
        "OWNER_EVIDENCE": evidence,
        "GROUNDING": "GROUNDED" if grounded else "NON_GROUNDED",
        "OBJECTIVE_SATISFACTION": objective,
        "FIRST_MATERIAL_DIVERGENCE": first_div,
        "CAUSAL_HYPOTHESIS": causal,
        "GROUNDED_WITHOUT_OBJECTIVE": grounded_wo,
        "ENV_INVALID": False,
        "first_mcp_target": first,
        "tool_calls": run.get("tool_calls"),
        "elapsed_s": run.get("elapsed_s"),
        "llm_request_count": (run.get("llm_runs") or {}).get("count"),
    }


def main() -> int:
    artifact = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "delia-api/.battery/int1-v2-stability/stability-comparison.json"
    )
    data = json.loads(artifact.read_text(encoding="utf-8"))
    scored = [score_run(r) for r in data.get("runs") or []]
    by: dict[str, list] = defaultdict(list)
    for s in scored:
        by[s["scenario_id"]].append(s)
    summary = {}
    for sid, rows in by.items():
        valid = [r for r in rows if not r.get("ENV_INVALID")]
        c = Counter(r["OBJECTIVE_SATISFACTION"] for r in rows)
        cv = Counter(r["OBJECTIVE_SATISFACTION"] for r in valid)
        gwo = sum(1 for r in rows if r["GROUNDED_WITHOUT_OBJECTIVE"])
        firsts = Counter(r["first_mcp_target"] for r in rows)
        firsts_v = Counter(r["first_mcp_target"] for r in valid)
        summary[sid] = {
            "n": len(rows),
            "n_valid_env": len(valid),
            "n_env_invalid": sum(1 for r in rows if r.get("ENV_INVALID")),
            "SATISFIED": c.get("SATISFIED", 0),
            "PARTIAL": c.get("PARTIAL", 0),
            "NOT_SATISFIED": c.get("NOT_SATISFIED", 0),
            "INCONCLUSIVE": c.get("INCONCLUSIVE", 0),
            "valid_env_objectives": dict(cv),
            "grounded_without_objective": gwo,
            "first_tool_distribution": dict(firsts),
            "first_tool_distribution_valid_env": dict(firsts_v),
            "tool_calls": [r["tool_calls"] for r in rows],
            "latency_s": [r["elapsed_s"] for r in rows],
            "causal": dict(Counter(r["CAUSAL_HYPOTHESIS"] for r in rows)),
        }
    out = {
        "scoring_kind": "deterministic_heuristic_review_proposal",
        "authority": "NOT_FINAL_requires_human_review",
        "env_invalid_total": sum(1 for r in scored if r.get("ENV_INVALID")),
        "scored_runs": scored,
        "per_scenario": summary,
    }
    out_path = artifact.with_name("stability-rubric-scores.json")
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"per_scenario": summary}, ensure_ascii=False, indent=2))
    print(f"STABILITY_SCORES_PATH={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
