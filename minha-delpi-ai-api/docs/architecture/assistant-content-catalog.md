# Catálogo de conteúdo do assistente (JSON)

Todos os textos exibidos ao usuário ou usados em respostas diretas devem ficar em `app/content/pt-BR/assistant/*.json`, carregados via `ContentService` ou `ChatAssistantContentService`.

**Regra do repositório (Cursor):** `.cursor/rules/assistant-content-json.mdc` — novas implementações devem seguir este padrão; não introduzir textos soltos em Python/TS.

## Loader genérico

`ChatAssistantContentService` (`app/domain/services/chat_assistant_content_service.py`):

| Método | Uso |
|--------|-----|
| `get(bundle, *path)` | String em caminho aninhado |
| `format(bundle, *path, **values)` | Template `{placeholder}` |
| `list(bundle, *path)` | Lista de termos (intenção, marcadores) |
| `get_mapping(bundle, *path)` | Objeto chave → string |
| `get_node(bundle, *path)` | Nó arbitrário (dict/list) |
| `title_for_path(bundle, path, path_key=…)` | Título por fragmento de URL |
| `get_error_type` / `get_error_reasons` | Tipos em `error_handling.json` |

`bundle` = nome do arquivo sem extensão (ex.: `web_search` → `assistant/web_search.json`).

Wrappers especializados (mantêm API estável):

- `ExternalActionResponseContentService` → `external_action_responses.json`
- `ChatProductOperationalContentService` → `product_operational_content.json`

## Arquivos por domínio

