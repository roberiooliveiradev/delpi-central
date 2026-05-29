#!/usr/bin/env python3
"""Adapta GPT_instructions (api-delpi-py) e sincroniza RAG do agente minha-delpi-chat.

Uso (container minha-delpi-ai-api):

  PYTHONPATH=/app python scripts/sync_gpt_instructions_knowledge.py \\
    --source-dir /workspace/api-delpi-py/GPT_instructions

  # Gerar arquivos + mapa + ingerir no agente (requer owner/editor):
  PYTHONPATH=/app python scripts/sync_gpt_instructions_knowledge.py \\
    --source-dir /workspace/api-delpi-py/GPT_instructions \\
    --agent-key minha-delpi-chat \\
    --user-id <uuid> \\
    --ingest

Montagem dev (delpi-central + api-delpi-py):

  docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \\
    python scripts/sync_gpt_instructions_knowledge.py \\
    --source-dir /workspace/api-delpi-py/GPT_instructions \\
    --agent-key minha-delpi-chat \\
    --user-id 4ac305a6-0569-40b8-a918-b908cfeba169 \\
    --ingest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MONOREPO_ROOT = DEFAULT_REPO_ROOT.parent
DEFAULT_SOURCE = DEFAULT_MONOREPO_ROOT.parent / "api-delpi-py" / "GPT_instructions"
DEFAULT_OUTPUT = (
    DEFAULT_REPO_ROOT
    / "docs"
    / "knowledge"
    / "domains"
    / "gpt-instructions"
)
DEFAULT_GLOBAL_OUTPUT = (
    DEFAULT_REPO_ROOT
    / "docs"
    / "knowledge"
    / "domains"
    / "global"
)
DEFAULT_COVERAGE_MAP = (
    DEFAULT_REPO_ROOT
    / "docs"
    / "knowledge"
    / "gpt-instructions-coverage-map.md"
)
DEFAULT_AGENT_KEY = "minha-delpi-chat"


def _resolve_source_path(source_dir: Path, source_file: str) -> Path:
    return source_dir / source_file


def _generate_adapted_files(source_dir: Path, output_dir: Path) -> list[dict]:
    from app.domain.services.gpt_instructions_adaptation_service import (
        GptInstructionsAdaptationService,
    )
    from app.domain.services.gpt_instructions_coverage_service import (
        GptInstructionsCoverageService,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict] = []

    for entry in GptInstructionsCoverageService.agent_ingest_sources():
        source_path = _resolve_source_path(source_dir, entry.source_file)

        if not source_path.is_file():
            generated.append(
                {
                    "sourceFile": entry.source_file,
                    "status": "missing_source",
                    "path": str(source_path),
                }
            )
            continue

        raw = source_path.read_text(encoding="utf-8")
        adapted = GptInstructionsAdaptationService.adapt(
            raw,
            source_name=entry.source_file,
        )
        out_name = GptInstructionsAdaptationService.output_filename(entry.source_file)
        out_path = output_dir / out_name
        out_path.write_text(adapted, encoding="utf-8")

        generated.append(
            {
                "sourceFile": entry.source_file,
                "status": "generated",
                "outputPath": str(out_path),
                "outputName": out_name,
                "chars": len(adapted),
                "tags": list(entry.tags),
            }
        )

    return generated


def _generate_global_files(source_dir: Path, output_dir: Path) -> list[dict]:
    from app.domain.services.agent_knowledge_filename_service import AgentKnowledgeFilenameService
    from app.domain.services.gpt_instructions_adaptation_service import (
        GptInstructionsAdaptationService,
    )
    from app.domain.services.gpt_instructions_coverage_service import (
        GptInstructionsCoverageService,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict] = []

    for entry in GptInstructionsCoverageService.global_sync_sources():
        source_path = _resolve_source_path(source_dir, entry.source_file)

        if not source_path.is_file():
            generated.append(
                {
                    "sourceFile": entry.source_file,
                    "status": "missing_source",
                    "path": str(source_path),
                    "scope": "global",
                }
            )
            continue

        raw = source_path.read_text(encoding="utf-8")
        synced = GptInstructionsAdaptationService.adapt_global(
            raw,
            source_name=entry.source_file,
        )
        out_name = AgentKnowledgeFilenameService.normalize(entry.source_file)
        out_path = output_dir / out_name
        out_path.write_text(synced, encoding="utf-8")

        generated.append(
            {
                "sourceFile": entry.source_file,
                "status": "generated",
                "outputPath": str(out_path),
                "outputName": out_name,
                "chars": len(synced),
                "tags": list(entry.tags),
                "scope": "global",
            }
        )

    readme = output_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Conhecimento global (chat base / company-knowledge)\n\n"
            "Documentos com `scope: global` — herdados por chats e agentes com skill "
            "`company-knowledge`.\n\n"
            "Regenerar com `scripts/sync_gpt_instructions_knowledge.py --sync-global`.\n",
            encoding="utf-8",
        )

    return generated


def _ingest_global_documents(*, user_id: str, generated: list[dict]) -> list[dict]:
    from app.application.dto.ingest_document_request import IngestDocumentRequest
    from app.application.services.knowledge_curatorial_metadata_service import (
        build_global_curatorial_metadata,
    )
    from app.composition.chat_composer import make_ingest_knowledge_document_use_case

    use_case = make_ingest_knowledge_document_use_case()
    results: list[dict] = []

    for item in generated:
        if item.get("status") != "generated" or item.get("scope") != "global":
            continue

        out_path = Path(item["outputPath"])
        content = out_path.read_text(encoding="utf-8")
        title = item["sourceFile"]
        source_ref = f"repo:docs/knowledge/domains/global/{item['outputName']}"

        metadata = build_global_curatorial_metadata(
            category="normas" if "normas" in (item.get("tags") or []) else "operacional",
            tags=item.get("tags") or [],
            namespace="global:company-knowledge",
            domain="delpi",
            extra={
                "origin": "sync_gpt_instructions_knowledge",
                "sourceOrigin": "api-delpi-py/GPT_instructions",
                "originalFilename": item["sourceFile"],
            },
        )

        try:
            response = use_case.execute(
                IngestDocumentRequest(
                    title=title,
                    source_type="manual",
                    source_ref=source_ref,
                    content=content,
                    metadata=metadata,
                    user_id=user_id,
                )
            )
            results.append(
                {
                    **item,
                    "ingest": "duplicate" if response.get("duplicate") else "created",
                    "documentId": response.get("id"),
                    "chunkCount": response.get("chunks"),
                }
            )
        except Exception as exc:  # noqa: BLE001 — script CLI reporta falha por arquivo
            results.append({**item, "ingest": "error", "error": str(exc)})

    return results


def _ingest_agent_sources(
    *,
    agent_key: str,
    user_id: str,
    output_dir: Path,
    generated: list[dict],
) -> list[dict]:
    from app.composition.chat_composer import make_create_agent_source_use_case
    from app.infrastructure.persistence.postgres_chat_agent_repository import (
        PostgresChatAgentRepository,
    )

    repo = PostgresChatAgentRepository()
    agents = repo.list_accessible(UUID(user_id), include_disabled=True)
    agent_id = None

    for agent, _role, _published in agents:
        if agent.key == agent_key:
            agent_id = str(agent.id)
            break

    if not agent_id:
        raise ValueError(f"Agent {agent_key!r} not found or inaccessible for user {user_id}")

    use_case = make_create_agent_source_use_case()
    results: list[dict] = []

    for item in generated:
        if item.get("status") != "generated":
            results.append({**item, "ingest": "skipped"})
            continue

        out_path = Path(item["outputPath"])
        content = out_path.read_text(encoding="utf-8")
        title = item["sourceFile"]

        try:
            response = use_case.execute_text(
                user_id=user_id,
                agent_id=agent_id,
                title=title,
                content=content,
                metadata={
                    "tags": item.get("tags") or [],
                    "categories": ["operacional", "gpt-instructions"],
                    "sourceOrigin": "api-delpi-py/GPT_instructions",
                    "originalFilename": item["sourceFile"],
                },
            )
            results.append(
                {
                    **item,
                    "ingest": "duplicate" if getattr(response, "duplicate", False) else "created",
                    "documentId": str(getattr(response, "id", "") or ""),
                    "chunkCount": getattr(response, "chunk_count", None),
                }
            )
        except Exception as exc:  # noqa: BLE001 — script CLI reporta falha por arquivo
            results.append({**item, "ingest": "error", "error": str(exc)})

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Pasta GPT_instructions do api-delpi-py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destino dos .md adaptados (agente).",
    )
    parser.add_argument(
        "--global-output-dir",
        type=Path,
        default=DEFAULT_GLOBAL_OUTPUT,
        help="Destino dos documentos globais (company-knowledge).",
    )
    parser.add_argument(
        "--coverage-map",
        type=Path,
        default=DEFAULT_COVERAGE_MAP,
        help="Destino do mapa markdown documento a documento.",
    )
    parser.add_argument("--agent-key", default=DEFAULT_AGENT_KEY)
    parser.add_argument("--user-id", help="UUID do usuário owner/editor do agente (para --ingest).")
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingerir arquivos gerados como agent_source do agente.",
    )
    parser.add_argument(
        "--sync-global",
        action="store_true",
        help="Copiar documentos globais (GPT_instructions, Normas, etc.) para domains/global/.",
    )
    parser.add_argument(
        "--ingest-global",
        action="store_true",
        help="Ingerir documentos globais na base company-knowledge (requer --sync-global e --user-id).",
    )
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        print(
            json.dumps(
                {
                    "error": "source_dir_not_found",
                    "path": str(args.source_dir),
                    "hint": "Monte api-delpi-py ou passe --source-dir.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    from app.composition.root_composer import create_application
    from app.domain.services.gpt_instructions_coverage_service import (
        GptInstructionsCoverageService,
    )

    app = create_application()
    report: dict = {"sourceDir": str(args.source_dir), "outputDir": str(args.output_dir)}

    with app.app_context():
        generated = _generate_adapted_files(args.source_dir, args.output_dir)
        report["generated"] = generated
        report["generatedCount"] = sum(1 for item in generated if item.get("status") == "generated")
        report["missingSourceCount"] = sum(
            1 for item in generated if item.get("status") == "missing_source"
        )

        if args.sync_global or args.ingest_global:
            global_generated = _generate_global_files(args.source_dir, args.global_output_dir)
            report["globalGenerated"] = global_generated
            report["globalGeneratedCount"] = sum(
                1 for item in global_generated if item.get("status") == "generated"
            )
            report["globalMissingSourceCount"] = sum(
                1 for item in global_generated if item.get("status") == "missing_source"
            )
            report["missingSourceCount"] = report.get("missingSourceCount", 0) + report[
                "globalMissingSourceCount"
            ]

        coverage_md = GptInstructionsCoverageService.build_markdown_report()
        args.coverage_map.parent.mkdir(parents=True, exist_ok=True)
        args.coverage_map.write_text(coverage_md, encoding="utf-8")
        report["coverageMapPath"] = str(args.coverage_map)

        if args.ingest:
            if not args.user_id:
                print("--user-id é obrigatório com --ingest", file=sys.stderr)
                return 2

            from app.extensions.db import db

            ingest_results = _ingest_agent_sources(
                agent_key=args.agent_key,
                user_id=args.user_id,
                output_dir=args.output_dir,
                generated=generated,
            )
            db.session.commit()
            report["ingest"] = ingest_results
            report["ingestCreated"] = sum(1 for item in ingest_results if item.get("ingest") == "created")
            report["ingestDuplicate"] = sum(
                1 for item in ingest_results if item.get("ingest") == "duplicate"
            )

        if args.ingest_global:
            if not args.user_id:
                print("--user-id é obrigatório com --ingest-global", file=sys.stderr)
                return 2
            if not args.sync_global:
                print("--ingest-global requer --sync-global", file=sys.stderr)
                return 2

            from app.extensions.db import db

            global_ingest = _ingest_global_documents(
                user_id=args.user_id,
                generated=report.get("globalGenerated") or [],
            )
            db.session.commit()
            report["globalIngest"] = global_ingest
            report["globalIngestCreated"] = sum(
                1 for item in global_ingest if item.get("ingest") == "created"
            )
            report["globalIngestDuplicate"] = sum(
                1 for item in global_ingest if item.get("ingest") == "duplicate"
            )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("missingSourceCount", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
