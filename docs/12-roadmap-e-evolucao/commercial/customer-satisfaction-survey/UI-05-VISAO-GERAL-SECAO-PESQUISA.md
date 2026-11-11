# Ponto de entrada B — Seção de Satisfação na Visão Geral existente

> **Estado:** ESPECIFICAÇÃO DE UI / WIREFRAME PROPOSTO — **NÃO IMPLEMENTADO**. Entrega 1. Ref observada: `main` / `c135a9823e054ce1234f73eee627548043737264` em 11/11/2026; confirmar HEAD/branch/working tree antes de implementar. Owner visual: `plugins/commercial` ou `plugins/public-hub` conforme indicado. Autoridade de regra e dados: `commercial-api`.
>
> **Fontes:** [índice mestre](./REQUIREMENTS-INDEX.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md), [plano de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md) e plano Word integral; código existente: \`plugins/commercial/src/features/overview/OverviewPage.tsx\`, \`src/app/commercialUi.ts\`, \`features/analytics/components/AnalyticsClosingRateSeriesChart.tsx\`.

**Regra visual obrigatória:** reaproveitar exclusivamente componentes de `@delpi/plugin-ui/index` e wrappers/compostos já usados no Portal, sem implementar novo componente visual nativo da página. Layout semântico e ligação de dados React são permitidos; se uma necessidade realmente não estiver coberta, registrar lacuna e passar pelo Abstraction Gate antes de alterar o PluginUI. Não criar CSS/kit de design paralelo.

## 1. Decisão: uma seção na página existente

A página `OverviewPage.tsx` **já contém** `CommercialPageHero`, `SectionCard`, `CommercialDashboardKpiCard`, `CommercialMetricCard` e gráficos. Acrescentar **uma única seção “Pesquisa de Satisfação do Cliente”** contendo **todos os indicadores gerais da entrega 1**, para usuários autorizados do Comercial, sem criar uma nova página ou colocar cada indicador em uma seção diferente.

**Corte de dados:** última campanha encerrada. É um resumo geral independente dos filtros atuais de pedidos/carteira da Visão Geral, evitando que o mesmo IGS mude com filtros comerciais sem o usuário perceber. Informar claramente campanha/período e quantidade de respondentes.

## 2. Wireframe

```text
┌─ Visão Geral — seções já existentes ──────────────────────────────────────┐
│ [KPI ROL...] [Pedidos...] [Gráficos comerciais...]                       │
├──────────────────────────────────────────────────────────────────────────┤
│ PESQUISA DE SATISFAÇÃO DO CLIENTE     Última campanha encerrada: 2026/2 │
│                                                                          │
│ [IGS /5]  [NPS]  [Taxa de resposta]  [Satisfeitos %]  [Críticos %]       │
│ Respondentes: N de N participantes cadastrados                           │
│                                                                          │
│ Médias das 10 dimensões      ━━━━━━━━━━ barras compactas                │
│ Evolução do IGS/NPS          ───●────●────●── (campanhas anteriores)      │
│                                                       [Ver análise...]    │
└──────────────────────────────────────────────────────────────────────────┘
```

Sem lista de clientes, tabela de respostas identificadas, comentários, tokens ou cadastro de campanhas. O indicador de conclusão de planos de ação será adicionado na **entrega 2 obrigatória**, quando houver fonte oficial.

## 3. Mapa real de componentes

| Região | Reutilizar | Evidência |
|---|---|---|
| Container da seção | `SectionCard` com `cmSectionCardClassNames`/`cmSectionLabels` | Padrão em `OverviewPage.tsx` |
| KPIs compactos | `CommercialMetricCard` | Wrapper `createMetricKpiCard` em `commercialUi.ts` |
| Dez dimensões | `CommercialHorizontalValueBars` | Wrapper de `HorizontalValueBars` do PluginUI |
| Evolução compacta | `ChartViewShell` e `MultiTypeSeriesChart` se o espaço permitir; ou `CommercialCompareSparkline` já exportado | Bibliotecas reais no Portal/PluginUI |
| Ação “Ver análise completa” | `CommercialActionButton` e `navigatePluginView` | Uso atual no MFE |
| Loading, erro ou vazio | `CommercialLoadingCard`, `EmptyState` / `CommercialStateBanner` | Uso em Visão Geral |

## 4. Regras de exibição e segurança

- A `commercial-api` fornece projeção **somente agregada** do mesmo serviço oficial `GET /satisfaction-surveys/results`. Não introduzir endpoint privado nem pré-carregar respostas para filtrar no cliente.
- A seção é visível a `commercial.access` e aos gestores. Backend proíbe individualização e suprime grupos com amostra pequena; caso a amostra seja insuficiente, mostrar estado protegido em vez de valor.
- Sem campanha encerrada: “Pesquisa ainda sem resultados consolidados”. Sem respostas: IGS/NPS indisponíveis, não `0`. Erro de API ≠ ausência de resposta.
- Taxa de resposta = respostas ÷ participantes cadastrados, sem sugerir comprovante de e-mail enviado (convite manual).
- Ação abre [Página 01 — Resultados](./UI-01-RESULTADOS-PESQUISA.md), conservando o padrão de navegação.
- A seção ocupa o fluxo responsivo existente e não altera a estrutura do dashboard; dados fictícios só podem existir no wireframe/documento.

## 5. Critérios de aceite

1. Uma só seção com título canônico, 5 KPIs e visão compacta das 10 dimensões e evolução; sem duplicação de cards por área.
2. Nenhuma informação por cliente ou chamada a endpoints privados, inclusive em logs/devtools sob `commercial.access`.
3. Dados da última campanha encerrada, com período/denominadores, calculados no backend.
4. Estados distintos carregando/sem campanha/sem respostas/amostra protegida/erro.
5. Responsivo e acessível, usando somente componentes PluginUI/CommercialUi reais, respeitando o padrão visual atual.
6. Testes de integração e de autorização + paridade do serviço agregado com CAIO `analyze`.
