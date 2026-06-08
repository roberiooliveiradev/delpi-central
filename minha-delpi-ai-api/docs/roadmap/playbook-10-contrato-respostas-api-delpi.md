# Playbook 10 — Contrato de respostas api-delpi para IA

Projeto: Plataforma DELPI (api-delpi + consumidores HTTP)  
Escopo: padronizar o JSON retornado pela api-delpi para **IA**, **plugins MFE**, **strategic-indicators-api** e demais integrações — com **compatibilidade retroativa** explícita.

> **Princípios:**  
> 1. A api-delpi **declara** o que devolve (`data` + `meta` opcional).  
> 2. O chat base **interpreta** e **apresenta** (não duplicar UI na API).  
> 3. **Nenhuma mudança quebra** consumidores existentes sem período de transição (`dataVersion`, `?legacy=true`, campos aditivos).

Relacionado: [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md), [`../architecture/chat-assistant-content-presentation.md`](../architecture/chat-assistant-content-presentation.md), [`playbook-09-apresentacao-rica.md`](./playbook-09-apresentacao-rica.md), [`../../../api-delpi/docs/api/11-guia-agente-chat.md`](../../../api-delpi/docs/api/11-guia-agente-chat.md).

**Última revisão:** jun/2026

---

## 1. Objetivo

Melhorar a compreensão das respostas da api-delpi por:

- pipeline de **seleção de actions** (OpenAPI + RAG);
- **presenter** do chat (`ExternalActionResultPresenter`);
- **LLM** (resumo humanizado, sem JSON bruto);
- **usuário** (tabelas, árvores, gráficos no MFE).

Hoje o agente sabe *qual rota* chamar, mas adivinha *o shape* de `data`. Este playbook define o contrato alvo e o roadmap de implementação.

---

## 2. Estado atual (baseline)

### 2.1 api-delpi

| Aspecto | Situação |
|---------|----------|
| Envelope | `{ success, message, data }` na maioria das rotas |
| OpenAPI | Paths e params documentados; **`data` opaco** (sem `response_model`) |
| Metadados de agente | `openapi_agent_metadata.py` em ~20 operações chat-critical |
| Serialização | Mista: `to_dict()`, dict cru, `Page`, árvores recursivas |
| Erros | 404 FastAPI (`detail`) vs envelope `success: false` |
| Domínio Protheus | `SIM`/`NAO`, datas `YYYYMMDD`, status em PT |
| Rotas pesadas | `/analyser` agrega product + structure + guide + inspection |

Arquivos de referência:

- `api-delpi/app/core/responses.py`
- `api-delpi/app/interface/http/openapi_agent_metadata.py`
- `api-delpi/app/interface/http/routes/product_routes.py`
- `api-delpi/docs/api/00-visao-geral.md`, `11-guia-agente-chat.md`

### 2.2 Chat IA (minha-delpi-ai-api)

```text
HTTP → sanitize_response → ExternalActionResultPresenter
                              ├─ present() → humanizedSummary (LLM)
                              └─ build_*_presentation() → toolCalls.metadata (MFE)
       → ChatPresentationDecisionService → presentationDecision
       → MFE ChatAssistantContent
```

| Consumidor | Recebe hoje |
|------------|-------------|
| **MFE** | `presentation`, `tablePresentation`, `treePresentation`, `chartPresentation`, `textPresentation` |
| **LLM** | `humanizedSummary` (título + linhas) — **não** recebe rows/nodes completos |
| **Seleção de rota** | `path`, `summary`, `description`, `operationId` (quando definido) |

Arquivos de referência:

- `minha-delpi-ai-api/app/application/use_cases/execute_external_action_use_case.py`
- `minha-delpi-ai-api/app/domain/services/external_actions/external_action_result_presenter.py`
- `minha-delpi-ai-api/app/application/services/external_actions/external_action_selection_service.py`
- `minha-delpi-ai-api/app/content/pt-BR/assistant/column_labels.json`

### 2.3 Consumidores HTTP (além do chat)

A api-delpi é **API compartilhada**. Mudanças no envelope ou em `data` impactam todos os clientes abaixo.

