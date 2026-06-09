# Perguntas de teste — chat operacional, playbooks e apresentação (jun/2026)

Roteiro **pronto para copiar e colar** no chat. Use a **mesma conversa** nos blocos multi-turno.

**Agente:** Minha DELPI Chat (`minha-delpi-chat`) · **Ambiente:** gateway + api-delpi no ar.

## Produtos de referência

| Código | Uso |
|--------|-----|
| `10080001` | MP homologada (preço, NF, ICMS, orçamento) |
| `90261255` | PA homologado (BOM multinível, simulador de custo) |
| `90269002` | Playbook fabril (status produção/expedição) |
| `10080022` | Estoque / paginação / drill-down clássico |
| `90260142` | Roteiro + interpretação de dados |

---

## Roteiro rápido (~15 min)

Copie na ordem; marque OK/Falha na tabela ao final.

| # | Cole no chat | Rota / efeito esperado |
|---|--------------|------------------------|
| R1 | `estoque do produto 10080022` | `/stock` — tabela ou gráfico |
| R2 | `status fabril do produto 90269002 hoje` | `/factory-status` — pede data se omitir «hoje» |
| R3 | `análise de preço da matéria-prima 10080001` | `/raw-material-price-intelligence` |
| R4 | `quais materiais mais impactam o custo do PA 90261255?` | `/cost-impact-simulation` |
| R5 | `qual o preço de venda do produto 10080001?` | `/pricing` — **não** rota de compra MP |
| R6 | *(após R3)* `mostre o último resultado em tabela` | Refinamento de formato — mesma rota, sem nova consulta errada |
| R7 | *(após R1)* clique chip **Gerar gráfico** ou digite `gere um gráfico com os dados acima` | Chips pós-resposta / refinamento |

---

## Playbook fabril (produto `90269002`)

| # | Pergunta | Rota esperada | Notas |
|---|----------|---------------|-------|
| F1 | `status fabril do produto 90269002 hoje` | `/factory-status` | Data explícita ou resposta curta «hoje» |
| F2 | `situação de produção do 90269002 hoje` | `/production-status` | |
| F3 | `inspeção final expedição produto 90269002 hoje` | `/shipping-status` | |
| F4 | `quais matérias-primas exclusivas existem na estrutura do produto 90269002?` | `/structure/exclusivity` | |
| F5 | `status fabril do produto 90269002` | *(pending)* | Deve **pedir data** antes da API |
| F6 | *(após F5)* `hoje` | `/factory-status` | Sessão ativa recomponha a pergunta |

---

## Playbook preço MP e simulador PA

| # | Pergunta | Rota esperada | Notas |
|---|----------|---------------|-------|
| MP1 | `Análise de preço da matéria-prima 10080001` | `/raw-material-price-intelligence` | Resposta rápida; sem improvisação LLM |
| MP2 | `Última compra e ICMS do produto 10080001` | `/raw-material-price-intelligence` ou `/last-purchase` | Intelligence quando pede ICMS composto |
| MP3 | `Histórico de orçamento de compra do produto 10080001` | `/purchase-budget-history` | **Não** confundir com `/purchases` |
| MP4 | `Histórico de preço de compra do 10080001` | `/purchase-price-history` | Variação % vem da API |
| MP5 | `Quais materiais mais impactam o custo do PA 90261255?` | `/cost-impact-simulation` | Ranking Pareto na BOM |
| MP6 | `Simule aumento de 10% nos materiais do produto 90261255` | `/cost-impact-simulation` | `adjustment_percent=10` |
| MP7 | `Simule impacto de custo do produto 10080001` | erro amigável | MP na rota PA → API 400 |
| MP8 | `Qual o preço de venda do produto 10080001?` | `/pricing` | Desambiguação compra × venda |
| MP9 | `últimas compras do produto 10080001` | `/purchases` | Listagem — **não** orçamento SC/PC |
| MP10 | *(sessão nova)* `análise de preço MP` → *(só)* `10080001` | `/raw-material-price-intelligence` | Continuação de sessão / código isolado |

---

