"""Fail-fast source completeness for CLARA's curated operational fichas."""

from __future__ import annotations

import re
from pathlib import Path

from clara_golden_set_r01_r15 import GOLDEN_SET, NEGATIVE_SET
from controllership_finance_app.application.clara.corpus_ingestion import segment_markdown
from controllership_finance_app.application.clara.corpus_manifest import (
    AUTHORIZED_SOURCES,
    OPERATIONAL_SOURCE_IDS,
    STALE_SEGMENT_FIXES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OBSOLETE_CORPUS = "5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00"


def _operational_segments():
    result = {}
    for spec in AUTHORIZED_SOURCES:
        if spec.source_id not in OPERATIONAL_SOURCE_IDS:
            continue
        content = (REPO_ROOT / spec.path).read_text(encoding="utf-8")
        assert OBSOLETE_CORPUS not in content, spec.path
        fixes = [f for f in STALE_SEGMENT_FIXES if f["source_id"] == spec.source_id]
        kept = []
        for segment in segment_markdown(content):
            entry = next((f for f in fixes
                          if f["title_contains"] in segment.title
                          or f["title_contains"] in segment.heading_path), None)
            if entry and entry["action"] == "drop":
                continue
            body = segment.content
            if entry and entry["action"] == "fix":
                for old, new in entry.get("fix_lines", ()):
                    body = body.replace(old, new)
            kept.append((segment.heading_path, body))
        result[spec.source_id] = (spec, kept)
    return result


def test_canonical_operational_source_coverage_for_115_cases():
    sources = _operational_segments()
    assert set(sources) == OPERATIONAL_SOURCE_IDS
    assert len(GOLDEN_SET) == 105 and len(NEGATIVE_SET) == 10
    for case in GOLDEN_SET + NEGATIVE_SET:
        required = case.get("asserts") or case.get("markers") or []
        cited = set(case.get("cite") or sources)
        found = False
        for source_id, (spec, segments) in sources.items():
            if source_id not in cited or case["report_id"] not in spec.related_report_ids:
                continue
            for _, segment in segments:
                if all(re.search(r"(?<!\w)" + re.escape(marker.lower()) +
                                 r"(?!\w)", segment.lower())
                       for marker in required):
                    found = True
                    break
            if found:
                break
        assert found, (case["id"], "no citable operational segment", required)


def test_r09_superseded_timeline_not_ingested():
    _, segments = _operational_segments()["ficha-r09"]
    obsolete_headings = ("Histórico de implementação", "Atualização — Gate 040",
                         "Atualização — Gate 041", "Atualização — Gate 042",
                         "Registro anterior")
    assert not any(
        any(heading in path for heading in obsolete_headings)
        for path, _ in segments
    )
