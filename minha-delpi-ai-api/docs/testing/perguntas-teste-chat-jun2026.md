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
PYTHONPATH=. .venv/bin/python scripts/audit_presentation_coverage.py --check-table-roles
PYTHONPATH=. .venv/bin/python scripts/audit_presentation_coverage.py --check-visual-builders

# Contrato por entidade (pytest)
PYTHONPATH=. .venv/bin/pytest tests/unit/domain/services/test_chat_presentation_entity_contract.py -q
PYTHONPATH=. .venv/bin/pytest tests/unit/application/use_cases/test_playbook_presentation_pipeline_regression.py -q
```

---

## §8 — Homologação Playbook 12 (R1–R12)

Roteiro manual pós-refatoração declarativa. Marque OK/Falha após cada item.

| ID | Pergunta / ação | Valida |
|----|-----------------|--------|
| H1 | `analise de preço 90260145` — stack narrativo + abas KPI/tabela | R4, R8 |
| H2 | `status fabril 90263749` — KPI em cards, ordem painel | R1, R2 |
| H3 | `estrutura 10080001` — árvore + tabela sem duplicata | R3, R8 |
| H4 | `estoque 10080001` — tabela stock, sem narrativa humanizada forçada | R4, R8 |
| H5 | `status produção` (produto playbook) — dashboard + KPI | R2, R6 |
| H6 | `última compra MP 10080001` — bundle compra | R2 |
| H7 | Modo **Tabela** na toolbar — respeita preferência | R5, R7 |
| H8 | Modo **Gráfico** em rota com série — chart disponível | R2, R6 |
| H9 | Multi-rota analyser — seções numeradas, toolbar por bloco | R1, R3, R7 |
| H10 | Rotas tier C (ex. HR snapshot) — schema-driven + KPI | R6 |
| H11 | Chip «Ver em gráfico» pós-resposta | onda 1 |
| H12 | Regressão pytest entity contract + audit coverage | R9 CI |

**Gates CI (R9–R12):**

```bash
cd minha-delpi-ai-api
PYTHONPATH=. python scripts/audit_presentation_coverage.py --check-playbook12
PYTHONPATH=. pytest tests/unit/domain/services/test_playbook12_regression_suite.py \
  tests/unit/domain/services/test_chat_presentation_entity_contract.py -q