| Consumidor | Como chama | Como parseia hoje | Rotas típicas |
|------------|------------|-------------------|---------------|
| **strategic-indicators-api** | HTTP interno (`DELPI_API_URL`) | `shared/delpi_api_client` — extrai `body["data"]` se existir | `/financial/*`, `/commercial/*`, `/production/*`, `/supplies/*`, `/quality/*`, `/engineering/lmps/*` |
| **Plugins MFE — dashboards** | Gateway `/apps/api-delpi/...` | `ApiSuccessResponse<T>` → `response.data` | Ver tabela abaixo |
| **Plugins MFE — operacionais** | Idem | `fetch` + envelope | `/scheduling`, `/quality/audit-5s`, `/production` (eficiência) |
| **Portal (shell)** | Gateway | `delpiApi.ts` — envelope + `data` | `/health`, `/products`, `/system/status` |
| **minha-delpi-ai-api** | Actions OpenAPI + bearer do usuário | `_unwrap_data` + presenter | `/products/*`, KPIs, SQL `/data/sql` |
| **plugin strategic-indicators** | **Não** chama api-delpi no browser | Consome `strategic-indicators-api` | Indireto via SI backend |
| **plugin minha-delpi-chat** | **Não** chama api-delpi no browser | Consome `minha-delpi-ai-api` | Indireto via actions |
| **plugin transformometro** | Sem integração direta hoje | — | — |

#### Plugins frontend que consomem api-delpi **diretamente** (HTTP no browser)

| Plugin | Arquivo API | Prefixo gateway |
|--------|-------------|-----------------|
| `dashboard-supplies` | `src/api/suppliesApi.ts` | `/apps/api-delpi/supplies` |
| `dashboard-commercial` | `src/api/commercialApi.ts` | `/apps/api-delpi/commercial` |
| `dashboard-production` | `src/api/productionApi.ts` | `/apps/api-delpi/production` |
| `dashboard-quality` | `src/api/qualityApi.ts` | `/apps/api-delpi/quality` |
| `dashboard-financial` | `src/api/financialApi.ts` | `/apps/api-delpi/financial` |
| `dashboard-engineering` | `src/api/engineeringApi.ts` | `/apps/api-delpi/engineering` |
| `dashboard-hr` | `src/api/hrApi.ts` | `/apps/api-delpi/hr` |
| `dashboard-lmps` | `src/api/lmpApi.ts` | `/apps/api-delpi/engineering/lmps` |
| `dashboard-delpi` | `src/data/delpiApi.ts` | `/apps/api-delpi/products` |
| `central-agendamento` | `src/constants/scheduling.ts` | `/apps/api-delpi/scheduling` |
| `auditoria-5s` | `src/constants/audit5s.ts` | `/apps/api-delpi/quality/audit-5s` (+ Socket.IO no mesmo host) |
| `eficiencia-fabril` | `src/api/eficienciaFabrilApi.ts` | `/apps/api-delpi/production` |

Todos seguem o mesmo padrão: `success` / `message` / `data` — tipos em `src/types/api.ts` ou inline (`ApiSuccessResponse<T>`).

**Padrão dominante nos MFEs** (`plugins/dashboard-*/src/types/api.ts`):

```typescript
type ApiSuccessResponse<T> = {
  success: boolean;
  message?: string;
  data: T;
};
// Uso: return response.data;
```

**Padrão no SI** (`shared/delpi_api_client/client.py`):

```python
body = resp.json()
if isinstance(body, dict) and "data" in body:
    return body["data"]
return body
```

**Implicação:** campos novos no **root** (`meta`, `error`) são **aditivos** — consumidores que só leem `success`/`message`/`data` **não quebram**. Mudanças **dentro de `data`** (renomear, remover, mudar tipo) exigem migração coordenada.

Arquivos de referência:

- `shared/delpi_api_client/client.py`
- `plugins/dashboard-supplies/src/api/suppliesApi.ts` (padrão replicado em commercial, production, quality, …)
- `strategic-indicators-api/si_app/infrastructure/gateways/delpi_*_gateway.py`
- `infra/docker-compose.dev.yml` (`DELPI_API_URL`, `API_DELPI_BASE_URL`)

---

## 3. Problemas que o contrato deve resolver

