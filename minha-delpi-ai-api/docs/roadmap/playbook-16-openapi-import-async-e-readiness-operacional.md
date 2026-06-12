# Playbook 16 — Import OpenAPI assíncrono e readiness operacional

**Status:** implementado (jun/2026) — Sprints A–D entregues; aceite operacional via homologação  
**Parent:** [`playbook-15-rotas-operacionais-sem-sql.md`](./playbook-15-rotas-operacionais-sem-sql.md)  
**Relacionado:** [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md), [`../../../api-delpi/docs/api/12-procedimento-reimport-openapi.md`](../../../api-delpi/docs/api/12-procedimento-reimport-openapi.md)

---

## 1. Problema observado (jun/2026)

### 1.1 Sintoma no chat

Pergunta: *«liste produtos programados para produzir hoje na filial 01»* com agente ativo.

| Etapa visível | Significado |
|---------------|-------------|
| «Buscando a resposta mais direta…» | `ChatOperationalPipelineService.should_optimize` = true — intent Playbook 15 reconhecida |
| «Planejando passo 1/1: consultas OpenAPI» | UI sempre emite antes de `plan_actions` — **não** prova que a rota foi selecionada |
| «Gerando resposta em linguagem natural…» | **Nenhuma** `execute_external_action` planejada → LLM responde sem dados |

### 1.2 Causa raiz (três camadas)

A rota operacional exige **três níveis** alinhados — não basta existir na api-delpi:

```text
api-delpi (GET /production/schedule/today)
    ↓ deploy + OpenAPI publicado
Catálogo global (provider api-delpi, action get_production_schedule_today)
    ↓ reimport concluído
Agente (action habilitada em allowedActionIds)
    ↓ toggle no builder
Chat runtime → select_production_operational → execute_external_action
```

| Camada | Onde verificar | Falha típica |
|--------|----------------|--------------|
| **API** | `GET /apps/api-delpi/openapi.json` contém `operationId` | Deploy api-delpi sem merge |
| **Catálogo** | Admin → Ações → «API DELPI · N rota(s)» lista `get_production_schedule_today` | Reimport não rodou ou travou |
| **Agente** | Builder → rotas → action **enabled** | Rota no catálogo global mas não ligada ao agente |

**Roteamento determinístico (Playbook 15)** usa `path_token` + `allowed_action_ids` — **não depende de embedding**. Assim que a action existir no catálogo **e** estiver permitida no agente, a seleção REST funciona.

### 1.3 Por que «Atualizar rotas» demora

Fluxo atual (`POST .../providers/{key}/import`) é **síncrono** e bloqueia até o fim:

1. Baixar `openApiUrl` (timeout 20s)
2. Parse + upsert de ~135 actions
3. **Para cada action:** `embed_action()` se `EXTERNAL_ACTION_EMBEDDING_ON_IMPORT=true` (default)

Gargalo: **N chamadas sequenciais ao serviço de embedding** dentro de uma única requisição HTTP (`PostgresExternalActionRepository.import_schema_from_json`).

Embeddings servem **fallback semântico** e tool router — **não** rotas Playbook 15 com `path_token`.

---

## 2. Objetivos das próximas implementações

| # | Objetivo | Benefício |
|---|----------|-----------|
| O1 | Import **assíncrono** com job id | UI não trava; operador pode continuar no builder |
| O2 | **Progresso** por fase (`done` / `total`) | «Cadastrando 135/135» · «Indexando 45/135» |
| O3 | **Disponibilizar rotas antes** do fim dos embeddings | Habilitar action assim que fase 2 commitar |
| O4 | **Readiness operacional** pós-import | Checklist/smoke automático: rota X no catálogo + habilitável no agente |
| O5 | **Feedback claro** quando intent bate mas action falta | Evitar LLM silencioso; mensagem PT-BR via JSON |

---

## 3. Arquitetura alvo — job de import

### 3.1 Fases do job

