#!/usr/bin/env python3
"""Ingestão RAG do agente de desenho — fontes em docs/knowledge/domains/agents/minha-delpi-chat.

Uso (container minha-delpi-ai-api):

  PYTHONPATH=/app python scripts/sync_drawing_agent_knowledge.py --list

  PYTHONPATH=/app python scripts/sync_drawing_agent_knowledge.py \\
    --agent-id b85edd53-2fd9-4e2f-ab17-92fd288f4f85 \\
    --user-id <uuid> \\
    --ingest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGENT_DIR = (
    DEFAULT_REPO_ROOT
    / "docs"
    / "knowledge"
    / "domains"
    / "agents"
    / "minha-delpi-chat"
)
DEFAULT_MANIFEST = DEFAULT_AGENT_DIR / "manifest.json"
DEFAULT_AGENT_ID = "b85edd53-2fd9-4e2f-ab17-92fd288f4f85"


def _collect_sources() -> list[dict]:
    from app.domain.services.chat_drawing_agent_knowledge_coverage_service import (
        ChatDrawingAgentKnowledgeCoverageService,
    )

    return [
        {
            "sourceFile": entry.source_file,
            "title": entry.title,
            "tags": list(entry.tags),
            "notes": entry.notes,
        }
        for entry in ChatDrawingAgentKnowledgeCoverageService.ingest_sources()
    ]


def _ingest_sources(
    *,
    agent_id: str,
    user_id: str,
    source_dir: Path,
) -> list[dict]:
    from app.composition.chat_composer import make_create_agent_source_use_case
    from app.infrastructure.persistence.postgres_chat_agent_repository import (
        PostgresChatAgentRepository,
    )

    repo = PostgresChatAgentRepository()
    agents = repo.list_accessible(UUID(user_id), include_disabled=True)
    requested_agent_id = str(agent_id).strip()
    resolved_agent_id = None

    for agent, _role, _published in agents:
        if str(agent.id) == requested_agent_id:
            resolved_agent_id = str(agent.id)
            break

    if not resolved_agent_id:
        raise ValueError(
            f"Agent {requested_agent_id!r} not found or inaccessible for user {user_id}"
        )

    use_case = make_create_agent_source_use_case()
    results: list[dict] = []

    for item in _collect_sources():
        source_path = source_dir / item["sourceFile"]

        if not source_path.is_file():
            results.append({**item, "status": "missing_source", "path": str(source_path)})
            continue

        content = source_path.read_text(encoding="utf-8")

        try:
            response = use_case.execute_text(
                user_id=user_id,
                agent_id=resolved_agent_id,
                title=item["title"],
                content=content,
                metadata={
                    "tags": item.get("tags") or [],
                    "categories": ["engenharia", "desenho"],
                    "sourceOrigin": "docs/knowledge/domains/agents/minha-delpi-chat",
                    "originalFilename": item["sourceFile"],
                },
            )
            results.append(
                {
                    **item,
                    "status": "ingested",
                    "ingest": "duplicate" if getattr(response, "duplicate", False) else "created",
                    "documentId": str(getattr(response, "id", "") or ""),
                    "chunkCount": getattr(response, "chunk_count", None),
                    "chars": len(content),
                }
            )
        except Exception as exc:  # noqa: BLE001 — script CLI reporta falha por arquivo
            results.append({**item, "status": "error", "error": str(exc)})

    return results


def _update_manifest(results: list[dict], manifest_path: Path) -> None:
    if not manifest_path.is_file():
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")

    if not isinstance(files, list):
        return

    by_name = {
        str(item.get("sourceFile") or ""): item
        for item in results
        if item.get("status") == "ingested"
    }

    for entry in files:
        canonical = str(entry.get("canonicalFilename") or "")

        if canonical not in by_name:
            continue

        ingested = by_name[canonical]
        document_id = str(ingested.get("documentId") or "").strip()

        if document_id:
            entry["documentId"] = document_id

        chunk_count = ingested.get("chunkCount")

        if chunk_count is not None:
            entry["chunkCount"] = chunk_count

        entry["sizeBytes"] = ingested.get("chars") or entry.get("sizeBytes") or 0

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_AGENT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--agent-id", default=DEFAULT_AGENT_ID)
    parser.add_argument("--user-id", help="UUID owner/editor do agente (obrigatório com --ingest).")
    parser.add_argument("--list", action="store_true", help="Listar fontes canônicas.")
    parser.add_argument("--ingest", action="store_true", help="Ingerir fontes no agente.")
    args = parser.parse_args()

    if args.list:
        print(json.dumps(_collect_sources(), ensure_ascii=False, indent=2))
        return 0

    if not args.ingest:
        parser.error("Informe --list ou --ingest")

    if not args.user_id:
        print("--user-id é obrigatório com --ingest", file=sys.stderr)
        return 2

    if not args.source_dir.is_dir():
        print(
            json.dumps(
                {"error": "source_dir_not_found", "path": str(args.source_dir)},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    from app.composition.root_composer import create_application

    app = create_application()

    with app.app_context():
        from app.extensions.db import db

        results = _ingest_sources(
            agent_id=args.agent_id,
            user_id=args.user_id,
            source_dir=args.source_dir,
        )
        _update_manifest(results, args.manifest)
        db.session.commit()

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0 if all(item.get("status") == "ingested" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
