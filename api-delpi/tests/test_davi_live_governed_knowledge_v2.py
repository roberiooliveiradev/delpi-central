"""DAVI governed knowledge V2 — MP/PI full norms via corpus_version=2.

Proves the additive V2 revision: V1 stays byte-intact and servable, the two
ratified normative documents are retrievable with provenance, version
selection fails closed, and MCP surface stays at two tools.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

_EVIDENCE = "docs/integrations/evidence"
_MP_DOC = "api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md"
_PI_DOC = "api-delpi/docs/api/padroes-totvs/codigos-intermediarios-pi.md"


@pytest.fixture()
def published_corpus_v2(tmp_path):
    """Stage V1+V2 evidence files and all corpus documents in a sandbox."""
    root = Path(__file__).resolve().parents[1]
    evidence = root / _EVIDENCE
    paths: set[str] = set()
    for version in (1, 2):
        manifest = json.loads(
            (evidence / f"davi-governed-knowledge-manifest-v{version}.json").read_text()
        )
        index = json.loads(
            (evidence / f"davi-governed-knowledge-topics-v{version}.json").read_text()
        )
        paths.update(entry["path"] for entry in manifest["documents"])
        paths.update(entry["source_path"] for entry in index["deferred_sources"])
        paths.add(manifest["freeze_artifact"])
        paths.add(f"api-delpi/{_EVIDENCE}/davi-governed-knowledge-manifest-v{version}.json")
        paths.add(f"api-delpi/{_EVIDENCE}/davi-governed-knowledge-topics-v{version}.json")
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


def test_v2_manifest_is_pinned_and_complete(published_corpus_v2):
    manifest = json.loads(
        (published_corpus_v2 / f"{_EVIDENCE}/davi-governed-knowledge-manifest-v2.json").read_text()
    )
    paths = {doc["path"] for doc in manifest["documents"]}
    assert manifest["corpus_version"] == 2
    assert len(paths) == 17
    assert _MP_DOC in paths and _PI_DOC in paths
    # V1 15 documents remain members, byte-identical.
    v1 = json.loads(
        (published_corpus_v2 / f"{_EVIDENCE}/davi-governed-knowledge-manifest-v1.json").read_text()
    )
    v1_docs = {doc["path"]: doc["sha256"] for doc in v1["documents"]}
    v2_docs = {doc["path"]: doc["sha256"] for doc in manifest["documents"]}
    assert all(v2_docs[path] == sha for path, sha in v1_docs.items())


def test_mp_norm_read_with_provenance_and_term_bala_evidence(published_corpus_v2):
    reader = _reader(published_corpus_v2)
    result = reader.execute(topic="mp_description_standards", corpus_version=2, page_size=3)
    assert result["knowledge_kind"] == "GUIDANCE"
    assert result["authority"] == "GUIDANCE_NOT_DOMAIN_TRUTH"
    assert result["corpus_version"] == 2
    assert result["corpus_id"] == "davi-governed-knowledge"
    assert result["source_path"] == _MP_DOC
    assert len(result["manifest_identity"]) == 64
    assert len(result["source_git_sha"]) == 40
    raw = (published_corpus_v2 / _MP_DOC.removeprefix("api-delpi/")).read_bytes()
    assert result["source_sha256"] == hashlib.sha256(raw).hexdigest()
    # Normative evidence: the document really documents the TERM. prefix and BALA type.
    whole = ""
    page = 1
    while True:
        chunk = reader.execute(topic="mp_description_standards", corpus_version=2,
                               page=page, page_size=3)
        whole += "".join(item["text"] for item in chunk["items"])
        if not chunk["has_more"]:
            break
        page += 1
    assert "TERM." in whole
    assert "TERM. BALA" in whole
    assert "&lt;script" not in whole


def test_pi_norm_read_with_provenance(published_corpus_v2):
    result = _reader(published_corpus_v2).execute(
        topic="pi_intermediate_codes", corpus_version=2, page_size=2
    )
    assert result["corpus_version"] == 2
    assert result["source_path"] == _PI_DOC
    joined = "".join(item["text"] for item in result["items"])
    assert "50xx" in joined or "intermedi" in joined.lower()
    assert result["total"] >= 1


def test_version_selection_and_v1_compatibility(published_corpus_v2):
    from app.application.use_cases.read_governed_technical_knowledge_use_case import (
        KnowledgeReadError,
    )
    reader = _reader(published_corpus_v2)
    v1 = reader.execute(topic="product_master_sb1", corpus_version=1, page_size=1)
    v2 = reader.execute(topic="product_master_sb1", corpus_version=2, page_size=1)
    assert v1["corpus_version"] == 1 and v2["corpus_version"] == 2
    assert v1["items"][0]["text"] == v2["items"][0]["text"]
    assert v1["manifest_identity"] != v2["manifest_identity"]
    # V2-only topics are not visible under V1.
    with pytest.raises(KnowledgeReadError, match="NOT_FOUND"):
        reader.execute(topic="mp_description_standards", corpus_version=1)
    with pytest.raises(KnowledgeReadError, match="NOT_FOUND"):
        reader.execute(topic="pi_intermediate_codes", corpus_version=1)
    # Unsupported versions fail closed with STALE_VERSION.
    for version in (0, 3, 99):
        with pytest.raises(KnowledgeReadError, match="STALE_VERSION"):
            reader.execute(topic="product_master_sb1", corpus_version=version)


def test_v2_corruption_and_unapproved_paths_fail_closed(published_corpus_v2):
    from app.application.use_cases.read_governed_technical_knowledge_use_case import (
        KnowledgeReadError,
    )
    evidence = published_corpus_v2 / _EVIDENCE
    # Tampered V2 manifest -> CORPUS_UNAVAILABLE, and V1 stays intact.
    v2_manifest = evidence / "davi-governed-knowledge-manifest-v2.json"
    data = json.loads(v2_manifest.read_text())
    data["documents"][0]["sha256"] = "0" * 64
    v2_manifest.write_text(json.dumps(data))
    with pytest.raises(KnowledgeReadError) as exc:
        _reader(published_corpus_v2).execute(topic="mp_description_standards", corpus_version=2)
    assert exc.value.code == "CORPUS_UNAVAILABLE"
    # V1 remains servable after V2 corruption.
    result = _reader(published_corpus_v2).execute(topic="product_master_sb1", corpus_version=1, page_size=1)
    assert result["corpus_version"] == 1


def test_v2_index_rejects_unratified_promotion(published_corpus_v2):
    from app.application.use_cases.read_governed_technical_knowledge_use_case import (
        KnowledgeReadError,
    )
    index_path = published_corpus_v2 / f"{_EVIDENCE}/davi-governed-knowledge-topics-v2.json"
    index = json.loads(index_path.read_text())
    index["topics"].append({
        "id": "sneaky_topic", "title": "x", "source_path": _MP_DOC,
        "status": "FROZEN_V2", "intent": "CONCEPTUAL_GUIDANCE_ONLY", "aliases": ["x"]
    })
    index_path.write_text(json.dumps(index))
    with pytest.raises(KnowledgeReadError) as exc:
        _reader(published_corpus_v2).execute(topic="mp_description_standards", corpus_version=2)
    assert exc.value.code == "CORPUS_UNAVAILABLE"