| Fase | `phase` | Descrição | Commit DB | Bloqueia uso da rota? |
|------|---------|-----------|-----------|------------------------|
| 1 | `fetch_schema` | GET `openApiUrl` ou schema inline | schema history | sim |
| 2 | `import_actions` | Upsert actions **sem** embedding (ou batch deferido) | actions | **não** (após commit) |
| 3 | `embed_actions` | Backfill embedding por action | embedding por linha | não (só ranking semântico) |
| 4 | `generate_catalog` | `api-delpi-openapi-catalog.md` (opcional) | arquivo | não |
| 5 | `done` / `failed` | Estado terminal | — | — |

### 3.2 Contrato HTTP (proposto)

**Iniciar import (substitui sync bloqueante ou convive em paralelo):**

```http
POST /chat/agents/{agentId}/providers/{providerKey}/import
Accept: application/json

→ 202 Accepted
{
  "jobId": "uuid",
  "status": "queued",
  "pollUrl": "/chat/providers/{providerKey}/import/jobs/{jobId}"
}
```

**Compatibilidade:** header `Prefer: respond-async` ou query `?async=true`. Sem flag → comportamento atual `200` (deprecated após migração UI).

**Consultar progresso:**

```http
GET /chat/providers/{providerKey}/import/jobs/{jobId}

→ 200
{
  "jobId": "uuid",
  "status": "running|completed|failed|cancelled",
  "phase": "embed_actions",
  "phaseLabel": "Indexando rotas para busca semântica",
  "progress": {
    "done": 45,
    "total": 135,
    "unit": "actions"
  },
  "result": {
    "actionsImported": 135,
    "embeddingsUpdated": 45,
    "schemaHash": "..."
  },
  "error": null,
  "startedAt": "...",
  "updatedAt": "..."
}
```

**SSE opcional (fase 2):** `GET .../import/jobs/{jobId}/stream` — mesmo padrão de eventos do chat (`phase`, `progress`).

### 3.3 Camadas (clean architecture)

| Peça | Camada | Responsabilidade |
|------|--------|------------------|
| `ExternalActionImportJobService` | application | Orquestra fases, persiste progresso, thread + `app.app_context` |
| `ExternalActionImportJobRepository` | infrastructure | Tabela `ai_external_action_import_jobs` ou Redis TTL |
| `ImportExternalActionsSchemaUseCase` | application | Mantém `execute_from_json/url`; aceita flag `skipEmbedding` |
| `ReindexExternalActionEmbeddingsUseCase` | application | Estender com callback `on_progress(done, total)` |
| Handler import | interfaces/http | `202` + enqueue; GET job |
| Textos fase/progresso | `assistant/agent_actions.json` | **Proibido** string PT no Python |
| UI | `ChatAgentActionsPage.tsx` | Poll 1–2s, barra + fase; desbloqueia lista após fase 2 |

**Referência de padrão async existente:** `ChatAttachmentIndexSchedulerService` (thread daemon + Flask context).

### 3.4 Configuração

| Variável | Default proposto | Efeito |
|----------|------------------|--------|
| `EXTERNAL_ACTION_EMBEDDING_ON_IMPORT` | `false` quando async ligado | Import rápido; embeddings só na fase 3 |
| `EXTERNAL_ACTION_IMPORT_ASYNC_ENABLED` | `true` | UI usa job async |
| `EXTERNAL_ACTION_IMPORT_EMBED_BATCH_SIZE` | `8` | Paralelismo controlado na fase 3 |

---

## 4. UI — builder de actions

### 4.1 Estado atual (pós-implementação)

- Botão «Atualizar rotas» → `POST import?async=true` → poll `GET import/jobs/{id}`
- Barra de progresso + fase (`phaseLabel` da API)
- Badge «Indexação: done/total» no provider enquanto `phase=embed_actions` (`GET import/jobs/latest`)
- Import síncrono (`200`) mantido sem `async=true` (API/CLI legado)

### 4.2 Comportamento alvo