| # | Problema | Impacto |
|---|----------|---------|
| P1 | OpenAPI sem schema de resposta | RAG e reimport não sabem parsear `data` |
| P2 | `operationId` ausente em rotas usadas pelo chat | IDs instáveis; embeddings desalinhados |
| P3 | Envelope/erro inconsistente | Retry e mensagens ao usuário falham |
| P4 | Paginação implícita (omitir `page` = dump full) | Estouro de contexto no `/structure`, `/parents` |
| P5 | Valores Protheus crus no JSON | Presenter precisa de heurísticas por rota |
| P6 | `/analyser` monolítico | Uma action traz 4 domínios sem `meta.sections` |
| P7 | Rotas semanticamente próximas (`inspection` vs `shipping-status`) | Seleção correta, interpretação errada |
| P8 | Falha lógica dentro de `200` (ex.: pricing) | Agente trata como sucesso |
| P9 | Presenter acoplado a `path` string | Cada rota nova = if no chat base |
| P10 | Mudança em `data` sem inventário de consumidores | Dashboards e SI quebram em produção |
| P11 | 404 `detail` vs envelope | MFEs e `DelpiApiClient` tratam erro de forma diferente |

---

## 4. Arquitetura alvo

### 4.1 Divisão de responsabilidades

| Camada | Responsabilidade | Não faz |
|--------|------------------|---------|
| **api-delpi** | Dados ERP, envelope, `meta` semântico, schemas OpenAPI, normalização de domínio | Tabela/árvore/gráfico para UI |
| **Chat base** | Presenter, decisão de formato, compactação narrativa, políticas | SQL Protheus, regras de negócio ERP |
| **Agente** | Filtrar actions/skills, prompt de identidade | Layout de apresentação |
| **MFE** | Renderizar `toolCalls.metadata` | Chamar api-delpi direto |

### 4.2 Envelope alvo

```json
{
  "success": true,
  "message": "Estoque do produto carregado com sucesso",
  "data": { },
  "error": null,
  "meta": {
    "dataVersion": "2026-06",
    "operationId": "get_product_stock",
    "entity": "product_stock",
    "shape": "paged_list",
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total": 12,
      "total_pages": 1
    },
    "fields": {
      "available_quantity": "Saldo disponível (atual - empenhado - reservado)"
    },
    "relatedRoutes": {
      "summary": "/products/{code}/summary",
      "fullAnalysis": "/products/{code}/analyser"
    }
  }
}
```

Erro padronizado:

```json
{
  "success": false,
  "message": "Produto 99999999 não encontrado",
  "data": null,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "recoverable": true
  },
  "meta": {
    "operationId": "get_product_detail",
    "entity": "product"
  }
}
```

### 4.3 Perfis de resposta (`meta.shape`)

| Perfil | `entity` (ex.) | Rotas típicas | `data` esperado |
|--------|----------------|---------------|-----------------|
| `paged_list` | `product_stock`, `product_search` | `/stock`, `/search`, guide paginado | `items[]` + totais |
| `hierarchy` | `product_structure`, `product_parents` | `/structure`, `/parents` | `root` + `items[]` recursivos |
| `product_snapshot` | `product` | `/{code}`, `/summary` | `product` + blocos opcionais |
| `composite_analysis` | `product_analyser` | `/analyser`, `/factory-status` | seções nomeadas |
| `playbook_report` | `production_status`, `shipping_status` | playbooks fabril | `product` + `items` + `summary` |
| `scalar` | `product_pricing` | `/pricing` | objeto único ou lista curta |

O presenter do chat passa a priorizar `meta.entity` / `meta.shape` em vez de apenas `path`.

### 4.4 Política de compatibilidade (obrigatória)

Toda fase do roadmap obedece esta matriz:

| Tipo de mudança | Permitido sem coordenação? | Exemplo |
|-----------------|----------------------------|---------|
| Campo **novo** em `meta` ou `error` (root) | Sim | `meta.shape`, `error.code` |
| Campo **novo opcional** em `data` | Sim | `reference_date_iso` ao lado de `reference_date` |
| Campo **renomeado** em `data` | Não — período de transição | `warehouse` → `location` (manter alias) |
| Campo **removido** de `data` | Não — `dataVersion` bump + deprecação | remover `SIM`/`NAO` string |
| Mudança de **tipo** em `data` | Não — campo paralelo ou `?legacy=true` | `"SIM"` → `true` |
| Default de query alterado | Não — opt-in explícito | `/analyser` default `summary` só com `?view=` documentado |
| Status HTTP de erro | Coordenar SI + MFEs | 404 envelope vs `detail` |

**Regras de ouro:**