| Arquivo | Domínio | Serviços principais |
|---------|---------|-------------------|
| `external_action_responses.json` | **`domainPredicates`** + **`systemPredicates`** + **`productSearchPredicates`** + `actionSelection` + `selectionReasons` | `ChatProductRoutePredicateService`, `ExternalActionResponseContentService` |
| `operational_route_registry.json` | Catálogo declarativo DOCIE (`dispatchOrder`, `fallbackPolicies`, **`sqlReadiness`**, ~78 rotas manuais + **`autoTierCRoutes`** geradas do OpenAPI, `match.productionOperationalKind` PB15, predicados, intent binding) | `OperationalRouteRegistryService`, `OperationalRouteRegistryGeneratorService`, `ExternalActionOperationalRouteSelectionService`, `ExternalActionSqlFallbackPolicyService`, `OperationalRouteRegistryLintService` |
| `product_query_intent.json` | Marcadores de intenção operacional; **`intentProbes`** declarativos + pipeline detect/refine; **`routePredicates`**, **`playbookPredicates`**, **`subIntentPredicates`**, **`intentDetectPipeline`**, **`intentRefinementPipeline`**, **`singleScopeIntentMap`** (DOCIE Fase 11–17) | `ChatProductQueryIntentService`, `ChatProductQueryIntentDetectionService`, `ChatProductRoutePredicateService`, `OperationalRouteMatcherService` |
| `product_operational_content.json` | Produto: escopos, plural, presenter estoque, presentation MFE | `ChatProductOperationalContentService`, plural, multi-scope |
| `presenter_content.json` | Títulos de rotas/KPI, markdown analyser, matchers KPI | `ExternalActionResultPresenter` |
| `analyser_insights.json` | Narrativa de abertura e pontos de atenção do `/analyser` | `ChatProductAnalyserDivergenceService` |
| `api_route_domains.json` | Domínios de rota operacional; **`parameterStrategies`** declarativas (bindings, patterns, granularity) | `ChatOperationalApiDomainService`, `OperationalApiParameterBuilderService` |
| `presentation_profiles.json` | Perfil `directives` (3 tabelas MPs/fornecedores/última compra; stack em Automático) | `ChatPresentationProfileService`, `ChatPresentationTableAssemblyService` |
| `response_modes.json` | Modos Rápida/Normal/Pensador (rótulos, aliases, avisos de `responseModeEffect`, **`fastCommentaryDirect`**, **`fastLlmBudget`**) | `ChatResponseModeContentService`, `ChatResponseModeService`, `ChatOperationalLlmSynthesisBriefDirectService` |
| `operational_narrative_synthesis.json` | Gate LLM narrativo (perfis evidence-first, policies por modo, termos factuais estreitos) | `ChatOperationalNarrativeSynthesisContentService`, `ChatOperationalNarrativeSynthesisService` |
| `operational_llm_synthesis_context.json` | Budget de fatos no prompt LLM (`maxChars`, `maxProfileTableRows`, limites de linhas/tabela/SQL) | `ChatOperationalLlmSynthesisContextContentService`, `ChatOperationalLlmSynthesisContextService` |
| `presentation_prose_delivery.json` | Modos prosa template × LLM × direct; chaves metadata do contrato | `ChatPresentationProseDeliveryContentService`, `ChatPresentationProseDeliveryService` |
| `response_mode_synthesis_quality.json` | Critérios smoke/regressão da síntese LLM (similaridade vs template, contexto, deflexão, escada de modos) | `ChatResponseModeSynthesisQualityContentService`, `ChatResponseModeSynthesisQualityService` |
| `column_labels.json` | Perfis `directivesRawMaterials`, `directivesSuppliers`, `directivesLastPurchase` (detect por `/directives/`) | `ExternalActionColumnLabelService`, `ChatPresentationFieldNormalizationService` |
| Changelog integrado | `docs/changelog/2026-06-product-directives-chat.md` | Roteamento, apresentação, MFE filtros, modos Automático/Tabela/Texto |
| `production_operational_intent.json` | Marcadores Playbook 15 — consumo, compras ranking, refugo, OPs, CT, empenho, planejado×real (`terms`, `excludeTerms`, `pathTokens`) | `ChatProductionOperationalIntentService`, `operational_route_registry.json` |
| `intent_router.json` | Marcadores de roteamento (autoajuda, RAG, apresentação, web block, operacional) | `ChatIntentRouterService` |
| `intent_disambiguation.json` | Clarificação de escopo operacional (chips + directAnswer) | `ChatIntentDisambiguationService` |
| `product_overview_intent.json` | «Me fale do produto» e visão geral | `ChatProductOverviewIntentService` |
| `error_handling.json` | Erros recuperáveis, chips, SQL tipado | `ChatErrorHandlingClassifier`, SQL interpretation |
| `sql_execution_errors.json` | Ponte tipos SQL → `error_handling.types` | `ChatSqlExecutionErrorInterpretationService` |
| `data_coverage.json` | Avisos parcial/paginação/profundidade | `ChatDataCoverageNoticeService` |
| `structure_comparison.json` | Comparação BOM/ficha | `ChatStructureComparisonService` |
| `memory_ux.json` | Memória de sessão (barra + introspecção) | `ChatMemoryUxService` |
| `web_search.json` | Resposta direta e follow-up pós-pesquisa | `ChatWebSearchDirectAnswerService`, `ChatWebSearchSourceFollowUpService` |
| `drawing_validation.json` | Relatório, checklist, rótulos de status (`statusPresentation`), campos do markdown (`reportFields`), export CSV/PDF/XLSX (`export`), regras de consolidação de seção (`presentation`), **`bomQuantitySemantics.refinementTriggers`** (15.8) | `ChatDrawingValidationContentService`, `ChatDrawingValidationPresentationService`, `ChatDrawingValidationOrchestrationService`, `ChatDrawingReportExportService`, `ChatDrawingBomQuantityAssertivenessService` |
| `drawing_query_intent.json` | Marcadores de intent de análise de desenho (PDF, conformidade, BOM), respostas diretas e fallback LLM (`llmFallback` → `drawing-report-llm-fallback.md`) | `ChatDrawingIntentService` |
| `drawing_stamp.json` | Rótulos de carimbo, regiões, **`layoutAnalysis`** (XY-Cut), exclusões cliente/BOM, clarificações, gate nativo (Onda 14), padrões de cota/decape, **`bomColumnHeaders`** / **`bomColumnInference`** / **`bomRowRefinement`** / **`bomComparison`** (15.8) | `ChatDrawingStampExtractionService`, `ChatDrawingPageLayoutAnalysisService`, `ChatDrawingDimensionsExtractionService`, `ChatDrawingPatternsService`, `ChatDrawingBomTableInterpretationService`, `ChatDrawingBomComparisonService` |
| `document_vision.json` | Intent OCR, VLM, `pdfExtraction` (fusão, perfis `generic`/`drawing_delpi`); **`pdfExtraction.tableStructure`** + **`rowParsing`** (15.8.2b, genérico) | `ChatDocumentVisionContentService`, `ChatPdfDocumentExtractionService`, `ChatPdfTableStructureService`, `ChatDocumentVisionSkillService` |
| `user_context.json` | Respostas diretas sobre perfil e papéis | `ChatUserContextService` |
| `data_interpretation.json` | Marcadores e título padrão de interpretação de dados | `ChatDataInterpretationAnswerService` |
| `humanized_data_response.json` | Templates de resumo, alertLevel, limitações, próximas ações e camadas de leitura (Playbook 13) | `ChatHumanizedDataResponseContentService`, `ChatHumanizedDataResponseService` |
| `stream.json` | Status SSE + fases de atividade + desenho | `ContentService.stream`, `ChatStreamActivityService` |
| `tool_context.json` | Roteador, paginação, drawing no tool context, erros de ferramenta | `ChatToolContextContentService`, `ChatToolContextSelectionService`, `ChatToolContextPreTurnService` |
| `turn_preparation.json` | Respostas diretas da preparação de turno (ex.: interpretação sem dados; **`directAnswers.projectSources`** — inventário de fontes do projeto) | `ChatTurnPreparationContentService`, `ChatTurnPreparationDirectAnswerService`, `ChatProjectSourcesIntentService` |
| `operational_parameters.json` | Parâmetros faltantes (`missingProductCode`, `missingDateByContext`, OV, filial) | `ChatOperationalParameterService`, `ChatOperationalDateParameterService` |
| `operational_follow_up_routing.json` | Follow-up operacional: escopo de produto, herança de data playbook, segmentos, gate capabilities | `ChatOperationalFollowUpRoutingService` |
| `interactivity.json` | Chips, refinamentos | Vários serviços de interatividade |
| `identity.json` | Quem é você, perfil | `ChatAssistantIdentityService` |
| `small_talk.json` | Conversa leve | `ChatSmallTalkService` |
| `unclear_requests.json` | Pedidos ambíguos | `ChatUnclearRequestService` |
| `utility_answers.json` | Hora, data | `ChatUtilityDirectAnswerService` |
| `onboarding.json` | Onboarding | `ChatOnboardingService` |
| `attachments.json` | Welcome/chips pós-upload (PB05), preview de leitura, **`ingestUi`** (dropzone, composer, agente — PB17) | API `ChatAttachmentContentService`; MFE `workspaceFileIngestContent.ts` + `sync:attachments-content` |
| `message_composer.json` | Composer (corretor de digitação P14) | MFE `messageComposerContent.ts` + `POST /chat/typing-suggestions` |
| `typing_correction_rules.json` | Typos operacionais estáticos (normalização + sugestões P14) | `ChatMessageNormalizationService.configure_static_rules` |
| `typing_correction_lexicon.json` | Vocabulário operacional para fuzzy P14-5 | `ChatTypingCorrectionFuzzyLexiconService.configure` |
| `text_correction_spell_check.json` | Preflight LanguageTool na skill de correção textual | `ChatTextCorrectionSpellContentService` |
| `capabilities.json` | Capacidades | `ChatCapabilitiesService` |
| `column_labels.json` | Colunas de tabelas, perfil KV do produto, tabelas fixas do presenter | `ExternalActionColumnLabelService`, `ExternalActionResultPresenter` |
| `personality_playbook.json` | Tom, feedback, **`drawingFollowUpChips`** / **`drawingFollowUpQueries`** (incl. «Reextrair BOM do PDF», 15.8.5) | `ChatPersonalityContentService`, `ChatDrawingFollowUpService` |
| `sql_intent_vocabulary.json` | Marcadores SQL (intenção, refinamento, produção, analisador) — seção **`shared`** para termos reutilizados | `ChatSqlIntentVocabularyService` → vários `ChatSql*` |
| `analysis_intent_vocabulary.json` | Marcadores de análise/comparação | `ChatAnalysisIntentVocabularyService` |
| `text_context_vocabulary.json` | Resolução de contexto textual (produto, filial, datas) | `ChatTextContextVocabularyService` |
| `term_extraction_vocabulary.json` | Stopwords e marcadores de pergunta de definição | `ChatTermExtractionVocabularyService` |
| `session_vocabulary.json` | Marcadores de mudança de assunto na sessão ativa | `ChatSessionVocabularyService` |
| `operational_pipeline_vocabulary.json` | Termos operacionais vs. documentais no fast path | `ChatOperationalPipelineVocabularyService` |
| `operational_group_by_refinement.json` | Rotas, dimensões e estratégia session/refetch para agrupamento de follow-up | `ChatOperationalGroupByRefinementService`, `ChatOperationalSessionDataRefinementService` |
| `presentation_vocabulary.json` | Dedup estrutura/BOM, **`decisionReasons`**, insights, Playbook 12 (`tableRoles`, `tierAPipelineCases`), **`automaticScoreMarkers`** (listagem vs ranking no Automático) | `ChatPresentationVocabularyService` |
| `date_range_vocabulary.json` | Meses, frases de período e métricas temporais | `ChatDateRangeVocabularyService` |
| `canvas_transform_vocabulary.json` | Termos e templates de transformação na lousa | `ChatCanvasTransformVocabularyService` |
| `presentation_profiles.json` | `entityProfiles`, **`entitySetProfileContracts`**, `entitySets`, `pathRules`, `noChartEntities`, `chartPolicy`, `defaultViewPolicy`, visualBuilders, stackPlan | `ChatPresentationProfileService`, `ChatPresentationCoverageService` |
| `ChatOperationalResponseProfileService` | Roteamento `meta.entity` → perfil/presenter OpenAPI (alias legado: `ChatApiDelpiResponseProfileService`) | path hardcoded em presenters |
| `presenter_content.json` → `schemaDriven` | Narrativa mínima para rotas tier C/B sem builder dedicado | `ChatSchemaDrivenPresentationService` |
| `presenter_content.json` → `humanizedNarrative` | Panorama, leitura rápida, destaques, prefixos de atenção e conclusão do enriquecimento genérico | `ChatPresentationHumanizedNarrativeService`, `ChatPresentationStackOrderService` |
| `presentation_profiles.json` → `humanizedNarrative` | `skip` ou `enrich` por perfil (ex.: stock, sale_pricing) | `ChatPresentationProfileService`, `ChatPresentationHumanizedNarrativeService` |
| `presenter_content.json` → `stackSectionFraming` | Frases de framing por seção (`default`, `byProfile.sale_pricing`, …) | `ChatPresentationStackMarkdownService`, `ChatPresentationSectionAvailabilityService` |
| `presenter_content.json` → `routes.salePricing` | Narrativa de precificação: panorama, leitura, atenção, conclusão, KPI | `ExternalActionProductPricingPresenter` |
| `presenter_content.json` → `generic.treeOutlineHeader` / `treeOutlineTruncated` | Cabeçalho e truncamento do outline ASCII em modo Texto (estrutura/BOM) | `ChatPresentationTreeMarkdownService` |
| `presenter_content.json` → `compositeVisualSpecs` | Spec declarativa do quartet KPI/árvore/gráfico/dashboard por perfil (Playbook 12 R6) | `ChatPresentationCompositeVisualBuilder`, `ChatPresentationProfileCompositeVisualService` |

