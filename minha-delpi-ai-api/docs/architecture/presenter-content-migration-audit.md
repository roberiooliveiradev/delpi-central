# Varredura final — migração de textos do presenter (jun/2026)

Relatório de auditoria após centralização em `app/content/pt-BR/assistant/*.json`.

## Escopo

- **Arquivo principal:** `external_action_result_presenter.py`
- **Bundles:** `presenter_content.json`, `product_operational_content.json`, `column_labels.json`, `external_action_responses.json`, `analyser_insights.json`

## Concluído nesta varredura

| Área | Antes | Depois |
|------|--------|--------|
| `_present_items` (estoque) | String `.format()` duplicada | `product_operational_content.presenter.stock.detailLine` |
| `_present_items` (fornecedor/cliente) | Lead time / preço / nome inline | `presenter_content.itemsListPreview` |
| `build_presentation` (stock/parents/structure) | Títulos fixos em Python | `titlesByPathFragment` + fallbacks operacionais |
| SQL em `build_presentation` | `"Consulta SQL"` | `external_action_responses.sql.defaultTitle` |
| Tabela genérica | `"Dados retornados"` | `presenter_content.generic.itemsTableDefaultTitle` |
| Gráficos | Títulos fixos | `presenter_content.charts.defaultVisualizationTitle` / `heatmapTitle` |
| Erro API sem mensagem | `"Erro desconhecido na API."` | `presenter_content.apiErrors.unknown` |
| KPI fallback | `"Indicador"` espalhado | `_kpi_title(path)` / `kpiTitles.default` |
| Text presentation | `"Resultado"` | `generic.textPresentationFallback` |
| Text presentation (estoque) | `"Detalhamento por filial e armazém"` | `generic.stockTextDetailHeader` |
| Tool context (lote 12–13) | Roteador, paginação, drawing, execução, erros | `tool_context.json` + `ChatToolContextContentService` |

## Já centralizado (não reimplementar)

- Rotas: `routePresentations` (guide, inspection, lmp, saleOrders, structureItems, productSearch, factoryStatus)
- Narrativas: `productOverview`, `analyserProfile`, `analyserInsights`, `guideItemNarrative`, `systemTablesNarrative`, `routeNarratives`
- Analyser abertura/atenção: `analyser_insights.json` + `ChatProductAnalyserDivergenceService`
- Colunas: `column_labels` + `ExternalActionColumnLabelService`
- Faturamento, PMR, valor estoque, tabelas fixas analyser, markdown inspeção, `analyserCompact`
- Cronograma produção: `external_action_responses.productionSchedule`
- MFE: `plugins/minha-delpi-chat/src/content/product_operational_content.json` (sync manual)

## Residual aceitável (permanece no Python)

| Categoria | Exemplos | Motivo |
|-----------|----------|--------|
| Formatação numérica/data | `_format_currency`, `_format_protheus_date`, `f"{raw[6:8]}/..."` | Lógica, não copy de UI |
| Chaves de API | `QP7_*`, `X2_*`, `COD_PRODUTO` | Contrato Protheus |
| Markdown estrutural | `f"### {title}"`, `f"**{label}:** {value}"` | Template; `title`/`label` vêm do JSON |
| Marcadores de chart (intenção) | `heatmap`, `mapa de calor` em regex de mensagem | Detecção, não exibição |
| Agregação / delta KPI | `f"+{self._format_num(diff)}"` | Valores dinâmicos |
| Truncamento técnico | `row[k] += f" (+{len(v) - 5})"` | Metadado de preview |

## Residual opcional (baixa prioridade)

1. ~~**`_present_product_with_details`** — bullet `f"- {preview}"`~~ → **feito (Fase 5):** `generic.collectionPreviewLine` em `product_overview_presenter.py`.
2. **Playbook reports** — títulos migrados para `presenter_content.playbookReports` (Fase 5).
3. **Listagens genéricas** — colunas dinâmicas continuam via `label_for` + `_COLUMN_TYPE_MAP` (documentado no catálogo).
4. **Outros serviços** — `ChatSqlQueryRefinementService`, rotas HTTP e testes de regressão ainda referenciam «Consulta SQL» / «Visualização dos dados» como strings de fixture ou título de refinamento SQL (fora do presenter).
5. **`execute_external_action_use_case`** — conjunto `wrong_titles` para UX de chat (não é bundle do presenter).
6. **`chat_canvas_content_service`** — mensagens da lousa ainda inline (baseline do gate Fase 5; migrar para bundle canvas).

## Verificação

```bash
docker exec delpi-minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_presenter_content_helpers.py \
  tests/unit/domain/services/test_external_action_result_presenter*.py \
  tests/unit/infrastructure/content/test_no_hardcoded_pt_strings.py -q
```

## Referências

- [assistant-content-catalog.md](./assistant-content-catalog.md)
- Regra de workspace: inteligência no chat base, não só no prompt do agente