1. **`data` é o contrato dos consumidores legados** — plugins e SI dependem dos shapes atuais.
2. **`meta` é o contrato novo** — IA e ferramentas novas; ignorado por clientes antigos.
3. **`?legacy=true`** (ou header `X-Delpi-Api-Legacy: 1`) durante Fase 5+ para respostas no formato antigo quando houver normalização.
4. **Matriz rota × consumidor** atualizada na Fase 0 antes de qualquer breaking change.
5. **Gate de release:** nenhuma fase fecha sem smoke dos consumidores listados em § 4.5.

### 4.5 Adaptação por consumidor

| Consumidor | O que ajustar nas fases | O que **não** precisa mudar cedo |
|------------|-------------------------|----------------------------------|
| **Plugins MFE** | Fase 2: tratar `error.code` no `httpClient` (opcional). Fase 5: tipos TS se novos campos em `data`. Tipar `meta?` em `ApiSuccessResponse`. | Leitura de `response.data` permanece |
| **strategic-indicators-api** | Fase 2: `DelpiApiClient` parsear envelope de erro unificado. Fase 5: gateways se campos normalizados forem adotados no snapshot. | `_get()` que retorna só `data` |
| **shared/delpi_api_client** | Evoluir para `get_envelope()` → `{data, meta, error}`; manter métodos atuais como wrapper | Assinaturas existentes |
| **minha-delpi-ai-api** | Fases 3–7: presenter por `meta`; reimport OpenAPI | Actions continuam funcionando com fallback por `path` |
| **Gateway nginx** | Nenhuma mudança de contrato | Proxy transparente |

**Smoke obrigatório por release (api-delpi):**

- [ ] `npm run build` em `dashboard-supplies`, `dashboard-commercial`, `dashboard-production` (amostra MFE).
- [ ] Snapshot SI em dev (`SI_MEASUREMENTS_BACKEND=api_delpi_http`) — sem aumento de `measurement_errors`.
- [ ] Turno de chat com produto real autorizado (tabela + árvore + lousa).
- [ ] `pytest api-delpi/tests/` + testes de gateway SI se alterou rota compartilhada.

---

## 5. Roadmap

### Visão geral

```text
Fase 0 ─ Documentação e inventário (baseline)
Fase 1 ─ operationId + guia agente completo
Fase 2 ─ Envelope e erros unificados
Fase 3 ─ meta semântico nas rotas chat-critical
Fase 4 ─ OpenAPI response_model + examples
Fase 5 ─ Normalização de domínio Protheus
Fase 6 ─ Views leves (summary) e custo de payload
Fase 7 ─ Presenter por perfil + testes de contrato no chat
```

| Fase | Pacote principal | Esforço | Impacto IA | Impacto outros consumidores |
|------|------------------|---------|------------|----------------------------|
| 0 | docs | Baixo | Alinhamento | Inventário rota × cliente |
| 1 | api-delpi | Baixo | Seleção estável | Nenhum (só OpenAPI metadata) |
| 2 | api-delpi + clientes | Baixo | Erros confiáveis | SI + MFEs: handler de erro envelope |
| 3 | api-delpi | Médio | Parser genérico | Nenhum (`meta` aditivo) |
| 4 | api-delpi | Médio | RAG + reimport | Nenhum (schemas documentais) |
| 5 | api-delpi + MFE/SI | Médio | Menos heurística | **Coordenado** — `?legacy=true` |
| 6 | api-delpi + chat | Médio | Menos tokens | Opt-in `?view=` — default não muda sem aviso |
| 7 | minha-delpi-ai-api | Médio | Regressão segura | Nenhum |

---

### Fase 0 — Inventário e baseline

**Objetivo:** Congelar o estado atual e definir rotas prioritárias.

**Entregas:**

- [x] Matriz rota × `operationId` × `meta.shape` proposto (produtos + suprimentos + engenharia usados no chat).
- [x] **Matriz rota × consumidor** (SI, cada dashboard, chat, portal) — quem parseia qual path.
- [x] Fixtures JSON em `minha-delpi-ai-api/tests/fixtures/api_delpi_responses/` (8 arquivos + loader + testes).
- [x] Checklist de rotas **sem** `agent_route()` (produtos NF + engenharia LMP/transforma).

**Documento:** [`api-delpi/docs/roadmaps/fase-0-inventario-contrato-respostas.md`](../../../api-delpi/docs/roadmaps/fase-0-inventario-contrato-respostas.md)

