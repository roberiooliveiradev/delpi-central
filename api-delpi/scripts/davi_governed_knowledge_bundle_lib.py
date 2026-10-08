"""Deterministic DAVI governed-knowledge bundle builder (provider-neutral).

TASK: DAVI-GOVERNED-KNOWLEDGE-RUNTIME-IMPLEMENTATION-001

Produces a derived corpus for Workspace Agent Files upload. Governance
authority: the freeze artifact owns corpus membership; the pinned manifest
owns content hashes. This module never uploads, never calls provider APIs,
never mutates source documents, and never touches network.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

CORPUS_ID = "davi-governed-knowledge"
CORPUS_VERSION = 1

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent

FREEZE_ARTIFACT = (
    "api-delpi/docs/integrations/evidence/davi-governed-knowledge-freeze-001.md"
)
FREEZE_SHA = "d9926cc14a8a4edd1b52775b82cf7353aede75b4"
MANIFEST_REPO_PATH = (
    "api-delpi/docs/integrations/evidence/davi-governed-knowledge-manifest-v1.json"
)
OUTPUT_DIR = API_ROOT / "dist" / "davi-governed-knowledge" / "v1"

_DOC_PREFIX = "api-delpi/"
_CORPUS_SECTION = "## FROZEN_FIRST_CORPUS"
_CORPUS_ROW = re.compile(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|", re.MULTILINE)


class BundleError(RuntimeError):
    """Fail-closed corpus validation/build error."""


def resolve_source_path(rel: str, repo_root: Path = REPO_ROOT) -> Path:
    """Resolve a repo-relative doc path in monorepo or flat (container) layout."""
    rooted = repo_root / rel
    if rooted.exists():
        return rooted
    if rel.startswith(_DOC_PREFIX):
        return API_ROOT / rel[len(_DOC_PREFIX):]
    return rooted


def frozen_corpus_paths(repo_root: Path = REPO_ROOT) -> list[str]:
    """Corpus membership authority: parse the freeze artifact table."""
    text = resolve_source_path(FREEZE_ARTIFACT, repo_root).read_text(
        encoding="utf-8"
    )
    if _CORPUS_SECTION not in text:
        raise BundleError("freeze artifact lacks FROZEN_FIRST_CORPUS section")
    section = text.split(_CORPUS_SECTION, 1)[1]
    end = section.find("\n## ")
    if end > 0:
        section = section[:end]
    paths = _CORPUS_ROW.findall(section)
    if len(set(paths)) != len(paths):
        raise BundleError("freeze artifact contains duplicate corpus paths")
    return paths


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_git_sha(repo_root: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _manifest_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    """Content-identity subset of a manifest (excludes generated metadata)."""
    return {
        "corpus_id": manifest["corpus_id"],
        "corpus_version": manifest["corpus_version"],
        "source_git_sha": manifest["source_git_sha"],
        "freeze_artifact": manifest["freeze_artifact"],
        "freeze_sha": manifest["freeze_sha"],
        "documents": manifest["documents"],
    }


def manifest_sha256(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(
        _manifest_identity(manifest), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def emit_manifest(
    *,
    generated_at: str,
    repo_root: Path = REPO_ROOT,
    source_git_sha: str | None = None,
) -> dict[str, Any]:
    """Derive the pinned manifest from the freeze artifact corpus."""
    paths = frozen_corpus_paths(repo_root)
    documents: list[dict[str, str]] = []
    for rel in paths:
        src = resolve_source_path(rel, repo_root)
        if not src.is_file():
            raise BundleError(f"corpus source missing: {rel}")
        documents.append({"path": rel, "sha256": sha256_file(src)})
    manifest: dict[str, Any] = {
        "corpus_id": CORPUS_ID,
        "corpus_version": CORPUS_VERSION,
        "source_git_sha": source_git_sha or current_git_sha(repo_root),
        "freeze_artifact": FREEZE_ARTIFACT,
        "freeze_sha": FREEZE_SHA,
        "generated_at": generated_at,
        "documents": documents,
    }
    manifest["manifest_sha256"] = manifest_sha256(manifest)
    return manifest


def _provenance_header(doc: dict[str, str], manifest: dict[str, Any]) -> str:
    return (
        "DAVI GOVERNED KNOWLEDGE\n"
        f"corpus_id: {manifest['corpus_id']}\n"
        f"corpus_version: {manifest['corpus_version']}\n"
        f"source_path: {doc['path']}\n"
        f"source_git_sha: {manifest['source_git_sha']}\n"
        f"source_sha256: {doc['sha256']}\n"
        "\n---\n\n"
    )


def _validate_manifest(
    manifest: dict[str, Any], repo_root: Path
) -> list[dict[str, str]]:
    if manifest.get("corpus_id") != CORPUS_ID:
        raise BundleError("manifest corpus_id mismatch")
    if manifest.get("corpus_version") != CORPUS_VERSION:
        raise BundleError("manifest corpus_version mismatch")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise BundleError("manifest has no documents")
    paths = [d.get("path") for d in documents]
    if any(not p for p in paths):
        raise BundleError("manifest document missing path")
    if len(set(paths)) != len(paths):
        raise BundleError("manifest contains duplicate source paths")
    frozen = set(frozen_corpus_paths(repo_root))
    manifest_set = set(paths)
    extra = manifest_set - frozen
    missing = frozen - manifest_set
    if extra:
        raise BundleError(f"unapproved path in manifest: {sorted(extra)}")
    if missing:
        raise BundleError(f"expected corpus member missing: {sorted(missing)}")
    names = [Path(p).name for p in paths]
    if len(set(names)) != len(names):
        raise BundleError("duplicate output filename in corpus")
    return documents


def build_bundle(
    manifest: dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    output_dir: Path = OUTPUT_DIR,
) -> list[Path]:
    """Validate sources against the pinned manifest and emit derived files.

    Fail-closed on: missing source, duplicate source, hash mismatch,
    unapproved path, missing corpus member. No network, no provider calls,
    no source mutation.
    """
    documents = _validate_manifest(manifest, repo_root)
    outputs: list[tuple[Path, bytes]] = []
    for doc in documents:
        rel = doc["path"]
        src = resolve_source_path(rel, repo_root)
        if not src.is_file():
            raise BundleError(f"corpus source missing: {rel}")
        actual = sha256_file(src)
        if actual != doc["sha256"]:
            raise BundleError(f"hash mismatch for {rel}")
        content = _provenance_header(doc, manifest).encode("utf-8") + src.read_bytes()
        outputs.append((output_dir / Path(rel).name, content))
    output_dir.mkdir(parents=True, exist_ok=True)
    written = [path for path, content in outputs if _write(path, content)]
    manifest_out = output_dir / "manifest.json"
    _write(
        manifest_out,
        (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
    )
    written.append(manifest_out)
    return written


def _write(path: Path, content: bytes) -> bool:
    path.write_bytes(content)
    return True
