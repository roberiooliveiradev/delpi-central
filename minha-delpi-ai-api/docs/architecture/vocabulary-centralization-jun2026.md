# Centralização de vocabulário e narrativa SQL — jun/2026

**Status:** entregue (commits `b8b06933` … `403e7fc0`)  
**Público:** desenvolvimento `minha-delpi-ai-api`  
**Regra Cursor:** `.cursor/rules/assistant-content-json.mdc`, `centralized-rules-first.mdc`

---

## Objetivo

Substituir **listas e frases PT** espalhadas em constantes `_TERMS`, `_PHRASES` e strings literais nos serviços Python por **bundles JSON reutilizáveis**, carregados via loaders finos (`*VocabularyService` / `*ContentService`).

Benefícios:

- Uma única fonte de termos compartilhados (ex.: «consulta anterior», «agrupar por»).
- Manutenção de copy sem tocar lógica de intenção/refinamento.
- Testes de regressão que validam chaves JSON + comportamento canônico.
- Alinhamento com ADR 003/006 (conteúdo do assistente em JSON).

**O que permanece no Python:** regex, expressões SQL, heurísticas numéricas, mapeamentos Protheus técnicos, ordem de roteamento.

---

## Commits (cronologia)

| Hash | Mensagem | Escopo principal |
|------|----------|------------------|
| `b8b06933` | fix(chat): programação de produção por filial na consulta SQL | Breakdown «por filial» SC2010, fast path dispatch, refinamento filial |
| `08432dce` | Centralizar vocabulário SQL/análise/texto em JSON e motor de refinamento por coluna | Bundles `*_vocabulary.json`, `ChatSqlDynamicColumnRefinementService`, testes |
| `437587e2` | Centralizar vocabulário compartilhado e narrativa de produção SQL em JSON | Seção `shared`, loaders base, narrativa SC2010, paginação/sessão/date_range |
| `403e7fc0` | Extrair textos de dashboard, temporal, canvas e web search para JSON | Presenter dashboard, temporal, lousa, web search planning/intent |

**Estatística acumulada (08432dce…403e7fc0):** ~62 arquivos, +4298 / −1512 linhas em `minha-delpi-ai-api/`.

---

## Arquitetura

```text
app/content/pt-BR/assistant/*.json
        ↓
ChatAssistantVocabularyService (base)
  · terms / merge_terms / text / format / synonym_map / node
        ↓
ChatSqlIntentVocabularyService, ChatDateRangeVocabularyService, …
        ↓
Serviços de domínio (ChatSql*, ChatTemporal*, ChatWebSearch*, …)
```

### Classe base

`app/domain/services/chat_assistant_vocabulary_service.py`

| Método | Uso |
|--------|-----|
| `terms(*path)` | Lista de marcadores |
| `merge_terms(*paths)` | Une listas do mesmo bundle sem duplicar |
| `text` / `format` | Template com `{placeholder}` |
| `synonym_map(*path)` | Objeto chave → aliases (colunas dinâmicas) |
| `mapping` / `node` | Estruturas arbitrárias |

### Composição `shared` (SQL)

Em `sql_intent_vocabulary.json`, termos canônicos em `shared.*` são compostos nos loaders:

| Método loader | Composição |
|---------------|------------|
| `incremental_authoring_terms()` | `shared.previousQueryTerms` + `shared.groupByCommandTerms` + `queryRefinement.incrementalAuthoringSpecific` |
| `incremental_edit_terms()` | `shared.previousQueryTerms` + `advancedSqlSpecialist.incrementalEditSpecific` |
| `group_by_terms()` | `shared.groupByCommandTerms` + `shared.groupByExtendedTerms` |
| `filter_prefix_terms()` | `shared.filterPrefixTerms` |
| `column_definitions(table)` | `queryRefinement.columnDefinitions.{SC2010\|SB2010\|SA1010}` |

---

## Bundles JSON criados ou estendidos

| Arquivo | Conteúdo |
|---------|----------|
| `sql_intent_vocabulary.json` | Intenção/refinamento SQL, produção, analisador, especialista, **`shared`**, `columnDefinitions`, `schemaExplore` / `schemaRelations` |
| `analysis_intent_vocabulary.json` | Marcadores de análise/comparação |
| `text_context_vocabulary.json` | Referência anterior, lousa, anexo, `inlineExtractVerbs`, blocos de prompt |
| `date_range_vocabulary.json` | Meses, frases de período, métricas, `weekdaysPt`, `temporalRangeMarkers` |
| `term_extraction_vocabulary.json` | Stopwords e gatilhos de pergunta de definição |
| `session_vocabulary.json` | Marcadores de mudança de assunto (`topicChangeMarkers`) |
| `operational_pipeline_vocabulary.json` | Termos operacionais vs. documentais (fast path) |
| `canvas_transform_vocabulary.json` | Termos por tipo de transformação na lousa + templates |
| `external_action_responses.json` | `productionSchedule.narrative`, `sqlQueryRefinement.*`, `sqlColumnRefinement.*` |
| `presenter_content.json` | `dashboardPresentation`, `presentationRecommendation` |
| `tool_context.json` | Paginação (`fullFetchTerms`, `continueTerms`, `yesOnlyTerms`), `presentation.queryCompleted` |
| `operational_parameters.json` | `productContextTerms` |
| `web_search.json` | `explicitRequest`, `planning` (deep/quick/official) |

