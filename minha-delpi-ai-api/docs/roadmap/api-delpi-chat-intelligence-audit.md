# Roadmap — Inteligência do chat × rotas api-delpi

**Objetivo:** garantir que o **chat base** (`minha-delpi-ai-api`) selecione a rota correta, responda com clareza (texto/tabela/markdown), trate typos e informe limitações — para **todos os agentes** herdarem o mesmo comportamento.

**Última atualização:** 2026-05-30  
**Branch de trabalho:** `main`

---

## Legenda de status

| Status | Significado |
|--------|-------------|
| OK | Seleção heurística + testes de regressão cobrindo a intenção |
| PARCIAL | Funciona via ranking semântico ou subconjunto de frases; melhorias pendentes |
| OK* | Coberto indiretamente (ex.: múltiplas rotas no mesmo domínio) |
| N/A | Rota não montada no `main.py` ou só MFE (sem action no chat) |

---

## Resumo executivo (onda atual)

| Domínio | Rotas | Status geral | Principais melhorias nesta onda |
|---------|-------|--------------|----------------------------------|
| Produtos | 18 | OK / PARCIAL | Busca por `group_code`; comparação BOM; apresentação markdown |
| Engenharia LMP | 7 | OK | Dashboard vs lista vs detalhe OV |
| Suprimentos | 4 | OK | CPV, OTD, IDD, stock-value desambiguado de estoque item |
| Vendas (OV) | 1 | OK | `list_sale_orders` |
| Comercial | 9 | OK | + `/commercial/proposals`; heurísticas KPI |
| Financeiro | 4 | OK | EBITDA, PMR, ROL, custo fixo + typos |
| Produção | 9 | OK | OEE/OTD %, séries, eficiência fabril, custos |
| RH | 4 | OK | Snapshot, PDI, avaliações, filiais |
| Qualidade TOTVS | 10 | OK | NC, PPM, kaizen, 5S, filiais |
| Dados SQL | 1 | OK | Intent SQL + policy skill |
| Sistema | 8 | OK | tabelas/colunas + schema/índices/relações |
| Eng. Transforma+ | 2 | OK | `_select_transforma_action` |
| NC PostgreSQL | 10+ | PARCIAL | Rotas `/quality/audit-5s/*` montadas; catálogo + heurísticas 11.6 |
| Capacidades | — | OK | `ChatCapabilitiesService` + perguntas por feature |
| Conhecimento | — | OK | Base global agentes; limite 2M chars documento |

---

## 1. Produtos (`/products`)

| Rota | Frases teste (corretas) | Typos / variações | Seleção | Resposta | Status | Notas |
|------|-------------------------|-------------------|---------|----------|--------|-------|
| `GET /search` | liste 3 exemplos de TERM; busque parafuso m8 | forncedor→N/A aqui | `search_products` | lista + tabela UI | OK | `group_code` ao pedir grupo |
| `GET /{code}` | descrição do 10080047 | descricao, prodt | description intent | markdown cadastro | OK | |
| `GET /{code}/summary` | resumo do 10080047 | resumo sintetico | summary rank | markdown | OK | vs analyser explícito |
| `GET /{code}/analyser` | ficha completa 10080047 | | analyser rank | | OK | |
| `GET /{code}/stock` | estoque do 10080047 | estoq, estq | STOCK intent | tabela/lista | OK | ≠ stock-value empresa |
| `GET /{code}/structure` | estrutura do 90260077 | estrutur | STRUCTURE | markdown hierárquico | OK | comparação multi-produto |
| `GET /{code}/structure/excel` | exportar estrutura excel | | | download MFE | N/A chat | preferir JSON |
| `GET /{code}/parents` | onde é usado o 10080001 | produto pai | PARENTS | lista | OK | |
| `GET /{code}/suppliers` | fornecedores do 10080001 | forncedores | suppliers rank | lista | OK | |
| `GET /{code}/customers` | clientes do produto | clinte | customers rank | lista | OK | |
| `GET /{code}/purchases` | histórico de compras | compra≠compare | purchases | lista | OK | normalização comprare |
| `GET /{code}/sales` | vendas do produto | | sales | lista | OK | |
| `GET /{code}/sales/open-orders` | carteira pedidos abertos | | open-orders | lista | OK | |
| `GET /{code}/sales/billing` | faturamento do item | faturmento | billing rank | lista | OK | separado de `/sales` |
| `GET /{code}/pricing` | preço do 10080001 | preco, prço | pricing | | OK | |
| `GET /{code}/guide` | roteiro do produto | | guide | | OK | |
| `GET /{code}/inspection` | inspeção do produto | inspecao | inspection | | OK | |
| `GET /{code}/internal-movements` | movimentações internas | movimentac | internal-movements | | OK | |
| `GET /{code}/inbound-invoice-items` | notas de entrada | nfe entrada | inbound | | OK | |
| `GET /{code}/outbound-invoice-items` | notas de saída | nfe saida | outbound | | OK | |

**Erros especulados e soluções**