## Vocabulário compartilhado (dicionários PT)

Termos e frases de **intenção/heurística** ficam em bundles `*_vocabulary.json`. Vários serviços Python leem o **mesmo** JSON via subclasses de `ChatAssistantVocabularyService`:

| Método | Uso |
|--------|-----|
| `terms(*path)` | Lista de marcadores em caminho aninhado |
| `merge_terms(*paths)` | Une listas do mesmo bundle sem duplicar (ex.: `shared` + seção específica) |
| `text` / `format` | Template com `{placeholder}` |
| `synonym_map` | Objeto chave → lista de aliases |
| `node` / `mapping` | Nó arbitrário ou mapa chave→string |

**Padrão:** definir termos canônicos uma vez em `shared.*`; métodos de conveniência no loader (ex.: `incremental_authoring_terms()`) compõem `shared` + chaves específicas. Regex, SQL e heurísticas numéricas permanecem no Python.

**Novo domínio:** criar `assistant/<dominio>_vocabulary.json`, subclass com `BUNDLE = "<dominio>_vocabulary"`, consumir só via loader — não copiar listas entre serviços.

## Migração (jun/2026) — já centralizado

- Stream activity: `stream.activity.phaseGroups`, `drawingStages`
- SQL execution errors → `error_handling.types` via `sql_execution_errors.errorTypeToHandling`
- Cobertura de dados → `data_coverage.json`
- Comparação de estrutura (insufficient data) → `structure_comparison.json`
- Memória UX → `memory_ux.json`
- Web search direct answer → `web_search.json` (antes em `product_operational_content.webSearch`)
- Web search follow-up (links, resumo, parâmetros, comparação) → `web_search.followUp`
- Validação de desenho (relatório, templates de checklist, conclusões) → `drawing_validation.json`
- Apresentação do relatório de desenho (rótulos de status, consolidação de itens repetidos, expansão item a item em BOM/50xx, árvore SG1010, roteiro completo, labels de export) → `drawing_validation.json` (`statusPresentation`, `reportFields`, `export`, `presentation`) + `ChatDrawingValidationPresentationService`; MFE render-only consome `drawingAnalysisExport.statusLabels` / `exportLabels` e suprime apresentação duplicada do `/analyser`
- Parâmetros do `/analyser` em turno de desenho (`view=full` obrigatório; sem `view=summary` nem paginação parcial) → `ChatDrawingAnalyserParameterService` (application: `ExternalActionProductRouteCatalogService.build_product_parameters`, `ChatExternalActionOrchestrationService`, `ChatToolContextSelectionService`)
- Exportação do relatório de desenho (tabelas estruturadas `tables[]` para PDF/CSV/XLSX; PDF via HTML no padrão inspeções de entrada com logo DELPI) → `ChatDrawingValidationPresentationService.build_export_tables` + `ChatDrawingReportExportService`; MFE: `drawingAnalysisPrint.ts`, `drawingAnalysisExport.ts`
- Intent de análise de desenho (gatilhos, vocabulário com anexo, códigos explícitos sem PDF, direct answers, biblioteca não encontrada) → `drawing_query_intent.json`
- SSE de busca na biblioteca → `stream.json` → `activity.drawingStages.fetch_library_pdf`
- Contexto de usuário (perfil, papéis, permissões, grupos) → `user_context.json`
- Interpretação de dados (marcadores genéricos) → `data_interpretation.json`
- Detalhe de linha da última tabela (drill-down MFE) → `data_interpretation.rowDetail` + `analysis_intent_vocabulary.rowDetailRequestTerms` → `ChatPresentationRowDetailAnswerService`
- Títulos de lista no presenter → `presenter_content.titlesByPathFragment`
- KPI por fragmento de path → `presenter_content.kpiPathMatchers` + `kpiTitles`
- Analyser (destaques, atenção, PMR, pais, compras) → `presenter_content.analyserMarkdown` + `analyser_insights.json`
- Intenção de consulta de produto (estoque, vendas, pais, resumo, playbook) → `product_query_intent.json` (`routePredicates`, `playbookPredicates`, `subIntentPredicates`); regex de pais em `parents.regexPatterns`; plural via matcher `pluralScopeLinked`
- Resumos de texto de parents/estrutura → `presenter_content.routeNarratives`
- Visão geral do produto → `product_overview_intent.json`
- Presenter genérico (vazio operacional, erros API, paginação, analyser) → `presenter_content.generic`, `operationalEmpty`, `apiErrors`, `pagination`, `analyserCollections`
- Apresentações por rota (roteiro, inspeção, OV, LMP, busca, estrutura, SX2) → `presenter_content.routePresentations`
- Field labels do presenter (aliases de produto/preço/estoque, perfil KV, componentes da estrutura) → `column_labels.fields` + `column_labels.presenter`
- Ordem/rótulo preferido de colunas tabulares (hints — **não** whitelist; payload da API define o que aparece) → `column_labels.tableProfiles` + `ExternalActionColumnLabelService.resolve_columns_for_items`
- Humanização centralizada (tabular + KV) — **R21 playbook-12** → `ChatPresentationFieldLabelResolutionService` + `resolve_field_labels` + `format_field_value`
- Descoberta de rótulo ausente (web + LLM, pós-vocabulário) — **R16 playbook-12** → `column_labels.columnLabelDiscovery` + `PresentationColumnLabelDiscoveryPort` → `ChatPresentationColumnLabelDiscoveryService`
- ~~`column_labels.presenter.fixedTableColumns`~~ **deprecated jun/2026** — migrado para `tableProfiles`; ver Playbook 12 § R15
- KPI genérico, títulos de detalhe de produto, gráficos (estrutura/estoque) e resumo compacto do analyser → `presenter_content.genericKpi`, `productDetailTitles`, `charts`, `analyserCompact`
- Narrativas de visão geral, perfil analyser, insights, roteiro (markdown), SX2 e títulos de apresentação → `presenter_content.productOverview`, `analyserProfile`, `analyserInsights`, `guideItemNarrative`, `systemTablesNarrative`
- Linhas de lista por rota (roteiro preview, LMP, OV, estrutura, busca) → `presenter_content.routePresentations.*`; cronograma SQL → `external_action_responses.productionSchedule`
- Dict fallback, preview de coleção e inspeção plana (características + limites de teste) → `presenter_content.generic`, `routePresentations.inspection`
- Varredura final do presenter (estoque/fornecedor em `_present_items`, títulos stock/parents/structure, SQL/chart/KPI/erro API) → `presenter_content` + `product_operational_content`; ver [presenter-content-migration-audit.md](./presenter-content-migration-audit.md)
- **Vocabulário SQL/temporal/sessão/web (jun/2026)** → bundles `*_vocabulary.json`, loaders `ChatAssistantVocabularyService`; ver [vocabulary-centralization-jun2026.md](./vocabulary-centralization-jun2026.md)

