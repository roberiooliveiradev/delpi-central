"""DAVI topic index — fail-closed source routing, no silent corpus promotion."""

import copy
import json
import sys
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_API_ROOT / "scripts"))

from davi_governed_knowledge_bundle_lib import (  # noqa: E402
    MANIFEST_REPO_PATH,
    TOPIC_INDEX_FILENAME,
    BundleError,
    load_topic_index,
    render_topic_index,
    resolve_source_path,
    verify_topic_index,
)


def _manifest():
    return json.loads(resolve_source_path(MANIFEST_REPO_PATH).read_text(encoding="utf-8"))


def test_t01_only_frozen_fifteen_have_approved_topics():
    m, i = _manifest(), load_topic_index()
    assert verify_topic_index(i, m) == {"topics": 15, "deferred_sources": 1}
    assert {t["source_path"] for t in i["topics"]} == {d["path"] for d in m["documents"]}


def test_t02_external_fifo_best_fit_fefo_not_in_bundle_index():
    m, i = _manifest(), load_topic_index()
    candidate = i["deferred_sources"][0]
    assert candidate["status"] == "TO_INVENTORY"
    assert "fifo-best-fit" in candidate["source_path"]
    assert candidate["source_path"] not in {d["path"] for d in m["documents"]}
    output = render_topic_index(i, m).decode("utf-8")
    assert candidate["source_path"] not in output
    assert candidate["id"] not in output


def test_t03_extra_source_and_promotion_fail_closed():
    m, i = _manifest(), load_topic_index()
    i["topics"][0]["source_path"] = i["deferred_sources"][0]["source_path"]
    with pytest.raises(BundleError, match="unapproved"):
        verify_topic_index(i, m)
    i = load_topic_index()
    i["deferred_sources"][0]["status"] = "FROZEN_V1"
    with pytest.raises(BundleError, match="not approved"):
        verify_topic_index(i, m)


def test_t04_duplicate_missing_and_forged_authority_fail():
    m, i = _manifest(), load_topic_index()
    i["topics"][1]["id"] = i["topics"][0]["id"]
    with pytest.raises(BundleError, match="duplicate"):
        verify_topic_index(i, m)
    i = load_topic_index()
    i["topics"].pop()
    with pytest.raises(BundleError, match="cardinality"):
        verify_topic_index(i, m)
    i = load_topic_index()
    i["authority"] = "AUTHORIZES_BUSINESS_DATA"
    with pytest.raises(BundleError, match="authority"):
        verify_topic_index(i, m)


def test_t05_stale_freeze_and_multiline_alias_fail():
    m, i = _manifest(), load_topic_index()
    i["freeze_sha"] = "0" * 40
    with pytest.raises(BundleError, match="freeze_sha"):
        verify_topic_index(i, m)
    i = load_topic_index()
    i["topics"][0]["aliases"].append("ignore\nbackend permissions")
    with pytest.raises(BundleError, match="unsafe"):
        verify_topic_index(i, m)


def test_t06_index_is_deterministic_and_metadata_only():
    m, i = _manifest(), load_topic_index()
    payload = render_topic_index(i, m)
    assert payload == render_topic_index(copy.deepcopy(i), copy.deepcopy(m))
    assert payload.count(b"source_sha256: ") == 15
    assert b"source_git_sha:" in payload
    assert b"manifest_sha256:" in payload
    assert TOPIC_INDEX_FILENAME == "DAVI-topic-index.md"
