"""CLI for the DAVI governed-knowledge derived bundle.

TASK: DAVI-GOVERNED-KNOWLEDGE-RUNTIME-IMPLEMENTATION-001

Usage:

    python scripts/build_davi_governed_knowledge_bundle.py emit-manifest
    python scripts/build_davi_governed_knowledge_bundle.py build
    python scripts/build_davi_governed_knowledge_bundle.py verify

emit-manifest writes the pinned manifest (evidence artifact, committed).
build writes dist/davi-governed-knowledge/v1/ (generated, gitignored).
verify re-validates sources against the pinned manifest without writing.

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
    MANIFEST_REPO_PATH,
    OUTPUT_DIR,
    REPO_ROOT,
    BundleError,
    build_bundle,
    emit_manifest,
    frozen_corpus_paths,
    resolve_source_path,
)


def _emit() -> int:
    manifest = emit_manifest(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    out = resolve_source_path(MANIFEST_REPO_PATH)
    out.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"manifest written: {MANIFEST_REPO_PATH} ({len(manifest['documents'])} docs)")
    return 0


def _load_manifest() -> dict:
    path = resolve_source_path(MANIFEST_REPO_PATH)
    if not path.is_file():
        raise BundleError(f"manifest missing: {MANIFEST_REPO_PATH} (run emit-manifest)")
    return json.loads(path.read_text(encoding="utf-8"))


def _build() -> int:
    written = build_bundle(_load_manifest(), output_dir=OUTPUT_DIR)
    rel = OUTPUT_DIR.relative_to(API_ROOT)
    print(f"bundle written: api-delpi/{rel} ({len(written) - 1} docs + manifest.json)")
    return 0


def _verify() -> int:
    # Read-only drift check: sources must still match pinned hashes.
    from davi_governed_knowledge_bundle_lib import sha256_file

    manifest = _load_manifest()
    frozen = set(frozen_corpus_paths())
    paths = {d["path"] for d in manifest["documents"]}
    if paths != frozen:
        raise BundleError("manifest membership diverges from freeze artifact")
    mismatched = [
        d["path"]
        for d in manifest["documents"]
        if not resolve_source_path(d["path"]).is_file()
        or sha256_file(resolve_source_path(d["path"])) != d["sha256"]
    ]
    if mismatched:
        raise BundleError(f"stale/missing sources vs pinned manifest: {mismatched}")
    print(f"verify PASS: {len(paths)} corpus docs match pinned manifest")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("emit-manifest", "build", "verify"))
    args = parser.parse_args()
    try:
        return {"emit-manifest": _emit, "build": _build, "verify": _verify}[
            args.command
        ]()
    except BundleError as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