**Critério de aceite:** Documento de inventário linkado neste playbook; ≥ 8 fixtures versionadas; matriz de consumidores revisada pelo time de plugins/SI.

**Dono sugerido:** Chat base + api-delpi.

---

### Fase 1 — Metadados de agente completos

**Objetivo:** Toda rota usada pelo chat com `summary`, `description`, `operationId` estável.

**Entregas (api-delpi):**

- [x] `agent_route()` em: `parents`, `guide`, `inspection`, `pricing`, `/{code}`, `/{code}/summary`, `suppliers`, `customers`, `billing`, `internal-movements`, NF entrada/saída, engenharia LMP/transforma.
- [x] Atualizar `docs/api/11-guia-agente-chat.md` e `minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md`.
- [x] Procedimento de reimport: [`api-delpi/docs/api/12-procedimento-reimport-openapi.md`](../../../api-delpi/docs/api/12-procedimento-reimport-openapi.md).

**Critério de aceite:** Nenhuma rota da tabela «Produtos» do guia 11 sem `operationId` explícito; teste de smoke no OpenAPI exportado.

**Dependências:** Fase 0.

---

### Fase 2 — Envelope e erros unificados

**Objetivo:** Um único padrão de sucesso/falha; 404 não usa `detail` solto.

**Entregas (api-delpi):**

- [x] `error_response` estendido com `error: { code, recoverable }`.
- [x] Handler FastAPI 404/422 mapeado para envelope; exceções em `00-visao-geral.md`.
- [x] Pricing: falha lógica do use case → envelope 404 `PRODUCT_PRICING_NOT_FOUND` + teste.
- [x] `success_response` aceita `meta` opcional.

**Entregas (consumidores):**

- [x] `DelpiApiClient.parse_envelope()` + `format_error_message` em `shared/delpi_api_client/envelope.py`.
- [x] `httpClient.ts` dos dashboards (9 MFEs) + `central-agendamento`: `error.code` na mensagem.
- [x] Exceções remanescentes documentadas em `00-visao-geral.md`.

**Critério de aceite:** Testes HTTP para 200/404/400 com mesmo shape; guia 00 atualizado; SI snapshot em dev sem regressão; um dashboard smoke (supplies CPV).

**Dependências:** Fase 1.

---

### Fase 3 — Bloco `meta` semântico (rotas chat-critical)

**Objetivo:** Respostas auto-descritivas sem mudar o SQL.

**Entregas (api-delpi):**

- [x] `ResponseMetaBuilder` em `api-delpi/app/application/services/response_meta_builder.py`.
- [x] Aplicar em: `get_product_stock`, `get_product_structure`, `get_product_analyser`, `get_product_factory_status`, `search_products`, `get_product_summary`, `get_product_detail`.
- [x] `dataVersion: "2026-06"` fixo até breaking change.

**Entregas (chat — adaptação mínima):**

- [x] `apiDelpiResponseMeta` em `execution_metadata` quando envelope traz `meta`.
- [x] Teste unitário de extração de `meta` no `ExecuteExternalActionUseCase`.

**Critério de aceite:** Cada rota acima retorna `meta.shape` coerente; fixture + teste de integração no gateway.

**Dependências:** Fase 2.

---

### Fase 4 — OpenAPI `response_model` + examples

**Objetivo:** `openapi.json` descreve `data` e exemplos reais.

**Entregas (api-delpi):**

- [x] Pydantic models por perfil: `PagedListResponse`, `HierarchyResponse`, `ProductSnapshotResponse`, `CompositeAnalysisResponse`, `PlaybookReportResponse`.
- [x] `response_model` nas rotas da Fase 3.
- [x] `openapi_extra` com `examples` em stock, structure, factory-status.
- [x] `custom_openapi()` preserva examples (se necessário).

**Entregas (chat):**

- [x] Reimport do provider `api_delpi` em ambiente dev documentado no playbook.
- [x] `responseSchema` do OpenAPI alimenta `ExternalActionColumnLabelService` onde couber.

**Critério de aceite:** `openapi.json` contém schemas não vazios para ≥ 6 operações; diff de reimport não quebra actions existentes.

**Dependências:** Fase 3.

---

### Fase 5 — Normalização de domínio na origem

**Objetivo:** Reduzir heurísticas Protheus no presenter.

**Entregas (api-delpi):**

