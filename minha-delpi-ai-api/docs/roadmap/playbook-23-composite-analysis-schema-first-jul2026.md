# Playbook 23 — Inteligência de dados compostos no chat base (`composite_analysis`)

**Status:** implementado (jul/2026) — factory-status, cost-impact-simulation; genérico por shape
**Público:** backend chat, MFE, agentes Cursor, revisores de PR
**Depende de:** [playbook-22-schema-first-api-actions-jun2026.md](./playbook-22-schema-first-api-actions-jun2026.md) · [presentation-delivered-pure-jun2026.md](../architecture/presentation-delivered-pure-jun2026.md)

---

## 1. Objetivo e princípio

Dar ao **pipeline de apresentação do chat base** inteligência para interpretar a **forma** dos dados que recebe quando o payload é **multi-seção** (shape `composite_analysis`: factory-status, analyser e futuros) e materializar automaticamente **KPI + tabelas por seção + árvore (BOM) + dashboard**, de forma **genérica e dirigida por `meta.shape` / `meta.sections`** — sem presenter por rota.

Como a inteligência vive no **chat base**, todo **agente herda** (princípio `chat-intelligence-base.mdc`): qualquer rota que devolva `composite_analysis` ganha apresentação rica sem código novo.

## 2. Diagnóstico (validado jul/2026)

- O commit `1322970f3` (24/jun/2026) removeu `product_composite_analysis_presenter.py` (654 linhas) na migração Playbook 22 e **não** reimplementou o shape `composite_analysis` no caminho schema-first.
- `ChatSchemaDrivenPresentationService.build_bundle` chama `extract_tabular_rows(root)`, que só encontra **um** array `items` na raiz. No composite os dados estão em `structure` / `raw_material_stock` / `production` / `shipping` → retorna 0 → sem tabela/árvore/KPI/dashboard.
- Resultado: `availableFormats: ['text']` → delivered-pure zera o markdown → sobra só a narrativa do LLM.

Reprodução:

```python
# factory-status → availableFormats: ['text'] | kpi/dashboard/tree/tables ausentes
uc._build_presentation_metadata(action={'path': '/products/90269002/factory-status'}, sanitized_data=env, ...)
```

## 3. Conformidade com diretrizes `.cursor`

| Diretriz | Cumprimento |
|---|---|
| `schema-first-presentation-delivered.mdc` | Sem `*_presenter.py` por rota, sem `visualBuilders`/`tableAssembly`. Lógica composta em `ChatSchemaDrivenPresentationService`, dirigida por `meta.shape`/`meta.sections` — genérica. |
| `chat-intelligence-base.mdc` | Inteligência transversal no chat base; agentes herdam; nada no prompt do agente. |
| `centralized-rules-first.mdc` | Uma fonte de verdade; sem duplicar em `Send*`/`Stream*`. |
| `presentation-operational-decoupling.mdc` | `dataAnswer`/comentário via `ChatDataInsightEnrichmentService`; MFE render-only; nada no markdown das tabelas. |
| `assistant-content-json.mdc` | Títulos, roles, políticas em `presentation_profiles.json`/`presenter_content.json`/`column_labels.json`. Python só lógica. |
| `clean-architecture-chat-api.mdc` | `domain/services`; sem import de infra; use case inalterado. |
| `test-and-commit.mdc` | Testes com fixture real + gates. |

### Tensão resolvida
O delivered-pure prega *"uma tabela genérica + dataAnswer"* e *"stack só com «visão integrada»"* — isso vale para **listas simples**. Para `composite_analysis`, a apresentação **genérica correta É multi-seção**, pois a semântica do payload é uma análise integrada. Continua alinhado por ser **dirigido por shape, genérico e sem acoplamento por rota**. Formaliza-se em `openapiShapeDefaults.composite_analysis` (`stackLayoutPolicy: on_demand` → `always`).

## 4. Arquitetura