Catálogo completo: [`assistant-content-catalog.md`](./assistant-content-catalog.md).

---

## Funcionalidades de chat base entregues

### 1. Programação de produção SQL (SC2010)

| Peça | Serviço / JSON |
|------|----------------|
| Fast path «produzidos hoje / programados para produzir» | `ChatSqlProductionQueryService`, `ChatSqlOperationalIntentService` |
| Breakdown «por filial» | `expand_production_sql_by_branch`, vocabulário `productionQuery.branchBreakdownTerms` |
| Refinamento multi-turn filial | `ChatSqlQueryRefinementService` + dispatch antes de refinamento genérico |
| Narrativa enriquecida (não só contagem) | `ChatSqlProductionSchedulePresentationService` → `productionSchedule.narrative` |
| Presenter SQL | `sql_presenter.py` monta `linhas` via serviço de narrativa |
| Direct answer | `ChatExternalActionDirectAnswerService` usa `linhas` quando não são só contagem genérica |

Frase «programados para produzir» adicionada em `operationalIntent.productionPhrases`.

### 2. Motor de refinamento dinâmico por coluna

`ChatSqlDynamicColumnRefinementService` — agrupar/filtrar por coluna do SELECT ativo.

- Integrado em `ChatSqlQueryRefinementService.resolve()` **antes** do breakdown filial SC2010.
- Sinônimos de coluna em `dynamicColumnRefinement.columnSynonyms`.
- Textos de `reason` em `external_action_responses.json` → `sqlColumnRefinement`.
- **48+** testes em `test_chat_sql_dynamic_column_refinement_service.py`.
- Fix regex: «filtrar» não confundir com filial (`90` de código de produto).

### 3. Refinamento SQL — textos e colunas centralizados

Motivos de refinamento e resposta «mostrar SQL» em `external_action_responses.json` → `sqlQueryRefinement`.

Definições de coluna (aliases PT + SQL Protheus) em `sql_intent_vocabulary.json` → `queryRefinement.columnDefinitions` — consumidas por `ChatSqlQueryRefinementService` via `ChatSqlIntentVocabularyService.column_definitions()`.

### 4. Especialista SQL — schema prefetch

Textos de prefetch de schema e relações SX9 em `advancedSqlSpecialist.schemaExplore` e `schemaRelations` — consumidos por `ChatAdvancedSqlSpecialistService` (incl. intro de authoring SQL).

### 5. Outros domínios migrados

| Domínio | Loader | Serviço consumidor |
|---------|--------|-------------------|
| Intervalo de datas | `ChatDateRangeVocabularyService` | `ChatDateRangeIntentService` |
| Ponto temporal (dia) | idem (`weekdaysPt`, `temporalRangeMarkers`) | `ChatTemporalIntentService` |
| Sessão ativa | `ChatSessionVocabularyService` | `ChatActiveQuerySessionService` |
| Paginação consolidada | `ChatToolContextContentService` | `ChatPaginationConsolidationService` |
| Pipeline operacional | `ChatOperationalPipelineVocabularyService` | `ChatOperationalPipelineService` |
| Parâmetros operacionais | `operational_parameters.json` | `ChatOperationalParameterService` |
| Extração de termos | `ChatTermExtractionVocabularyService` | `ChatTermExtractionService` |
| Contexto textual | `ChatTextContextVocabularyService` | `ChatTextContextResolverService` |
| Dashboard multi-card | `presenter_content.dashboardPresentation` | `ChatDashboardPresentationService` |
| Recomendação de formato | `presenter_content.presentationRecommendation` | `ChatPresentationRecommendationService` |
| Transformação lousa | `ChatCanvasTransformVocabularyService` | `ChatCanvasTransformService` |
| Web search explícita/planejamento | `ChatWebSearchVocabularyService` | `ChatWebSearchIntentService`, `ChatWebSearchPlanningService` |

---

## Serviços Python que passaram a consumir JSON

**Vocabulário SQL / análise (08432dce):**

