# Guia de desenvolvimento — minha-delpi-ai-api

> **Público:** desenvolvedores backend  
> **Pré-requisitos:** Python 3.12+, PostgreSQL com pgvector, stack Minha DELPI (Keycloak, Core API)

---

## 1. Setup local

### Com Docker (recomendado)

```bash
cd infra
docker compose -f docker-compose.dev.yml up -d minha-delpi-ai-api postgres-plugins ollama
```

Migrations rodam no boot do container (`docker-entrypoint.sh`).

### Sem Docker

```bash
cd minha-delpi-ai-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

set -a && source ../infra/.env && set +a
export DATABASE_URL="postgresql+psycopg://${PLUGINS_DB_USER}:${PLUGINS_DB_PASSWORD}@localhost:5433/${PLUGINS_DB_NAME}"

flask --app app.main:app db upgrade
flask --app app.main:app run --debug
```

Variáveis: `infra/.env.dev.example`, `app/infrastructure/config/settings.py`.

---

## 2. Estrutura do código

```text
app/
  interfaces/http/
    routes/
      chat_routes.py          # Facade — delega sub-rotas
      chat/
        session_routes.py     # Sessões
        message_routes.py     # Mensagens send/stream
        agent_routes.py       # Agentes
        project_routes.py     # Projetos
        attachment_routes.py  # Anexos
        meta_routes.py        # Capabilities, catalog, typing-suggestions
      admin_routes.py
      knowledge_routes.py
      tool_routes.py
      health_routes.py

  composition/
    root_composer.py          # App factory wiring
    chat_composer.py          # make_send_chat_message, make_stream_*
    admin_composer.py
    repository_composer.py
    llm_composer.py
    external_action_composer.py
    …

  application/
    use_cases/
      send_chat_message_use_case.py
      stream_chat_message_use_case.py
      execute_external_action_use_case.py
      …
    services/
      chat_turn/              # Preparação e conclusão do turno
        chat_turn_preparation_service.py
        chat_turn_completion_service.py
        chat_turn_preparation_*_service.py   # delegates
      chat_tool_context_service.py
      chat_prompt_builder_service.py
      …
    dto/                      # Request/response DTOs

  domain/
    services/                 # Regras de negócio (~150+ serviços)
    external_actions/
      presenters/             # Sub-presenters por rota/perfil
    prompt_policies/          # *.md — instruções LLM globais
    ports/                    # ABC: repos, LLM, content
    entities/                 # ChatSession, ChatMessage, …
    skills/                   # Registro de skills

  infrastructure/
    persistence/              # Postgres*Repository
    gateways/                 # LLM, web search, core-api HTTP
    content/                  # ContentService (loader JSON)
    config/settings.py

  content/pt-BR/
    assistant/                # Bundles JSON (textos PT-BR)
    labels/                   # Rótulos rotas api-delpi
    skills/
```

**Regra:** `domain` não importa `infrastructure` nem `interfaces`. Repositories só instanciados em `composition/`.

---

## 3. Fluxo de uma feature de chat

### 3.1 Pergunta: «onde coloco a regra?»

```text
1. É texto exibido ao usuário?
   → app/content/pt-BR/assistant/*.json + *ContentService
   → catálogo: docs/architecture/assistant-content-catalog.md

2. É instrução longa para o LLM (todos os chats)?
   → domain/prompt_policies/*.md + PromptPolicyService

3. É detecção de intenção / roteamento / resposta direta?
   → domain/services/*IntentService ou *DirectAnswerService
   → registrar em ChatTurnPreparationService ou pipeline

4. É execução de API externa?
   → ExternalActionSelectionService + ExecuteExternalActionUseCase
   → presenter em domain/external_actions/presenters/

5. É orquestração de turno (RAG, flags, SSE)?
   → application/services/chat_turn/

6. É novo endpoint HTTP?
   → interfaces/http/routes/ + use case + composition/make_*
```

### 3.2 Checklist de implementação

