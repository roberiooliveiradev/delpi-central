# 25 — Visão Geral — Indicadores Financeiros

## Estado

**TARGET / SOURCE_INVENTORY_REQUIRED**

## Objetivo

A página **Visão geral** é a superfície analítica do Portal Controladoria & Finanças.

Ela deve responder:

> Como está a situação financeira e gerencial relevante para Controladoria & Finanças, com indicadores confiáveis, comparáveis e rastreáveis às suas fontes?

## Decisão de produto

```text
VISÃO_GERAL = INDICADORES FINANCEIROS
```

Não confundir com o Cockpit da Competência.

```text
Visão geral = visão analítica/gerencial do Portal
Cockpit = situação operacional de uma competência do fechamento
```

## Boundary com Portal Financeiro P0

`plugins/financial` + `financial-api` continuam produto distinto.

A nova Visão geral pode reutilizar fontes, contracts, indicadores canônicos, owners e componentes compartilháveis.

Ela não deve copiar telas do Portal Financeiro, duplicar fórmula/SQL, mover ownership ou criar segunda fonte para o mesmo indicador.

```text
REUSE SOURCE/OWNER != COPY PRODUCT
```


## Reuso obrigatório de `@delpi/plugin-ui`

A Visão geral deve reutilizar o kit analítico da plataforma; não criar cards KPI, containers de gráfico, filtros ou tabelas locais equivalentes.

Import canônico:

```ts
import {
  KpiCard,
  MetricKpiCard,
  ChartCard,
  QuickPeriodSelector,
  createDashboardFiltersKit,
  LineSeriesChart,
  AreaSeriesChart,
  BarSeriesChart,
  ComparativeAreaChart,
  DataTableSection,
  EmptyState,
  LoadingState,
  StateBox,
} from "@delpi/plugin-ui/index";
```

Estilos/runtime:

```ts
await import("@delpi/plugin-ui/styles");
```

Diretriz de uso:

| Necessidade | Reuso canônico |
|---|---|
| KPI principal | `KpiCard` ou `MetricKpiCard` |
| container de visualização | `ChartCard` |
| filtro rápido de período | `QuickPeriodSelector` |
| filtros gerais | `createDashboardFiltersKit` |
| tendência temporal | `LineSeriesChart` / `AreaSeriesChart` |
| comparação categórica | `BarSeriesChart` |
| comparação de áreas/séries | `ComparativeAreaChart` quando o contrato justificar |
| drilldown tabular | `DataTableSection` |
| unavailable/empty/loading | `StateBox`, `EmptyState`, `LoadingState` |

A escolha do tipo de gráfico vem do **contrato do indicador**, não da disponibilidade de um componente.

**DO NOT RECREATE:** KPI card, chart card, period selector, filter chrome, chart primitive ou data table que já exista no kit.

## Indicadores

O conjunto exato de indicadores ainda precisa de inventário técnico/funcional.

```text
INDICATOR_SET = TO_INVENTORY
```

Cada indicador só entra quando possuir:

```text
NAME
BUSINESS_MEANING
OWNER
SOURCE
FORMULA
GRAIN
PERIOD
FRESHNESS
UNIT
FAILURE_BEHAVIOR
DRILLDOWN
AUTHORIZATION
TEST_EVIDENCE
```

Não inventar indicador apenas porque existe visualização semelhante em outro Portal.

## Composição lógica

```text
OverviewHeader
→ FinancialIndicatorGrid
→ TrendSection
→ ComparisonSection
→ AttentionSection
→ SourceFreshness
→ ContextualHelp
```

Os nomes são lógicos, não contrato React.

## FinancialIndicatorGrid

Deve priorizar poucos indicadores principais e permitir expansão/drilldown.

Regras:
- número sempre acompanhado de unidade;
- período/contexto explícito;
- source/freshness disponível;
- erro de source não aparece como zero;
- parcial não se apresenta como consolidado;
- valores calculados indicam regra/version quando material.

## Tendências e comparativos

Podem incluir, quando suportados pelo owner: evolução temporal, comparação entre períodos, comparação entre unidades/dimensões, decomposição do indicador e drilldown para detalhe.

Nenhum comparativo pode inventar baseline ausente.

## AttentionSection

Pode destacar variações relevantes, sources indisponíveis, indicadores fora do comportamento esperado e itens que mereçam investigação.

Não usar threshold inventado. Limites/targets precisam de owner e contrato.

## Filtros

Filtros dependem do grain dos indicadores aprovados e podem incluir, se suportados pela fonte, período, empresa/unidade e dimensão gerencial.

Filtro de filial/unidade é contexto de dado, não permission code do Portal.

## IA

A IA pode explicar indicador, resumir variação, comparar períodos, apontar source e sugerir investigação.

Não pode redefinir fórmula, alterar target, esconder source indisponível, afirmar causalidade sem evidência ou autorizar ação.

## Estados

Cobrir `LOADING`, `EMPTY`, `PARTIAL`, `UNAVAILABLE_SOURCE`, `ERROR`, `FORBIDDEN` e `NOT_FOUND`.

Indicadores independentes devem degradar isoladamente quando o contract permitir.

## Help

Deve explicar significado, período, unidade, fórmula em linguagem de negócio, source, freshness, diferença entre indisponível e zero e como acessar drilldown.

## Inventário obrigatório antes da implementação

Inventariar os indicadores financeiros existentes, incluindo owners, APIs/BFFs atuais, api-delpi, strategic-indicators-api, Portal Financeiro P0 e demais sources autorizados.

Classificar cada candidato:

```text
REUSE_AS_IS
REUSE_SOURCE_RECOMPOSE_UI
NEW_INDICATOR_REQUIRED
OUT_OF_SCOPE
UNKNOWN
```

Se duas fórmulas diferentes existirem para o mesmo nome, registrar `EXECUTION_DRIFT` e não escolher silenciosamente.

## Critérios de aceite

- acessível por `controllership-finance.access`;
- nenhum permission code específico por indicador;
- source indisponível != zero;
- indicador sem owner/fórmula não entra em produção;
- drilldown preserva contexto;
- Portal Financeiro P0 continua distinto;
- desktop/mobile, claro/escuro, teclado/foco;
- Help sincronizada.
