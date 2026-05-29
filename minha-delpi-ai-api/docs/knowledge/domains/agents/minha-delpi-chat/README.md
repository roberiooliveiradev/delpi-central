# Conhecimento exportado — agente `minha-delpi-chat`

Pasta para **importação/reimportação** de fontes do agente no admin ou via `POST /chat/agents/{id}/sources` (multipart).

## Conteúdo

- **12 arquivos** com nomes canônicos (ex.: `sql-data-api-instructions.md`, `drawing-rules-delpi.md`)
- **`manifest.json`** — mapeamento `originalFilename` → `canonicalFilename`, IDs no banco, chunk counts

## Padrão de nomes

`{categoria}-{topico}[-detalhe].{ext}` — categorias: `api-`, `sql-`, `drawing-`, `produto-`, `engenharia-`.

Normalização: `AgentKnowledgeFilenameService` + `scripts/export_agent_knowledge_bundle.py`.

## Regenerar do banco

```bash
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
  python scripts/export_agent_knowledge_bundle.py --agent-key minha-delpi-chat
```

## O que não entra aqui

Documentos **globais** (`company-knowledge`) ficam em [`../global/`](../global/) — ex.: `normas-tecnicas-delpi.md`.

## Download na UI

Fontes do agente: botão **Baixar** no builder (`GET /chat/sources/{id}/download`).
