# Minha DELPI AI API — Documentação técnica

> **Pacote:** `minha-delpi-ai-api`  
> **Status:** documentação oficial (jun/2026)  
> **Base URL (gateway):** `/apps/minha-delpi-ai/api`

Índice central de toda a documentação deste serviço. Para visão da plataforma (gateway, portal, plugins), ver também [`../../docs/08-plugins/minha-delpi-chat/documentacao-tecnica.md`](../../docs/08-plugins/minha-delpi-chat/documentacao-tecnica.md).

---

## Comece por aqui

| Ordem | Documento | Para quem |
|------:|-----------|-----------|
| 1 | [api/00-visao-geral.md](./api/00-visao-geral.md) | Auth, erros, SSE, permissões |
| 2 | [architecture/chat-intelligence-base.md](./architecture/chat-intelligence-base.md) | Pipeline de inteligência (leitura obrigatória para backend) |
| 3 | [development/guia-desenvolvimento.md](./development/guia-desenvolvimento.md) | Onde colocar código, testes, PR |
| 4 | [api/README.md](./api/README.md) | Referência HTTP completa |

---

## Mapa de pastas `docs/`

```text
docs/
  README.md              ← você está aqui
  api/                   # Contratos HTTP (endpoints, payloads, SSE)
  architecture/          # Pipeline, apresentação, memória, ADRs
  development/           # Guia do desenvolvedor, estrutura de código
  knowledge/             # Documentos RAG para agentes (não é código)
  roadmap/               # Evolução, playbooks, ondas de inteligência
  changelog/             # Entregas datadas (mai–jun/2026)
  testing/               # Smokes, homologação, casos manuais
```

---

## API HTTP (`docs/api/`)

Referência baseada nas rotas reais do Flask e nos tipos do plugin `minha-delpi-chat`.

| Arquivo | Conteúdo |
|---------|----------|
| [README.md](./api/README.md) | Índice e permissões |
| [00-visao-geral.md](./api/00-visao-geral.md) | Base URL, auth, erros, SSE |
| [01-health-status-capabilities.md](./api/01-health-status-capabilities.md) | Health, status, capabilities |
| [02-chat-sessoes-mensagens.md](./api/02-chat-sessoes-mensagens.md) | Sessões, stream, pin, resend |
| [03-agentes.md](./api/03-agentes.md) | CRUD, publicar, preview, shares |
| [04-actions-openapi.md](./api/04-actions-openapi.md) | Providers, rotas, teste |
| [05-projetos-fontes-anexos-artefatos.md](./api/05-projetos-fontes-anexos-artefatos.md) | Projetos, anexos, download |
| [06-knowledge.md](./api/06-knowledge.md) | Ingestão e busca RAG |
| [07-tools.md](./api/07-tools.md) | Tools internas |
| [08-admin.md](./api/08-admin.md) | Painel admin, métricas, simulação |
| [09-deploy-migrations-schema.md](./api/09-deploy-migrations-schema.md) | Deploy, Alembic, schema |
| [10-referencia-rapida-endpoints.md](./api/10-referencia-rapida-endpoints.md) | Tabela consolidada |
| [11-skills.md](./api/11-skills.md) | Catálogo de skills |
| [12-modelo-conceitual.md](./api/12-modelo-conceitual.md) | Entidades e relações |

---

## Arquitetura (`docs/architecture/`)

| Documento | Conteúdo |
|-----------|----------|
| [README.md](./architecture/README.md) | Índice de arquitetura |
| [new-api-route-checklist.md](./architecture/new-api-route-checklist.md) | **Nova rota api-delpi** — HTTP, registry, perfil, CI |
| [chat-intelligence-base.md](./architecture/chat-intelligence-base.md) | **Núcleo** — pipeline, serviços, roteamento api-delpi |
| [chat-pre-llm-layers.md](./architecture/chat-pre-llm-layers.md) | Fases A/B/C antes do LLM |
| [chat-assistant-content-presentation.md](./architecture/chat-assistant-content-presentation.md) | Apresentação rica (API + contrato MFE) |
| [assistant-content-catalog.md](./architecture/assistant-content-catalog.md) | Catálogo `app/content/pt-BR/assistant/*.json` |
| [session-memory.md](./architecture/session-memory.md) | Memória, assertividade, contexto |
| [intent-routing.md](./architecture/intent-routing.md) | Roteamento de intenção (Playbook 02) |
| [product-operational-content.md](./architecture/product-operational-content.md) | Vocabulário operacional de produto |
| [vocabulary-centralization-jun2026.md](./architecture/vocabulary-centralization-jun2026.md) | Centralização de termos SQL/intent |
| [humanized-narrative-stack-jun2026.md](./architecture/humanized-narrative-stack-jun2026.md) | Narrativa humanizada pós-tool |
| [email-writing.md](./architecture/email-writing.md) | Escrita de e-mails corporativos |
| [text-correction.md](./architecture/text-correction.md) | Correção de texto e typos |
| [continuous-learning.md](./architecture/continuous-learning.md) | Aprendizado contínuo (roadmap) |
| [adr/README.md](./architecture/adr/README.md) | Architecture Decision Records |