```

| Gate | Comportamento |
|------|---------------|
| `--check-profiles` | fail — tier A/B sem perfil dedicado |
| `--check-table-roles` | fail — fixture tier A com tabela sem `role` |
| `--check-visual-builders` | warn — `viewOrder` com kpi/tree/chart/dashboard sem builder |
| `--check-interactivity-chips` | fail — fixture tier A sem chip pós-resposta declarado |
| `--check-playbook12` | fail — qualquer gate R12 (inclui path baseline + new ops) |
| `--check-new-operations` | fail — operação nova OpenAPI sem contrato |

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

**Smoke E2E** (`smoke_perguntas_teste_chat_jun2026.py`) — **16/16 cenários single-turn OK** *(execução 09/jun)*:

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

## Homologação R13 — pós-E2E apresentação (10/jun/2026)

**Commit:** `16052f98` · **Smoke completo:** **21/21 OK** · **Regressão R13:** `--case R13`.

| Caso | Resultado |
|------|-----------|
| E1 «Como está a fábrica… **hoje**» | `/factory-status` *(sem data → `missing_date`, F5)* |
| E3 «analise de preço 90260145» | `/pricing` |
| E4 fabril após estoque na sessão | `/factory-status` |
| E6 `metadata.interactivity` no POST | OK |

```bash
cd minha-delpi-ai-api
SMOKE_PAUSE_SECONDS=2 python3 scripts/smoke_perguntas_teste_chat_jun2026.py --case R13
```

---

## Homologação apresentação + roteiro completo (jun/2026)

Revalidação após **stack rico** (narrativa + KPI/árvore/gráfico/dashboard), árvore BOM, dedup estrutura e vocabulário centralizado (`presentation_vocabulary.json`).

**Commit:** `6015a38c` · **Ambiente:** gateway `localhost`, usuário `rober`, agente Minha DELPI Chat.

### Smoke E2E — roteamento e turnos

Comando (no **host**, não dentro do container — `localhost` não resolve de dentro da API):

```bash
cd minha-delpi-ai-api
SMOKE_BASE_URL=http://localhost PYTHONPATH=. python3 scripts/smoke_perguntas_teste_chat_jun2026.py
```

**Resultado: 21/21 OK** (single-turn + multi-turn F5/F6, MP10, R6, MP7).

| Cenário | Pergunta (resumo) | Rota / efeito | Latência |
|---------|-------------------|---------------|----------|
| R1 | estoque `10080022` | `/stock` | ~1,5 s |
| R2 | status fabril `90269002` hoje | `/factory-status` | ~1,5 s |
| R3 | análise MP `10080001` | `/raw-material-price-intelligence` | ~1,6 s |
| R4 | impacto custo PA `90261255` | `/cost-impact-simulation` | ~1,5 s |
| R5 | preço venda `10080001` | `/pricing` | ~1,5 s |
| F2 | produção `90269002` hoje | `/production-status` | ~1,4 s |
| F3 | expedição `90269002` hoje | `/shipping-status` | ~1,3 s |
| F4 | MPs exclusivas estrutura `90269002` | `/structure/exclusivity` | ~1,4 s |
| MP1 | Análise preço MP `10080001` | `/raw-material-price-intelligence` | ~1,4 s |
| MP2 | Última compra + ICMS | `/last-purchase` | ~1,1 s |
| MP3 | Orçamento compra | `/purchase-budget-history` | ~1,5 s |
| MP4 | Histórico preço compra | `/purchase-price-history` | ~1,6 s |
| MP6 | Simule +10% PA | `/cost-impact-simulation` | ~1,5 s |
| MP8 | Preço venda | `/pricing` | ~1,7 s |
| MP9 | Últimas compras | `/purchases` | ~1,3 s |
| D1 | Preço venda *(não intelligence)* | `/pricing` — **não** `/raw-material-price-intelligence` | OK |
| F5 | status fabril sem data | `pending=missing_date` | OK |
| F6 | continuação «hoje» | `/factory-status` | ~1,8 s |
| MP10 | «análise MP» → `10080001` | `/raw-material-price-intelligence` | ~1,8 s |
| R6 | refinamento «em tabela» | sem `/system/tables`; reapresenta último resultado | ~68 s |
| MP7 | MP no simulador PA | erro amigável / não OK silencioso | ~1,3 s |

### Apresentação — regressão de pipeline (fixtures API-DELPI)

`pytest tests/unit/application/use_cases/test_playbook_presentation_pipeline_regression.py` — **5/5 OK**:

| Caso | Rota / fixture | O que valida |
|------|----------------|--------------|
| R2 fabril | `90269002` `/factory-status` | `selected=text`, `layoutMode=stack`, KPI + árvore + dashboard |
| F4 exclusividade | `90261805` `/structure/exclusivity` | árvore PA→PI→MP, dedup tabela estrutura, MPs `10020053`/`10080185` na narrativa, painel `structure` |
| R3 MP | `10080022` `/raw-material-price-intelligence` | narrativa rica + stack + KPI + gráfico |
| R4 simulador | `90261255` `/cost-impact-simulation` | stack + KPI + gráfico |
| R1 estoque | `90269001` `/stock` | stack texto + árvore + tabela de posições |

Lote ampliado (intent + apresentação): **219 passed** — `test_chat_intelligence_regression`, `test_chat_product_query_intent_service`, `test_playbook_presentation_pipeline_regression`.

### Narrativa humanizada — roteiro R1–R5 (jun/2026)

**Commits:** `70d9556f`, `cc4ce7d8` · Doc: [`humanized-narrative-stack-jun2026.md`](../architecture/humanized-narrative-stack-jun2026.md)

`pytest tests/unit/application/use_cases/test_roteiro_rapido_humanization.py` — **7/7 OK**:

| Caso | Pergunta (resumo) | O que valida |
|------|-------------------|--------------|
| R1 | estoque `10080022` | `selected=text`, `layoutMode=stack`, `humanizedSections`, markdown narrativo |
| R2 | status fabril `90269002` | idem |
| R3 | análise MP `10080001` | idem + «Leitura do histórico» e «Pontos de atenção» |
| R4 | simulador PA `90261255` | stack humanizado |
| R5 | preço venda `10080001` | «Panorama», «Leitura rápida», «Conclusão»; sem `R$ R$` |

Homologação manual recomendada: `analise de preço 90260145` — aba **Completo/Texto** deve mostrar narrativa antes de KPI/gráfico/árvore (21 tabelas WEG LINHARES).

### Não coberto por smoke automatizado

| # | Tipo | Notas |
|---|------|-------|
| R7 | Chip «Gerar gráfico» pós-estoque | Manual / MFE |
| F1 | Igual R2 | Coberto indiretamente por R2 |
| MP5 | Igual R4 | Coberto indiretamente por R4 |
| AP1–AP15 | Toolbar, chips, paginação | Manual — ver [`presentation-homologation-jun2026.md`](presentation-homologation-jun2026.md) |
| D2–D4 | Desambiguação negativa | Parcialmente coberto por pytest de intent |

---

## Registro do teste — jun/2026

| # | OK | Observação |
|---|:--:|------------|
| R1 | ☑ | smoke E2E `/stock` |
| R2 | ☑ | smoke + pipeline stack fabril |
| R3 | ☑ | smoke `/raw-material-price-intelligence` |
| R4 | ☑ | smoke + pipeline cost-impact |
| R5 | ☑ | smoke `/pricing` |
| R6 | ☑ | smoke refinamento tabela (~68 s) |
| R7 | ☐ | manual — chip gráfico |
| F1 | ☑ | equivalente R2 |
| F2 | ☑ | smoke `/production-status` |
| F3 | ☑ | smoke `/shipping-status` |
| F4 | ☑ | smoke + pipeline exclusividade `90261805` |
| F5 | ☑ | smoke `missing_date` |
| F6 | ☑ | smoke continuação «hoje» |
| MP1 | ☑ | smoke intelligence |
| MP2 | ☑ | smoke `/last-purchase` |
| MP3 | ☑ | smoke orçamento |
| MP4 | ☑ | smoke histórico preço |
| MP5 | ☑ | equivalente R4 |
| MP6 | ☑ | smoke simulação +10% |
| MP7 | ☑ | smoke erro MP no simulador |
| MP8 | ☑ | smoke pricing |
| MP9 | ☑ | smoke purchases |
| MP10 | ☑ | smoke sessão ativa |
| AP1 | ☐ | manual toolbar |
| AP5 | ☐ | manual refinamento |
| AP9 | ☐ | manual chips |
| D1 | ☑ | smoke não intelligence |

**Tester:** automação + revisão assistente · **Ambiente:** local (WSL2, docker compose) · **Commit:** `6015a38c`