| Erro | Causa | Solução aplicada |
|------|-------|------------------|
| Comparação pede consultar de novo | `analysis_mode` sem fetch | `ChatStructureComparisonOrchestrationService` |
| Tabela duplicada nível 1 | presenter items antes de markdown | prioridade `root+items` → markdown |
| Busca por grupo vazia | só `description` preenchido | `_extract_search_group_code` |
| «consegue buscar por grupo?» → API vazia | não era capability | `is_capability_inquiry` |
| «grupo 1008» → `/analyser` | `1008` extraído como código de produto | `_is_group_code_numeric_token` + prioridade search |

---

## 2. Engenharia (`/engineering`)

| Rota | Frases teste | Typos | Status | Notas |
|------|--------------|-------|--------|-------|
| `GET /lmps` | listar lmps da semana | | OK | |
| `GET /lmps/dashboard` | dashboard de lmps | | OK | |
| `GET /lmps/dashboard/summary` | kpis do painel lmp | | OK | `_rank_lmp_actions` |
| `GET /lmps/dashboard/items` | itens do dashboard | | OK | `_rank_lmp_actions` |
| `GET /lmps/dashboard/charts` | gráficos lmp | graficos | OK | `_rank_lmp_actions` |
| `GET /lmps/{sale_number}` | detalhe lmp ov 123456 | | OK | OV ≠ código produto |
| `GET /transforma-mais/processes` | processos transforma mais | transforma+ | OK | `_select_transforma_action` |
| `GET /transforma-mais/processes/summary` | resumo transforma mais | | OK | preferência por «resumo» |

---

## 3. Suprimentos (`/supplies`)

| Rota | Frases teste | Typos | Status |
|------|--------------|-------|--------|
| `GET /stock-value` | valor total estoque empresa | estqoue | OK |
| `GET /inventory-turnover` | giro de estoque filial 01 | | OK |
| `GET /cpv` | qual o cpv filial 01 | | OK |
| `GET /otd` | otd de compras | | OK |

---

## 4. Vendas (`/sales`)

| Rota | Frases teste | Status |
|------|--------------|--------|
| `GET /` | listar ordens de venda da semana | OK |

---

## 5. Comercial (`/commercial`)

| Rota | Frases teste | Typos | Status |
|------|--------------|-------|--------|
| `GET /closing-rate` | taxa de conversão de vendas | | OK |
| `GET /rol/series` | série de rol comercial | | OK |
| `GET /sales-order-otd` | otd de pedidos de venda | | OK |
| `GET /new-clients-average` | média de novos clientes | | OK |
| `GET /new-clients-rol-pct` | rol clientes novos | | OK |
| `GET /new-business-rol-pct` | rol novos negócios | | OK |
| `GET /head_office_rol_target_pct` | meta rol matriz | | OK |
| `GET /branch_rol_target_pct` | meta rol filial | | OK |
| `GET /proposals` | propostas comerciais ganhas | propostas | OK |

---

## 6. Financeiro (`/financial`)

| Rota | Frases teste | Typos | Status |
|------|--------------|-------|--------|
| `GET /rol` | rol financeiro | | OK |
| `GET /ebitda_pct` | ebitda do período | ebita→ebitda | OK |
| `GET /fixed_cost_pct` | custo fixo | | OK |
| `GET /pmr` | pmr filial 01 | | OK |

Legado `/finacial/*`: mesmo router; preferir `/financial` no catálogo.

---

## 7. Produção (`/production`)

| Rota | Frases teste | Status |
|------|--------------|--------|
| `GET /on_time_delivery_pct` | otd de produção | OK |
| `GET /overall_equipment_effectiveness_pct` | oee | OK |
| `GET /direct_labor_cost_pct` | mão de obra direta | OK |
| `GET /production_cost_pct` | custo de produção | OK |
| `GET /depreciation_pct` | depreciação | OK |
| `GET /oee/series` | série histórica oee | oee | OK |
| `GET /otd/series` | série histórica otd | | OK |
| `GET /eficiencia-fabril/dashboard` | painel eficiência fabril | eficiencia | OK |
| `GET /eficiencia-fabril/appointments` | apontamentos eficiência | | OK |

---

## 8. RH (`/hr`)

| Rota | Frases teste | Status |
|------|--------------|--------|
| `GET /branches` | filiais rh | filial rh | OK | dept KPI `/hr/branches` |
| `GET /snapshot` | indicadores de rh | OK |
| `GET /active-pdi-count` | pdis ativos | OK |
| `GET /performance-reviews-completion` | avaliações de desempenho | OK |

---

## 9. Qualidade (`/quality`)

| Rota | Frases teste | Typos | Status |
|------|--------------|-------|--------|
| `GET /branches` | filiais qualidade | | OK | dept KPI `/quality/branches` |
| `GET /nonconformities` | listar não conformidades | nao conformidade | OK |
| `GET /nonconformities/series` | série de nc | OK |
| `GET /ppm/internal/summary` | ppm interno | OK |
| `GET /ppm/external/summary` | ppm externo | OK |
| `GET /audit-5s/summary` | auditoria 5s | OK |
| `GET /kaizens/summary` | kaizens | kaisen→kaizen | OK |

---

