# Refinamento de dados da sessão (formato e agrupamento)

**Escopo:** follow-ups sobre resultado operacional já obtido  
**Arquitetura pai:** [chat-intelligence-base.md](./chat-intelligence-base.md)

Este fluxo trata refinamento de **dados já presentes na sessão** ou reconsulta da **mesma Action/capability**, não descoberta manual de endpoint. Seleção de Actions continua regida pelo pipeline OpenAPI-first.

Follow-ups do usuário sobre o último resultado operacional podem ser resolvidos de duas formas:

| Estratégia | Quando | Exemplo |
|------------|--------|---------|
| **session** | Payload retido contém as colunas necessárias | TOP 50 por item → «consumo por unidade» |
| **refetch** | Coluna ausente ou o agrupamento precisa do dataset completo | TOP 50 → «agrupar por grupo de produto» |

## Pipeline pré-turno

Ordem em `ChatToolContextPreTurnService._resolve_paginated_shortcuts`:

```text
1. ChatPaginatedExternalActionService.resolve_format_refinement_turn
2. ChatPaginatedExternalActionService.resolve_group_by_session_refinement_turn
3. paginação / consolidação / recuperação de erro
```

Se um refinamento puder reutilizar com segurança o resultado existente, não deve disparar nova descoberta de Action.

## Responsabilidades

| Responsabilidade | Módulo/config |
|------------------|---------------|
| Dimensões de agrupamento | `operational_group_by_refinement.json` |
| Decisão session vs refetch | `ChatOperationalSessionDataRefinementService` |
| Agregação tabular | `ChatTabularDataAggregationService` |
| Atalho in-memory | `ChatOperationalGroupBySessionRefinementService` |
| Recuperação do payload da sessão | `ChatPresentationFormatRefinementService` |
| Reconsulta quando necessária | `ChatOperationalRefinementService.plan_operational_group_by_follow_ups` |
| Aviso de amostra retida | `data_coverage.json` + metadata `sessionDataRefinement` |

A configuração de refinamento descreve **como transformar/reconsultar um resultado já conhecido**. Ela não substitui OpenAPI/Action Catalog e não deve ensinar ao motor qual endpoint selecionar para uma intenção nova.

## Perfil de dimensão

Exemplo:

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
| `strategy` | `local` \| `refetch` \| `auto` | `auto`: tenta local se a coluna existir |
| `localCategoryField` | chave da linha | eixo do agrupamento in-memory |
| `localMetricFields` | lista | métricas agregadas |
| `refetchGroupBy` | parâmetro suportado pela Action | agrupamento usado na reconsulta |

## Estender uma dimensão

1. Validar o contrato real da Action e o payload retido.
2. Adicionar a dimensão à configuração canônica de refinamento, sem duplicar schema OpenAPI.
3. Se houver reconsulta, usar somente parâmetros aceitos pelo schema da Action.
4. Atualizar labels de UI somente quando necessário.
5. Cobrir session, refetch, argumento inválido e resultado parcial nos testes.
6. Validar follow-up em R6 e outcome em R9; incluir demais dimensões R1–R11 aplicáveis.

## Metadata

`sessionDataRefinement` + `dataCoverageNotice` devem deixar explícito quando um agrupamento é calculado apenas sobre a amostra retida.
