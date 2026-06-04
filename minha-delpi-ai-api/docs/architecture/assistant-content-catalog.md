# Catálogo de conteúdo do assistente (JSON)

Todos os textos exibidos ao usuário ou usados em respostas diretas devem ficar em `app/content/pt-BR/assistant/*.json`, carregados via `ContentService` ou `ChatAssistantContentService`.

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
| `external_action_responses.json` | SQL, produção, composite, temporal, segurança em actions | `ExternalActionResponseContentService`, composite, presenter (parcial) |
| `product_operational_content.json` | Produto: escopos, plural, presenter estoque, presentation MFE | `ChatProductOperationalContentService`, plural, multi-scope |
| `presenter_content.json` | Títulos de rotas/KPI, markdown analyser, matchers KPI | `ExternalActionResultPresenter` |
| `analyser_insights.json` | Narrativa de abertura e pontos de atenção do `/analyser` | `ChatProductAnalyserDivergenceService` |
| `product_query_intent.json` | Marcadores de intenção operacional de produto | `ChatProductQueryIntentService` |
| `product_overview_intent.json` | «Me fale do produto» e visão geral | `ChatProductOverviewIntentService` |
| `error_handling.json` | Erros recuperáveis, chips, SQL tipado | `ChatErrorHandlingClassifier`, SQL interpretation |
| `sql_execution_errors.json` | Ponte tipos SQL → `error_handling.types` | `ChatSqlExecutionErrorInterpretationService` |
| `data_coverage.json` | Avisos parcial/paginação/profundidade | `ChatDataCoverageNoticeService` |
| `structure_comparison.json` | Comparação BOM/ficha | `ChatStructureComparisonService` |
| `memory_ux.json` | Memória de sessão (barra + introspecção) | `ChatMemoryUxService` |
| `web_search.json` | Resposta direta e follow-up pós-pesquisa | `ChatWebSearchDirectAnswerService`, `ChatWebSearchSourceFollowUpService` |
| `drawing_validation.json` | Relatório e checklist de análise de desenho | `ChatDrawingValidationOrchestrationService` |
| `user_context.json` | Respostas diretas sobre perfil e papéis | `ChatUserContextService` |
| `data_interpretation.json` | Marcadores e título padrão de interpretação de dados | `ChatDataInterpretationAnswerService` |
| `stream.json` | Status SSE + fases de atividade + desenho | `ContentService.stream`, `ChatStreamActivityService` |
| `operational_parameters.json` | Parâmetros faltantes | `ChatOperationalParameterService` |
| `interactivity.json` | Chips, refinamentos | Vários serviços de interatividade |
| `identity.json` | Quem é você, perfil | `ChatAssistantIdentityService` |
| `small_talk.json` | Conversa leve | `ChatSmallTalkService` |
| `unclear_requests.json` | Pedidos ambíguos | `ChatUnclearRequestService` |
| `utility_answers.json` | Hora, data | `ChatUtilityDirectAnswerService` |
| `onboarding.json` | Onboarding | `ChatOnboardingService` |
| `capabilities.json` | Capacidades | `ChatCapabilitiesService` |
| `column_labels.json` | Colunas de tabelas, perfil KV do produto, tabelas fixas do presenter | `ExternalActionColumnLabelService`, `ExternalActionResultPresenter` |
| `personality_playbook.json` | Tom e feedback | `ChatPersonalityContentService` |

## Migração (jun/2026) — já centralizado

- Stream activity: `stream.activity.phaseGroups`, `drawingStages`
- SQL execution errors → `error_handling.types` via `sql_execution_errors.errorTypeToHandling`
- Cobertura de dados → `data_coverage.json`
- Comparação de estrutura (insufficient data) → `structure_comparison.json`
- Memória UX → `memory_ux.json`
- Web search direct answer → `web_search.json` (antes em `product_operational_content.webSearch`)
- Web search follow-up (links, resumo, parâmetros, comparação) → `web_search.followUp`
- Validação de desenho (relatório, templates de checklist, conclusões) → `drawing_validation.json`
- Contexto de usuário (perfil, papéis, permissões, grupos) → `user_context.json`
- Interpretação de dados (marcadores genéricos) → `data_interpretation.json`
- Títulos de lista no presenter → `presenter_content.titlesByPathFragment`
- KPI por fragmento de path → `presenter_content.kpiPathMatchers` + `kpiTitles`
- Analyser (destaques, atenção, PMR, pais, compras) → `presenter_content.analyserMarkdown` + `analyser_insights.json`
- Intenção de consulta de produto (estoque, vendas, pais, resumo, etc.) → `product_query_intent.json` (regex de código e pais permanecem no serviço)
- Resumos de texto de parents/estrutura → `presenter_content.routeNarratives`
- Visão geral do produto → `product_overview_intent.json`
- Presenter genérico (vazio operacional, erros API, paginação, analyser) → `presenter_content.generic`, `operationalEmpty`, `apiErrors`, `pagination`, `analyserCollections`
- Apresentações por rota (roteiro, inspeção, OV, LMP, busca, estrutura, SX2) → `presenter_content.routePresentations`
- Field labels do presenter (aliases de produto/preço/estoque, perfil KV, componentes da estrutura) → `column_labels.fields` + `column_labels.presenter`
- Faturamento, PMR, valor de estoque (KPI + tabela filial), tabelas fixas (roteiro/inspeção analyser, LMP, OV, SX2, busca) e markdown de inspeção → `presenter_content` + `column_labels.presenter.fixedTableColumns`
- KPI genérico, títulos de detalhe de produto, gráficos (estrutura/estoque) e resumo compacto do analyser → `presenter_content.genericKpi`, `productDetailTitles`, `charts`, `analyserCompact`
- Narrativas de visão geral, perfil analyser, insights, roteiro (markdown), SX2 e títulos de apresentação → `presenter_content.productOverview`, `analyserProfile`, `analyserInsights`, `guideItemNarrative`, `systemTablesNarrative`
- Linhas de lista por rota (roteiro preview, LMP, OV, estrutura, busca) → `presenter_content.routePresentations.*`; cronograma SQL → `external_action_responses.productionSchedule`

## Pendente (próximas PRs)

Prioridade sugerida para novos JSON ou seções:

1. Listagens genéricas (`_format_collection_item_lines`, dict flatten) e inspeção em rota ainda com lógica inline
2. Colunas dinâmicas em listagens genéricas continuam via `label_for` + `_COLUMN_TYPE_MAP`

## Como adicionar conteúdo

1. Editar o JSON em `app/content/pt-BR/assistant/`.
2. No serviço: `ChatAssistantContentService.get("meu_bundle", "secao", "chave")`.
3. Teste unitário mínimo que valida a chave existe.
4. Atualizar esta tabela e, se for domínio grande, `product-operational-content.md` ou doc específica.
5. MFE: importar o mesmo JSON quando o texto for compartilhado (padrão `operationalPresentationContent.ts`).

## Cache

`invalidate_assistant_content_cache(bundle)` ou `ContentService.clear_cache()` após alterar JSON em runtime de testes.
