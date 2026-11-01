# 27 — VISTA DESIGN INTELLIGENCE — DI-0 DISCOVERY & GAP ANALYSIS REPORT

**Data:** 2026-10-31 · **HEAD:** `2f9eb7c33` (= origin/main)
**Escopo:** inventário puro — sem código novo, sem deploy, sem tools novas.

## Descoberta central — inteligência já existente (maior que o assumido)

O mandato DI-0 referenciava os 11 tópicos históricos de Knowledge. O
HEAD revela uma camada de inteligência **muito mais rica** — já
implementada:

### `tv_app/content/design_intelligence.json` — `EXISTING`

- `componentSpecs` — especificações por componente visual.
- `designMethodology` — metodologia de decisão de design.

### `tv_app/content/vista_agent_intelligence.json` — `EXISTING`

Chaves inspecionadas (16+):

- `persona`, `narrative`, `story` — identidade da especialista.
- `actions_runtime` — catálogo de ações.
- `knowledge_orchestration` — **`principle`, `sources`, `precedence`,
  `routing`, `gates`, `composition_order`, `sufficiency`,
  `gap_handling`, `epistemology`, `forbidden`** — orquestração de
  conhecimento já com regras de precedência, suficiência e
  tratamento de lacuna.
- `design_intelligence` — referência ao design_intelligence.json.
- `visual_selection` — critérios de escolha de visual.
- `shape_chrome` — chrome/estrutura de shapes.
- `composed_visuals` — composição de visuais múltiplos.
- `visual_impact` — impacto/avaliação visual.
- `object_resolution` — resolução de objetos por nome/referência.
- `playlist_curation` — curadoria de playlist (ordem, rotação).
- `branch_scope`, `filter_layering`, `param_expressions` —
  escopo/filtros/parametrização.
- `execution_posture`, `continuous_review` — postura e revisão.

### `vista_agent_intelligence_service.py` — `EXISTING`

Serviço de aplicação que expõe a orquestração: `persona_context`,
`version`, `catalog` (via `PresentationRecipeService.
catalog_projection_for_actions`), `authority`, `execution_posture`,
`knowledge_orchestration`, `actions_runtime`, `character`,
`continuous_review`, `visual_impact`, `visual_selection`,
`composed_visuals`, `shape_chrome`, `object_resolution`,
`editor_focus`, `playlist_curation` — projeção para actions.

### `tv_app/domain/presentation_intelligence/` — `EXISTING`

`models.py` com `kpi_options_patch` e modelos de inteligência de
apresentação — **domínio já possui raciocínio de KPI/visual**.

## Estado atual — classificação honesta

| Dimensão | Estado | Evidência |
|---|---|---|
| Conhecimento **descritivo** (como funciona) | `PROVEN` | 11 tópicos + intelligence JSON rico |
| Conhecimento **prescritivo** (quando/como escolher) | `PARTIALLY_SUPPORTED` | `visual_selection`, `composition_order`, `designMethodology` existem — profundidade não auditada tópico a tópico |
| Conhecimento **avaliativo** (é adequado?) | `TO_INVENTORY` | `visual_impact`, `continuous_review` existem — não há rubrica objetiva de qualidade de dashboard |
| Componentes de painel | `PROVEN` parcial | `componentSpecs` existe + block types do renderer — inventário detalhado por componente não feito nesta onda |
| Pipeline intent→compose | `PROVEN` parcial | `knowledge_orchestration.composition_order` + `analyze.intent_materialization` (existente) |
| Design system DELPI | `TO_INVENTORY` | `design_intelligence.json.componentSpecs` — tokens/tipografia/grid não auditados nesta onda |
| Indicadores de negócio | `TO_INVENTORY` | `playlist_curation` + `kpi_options_patch` existem; catálogo de indicadores por domínio (OEE, qualidade etc.) não encontrado |

## Matriz de lacunas (preliminar)

| Capability | Estado | Gap | Prioridade |
|---|---|---|---|
| Knowledge prescritivo profissional (princípios DV/UX/signage) | PARTIAL | conhecimento existe mas não auditado por profundidade/completude | P1 |
| Rubrica objetiva de qualidade de dashboard (legibilidade, densidade, hierarquia) | TO_INVENTORY | `visual_impact` existe; critérios mensuráveis a definir | P1 |
| Catálogo de indicadores por domínio (owner-definido) | TO_INVENTORY | não é VISTA decidir fórmulas — requer owner de dados | P2 |
| Design tokens DELPI canônicos | TO_INVENTORY | verificar se componentSpecs cobrem | P1 |
| Autonomous authoring E2E (NL → preview → prepare → commit) | PARTIAL | `composition_order` + `intent_materialization` existem; E2E não certificado | P1 |
| Verificação visual autoritativa (screenshot/diff paridade) | TO_INVENTORY | `visual_verification` tópico existe; motor de verificação a confirmar | P2 |

## Referências profissionais (fontes primárias — não avaliadas por conteúdo nesta onda)

| Fonte | Aplicabilidade |
|---|---|
| Microsoft Power BI design guidance | layout, hierarquia, escolha de visual |
| Tableau visual best practices | chart selection, cores, densidade |
| Grafana dashboard guidelines | painéis operacionais, alertas, distância |
| W3C WCAG contrast | legibilidade/acessibilidade |
| Few, "Information Dashboard Design" | literatura referência DV/indicadores |
| Knaflic, "Storytelling with Data" | narrativa executiva vs operacional |

**Nota:** recomendações BI desktop não se traduzem automaticamente
para TV industrial 1080p/4K a distância — a camada `digital_signage`
é o diferencial a desenvolver (legibilidade, tempo de leitura, rotação).

## Roadmap proposto (hipóteses — sem implementação autorizada)

| Onda | Goal | Reuse decision |
|---|---|---|
| **DI-1** Knowledge profissional | auditar/expandir `vista_agent_intelligence.json` + `design_intelligence.json` com princípios DV/UX/signage verificados | EXTEND (mecanismo já existe) |
| **DI-2** Design reasoning | aprofundar `visual_selection`/`composition_order` com critérios por tipo de indicador/pergunta | EXTEND |
| **DI-3** Composição assistida | E2E `analyze.intent_materialization` → proposta com componentes suportados → preview | EXTEND |
| **DI-4** Quality verification | rubrica objetiva + `visual_impact`/`continuous_review` | EXTEND |
| **DI-5** Governed authoring | NL → proposta → prepare → consent → commit → verify | EXTEND (seis verbos + A5 existentes) |

**Nenhuma onda exige nova tool MCP ou GPT Action** — a orquestração
existe; evolução é de conteúdo/critério dentro dos seis verbos.

## Veredito

**`DI0_INVENTORY_PARTIAL`** — a camada de inteligência é significativamente
mais desenvolvida que o baseline assumido pelo mandato; o que falta
é auditoria tópico-a-tópico de profundidade (prescritivo vs descritivo
vs avaliativo), rubrica de qualidade objetiva, catálogo de indicadores
por domínio (owner de dados) e certificação do pipeline de authoring
E2E. Recomendação: **extensão do mecanismo existente** — zero registry
ou engine novo indicado pelo inventário.
