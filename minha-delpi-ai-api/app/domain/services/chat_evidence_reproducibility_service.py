"""Evidence reproducibility — runner é a única fonte de veredito.

Regras (A11-03 / J-R3):
- ``globalReleasePass`` não pode contradizer ``reasonGlobalReleasePassFalse``
  nem dimensões live deferred;
- offline-only não fecha release;
- provenance mínima deve estar presente em manifests de release novos.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_PROVENANCE_KEYS = (
    "finalCandidateGitSha",
    "datasetVersion",
    "datasetHash",
    "timestamp",
    "runnerSha256",
    "configHash",
)


@dataclass(frozen=True)
class EvidenceConsistencyFinding:
    path: str | None
    ok: bool
    errors: tuple[str, ...]
    expected_global_release_pass: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChatEvidenceReproducibilityService:
    SOURCE = "plan-11/J-R3 + audit A11-03"

    @classmethod
    def file_sha256(cls, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @classmethod
    def stable_config_hash(cls, payload: dict[str, Any]) -> str:
        import json

        material = {
            "datasetVersion": payload.get("datasetVersion"),
            "datasetHash": payload.get("datasetHash"),
            "routingCasesHash": payload.get("routingCasesHash"),
            "environment": payload.get("environment"),
            "liveLlm": payload.get("liveLlm"),
            "role": payload.get("role"),
            "planStep": payload.get("planStep"),
        }
        raw = json.dumps(material, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def structural_release_blocked(cls, manifest: dict[str, Any]) -> bool:
        reason = str(manifest.get("reasonGlobalReleasePassFalse") or "").strip()
        if reason:
            return True
        live_deferred = manifest.get("liveDeferred")
        if isinstance(live_deferred, dict) and live_deferred:
            return True
        role = str(manifest.get("role") or "").upper()
        if manifest.get("liveLlm") is False and role.endswith("OFFLINE"):
            return True
        aggregate = str(manifest.get("aggregateStatus") or "").upper()
        if aggregate in {"FAIL", "INCONCLUSIVE"}:
            return True
        return False

    @classmethod
    def expected_global_release_pass(cls, manifest: dict[str, Any]) -> bool:
        if cls.structural_release_blocked(manifest):
            return False
        return bool(manifest.get("globalReleasePass"))

    @classmethod
    def validate_manifest(
        cls,
        manifest: dict[str, Any],
        *,
        path: str | None = None,
        require_provenance: bool = False,
    ) -> EvidenceConsistencyFinding:
        errors: list[str] = []
        expected = False if cls.structural_release_blocked(manifest) else bool(
            manifest.get("globalReleasePass")
        )
        stored = manifest.get("globalReleasePass")

        if cls.structural_release_blocked(manifest) and stored is True:
            errors.append(
                "globalReleasePass=true contradiz reason/liveDeferred/offline "
                "(runner produziria false)"
            )

        if require_provenance:
            for key in REQUIRED_PROVENANCE_KEYS:
                if not str(manifest.get(key) or "").strip():
                    errors.append(f"provenance ausente: {key}")

        return EvidenceConsistencyFinding(
            path=path,
            ok=not errors,
            errors=tuple(errors),
            expected_global_release_pass=expected,
        )

    @classmethod
    def align_global_release_pass(cls, manifest: dict[str, Any]) -> dict[str, Any]:
        out = dict(manifest)
        previous = out.get("globalReleasePass")
        if cls.structural_release_blocked(out):
            out["globalReleasePass"] = False
        out["evidenceReproducibility"] = {
            "alignedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": cls.SOURCE,
            "previousGlobalReleasePass": previous,
            "alignedGlobalReleasePass": out.get("globalReleasePass"),
        }
        return out

    @classmethod
    def build_provenance(
        cls,
        *,
        git_sha: str,
        dataset_version: str,
        dataset_hash: str,
        runner_path: Path,
        config_material: dict[str, Any],
        provider: str | None = None,
        model: str | None = None,
        routing_cases_hash: str | None = None,
    ) -> dict[str, Any]:
        return {
            "finalCandidateGitSha": git_sha,
            "datasetVersion": dataset_version,
            "datasetHash": dataset_hash,
            "routingCasesHash": routing_cases_hash,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "runnerPath": str(runner_path).replace("\\", "/"),
            "runnerSha256": cls.file_sha256(runner_path) if runner_path.is_file() else "",
            "configHash": cls.stable_config_hash(config_material),
            "provider": provider,
            "model": model,
        }