- `ChatSqlOperationalIntentService`, `ChatSqlProductionQueryService`, `ChatSqlIntentService`
- `ChatSqlQueryRefinementService`, `ChatSqlDynamicColumnRefinementService`
- `ChatSqlInventoryQueryService`, `ChatSqlResultAnalyzerService`
- `ChatAdvancedSqlSpecialistService`, `ChatSqlQueryPatternAdvisorService`
- `ChatAnalysisIntentService`, `ChatTextContextResolverService`

**Centralização adicional (437587e2):**

- `ChatSqlQueryRefinementService` (reasons + columnDefinitions)
- `ChatActiveQuerySessionService`, `ChatOperationalParameterService`, `ChatOperationalPipelineService`
- `ChatPaginationConsolidationService`, `ChatToolContextPresentationService`
- `ChatDateRangeIntentService`, `ChatTemporalIntentService`
- `ChatSqlProductionSchedulePresentationService`, `sql_presenter.py`

**Rodada dashboard/temporal/canvas/web (403e7fc0):**

- `ChatDashboardPresentationService`, `ChatCanvasTransformService`
- `ChatPresentationRecommendationService`, `ChatAdvancedSqlSpecialistService` (relações)

---

## Testes de regressão

| Arquivo | Escopo |
|---------|--------|
| `test_sql_intent_vocabulary_content.py` | Bundles SQL, `shared`, columnDefinitions, especialista |
| `test_analysis_intent_vocabulary_content.py` | Bundle análise |
| `test_text_context_vocabulary_content.py` | Bundle contexto textual |
| `test_shared_vocabulary_content.py` | date_range, session, pipeline, canvas, web_search |
| `test_chat_sql_dynamic_column_refinement_service.py` | Motor agrupar/filtrar por coluna |
| `test_chat_sql_production_schedule_presentation_service.py` | Narrativa SC2010 |
| `test_sql_branch_breakdown_matrix.py` | Matriz «por filial» produção |
| `test_external_action_result_presenter_sql.py` | Presenter SQL + narrativa |
| `test_chat_sql_query_refinement_service.py` | Refinamento multi-turn |
| `test_chat_date_range_intent_service.py`, `test_chat_temporal_intent_service.py` | Temporal |
| `test_chat_web_search_intent_service.py`, `test_chat_web_search_planning_service.py` | Web search |
| `test_chat_dashboard_presentation_service.py` | Dashboard multi-panel |

Comando útil (smoke local):

```bash
cd minha-delpi-ai-api && .venv/bin/pytest \
  tests/unit/domain/services/test_sql_intent_vocabulary_content.py \
  tests/unit/domain/services/test_shared_vocabulary_content.py \
  tests/unit/domain/services/test_chat_sql_dynamic_column_refinement_service.py \
  tests/unit/domain/services/test_chat_sql_production_schedule_presentation_service.py \
  tests/unit/domain/services/test_external_action_result_presenter_sql.py \
  tests/unit/domain/services/test_chat_date_range_intent_service.py \
  tests/unit/domain/services/test_chat_temporal_intent_service.py \
  tests/unit/domain/services/test_chat_web_search_intent_service.py \
  tests/unit/domain/services/test_chat_dashboard_presentation_service.py -q
```

---

## Pendências conhecidas (próximas rodadas)

> **Arquitetura W4+ e registry:** ver [chat-refactor-status-jun2026.md](./chat-refactor-status-jun2026.md) §4 — adiado em favor de bugs e qualidade de resposta.

1. **Filtro família/prefixo** no `ChatSqlProductionQueryService` (`LIKE '9026%'` quando token é prefixo).
2. **Regex temporais** (`_TODAY_PATTERNS`, etc.) — candidatos a JSON ou builder a partir de termos.
3. **`ChatPresentationChartExplainService`** — tokens de eficiência ainda inline.
4. **Narrativa/insights** em outras rotas SQL/operacionais (estoque agregado, factory-status) no mesmo padrão SC2010.
5. **MFE:** espelhar bundles compartilhados em `plugins/minha-delpi-chat/src/content/` quando UI exibir os mesmos textos.

---

## Como estender (checklist)

1. Identificar strings PT ou listas de marcadores no serviço canônico (não patch no use case nem no prompt de agente).
2. Escolher bundle existente ou criar `assistant/<dominio>_vocabulary.json`.
3. Subclassificar `ChatAssistantVocabularyService` com `BUNDLE` fixo; expor métodos compostos se houver `shared`.
4. Consumir só via loader no serviço de domínio.
5. Teste unitário mínimo + caso em `chat_intelligence_regression_cases.py` se afetar roteamento.
6. Atualizar [`assistant-content-catalog.md`](./assistant-content-catalog.md) e, se escopo grande, este doc.
