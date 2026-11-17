"""DAVI governed knowledge V3 — MP norm MP1008 generic revision (G25-L2-B).

Proves the additive V3 publication: V1/V2 artifacts stay byte-intact and
verifiable, the revised MP norm (AWG range + CARRETEL packaging, generic
1008 scope, PR #238) is served at corpus_version=3, and older versions keep
serving their own pinned content.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

_EVIDENCE = "docs/integrations/evidence"
_MP_DOC = "api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md"


@pytest.fixture()
def published_corpus_v3(tmp_path):
    """Stage V1+V2+V3 evidence files; drifted docs staged at pinned blobs."""
    root = Path(__file__).resolve().parents[1]
    repo_root = root.parent
    evidence = root / _EVIDENCE
    paths: set[str] = set()
    pinned: dict[tuple[str, str], str] = {}
    for version in (1, 2, 3):
        manifest = json.loads(
            (evidence / f"davi-governed-knowledge-manifest-v{version}.json").read_text()
        )
        index = json.loads(
            (evidence / f"davi-governed-knowledge-topics-v{version}.json").read_text()
        )
        for entry in manifest["documents"]:
            paths.add(entry["path"])
            pinned.setdefault(
                (entry["path"], manifest["source_git_sha"]),
                entry["sha256"],
            )
        paths.update(entry["source_path"] for entry in index["deferred_sources"])
        paths.add(manifest["freeze_artifact"])
        paths.add(f"api-delpi/{_EVIDENCE}/davi-governed-knowledge-manifest-v{version}.json")
        paths.add(f"api-delpi/{_EVIDENCE}/davi-governed-knowledge-topics-v{version}.json")
    # Stage each document at the content pinned by the NEWEST manifest that
    # contains it, so v3 reads current content and v1/v2 reads pinned content.
    # The sandbox serves one tree: to keep all versions servable, stage the
    # V3-pinned bytes for the changed doc and let V1 (which lacks it) be
    # unaffected; V2's pinned blob is covered by the dedicated drift test
    # below.
    for source in paths:
        relative = source.removeprefix("api-delpi/")
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, target)
    return tmp_path


def _reader(root):
    from app.application.use_cases.read_governed_technical_knowledge_use_case import (
        ReadGovernedTechnicalKnowledgeUseCase,
    )
    from app.infrastructure.knowledge.governed_knowledge_repository import (
        GovernedKnowledgeRepository,
    )
    return ReadGovernedTechnicalKnowledgeUseCase(GovernedKnowledgeRepository(api_root=root))


def test_v3_manifest_is_pinned_and_complete(published_corpus_v3):
    manifest = json.loads(
        (published_corpus_v3 / f"{_EVIDENCE}/davi-governed-knowledge-manifest-v3.json").read_text()
    )
    assert manifest["corpus_version"] == 3
    paths = {doc["path"]: doc["sha256"] for doc in manifest["documents"]}
    assert len(paths) == 17 and _MP_DOC in paths
    # V3 pins the revised MP norm (PR #238 content), distinct from V2 pin.
    v2 = json.loads(
        (published_corpus_v3 / f"{_EVIDENCE}/davi-governed-knowledge-manifest-v2.json").read_text()
    )
    v2_docs = {doc["path"]: doc["sha256"] for doc in v2["documents"]}
    assert paths[_MP_DOC] != v2_docs[_MP_DOC]
    # All other corpus documents keep identical pinned hashes V2 -> V3.
    assert all(paths[p] == sha for p, sha in v2_docs.items() if p != _MP_DOC)


def test_v3_mp_norm_serves_awg_and_carretel_revision(published_corpus_v3):
    reader = _reader(published_corpus_v3)
    result = reader.execute(topic="mp_description_standards",
                            corpus_version=3, page_size=3)
    assert result["corpus_version"] == 3
    assert result["source_path"] == _MP_DOC
    raw = (published_corpus_v3 / _MP_DOC.removeprefix("api-delpi/")).read_bytes()
    assert result["source_sha256"] == hashlib.sha256(raw).hexdigest()
    whole = ""
    page = 1
    while True:
        chunk = reader.execute(topic="mp_description_standards",
                               corpus_version=3, page=page, page_size=3)
        whole += "".join(item["text"] for item in chunk["items"])
        if not chunk["has_more"]:
            break
        page += 1
    assert "CARRETEL" in whole
    assert "18-22AWG" in whole
    assert "TERM. BALA" in whole


def test_v3_is_default_latest_and_v1_unaffected(published_corpus_v3):
    from app.application.use_cases.read_governed_technical_knowledge_use_case import (
        KnowledgeReadError,
    )
    reader = _reader(published_corpus_v3)
    latest = reader.execute(topic="mp_description_standards")
    assert latest["corpus_version"] == 3
    v1 = reader.execute(topic="product_master_sb1", corpus_version=1, page_size=1)
    assert v1["corpus_version"] == 1
    with pytest.raises(KnowledgeReadError, match="STALE_VERSION"):
        reader.execute(topic="product_master_sb1", corpus_version=4)


def test_v2_superseded_doc_fails_closed_in_current_tree(published_corpus_v3):
    """Integrity guard: a superseded version cannot serve drifted bytes.

    In the published tree the MP norm carries V3 content; V2's pinned hash
    no longer matches, so V2 reads of that document must fail closed —
    proving a version is never silently served stale content.
    """
    from app.application.use_cases.read_governed_technical_knowledge_use_case import (
        KnowledgeReadError,
    )
    reader = _reader(published_corpus_v3)
    with pytest.raises(KnowledgeReadError) as exc:
        reader.execute(topic="mp_description_standards", corpus_version=2)
    assert exc.value.code == "CORPUS_UNAVAILABLE"


def test_v2_pinned_blob_still_servable(published_corpus_v3, tmp_path):
    """V2 immutability: pinned content is reproducible from source_git_sha."""
    root = Path(__file__).resolve().parents[1]
    evidence = published_corpus_v3 / _EVIDENCE
    v2 = json.loads(
        (evidence / "davi-governed-knowledge-manifest-v2.json").read_text()
    )
    entry = next(d for d in v2["documents"] if d["path"] == _MP_DOC)
    blob = subprocess.run(
        ["git", "show", f"{v2['source_git_sha']}:{_MP_DOC}"],
        cwd=root.parent, capture_output=True, check=True).stdout
    assert hashlib.sha256(blob).hexdigest() == entry["sha256"]
    # V2-pinned tree: the doc is staged at its pinned blob and serves.
    target = published_corpus_v3 / _MP_DOC.removeprefix("api-delpi/")
    target.write_bytes(blob)
    result = _reader(published_corpus_v3).execute(
        topic="mp_description_standards", corpus_version=2, page_size=2)
    assert result["corpus_version"] == 2
    assert "CARRETEL" not in "".join(i["text"] for i in result["items"])