## DOCIE — gates CI (jun/2026)

| Script | Gate |
|--------|------|
| `scripts/lint_operational_route_registry.py --check` | Registry + vocabulário + cobertura tier C |
| `scripts/generate_operational_route_registry.py --check` | `autoTierCRoutes` sincronizado com OpenAPI baseline |
| `scripts/audit_presentation_path_ifs.py --check` | Apresentação entity-first (Fase 19) |
| `scripts/audit_presentation_coverage.py --check-profiles` | Tier A sem `generic`; **contratos entitySet × perfil**; path vs catch-all |

Workflow: `.github/workflows/minha-delpi-ai-api-docie.yml`. Regenerar tier C após reimport OpenAPI: `generate_operational_route_registry.py --write`.

**Nova rota:** checklist completo em [new-api-route-checklist.md](./new-api-route-checklist.md).

## Pendente (baixa prioridade)

1. Colunas dinâmicas em listagens genéricas continuam via `label_for` + `_COLUMN_TYPE_MAP`
2. Regex temporais pontuais (`_TODAY_PATTERNS` em `ChatTemporalIntentService`) e tokens de apresentação adjacentes — ver pendências em [vocabulary-centralization-jun2026.md](./vocabulary-centralization-jun2026.md)

## Como adicionar conteúdo

1. Editar o JSON em `app/content/pt-BR/assistant/`.
2. No serviço: `ChatAssistantContentService.get("meu_bundle", "secao", "chave")`.
3. Teste unitário mínimo que valida a chave existe.
4. Atualizar esta tabela e, se for domínio grande, `product-operational-content.md` ou doc específica.
5. MFE: importar o mesmo JSON quando o texto for compartilhado (padrão `operationalPresentationContent.ts`).

## Cache

`invalidate_assistant_content_cache(bundle)` ou `ContentService.clear_cache()` após alterar JSON em runtime de testes.
