# Conhecimento global (chat base / company-knowledge)

Documentos com `scope: global` — herdados por chats e agentes com skill **`company-knowledge`** (default `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL=true`).

## Arquivos

| Arquivo | Origem | Uso |
|---------|--------|-----|
| [normas-tecnicas-delpi.md](./normas-tecnicas-delpi.md) | `GPT_instructions/Normas_Tecnicas_DELPI.md` | Descrição técnica de matérias-primas (grupos 1001–1025); intent `ChatTechnicalDescriptionIntentService` |
| [gpt-instructions.md](./gpt-instructions.md) | `GPT_instructions/GPT_instructions.md` | Regras gerais de comportamento GPT |
| [o-arquiteto-do-codigo.md](./o-arquiteto-do-codigo.md) | `GPT_instructions/O_ARQUITETO_DO_CODIGO.md` | Identidade / plataforma DELPI |

## Sincronizar

Monte `api-delpi-py` e rode no container:

```bash
docker compose -f infra/docker-compose.dev.yml run --rm \
  -v /caminho/api-delpi-py:/workspace/api-delpi-py:ro \
  -e PYTHONPATH=/app minha-delpi-ai-api \
  python scripts/sync_gpt_instructions_knowledge.py \
  --source-dir /workspace/api-delpi-py/GPT_instructions \
  --sync-global --ingest-global --user-id <uuid>
```

Saída: arquivos nesta pasta + ingestão na base RAG (`scope: global`).

## Perguntas típicas (chat)

- «Como descrever um terminal?» → RAG **Normas**, grupo **1008**, sem API de catálogo.
- «Qual a descrição do produto X?» → API REST (cadastro existente) — **não** usa Normas como lookup.

Checklist **N1–N4:** [`../../testing/smoke-operacional-manual.md`](../../testing/smoke-operacional-manual.md).