- [ ] Booleanos: `exclusive_raw_material: true` + `exclusive_raw_material_label: "Sim"` (manter legado opcional por query `?legacy=true` durante transição).
- [ ] Datas ISO 8601 em campos novos (`reference_date_iso`); manter `YYYYMMDD` em `*_raw` se necessário.
- [ ] Alinhar nomes: `warehouse` ↔ query `location` (deprecar um com alias documentado).
- [ ] `GET /products/{code}?view=summary` — subset de campos (~15) vs cadastro completo.

**Entregas (consumidores — obrigatório nesta fase):**

- [ ] Query `?legacy=true` (default `false`) devolve campos antigos (`SIM`/`NAO`, `YYYYMMDD`) onde houver normalização.
- [ ] Atualizar tipos TS dos dashboards **somente** se adotarem campos novos; senão continuam ignorando.
- [ ] Gateways SI: ler campos novos com fallback para legado (`exclusive_raw_material` bool OU string).
- [ ] CHANGELOG api-delpi com tabela «campo antigo → campo novo → data de remoção».

**Critério de aceite:** Testes de use case com asserts em tipos normalizados; guia 02-produtos atualizado; **smoke SI + 3 dashboards** com e sem `legacy=true`.

**Dependências:** Fase 4 (schemas refletem tipos novos).

---

### Fase 6 — Views leves e custo de payload

**Objetivo:** IA e chat não precisam de `/analyser` full por padrão.

**Entregas (api-delpi):**

- [ ] `GET /products/{code}/analyser?view=summary|full` — **default permanece `full`** até comunicado; `summary` opt-in (não quebra consumidores que esperam payload completo).
- [ ] `meta.sections[]` em composite: `{ key, label, itemCount, truncated }`.
- [ ] Documentar em `11-guia-agente-chat.md`: quando usar granular vs analyser vs factory-status.

**Entregas (chat):**

- [ ] `ExternalActionSelectionService` prefere rotas granulares quando intent é pontual (estoque, estrutura).
- [ ] `ChatDataCoverageNoticeService` lê `meta.sections` quando existir.

**Critério de aceite:** `view=summary` &lt; 30% do tamanho de `full` em fixture de produto; seleção não chama `full` sem intent explícito.

**Dependências:** Fase 3.

---

### Fase 7 — Presenter por perfil + regressão

**Objetivo:** Chat base consome contrato; menos `if path`.

**Entregas (minha-delpi-ai-api):**

- [ ] `ChatApiDelpiResponseProfileService` — mapa `meta.entity` → handler de `present()` / `build_presentation()`.
- [ ] Migrar rotas `/structure`, `/stock`, `/analyser`, `/factory-status` para perfil primeiro; manter fallback por `path`.
- [ ] `humanizedSummary` enriquecido com `meta.fields` quando útil.
- [ ] Testes: `tests/fixtures/api_delpi_responses/` × presenter × regressão em `tests/fixtures/chat_intelligence_regression_cases.py`.

**Critério de aceite:** ≥ 80% das rotas chat-critical roteadas por perfil; suite verde; nenhuma regressão em apresentação multi-rota produto.

**Dependências:** Fases 3–6 (meta estável).

---

## 6. O que NÃO fazer

- Não gerar `presentation` (table/tree/chart) na api-delpi.
- Não enviar JSON bruto completo ao LLM no prompt principal.
- Não duplicar regras de layout no prompt de agente.
- Não criar um envelope diferente por módulo (financeiro, qualidade, etc.) — estender o mesmo `meta`.
- Não remover campos legados sem `dataVersion` bump + período de transição.
- Não alterar default de paginação ou `view` sem opt-in — plugins e scripts podem depender do dump completo.
- Não mudar paths HTTP nem prefixos `/apps/api-delpi` (gateway e MFEs hardcoded).

---

## 7. Testes e validação

| Tipo | Onde | Quando |
|------|------|--------|
| Contrato HTTP | `api-delpi/tests/` | Cada fase api-delpi |
| Fixture JSON | `minha-delpi-ai-api/tests/fixtures/api_delpi_responses/` | Fase 0+ |
| Cliente compartilhado | `shared/delpi_api_client/` (+ testes se existirem) | Fase 2+ |
| Snapshot SI | `strategic-indicators-api/tests/` ou smoke manual | Fase 2, 5 |
| Build MFE | `plugins/dashboard-*` | Fase 2, 5 |
| Presenter unitário | `test_external_action_result_presenter*.py` | Fase 7 |
| Regressão chat | `chat_intelligence_regression_cases.py` | Fase 7 |
| E2E manual | Pergunta produto → tabela/árvore/lousa | Release |

