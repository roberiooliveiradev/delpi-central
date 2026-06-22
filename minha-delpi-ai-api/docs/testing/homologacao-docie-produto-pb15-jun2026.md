# Homologação DOCIE — produto + Playbook 15 (jun/2026)

Checklist e evidências para **DoD DOCIE §11 item 6** (homologação manual produto + PB15).

**Ambiente:** stack local (`SMOKE_BASE_URL=http://localhost`), agente Minha DELPI Chat habilitado, api-delpi ativa.

**Commit DOCIE:** `b756a2be` (Fase 20) · documentação `3bc9858e`.

---

## 1. Regressão automatizada (offline)

| Suite | Comando | Resultado |
|-------|---------|-----------|
| Seleção produto + PB15 | `pytest tests/unit/domain/services/test_chat_intelligence_regression.py tests/unit/application/services/test_external_action_operational_route_selection_service.py tests/unit/domain/services/test_chat_production_operational_intent_service.py -q` | **228 passed** |
| Gates DOCIE | `lint_operational_route_registry.py --check`, `generate_operational_route_registry.py --check`, `audit_presentation_path_ifs.py --check` | **OK** |

---

## 2. Smoke E2E — rotas produto (playbook)

**Script:** `scripts/smoke_playbook_product_routes.py`

**Data:** 16/06/2026

| # | Cenário | Path esperado | Resultado |
|---|---------|---------------|-----------|
| 1 | Estoque sem código | `missing_product_code` | OK |
| 2 | Estoque `90269002` | `/products/…/stock` | OK |
| 3 | Status fabril + data | `/factory-status` | OK |
| 4 | Produção + data | `/production-status` | OK |
| 5 | Expedição + data | `/shipping-status` | OK |
| 6 | Exclusividade MP | `/structure/exclusivity` | OK |
| 7 | Preço MP `10080001` | `/raw-material-price-intelligence` | OK |
| 8 | Última compra MP | `/last-purchase` | OK |
| 9 | Simulador PA `90261255` | `/cost-impact-simulation` | OK |
| 10 | Preço de venda | `/pricing` | OK |
| 11 | Continuação estoque (sessão) | `/stock` | OK |

---

## 3. Smoke E2E — Playbook 15 (produção operacional)

**Script:** `scripts/smoke_playbook_production_operational.py`

**Data:** 16/06/2026 · **PASS — 0 falhas**

### api-delpi (16 rotas REST)

P0–P3: consumo top, compras ranking, refugos, programação do dia, OPs abertas/finalizadas, resumo CT, consumo por CT/validado, empenho, OPs sem consumo, tempo médio CT, consumo por item, planejado×real.

### chat E2E (14 cenários S1–S14)

Seleção via registry DOCIE (`operationalRoutes`) — paths `/production/*` e `/purchases/top-products` confirmados nos metadados da resposta.

---

## 4. Amostra manual recomendada (UI)

Copiar/colar de [`perguntas-teste-chat-jun2026.md`](perguntas-teste-chat-jun2026.md) — blocos **F** (fabril) e **H** (humanização), se validar MFE:

| ID | Pergunta | Verificar |
|----|----------|-----------|
| F1 | `status fabril do 90269002 hoje` | Painel/tabela, não SQL |
| F2 | `situação de produção do 90269002 hoje` | `/production-status` |
| H5 | `status produção` (com produto em contexto) | KPI + dashboard |

Apresentação rica: [`presentation-homologation-jun2026.md`](presentation-homologation-jun2026.md) — **gates automatizados OK** (16/06/2026); amostra manual MFE (toolbar) opcional.

---

## 5. Critério de aceite DOCIE

- [x] Seleção produto playbook (estoque, status, MP/PA, pricing) via registry — smoke E2E OK
- [x] 14 rotas PB15 REST + chat — smoke E2E OK
- [x] Regressão unitária inalterada — 228 casos OK
- [x] Gates CI DOCIE — OK
- [ ] UI toolbar/modos Automático·Tabela·Texto — amostra manual opcional (não bloqueia DoD seleção)

**Status DoD §11.6:** homologação **produto + PB15** concluída em ambiente local (16/06/2026).

---

## 6. Homologação E2E — qualidade operacional (jun/2026)

**PA de referência:** `90260140` (programação 22/06/2026) · roadmap [`playbook-chat-operational-quality-roadmap-jun2026.md`](../roadmap/playbook-chat-operational-quality-roadmap-jun2026.md)

### Regressão offline (CI)

| Suite | Comando | Escopo |
|-------|---------|--------|
| Seleção PA 90260140 | `pytest tests/unit/domain/services/test_chat_intelligence_regression.py -k OQ -q` | Fabril, produção, expedição, custo +10% |
| Contrato scripts eval | `pytest tests/unit/scripts/test_operational_quality_eval_jun2026.py -q` | `FOLLOW_UPS` / `SCENARIOS` alinhados ao mapa |

### Smoke E2E (stack local + Ollama)

Requer `SMOKE_BASE_URL=http://localhost`, credenciais Keycloak e api-delpi ativa.

```bash
cd minha-delpi-ai-api
PYTHONPATH=. SMOKE_BASE_URL=http://localhost SMOKE_PAUSE_SECONDS=1 \
  .venv/bin/python scripts/eval_real_product_flow_jun2026.py
PYTHONPATH=. SMOKE_BASE_URL=http://localhost SMOKE_PAUSE_SECONDS=1.5 \
  .venv/bin/python scripts/eval_response_modes_product_routes_jun2026.py
```

Relatórios gerados em `scripts/eval_*_report.json` (ignorados pelo git).

---

## Reexecução rápida

```bash
cd minha-delpi-ai-api
PYTHONPATH=. SMOKE_BASE_URL=http://localhost SMOKE_PAUSE_SECONDS=1 \
  python3 scripts/smoke_playbook_product_routes.py
PYTHONPATH=. SMOKE_BASE_URL=http://localhost SMOKE_PAUSE_SECONDS=1 \
  python3 scripts/smoke_playbook_production_operational.py
```