1. Click → `POST import?async=true` → recebe `jobId`
2. Barra de progresso + texto de fase (de `phaseLabel` ou chave JSON)
3. Ao `phase=import_actions` com `done=total` → **reload rotas** (lista já utilizável)
4. Embeddings continuam em background; badge «Indexação: 45/135» no provider
5. Erro → toast + detalhe `error`; job `failed` consultável

### 4.3 Arquivos MFE

| Arquivo | Mudança |
|---------|---------|
| `plugins/minha-delpi-chat/src/data/api/chatApi.ts` | `startImportJob`, `getImportJob` |
| `ChatAgentActionsPage.tsx` | Poll, progress UI, reload incremental |
| `ActionRoutesSection.tsx` | Empty state: «Rota ainda não importada — use Atualizar rotas» |
| Testes | mock poll + estados `running`/`completed` |

---

## 5. Readiness operacional (pós-deploy)

Checklist automatizável após reimport — estender `scripts/sync_api_delpi_openapi.py` e smoke Playbook 15.

### 5.1 Verificações

| ID | Verificação | Comando / assert |
|----|-------------|------------------|
| R1 | OpenAPI contém operationId | `jq '.paths...' openapi.json` |
| R2 | Action no Postgres | `list_actions(provider_key=api-delpi)` contém path |
| R3 | Seleção determinística | `ExternalActionSelectionService.select_action(mensagem, allowed=[actionId])` |
| R4 | Agente produção | Smoke S4 «programados hoje» com agente padrão |

### 5.2 Matriz Playbook 15 — actions críticas

| operationId | path | Caso regressão |
|-------------|------|----------------|
| `get_production_schedule_today` | `/production/schedule/today` | PO / S4 |
| `get_production_orders_open` | `/production/orders/open` | PO05 / S5 |
| `get_production_consumption_top_items` | `/production/consumption/top-items` | S1 |
| `get_purchases_top_products` | `/purchases/top-products` | S2 |

Script proposto: `scripts/check_operational_action_readiness.py` — exit 1 lista actions ausentes.

### 5.3 Procedimento pós-deploy (atualizado)

1. Deploy api-delpi  
2. `./scripts/homologacao/sync-api-delpi-openapi.sh` (ou job async na UI)  
3. `check_operational_action_readiness.py`  
4. Builder: confirmar actions críticas **enabled** no Agente Minha DELPI  
5. Smoke S1–S4  

---

## 6. Melhoria pipeline — intent sem action (O5)

**Problema:** `ChatProductionOperationalIntentService.matches_rest_route` = true, mas `select_production_operational` retorna `None` → `plan_actions` vazio → LLM.

**Comportamento alvo:**

| Condição | Ação |
|----------|------|
| Intent REST + action ausente no catálogo | Direct answer: «Rota ainda não importada no provider api-delpi…» (`turn_preparation.json`) |
| Intent REST + action no catálogo mas **não** em `allowedActionIds` | Direct answer: «Habilite a action X no agente…» |
| Intent REST + action permitida | Fluxo normal `execute_external_action` |

**Módulo canônico:** `ChatOperationalParameterService` ou delegate em `ExternalActionSelectionDispatchService` — **não** patch no MFE.

**Não reativar SQL** quando `matches_rest_route` — Playbook 15 §3 desambiguação mantida.

---

## 7. Ordem de implementação (sprints)

### Sprint A — Quick win (sem job table)

- [x] Default `EXTERNAL_ACTION_EMBEDDING_ON_IMPORT=false` (bootstrap `.env`; admin pode ligar `externalActionEmbeddingOnImport`)
- [x] `scripts/check_operational_action_readiness.py` — 4 actions críticas Playbook 15
- [x] O5 parcial: direct answer quando intent REST sem action (`turn_preparation.json` + `ChatProductionOperationalActionReadinessService`)
- [x] Documentar no builder: «Rotas disponíveis após import; indexação semântica em background»

### Sprint B — Job async + progresso API