```text
build_bundle(host, data, path, entity, shape, sections)
  ├─ shape == composite_analysis (ou >1 seção detectada):
  │    build_composite_bundle(...)
  │      ├─ _resolve_composite_sections(root, sections_meta)  # meta.sections → fallback sub-objetos com items
  │      ├─ por seção → build_table (role por seção)
  │      ├─ seção estrutura → build_tree (BOM)
  │      ├─ KPI de indicators/summaries (ChatPresentationKpiAssemblyService)
  │      └─ dashboard = ChatDashboardPresentationService.build(kpi, tree, tables)
  └─ senão: caminho array-único atual (inalterado)
→ ChatDataInsightEnrichmentService (dataAnswer)
→ ChatPresentationDecisionService (layoutMode=stack p/ composite)
→ finalize → data-only
```

## 5. Fases

### Fase A — Detecção genérica de seções
- `ChatSchemaDrivenPresentationService._resolve_composite_sections(root, sections_meta)`: preferir `meta.sections` (key+label+itemCount); fallback iterar `root` por sub-objetos `{items, summary}`.
- `build_bundle` ganha params opcionais `shape` e `sections` (default = comportamento atual → zero regressão).
- `ChatPresentationApiDeliveredMetadataService.build` propaga `shape`/`sections` do envelope `meta`.

### Fase B — Builders por seção (reuso)
- Tabelas: reuso de `build_table` / `host._build_items_table` por seção; `role` de config.
- Árvore: reuso de `build_tree` (estrutura BOM já suportada por `ChatProductStructurePresentationService`).
- KPI: cards de `indicators` + summaries via `ChatPresentationKpiAssemblyService`.
- Dashboard: `ChatDashboardPresentationService.build(...)`.
- `SchemaPresentationBundle` estendido (ou `CompositePresentationBundle` com `tables: list`, `kpi`, `tree`, `dashboard`).

### Fase C — Slots + decisão
- Popular `kpiPresentation`, `treePresentation`, `tablePresentations`, `dashboardPresentation`, `availableFormats`.
- Decisão: `layoutMode=stack`, `stackPresentationPlan.tailVisualOrder=['dashboard']`, `humanizedSections=True` (por shape/perfil).

### Fase D — Config declarativa (JSON)
- `presentation_profiles.json` → `openapiShapeDefaults.composite_analysis`: `stackLayoutPolicy: always`, `sectionRoles` (`structure→profile`, `raw_material_stock→list`, `production→detail`, `shipping→detail`).
- `presenter_content.json` → títulos de seção (recuperar do presenter removido via git).
- `column_labels.json` → rótulos por seção (preferir `meta.fields`).

### Fase E — Comentário / dataAnswer
- Manter `ChatDataInsightEnrichmentService` + builders de commentary do factory (já corrigido o bug "exclusiva"×"sem estoque") produzindo `dataAnswer`/`dataCommentary`; sem repetir fatos no markdown.

### Fase F — Testes e gates
- Portar/reativar `test_presentation_response_quality.py` (factory): `kpiPresentation.type == kpi`, `dashboardPresentation.type == dashboard`, `tablePresentations`, `tailVisualOrder == ['dashboard']`, markdown com fatos.
- Novo teste em `test_chat_schema_driven_presentation_service.py`: `build_composite_bundle` com fixture real.
- Cobrir analyser (2º caso composite) para provar generalidade.
- Gates: `audit_presentation_coverage.py --check-profiles`, `audit_openapi_profile_pruning.py --check`, `generate_operational_route_registry.py --check`.

## 6. Guardrails / riscos

- Params novos de `build_bundle` são opt-in (default = atual) → zero regressão em shapes simples.
- Grep zero: `product_composite_analysis_presenter`, `visual_bundle`, `table_assembly`.
- Nenhum texto/limite/role mágico em Python — tudo em JSON.
- Coleção de testes quebrada pré-existente (módulos removidos no `1322970f3`) não é escopo; rodar com alvo específico.

## 7. Definition of Done

