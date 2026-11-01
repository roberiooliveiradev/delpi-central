# 29 — VISTA DESIGN INTELLIGENCE — DI-0.2 AUTONOMOUS DESIGN BENCHMARK & COMPONENT MAPPING

**Data:** 2026-10-31 · **HEAD:** `d5ab0d7b47` (doc 28)
**Escopo:** diagnóstico executável — benchmark real via `DesignIntelligenceService`
(read-only, sem mutations). Sem código novo, sem deploy, sem tools.

## Consumo real confirmado — `SERVICE_TESTED`

`DesignIntelligenceService` invocado diretamente (read-only):
`semantic_digest` + `visual_recommendation` + `design_intent_for_message`
— nenhum efeito persistente, nenhuma credencial externa.

## Inventário de componentes — `componentSpecs` (13)

`heading`, `text`, `shape`, `icon`, `image`, `kpi_view`, `data_kpi`,
`chart_view`, `data_chart`, `table_view`, `data_table`, `canvas_table`,
`input` — reais no `design_intelligence.json` do HEAD.

## Benchmark A–E — `design_intent_for_message`

| Cenário | Mensagem | Resultado |
|---|---|---|
| A — Produção | "eficiência da produção + problemas" | `IMPROVE_EXISTING` |
| B — Estoque | "produtos atenção estoque" | `None` |
| C — Comercial | "vendas + metas" | `None` |
| D — Qualidade | "problemas qualidade + evolução" | `None` |
| E — Gestão | "situação geral operações" | `None` |

**DG-7 — intent classification keyword-narrow:** só A classificado.
B–E produzem `None` → sem roteamento de intent — `DESIGN_REASONING_GAP`.

## Bateria de escolhas visuais — 7 casos executados

`semantic_digest(rows)` → `visual_recommendation(digest)`:

| Caso | Dados | Recomendação | Avaliação |
|---|---|---|---|
| comparação | linha×qty (2 cat) | **doughnut** | subótimo (bar é alternativa correta) |
| temporal | dia×qty (2 rows) | **doughnut** | **FAIL** — regra correta `line` existe mas `temporal` não foi detectado |
| meta | nome×real×meta | **gauge** | PASS |
| ranking | 3 produtos×alerta | **doughnut** | subótimo (cardinalidade 3 < 4 → caiu em composition; horizontal_bar é a regra correta para ranking) |
| distribuição | faixa×qtd | **doughnut** | aceitável (composição de faixas) |
| estado | maquina×status | **table_view** | PASS (sem métrica → listing honesto) |
| detalhe | cod×desc×qtd×valor | **doughnut** | subótimo (detail listing deveria ser table) |

## Root cause — `DESIGN_REASONING_GAP` (camada de digest, não de regra)

`_recommend` tem regras corretas (`temporal→line`, `goal→gauge`,
`ranking>4→horizontal_bar`, `composition→doughnut`, `no-metric→table`).

O bug está em `semantic_digest`/`_role_for` — **role detection estreita**:

- `temporal` caso: `"dia"` não estava em `_TEMPORAL_KEYS` → role
  "dimension"/"category" → `composition` → doughnut (a regra correta
  `line` nunca disparou).
- `ranking` caso: cardinalidade 3 < 4 → `composition` → doughnut
  (ranking com poucos itens não reconhecido como ranking).
- `detalhe` caso: múltiplas métricas + dims → composition → doughnut
  (listing detalhado não distinguido de composição).
- `estado`: PASS — listing honesto para shapeless strings (comentário
  no código confirma intent explícito de "nunca fabricar gráfico
  categórico em dados sem forma").

## Rubrica Q1–Q10 — evidência parcial

`design_audit` existe (`PROVEN` N4) mas a bateria não exercitou um
painel real de ponta a ponta — Q-avaliação por cenário `NOT_EVALUABLE`
sem E2E de authoring.

## Limitações reais — mapa

| Bloqueio | Tipo | Root cause | Reuse |
|---|---|---|---|
| DG-7 intent não classificado (B–E) | **B — Raciocínio** | `design_intent_for_message` keyword-narrow | EXTEND |
| DG-8 role detection incompleta | **B — Raciocínio** | `_role_for`/`_TEMPORAL_KEYS` + ranking<4 + detail listing | EXTEND `semantic_digest` |
| DG-9 composição E2E não certificada | **G — Experiência** | benchmark authoring E2E não executável sem mutations | EXTEND |
| DG-3 indicadores por domínio | **C — Dados** | owner `api-delpi` | owner contract |
| DG-6 visual verification motor | **F — Verificação** | `visual_verification` existe; screenshot/diff TO_INVENTORY | EXTEND |

## Roadmap revisado — evidência muda decisões

| Onda | DI-0.1 | DI-0.2 | Motivo |
|---|---|---|---|
| DI-1 Knowledge profissional | GO_WITH_PREREQ | **GO** | conteúdo existe, precisa auditoria+extensão |
| DI-2 Design reasoning | HOLD | **GO** | DG-7+DG-8 comprovados — falhas reais em digest/intent |
| DI-3 Composição assistida | GO_WITH_PREREQ | **GO_WITH_PREREQUISITES** | precisa DI-2 corrigir escolhas primeiro |
| DI-4 Quality verification | GO | **GO** | `design_audit` base sólida |
| DI-5 Governed authoring | GO_WITH_PREREQ | **HOLD** | precisa DI-3 primeiro |

**Primeira implementação recomendada: DI-2** — falhas comprovadas de
role detection (DG-8) e intent (DG-7) são o gargalo que impede
recomendações corretas; ambas são `EXTEND` em código existente
(`semantic_digest` + `design_intent_for_message`), não engines novas.

## Veredito

**`DI02_BENCHMARK_PARTIAL`** — benchmark executado por `SERVICE_TESTED`
(visual_recommendation + design_intent, sem mutations prod); lacunas
comprovadas (DG-7 intent narrow, DG-8 role detection, DG-9 E2E não
certificado); authoring E2E permanece `NOT_EXECUTABLE_IN_CURRENT_ENVIRONMENT`
(sem mutations de produção permitidas nesta fase).
