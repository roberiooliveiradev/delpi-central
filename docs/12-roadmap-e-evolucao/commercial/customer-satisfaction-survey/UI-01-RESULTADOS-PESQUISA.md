# Página 01 — Resultados da Pesquisa de Satisfação do Cliente

> **Estado:** ESPECIFICAÇÃO DE UI / WIREFRAME PROPOSTO — **NÃO IMPLEMENTADO**. Entrega 1. Ref observada: `main` / `c135a9823e054ce1234f73eee627548043737264` em 11/11/2026; confirmar HEAD/branch/working tree antes de implementar. Owner visual: `plugins/commercial` ou `plugins/public-hub` conforme indicado. Autoridade de regra e dados: `commercial-api`.
>
> **Fontes:** [índice mestre](./REQUIREMENTS-INDEX.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md), [plano de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md) e plano Word integral; código existente: \`plugins/commercial/src/features/overview/OverviewPage.tsx\`, \`features/analytics/AnalyticsOtdPage.tsx\`, \`features/analytics/components/AnalyticsClosingRateSeriesChart.tsx\`.

**Regra visual obrigatória:** reaproveitar exclusivamente componentes de `@delpi/plugin-ui/index` e wrappers/compostos já usados no Portal, sem implementar novo componente visual nativo da página. Layout semântico e ligação de dados React são permitidos; se uma necessidade realmente não estiver coberta, registrar lacuna e passar pelo Abstraction Gate antes de alterar o PluginUI. Não criar CSS/kit de design paralelo.

## 1. Objetivo, públicos e rota

Abrir **diretamente em Resultados** ao escolher `Início > Marketing > Pesquisa de satisfação do cliente`. Path de UI proposto: `/apps/commercial/satisfaction-results` (conservar consistência com `pluginRoutes.ts`, sem hardcode no componente). Usuário `commercial.access` vê somente consolidados; `commercial.marketing` ou `commercial.manage` também podem acessar a área de configuração e consultar, por ação autorizada, respostas individuais. É uma página do MFE Comercial, não página pública.

**Decisão de navegação:** neste ciclo o acesso a Configuração pode ser uma aba/ação no cabeçalho para o gestor, mas os dados de gestão não são montados nem buscados para `access`. A lista/detalhe de campanhas constitui a segunda página especificada em [02](./UI-02-CONFIGURACAO-PESQUISAS.md). Não criar intermediária “Home Marketing”.

## Decisão visual aprovada — Hero único para controles da página (11/11/2026)

**Todos os filtros globais e botões de ação da página de Resultados devem ficar no `CommercialPageHero` existente**, com densidade compacta, reproduzindo o padrão real das páginas analíticas do Comercial (`OverviewPage.tsx`, `AnalyticsOtdPage.tsx`, `AnalyticsOpportunitiesPage.tsx`). `CommercialPagePath` continua acima do Hero se exigido pelo padrão de rota. **Não** criar header próprio, barra de filtros separada abaixo do Hero, nem abas decorativas que dupliquem a navegação.

- **Headline do Hero:** título “Pesquisa de Satisfação do Cliente”, descrição curta, ajuda contextual via `CommercialSectionHintLabel`, ações à direita via `CommercialActionButton`: **Atualizar**, **Configuração** (somente `commercial.marketing`/`commercial.manage`). Nenhum indicador é exibido no Hero.
- **Corpo inferior do Hero:** controles `CommercialSelectField`, `CommercialMultiSelectField`, `CommercialFilterBarShell`/`cmFiltersKit` e `CommercialClearFiltersButton`: Ano, Campanha/Ano completo, segmento/estratégicos, cliente, vendedor, região, tempo de relacionamento e faturamento — **apenas quando a origem e a segurança forem confirmadas no backend**. `Limpar filtros` no próprio Hero. Não usar filtros operacionais de pedidos por herança.
- **Exceção semântica necessária:** ações **contextuais de linha ou conteúdo** (abrir uma resposta, copiar link de participante) permanecem junto ao item afetado; confirmação/cancelamento continuam no diálogo/formulário correspondente. Essa exceção não autoriza ações globais fora do Hero.
- **Responsividade:** controles quebram em linhas ou recolhem dentro da área inferior do mesmo Hero usando kit existente; nunca mover filtros globais para um card separado. A seção seguinte inicia diretamente pelo **Resumo executivo**.
- **Status:** decisão de composição visual aprovada pelo solicitante; sem implementação neste commit.

## 2. Wireframe desktop — ordem e hierarquia

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [CommercialPagePath: Marketing / Pesquisa]                                 │
├─ COMMERCIAL PAGE HERO (compacto) ────────────────────────────────────────────┤
│ Pesquisa de satisfação do cliente        [Atualizar] [Configuração]*         │
│ Acompanhe os resultados e a evolução da satisfação                           │
│                                                                              │
│ [Ano ▼] [Campanha / Ano completo ▼] [Segmento ▼] [Mais filtros ▼]          │
│ [Cliente ▼] [Vendedor ▼] [Região ▼] [Tempo ▼] [Faturamento ▼]              │
│ [Limpar filtros]                              *somente marketing/manage     │
├──────────────────────────────────────────────────────────────────────────────┤
│ RESUMO EXECUTIVO                                                             │
│ [IGS /5] [NPS] [Taxa resposta] [Satisfeitos %] [Críticos %]                 │
│ Contexto: pesquisa/intervalo + população + indisponibilidade quando houver  │
├──────────────────────────────────────────────────────────────────────────────┤
│ AVALIAÇÃO DAS 10 DIMENSÕES                       | EVOLUÇÃO HISTÓRICA       │
│ Qualidade          ━━━━━━━━━ 4,6 (n=...)         | [IGS ▼] [Semestre ▼]    │
│ Prazo              ━━━━━━━   3,8                 | série por campanha      │
│ ... 8 dimensões restantes                        | anos selecionáveis      │
├──────────────────────────────────────────────────────────────────────────────┤
│ COMPARAÇÃO GERAL / ESTRATÉGICOS / DEMAIS                                     │
│ Tabela: IGS | NPS | taxa | satisfeitos | críticos | dimensões                 │
├──────────────────────────────────────────────────────────────────────────────┤
│ HISTÓRICO ANUAL / SEMESTRAL                                                  │
│ Tabela de campanhas: período, amostra, IGS, NPS, tendências                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ RESPOSTAS POR EMPRESA*                                                       │
│ [Buscar empresa] [Tabela restrita] [Abrir leitura da resposta]               │
│ *renderizar e consultar SOMENTE para marketing/manage                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Mobile/tablet:** filtros em fluxo vertical/colapsável no componente de filtros oficial; KPIs em 1–2 colunas; gráfico em largura integral; tabelas usam padrões de responsividade/overflow do `CommercialDataTable`; sem esconder nomes ou denominadores relevantes. Não inventar novos “mobile cards” quando o kit já prevê apresentação adaptativa.

## 3. Wireframe dos estados

```text
┌─ Pesquisa de satisfação do cliente ─────────────────────────────────────────┐
│ [Ano ▼] [Campanha ▼]                                                         │
│ [Carregando indicadores…]  → CommercialLoadingCard                          │
│                                                                            │
│ Sem campanha: "Ainda não há pesquisas encerradas."                          │
│ Sem respostas: "Nenhuma resposta para este período."                        │
│ Baixa amostra: "Resultado indisponível para proteger a confidencialidade."  │
│ Falha: "Não foi possível consultar os resultados." [Tentar novamente]       │
└────────────────────────────────────────────────────────────────────────────┘
```

Não substituir falta de resposta por `0`. Onde a fonte não possui dimensão, mostrar “Indisponível” e não inventar valor.

## 4. Mapa exato de componentes reutilizados

| Região | Reuso verificado | Fonte real / regra |
|---|---|---|
| Hero/título/todas ações globais | `CommercialPageHero`, `CommercialSectionHintLabel`, `CommercialActionButton`, `CommercialPagePath` | Hero compacto com ações Atualizar e Configuração; wrappers PluginUI de `commercialUi.ts`, padrão `OverviewPage.tsx` |
| Organização visual | `SectionCard` ou `CommercialSectionCard` | PluginUI + wrapper; mesmas classes/labels do Portal |
| Navegação Resultados/Configuração | `CommercialUnderlineNav` | Wrapper de `createDashboardUnderlineNav` já exportado; adequar às props atuais |
| Filtros globais dentro do Hero | `CommercialFilterBarShell`, `CommercialSelectField`, `CommercialMultiSelectField`, `CommercialClearFiltersButton`, `cmFiltersKit` | **Como children do `CommercialPageHero`**, não abaixo; `commercialUi.ts`, padrão `AnalyticsFilters.tsx` |
| 5 KPIs | `CommercialMetricCard` | Wrapper existente; não usar `CommercialDashboardKpiCard` se não houver metas/IDD |
| 10 dimensões | `CommercialHorizontalValueBars` | Wrapper real do PluginUI em `commercialUi.ts`; confirmar formato das props antes do código |
| Evolução IGS/NPS | `ChartViewShell`, `MultiTypeSeriesChart`, `ChartTypeSegmentToggle`, `ChartOverlayOptionsPopover` quando necessários | PluginUI, usados em `AnalyticsClosingRateSeriesChart.tsx`; **não copiar seu serviço de dados** |
| Comparação/histórico | `CommercialDataTable`, `CommercialPagination` | Wrappers do PluginUI com estilo Comercial |
| Respostas restritas | `CommercialDataTable`, `CommercialHostDrawer` ou `CommercialDetailCard` | Reuso para leitura, nunca editor; autorização backend |
| Carregando/erro/vazio | `CommercialLoadingCard`, `EmptyState`, `CommercialStateBanner` | PluginUI e `commercialUi.ts` |

**Atenção ao gráfico:** a lib já dispõe dos componentes mencionados; a escolha entre linhas/colunas e escala será validada pela API/dados reais. Sem componente `SurveyChart` ou `SatisfactionKpiCard` próprio na camada de página. Composição leve usando componentes existentes é aceitável; abstração nova somente se comprovadamente indispensável.

## 5. Comportamento dos filtros e cálculos

- Seletores principais: **Ano** e **Campanha** (`Ano completo` ou campanha específica). Ano completo **recalcula** IGS/NPS e todos os indicadores com união das respostas válidas; não calcula média de médias sem pesos. Exibir número de respostas e participantes do período.
- Segmentações solicitadas no Word: cliente, segmento, vendedor, região, tempo de relacionamento, volume/faturamento e clientes estratégicos versus demais; expor **somente filtros que o backend comprovar**, com informações de domínio/período. Para `commercial.access`, impedir recortes de cliente individual ou amostras pequenas que revelem respostas.
- Não aplicar filtros genéricos da Visão Geral (carteira, pedidos ou faturamento) silenciosamente. Pesquisa tem filtro próprio e consulta oficial.
- Ordem da análise: KPIs → dimensões → evolução histórica (semestre/ano) → comparação Geral/Estratégicos/Demais → histórico em tabela. Campanhas com populações distintas mostram denominadores; série histórica não finge mesma amostra.
- KPIs: IGS, NPS, taxa de resposta, satisfeitos e críticos. `Respondentes / participantes` é contexto da taxa, não sexto KPI obrigatório.
- Escala IGS e 10 dimensões: 1–5, NPS -100..100, taxa e percentuais 0–100. O eixo de gráfico nunca altera fórmula oficial. Cada dimensão indica amostra válida; `Não se aplica` não entra na média.
- Histórico anual: apresentar IGS/NPS recalculados por todas as respostas do ano; escolher campanha anterior real para comparação, não deduzir “semestre” a partir de nome.
- Planos de ação concluídos: **entrega 2 obrigatória** do produto completo; não exibir como zero nesta entrega.

## 6. API, segurança e componentes de fluxo

| Ação | Contrato backend planejado | Visibilidade |
|---|---|---|
| Resultados, histórico, dimensões, comparações | `GET /satisfaction-surveys/results` (consulta tipada e agregada) | `commercial.access` ou Gestão; sempre com proteção de pequenos grupos |
| Respostas por empresa | `GET /satisfaction-surveys/campaigns/{campaign_id}/responses`, `GET /satisfaction-surveys/responses/{response_id}` | Somente `commercial.marketing`/`commercial.manage` |
| Abrir configuração | Navegação local `pluginRoutes.ts`, autorizada também no backend | Só Gestão |

Não enviar para o frontend agregados identificáveis “para esconder com CSS”; o backend devolve somente conteúdo permitido. Evitar `GET` privado em efeitos executados por usuários `access`.

## 7. Critérios de aceite e testes da página

1. A rota resolve no MFE e a página abre em Resultados; gerente acessa Configuração; Access só vê agregados.
2. Todos os componentes visuais constam no PluginUI/CommercialUi existentes; não há componentes estilizados novos na página.
3. Filtros por ano/campanha produzem números canônicos e denominadores coerentes; carregamento/erro/sem dados/sem amostra são distintos.
4. Tabela e gráfico usam critérios oficiais; evolução histórica por várias campanhas não depende de um ano fixo.
5. Falta de fonte de segmento é mostrada corretamente; filtro de pequeno grupo não vaza informação.
6. Resposta individual jamais aparece/é buscada sob `commercial.access`; teste negativo REST/MCP.
7. Desktop, tablet, celular, teclado, foco, nomes acessíveis e zoom atendem ao kit existente.
8. CAIO `read` e `analyze` usam os mesmos casos de uso/indicadores do backend; execução por incremento e relatório documentado.

**Referências de implementação:** `plugins/commercial/src/app/pluginRoutes.ts`, `app/pluginNavigation.ts`, `src/App.tsx`, `src/api/httpClient.ts`, `src/app/commercialUi.ts`, `features/analytics/components/AnalyticsClosingRateSeriesChart.tsx` e testes estruturais da Visão Geral.