"""CLARA — pipeline governado de ingestão do corpus PROC-0072.

Somente fontes explicitamente autorizadas no manifest são ingeridas —
nunca varredura indiscriminada do repositório. Cada item carrega
proveniência verificável: ``source_id``, versão/SHA da fonte, hash do
conteúdo e ``citation_locator`` (documento + caminho de seção).

Reindexação governada: para um mesmo locator estável (documento +
heading path), conteúdo alterado gera novo item que SUPERSEDE o
anterior — o histórico permanece consultável, a recuperação retorna
somente ``PUBLISHED``.

Execução: ``python -m controllership_finance_app.application.clara.
corpus_ingestion --docs-root <repo>/docs/... [--publish]``.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from controllership_finance_app.infrastructure.persistence.clara_knowledge_repository import (
    ClaraKnowledgeRepository,
)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


@dataclass(frozen=True)
class SourceSpec:
    """Fonte autorizada do corpus — inventário explícito, nunca glob."""

    source_id: str
    path: str  # relativo a docs_root
    source_type: str
    name: str
    origin_authority: str
    evidence_classification: str
    topic: str
    business_step: str | None = None
    related_report_ids: tuple[str, ...] = ()
    access_scope: str = "PORTAL_ACCESS"
    description: str | None = None


@dataclass
class Segment:
    title: str
    heading_path: str
    content: str
    line_start: int
    line_end: int


def segment_markdown(text: str, *, max_chars: int = 6000) -> list[Segment]:
    """Segmenta por headings ATX preservando o caminho de seção.

    Seções acima de ``max_chars`` são divididas em partes ordenadas —
    o heading path é mantido, o locator ganha sufixo de parte.
    """
    lines = text.splitlines()
    segments: list[Segment] = []
    stack: list[tuple[int, str]] = []
    current_title = "Documento"
    current_path = "documento"
    buf: list[str] = []
    buf_start = 1

    def _flush(end_line: int) -> None:
        nonlocal buf, buf_start
        body = "\n".join(buf).strip()
        if body:
            for part_idx in range(0, len(body), max_chars):
                chunk = body[part_idx : part_idx + max_chars]
                part = part_idx // max_chars
                segments.append(
                    Segment(
                        title=current_title,
                        heading_path=(
                            current_path
                            if part == 0
                            else f"{current_path}#part-{part + 1}"
                        ),
                        content=chunk,
                        line_start=buf_start,
                        line_end=end_line,
                    )
                )
        buf = []

    for idx, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            _flush(idx - 1)
            level = len(match.group(1))
            title = match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            current_title = title
            current_path = " > ".join(t for _, t in stack)
            buf_start = idx + 1
            continue
        if not buf and not line.strip():
            buf_start = idx + 1
            continue
        buf.append(line)
    _flush(len(lines))
    return segments


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest_source(
    spec: SourceSpec,
    *,
    docs_root: Path,
    repository: ClaraKnowledgeRepository,
    actor: str = "clara-corpus-ingestion",
) -> dict[str, Any]:
    """Ingere uma fonte autorizada com supersede governado.

    Retorna estatísticas honestas — um arquivo inexistente falha
    alto (nunca marca ingestão como sucesso sem conteúdo).
    """
    path = docs_root / spec.path
    if not path.is_file():
        raise FileNotFoundError(
            f"Fonte declarada e ausente: {spec.path}"
        )
    raw = path.read_text(encoding="utf-8")
    source_hash = _sha256_file(path)
    repository.register_source(
        source_id=spec.source_id,
        source_type=spec.source_type,
        name=spec.name,
        source_version=source_hash[:12],
        source_hash=source_hash,
        origin_authority=spec.origin_authority,
        description=spec.description,
        metadata={
            "path": spec.path,
            "ingested_by": actor,
        },
    )
    segments = segment_markdown(raw)
    inserted = superseded = deduplicated = 0
    for seg in segments:
        locator_key = f"{spec.path}::{seg.heading_path}"
        locator = {
            "key": locator_key,
            "document": spec.path,
            "heading_path": seg.heading_path,
            "source_id": spec.source_id,
            "source_version": source_hash[:12],
            "line_range": [seg.line_start, seg.line_end],
        }
        result = repository.ingest_item(
            source_id=spec.source_id,
            topic=spec.topic,
            title=seg.title,
            content=seg.content,
            business_step=spec.business_step,
            related_report_ids=list(spec.related_report_ids),
            origin_authority=spec.origin_authority,
            evidence_classification=spec.evidence_classification,
            citation_locator=locator,
            access_scope=spec.access_scope,
        )
        if result.get("_deduplicated"):
            deduplicated += 1
        elif result.get("_superseded"):
            superseded += 1
        else:
            inserted += 1
    return {
        "source_id": spec.source_id,
        "segments": len(segments),
        "inserted": inserted,
        "superseded": superseded,
        "deduplicated": deduplicated,
        "source_hash": source_hash,
    }


def ingest_manifest(
    specs: list[SourceSpec],
    *,
    docs_root: Path,
    repository: ClaraKnowledgeRepository | None = None,
    publish: bool = True,
    actor: str = "clara-corpus-ingestion",
) -> dict[str, Any]:
    repo = repository or ClaraKnowledgeRepository()
    results = []
    failures = []
    for spec in specs:
        try:
            results.append(ingest_source(
                spec, docs_root=docs_root, repository=repo, actor=actor
            ))
        except Exception as exc:  # noqa: BLE001
            failures.append(
                {"source_id": spec.source_id, "error": str(exc)}
            )
    corpus = None
    if publish and not failures:
        corpus = repo.publish_corpus_version(
            actor=actor,
            manifest={
                "sources": [r["source_id"] for r in results],
                "docs_root": str(docs_root),
            },
        )
    return {
        "ingested": len(results),
        "failed": len(failures),
        "failures": failures,
        "results": results,
        "corpus_version": (
            {
                "corpus_version_id": str(corpus["corpus_version_id"]),
                "item_count": corpus["item_count"],
                "source_count": corpus["source_count"],
            }
            if corpus
            else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingestão governada do corpus CLARA (PROC-0072)."
    )
    parser.add_argument("--docs-root", required=True)
    parser.add_argument("--no-publish", action="store_true")
    parser.add_argument("--actor", default="clara-corpus-ingestion")
    args = parser.parse_args()
    from controllership_finance_app.application.clara.corpus_manifest import (  # noqa: E501
        AUTHORIZED_SOURCES,
    )

    outcome = ingest_manifest(
        AUTHORIZED_SOURCES,
        docs_root=Path(args.docs_root),
        publish=not args.no_publish,
        actor=args.actor,
    )
    import json

    print(json.dumps(outcome, indent=2, default=str))
    if outcome["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