## Apresentação — toolbar, chips e refinamento (jun/2026)

Use **mesma conversa** dentro de cada mini-cenário.

### Preferência na toolbar

| # | Sequência | O que observar |
|---|-----------|----------------|
| AP1 | `estoque do produto 10080022` → selecione **Tabela** antes de enviar (ou chip formato) | `presentation.type` = table; `selected` = table |
| AP2 | Mesma rota → selecione **Gráfico** | Gráfico principal; `selected` = chart |
| AP3 | `estrutura do produto 90260047` → **Árvore** | `selected` = tree |
| AP4 | `análise de preço da matéria-prima 10080001` → **Texto** | Narrativa + stack se perfil permitir |

### Refinamento conversacional (sem nova rota errada)

| # | Sequência | O que observar |
|---|-----------|----------------|
| AP5 | *(após estoque 10080022)* `mostre os dados acima em tabela` | Reapresenta último resultado |
| AP6 | *(após estoque)* `mostre o último resultado em gráfico` | Chart a partir do cache |
| AP7 | *(após analyser)* `coloque em uma tabela` | Não roteia para `/system/tables` |
| AP8 | *(após MP1)* `mostre em linha` | Chip/recomendação série temporal se houver datas |

### Chips «Próximos passos»

| # | Após resposta | Chips esperados (exemplos) |
|---|---------------|----------------------------|
| AP9 | Estoque (texto) | Ver como tabela · Gerar gráfico · Só com saldo |
| AP10 | Tabela MP (MP1) | Exportar CSV · Ver em linha (se datas) |
| AP11 | Simulador PA (MP5) | Exportar CSV · Gerar gráfico |
| AP12 | Gráfico | Ver como tabela · Explique esse gráfico |

### Paginação + formato

| # | Sequência | O que observar |
|---|-----------|----------------|
| AP13 | `onde é usado o 10080022` → `traga tudo` | Consolida páginas |
| AP14 | *(após AP13)* `sim, continue` | Mantém formato preferido do turno anterior |
| AP15 | *(após estoque)* `mostre o último resultado em tabela` | `collect_last_preferred_format` cross-turn |

---

## Desambiguação — não deve acionar

| # | Pergunta | O que **não** deve acontecer |
|---|----------|------------------------------|
| D1 | `Qual o preço de venda do produto 10080001?` | Rota `/raw-material-price-intelligence` |
| D2 | `Histórico de orçamento…` com pedido SC/PC/cotação | Rota genérica `/purchases` no lugar de `/purchase-budget-history` |
| D3 | `Simule custo do 10080001` (MP) | Simulador PA sem erro claro |
| D4 | `coloque em uma tabela` *(sem consulta prévia)* | Nova rota operacional aleatória |

---

## Smoke automatizado (mesmas frases)

```bash
cd minha-delpi-ai-api

# Perguntas deste roteiro (E2E gateway, user rober)
SMOKE_BASE_URL=http://localhost \
SMOKE_MP_CODE=10080001 \
SMOKE_PA_CODE=90261255 \
SMOKE_PRODUCT_CODE=90269002 \
PYTHONPATH=. .venv/bin/python scripts/smoke_perguntas_teste_chat_jun2026.py

# Playbook produto + fabril + MP/PA (rotas isoladas)
SMOKE_PRODUCT_CODE=90269002 \
SMOKE_MP_CODE=10080001 \
SMOKE_PA_CODE=90261255 \
SMOKE_BASE_URL=http://localhost \
PYTHONPATH=. .venv/bin/python scripts/smoke_playbook_product_routes.py

# Gate apresentação (CI local)
PYTHONPATH=. .venv/bin/python scripts/audit_presentation_coverage.py --check-profiles

# Contrato por entidade (pytest)
PYTHONPATH=. .venv/bin/pytest tests/unit/domain/services/test_chat_presentation_entity_contract.py -q
```

Homologação amostral completa: [`presentation-homologation-jun2026.md`](presentation-homologation-jun2026.md).

