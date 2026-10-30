# CAIO 3.0 — Inventário P0: fontes, perguntas de referência e baseline

> Artefato canônico da etapa P0 da trilha [CAIO-3-0-EXECUTION-TRAIL.md](CAIO-3-0-EXECUTION-TRAIL.md).
> **Data:** 2026-10-30 · **Owner:** commercial-api · **Base:** `main b453b0981c`.
> Distinção obrigatória: `CURRENT` (comprovado), `PROPOSED`, `TO_INVENTORY`, `PENDING`.

## 1. Corpus de conhecimento — inventário auditável

Fonte: `commercial-api/commercial_app/content/caio_commercial_knowledge.json` v2.0 — 16 tópicos ativos + 1 planned.

| Tópico | Fonte canônica citada | Cobertura | Status |
|---|---|---|---|
| `caio.usage` | IMPLEMENTATION_PLAN + interface/mcp | operação da superfície semântica | CURRENT |
| `caio.tool_map` | semantic_registry.py | mapa entidade→ações | CURRENT |
| `commercial.glossary` | contratos commercial-api | conceitos carteira/pedidos/propostas/ROL | CURRENT |
| `commercial.portfolio_governance` | seller_portfolio_routes + use case | governança de carteiras | CURRENT |
| `commercial.worklist_process` | worklist_routes + use case | worklist e follow-ups | CURRENT |
| `commercial.interaction_rooms` | interaction_room_routes + use cases | salas/mensagens/menções | CURRENT |
| `commercial.indicators` | analytics_routes + gateway | indicadores e análises | CURRENT |
| `commercial.scope_semantics` | totvs_bff_helpers | escopo de carteira | CURRENT |
| `commercial.permissions` | commercial_permissions | permissões efetivas | CURRENT |
| `commercial.integrations` | delpi_commercial_gateway + helpers | integrações/proveniência/handoff binário | CURRENT |
| `commercial.delete_governance` | proposal_store | prepare/commit selado | CURRENT |
| `commercial.honest_states` | semantic_bridge error mapping | estados honestos | CURRENT |
| `commercial.processes` | Portal + use cases | cadeias multi-etapa | CURRENT |
| `commercial.proposals` | API-ROUTES §4.2 + api-delpi | propostas, branch/revision, document_url | CURRENT |
| `commercial.otd` | KPI-FICHAS §KPI-OTD + api-delpi | pontualidade de entrega | CURRENT |
| `commercial.production` | BFF produção api-delpi | OPs e dados de fábrica | CURRENT |
| `products.guide` | — | — | PLANNED (honesto) |

**Lacunas comprovadas (vs. visão 3.0):** métodos comerciais profissionais (ABC/RFV/funil/5 Porquês…), roteiros de diagnóstico, seleção contextual de conhecimento, pesquisa externa, métodos B2B/processos — nenhum presente → `P1`–`P5`.

## 2. Contrato de contexto efetivo — o que o CAIO realmente recebe

**Comprovado em código (`semantic_bridge.tool_knowledge`):** a tool `knowledge` recebe `topic` (obrigatório), `task` e `query` (opcionais, hoje apenas ecoados na resposta). O MCP **não** recebe histórico da conversa do ChatGPT, não possui memória persistente, não possui buscador web e não possui RAG. Toda seleção contextual deve operar sobre `topic`/`query`/`task` explicitamente passados — ou ser implementada como extensão dessa superfície existente (P3), sem presumir poderes do host.

**Autorização:** `knowledge` exige principal humano + `commercial.access` (mesmo gate das rotas REST). Todo o corpus é classificado `internal` (a mesma classe de acesso das demais tools) — não há vazamento cross-user porque a seleção não carrega dados de carteira; carrega apenas orientação versionada.

## 3. Perguntas de referência (baseline reproduzível)

Conjunto usado para medir adequação metodológica em P1–P5:

| # | Pergunta de referência | Comportamento esperado |
|---|---|---|
| Q1 | "Analise os últimos 90 dias da situação comercial" | roteiro diagnóstico executivo + indicadores oficiais |
| Q2 | "Quais clientes pararam de comprar ou reduziram?" | método de retração/RFV + roteiro clientes em retração |
| Q3 | "Quais pedidos estão em risco de entrega?" | roteiro saúde de pedidos + OTD + produção |
| Q4 | "Estou batendo a meta? Onde está o desvio?" | método desvio meta×realizado + indicadores owner |
| Q5 | "Como está o funil de propostas?" | método funil/conversão + propostas/oportunidades |
| Q6 | "Por que as vendas do cliente X caíram?" | 5 Porquês/Ishikawa como investigação de hipóteses |
| Q7 | "Quais clientes concentram o faturamento?" | ABC/Pareto + billing series |
| Q8 | "Como funciona a exclusão de uma carteira?" | `commercial.delete_governance` (já CURRENT) |
| Q9 | "Qual o melhor método para qualificar uma oportunidade?" | SPIN/MEDDPICC como referência externa (P5) |
| Q10 | "Qual é a política DELPI para SPIN?" | honesto: método externo ≠ regra DELPI |

**Rubrica por resposta:** fato oficial correto · fonte citada · método pertinente · hipótese vs fato separados · autorização/escopo respeitados · próximo passo útil · honestidade de lacuna. Sem resposta de método para dados que não existem; sem promessa de precisão de forecast.

## 4. Baseline de testes (anterior a P1)

- Suíte CAIO: **656 passed / 58 skipped** (`b453b0981c`).
- commercial-api: **1224 passed / 3 failed** — falhas baseline preexistentes fora do escopo.
- `knowledge`: recuperação exata por `topic` — 16 tópicos com `source`+`guidance`; tópico desconhecido → 404 com lista; planned → 501 honesto.

## 5. Lacunas → etapas

| Lacuna | Etapa | Estado |
|---|---|---|
| Biblioteca de métodos comerciais tipada | P1 | TO_INVENTORY → implementado P1 |
| Roteiros de diagnóstico | P2 | implementado P2 |
| Seleção contextual por `query` | P3 | implementado P3 |
| Conector/buscador externo autorizado | P4 | verificado: **inexistente** → `BLOCKED_EXTERNAL` |
| Métodos B2B/processos + validação de negócio | P5 | implementado como referência externa; `PENDING_BUSINESS_VALIDATION` |