- factory-status e analyser retornam dashboard/tabelas/árvore/KPI, `layoutMode: stack`, markdown com fatos e `dataAnswer` coerente.
- Comportamento genérico por shape (novo `composite_analysis` funciona sem código novo).
- Testes de qualidade + gates verdes; sem novos desvios de arquitetura.

## 8. Generalização por composto agregado (cost-impact-simulation)

Nem todo `composite_analysis` tem seções `structure/stock/production`. O `cost-impact-simulation` expõe **um ranking** (`materials.items`) + **métricas agregadas no root** (`summary`, `simulation`), sem seções aninhadas com `summary`. Sem tratamento, ele caía em tabela genérica sem KPI ("Foram retornados N registros. Total de rank: 15").

Ajustes **genéricos** (servem a qualquer composto agregado futuro):

| Ponto | Mudança |
|---|---|
| `ChatSchemaDrivenPresentationService._build_composite_kpi` | Além dos `summary` aninhados por seção, passa a ler `summary` / `simulation` / `indicators` no **root** (campos escalares) como fonte de cards. |
| `ChatSchemaDrivenPresentationService._build_composite_text` | Quando o `routeNamespace` não produz linhas (dados não têm as seções factory), cai em **lead genérico** (`_build_generic_composite_text`: produto + seções analisadas). |
| `presenter_content.json` → `compositeAnalysis` | Cards de custo (`total_material_cost`, `pa_standard_cost`, `top_material_impact_percent`, `projected_cost_delta`, `adjustment_percent`, …), `sectionRoles`/`sectionLabels` para `materials`, e templates `genericNarrative`. |
| `presentation_profiles.json` → `cost_impact_simulation` | `stackLayoutPolicy: always` + `proseDelivery: template` (consistente com `factory_status`), para stack rico com lead preservado. |

Unidade dos cards inferida por `ChatPresentationKpiAssemblyService` (`R$` → currency, `%` → percent) — sem formatação hardcoded.

## 9. Validação com produtos reais (jul/2026)

Testado ao vivo (api-delpi + pipeline de apresentação) com produtos em produção, comparando os componentes gerados **linha a linha** contra a fonte crua:

| Rota / playbook | Produto | Resultado |
|---|---|---|
| `factory-status` (visão/status) | `90261299` | Stack: KPI (8 cards), dashboard (5 painéis), árvore BOM (12 nós, 0 ausentes/`unknown`), 3 tabelas. Contagens KPI batem com a fonte (11 comp., 7 MP, 0 exclusivas, 3 OPs PA). |
| `production-status` (situação de produção) | `90261299` | Tabela + veredito factual coerente com SH6010. |
| `cost-impact-simulation` (simulador de custos) | `90261255` | Stack: lead + KPI de custo + ranking Pareto. Custo materiais R$ 49.598,35 e maior impacto 58,74% batem com a MP #1 (10000×2,9133=29.133). Simulação +10% ok. |
| Operacionais (`consumption/top-items`, `purchases/top-products`, `losses/top-materials`, `schedule/today`, `orders/open`) | dados reais | Tabela + avisos de cobertura corretos (truncamento, consolidado por filial). |

Árvore BOM confere código (label) + descrição (subtitle) + tipo PA/PI/MP (badge) + unidade/quantidade (meta). O nó `unknown` observado antes era artefato de fixture esparso; com dados reais os componentes vêm completos.

## 10. Histórico

| Data | Evento |
|---|---|
| jul/2026 | Correção do bug factual "MP exclusiva × sem estoque" no factory-status (`presenter_content.json`). |
| jul/2026 | Diagnóstico: `composite_analysis` perdeu apresentação rica no `1322970f3`; plano de reconstrução schema-first (este playbook). |
| jul/2026 | Implementação schema-first do composto (factory-status): KPI + tabelas + árvore + dashboard + stack. |
| jul/2026 | Generalização para composto agregado (cost-impact-simulation): KPI de `summary` no root + lead genérico + perfil `always`/`template`. Validado com produtos reais. |
