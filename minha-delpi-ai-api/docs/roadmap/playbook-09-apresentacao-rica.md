# Playbook 09 — Apresentação Rica

Projeto: Minha DELPI Chat IA  
Escopo: tabelas, gráficos, KPIs, árvores, cards, checklists, lousa, dashboards e escolha automática do melhor formato de resposta.

> **Princípio:** Dado certo no formato certo. Implementação no **chat base** (presenter + MFE), sem duplicar em agentes.

Legado: [`apresentacao-rica-chat-onda-9.md`](./apresentacao-rica-chat-onda-9.md), [`melhorias/playbook_ampliacao_graficos_minha_delpi_chat.md`](./melhorias/playbook_ampliacao_graficos_minha_delpi_chat.md), [`melhorias/playbooks_melhoria_minha_delpi_chat/09_dashboards_graficos_apresentacao_rica.md`](./melhorias/playbooks_melhoria_minha_delpi_chat/09_dashboards_graficos_apresentacao_rica.md).

---

## Implementação (jun/2026)

| Componente | Responsabilidade |
|------------|------------------|
| `ChatPresentationDataShapeAnalyzer` | Linhas/colunas, data, numérico, hierarquia, recomendação interna |
| `ChatPresentationDecisionService` | Formato preferido, fallback, `availableViews`, motivo |
| `ChatPresentationInsightService` | Insight automático curto (§16) |
| `ChatPresentationChartPolicyService` | Limites de fatias/pontos e agrupamento «Outros» (§25) |
| `ChatPresentationAxisPreferenceService` | Eixos X/Y padrão (eficiência, operador) + colunas no `config` |
| `ChatChartTypeSelectionService` | Subtipo de gráfico (linha, barra H, rosca, combo, …) |
| `ExternalActionResultPresenter` | Monta `presentation` / `tablePresentation` / `chartPresentation` |
| `ExecuteExternalActionUseCase` | Enriquece metadata com `presentationDecision` |
| MFE `ChatAssistantContent` | Único renderizador: segmentos, toolbar de formato, registry extensível |
| MFE `assistantContentRegistry` | Novos visuais: `registerAssistantSegmentRenderer` |

---

## Pipeline

```
Dados da action → Presenter (table/chart/tree/kpi/text)
               → ExecuteExternalActionUseCase (primary + table/tree/chart + textPresentation)
               → ChatPresentationDecisionService.enrich_metadata
                    (layoutMode, visualOrder, availableViews, selected, insight)
               → MFE buildAssistantContentSegments → ChatAssistantContent
```

Ver: [`../architecture/chat-assistant-content-presentation.md`](../architecture/chat-assistant-content-presentation.md).

---

## Metadata `presentationDecision` (exemplo)

```json
{
  "presentationDecision": {
    "selected": "line_chart",
    "fallback": "table",
    "reason": "dados temporais com valor numérico",
    "layoutMode": "stack",
    "visualOrder": ["text", "table", "line_chart", "chart"],
    "insight": "O maior valor ocorreu em mar/2026; o menor, em jan/2026.",
    "availableViews": ["line_chart", "table", "chart"],
    "dataShape": {
      "rows": 12,
      "columns": 2,
      "hasDate": true,
      "hasNumeric": true,
      "hasCategory": true,
      "hasHierarchy": false
    },
    "intent": "sales_lookup"
  }
}
```

---

## Testes de regressão

| Caso | Dados / pedido | Formato esperado |
|------|----------------|------------------|
| P1 | Lista simples | `table` |
| P2 | Data + valor | `line_chart` |
| P3 | Ranking (nomes longos) | `horizontal_bar` |
| P4 | Participação | `donut` |
| P5 | Indicador único | `kpi` |
| P6 | BOM / hierarquia | `tree` |
| P7 | Texto longo / lousa | `canvas` |
| P8 | Pendências | `checklist` |
| P9 | Muitas categorias | `horizontal_bar` |
| P10 | Sem número | `table` |
| P11 | Meta x realizado | `grouped_bar` |
| P12 | Pedido de gráfico | `chart` |
| P13 | Pedido de tabela | `table` |
| P14 | Dados vazios | `text` |
| P15 | Formato pedido (linha) | `line_chart` |
| P16 | Eficiência fabril (LMP, várias métricas) | `horizontal_bar` + eixo Y `eficiencia_percentual` |

Arquivos: `tests/fixtures/rich_presentation_cases.py`, `tests/unit/domain/services/test_rich_presentation.py`, `test_chat_presentation_axis_preference_service.py`, `test_chat_chart_type_selection_service.py`.

---

## Roadmap

| Fase | Status |
|------|--------|
| 1 — Decisão básica de formato | **Concluída** — API + MFE (`presentationDecision`, insight, toggle inicial, chips de alternância) |
| 2 — Gráficos ampliados | **Concluída** — sync `chartType`, limites, insight, política de fatias |
| 3 — Alternância de visualização | **Concluída** — toolbar em `ChatAssistantContent` (Tabela/Árvore/Gráfico conforme `availableViews`); chips e «Explique esse gráfico»; seletores de eixo no gráfico |
| 4 — Interatividade | **Concluída** — filtros por categoria, eixos configuráveis, explicar gráfico inline (`chartExplanation`, `explain_chart`), drill-down, zoom, export PNG/lousa |
| 5 — Dashboards e insights | **Concluída** — dashboard multi-card, explicar painel inline, `ChatPresentationRecommendationService` + banner/chips de formato alternativo |
| 6 — Métricas e otimização | **Concluída** — auditoria + telemetria MFE; admin com taxas (engajamento, troca de vista/eixo), distribuições e **alertas** heurísticos |

---

## Resumo executivo

Apresentação rica transforma dados em entendimento. O Playbook 09 consolida a escolha automática de formato no chat base; fases 2–6 evoluem sobre a base da Onda 9 sem reimplementar o MFE.