- [x] Modelo/tabela job + `ExternalActionImportJobService`
- [x] `POST import?async=true` → `202`
- [x] `GET import/jobs/{id}` com `progress`
- [x] Refatorar `import_schema_from_json`: fase 2 sem embed; fase 3 com callback
- [x] Testes unitários job + import split

### Sprint C — UI progresso

- [x] `chatApi.ts` + poll
- [x] Barra e fases no `ChatAgentActionsPage`
- [x] Reload rotas ao completar fase 2
- [x] Testes MFE

### Sprint D — Readiness + mensagens operador (O5)

- [x] Direct answer quando action missing (`turn_preparation.json`)
- [x] Regressão unitária: `test_chat_production_operational_action_readiness_service.py`
- [x] Smoke S4 no playbook de homologação (`scripts/homologacao/check-playbook16-operational-readiness.sh`)

---

## 8. Testes de regressão

| Área | Arquivo / caso |
|------|----------------|
| Import split | `test_postgres_external_action_repository_import.py` — embed deferido |
| Job progress | `test_external_action_import_job_service.py` |
| HTTP 202/GET | `test_agent_provider_import_routes.py` |
| Seleção schedule + filial | `test_external_action_selection_service.py` — mensagem com filial 01 |
| Readiness script | `test_check_operational_action_readiness.py` |
| UI poll | `ChatAgentActionsPage.test.tsx` ou integração API mock |

Fixture sugerida em `production_operational_regression_cases.py`:

```python
_operational_route_case(
    "PO15",
    "liste produtos programados para produzir hoje na filial 01",
    action_id="...get_production_schedule_today",
    path="/production/schedule/today",
    operation_id="get_production_schedule_today",
    parameters=["reference_date", "branch", "limit"],
)
```

---

## 9. Checklist de aceite (Playbook 16)

- [x] Import 135 rotas: UI responde em &lt; 5s (fase 2 commitada) — validar após reimport no ambiente
- [x] Progresso visível: `done/total` durante embeddings (UI + `GET import/jobs/latest`)
- [x] `get_production_schedule_today` selecionável **antes** do fim da fase 3 (seleção REST não usa embedding)
- [x] Pós-deploy: readiness — `sync-api-delpi-openapi.sh` passo 5 + `check-playbook16-operational-readiness.sh`
- [x] Intent REST sem action → direct answer O5 (`ChatProductionOperationalActionReadinessService`)
- [x] Textos PT só em `assistant/*.json` (`importJob.phaseLabels`, `turn_preparation.json`)
- [x] Procedimento §12 api-delpi e §04 actions-openapi linkam este playbook

---

## 10. Referências

| Doc | Conteúdo |
|-----|----------|
| [playbook-15-rotas-operacionais-sem-sql.md](./playbook-15-rotas-operacionais-sem-sql.md) | Rotas R01–R16 |
| [playbook-15-chat-integracao-producao-suprimentos.md](./playbook-15-chat-integracao-producao-suprimentos.md) | Intent + seleção |
| [12-procedimento-reimport-openapi.md](../../../api-delpi/docs/api/12-procedimento-reimport-openapi.md) | Job pós-deploy |
| [04-actions-openapi.md](../api/04-actions-openapi.md) | Contrato providers/actions |
| [chat-intelligence-base.md](../architecture/chat-intelligence-base.md) | Pipeline e fast path |
| `scripts/sync_api_delpi_openapi.py` | Sync CLI atual |
| `scripts/homologacao/sync-api-delpi-openapi.sh` | Automação homolog/prod |

---

## 11. Resumo executivo

O Playbook 15 entregou **roteamento determinístico**; o gargalo operacional passou a ser **cadastro e habilitação da action**, não inferência SQL. Import síncrono com embedding bloqueante atrasa esse cadastro e mascara o progresso na UI.

**Próximo passo operacional:** reimport no ambiente (`Atualizar rotas` ou `sync-api-delpi-openapi.sh`), habilitar actions críticas no agente e rodar `check-playbook16-operational-readiness.sh`.
