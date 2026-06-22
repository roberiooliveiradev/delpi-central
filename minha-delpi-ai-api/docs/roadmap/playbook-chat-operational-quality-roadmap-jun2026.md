# Playbook — Qualidade operacional no chat (fabril, MP, custo PA)

**Status:** Sprint 1 em andamento (jun/2026)  
**Evidência E2E:** `scripts/eval_real_product_flow_jun2026.py` · relatório `scripts/eval_real_product_flow_report.json`  
**PA de referência homologado:** `90260140` (programação 22/06/2026)  
**Relacionado:** [playbook-chat-preco-mp-simulador-custos-pa.md](./playbook-chat-preco-mp-simulador-custos-pa.md) · [chat-response-modes.md](../architecture/chat-response-modes.md) · [homologacao-docie-produto-pb15-jun2026.md](../testing/homologacao-docie-produto-pb15-jun2026.md)

---

## 1. Diagnóstico (jun/2026)

Fluxo real testado: programação do dia → PA **9026** da lista → perguntas fabril / MP / simulador × modos **Rápida · Normal · Pensador**.

| Dimensão | Resultado | Gap principal |
|----------|-----------|---------------|
| **Roteamento** | ~87% OK | Perguntas sem «hoje» falham em `/production-status`; coloquial «visão fabril» às vezes sem tool |
| **HTTP api-delpi** | Timeouts 30s no modo Rápida | Rotas `composite_analysis` lentas (`factory-status`, `raw-material-price-intelligence`) |
| **Conteúdo** | `dataAnswer` vazio na UI; erros «Não consegui consultar» com rota OK | Falha intermitente + prosa sem ancoragem nos fatos |
| **Alucinação** | Programação do dia inventou «Produto A: 50 un»; factory-status genérico «em andamento» | `ChatCompositeDirectAnswerService` vazio → LLM improvisa |
| **Modos** | Pouca diferenciação — muito `simple_direct` / `operationalFastPath` | Commentary direct e síntese LLM não consomem `dataCommentary` |

---

## 2. Roadmap por sprint

### Sprint 1 — Confiabilidade e fatos (P0) — **em implementação**

| ID | Entrega | Módulo canônico | Aceite |
|----|---------|-----------------|--------|
| S1.1 | Timeout **60s** em rotas `composite_analysis` | `ExternalActionHttpExecutionService` + `HttpExternalActionGateway` | Rápida sem timeout em `factory-status` / `raw-material-price-intelligence` |
| S1.2 | **Retry 1×** em timeout / HTTP 502–504 | `HttpExternalActionGateway` | Smoke `eval_real_product_flow` falhas HTTP < 5% |
| S1.3 | Mensagem de timeout canônica (JSON) | `ChatSecurityMessagingService` + `external_action_responses.json` | Texto `composite.timeout` em falhas Read timed out |
| S1.4 | Falha total de tool → **prosa só do direct answer** (sem LLM) | `ChatResponseModeService.apply_turn_direct_answer_policy` | Nenhuma inventação quando `ok=false` em todas as tools |
| S1.5 | Preservar `dataAnswer`/`dataCommentary` no metadata da tool | `ChatToolContextExternalActionFormatter._build_safe_tool_metadata` | Metadata da mensagem com `dataAnswer` quando API ok |

**Config declarativa:** `external_action_responses.json` → `httpExecution`.

### Sprint 2 — Roteamento e parâmetros (P1)

| ID | Entrega |
|----|---------|
| S2.1 | «Visão fabril integrada» / coloquial → `/factory-status` |
| S2.2 | Produção granular herda **hoje** quando código presente |
| S2.3 | «Simule +10%» → `adjustment_percent=10` em `cost-impact-simulation` |
| S2.4 | «Última compra e ICMS» → `/last-purchase` (não intelligence) |

### Sprint 3 — Modos Rápida / Normal / Pensador (P1)

| ID | Entrega |
|----|---------|
| S3.1 | Rápida: `fastCommentaryDirect` com lead `dataCommentary` (brief) |
| S3.2 | Normal/Pensador: síntese LLM ancorada; gate anti-alucinação reforçado |
| S3.3 | Pensador: anti-duplicação de blocos na finalização |
| S3.4 | Smoke fixo PA do dia nos 3 modos no CI |

### Sprint 4 — Apresentação rica (P2)

| Rota | Entrega |
|------|---------|
| `/production/schedule/today` | Tabela auditável com códigos 9026 (não prosa inventada) |
| `/factory-status` | Painel seções structure / production / shipping / `factory_status` |
| `/cost-impact-simulation` | Pareto + KPI simulação |
| `/raw-material-price-intelligence` | Última compra + variação + orçamento |

### Sprint 5 — Regressão contínua

- `chat_intelligence_regression_cases.py` — mapa fabril/MP/custo do usuário
- `eval_real_product_flow_jun2026.py` no pipeline de homologação
- Atualizar [homologacao-docie-produto-pb15-jun2026.md](../testing/homologacao-docie-produto-pb15-jun2026.md)

---

## 3. Mapa rota × pergunta (referência)

Ver tabela do usuário (fabril amplo → `/factory-status`; MP → `/raw-material-price-intelligence`; custo → `/cost-impact-simulation`; granulares conforme playbook preço MP).

---

## 4. Testes

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/eval_real_product_flow_jun2026.py
.venv/bin/python -m pytest tests/unit/domain/services/test_external_action_http_execution_service.py -q
.venv/bin/python -m pytest tests/unit/infrastructure/external_actions/test_http_external_action_gateway_retry.py -q
```

---

## 5. Histórico

| Data | Evento |
|------|--------|
| jun/2026 | E2E PA 90260140; roadmap criado; Sprint 1 iniciado |
