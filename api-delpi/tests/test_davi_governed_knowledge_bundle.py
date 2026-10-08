"""DAVI governed-knowledge derived bundle — deterministic build contract.

TASK: DAVI-GOVERNED-KNOWLEDGE-RUNTIME-IMPLEMENTATION-001
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _API_ROOT.parent
sys.path.insert(0, str(_API_ROOT / "scripts"))

from davi_governed_knowledge_bundle_lib import (  # noqa: E402
    CORPUS_ID,
    CORPUS_VERSION,
    FREEZE_ARTIFACT,
    FREEZE_SHA,
    BundleError,
    build_bundle,
    emit_manifest,
    frozen_corpus_paths,
    manifest_sha256,
    resolve_source_path,
    sha256_file,
    verify_manifest,
)

_CORPUS_COUNT = 15
_SOURCE_SHA = "a" * 40


def _manifest() -> dict:
    return emit_manifest(
        generated_at="2026-10-08T00:00:00+00:00",
        source_git_sha=_SOURCE_SHA,
    )


def _freeze_text(paths: list[str]) -> bytes:
    rows = "\n".join(f"| {i} | `{p}` |" for i, p in enumerate(paths, 1))
    return (
        f"# freeze\n\n## FROZEN_FIRST_CORPUS\n\n| # | path |\n|---|---|\n{rows}\n"
    ).encode("utf-8")


def _fake_git(
    manifest: dict,
    *,
    doc_bytes=None,
    freeze_bytes=None,
    freeze_sha: str = FREEZE_SHA,
    source_sha: str = _SOURCE_SHA,
):
    """In-memory blob store keyed by (sha, repo-rel path).

    Models pinned git objects without requiring a git binary. Resolvable
    SHAs are fixed (freeze_sha/source_sha), so mutated manifest fields
    fail closed instead of becoming resolvable.
    """
    blobs = {
        (freeze_sha, FREEZE_ARTIFACT): (
            freeze_bytes
            if freeze_bytes is not None
            else resolve_source_path(FREEZE_ARTIFACT).read_bytes()
        )
    }
    for doc in manifest["documents"]:
        rel = doc["path"]
        blobs[(source_sha, rel)] = (
            doc_bytes[rel]
            if doc_bytes and rel in doc_bytes
            else resolve_source_path(rel).read_bytes()
        )

    def reader(sha: str, rel: str) -> bytes:
        if (sha, rel) not in blobs:
            raise BundleError(f"git object not found at {sha}: {rel}")
        return blobs[(sha, rel)]

    def resolver(sha: str) -> bool:
        return sha in {freeze_sha, source_sha}

    return reader, resolver


def _build(manifest: dict, out: Path, **kwargs):
    reader, resolver = _fake_git(manifest)
    return build_bundle(
        manifest,
        output_dir=out,
        blob_reader=reader,
        ref_resolver=resolver,
        **kwargs,
    )


def _retamper(manifest: dict) -> dict:
    """Refresh manifest_sha256 after a documents mutation."""
    manifest["manifest_sha256"] = manifest_sha256(manifest)
    return manifest


def _manifest_path(name: str) -> str:
    return f"api-delpi/docs/api/{name}.md"


def test_b01_emits_exactly_fifteen_approved_documents(tmp_path: Path) -> None:
    out = tmp_path / "bundle"
    written = _build(_manifest(), out)
    emitted = sorted(p.name for p in out.glob("*.md"))
    expected = sorted(Path(p).name for p in frozen_corpus_paths())
    assert len(written) == _CORPUS_COUNT + 1  # 15 docs + manifest.json
    assert emitted == expected
    assert len(emitted) == _CORPUS_COUNT


def test_b02_no_secondary_or_non_corpus_document_emitted(tmp_path: Path) -> None:
    out = tmp_path / "bundle"
    _build(_manifest(), out)
    names = {p.name for p in out.iterdir()}
    assert "commercial-billing-portfolio.md" not in names
    assert names == {Path(p).name for p in frozen_corpus_paths()} | {
        "manifest.json"
    }


def test_b03_source_files_unchanged_by_build(tmp_path: Path) -> None:
    before = {p: sha256_file(resolve_source_path(p)) for p in frozen_corpus_paths()}
    _build(_manifest(), tmp_path / "bundle")
    after = {p: sha256_file(resolve_source_path(p)) for p in frozen_corpus_paths()}
    assert before == after


def test_b04_every_output_carries_provenance_header(tmp_path: Path) -> None:
    manifest = _manifest()
    out = tmp_path / "bundle"
    _build(manifest, out)
    docs = {d["path"]: d for d in manifest["documents"]}
    for path, doc in docs.items():
        text = (out / Path(path).name).read_text(encoding="utf-8")
        head = text.split("---", 1)[0]
        assert "DAVI GOVERNED KNOWLEDGE" in head
        assert f"corpus_id: {CORPUS_ID}" in head
        assert f"corpus_version: {CORPUS_VERSION}" in head
        assert f"source_path: {path}" in head
        assert f"source_git_sha: {manifest['source_git_sha']}" in head
        assert f"source_sha256: {doc['sha256']}" in head


def test_b05_duplicate_source_in_manifest_fails(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["documents"].append(dict(manifest["documents"][0]))
    with pytest.raises(BundleError, match="duplicate"):
        _build(_retamper(manifest), tmp_path / "bundle")


def test_b06_missing_source_fails(tmp_path: Path, monkeypatch) -> None:
    manifest = _manifest()
    monkeypatch.setattr(
        Path, "is_file", lambda self: self.name != Path(
            manifest["documents"][0]["path"]
        ).name
    )
    with pytest.raises(BundleError, match="missing"):
        _build(manifest, tmp_path / "bundle")


def test_b07_hash_mismatch_fails(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["documents"][0]["sha256"] = "f" * 64
    with pytest.raises(BundleError, match="hash mismatch"):
        _build(_retamper(manifest), tmp_path / "bundle")


def test_b08_unapproved_extra_source_fails(tmp_path: Path) -> None:
    manifest = _manifest()
    extra = resolve_source_path(_manifest_path("commercial-billing-portfolio"))
    manifest["documents"].append(
        {"path": _manifest_path("commercial-billing-portfolio"),
         "sha256": sha256_file(extra)}
    )
    with pytest.raises(BundleError, match="unapproved"):
        _build(_retamper(manifest), tmp_path / "bundle")


def test_b09_same_manifest_produces_identical_bytes(tmp_path: Path) -> None:
    manifest = _manifest()
    out_a, out_b = tmp_path / "a", tmp_path / "b"
    _build(manifest, out_a)
    _build(manifest, out_b)
    for name in sorted(p.name for p in out_a.iterdir()):
        assert (out_a / name).read_bytes() == (out_b / name).read_bytes(), name


def test_b10_manifest_identifies_frozen_git_sha() -> None:
    manifest = _manifest()
    assert manifest["freeze_sha"] == FREEZE_SHA
    assert manifest["source_git_sha"] == _SOURCE_SHA
    assert manifest["manifest_sha256"] == manifest_sha256(manifest)
    # generated_at is excluded from content identity.
    clone = json.loads(json.dumps(manifest))
    clone["generated_at"] = "1999-01-01T00:00:00+00:00"
    clone["manifest_sha256"] = manifest_sha256(clone)
    assert clone["manifest_sha256"] == manifest["manifest_sha256"]


def _verify(manifest: dict, **kwargs):
    reader, resolver = _fake_git(manifest, **kwargs)
    return verify_manifest(manifest, blob_reader=reader, ref_resolver=resolver)


def test_c01_tampered_manifest_sha256_fails() -> None:
    manifest = _manifest()
    manifest["manifest_sha256"] = "0" * 64
    with pytest.raises(BundleError, match="manifest_sha256"):
        _verify(manifest)


def test_c02_source_git_sha_invalid_or_unresolvable_fails() -> None:
    manifest = _manifest()
    manifest["source_git_sha"] = "not-a-git-sha"
    _retamper(manifest)
    with pytest.raises(BundleError, match="source_git_sha"):
        _verify(manifest)
    manifest["source_git_sha"] = "b" * 40
    _retamper(manifest)
    with pytest.raises(BundleError, match="source_git_sha"):
        _verify(manifest)  # resolver cannot resolve it


def test_c03_pinned_source_bytes_differ_fails() -> None:
    manifest = _manifest()
    victim = manifest["documents"][0]["path"]
    with pytest.raises(BundleError, match="pinned source hash mismatch"):
        _verify(manifest, doc_bytes={victim: b"tampered bytes"})


def test_c04_freeze_sha_invalid_fails() -> None:
    manifest = _manifest()
    manifest["freeze_sha"] = "c" * 40
    _retamper(manifest)
    with pytest.raises(BundleError, match="freeze_sha"):
        _verify(manifest)


def test_c05_manifest_membership_differs_from_pinned_freeze_fails() -> None:
    manifest = _manifest()
    pinned_paths = [d["path"] for d in manifest["documents"][:-1]]
    with pytest.raises(BundleError, match="unapproved|missing"):
        _verify(manifest, freeze_bytes=_freeze_text(pinned_paths))
    # Reverse direction: pinned freeze contains a path absent from manifest.
    shrunk = _manifest()
    shrunk["documents"] = shrunk["documents"][:-1]
    _retamper(shrunk)
    with pytest.raises(BundleError, match="unapproved|missing"):
        _verify(shrunk)


def test_c06_current_freeze_membership_differs_from_pinned_fails(
    monkeypatch,
) -> None:
    manifest = _manifest()
    pinned = frozen_corpus_paths()
    monkeypatch.setattr(
        "davi_governed_knowledge_bundle_lib.frozen_corpus_paths",
        lambda repo_root=None: list(
            pinned[:-1] + ["api-delpi/docs/api/added-later.md"]
        ),
    )
    with pytest.raises(BundleError, match="current freeze membership diverges"):
        _verify(manifest, freeze_bytes=_freeze_text(pinned))


def test_c07_current_valid_pinned_manifest_passes() -> None:
    manifest = json.loads(
        resolve_source_path(
            "api-delpi/docs/integrations/evidence/"
            "davi-governed-knowledge-manifest-v1.json"
        ).read_text(encoding="utf-8")
    )
    evidence = _verify(manifest, source_sha=manifest["source_git_sha"])
    assert evidence["corpus_id"] == CORPUS_ID
    assert evidence["documents"] == _CORPUS_COUNT
    assert evidence["freeze_sha"] == FREEZE_SHA


def test_c08_head_newer_than_source_git_sha_passes() -> None:
    """source_git_sha is frozen identity; HEAD may be newer/non-causal."""
    manifest = _manifest()
    # Resolver knows only pinned SHAs; a hypothetical newer HEAD is absent and
    # must not be consulted or required.
    evidence = _verify(manifest)
    assert evidence["source_git_sha"] == _SOURCE_SHA


def test_pinned_manifest_matches_current_sources() -> None:
    """Committed manifest must pin the real frozen corpus at this HEAD."""
    from davi_governed_knowledge_bundle_lib import MANIFEST_REPO_PATH

    manifest = json.loads(
        resolve_source_path(MANIFEST_REPO_PATH).read_text(encoding="utf-8")
    )
    assert manifest["corpus_id"] == CORPUS_ID
    assert manifest["corpus_version"] == CORPUS_VERSION
    assert len(manifest["documents"]) == _CORPUS_COUNT
    for doc in manifest["documents"]:
        src = resolve_source_path(doc["path"])
        assert src.is_file(), doc["path"]
        assert sha256_file(src) == doc["sha256"], doc["path"]


def test_builder_has_no_network_or_provider_dependency() -> None:
    lib = (_API_ROOT / "scripts" / "davi_governed_knowledge_bundle_lib.py").read_text(
        encoding="utf-8"
    )
    cli = (
        _API_ROOT / "scripts" / "build_davi_governed_knowledge_bundle.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "openai",
        "requests",
        "httpx",
        "urllib.request",
        "openai_client",
        "embedding",
        "vector",
    ):
        assert forbidden not in lib.lower(), forbidden
        assert forbidden not in cli.lower(), forbidden


def test_corpus_membership_comes_from_freeze_artifact() -> None:
    paths = frozen_corpus_paths()
    assert len(paths) == _CORPUS_COUNT
    assert all(p.startswith("api-delpi/docs/api/") for p in paths)
