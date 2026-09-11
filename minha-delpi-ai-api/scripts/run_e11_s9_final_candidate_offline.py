#!/usr/bin/env python3
"""E11.S9 — final candidate offline battery on r1_r11_corpus_v2 + E11 sidecars.

J-R2: corpus ativo deve passar ChatRequiredDimensionsMatrixService antes dos harnesses.
v1 (371f0cfa…) permanece histórico e falha o gate de dimensões.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.domain.services.chat_required_dimensions_matrix_service import (  # noqa: E402
    ChatRequiredDimensionsMatrixService,
)
from app.domain.services.chat_evidence_reproducibility_service import (  # noqa: E402
    ChatEvidenceReproducibilityService,
)

EXPECTED_CORPUS_HASH = (
    "1147e05d6beae96dcf2322a08195f0bcc7a3727206418cd056692d570ce9523f"
)

# Sidecars that strengthen corpus proxies without mutating harnessRef freeze.
SIDECARS: list[dict] = [
    {
        "id": "e11.sidecar.unknown_openapi",
        "coversClassIds": [11],
        "requiredDimensions": ["R9", "R11"],
        "harnessRefs": [
            "tests/unit/application/services/test_e9_s10_unknown_external_openapi_offline.py",
            "tests/unit/application/services/test_e11_s5_registry_operation_ids_cutover.py",
        ],
    },
    {
        "id": "e11.sidecar.metamorphic_continuity",
        "coversClassIds": [12],
        "requiredDimensions": ["R9", "R10"],
        "harnessRefs": [
            "tests/unit/application/services/test_e1_s6b_selection_cutover.py",
            "tests/unit/application/services/test_e11_s5_registry_operation_ids_cutover.py",
        ],
    },
    {
        "id": "e11.sidecar.send_stream_parity",
        "coversClassIds": [18],
        "requiredDimensions": ["R7", "R8"],
        "harnessRefs": [
            "tests/unit/application/services/test_e9_s10_send_stream_parity_offline.py",
        ],
    },
    {
        "id": "e11.sidecar.semantic_authority",
        "coversClassIds": [1, 2, 4],
        "requiredDimensions": ["R1", "R2", "R4"],
        "harnessRefs": [
            "tests/unit/application/services/test_e11_s6_semantic_authority_cutover.py",
            "tests/unit/domain/services/test_e11_s7_capability_contract_metadata.py",
        ],
    },
    {
        "id": "e11.sidecar.security_hygiene",
        "coversClassIds": [14, 15],
        "requiredDimensions": ["R10", "R11"],
        "harnessRefs": [
            "tests/unit/scripts/test_e11_s8_smoke_credentials.py",
            "tests/unit/domain/services/test_chat_write_confirmation_service.py",
            "tests/unit/domain/services/test_chat_input_security_service.py",
        ],
    },
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_pytest(stdout: str) -> dict[str, int]:
    passed = failed = errors = skipped = 0
    m = re.search(r"(\d+) passed", stdout)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+) failed", stdout)
    if m:
        failed = int(m.group(1))
    m = re.search(r"(\d+) error", stdout)
    if m:
        errors = int(m.group(1))
    m = re.search(r"(\d+) skipped", stdout)
    if m:
        skipped = int(m.group(1))
    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
    }


def _run_pytest(root: Path, refs: list[str]) -> tuple[dict, str, int]:
    cmd = [str(root / ".venv/bin/pytest"), "-q", "--tb=line", *refs]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return _parse_pytest(proc.stdout or ""), out, proc.returncode


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    corpus_path = root / "tests/fixtures/intelligence_baseline/r1_r11_corpus_v2.json"
    routing_path = root / "tests/fixtures/intelligence_baseline/routing_cases.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    dataset_hash = _sha256(corpus_path)
    routing_hash = _sha256(routing_path)

    matrix_report = ChatRequiredDimensionsMatrixService.validate_corpus(corpus)
    if not matrix_report.ok:
        print("REQUIRED_DIMENSIONS_MATRIX=FAIL")
        print(json.dumps(matrix_report.as_dict(), ensure_ascii=False, indent=2))
        return 2

    if dataset_hash != EXPECTED_CORPUS_HASH:
        print("DATASET_HASH_MISMATCH", dataset_hash, EXPECTED_CORPUS_HASH)
        return 2

    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
        cwd=root.parent,
    ).strip()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = "e11-s9-final-candidate-offline-v1"
    run_dir = root / "docs/testing/evidence/runs" / f"{ts}_{sha[:8]}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    case_results: list[dict] = []
    any_fail = False
    dimension_hits: dict[str, list[str]] = {}

    for case in corpus.get("cases") or []:
        case_id = str(case.get("id") or "")
        ref = str(case.get("harnessRef") or "").strip()
        path = root / ref
        required = list(case.get("requiredDimensions") or [])
        if not path.is_file():
            case_results.append(
                {
                    "caseId": case_id,
                    "classId": case.get("classId"),
                    "status": "FAIL",
                    "reason": "missing_harness",
                    "harnessRef": ref,
                    "requiredDimensions": required,
                }
            )
            any_fail = True
            continue

        if path.suffix.lower() == ".json":
            case_results.append(
                {
                    "caseId": case_id,
                    "classId": case.get("classId"),
                    "status": "PASS_INDEXED_FIXTURE",
                    "harnessRef": ref,
                    "requiredDimensions": required,
                    "note": "fixture indexed; reinforced by sidecars when applicable",
                }
            )
            for dim in required:
                dimension_hits.setdefault(dim, []).append(f"{case_id}:indexed")
            continue

        counts, out, code = _run_pytest(root, [ref])
        ok = code == 0 and counts["failed"] == 0 and counts["errors"] == 0
        status = "PASS_OFFLINE" if ok else "FAIL"
        if not ok:
            any_fail = True
        case_results.append(
            {
                "caseId": case_id,
                "classId": case.get("classId"),
                "status": status,
                "harnessRef": ref,
                "requiredDimensions": required,
                "pytest": {**counts, "exitCode": code},
            }
        )
        (run_dir / f"case-{case_id}.stdout.txt").write_text(out, encoding="utf-8")
        for dim in required:
            dimension_hits.setdefault(dim, []).append(
                f"{case_id}:{'PASS' if ok else 'FAIL'}"
            )

    sidecar_results: list[dict] = []
    for side in SIDECARS:
        refs = list(side["harnessRefs"])
        missing = [ref for ref in refs if not (root / ref).is_file()]
        if missing:
            sidecar_results.append(
                {
                    "id": side["id"],
                    "status": "FAIL",
                    "reason": "missing_harness",
                    "missing": missing,
                }
            )
            any_fail = True
            continue
        counts, out, code = _run_pytest(root, refs)
        ok = code == 0 and counts["failed"] == 0 and counts["errors"] == 0
        status = "PASS_OFFLINE" if ok else "FAIL"
        if not ok:
            any_fail = True
        sidecar_results.append(
            {
                "id": side["id"],
                "status": status,
                "coversClassIds": side["coversClassIds"],
                "requiredDimensions": side["requiredDimensions"],
                "harnessRefs": refs,
                "pytest": {**counts, "exitCode": code},
            }
        )
        (run_dir / f"sidecar-{side['id']}.stdout.txt").write_text(out, encoding="utf-8")
        for dim in side["requiredDimensions"]:
            dimension_hits.setdefault(dim, []).append(
                f"{side['id']}:{'PASS' if ok else 'FAIL'}"
            )

    # Aggregate R1–R11 from offline evidence only.
    required_all = [f"R{i}" for i in range(1, 12)]
    dimensions: dict[str, str] = {}
    for dim in required_all:
        hits = dimension_hits.get(dim) or []
        if any(h.endswith(":FAIL") for h in hits):
            dimensions[dim] = "FAIL"
        elif hits:
            dimensions[dim] = "PASS_OFFLINE"
        else:
            dimensions[dim] = "INCONCLUSIVE"

    aggregate = "FAIL" if any_fail else "PASS_OFFLINE"
    # Live dims still required for release — marked deferred here.
    live_deferred = {
        "R7_live_send_stream_ui": "DEFERRED_LIVE",
        "R8_live_latency_p50_p95": "DEFERRED_LIVE",
        "R9_live_surface": "DEFERRED_LIVE",
        "R11_live_efficiency": "DEFERRED_LIVE",
    }

    runner_path = Path(__file__).resolve()
    config_material = {
        "datasetVersion": corpus.get("datasetVersion"),
        "datasetHash": dataset_hash,
        "routingCasesHash": routing_hash,
        "environment": "host-offline",
        "liveLlm": False,
        "role": "FINAL_CANDIDATE_OFFLINE",
        "planStep": "E11.S9",
    }
    provenance = ChatEvidenceReproducibilityService.build_provenance(
        git_sha=sha,
        dataset_version=str(corpus.get("datasetVersion") or ""),
        dataset_hash=dataset_hash,
        runner_path=runner_path,
        config_material=config_material,
        routing_cases_hash=routing_hash,
    )

    manifest = {
        "runId": run_id,
        "wave": "J",
        "planStep": "E11.S9",
        "program": "llm-json-decoupling",
        "role": "FINAL_CANDIDATE_OFFLINE",
        "timestamp": provenance["timestamp"],
        "finalCandidateGitSha": sha,
        "environment": "host-offline",
        "datasetVersion": corpus.get("datasetVersion"),
        "datasetHash": dataset_hash,
        "routingCasesHash": routing_hash,
        "runnerPath": provenance["runnerPath"],
        "runnerSha256": provenance["runnerSha256"],
        "configHash": provenance["configHash"],
        "liveLlm": False,
        "aggregateStatus": aggregate,
        "globalReleasePass": False,
        "reasonGlobalReleasePassFalse": (
            "Live requiredDimensions (send/stream/F5/efficiency) deferred to "
            "live battery with SMOKE_USER/PASSWORD; offline alone cannot close VERIFY_FINAL."
        ),
        "dimensionsOffline": dimensions,
        "liveDeferred": live_deferred,
        "cases": case_results,
        "sidecars": sidecar_results,
        "notes": [
            "Corpus v2 + matrix gate (J-R2); provenance (J-R3).",
            "Historical A–I PASS is not reused as release evidence.",
            "globalReleasePass forever false while liveDeferred is non-empty.",
        ],
    }
    consistency = ChatEvidenceReproducibilityService.validate_manifest(
        manifest, require_provenance=True
    )
    if not consistency.ok:
        print("EVIDENCE_REPRODUCIBLE=FAIL", consistency.errors)
        return 2
    manifest["evidenceReproducibility"] = {
        "ok": True,
        "source": ChatEvidenceReproducibilityService.SOURCE,
    }

    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    mirror = (
        root
        / "docs/roadmap/llm-json-decoupling/evidence/e11-s9-final-candidate-offline-v1"
    )
    mirror.mkdir(parents=True, exist_ok=True)
    (mirror / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "runDir": str(run_dir),
                "finalCandidateGitSha": sha,
                "aggregateStatus": aggregate,
                "dimensionsOffline": dimensions,
            },
            indent=2,
        )
    )
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
