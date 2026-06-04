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
| `presenter_content.json` | Títulos de rotas/KPI, markdown analyser | `ExternalActionResultPresenter._infer_items_title` |
| `error_handling.json` | Erros recuperáveis, chips, SQL tipado | `ChatErrorHandlingClassifier`, SQL interpretation |
| `sql_execution_errors.json` | Ponte tipos SQL → `error_handling.types` | `ChatSqlExecutionErrorInterpretationService` |
| `data_coverage.json` | Avisos parcial/paginação/profundidade | `ChatDataCoverageNoticeService` |
| `structure_comparison.json` | Comparação BOM/ficha | `ChatStructureComparisonService` |
| `memory_ux.json` | Memória de sessão (barra + introspecção) | `ChatMemoryUxService` |
| `web_search.json` | Resposta direta e marcadores de follow-up | `ChatWebSearchDirectAnswerService` |
| `stream.json` | Status SSE + fases de atividade + desenho | `ContentService.stream`, `ChatStreamActivityService` |
| `operational_parameters.json` | Parâmetros faltantes | `ChatOperationalParameterService` |
| `interactivity.json` | Chips, refinamentos | Vários serviços de interatividade |
| `identity.json` | Quem é você, perfil | `ChatAssistantIdentityService` |
| `small_talk.json` | Conversa leve | `ChatSmallTalkService` |
| `unclear_requests.json` | Pedidos ambíguos | `ChatUnclearRequestService` |
| `utility_answers.json` | Hora, data | `ChatUtilityDirectAnswerService` |
| `onboarding.json` | Onboarding | `ChatOnboardingService` |
| `capabilities.json` | Capacidades | `ChatCapabilitiesService` |
| `column_labels.json` | Colunas de tabelas | `ExternalActionColumnLabelService` |
| `personality_playbook.json` | Tom e feedback | `ChatPersonalityContentService` |

## Migração (jun/2026) — já centralizado

- Stream activity: `stream.activity.phaseGroups`, `drawingStages`
- SQL execution errors → `error_handling.types` via `sql_execution_errors.errorTypeToHandling`
- Cobertura de dados → `data_coverage.json`
- Comparação de estrutura (insufficient data) → `structure_comparison.json`
- Memória UX → `memory_ux.json`
- Web search direct answer → `web_search.json` (antes em `product_operational_content.webSearch`)
- Títulos de lista no presenter → `presenter_content.titlesByPathFragment`

## Pendente (próximas PRs)

Prioridade sugerida para novos JSON ou seções:

1. `drawing_validation.json` — `chat_drawing_validation_orchestration_service.py`
2. `user_context.json` — `chat_user_context_service.py`
3. `web_search.json` — completar marcadores em `chat_web_search_source_follow_up_service.py`
4. `analyser_insights.json` — `chat_product_analyser_divergence_service.py`, seções `**Destaques**` no presenter
5. `presenter_content.json` — KPI titles (`_kpi_title`), narrativas analyser restantes
6. `data_interpretation.json` — `chat_data_interpretation_answer_service.py`
7. Termos de intenção ainda inline em `chat_product_query_intent_service.py` (parents regex mantém lógica; termos literais podem ir para JSON)

## Como adicionar conteúdo

1. Editar o JSON em `app/content/pt-BR/assistant/`.
2. No serviço: `ChatAssistantContentService.get("meu_bundle", "secao", "chave")`.
3. Teste unitário mínimo que valida a chave existe.
4. Atualizar esta tabela e, se for domínio grande, `product-operational-content.md` ou doc específica.
5. MFE: importar o mesmo JSON quando o texto for compartilhado (padrão `operationalPresentationContent.ts`).

## Cache

`invalidate_assistant_content_cache(bundle)` ou `ContentService.clear_cache()` após alterar JSON em runtime de testes.