- [ ] Serviço canônico identificado (não patch no use case)
- [ ] Send **e** stream usam o mesmo serviço
- [ ] Texto PT-BR só em JSON (ou policy MD para LLM)
- [ ] Teste unitário ou caso em `chat_intelligence_regression_cases.py`
- [ ] Doc atualizada se contrato HTTP ou arquitetura mudou

### 3.3 Nova rota api-delpi exposta ao chat

Seguir **[`docs/architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md)** — resumo:

1. **api-delpi:** `api_delpi_success` + `route_contract_registry` + smoke `meta`
2. **Registry:** `operational_route_registry.json` + `generate_operational_route_registry.py --check`
3. **Apresentação:** `entityProfiles`, `entitySetProfileContracts`, `pathRules` (específica antes de catch-all)
4. **Pipeline:** `ChatPresentationMetadataPipelineService` → `viewIntent` → `presentationDecision`
5. **CI:** `audit_presentation_coverage.py --check-profiles` + teste `test_chat_presentation_view_intent_service.py`

Detalhe api-delpi: [`api-delpi/docs/`](../api/) e playbook-10 no repositório central.

---

## 4. Send vs Stream

Ambos consomem:

| Fase | Serviço |
|------|---------|
| Preparação | `ChatTurnPreparationService.prepare()` |
| Montagem LLM | `ChatTurnLlmAssemblyService` |
| Conclusão | `ChatTurnCompletionService.complete()` |

Stream adicional:

| Componente | Papel |
|------------|-------|
| `StreamChatMessageUseCase` | Orquestra SSE |
| `ChatStreamTurnPrepareService` | Prepare em thread com callbacks |
| `ChatStreamActivityService` | Eventos `activity` |
| `ChatStreamCheckpointService` | Persistência incremental |
| `chat_sse_stream_service` | Emissão SSE |

**Proibido:** copiar o mesmo `if` em send e stream — extrair para serviço base.

ADR: [docs/architecture/adr/002-send-stream-turn-parity.md](../architecture/adr/002-send-stream-turn-parity.md).

---

## 5. Composition root (DI)

Novos use cases ou serviços com dependências:

1. Implementar serviço (domain ou application)
2. Registrar factory em `composition/*_composer.py`
3. Handler HTTP chama `make_*()` — **nunca** `Postgres*Repository()` na rota

Exemplo:

```python
# interfaces/http/routes/chat/message_routes.py
from app.composition.chat_composer import make_stream_chat_message

@bp.post("/sessions/<session_id>/messages/stream")
def stream_message(session_id: str):
    use_case = make_stream_chat_message()
    return use_case.execute(...)
```

---

## 6. Conteúdo JSON

Loader: `ChatAssistantContentService` → `ContentService` (infra).

```python
# ✅ Correto
ChatAssistantContentService.get("presenter_content", "titlesByPathFragment", "/stock")

# ❌ Evitar
return {"titulo": "Estoque do produto"}
```

Adicionar chave:

1. Editar JSON em `app/content/pt-BR/assistant/`
2. Usar via serviço de domínio ou application
3. Teste: chave existe (`test_presenter_content_helpers.py` como modelo)
4. Atualizar [assistant-content-catalog.md](../architecture/assistant-content-catalog.md)

Detalhes: [app/content/README.md](../../app/content/README.md).

---

## 7. Testes

### Unitários

```bash
pytest tests/unit -q

# Escopo de um serviço
pytest tests/unit/domain/services/test_chat_simple_turn_gate_service.py -q

# Regressão de inteligência
pytest tests/unit/domain/services/test_chat_intelligence_regression.py -q
```

### Fixtures de regressão

`tests/fixtures/chat_intelligence_regression_cases.py` — casos nomeados consumidos por `test_chat_intelligence_regression.py`.

Ao adicionar regra de roteamento/intenção, inclua caso que **falha sem a regra**.

### Smokes (container)

```bash
# Identidade
python scripts/smoke_identity_rag.py <user_id> <session_id> "quem te criou?"

# GPT/SQL melhorias
python scripts/smoke_gpt_instructions_improvements.py [user_id] [session_id]

# Sync OpenAPI
python scripts/sync_api_delpi_openapi.py
```

Checklist manual: [docs/testing/smoke-operacional-manual.md](../testing/smoke-operacional-manual.md).

### Auditoria clean architecture

```bash
python scripts/audit_clean_architecture.py
pytest tests/unit/infrastructure/test_no_hardcoded_pt_strings.py -q
```

Baseline: [docs/architecture/clean-architecture-baseline.json](../architecture/clean-architecture-baseline.json).

---

## 8. Migrations

```bash
flask --app app.main:app db migrate -m "descricao"
flask --app app.main:app db upgrade
```

Arquivos em `migrations/versions/`. Doc: [docs/api/09-deploy-migrations-schema.md](../api/09-deploy-migrations-schema.md).

---

## 9. Integração api-delpi

Quando uma rota nova entra na api-delpi:

1. Deploy api-delpi
2. `scripts/sync_api_delpi_openapi.py` — reimport OpenAPI + embeddings
3. Atualizar `labels/api_paths.json` e `capabilities.json` se necessário
4. Estender `ExternalActionSelectionService` ou `api_route_domains.json`
5. Presenter em `domain/external_actions/presenters/`
6. Atualizar [api-delpi-rotas-agente.md](../knowledge/api-delpi-rotas-agente.md)
7. Caso de regressão + smoke manual

Contrato de resposta: [playbook-10](../roadmap/playbook-10-contrato-respostas-api-delpi.md).

---

## 10. Agentes e conhecimento

| Tarefa | Onde |
|--------|------|
| Criar agente | API `POST /chat/agents` ou UI builder |
| Publicar | `POST /chat/agents/{id}/publish` |
| Vincular actions | Provider OpenAPI + agente |
| Documentos RAG | `docs/knowledge/` → ingestão admin |
| Export bundle | `scripts/export_agent_knowledge_bundle.py` |

Skills: registro em `domain/skills/`, doc [api/11-skills.md](../api/11-skills.md).

---

## 11. Variáveis de ambiente (dev)

| Variável | Default dev | Notas |
|----------|-------------|-------|
| `LLM_PROVIDER` | `ollama` | `vllm` em prod |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Modelo rápido CPU |
| `CHAT_AGENTIC_LOOP_ENABLED` | `false` | Evita loops caros |
| `CHAT_WEB_SEARCH_ENABLED` | `false` | Requer provider |
| `CHAT_DOCUMENT_VISION_ENABLED` | `true` (compose) | OCR anexos |
| `CHAT_PERSIST_BEFORE_PLAYBACK` | `true` | Stream com playback |
| `RAG_CONTEXT_MIN_SCORE` | ver settings | Calibração RAG |

Perfis completos: [chat-intelligence-settings-profiles.md](../knowledge/chat-intelligence-settings-profiles.md).

---

## 12. Checklist de PR

1. Domain sem import de infra?
2. Texto novo só em JSON ou policy MD?
3. Send/stream paridade?
4. Teste ou fixture de regressão?
5. `pytest` relevante passa?
6. Doc HTTP/arquitetura atualizada se contrato mudou?

Playbook completo: [playbook-11-clean-architecture-chat-api.md](../roadmap/playbook-11-clean-architecture-chat-api.md).

Regras Cursor (repo): `.cursor/rules/clean-architecture-chat-api.mdc`, `chat-intelligence-base.mdc`, `assistant-content-json.mdc`.

---

## 13. Referências

| Doc | Conteúdo |
|-----|----------|
| [docs/README.md](../README.md) | Índice geral |
| [architecture/chat-intelligence-base.md](../architecture/chat-intelligence-base.md) | Pipeline completo |
| [api/README.md](../api/README.md) | Endpoints HTTP |
| [README.md](../../README.md) | README do pacote |