---

## Desenvolvimento (`docs/development/`)

| Documento | Conteúdo |
|-----------|----------|
| [guia-desenvolvimento.md](./development/guia-desenvolvimento.md) | Estrutura `app/`, camadas, como estender o chat |
| [../app/content/README.md](../app/content/README.md) | Bundles JSON de textos PT-BR |
| [roadmap/playbook-11-clean-architecture-chat-api.md](./roadmap/playbook-11-clean-architecture-chat-api.md) | Clean architecture, checklist de PR |
| [roadmap/playbook-15-rotas-operacionais-sem-sql.md](./roadmap/playbook-15-rotas-operacionais-sem-sql.md) | Rotas produção/compras/perdas sem SQL (roadmap) |

---

## Conhecimento RAG (`docs/knowledge/`)

Documentos para **ingestão na base de conhecimento** — não confundir com código da API.

| Documento | Conteúdo |
|-----------|----------|
| [README.md](./knowledge/README.md) | Estrutura, sync, export de bundle |
| [api-delpi-rotas-agente.md](./knowledge/api-delpi-rotas-agente.md) | Mapa intenção → rota api-delpi |
| [chat-intelligence-settings-profiles.md](./knowledge/chat-intelligence-settings-profiles.md) | Perfis dev/prod de toggles admin |
| [domains/global/](./knowledge/domains/global/) | Normas, GPT instructions (escopo global) |
| [domains/agents/minha-delpi-chat/](./knowledge/domains/agents/minha-delpi-chat/) | Bundle exportável do agente |

---

## Roadmap e changelog

| Pasta | Índice |
|-------|--------|
| [roadmap/README.md](./roadmap/README.md) | Ondas 1–14, playbooks, admin, agentes |
| [changelog/](./changelog/) | Entregas por mês (sem índice único — ver roadmap) |

Changelogs recentes:

- [2026-06-viewintent-apresentacao-automatica.md](./changelog/2026-06-viewintent-apresentacao-automatica.md)
- [2026-06-playbook-inteligencia.md](./changelog/2026-06-playbook-inteligencia.md)
- [2026-06-playbook-14-corretor-digitacao-composer.md](./changelog/2026-06-playbook-14-corretor-digitacao-composer.md)
- [2026-05-inteligencia-chat-entregas.md](./changelog/2026-05-inteligencia-chat-entregas.md)

---

## Testes (`docs/testing/`)

| Documento | Conteúdo |
|-----------|----------|
| [README.md](./testing/README.md) | Índice de testes e smokes |
| [smoke-operacional-manual.md](./testing/smoke-operacional-manual.md) | Checklist manual (U1–U9, G1–G3, #70–79…) |
| [perguntas-teste-chat-jun2026.md](./testing/perguntas-teste-chat-jun2026.md) | Perguntas de regressão |
| [smoke-operational-intelligence-e2e.md](./testing/smoke-operational-intelligence-e2e.md) | E2E operacional |

Suíte automatizada: `tests/unit/` (pytest). Fixtures: `tests/fixtures/chat_intelligence_regression_cases.py`.

---

## Código — estrutura rápida

```text
minha-delpi-ai-api/
  app/
    interfaces/http/routes/   # Handlers Flask (finos)
    composition/              # make_* — composition root (DI)
    application/
      use_cases/              # Send, Stream, Admin…
      services/               # Orquestração de turno, RAG, tools
    domain/
      services/               # Regras de negócio e inteligência
      prompt_policies/        # Policies Markdown para o LLM
      ports/                  # Contratos ABC
    infrastructure/           # Postgres, LLM, gateways HTTP
    content/pt-BR/            # Textos PT-BR (JSON)
  migrations/                 # Alembic
  scripts/                    # Smokes, sync OpenAPI, export bundle
  tests/unit/                 # pytest
```

Detalhes: [development/guia-desenvolvimento.md](./development/guia-desenvolvimento.md).

---

## Serviços relacionados

| Serviço | Documentação |
|---------|--------------|
| Plugin UI | [../plugins/minha-delpi-chat/README.md](../plugins/minha-delpi-chat/README.md) |
| API operacional | [../api-delpi/docs/api/README.md](../api-delpi/docs/api/README.md) |
| Core API (RBAC) | [../docs/04-core-api/README.md](../docs/04-core-api/README.md) |
| Plataforma | [../docs/README.md](../docs/README.md) |

---

## Comandos úteis

```bash
# Testes unitários
pytest tests/unit -q

# Migrations (local)
flask --app app.main:app db upgrade

# Smoke identidade (container)
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/smoke_identity_rag.py <user_id> <session_id> "quem te criou?"

# Sync OpenAPI api-delpi
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/sync_api_delpi_openapi.py
```

Setup completo: [README.md](../README.md) na raiz do pacote.
