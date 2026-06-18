# Documentos para inteligência de agentes

Arquivos desta pasta são pensados para **ingestão na base de conhecimento** (`POST /knowledge/documents` ou upload no painel admin) e vinculação ao escopo RAG do agente.

**Changelog recente (maio/2026):** [`../changelog/2026-05-inteligencia-chat-entregas.md`](../changelog/2026-05-inteligencia-chat-entregas.md).

## Estrutura de pastas

| Pasta | Escopo RAG | Conteúdo |
|-------|------------|----------|
| [`sources/gpt-instructions/`](./sources/gpt-instructions/) | referência (não RAG direto) | Espelho verbatim de `api-delpi-py/GPT_instructions` — base para implementações |
| [`domains/global/`](./domains/global/) | `global` / `company-knowledge` | Normas Técnicas, GPT_instructions, O Arquiteto |
| [`domains/agents/minha-delpi-chat/`](./domains/agents/minha-delpi-chat/) | `agent_source` | Bundle exportável do agente (12 fontes + manifest) |
| [`domains/gpt-instructions/`](./domains/gpt-instructions/) | ingestão agente | Markdown adaptado da pasta `GPT_instructions` (api-delpi-py) |
| Raiz (`api-delpi-rotas-agente.md`, …) | agente / global | Guias curados e mapas |

## Documentos disponíveis

| Arquivo | Uso |
|---------|-----|
| [api-delpi-rotas-agente.md](./api-delpi-rotas-agente.md) | Agente com provider OpenAPI **api-delpi** — mapa intenção → rota, permissões, sinônimos e exemplos (maio/2026) |
| [treinamento-agente-interacoes-jun2026.md](./treinamento-agente-interacoes-jun2026.md) | **Treinamento ao vivo** — 6 interações copiar/colar (fabril, preço MP, simulador, fontes do projeto) |
| [gpt-instructions-coverage-map.md](./gpt-instructions-coverage-map.md) | Mapa documento a documento: GPT_instructions (api-delpi-py) × agente `minha-delpi-chat` |
| [chat-intelligence-settings-profiles.md](./chat-intelligence-settings-profiles.md) | Perfis **dev** e **produção** — toggles do Admin → Inteligência do chat |
| [sources/gpt-instructions/](./sources/gpt-instructions/) | **Cópia verbatim** da pasta GPT_instructions (14 .md + PDF) — fonte para sync e implementações |
| [domains/gpt-instructions/](./domains/gpt-instructions/) | Markdown **adaptado** (rotas api-delpi) gerado por `scripts/sync_gpt_instructions_knowledge.py` |
| [domains/global/](./domains/global/) | **Conhecimento global** (`company-knowledge`) — Normas, GPT_instructions, O Arquiteto |
| [domains/agents/minha-delpi-chat/](./domains/agents/minha-delpi-chat/) | **Bundle exportável** das fontes do agente (nomes normalizados + `manifest.json`) |
| [../roadmap/api-delpi-chat-intelligence-audit.md](../roadmap/api-delpi-chat-intelligence-audit.md) | Auditoria técnica rota a rota, erros conhecidos, testes de regressão (dev) |
| [../roadmap/playbook-15-rotas-operacionais-sem-sql.md](../roadmap/playbook-15-rotas-operacionais-sem-sql.md) | Roadmap: rotas REST produção/consumo/compras/perdas (substituir `/data/sql`) |

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
| Inteligência (ondas 1–11) | [`../roadmap/README.md`](../roadmap/README.md) |
| Análise de desenhos PDF (backlog) | [`../roadmap/inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md`](../roadmap/inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) |
| Arquitetura chat base | [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) |
| Playbook 15 — rotas sem SQL | [`../roadmap/playbook-15-rotas-operacionais-sem-sql.md`](../roadmap/playbook-15-rotas-operacionais-sem-sql.md) |
| Perfis inteligência do chat (dev/prod) | [`chat-intelligence-settings-profiles.md`](./chat-intelligence-settings-profiles.md) |
| Changelog maio/2026 | [`../changelog/2026-05-inteligencia-chat-entregas.md`](../changelog/2026-05-inteligencia-chat-entregas.md) |

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
3. **Sincronizar GPT_instructions:** `PYTHONPATH=/app python scripts/sync_gpt_instructions_knowledge.py` (fonte padrão: `docs/knowledge/sources/gpt-instructions/`; ou `--source-dir …/api-delpi-py/GPT_instructions`) `--agent-key minha-delpi-chat --user-id <uuid> --ingest`
4. **Sincronizar conhecimento global:** `… --sync-global [--ingest-global --user-id <uuid>]` → `docs/knowledge/domains/global/` (inclui `normas-tecnicas-delpi.md`)
5. **Exportar bundle do agente:** `PYTHONPATH=/app python scripts/export_agent_knowledge_bundle.py --agent-key minha-delpi-chat` → `docs/knowledge/domains/agents/minha-delpi-chat/`
6. **Smoke melhorias GPT/SQL:** conferir perfil em [`chat-intelligence-settings-profiles.md`](./chat-intelligence-settings-profiles.md); perguntas G1–G14 / N1–N14 em [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md); script `PYTHONPATH=/app python scripts/smoke_gpt_instructions_improvements.py [user_id] [session_id]`
7. Reindexar `api-delpi-rotas-agente.md` na base de conhecimento
8. Revisar [`../roadmap/api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md) e rodar a suíte de regressão documentada em [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)
