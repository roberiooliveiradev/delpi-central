"""CLI for the DAVI governed-knowledge derived bundle.

TASK: DAVI-GOVERNED-KNOWLEDGE-RUNTIME-IMPLEMENTATION-001

Usage:

    python scripts/build_davi_governed_knowledge_bundle.py emit-manifest [--corpus-version N]
    python scripts/build_davi_governed_knowledge_bundle.py build [--corpus-version N]
    python scripts/build_davi_governed_knowledge_bundle.py verify [--corpus-version N]

emit-manifest writes the pinned manifest (evidence artifact, committed).
build writes dist/davi-governed-knowledge/v<N>/ (generated, gitignored).
verify proves manifest identity, pinned freeze membership, pinned source
Git hashes and current-source reproducibility without writing.

No network. No provider calls. No source mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from davi_governed_knowledge_bundle_lib import (  # noqa: E402
    API_ROOT,
    BundleError,
    build_bundle,
    corpus_version_spec,
    emit_manifest,
    load_topic_index,
    output_dir_for,
    verify_topic_index,
    resolve_source_path,
    verify_manifest,
)


def _emit(spec) -> int:
    manifest = emit_manifest(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        spec=spec,
    )
    out = resolve_source_path(spec.manifest_repo_path)
    out.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"manifest written: {spec.manifest_repo_path} "
        f"({len(manifest['documents'])} docs)"
    )
    return 0


def _load_manifest(spec) -> dict:
    path = resolve_source_path(spec.manifest_repo_path)
    if not path.is_file():
        raise BundleError(
            f"manifest missing: {spec.manifest_repo_path} (run emit-manifest)"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _pin_check(manifest: dict, spec) -> None:
    """Published-version integrity pins — enforced on committed artifacts only."""
    if manifest.get("manifest_sha256") != spec.manifest_identity:
        raise BundleError("manifest identity does not match the published pin")
    if manifest.get("freeze_sha") != spec.freeze_sha:
        raise BundleError("freeze_sha does not match the published pin")


def _build(spec) -> int:
    output_dir = output_dir_for(spec.corpus_version)
    manifest = _load_manifest(spec)
    _pin_check(manifest, spec)
    written = build_bundle(manifest, output_dir=output_dir)
    rel = output_dir.relative_to(API_ROOT)
    print(
        f"bundle written: api-delpi/{rel} "
        f"({len(written) - 2} frozen docs + derived topic index + manifest.json)"
    )
    return 0


def _verify(spec) -> int:
    manifest = _load_manifest(spec)
    _pin_check(manifest, spec)
    evidence = verify_manifest(manifest)
    topic_evidence = verify_topic_index(
        load_topic_index(spec=spec), manifest
    )
    print("verify PASS:")
    print(f"  corpus={evidence['corpus_id']}")
    print(f"  version={evidence['corpus_version']}")
    print(f"  documents={evidence['documents']}")
    print(f"  freeze_sha={evidence['freeze_sha']}")
    print(f"  source_git_sha={evidence['source_git_sha']}")
    print(f"  manifest_sha256={evidence['manifest_sha256']}")
    print(
        f"  topics={topic_evidence['topics']}, "
        f"deferred={topic_evidence['deferred_sources']}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("emit-manifest", "build", "verify"))
    parser.add_argument(
        "--corpus-version",
        type=int,
        default=1,
        help="Published corpus version to operate on (default: 1).",
    )
    args = parser.parse_args()
    try:
        spec = corpus_version_spec(args.corpus_version)
        return {"emit-manifest": _emit, "build": _build, "verify": _verify}[
            args.command
        ](spec)
    except BundleError as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
