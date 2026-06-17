# Refinamento de dados da sessão (formato e agrupamento)

**Status:** implementado (jun/2026)  
**Parent:** [chat-assistant-content-presentation.md](./chat-assistant-content-presentation.md), [chat-intelligence-base.md](./chat-intelligence-base.md)

Follow-ups do usuário sobre o **último resultado operacional** podem ser resolvidos de duas formas, sem duplicar lógica em use case ou MFE:

| Estratégia | Quando | Exemplo |
|------------|--------|---------|
| **session** | Payload retido na conversa contém as colunas necessárias | TOP 50 por item → «consumo por unidade» |
| **refetch** | Coluna ausente ou ranking global no período | TOP 50 → «agrupar por grupo de produto» |

---

## Pipeline pré-turno

Ordem em `ChatToolContextPreTurnService._resolve_paginated_shortcuts`:

```
1. ChatPaginatedExternalActionService.resolve_format_refinement_turn
2. ChatPaginatedExternalActionService.resolve_group_by_session_refinement_turn
3. Paginação / consolidação / recuperação de erro
```

Se (1) ou (2) retornam sucesso, o turno **não** dispara nova seleção de rota.

---

## Módulos canônicos

| Responsabilidade | Módulo | Config |
|------------------|--------|--------|
| Vocabulário + rotas + dimensões | `ChatOperationalGroupByRefinementService` | `operational_group_by_refinement.json` |
| Decisão session vs refetch | `ChatOperationalSessionDataRefinementService` | dimensão: `strategy`, `localCategoryField`, `refetchGroupBy` |
| Agregação tabular | `ChatTabularDataAggregationService` | — |
| Atalho pré-turno (session) | `ChatOperationalGroupBySessionRefinementService` | — |
| Recuperar payload da sessão | `ChatPresentationFormatRefinementService` | mesmo contrato do refinamento de formato |
| Refetch operacional | `ChatOperationalRefinementService.plan_operational_group_by_follow_ups` → `operational_group_by_refinement` | api-delpi: `production_consumption_top_items_group_by.json` |
| Cobertura «amostra retida» | `data_coverage.json` → `sessionAggregateSample` | metadata `sessionDataRefinement` |

---

## Perfil de dimensão (`operational_group_by_refinement.json`)

```json
{
  "value": "unit",
  "label": "unidade de medida",
  "strategy": "local",
  "localCategoryField": "unit",
  "localMetricFields": ["real_consumption_qty"],
  "localSortField": "real_consumption_qty"
}
```

| Campo | Valores | Significado |
|-------|---------|-------------|
| `strategy` | `local` \| `refetch` \| `auto` | `auto`: tenta local se a coluna existir nas linhas retidas |
| `localCategoryField` | chave da linha | Eixo de agrupamento in-memory |
| `localMetricFields` | lista | Métricas somadas |
| `refetchGroupBy` | param API | Valor de `group_by` na reconsulta |

---

## Estender para nova rota ou dimensão

1. **Chat:** entrada em `operational_group_by_refinement.json` → `routes[]` + `dimensions[]`.
2. **API (se refetch):** dimensão em `api-delpi/app/content/production_consumption_top_items_group_by.json`.
3. **Colunas UI:** perfil em `column_labels.json`.
4. **Testes:** `test_chat_operational_session_data_refinement_service.py`, `test_chat_operational_group_by_session_refinement_service.py`.

---

## Metadata (session)

`sessionDataRefinement` + `dataCoverageNotice` (`sessionAggregateSample`) deixam claro que o agrupamento é sobre a **amostra retida**.
