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
    FREEZE_SHA,
    BundleError,
    build_bundle,
    emit_manifest,
    frozen_corpus_paths,
    manifest_sha256,
    resolve_source_path,
    sha256_file,
)

_CORPUS_COUNT = 15


def _manifest() -> dict:
    return emit_manifest(
        generated_at="2026-10-08T00:00:00+00:00",
        source_git_sha="0" * 40,
    )


def _manifest_path(name: str) -> str:
    return f"api-delpi/docs/api/{name}.md"


def test_b01_emits_exactly_fifteen_approved_documents(tmp_path: Path) -> None:
    out = tmp_path / "bundle"
    written = build_bundle(_manifest(), output_dir=out)
    emitted = sorted(p.name for p in out.glob("*.md"))
    expected = sorted(Path(p).name for p in frozen_corpus_paths())
    assert len(written) == _CORPUS_COUNT + 1  # 15 docs + manifest.json
    assert emitted == expected
    assert len(emitted) == _CORPUS_COUNT


def test_b02_no_secondary_or_non_corpus_document_emitted(tmp_path: Path) -> None:
    out = tmp_path / "bundle"
    build_bundle(_manifest(), output_dir=out)
    names = {p.name for p in out.iterdir()}
    assert "commercial-billing-portfolio.md" not in names
    assert names == {Path(p).name for p in frozen_corpus_paths()} | {
        "manifest.json"
    }


def test_b03_source_files_unchanged_by_build(tmp_path: Path) -> None:
    before = {p: sha256_file(resolve_source_path(p)) for p in frozen_corpus_paths()}
    build_bundle(_manifest(), output_dir=tmp_path / "bundle")
    after = {p: sha256_file(resolve_source_path(p)) for p in frozen_corpus_paths()}
    assert before == after


def test_b04_every_output_carries_provenance_header(tmp_path: Path) -> None:
    manifest = _manifest()
    out = tmp_path / "bundle"
    build_bundle(manifest, output_dir=out)
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
        build_bundle(manifest, output_dir=tmp_path / "bundle")


def test_b06_missing_source_fails(tmp_path: Path, monkeypatch) -> None:
    manifest = _manifest()
    monkeypatch.setattr(
        Path, "is_file", lambda self: self.name != Path(
            manifest["documents"][0]["path"]
        ).name
    )
    with pytest.raises(BundleError, match="missing"):
        build_bundle(manifest, output_dir=tmp_path / "bundle")


def test_b07_hash_mismatch_fails(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["documents"][0]["sha256"] = "f" * 64
    with pytest.raises(BundleError, match="hash mismatch"):
        build_bundle(manifest, output_dir=tmp_path / "bundle")


def test_b08_unapproved_extra_source_fails(tmp_path: Path) -> None:
    manifest = _manifest()
    extra = resolve_source_path(_manifest_path("commercial-billing-portfolio"))
    manifest["documents"].append(
        {"path": _manifest_path("commercial-billing-portfolio"),
         "sha256": sha256_file(extra)}
    )
    with pytest.raises(BundleError, match="unapproved"):
        build_bundle(manifest, output_dir=tmp_path / "bundle")


def test_b09_same_manifest_produces_identical_bytes(tmp_path: Path) -> None:
    manifest = _manifest()
    out_a, out_b = tmp_path / "a", tmp_path / "b"
    build_bundle(manifest, output_dir=out_a)
    build_bundle(manifest, output_dir=out_b)
    for name in sorted(p.name for p in out_a.iterdir()):
        assert (out_a / name).read_bytes() == (out_b / name).read_bytes(), name


def test_b10_manifest_identifies_frozen_git_sha() -> None:
    manifest = _manifest()
    assert manifest["freeze_sha"] == FREEZE_SHA
    assert manifest["source_git_sha"] == "0" * 40
    assert manifest["manifest_sha256"] == manifest_sha256(manifest)
    # generated_at is excluded from content identity.
    clone = json.loads(json.dumps(manifest))
    clone["generated_at"] = "1999-01-01T00:00:00+00:00"
    clone["manifest_sha256"] = manifest_sha256(clone)
    assert clone["manifest_sha256"] == manifest["manifest_sha256"]


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