**Smoke manual sugerido (código real do ambiente, não das fixtures):**

1. «Qual o estoque do {código}?» → tabela stock; `meta.shape=paged_list`.
2. «Estrutura do {código}» → árvore; blocos na lousa.
3. «Informações completas» → analyser summary; sem estouro de tokens.
4. Reimport OpenAPI → mesma actionId; chat responde igual.

---

## 8. Cronograma sugerido (indicativo)

| Sprint | Fases | Foco |
|--------|-------|------|
| S1 | 0 + 1 | Inventário (incl. consumidores) + operationId |
| S2 | 2 + 3 (stock, structure) | Envelope + meta piloto + DelpiApiClient |
| S3 | 3 (analyser, factory) + 4 parcial | OpenAPI examples |
| S4 | 5 + smoke SI/MFE | Normalização com `legacy` + CHANGELOG |
| S5 | 6 + 7 | Views opt-in + presenter por perfil |

Ajustar conforme capacidade. **Fases 1–3 são aditivas** — plugins e SI seguem funcionando sem deploy coordenado. **Fase 5 exige janela de migração** com todos os consumidores da matriz § 4.5.

---

## 9. Referências

| Documento | Conteúdo |
|-----------|----------|
| [`api-delpi/docs/api/11-guia-agente-chat.md`](../../../api-delpi/docs/api/11-guia-agente-chat.md) | Seleção de rotas |
| [`api-delpi/docs/api/00-visao-geral.md`](../../../api-delpi/docs/api/00-visao-geral.md) | Envelope e convenções |
| [`api-delpi/docs/api/02-produtos.md`](../../../api-delpi/docs/api/02-produtos.md) | Rotas de produto |
| [`api-delpi/docs/roadmaps/`](../../../api-delpi/docs/roadmaps/) | Playbooks SQL fabril |
| [`chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) | Pipeline chat |
| [`chat-assistant-content-presentation.md`](../architecture/chat-assistant-content-presentation.md) | Metadata → MFE |
| [`playbook-09-apresentacao-rica.md`](./playbook-09-apresentacao-rica.md) | Decisão table/tree/chart |
| [`shared/delpi_api_client/client.py`](../../../shared/delpi_api_client/client.py) | Cliente HTTP do SI |
| [`api-delpi/docs/api/00-visao-geral.md`](../../../api-delpi/docs/api/00-visao-geral.md) | Convenções envelope |

---

## 10. Controle de versão do contrato

| `dataVersion` | Mudança | Consumidores afetados |
|---------------|---------|------------------------|
| *(ausente)* | Baseline atual (jun/2026) | Todos — estado de referência |
| `2026-06` | `meta` + `error` no root (aditivo) | Nenhum obrigatório; chat opcional |
| `2026-07` | Envelope 404 unificado | SI, MFEs, chat — Fase 2 |
| *futuro* | Tipos normalizados; remoção `SIM`/`NAO` | SI gateways, dashboards, presenter — só após `legacy` deprecado |

Bump de `dataVersion` obrigatório quando campo em **`data`** for **removido** ou **mudar tipo**. Adição de campo opcional em `data` ou qualquer campo em `meta` **não** exige bump.

**Comunicação de breaking change:** entrada no CHANGELOG api-delpi + aviso em release notes do monorepo + atualização da matriz § 4.5.

---

## Resumo executivo

A api-delpi é consumida por **chat IA**, **strategic-indicators-api**, **plugins MFE** e outros clientes HTTP. O contrato evolui em duas camadas: **`data`** (estável para legado) e **`meta`** (novo, para IA). Mudanças aditivas nas fases 1–3 não exigem deploy coordenado; normalizações e defaults (fases 5–6) exigem **`?legacy=true`**, matriz de consumidores e smoke SI/MFE antes do merge.

Próximo passo recomendado: **Fase 1** (`agent_route` em LMP summary/transforma + reimport OpenAPI). Fase 0 concluída: [`fase-0-inventario-contrato-respostas.md`](../../../api-delpi/docs/roadmaps/fase-0-inventario-contrato-respostas.md).