Checklist histórico (U1–G14, #70–79, …): [`smoke-operacional-manual.md`](smoke-operacional-manual.md).

---

## Homologação 09/jun/2026 — roteamento playbook MP/PA

Sessão de correção e validação E2E (API gateway, usuário `rober`, agente Minha DELPI Chat). Objetivo: perguntas do roteiro acionarem a **rota correta** e respostas com markdown canônico (`### …`, `<!-- section:scope -->`).

### Problemas encontrados

| Sintoma | Causa raiz |
|---------|------------|
| `preço de venda` → `/sales` | `_looks_like_sales_question` tratava « venda do » dentro de «preço **de venda do** produto»; intent `SALES` filtrava só rotas de vendas |
| `Histórico de preço de compra` → `/raw-material-price-intelligence` | Termo genérico «preço de compra» no vocabulário de intelligence colidia com histórico |
| `Simule aumento de 10%…` → chips de desambiguação | `ChatIntentRouterService._operational_ambiguity` marcava pergunta como ambígua sem reconhecer simulador PA |
| MP2, orçamento, última compra → `/purchases` | `purchasesTerms` genérico («compra», «última compra») ganhava ranking sobre rotas playbook |
| Smoke em lote → HTTP 429 | Rate limit do gateway ao criar muitas sessões seguidas; cenários multi-turn (F6, MP10, R6, MP7) exigem pausa entre execuções |

### Correções (chat base — não patch no agente)

| Módulo | Mudança |
|--------|---------|
| `ChatProductQueryIntentService` | Rotas playbook (preço venda, intelligence, simulador, históricos) **antes** de multi-scope; `sale_pricing` não é `sales`; histórico de preço de compra não cai em intelligence |
| `ChatIntentRouterService` | Playbook e preço de venda **não** disparam desambiguação operacional; sub-intents dedicados |
| `ExternalActionProductRouteSelectionService` | Ranking suprime `purchases`/`pricing` genéricos quando intent playbook está claro; penaliza `/sales` em preço de venda |

### Resultado dos testes (09/jun/2026)

**Smoke E2E** (`smoke_perguntas_teste_chat_jun2026.py`) — **16/16 cenários single-turn OK**:

| Cenário | Rota obtida | Formato |
|---------|-------------|---------|
| R1–R5, F2–F4 | rotas fabril / MP / PA / pricing esperadas | markdown + `section:scope` |
| MP1–MP4, MP6, MP8–MP9, D1 | playbook MP/PA; D1 **não** intelligence | OK |
| MP2 | `/last-purchase` *(aceito também `/raw-material-price-intelligence`)* | OK |
| F5 | `pending=missing_date` | OK |

**Multi-turn** (F6, MP10, R6, MP7): não revalidados na mesma execução por **429** após o lote single-turn — rodar isoladamente com intervalo (~2 s) ou `--case` futuro.

**Pytest** (218 testes): `test_chat_product_query_intent_service`, `test_chat_intent_disambiguation_service`, `test_chat_intelligence_regression` — **OK**.

**Pré-requisito deploy:** reiniciar `minha-delpi-ai-api` após pull (`docker compose … restart minha-delpi-ai-api`) para recarregar módulos Python em volume bind.

---

## Registro do teste — ___/___/2026

| # | OK | Observação |
|---|:--:|------------|
| R1 | ☐ | |
| R2 | ☐ | |
| R3 | ☐ | |
| R4 | ☐ | |
| R5 | ☐ | |
| R6 | ☐ | |
| R7 | ☐ | |
| F1 | ☐ | |
| F2 | ☐ | |
| F3 | ☐ | |
| F4 | ☐ | |
| MP1 | ☐ | |
| MP2 | ☐ | |
| MP3 | ☐ | |
| MP4 | ☐ | |
| MP5 | ☐ | |
| MP6 | ☐ | |
| MP7 | ☐ | |
| MP8 | ☐ | |
| AP1 | ☐ | |
| AP5 | ☐ | |
| AP9 | ☐ | |
| D1 | ☐ | |

**Tester:** _______________ · **Ambiente:** local / homolog · **Commit/deploy:** _______________