## 10. Dados (`/data`)

| Rota | Frases teste | Status |
|------|--------------|--------|
| `POST /sql` | execute select top 10... | OK (skill + policy) |

Elaborar SQL sem executar: skill `sqlAuthoring`; não auto-action.

---

## 11. Sistema (`/system`)

| Rota | Frases teste | Status |
|------|--------------|--------|
| `GET /tables/search` | buscar tabela cliente | buscar tabela | OK | `_select_system_metadata_action` |
| `GET /tables/{name}/columns` | colunas da tabela SB1 | colunas da tabela | OK | extrai `tableName` |
| `GET /columns/search` | buscar coluna preço | | OK | dept KPI + system rank |
| `GET /tables/{name}/indexes` | índices da tabela | | OK | |
| `GET /tables/{name}/relations` | relações da tabela | | OK | |
| `GET /tables/{name}/schema` | schema completo SB1 | schema | OK | |

---

## 12. Transversal (chat base)

| Tema | Testes | Status |
|------|--------|--------|
| Capacidades gerais | `test_chat_capabilities_service` | OK |
| Pergunta «consegue X?» | capability inquiry + skip tools | OK |
| Base global agentes | `companyKnowledge` default true | OK |
| Documento >50k chars | `KNOWLEDGE_DOCUMENT_MAX_CHARS=2M` | OK |
| Regressão seleção | `test_chat_intelligence_regression` | OK |
| Regressão KPI dept | `test_chat_department_kpi_intent_service` | OK |
| Typos normalização | `test_chat_message_normalization_service` | OK |
| Utility direct (hora/data) | `test_chat_utility_direct_answer_service` | OK |
| Rótulos api-delpi | `test_chat_action_label_service` | OK (~84 rotas) |
| Admin timings | `adminDebug.intelligence.timings` | OK |

---

## Plano de testes automatizados

```bash
# Pacote inteligência + ingestão (última execução: 83 passed, 2026-05-27)
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_intelligence_regression.py \
  tests/unit/domain/services/test_chat_department_kpi_intent_service.py \
  tests/unit/application/services/test_external_action_selection_service.py \
  tests/unit/application/services/test_chat_structure_comparison_service.py \
  tests/unit/application/services/test_chat_capabilities_service.py \
  tests/unit/application/use_cases/test_ingest_knowledge_document_use_case.py \
  tests/unit/domain/services/test_chat_message_normalization_service.py \
  -q
```

### Casos de regressão adicionados (onda auditoria)

| Mensagem (amostra) | Rota esperada | Typos cobertos |
|--------------------|---------------|----------------|
| liste produtos do grupo MP | `/products/search?group_code=MP` | — |
| qual o ebitda do último trimestre | `/financial/ebitda_pct` | ebita→ebitda |
| taxa de conversão de vendas | `/commercial/closing-rate` | — |
| resumo de kaizens do mês | `/quality/kaizens/summary` | kaisen→kaizen |
| oee da produção | `/production/overall_equipment_effectiveness_pct` | — |
| resumo do produto 10080047 | `/products/{code}/summary` | — |
| ficha completa do produto 10080047 | `/products/{code}/analyser` | — |
| faturamento do produto 10080047 | `/products/{code}/sales/billing` | — |
| kpis do painel de LMPs | `/engineering/lmps/dashboard/summary` | — |
| processos do transforma mais | `/engineering/transforma-mais/processes` | — |
| colunas da tabela SB1 | `/system/tables/{tableName}/columns` | — |
| pmr da filial 02 | `/financial/pmr?branch=02` | — |

---

## Histórico de ondas

| Data | Commit | Escopo |
|------|--------|--------|
| 2026-05-27 | `2ad2b463` | Base global agentes |
| 2026-05-27 | `e9fbbaf6` | Comparação estruturas + fetch API |
| 2026-05-27 | `1359aac4` | Capabilities inquiry |
| 2026-05-27 | `223c8438` | Limite documento 2M chars |
| 2026-05-27 | `e1a99363` | Auditoria rotas: KPI dept, summary/analyser, billing, LMP dashboard, Transforma+, sistema Protheus, roadmap |
| 2026-05-27 | `9895bd43` | Fix: «grupo 1008» → `/products/search`, não `/analyser` |

---

## Próximos passos (backlog)

Itens 1–5 abaixo foram entregues na **Onda 11** — ver [inteligencia-chat-onda-11-paridade-assistentes.md](./inteligencia-chat-onda-11-paridade-assistentes.md).

1. ~~Parâmetros de data automáticos~~ — ✅ 11.1.2
2. ~~Heurística explícita summary vs analyser~~ — ✅ 11.1.3
3. ~~Montar rotas NC PostgreSQL e importar no catálogo~~ — ✅ **11.6** (heurísticas + `api_paths.json`; sync OpenAPI quando api-delpi habilitada)
4. Testes E2E com api-delpi mockada por domínio — **backlog**
5. ~~Expor `knowledgeDocumentMaxChars` em capabilities~~ — ✅ 11.5.2

**Próxima onda de produto:** [Onda 12 — drawing-analyser PDF](./inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md).
