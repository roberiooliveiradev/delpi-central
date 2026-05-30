#!/usr/bin/env python3
"""Exporta fontes do agente para docs/knowledge/domains/agents/{agent_id}/ (importação).

Lê documentos agent_source do banco e copia arquivos do storage local com nomes normalizados.

Uso:
  PYTHONPATH=/app python scripts/export_agent_knowledge_bundle.py \\
    --agent-id 11111111-1111-4111-8111-111111111111 \\
    [--user-id UUID]
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from app.composition.root_composer import create_application
from app.domain.services.agent_knowledge_filename_service import AgentKnowledgeFilenameService
from app.infrastructure.persistence.postgres_knowledge_repository import PostgresKnowledgeRepository

DEFAULT_AGENT_ID = "11111111-1111-4111-8111-111111111111"
OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "docs" / "knowledge" / "domains" / "agents"


def _resolve_content(document, metadata: dict) -> tuple[bytes, str]:
    storage_path = metadata.get("storagePath") or document.source_ref
    path = Path(str(storage_path)) if storage_path else None

    original = metadata.get("originalFilename") or document.title or "documento.md"
    filename = AgentKnowledgeFilenameService.normalize(original, title=document.title)

    if path and path.is_file():
        return path.read_bytes(), filename

    text = str(document.content or "").strip()
    if not text:
        raise ValueError("sem conteúdo nem arquivo no storage")

    if not Path(filename).suffix:
        filename = f"{filename}.md"

    return text.encode("utf-8"), filename


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta bundle de conhecimento do agente")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT_ID)
    parser.add_argument("--user-id", default=None, help="Opcional; só para log")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Destino (default: docs/knowledge/domains/agents/{agent_id})",
    )
    args = parser.parse_args()

    agent_id = args.agent_id.strip()
    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_ROOT / agent_id
    output_dir.mkdir(parents=True, exist_ok=True)

    app = create_application()
    exported: list[dict] = []
    errors: list[str] = []

    with app.app_context():
        knowledge_repo = PostgresKnowledgeRepository()

        documents = knowledge_repo.list_documents_by_metadata(
            filters={"scope": "agent_source", "agentId": agent_id},
            limit=500,
            active=True,
        )

        for document, chunk_count in documents:
            metadata = document.metadata or {}
            original = metadata.get("originalFilename") or document.title

            try:
                content, filename = _resolve_content(document, metadata)
            except ValueError as exc:
                errors.append(f"{original}: {exc}")
                continue

            target = output_dir / filename
            target.write_bytes(content)

            exported.append(
                {
                    "canonicalFilename": filename,
                    "originalFilename": original,
                    "title": document.title,
                    "documentId": str(document.id),
                    "chunkCount": chunk_count,
                    "sizeBytes": len(content),
                }
            )

    manifest = {
        "agentId": agent_id,
        "exportedAt": datetime.now(UTC).isoformat(),
        "outputDir": str(output_dir),
        "fileCount": len(exported),
        "files": sorted(exported, key=lambda item: item["canonicalFilename"]),
        "errors": errors,
        "namingConvention": {
            "pattern": "{categoria}-{topico}[-detalhe].{ext}",
            "categories": ["api", "sql", "drawing", "produto", "engenharia"],
            "note": "Nomes normalizados por AgentKnowledgeFilenameService para facilitar RAG e reimportação.",
        },
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = output_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Conhecimento exportado — agente `{agent_id}`\n\n"
            "Pasta para **importação/reimportação** de fontes do agente no admin ou via "
            "`POST /chat/agents/{{id}}/sources` (multipart).\n\n"
            "Regenerar com `scripts/export_agent_knowledge_bundle.py`.\n\n"
            "Ver `manifest.json` para mapeamento original → nome canônico.\n",
            encoding="utf-8",
        )

    # Copia guia de rotas curado se existir na base global do repo
    routes_src = Path(__file__).resolve().parents[1] / "docs" / "knowledge" / "api-delpi-rotas-agente.md"
    routes_dst = output_dir / "api-delpi-rotas-agente.md"
    if routes_src.is_file() and not routes_dst.exists():
        shutil.copy2(routes_src, routes_dst)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
