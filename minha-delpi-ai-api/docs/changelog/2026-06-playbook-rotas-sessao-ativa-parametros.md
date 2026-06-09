# Changelog — Playbooks fabril, parâmetros obrigatórios e sessão ativa (jun/2026)

Melhorias no **chat base** para rotas de playbook da api-delpi (`factory-status`, `production-status`, `shipping-status`, `structure/exclusivity`), **perguntas de parâmetro faltante** (código, data, filial…) e **continuação da mesma consulta** até o usuário mudar de assunto.

Documentação de arquitetura:

- [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) (§ Parâmetros obrigatórios · § Sessão ativa · § Playbooks fabril)
- [`../architecture/session-memory.md`](../architecture/session-memory.md) (`metadata.activeQuery`)
- [`../knowledge/api-delpi-rotas-agente.md`](../knowledge/api-delpi-rotas-agente.md) (regras de data e follow-up)

---

## Problema

| Sintoma | Causa |
|---------|--------|
| «status fabril do 90263059» consultava API com default «hoje» silencioso | Rotas com `reference_date` / `date_start` / `date_end` no schema sem validação no chat |
| «estoque» pedia período em vez de código | Termo «estoque» em `_PERIOD_METRIC_TERMS` acionava `missing_date` / `period_metric` |
| Resposta lenta ou improvisada pelo LLM | Turno caía em desambiguação ou síntese sem `execute_external_action` |
| Usuário mandava só o código após pergunta do chat | Pending resolvia `productCode`, mas planejamento não recomponha a pergunta original |
| Novos códigos na sequência («9026…», «1008…») | Sem herança explícita do tipo de consulta (estoque vs estrutura) |

---

## Solução (visão)

```text
Usuário: estoque
  → missing_product_code (operational_parameters.json)
  → metadata.activePending + direct_answer (sem tools/LLM)

Usuário: 90263059
  → compose_selection_message → "estoque 90263059"
  → GET /products/90263059/stock (~0,3s)
  → metadata.activeQuery { subIntent: stock, originalMessage: "estoque" }

Usuário: 10080099
  → compose → "estoque 10080099" (mesma sessão até mudar assunto)

Usuário: estrutura do 90263059
  → topic change → nova rota /structure
```

Rotas com **data obrigatória** (`factory-status`, `production-status`, `shipping-status`):

```text
Usuário: status fabril do 90263059
  → missing_date (pergunta data/período)

Usuário: hoje | semana passada | 01/06/2026
  → resumeMessage + parâmetros DD-MM-YYYY
  → GET /products/{code}/factory-status
```

---

## API — módulos canônicos

| Serviço | Função |
|---------|--------|
| `ChatOperationalDateParameterService` | Detecção de referência temporal; merge de `reference_date` / `date_start` / `date_end`; pending `missing_date`; não seleciona action sem data preenchida |
| `ChatActiveQuerySessionService` | `compose_selection_message`; `metadata.activeQuery`; continuação vs mudança de assunto; sessão web search |
| `ChatActivePendingService` | `activePending` estendido com `context.originalMessage`; `resumeMessage` para código (incl. múltiplos) e data |
| `ChatOperationalParameterService` | Pergunta código (STOCK, STRUCTURE, PARENTS, DESCRIPTION, ANALYSER, SUMMARY); guard de tools |
| `ChatExternalActionOrchestrationService` | Planejamento usa mensagem **composta** (`selection_message`) para intent e códigos |
| `ExternalActionProductRouteSelectionService` | Pula action se schema exige data e parâmetros temporais vazios |

Textos PT-BR: `operational_parameters.json` (`missingProductCode`, `missingDateByContext`).

---

## Playbooks — rotas e apresentação

| Playbook / intenção | Rota api-delpi | Presenter / profile |
|---------------------|----------------|---------------------|
| Situação produtiva | `GET /products/{code}/production-status` | `product_production_status` |
| Expedição / inspeção final | `GET /products/{code}/shipping-status` | `product_shipping_status` |
| Status fabril completo | `GET /products/{code}/factory-status` | `product_composite_analysis` + stack humanizado |
| Estrutura + MPs exclusivas | `GET /products/{code}/structure/exclusivity` | `product_structure_exclusivity` |

Wiring: `ExternalActionResultPresenter`, `ChatPresentationRoutePolicyService`, `ChatPresentationSectionAvailabilityService`, `ChatPresentationStackOrderService`, bundles `presenter_content.json` / `product_operational_content.json` / `product_query_intent.json`.

**Frases recomendadas (evitam desambiguação):**

- Expedição: «inspeção final expedição produto {code} hoje»
- Exclusividade: «quais matérias-primas exclusivas existem na estrutura do produto {code}?»

---

## Metadata do assistente

| Chave | Quando | Conteúdo |
|-------|--------|----------|
| `activePending` | Resposta pedindo parâmetro | `kind`: `missing_product_code` \| `missing_date` \| `ambiguous_period_year`; `context.originalMessage`, `subIntent`, `expectedParam` |
| `activeQuery` | Após tool operacional ou web search bem-sucedido | `queryKind`, `subIntent`, `originalMessage`, `expectedParam`, `routeSegment` (opcional) |

Resolução de pending: `ChatIntentRouterService.classify` → `clarification` + `resolved_params` antes do planejamento de actions.

---

## Vocabulário temporal

Reutiliza `ChatDateRangeIntentService`: **hoje**, **ontem**, **semana passada**, **este mês**, **últimos 30 dias**, datas `DD/MM/YYYY`, intervalos `01/04 a 30/04`, etc.

Formato enviado à API: **DD-MM-YYYY** (`reference_date`, `date_start`, `date_end`).

---

## Testes

| Tipo | Arquivo |
|------|---------|
| Regressão seleção | `tests/fixtures/chat_intelligence_regression_cases.py` (`DATE_RANGE_SELECTION_CASES`, playbooks produto) |
| Data obrigatória | `tests/unit/domain/services/test_chat_operational_date_parameter_service.py` |
| Sessão ativa | `tests/unit/domain/services/test_chat_active_query_session_service.py` |
| Presenter / fixtures | `tests/fixtures/api_delpi_responses/product_*_90269002.json` |
| Smoke E2E | `scripts/smoke_playbook_product_routes.py` |

```bash
# Unitários
cd minha-delpi-ai-api && .venv/bin/python -m pytest \
  tests/unit/domain/services/test_chat_operational_date_parameter_service.py \
  tests/unit/domain/services/test_chat_active_query_session_service.py -q

# E2E (container + gateway)
docker exec -e PYTHONPATH=/app -e SMOKE_BASE_URL=http://delpi-gateway \
  delpi-minha-delpi-ai-api python scripts/smoke_playbook_product_routes.py
```

Latência esperada no smoke local: **~0,1–0,4s** por cenário operacional (sem `llm_synthesis`).

---

## Commit de referência

`feat(chat): rotas de playbook com data, sessão ativa e apresentação otimizada` — jun/2026.
