# Documentos para inteligência de agentes

Arquivos desta pasta são pensados para **ingestão na base de conhecimento** (`POST /knowledge/documents` ou upload no painel admin) e vinculação ao escopo RAG do agente.

## Documentos disponíveis

| Arquivo | Uso |
|---------|-----|
| [api-delpi-rotas-agente.md](./api-delpi-rotas-agente.md) | Agente com provider OpenAPI **api-delpi** — mapa intenção → rota, permissões, sinônimos e exemplos (maio/2026) |
| [gpt-instructions-coverage-map.md](./gpt-instructions-coverage-map.md) | Mapa documento a documento: GPT_instructions (api-delpi-py) × agente `minha-delpi-chat` |
| [domains/gpt-instructions/](./domains/gpt-instructions/) | Markdown adaptado gerado por `scripts/sync_gpt_instructions_knowledge.py` |
| [../roadmap/api-delpi-chat-intelligence-audit.md](../roadmap/api-delpi-chat-intelligence-audit.md) | Auditoria técnica rota a rota, erros conhecidos, testes de regressão (dev) |

## Documentação técnica relacionada

| Área | Caminho |
|------|---------|
| API do chat (HTTP) | [`../api/README.md`](../api/README.md) |
| Actions OpenAPI | [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md) |
| Skills (prompt) | [`../api/11-skills.md`](../api/11-skills.md) |
| Modelo conceitual | [`../api/12-modelo-conceitual.md`](../api/12-modelo-conceitual.md) |
| Guia api-delpi (resumo) | [`../../../api-delpi/docs/api/11-guia-agente-chat.md`](../../../api-delpi/docs/api/11-guia-agente-chat.md) |
| Módulos api-delpi | [`../../../api-delpi/docs/api/06-modulos-departamentais.md`](../../../api-delpi/docs/api/06-modulos-departamentais.md) |
| Policy injetada em runtime | [`../../app/domain/prompt_policies/api-delpi-routes.md`](../../app/domain/prompt_policies/api-delpi-routes.md) |
| Inteligência (ondas 1–10) | [`../roadmap/README.md`](../roadmap/README.md) |
| Arquitetura chat base | [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) |

## Como anexar a um agente

1. **Admin → Conhecimento** — faça upload do `.md` ou cole o conteúdo em ingestão de texto.
2. Metadados sugeridos:
   - `tags`: `api-delpi`, `operacional`, `rotas`
   - `categories`: `operacional` (ou domínio do seu catálogo)
   - `namespaces`: conforme especialização do agente (ex.: `global:operacional`)
3. Na **especialização do agente**, inclua os `knowledgeTags` / `knowledgeCategories` que filtram esse documento.
4. Vincule o provider **api-delpi** ao agente (`authMode: user_token`) e **reimporte** o OpenAPI após cada deploy da api-delpi.
5. **Publique** o agente (`POST /chat/agents/{id}/publish`) para que visitantes usem a configuração em produção.

O arquivo `app/domain/prompt_policies/api-delpi-routes.md` é injetado automaticamente no prompt quando uma ferramenta `execute_external_action` da API DELPI é executada (complementa o RAG).

## Atualização

Sempre que rotas ou comportamento de seleção mudarem na api-delpi ou no pipeline do chat:

1. Deploy da api-delpi
2. **Sincronizar OpenAPI:** `PYTHONPATH=/app python scripts/sync_api_delpi_openapi.py` (reimport + embeddings + [`_generated/api-delpi-openapi-catalog.md`](./_generated/api-delpi-openapi-catalog.md))
3. **Sincronizar GPT_instructions:** `PYTHONPATH=/app python scripts/sync_gpt_instructions_knowledge.py --source-dir …/api-delpi-py/GPT_instructions --agent-key minha-delpi-chat --user-id <uuid> --ingest`
4. **Smoke melhorias GPT/SQL:** `PYTHONPATH=/app python scripts/smoke_gpt_instructions_improvements.py [user_id] [session_id]`
5. Reindexar `api-delpi-rotas-agente.md` na base de conhecimento
6. Revisar [`../roadmap/api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md) e rodar a suíte de regressão documentada em [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)
