# UI-01 — Página de Resultados da Pesquisa de Satisfação do Cliente

> **Status:** proposta de UX; **Resumo Executivo, Evolução Histórica, Avaliação das Dez Dimensões e Comparação entre Grupos aprovados visualmente**, demais seções ainda em revisão; **não implementada**. Regra do Hero com todos os filtros e ações globais: **decisão aprovada**. A nova ordem das seções e composição do resumo foram aceitas para registro, sujeitas à revisão por etapas. Branch consultada: `main`, HEAD-base desta revisão `4155399bb77e0b675916fcbc117d2db58d997f14` (revalidar antes da implementação).
>
> **Owner visual:** `plugins/commercial` (MFE). **Autoridade de regras, métricas, acesso e privacidade:** `commercial-api`; origem de clientes e atributos comerciais conforme fonte oficial via `api-delpi`/TOTVS. Esta especificação não concede autorização de implementação ou alteração de contrato backend.
>
> **Referências:** [índice mestre](./REQUIREMENTS-INDEX.md), [Word e decisões de negócio](./BUSINESS-DECISIONS.md), [contrato da entrega 1](./SURVEY-FIRST-RELEASE-CONTRACT.md), [plano global de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md). Código verificado em `plugins/commercial/src/app/commercialUi.ts`, `features/overview/OverviewPage.tsx`, `features/analytics/AnalyticsOtdPage.tsx`, `features/analytics/AnalyticsOpportunitiesPage.tsx`, `features/analytics/components/AnalyticsClosingRateSeriesChart.tsx`, `features/analytics/components/AnalyticsRolSeriesChart.tsx`, `plugins/plugin-ui/src/components/layout/PageHero.tsx`, `plugins/plugin-ui/src/components/charts/{HorizontalValueBars.tsx,ChartViewShell.tsx,MultiTypeSeriesChart.tsx}`.

## 1. Finalidade e critérios de UX

A entrada `Início > Marketing > Pesquisa de satisfação do cliente` abre diretamente a **página de Resultados**, rota candidata `/apps/commercial/satisfaction-results`, usando `pluginRoutes.ts`/`navigatePluginView`, não URL absoluta hardcoded em componentes. A visão serve a três perguntas: **como está a satisfação, como evoluiu e onde investigar oportunidades de melhoria**. O público `commercial.access` recebe exclusivamente agregados; `commercial.marketing` ou `commercial.manage` tem adicionalmente navegação para Configuração e consulta individual autorizada.

**Ordem proposta definitiva para revisão:** (1) `CommercialPagePath` e Hero; (2) Resumo executivo; (3) Evolução histórica; (4) Avaliação das dez dimensões; (5) Comparações por grupo; (6) consulta por empresa **somente para gestores**. A Evolução é gráfico combinado IGS/NPS com dois eixos, sem tabela histórica fixa, com detalhes por campanha sob demanda e exportação oficial. O indicador de ações concluídas será acrescentado na **entrega 2 obrigatória**, nunca simulado na primeira.

**Regra visual não negociável:** compor a página com componentes já publicados por `@delpi/plugin-ui/index` e wrappers existentes em `plugins/commercial/src/app/commercialUi.ts`. Não criar `SurveyKpi`, `SurveyChart`, botões nativos estilizados, CSS da página ou segundo design system. JSX de composição e transformação de dados são aceitáveis; gap real de componente => TO_INVENTORY + Abstraction Gate antes de alterar PluginUI.

## 2. Wireframe principal — desktop

```text
┌─ Comercial / Marketing / Pesquisa (CommercialPagePath) ───────────────────┐
│                                                                          │
├─ COMMERCIAL PAGE HERO ────────────────────────────────────────────────────┤
│ PORTAL COMERCIAL                                                         │
│ Pesquisa de Satisfação do Cliente                 [Atualizar] [Config.]* │
│ Indicadores, evolução e percepção dos clientes.                          │
│                                                                          │
│ [Ano ▼] [Campanha / Ano completo ▼] [Grupo ▼]                            │
│ [Mais filtros ▾]  (expande DENTRO do mesmo Hero)                          │
│   [Segmento] [Cliente**] [Vendedor] [Região] [Relacionamento] [Faturamento]│
│ [Limpar filtros]                  Estado: filtros adicionais ativos (N)  │
├──────────────────────────────────────────────────────────────────────────┤
│ RESUMO EXECUTIVO      2026/2 · 72 respostas / 100 participantes        │
│ [IGS 4,3/5 Δ+0,2] [NPS +48 Δ+7] [Resposta 72% Δ−2 p.p.] [Satis. 84%]  │
│ [Críticos 6%]   Delta somente quando há base anterior comparável        │
├──────────────────────────────────────────────────────────────────────────┤
│ EVOLUÇÃO HISTÓRICA                                                       │
│ [Linhas ▼] [Configurar séries ▼] [Exportar ▼] — barra do gráfico         │
│ [gráfico combinado: IGS esquerdo (1–5) + NPS direito (−100 a +100)]      │
├──────────────────────────────────────────────────────────────────────────┤
│ AVALIAÇÃO DAS 10 DIMENSÕES                                               │
│ [Ranking obrigatório: menor média primeiro; empate = ordem oficial]       │
│ Prazo de entrega       ━━━━━━━   3,8  (n válido)                          │
│ Flexibilidade          ━━━━━━━━  4,0                                      │
│ ... completar dez itens; eixo/máximo fixo 5                              │
├──────────────────────────────────────────────────────────────────────────┤
│ COMPARAÇÃO GERAL / ESTRATÉGICOS / DEMAIS                                 │
│ [Indicador | Geral | Estratégicos | Demais] — 5 indicadores visíveis    │
│ [Comparar também as dez dimensões ▾] — 10 linhas extras na mesma tabela │
│ valores supressos se amostra abaixo do limiar do backend                 │
├──────────────────────────────────────────────────────────────────────────┤
│ RESPOSTAS POR EMPRESA* (somente marketing/manage)                        │
│ Tabela apenas leitura → abrir resposta em CommercialHostDrawer           │
└──────────────────────────────────────────────────────────────────────────┘
* Controle e autorização no backend. **Cliente individual não é filtro
  disponível ao público agregado se permitir reidentificação.
```

**Exemplos numéricos:** exclusivamente ilustrativos; não inserir seed/mock persistente para produção. Não há dados reais demonstrados.

### Wireframe mobile

```text
┌─ PagePath ────────────────┐
│ Hero compacto             │
│ Título + descrição        │
│ [Atualizar] [Config.]*    │
│ [Ano ▼]                   │
│ [Campanha ▼]              │
│ [Grupo ▼]                 │
│ [Mais filtros ▾]          │
│ [Limpar filtros]          │
├───────────────────────────┤
│ Resumo executivo          │
│ [IGS]                     │
│ [NPS]                     │
│ [Taxa]                    │
│ [Satisfeitos]             │
│ [Críticos]                │
├───────────────────────────┤
│ Evolução histórica        │
│ [Tipo ▼] [Séries ▼] [CSV]│
│ [gráfico IGS + NPS]       │
│ [detalhe após toque]      │
├───────────────────────────┤
│ Dez dimensões             │
│ [10 barras empilhadas]    │
├───────────────────────────┤
│ Comparações               │
│ [5 cards comparativos]    │
│ [10 extras após expandir] │
├───────────────────────────┤
│ Respostas restritas*      │
└───────────────────────────┘
```

## 3. Hero — inventário fechado de conteúdo e reuso

A página real usa **`CommercialPageHero` com densidade `compact` (default do wrapper)**, exatamente como `OverviewPage.tsx`, `AnalyticsOtdPage.tsx` e `AnalyticsOpportunitiesPage.tsx`. O Hero real do PluginUI possui `eyebrow`, `title`, `description`, `badge`, `actions` e `children` (corpo inferior). `CommercialPagePath` aparece antes, como padrão analítico. Não reproduzir o Hero manualmente por `div`.

| Local | Componente existente (origem) | Conteúdo / comportamento |
|---|---|---|
| Antes do Hero | `CommercialPagePath` (`commercialUi.ts`) | Trilha e retorno para Início/Marketing, conforme API de path e rota existente |
| Eyebrow | Prop `eyebrow` de `CommercialPageHero` | “Portal Comercial” |
| Título | `CommercialSectionHintLabel` dentro de `title` do Hero | “Pesquisa de Satisfação do Cliente” e ajuda contextual real |
| Descrição | Prop `description` | “Acompanhe os resultados das pesquisas e a evolução da satisfação dos clientes.” |
| Ações globais à direita | `CommercialActionButton` (`ActionButton` do PluginUI) | “Atualizar”; “Configuração” só para gestão, navega à UI-02 |
| Filtros principais no corpo do Hero | `CommercialSelectField` | Ano (anos com dados), Campanha (campanha real ou Ano completo), Grupo (Geral/Estratégicos/Demais) |
| Controles complementares **dentro** do Hero | `CommercialFilterBarShell`, `cmFiltersKit`, `CommercialSelectField`, `CommercialMultiSelectField`, `CommercialTextField` conforme filtros reais | Segmento, cliente, vendedor, região, tempo de relacionamento e faturamento **somente com fonte oficial e permissão** |
| Área expansível de filtros | Preferir recursos de `cmFiltersKit`/`CommercialFilterBarShell` já exportados e inspecionar suas props/testes na etapa de implementação | Acionador “Mais filtros” fica no Hero, expansão no próprio Hero. **TO_INVENTORY:** comportamento/expander exato; não inventar componente `CommercialFilterPopover` |
| Limpar e contar filtros | `CommercialClearFiltersButton` + texto acessível | Limpa somente filtros de pesquisa, não estado de outros módulos |
| Recarregar resultados | `CommercialActionButton` | Refetch real com loading e estados; não navegar, não enviar formulário |

**Decisão semântica aprovada:** filtros de dados da página e ações globais ficam **somente no Hero**; controles de apresentação do gráfico (tipo, cores, visibilidade, tendências e exportação da série) ficam **no `ChartViewShell`**, como nas demais páginas do Comercial. Evolução inicial apresenta **IGS e NPS juntos**; visibilidade individual pode ser personalizada no inspetor de séries. A ordenação inicial das dimensões é menor média primeiro. Ações contextuais permanecem junto ao seu conteúdo.

**Volume e desempenho:** Ano/Campanha/Grupo sempre visíveis. Controles menos frequentes em “Mais filtros”, dentro do mesmo Hero; estado de filtros ativos permanece identificável. A seleção `Ano completo` só é oferecida se a API suportar consolidação adequada. Não usar `AnalyticsFilters` diretamente se sua semântica de pedidos/competência não corresponder à pesquisa: reutilizar **as primitivas oficiais**, não seus filtros operacionais.

## 4. Resumo executivo — composição aprovada, responsividade e PluginUI

> **Decisão de UX registrada em 11/11/2026:** cinco KPIs compactos com mesmo peso visual, todos com tendência em relação à campanha anterior **quando válida**, descrição da métrica e contexto da amostra. Abaixo é especificação de UI e testes, **não evidência de implementação**. A composição é revisada nesta etapa; fórmulas pertencem ao backend.

### 4.1 Conteúdo, ordem, hierarquia e semântica

A seção inicia **imediatamente depois do Hero**. O título é **“Resumo executivo”**. Na mesma faixa de cabeçalho, mostrar identificação exata da campanha/período selecionado e **“N respostas de N participantes cadastrados”** com fonte e contagem oficiais. Não criar sexto KPI “Respondentes”; o denominador está no cabeçalho e no contexto da Taxa de resposta. Se o filtro abranger múltiplas campanhas, explicitar **respostas por empresa/campanha** e participantes elegíveis por campanha, em vez de insinuar empresas únicas.

**Ordem fixa dos cinco cards:** 1. **IGS**; 2. **NPS**; 3. **Taxa de resposta**; 4. **Satisfeitos**; 5. **Críticos**. Todos têm mesmo tamanho/hierarquia no desktop e na composição responsiva, nenhum recebe destaque especial ou largura dupla. Não destacar Críticos em barra separada ou tom vermelho sem política formal.

Cada card apresenta, nessa ordem: **rótulo + ajuda contextual**, **valor principal**, **variação anterior com unidade correta**, **legenda de comparação identificando a campanha anterior**; a indicação de base/definição fica na ajuda e no contexto. Quando não existir comparação válida: “Sem comparação anterior” no slot de tendência, **sem valor `0` inventado**.

| Indicador | Valor principal | Variação vs. anterior | `titleHint` e regra oficial |
|---|---|---|---|
| **IGS** | `4,3 / 5` | `+0,2 ponto` | Média de satisfação geral das respostas válidas (escala 1 a 5); não é média das dez dimensões, salvo contrato canônico mudar explicitamente |
| **NPS** | `+48` (faixa -100 a +100) | `+7 pontos` | % promotores (9–10) − % detratores (0–6); passivos (7–8) contam na base; delta em pontos do índice, não em % |
| **Taxa de resposta** | `72%` | `−2 p.p.` | Respostas definitivas / participantes cadastrados e elegíveis da campanha, conforme denominação oficial do backend; cópia manual não comprova envio |
| **Satisfeitos** | `84%` | `+2 p.p.` | % com nota geral 4 ou 5, relativo às notas gerais válidas |
| **Críticos** | `6%` | `−2 p.p.` | % com nota geral 1 ou 2, relativo às notas gerais válidas; não é quantidade de casos de plano de ação |

**Números da tabela são somente ilustrativos** e não entram na implementação como valores padrão. Para todos os deltas: `resultado período atual − resultado período anterior` com mesmo cálculo, fontes oficiais e recorte suficientemente comparável. A legenda precisa indicar **qual foi a campanha anterior** (ex.: “vs. 2026/1”), não apenas “vs. anterior” sem referência.

**Interpretação e cor:** subir IGS/NPS/Resposta/Satisfeitos pode ser direção favorável; **reduzir Críticos** pode ser favorável. Entretanto, cor verde ou vermelha somente se uma política explícita definir essa interpretação e a amostra for comparável. Até essa definição, apresentar **sinal numérico e unidade com cor neutra**, sem semáforo ou classificação automática. Taxa de resposta menor não pode ser confundida com satisfação menor. Nunca adicionar meta, velocidade/velocímetro, IDD ou limiar de criticidade não aprovados.

### 4.2 Wireframes por largura — conteúdo completo, não apenas rearranjo

**Desktop largo** (faixa referencial **≥ 1200 px de área útil do conteúdo**, não apenas largura da janela): cinco cards na mesma linha, mantendo mesma largura. Os limites são **alvos de design, sujeitos a teste real com shell e zoom**, não breakpoints já comprovados do kit.

```text
┌─ RESUMO EXECUTIVO ──────────────────────────────────────────────────────────────────────────┐
│ Pesquisa 2026/2 · data/período             72 respostas / 100 participantes cadastrados  │
│                                                                                           │
│ ┌─ IGS ─────────┐ ┌─ NPS ─────────┐ ┌─ TAXA DE ─────┐ ┌─ SATISFEITOS ─┐ ┌─ CRÍTICOS ──┐ │
│ │ 4,3 / 5      │ │ +48           │ │ RESPOSTA      │ │ 84%            │ │ 6%           │ │
│ │ +0,2 ponto   │ │ +7 pontos     │ │ 72%           │ │ +2 p.p.       │ │ −2 p.p.      │ │
│ │ vs. 2026/1   │ │ vs. 2026/1    │ │ −2 p.p.       │ │ vs. 2026/1     │ │ vs. 2026/1   │ │
│ │ (?) fórmula  │ │ (?) fórmula   │ │ vs. 2026/1    │ │ (?) fórmula    │ │ (?) fórmula  │ │
│ └──────────────┘ └───────────────┘ └───────────────┘ └────────────────┘ └──────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

**Tablet / notebook estreito** (faixa referencial **600–1199 px úteis**): grid em **duas colunas**. Quinto card na posição padrão da terceira linha; **não** ocupar as duas colunas, não criar card maior ou layout especial para o último. Repetir tendência e ajuda em todos.

```text
┌─ RESUMO EXECUTIVO ─────────────────────────────┐
│ Pesquisa 2026/2 · 72 de 100                   │
│ ┌─ IGS ───────────────┐ ┌─ NPS ─────────────┐ │
│ │4,3/5; +0,2 ponto   │ │+48; +7 pontos    │ │
│ │vs. 2026/1; ajuda   │ │vs. 2026/1; ajuda │ │
│ └─────────────────────┘ └───────────────────┘ │
│ ┌─ TAXA RESPOSTA ─────┐ ┌─ SATISFEITOS ─────┐ │
│ │72%; −2 p.p.        │ │84%; +2 p.p.      │ │
│ │vs. 2026/1; ajuda   │ │vs. 2026/1; ajuda │ │
│ └─────────────────────┘ └───────────────────┘ │
│ ┌─ CRÍTICOS ──────────┐                       │
│ │6%; −2 p.p.         │                       │
│ │vs. 2026/1; ajuda   │                       │
│ └─────────────────────┘                       │
└────────────────────────────────────────────────┘
```

**Celular** (área útil **< 600 px**, referencial): **uma coluna**, ordem idêntica. Cards de altura compacta; valor principal e variação podem estar em linhas próximas **via slot `hint` existente**, respeitando o componente oficial. **Não forçar duas colunas**, rolagem horizontal, microtexto ou esconder tendência/ajuda.

```text
┌─ RESUMO EXECUTIVO ─────────────┐
│ Pesquisa 2026/2               │
│ 72 de 100 participantes       │
│ ┌─ IGS ──────────────────────┐ │
│ │ 4,3 / 5                   │ │
│ │ +0,2 ponto · vs. 2026/1   │ │
│ └───────────────────────────┘ │
│ ┌─ NPS ──────────────────────┐ │
│ │ +48                       │ │
│ │ +7 pontos · vs. 2026/1    │ │
│ └───────────────────────────┘ │
│ ┌─ TAXA DE RESPOSTA ─────────┐ │
│ │ 72%                       │ │
│ │ −2 p.p. · vs. 2026/1      │ │
│ └───────────────────────────┘ │
│ ┌─ SATISFEITOS ──────────────┐ │
│ │ 84%                       │ │
│ │ +2 p.p. · vs. 2026/1      │ │
│ └───────────────────────────┘ │
│ ┌─ CRÍTICOS ─────────────────┐ │
│ │ 6%                        │ │
│ │ −2 p.p. · vs. 2026/1      │ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

**Acessibilidade em todas as larguras:** `titleHint` acessível por teclado e leitor de tela, alvo acionável quando houver ajuda, ordem de foco coerente com ordem visual, contraste do tema existente, zoom de 200–400% sem corte de valores/tendências, não depender só de cor/ícone para sinal do delta, unidades lidas corretamente (pontos vs. pontos percentuais). Sem criar CSS de breakpoint específico desta tela se o grid responsivo oficial existente resolver.

### 4.3 Componentes exatos do PluginUI e contratos de props (confirmados no código)

| Peça | Nome no Comercial / origem no PluginUI | Props e decisão |
|---|---|---|
| **Container de seção** | `SectionCard` de `@delpi/plugin-ui/index`; alternativa já existente `CommercialSectionCard` = `createDashboardSectionCard` | `title="Resumo executivo"`, `cmSectionCardClassNames`, `cmSectionLabels` se usar diretamente `SectionCard`, mesmo padrão de `OverviewPage.tsx` |
| **Cinco KPIs** | `CommercialMetricCard` em `commercialUi.ts` → `createMetricKpiCard("cm")` → `MetricKpiCard` em `plugins/plugin-ui/src/components/layout/MetricKpiCard.tsx` | **`label`, `value`, `titleHint`, `hint`** são props reais. `hint` aceita `ReactNode`: acomodar delta e legenda. `hero=false`, `tone="default"`, `onClick` ausente para não insinuar drill-down |
| **Ajuda de fórmula** | `HelpTooltip` integrado ao próprio `MetricKpiCard` via `titleHint` | Não criar ícone `?` ou tooltip manual dentro da página |
| **Tendências** | `hint` de `CommercialMetricCard`; **não usar `CommercialTrendDelta` nesta seção** | Verificado que `TrendDelta.tsx` usa `formatTrendDeltaPct` e acrescenta `%` para qualquer `value` numérico. Isso **produziria unidade errada** para `+0,2 ponto`, `+7 pontos`, `−2 p.p.`. Usar texto formatado pelo domínio no slot do card; somente considerar evolução do PluginUI via Abstraction Gate se houver necessidade repetida |
| **Grid** | Grid responsivo já usado por `OverviewPage.tsx` com classes oficiais da área `cm-home-kpi-grid`/`cm-overview-kpi-grid`, após conferir seu CSS e breakpoints | Manter **5 / 2 / 1 colunas** em larguras úteis adequadas; não declarar que as classes atuais já realizam exatamente essa distribuição sem teste; ajustar apenas composição usando layout existente |
| **Loading** | `CommercialLoadingCard` em `commercialUi.ts` → `createDashboardLoadingActivityCard` | Enquanto aguarda consulta; não exibir zeros |
| **Vazio** | `EmptyState` (PluginUI) + `cmEmptyStateClassNames` | “Ainda não há resultados disponíveis para este período” conforme estado oficial |
| **Erro/protegido** | `CommercialStateBanner` → `createDashboardStateBanner` | Mensagem de falha distinta de privacidade/amostra; retry **global somente no Hero** |

**Não usar:** `CommercialDashboardKpiCard` (metas/IDD desnecessários), `CommercialSpeedometerGauge` (meta/limiar inexistente), `CommercialCompareSparkline` (histórico já está na seção seguinte), `CommercialTrendDelta` (formata percentual incorretamente para estes deltas), cards nativos estilizados ou classes CSS exclusivas sem inventário.

**Verificação pendente só de integração:** breakpoints reais do grid do Portal e espaço disponível no shell, como o `hint: ReactNode` se comporta em mobile, e correspondência dos cinco KPIs aos campos fornecidos pelo endpoint oficial. Nada disso autoriza criar componente novo antes de medir.

### 4.4 Estados e cálculos/denominadores

| Situação | UI do Resumo |
|---|---|
| Campanha válida encerrada com respostas e anterior comparável | Cinco valores e cinco deltas com unidade, período comparado e amostra |
| Campanha válida sem anterior | Cinco valores quando conhecidos; em cada card “Sem comparação anterior” |
| Resultado anual/recorte de múltiplas campanhas | Recalcular com todas as respostas válidas da seleção **no backend**; delta só se comparação anual/temporal explicitamente definida e comparável |
| Sem campanha encerrada | `EmptyState` contextual; não fabricar zero |
| Campanha sem respostas | Taxa pode ser `0%` **somente quando denominador real válido existir**, IGS/NPS/Satisfeitos/Críticos ficam “—” sem nota; evitar marcar tudo como erro |
| Falha de API | `CommercialStateBanner`, retry no Hero; não exibir KPI antigo como se fosse atual sem status de desatualização |
| Amostra suprimida/recorte pequeno | Apresentar “Dados protegidos” conforme decisão do backend, sem permitir recompor via outro filtro ou delta |
| Filtro sem fonte oficial | Filtro indisponível no Hero; não falsificar segmentação |

**Cálculos canônicos:** IGS usa notas gerais válidas (1–5), NPS usa diferença percentual de promotores/detratores nas respostas 0–10, satisfação 4–5 e criticidade 1–2 usam a pergunta geral, taxa usa respostas definitivas/participantes cadastrados/elegíveis conforme contrato da campanha. A API é autoridade; frontend apenas formata número, unidade e texto de período. NPS acumulado **não** deve ser calculado como média de NPS sem dados de amostra.

### 4.5 Critérios de aceite objetivos — Resumo Executivo

1. Resumo aparece logo abaixo do `CommercialPageHero`, sem filtros ou ações globais duplicadas na seção.
2. Cinco `CommercialMetricCard`, mesma hierarquia e ordem IGS/NPS/Taxa/Satisfeitos/Críticos; sem sexto card nem barra especial para críticos.
3. Cabeçalho identifica campanha/período e informa respostas e participantes cadastrados, distinguindo campanha individual de ano consolidado.
4. Todos os cinco KPIs exibem deltas **apenas quando comparáveis**; valores com unidades corretas e período anterior explícito. Ausência de comparação não aparece como 0.
5. Todos usam `titleHint` para fórmula; tendências no `hint` existente do card, sem uso indevido de `CommercialTrendDelta`.
6. Desktop: 5 colunas quando o shell oferecer espaço; tablet: 2; celular: 1. Nenhum KPI ausente, quinto sem largura extra e nenhum scroll horizontal.
7. Acessibilidade: foco, teclado, tooltips, zoom, contraste, leitor de tela; texto de tendência não depende só de cor.
8. Estados carregando, sem campanha, sem respostas, falha e amostra protegida são distintos e refletem decisões do backend.
9. Nenhuma meta, limiar ou classificação colorida inventada; nenhuma consulta identificável para `commercial.access`.
10. Validar CSS/grid do Portal e propriedades `hint` nos três tamanhos reais em testes de UI; relatório de execução com capturas por viewport, HEAD, diff, testes e resultados.

## 5. Evolução histórica — gráfico combinado e responsivo (VISUAL APROVADO)

> **Estado:** decisão visual aprovada em 11/11/2026; **não implementado**. Gráfico temporal único, IGS e NPS em dois eixos, com controles visuais oficiais do PluginUI. **Sem tabela histórica fixa**. Os wireframes são especificações conceituais, não capturas da interface real.

### 5.1 Objetivo e conteúdo

Responder “como evoluíram satisfação e recomendação por campanha?”, sem duplicar os KPIs do Resumo Executivo. Usar um `SectionCard` / `CommercialSectionCard` com título “Evolução histórica”, ajuda de interpretação das escalas, barra do gráfico, gráfico combinado e legenda. Categorias são campanhas reais **em ordem cronológica**, não períodos simulados. Tipo inicial: **linhas**. Série `igs`: eixo primário esquerdo (domínio **1–5**); série `nps`: eixo secundário direito (domínio **−100 a +100**). Rótulos, legenda e tooltip devem distinguir unidades; alturas relativas das duas linhas **não** são comparáveis. Não há gráfico duplicado, tabela permanente nem card de detalhes permanentemente aberto.

### 5.2 Wireframes específicos por largura

**Desktop largo** (alvo ≥ 1200 px de **área útil**; validar no shell real):

```text
┌─ EVOLUÇÃO HISTÓRICA ───────────────────────────────────────────────────────┐
│ Satisfação e recomendação por campanha; ajuda das escalas                  │
│ [Linhas ▾]    [Configurar séries ▾]                     [Exportar ▾]        │
│ IGS — eixo esquerdo (1–5)                  NPS — direito (−100 a +100)    │
│ 5 ┤    ╱────╱────╱────╱                ···NPS···                        100│
│ 4 ┤  ╱    IGS                        ···········                        50│
│ 3 ┤╱                         [tooltip ao interagir com campanha]          0│
│ 2 ┤                                             ·······                 −50│
│ 1 └ 24/1   24/2   25/1   25/2   26/1   26/2                        −100│
│ Legenda: IGS (primário) · NPS (secundário)                                  │
└───────────────────────────────────────────────────────────────────────────┘
```

**Tablet / notebook estreito** (alvo 600–1199 px úteis): **mesmo gráfico combinado**, ocupando largura útil toda. O `ChartViewShell` deve reorganizar/permitir quebra da barra, preservando tipo, configuração de séries e exportação; eixos e legenda identificados. Em dispositivo de toque, detalhe **após seleção**, abaixo do gráfico e fechável, sem sobrepor os dados.

```text
┌─ EVOLUÇÃO HISTÓRICA ────────────────────────┐
│ [Tipo ▾] [Séries ▾] [Exportar ▾]           │
│ IGS esq. 1–5 · NPS dir. −100 a +100       │
│ [gráfico combinado na largura disponível]  │
│ [legenda acessível]                        │
│ [detalhe abaixo somente se selecionado ×]  │
└────────────────────────────────────────────┘
```

**Celular** (alvo < 600 px úteis): único gráfico combinado em largura total, **sem rolagem horizontal da página**. Barra de ferramentas compacta pode quebrar em várias linhas ou usar os popovers oficiais; controles **não somem**. Preservar ambos os eixos e legenda, com rótulos temporais abreviados quando necessário e nomes completos acessíveis. **Ao abrir a página, detalhe fechado**; tocar ponto/campanha abre detalhe **abaixo do gráfico**, tocar outro ponto atualiza e ação de fechar o recolhe. Nunca manter tooltip grande sobre a área do gráfico no celular.

```text
┌─ EVOLUÇÃO HISTÓRICA ─────┐
│ [Linhas ▾]              │
│ [Configurar séries ▾]   │
│ [Exportar ▾]            │
│ IGS ⟵   ⟶ NPS          │
│ [gráfico combinado]      │
│ [legenda]                │
│                          │
│ APÓS TOQUE EM CAMPANHA:  │
│ ┌ Pesquisa 2026/2 ─ × ┐ │
│ │ IGS        4,3 / 5  │ │
│ │ NPS            +48  │ │
│ │ Respostas   72/100  │ │
│ │ Taxa           72%  │ │
│ └──────────────────────┘ │
└──────────────────────────┘
```

**Dados ilustrativos**, nunca valores padrão. Breakpoints são metas de UX, não classes CSS já comprovadas. Validar largura útil, popovers, eixos, foco, zoom de 200–400%, contraste e leitores de tela.

### 5.3 Ferramentas existentes do PluginUI — correspondência de código

O padrão completo já é utilizado em `plugins/commercial/src/features/analytics/components/AnalyticsRolSeriesChart.tsx` e parcialmente em `AnalyticsClosingRateSeriesChart.tsx`. **Reutilizar apresentação, não as regras de negócio de ROL ou conversão.**

| Funcionalidade / posição | Componente ou função real | Decisão para Marketing |
|---|---|---|
| Barra **dentro do gráfico** | `ChartViewShell` (`typeToggle`, `seriesColors`, `exportActions`, `overlays`) | Controles de **apresentação** junto ao gráfico. Filtros de dados/ano/campanha/segmento e ações globais ficam **somente no `CommercialPageHero`** |
| Gráfico e dois eixos | `MultiTypeSeriesChart` | `data`, `categoryKey`, `series`, `chartType`, `formatY`, `formatYSecondary`, `formatTooltipValue`, `secondaryDataKeys`; `series[].axis="secondary"` ou `secondaryDataKeys=["nps"]` |
| Trocar tipo | `ChartTypeSegmentToggle`, `TIME_MULTI_SERIES_TYPES` | `family="time_multi_series"`: **linhas** (padrão), **colunas**, **área**; testar dual-axis nos três; nunca oferecer pizza/empilhado para a evolução |
| Configurar série | `ChartSeriesColorsPopover` | IGS/NPS individual: cor, exibir/ocultar, habilitar tendência linear, cor/traçado/espessura da tendência, restaurar cada série ou tudo |
| Aplicar/resetar configuração | `applySeriesViewPreferences`, `buildChartSeriesConfigItems`, `patchSeriesTrendStyle`, `resetSeriesViewPreferences`, `seriesViewHasOverrides` em `seriesFillPreferences.ts` | Preferências alteram apenas visualização, nunca valores do backend |
| Salvar escolhas | `usePersistedChartPreferences` | `storageKey` isolada, proposta: `commercial:marketing:satisfaction-evolution`; persistência é **localStorage do navegador**, não perfil do backend |
| Exportação local | `CommercialTabularExportButtons` e `runTabularExport` | Exportar tabela de **agregados autorizados**: campanha/período, IGS, NPS, participantes, respostas e taxa; sem tabela fixa na página |
| Painel de opções | `ChartOverlayOptionsPopover` | Capacidade do kit confirmada; **não** copiar opção comparar ano anterior de ROL sem contrato de campanhas semestrais aprovado |
| Estados | `CommercialLoadingCard`, `EmptyState`, `CommercialStateBanner` | Diferenciar carregamento, sem dados, erro e amostras protegidas |

**Configuração inicial:** ambas as séries visíveis, sem tendência automática. Se ocultar ambas, fornecer mensagem de estado neutro ou impedir ocultar última série; verificar comportamento existente antes de implementar. Tendência do PluginUI é **linear descritiva, não previsão**; número mínimo de campanhas e tratamento de lacunas são **PENDING**, não assumir política.

### 5.4 Detalhe da campanha e interação

Conteúdo aprovado para o detalhe: **campanha/período; IGS; NPS; participantes cadastrados/elegíveis; respostas finais; taxa de resposta**. Cabe ao **commercial-api** calcular e autorizar valores e suprimir recortes pequenos. Não recalcular indicadores no tooltip com base em médias de valores exibidos.

- **Desktop/mouse:** tooltip flutuante junto ao ponto **apenas durante interação**; desaparece ao sair; sem abrir página ou atualizar filtros.
- **Tablet/celular por toque:** seleção da campanha abre **painel abaixo do gráfico apenas depois do toque**; por padrão fechado, atualizado ao selecionar outro ponto e explicitamente fechável. Tooltip grande não pode obstruir a área do gráfico.
- **Teclado/leitor de tela:** mesma consulta e fechamento por mecanismo acessível; verificar foco, anúncio, seleções e rótulos completos. Não depender exclusivamente de mouse.
- **Gap real:** o `MultiTypeSeriesChart` usa tooltip básico de Recharts, mas **não está comprovado** suporte pronto a conteúdo completo de detalhe, seleção persistente por toque nem equivalência por teclado. Primeiro investigar props e composição existentes; se necessário, menor extensão do **PluginUI** após Abstraction Gate, sem criar gráfico ou card nativo paralelo dentro de Marketing.

### 5.5 Integridade, limitações reais e segurança

1. Os eixos separados **existem** no `MultiTypeSeriesChart` via `axis`/ `secondaryDataKeys`, mas **os domínios fixos 1–5 e −100–100 não estão expostos como props confirmadas**. É **PENDING** a menor extensão do PluginUI, com teste regressivo nos gráficos já existentes; não simular eixos com CSS.
2. O `MultiTypeSeriesChart` tem `connectNulls` nas linhas; períodos sem pesquisa **não** devem criar pontos artificiais zero nem conexão enganosa. Resolver representação das lacunas com dados oficiais/menor ajuste, sem inventar campanhas.
3. Campanhas **encerradas** são pontos consolidados; se houver campanhas abertas, marcar claramente como parciais segundo contrato oficial. Seleções ano completo devem ser recomputadas no backend sobre respostas válidas e bases corretas, nunca média simples de NPS.
4. Mudança de população e amostra deve ficar visível no detalhe; uma linha ascendente não comprova causalidade ou melhora para o mesmo conjunto de clientes.
5. `commercial.access`: somente agregados protegidos; regras de supressão valem para gráfico, tooltip, painel e **exportação**. Personalização de gráfico não altera autorização nem recupera dados restritos.
6. Preferências de tipo/cor/série não pertencem ao Hero; todos os filtros que alteram o conjunto de dados ficam exclusivamente no Hero.

### 5.6 Critérios de aceite — Evolução Histórica

1. Um único `SectionCard`, um `MultiTypeSeriesChart` IGS + NPS dual-axis; **sem tabela histórica fixa**.
2. Toolbar oficial `ChartViewShell` com tipo, configuração individual de séries e exportação. Ano, campanha, grupo, período histórico e outros recortes ficam dentro do `CommercialPageHero`.
3. Tipo inicial linhas; alternância entre linhas, colunas e área com eixos/legendas/unidades corretos, sem alterar cálculos.
4. Inspector oficial: cores, visibilidade, tendência individual e estilo, reset individual/geral; persistir preferência no navegador com chave própria.
5. Domínio IGS fixo 1–5, NPS −100–100 **após validação e adaptação mínima**; até lá não declarar integração final concluída.
6. Desktop tooltip apenas ao interagir; celular/tablet painel **abaixo**, inicialmente fechado, abre após toque, permite trocar seleção e fechar.
7. Equivalência por teclado e leitor de tela; controles e dois eixos legíveis sem scroll horizontal, inclusive zoom 200–400%.
8. Detalhe: campanha, IGS, NPS, participantes, respostas e taxa; nunca dados protegidos. Exportação apenas de agregados autorizados.
9. Nenhum `0` para ausência; lacunas reais não interpoladas artificialmente; erros, carregamento e amostra suprimida com estados próprios.
10. Testar desktop/tablet/celular com capturas, tipo de gráfico, inspector, exportação, toque/foco, eixos e regressão dos gráficos de ROL/Closing Rate; relatório com HEAD, diff, testes, outcome e gaps.

## 6. Avaliação das dez dimensões — VISUAL APROVADO, ranking crescente

> **Decisão visual aprovada em 11/11/2026:** um ranking **com as dez dimensões**, ordenado automaticamente da **menor média para a maior**, empate resolvido pela ordem oficial do questionário; barras horizontais do PluginUI, sem tabela nem gráficos extras. **Não implementado.** Métricas, permissões e proteção de amostras pertencem ao `commercial-api`.

### 6.1 Objetivo operacional e hierarquia

Identificar rapidamente **quais dimensões estão relativamente pior e melhor avaliadas**, para orientar leitura do Comercial, sem confundir ranking com causalidade, plano de ação ou a métrica IGS. Esta seção vem **depois da Evolução Histórica**. Título **“Avaliação por dimensão”** e subtítulo **“Média das respostas válidas por aspecto · escala de 1 a 5”**, com ajuda: notas válidas de 1 a 5; `Não se aplica` e nulos não entram no numerador nem denominador; cada dimensão pode ter **n válido diferente**.

Um `SectionCard` / `CommercialSectionCard` envolve **uma lista de dez barras horizontais**, todas na mesma escala fixa de 1 a 5. Cada item contém **rótulo oficial da dimensão**, **barra proporcional à média no máximo 5**, **média formatada com uma casa decimal `x,x / 5`**, e **`n` respostas válidas**. Ordenar `mean ASC`, empatando pela **ordem canônica do questionário**, estável entre atualizações. Não usar cor por ranking, semáforo, “nota abaixo de 4 = crítico” nem inventar meta de satisfação. O menor item aparece primeiro porque identifica uma oportunidade de investigação, **não** porque já comprova um problema operacional.

As dez **chaves técnicas confirmadas no contrato da entrega 1**, para mapeamento de dados e ordem canônica, são: `quality`, `delivery_deadline`, `service`, `agility`, `communication`, `technical_support`, `commercial_support`, `flexibility`, `reliability`, `partnership`. Os rótulos curtos usados abaixo são **somente exemplos de UI**, não substituem a **redação integral e a ordem oficial das perguntas do Word**, que devem ser conferidas no contrato versionado antes da implementação. Não mapear por posição de array; usar chaves canônicas.

### 6.2 Wireframes em três tamanhos — todas as dez dimensões

**Desktop (alvo ≥ 1200 px de área útil):** `layout="columns"`, mesma linha para rótulo, barra e valor; `meta` exibe a quantidade de respostas válidas associada ao rótulo. Não abrir duas colunas de rankings (evitaria leitura global). As barras ocupam a largura disponível; nomes longos não podem ser truncados sem alternativa acessível.

```text
┌─ AVALIAÇÃO POR DIMENSÃO ─────────────────────────────────────────────────────────┐
│ Média de respostas válidas · notas 1–5 · Não se aplica excluído                 │
│                                                                                │
│ Prazo de entrega       n=61    ━━━━━━━━━━━━━━━━━━━────────  3,6 / 5           │
│ Flexibilidade          n=66    ━━━━━━━━━━━━━━━━━━━━───────  3,8 / 5           │
│ Comunicação            n=69    ━━━━━━━━━━━━━━━━━━━━━──────  3,9 / 5           │
│ Agilidade              n=68    ━━━━━━━━━━━━━━━━━━━━━──────  4,0 / 5           │
│ Suporte técnico        n=58    ━━━━━━━━━━━━━━━━━━━━━━─────  4,1 / 5           │
│ Atendimento            n=70    ━━━━━━━━━━━━━━━━━━━━━━─────  4,2 / 5           │
│ Suporte comercial      n=65    ━━━━━━━━━━━━━━━━━━━━━━━────  4,3 / 5           │
│ Confiabilidade         n=72    ━━━━━━━━━━━━━━━━━━━━━━━━───  4,4 / 5           │
│ Qualidade              n=71    ━━━━━━━━━━━━━━━━━━━━━━━━━──  4,5 / 5           │
│ Parceria               n=70    ━━━━━━━━━━━━━━━━━━━━━━━━━━─  4,6 / 5           │
└────────────────────────────────────────────────────────────────────────────────┘
```

**Tablet / notebook estreito (alvo 600–1199 px úteis):** manter **uma única lista ordenada**. Preferir `layout="columns"` enquanto rótulo, valor e amostra couberem; passar a `layout="stacked"` quando a largura do componente tornar nomes difíceis de ler, **sem depender apenas do tipo de dispositivo**. Preservar todas as dez linhas e o mesmo critério de ordenação.

```text
┌─ AVALIAÇÃO POR DIMENSÃO ──────────────────────┐
│ Prazo de entrega · n=61   ━━━━━━━──  3,6 / 5 │
│ Flexibilidade · n=66     ━━━━━━━━─  3,8 / 5 │
│ ... oito dimensões restantes, sem ocultar    │
└───────────────────────────────────────────────┘
```

**Celular (alvo < 600 px úteis):** `layout="stacked"`, no qual o PluginUI coloca **rótulo + valor acima e barra de largura plena abaixo**. `meta` informa `n` válido; os dez itens aparecem em rolagem **vertical natural da página**, nunca carrossel/scroll horizontal. Não reduzir tamanho do texto para forçar três colunas, não ocultar dimensões, e não criar segundo widget mobile.

```text
┌─ AVALIAÇÃO POR DIMENSÃO ──┐
│ Média · escala de 1 a 5   │
│ Prazo de entrega  3,6 / 5│
│ n=61 respostas válidas    │
│ ━━━━━━━━━━━━━━━━━─────   │
│ Flexibilidade     3,8 / 5│
│ n=66 respostas válidas    │
│ ━━━━━━━━━━━━━━━━━━───    │
│ ...                      │
│ Qualidade         4,5 / 5│
│ n=71 respostas válidas    │
│ ━━━━━━━━━━━━━━━━━━━━━─   │
│ Parceria          4,6 / 5│
│ n=70 respostas válidas    │
│ ━━━━━━━━━━━━━━━━━━━━━━   │
└──────────────────────────┘
```

**Todos os valores, contagens e comprimentos de barras dos wireframes são fictícios.** Não inserir dados ilustrativos como seed de produção. Breakpoints são referências de experiência, **não prova de CSS existente**: conferir layout real no shell e zoom 200–400%. Os rótulos deverão ser os oficiais.

### 6.3 Mapa exato de componentes PluginUI e propriedades confirmadas

| Papel | Componente real / origem | Props e decisão |
|---|---|---|
| Painel | `SectionCard` de `@delpi/plugin-ui/index`, ou wrapper `CommercialSectionCard` de `commercialUi.ts` | Um painel; título, subtítulo/ajuda seguindo padrão de seções do Comercial |
| Ranking | `CommercialHorizontalValueBars` de `plugins/commercial/src/app/commercialUi.ts` → `HorizontalValueBars` em `plugins/plugin-ui/src/components/charts/HorizontalValueBars.tsx` | `items: {id, label, value, valueLabel?, meta?}[]`, `max={5}`, `layout="columns" | "stacked"`, `aria-label`; usar `id` como chave canônica de dimensão |
| Escala | `max={5}` da implementação real | **Obrigatória:** sem prop, o kit usa **a maior nota presente** como máximo, ampliando visualmente todas as barras |
| Texto de amostra | `items[].meta` | `n = [contagem válida]`; mostrar contagens fornecidas/permitidas pelo backend, sem inventar base |
| Valores | `items[].value` e `items[].valueLabel` | `value` = média numérica válida de 1 a 5; `valueLabel` = `x,x / 5` localizado em pt-BR |
| Interação | `onItemClick` **omitido** | Lista não acionável; nenhum acesso a resposta individual por clique na barra |
| Aparência | Classes/tokens internos de `HorizontalValueBars` | Usar kit sem criar barras, classes ou lógica de cor próprias; não pintar dimensão de menor nota em alerta |
| Carregamento / vazio / erro | `CommercialLoadingCard`, `EmptyState`, `CommercialStateBanner` | Distinguir não carregado, nenhuma amostra válida, falha e proteção da amostra |

**Não usar `ChartViewShell` ou `ChartTypeSegmentToggle` nesta seção**: a análise possui uma única representação adequada (ranking de barras horizontais); não é a evolução temporal multi-séries. O padrão de ferramentas de aparência aprovado para os **gráficos temporais** não obriga criar troca de tipo em todos os indicadores. Não adicionar filtro de ordem no bloco: a **ordem crescente está aprovada como padrão fixo**; qualquer futura opção de consulta deverá respeitar a regra de filtros dentro do Hero.

### 6.4 Regras de dados, proteção e estados

- A média de cada dimensão é calculada **no `commercial-api`**: soma das notas 1–5 válidas ÷ total de respostas válidas daquela dimensão; `null` / “Não se aplica” não entram. Não calcular como IGS nem média das dez dimensões como satisfação geral.
- A UI recebe da API `mean`, `valid_count` e identificador canônico. Ordenar apenas os **agregados autorizados** por média crescente; desempatar pela ordem oficial; fonte dos dados continua sendo a API.
- Se `valid_count=0`/média ausente, **não** renderizar `0`/barra vazia como nota: mostrar “Sem avaliação” com a dimensão preservada; `HorizontalValueBars` exige `value:number`, logo **PENDING** como compor item sem média usando recurso do kit/estado neutro, sem forçar `0`. Itens sem média devem ficar **após** as dimensões com média, seguindo ordem oficial entre si, sem fingir que são as piores.
- Se a política de privacidade suprimir uma dimensão/recorte, não revelar nem a média nem contagem proibida, inclusive pela ordem (evitar ordenação que permita inferência). Exibir “Dados protegidos” em apresentação permitida pelo contrato; **PENDING** a composição para item suprimido.
- O ranking não classifica respostas individuais como críticas/satisfeitas por dimensão. Notas 1–2 e 4–5 para “Críticos” e “Satisfeitos” pertencem **exclusivamente à satisfação geral**.
- Não criar navegação para respostas privadas ou investigação identificável pelo público `commercial.access`; backend decide permissão, recortes e limiar mínimo.
- Cor padrão uniforme; sem setas de tendência, metas, limiar de 4, sem percentual de “satisfeitos” por dimensão inventado.

### 6.5 Critérios objetivos de aceite — Dimensões

1. Seção aparece depois da Evolução, num único painel com título, contexto da escala e ajuda sobre “Não se aplica”.
2. **Exatamente dez dimensões oficiais**, salvo supressão visual exigida pelo backend; rótulos fiéis ao questionário versionado e chaves estáveis.
3. Ordenação **da menor para a maior média**, desempate pela ordem oficial do questionário; sem alternância de ordenação fora do Hero.
4. **`CommercialHorizontalValueBars`**, `max={5}`, `items[].meta` com n válido, `valueLabel` com `x,x / 5`; nenhum componente paralelo de barras.
5. Desktop: rótulo/barra/nota na mesma linha; tablet adapta pelo espaço; celular: rótulo/nota acima, barra abaixo, todos os itens visíveis na rolagem vertical.
6. Não acrescentar tabela fixa, gráfico de linha, filtro local, mudança de tipo, tooltip customizado ou drill-down sem necessidade comprovada.
7. Sem “zero” para nota ausente, sem falso alerta ou meta; estados sem dados/erro/suprimidos próprios.
8. Não revelar contagens ou médias protegidas, nem por ordenação ou clique; sem queries de respostas individuais para `commercial.access`.
9. Testar os três tamanhos, nomes longos, contraste, zoom 200–400%, foco/leitor de tela e regressão visual do `HorizontalValueBars` já usado no Portal.
10. Execução depende de HEAD e working tree verificados, contrato versionado das perguntas e relatório de alterações/testes/gaps.

## 7. Comparação entre grupos de clientes — VISUAL APROVADO

> **Estado:** composição, expansão e comportamentos responsivos **aprovados para especificação em 11/11/2026**, sem implementação. A definição exata da classificação “cliente estratégico”, dos denominadores, limites de amostra, contrato da API e renderização responsiva continuam **TO_INVENTORY/PENDING** e não podem ser declarados existentes.

### 7.1 Finalidade, conteúdo e hierarquia

Comparar, no **mesmo recorte oficial de campanha/ano e filtros aplicados no Hero**, os resultados de **Geral**, **Clientes Estratégicos** e **Demais Clientes**, para identificar diferenças que merecem investigação sem duplicar o Resumo Executivo nem o ranking de dimensões. Esta seção aparece **depois da Avaliação das Dez Dimensões**, em **um único painel** “Comparação entre grupos”, com subtítulo do recorte e ajuda sobre população, escala, bases e proteção de amostras.

**Decisão aprovada:** exibir de início **somente cinco indicadores** em uma comparação lado a lado: (1) IGS (`x,x / 5`), (2) NPS (`+/-n` pontos), (3) taxa de resposta (%), (4) satisfeitos (%), (5) críticos (%). Um acionador local de apresentação **“Comparar também as dez dimensões”** mostra **dez linhas adicionais dentro da mesma tabela**, logo abaixo das cinco primeiras, com as **médias por dimensão (1–5)**. Ao recolher, as dez linhas desaparecem e os cinco indicadores permanecem. **Fechado inicialmente**; reabrir não altera filtros, dados nem autorização. Sem tabela duplicada, navegação, paginação, pesquisa local, alternância arbitrária de tipos de gráfico ou ordenação por colunas numéricas de unidades diferentes.

As dez dimensões usam as chaves canônicas `quality`, `delivery_deadline`, `service`, `agility`, `communication`, `technical_support`, `commercial_support`, `flexibility`, `reliability`, `partnership`; rótulos curtos nos exemplos **não substituem o texto/versionamento oficiais**. A ordem das linhas expandidas deve seguir a **ordem oficial do questionário**, mantendo comparação consistente entre colunas; o ranking crescente da seção 6 **não** se aplica à tabela de grupos.

### 7.2 Wireframes por tamanho (dados exclusivamente fictícios)

**Desktop, área útil larga (alvo ≥ 1200 px):** quatro colunas dentro do painel, sempre na ordem Indicador / Geral / Estratégicos / Demais. Abaixo de cada título de grupo, exibir **respostas / participantes** quando autorizado e com denominadores compatíveis; não confundir “cadastrados na campanha” com prova de convite efetivamente enviado. Valores numéricos alinhados à direita.

```text
┌─ COMPARAÇÃO ENTRE GRUPOS ────────────────────────────────────────────────────┐
│ Pesquisa 2026/2 · Quem respondeu e como avaliou? · Ajuda de indicadores     │
│ Indicador        Geral                Estratégicos          Demais           │
│                  72/100 respostas     34/40 respostas       38/60 respostas  │
│ IGS              4,3 / 5              4,5 / 5              4,1 / 5          │
│ NPS              +48                  +61                  +37              │
│ Taxa resposta    72%                  85%                  63,3%            │
│ Satisfeitos      84%                  90%                  80%              │
│ Críticos         6%                   3%                   8%               │
│ [Comparar também as dez dimensões ▾]                                       │
│                                                                           │
│ APÓS EXPANDIR, NAS MESMAS COLUNAS:                                        │
│ Qualidade        4,5                  4,7                  4,3              │
│ Prazo entrega    3,6                  4,0                  3,3              │
│ Atendimento      4,2                  4,4                  4,0              │
│ Agilidade        4,0                  4,2                  3,8              │
│ Comunicação      3,9                  4,1                  3,7              │
│ Suporte técnico  4,1                  4,3                  3,9              │
│ Suporte comercial4,3                  4,5                  4,1              │
│ Flexibilidade    3,8                  4,1                  3,5              │
│ Confiabilidade   4,4                  4,6                  4,2              │
│ Parceria         4,6                  4,8                  4,4              │
│ [Ocultar as dez dimensões ▴]                                              │
└───────────────────────────────────────────────────────────────────────────┘
```

**Tablet (alvo 600–1199 px úteis):** preferir **as mesmas quatro colunas** enquanto os rótulos e números couberem sem truncamento ambíguo. Se a largura útil impedir legibilidade, usar o modo de apresentação responsiva **oficial** do PluginUI, não introduzir rolagem horizontal na página. O acionador de dez dimensões permanece visível na seção, e não no Hero.

```text
┌─ COMPARAÇÃO ENTRE GRUPOS ───────────────────────────────┐
│ Indicador   Geral     Estratégicos      Demais         │
│ IGS         4,3/5       4,5/5           4,1/5         │
│ NPS         +48         +61             +37           │
│ ... cinco indicadores no total                         │
│ [Comparar também as dez dimensões ▾]                   │
│ [10 linhas adicionais na mesma grade, quando expandido]│
└────────────────────────────────────────────────────────┘
```

**Celular (< 600 px úteis):** **um bloco/card por indicador**, dentro do mesmo painel lógico, com **os três grupos lado a lado em cada indicador** e rótulos compreensíveis, preservando comparabilidade sem rolagem horizontal. O usuário vê os cinco blocos principais; ao acionar **“Comparar também as dez dimensões”**, surgem **dez blocos adicionais equivalentes** na mesma sequência lógica, não outra tabela nem modal. A UI é a **mesma coleção de linhas de dados em dois modos de apresentação**, não dois contratos nem duas consultas.

```text
┌─ COMPARAÇÃO ENTRE GRUPOS ──┐
│ IGS                       │
│ Geral    Estrat.   Demais │
│ 4,3/5    4,5/5     4,1/5 │
│ ───────────────────────── │
│ NPS                       │
│ Geral    Estrat.   Demais │
│ +48      +61       +37    │
│ ... resposta/satis./crít. │
│ [Comparar dez dimensões ▾]│
│                           │
│ AO EXPANDIR:              │
│ Qualidade                 │
│ Geral    Estrat.   Demais │
│ 4,5      4,7       4,3   │
│ ... até dez dimensões     │
└───────────────────────────┘
```

Os números servem **apenas de exemplo**, não podem ser copiados para dados de produção. Os breakpoints são **alvos visuais**, não estilos existentes comprovados; testar viewport útil real, ampliação 200–400%, nomes longos, teclado, leitor de tela e contraste.

### 7.3 Componentes reais e decisões de composição

**Fonte investigada:** `plugins/commercial/src/app/commercialUi.ts`, `plugins/plugin-ui/src/components/data/{DataTable.tsx,DataTableSection.tsx}`, `plugins/plugin-ui/src/components/layout/SectionCard.tsx`, e padrão de consumo em `plugins/commercial/src/features/analytics/components/CommercialProposalsTable.tsx`.

| Responsabilidade | Componente/contrato existente | Utilização aprovada / limitação |
|---|---|---|
| Painel, título e ajuda | `CommercialSectionCard` (wrapper de `createDashboardSectionCard`) | `title`, `subtitle`, `hint`, `children`; `SectionCard.collapsible` fecha **todo o corpo** do painel, **não** atende isoladamente à expansão só das dez dimensões |
| Tabela principal | `CommercialDataTable<T>` → `DataTable<T>` | `columns`, `rows`, `rowKey`, `compact`, `layout`, `loading`, `emptyMessage`; `DataTableColumn<T>` aceita `header`, `render`, `align`, `mobileLabel`; 4 colunas/5 linhas inicialmente |
| Linhas adicionais ao expandir | Estado local de composição React + mesmo `CommercialDataTable` | Alternar **somente o conjunto de linhas**: 5 indicadores + 10 dimensões quando aberto; sem renderizar segunda tabela. Usar acionador oficial do kit após localizar componente apropriado; acessibilidade `aria-expanded`/`aria-controls` |
| Expansão nativa de linha individual | `DataTable.expandedRowKey`, `renderExpandedRow`, `isRowExpandable` | **Existe, mas expande o detalhe de uma única linha**; não equivale automaticamente a inserir dez linhas irmãs. Não apresentar como solução pronta para o acionador geral de dimensões |
| Modo responsivo cards | `DataTableSection` com `viewLayoutPreferencesKey`, `renderCard`, `viewLayoutMobileMaxWidthPx` | Kit permite modo Tabela/Cards e padrão mobile ≤ 768 px quando habilitado; **não vem automaticamente de `CommercialDataTable`**. Validar composição oficial `DataTableSection`/ `DataCardsGrid` sem duplicar `SectionCard` ou toolbar e sem impor busca/paginação a 15 linhas |
| Card de dados opcional | `CommercialDataRecordCard`, `CommercialDataCardsGrid` | Componentes já exportados em `commercialUi.ts`; **props/adequação exatas à célula com três grupos: TO_INVENTORY**; evitar desenvolver card nativo com CSS paralelo |
| Ação local de expandir/recolher | Priorizar controle oficial PluginUI/Comercial, verificar exports e props na etapa de implementação | É comando de **apresentação local**, permitido neste painel; `CommercialActionButton` é candidato existente, mas validar semântica de disclosure acessível e densidade |
| Ajuda contextual | `hint` de `CommercialSectionCard` → tooltip oficial | Explicar diferença entre IGS/nota por dimensão, taxa e tamanhos dos grupos |
| Estados | `CommercialLoadingCard`, `CommercialEmptyState`, `CommercialStateBanner` | Carregamento/sem campanhas/erro/fonte indisponível/supressão diferenciados |

**Abstraction Gate:** não introduzir `SurveyGroupTable`, `MarketingCompareAccordion`, `MarketingMobileCards`, CSS responsivo independente ou uma segunda biblioteca. Se a montagem com `DataTableSection` não permitir facilmente o modo mobile, registrar gap e avaliar **menor extensão transversal** no kit com regressão antes de criar abstração.

**Não incluir por padrão:** `CommercialPagination`, `CommercialDataListToolbar`, filtros locais, seleção de linhas, sorting de indicadores heterogêneos, drawer ou botões de exportação não solicitados. A decisão de expandir/recolher não mexe na consulta nem nas escolhas do Hero.

### 7.4 Regras de dados, comparabilidade e proteção

1. **Geral = agregados autorizados para o mesmo recorte**; Estratégicos/Demais vêm de classificação oficial na fonte de autoridade ainda **TO_INVENTORY** (ex.: dados de referência do TOTVS por `api-delpi`, apenas após confirmação), não de regra improvisada no frontend. Os grupos só devem formar partição quando o domínio comprovar classificação completa/exclusiva; sem isso, não prometer `Geral = Estratégicos + Demais` nem reconstruir valores na tela.
2. Amostra por grupo tem **respostas e participantes cadastrados/elegíveis** quando autorizados; taxa = respostas/base oficial no `commercial-api`. “Participantes cadastrados” **não comprova envio entregue**. Diferença entre recortes e populações deve ser identificada; o usuário não deve confundir percentual de resposta com satisfação.
3. `IGS`, `NPS`, satisfeitos, críticos, taxas e médias das dez dimensões vêm de **agregação oficial do backend**, não de subtração entre percentuais, média simples de médias ou reconstituição de indivíduos no frontend.
4. Supressão de grupos pequenos é **backend-first**, incluindo inferência por diferença (`Geral − Estratégicos = Demais`), cruzamento com filtros, contagens, linhas expandidas, histórico e quaisquer exportações. O Portal **não** tenta esconder dados apenas com componentes: recebe somente valores autorizados e representa estado protegido.
5. Quando classificação fonte/cobertura é inexistente: indicar **“Comparação indisponível”**, sem fabricar proxy de cliente estratégico; quando grupos não possuem base válida, não converter ausência em zero. Quando dado é suprimido, não mostrar `n` que permita reidentificação.
6. `commercial.access` vê **apenas agregados autorizados**, mesmo após a expansão; respostas por cliente ficam restritas a `commercial.marketing` ou `commercial.manage` segundo contrato da frente, sempre com validação do `commercial-api`.

### 7.5 Critérios objetivos de aceite

1. Seção depois do ranking das dez dimensões, em **um único painel** com descrição do recorte e orientação sobre os grupos.
2. **Cinco linhas visíveis inicialmente**, na ordem IGS, NPS, Taxa de resposta, Satisfeitos, Críticos; quatro colunas (Indicador, Geral, Estratégicos, Demais) em desktop, dados e unidades corretos.
3. Acionador local “Comparar também as dez dimensões” inicia **recolhido**; expande **dez linhas da mesma tabela** imediatamente após as cinco principais; ação inversa as recolhe. Não criar outra tabela nem alterar filtros.
4. Dimensões usam nomes oficiais, chave estável e **ordem canônica do questionário**, com médias 1–5 e contagens válidas disponibilizadas conforme autorização.
5. Desktop quatro colunas; tablet mantém tabela enquanto legível; celular usa **cards por indicador, três grupos lado a lado**, mantendo a expansão dentro da **mesma coleção de dados**. Sem rolagem horizontal da página, elementos cortados nem cabeçalhos ilegíveis.
6. Usar `CommercialSectionCard` e `CommercialDataTable` e reutilizar kit oficial para disclosure e cards; **validar integração concreta** de `DataTableSection`/ `DataCardsGrid` antes de alegar suporte pronto em mobile.
7. Sem busca, paginação, seleção, filtros locais ou sort numérico sem justificativa; controle de apresentação local não é filtro de Hero.
8. Exibir respostas/participantes por grupo **somente quando permitidos**; proteção contra inferência por complemento e recortes deve existir no backend antes dos dados chegarem ao frontend.
9. Loading, vazio, sem classificação, amostra suprimida e erro distintos; nenhum valor ausente/suprimido renderizado como zero.
10. Testes em desktop, tablet, celular, zoom 200–400%, com teclado/leitor de tela; verificar expansão, recolhimento, foco, nomes longos, preservação de unidades, segurança e regressão dos componentes compartilhados. Relatório de execução com HEAD/branch/working tree, diff, testes, outcome e gaps.

## 8. Consulta individual — somente Marketing/Manage

**Não é um card de advertência vazio para usuários comuns.** Para `commercial.access`, essa região **não é renderizada nem carregada**. Para gestores:
- `SectionCard` “Respostas por empresa”, `CommercialDataTable` com empresa (`codigo + loja`, usando padrão autorizado), período/data, IGS individual, NPS individual e indicação de comentários; coluna de ação contextual “Abrir resposta”.
- `CommercialHostDrawer` + `CommercialDetailCard`/`CommercialDetailFieldGrid` para leitura imutável da resposta (10 dimensões, IGS, NPS, três comentários) e identificação da empresa.
- Ação de abrir resposta existe na linha, **exceção contextual** à regra de botões globais no Hero; filtros da lista, se necessários, ficam no Hero e somente para gestores.
- Sem editar, excluir, expor token, reenviar pesquisa ou criar ações da entrega 2. Se houver intenção de exportar dados individuais, só após nova decisão e avaliação de privacidade.
- Segurança no backend: `commercial.marketing` OU `commercial.manage`; `commercial.access` isolado nunca autoriza endpoint individual. Incluir testes negativos reais.

## 9. Estados, acessibilidade e responsividade

| Estado | Apresentação | Fonte |
|---|---|---|
| Carregando | `CommercialLoadingCard` para bloco, sem números falsos | Consulta em andamento |
| Sem campanha encerrada | `EmptyState`: “Ainda não há pesquisas encerradas.” | Backend sem campanha válida |
| Campanha encerrada sem respostas | Sem IGS/NPS numéricos; contagens verdadeiras | Sem resposta definitiva |
| Atributo/filtro sem fonte oficial | Não apresentar seletor não suportado; mensagem contextual | Inventário do atributo |
| Grupo pequeno protegido | `CommercialStateBanner` ou estado protegido do kit; não exibir valor | Backend suprime |
| Erro de rede/API | `CommercialStateBanner`, retry **global no Hero** | Falha de consulta |
| Acesso negado | `EmptyState` apropriado; não montar consultas restritas | Backend |
| Comparação anterior inexistente | Delta “—” com contexto “Sem comparação disponível” | Ausência de período comparável |

Desktop: Hero compacto, KPIs em 5 colunas quando couber, gráfico combinado e tooltip sob interação. Tablet: KPIs em 2 colunas e gráfico combinado com barra responsiva; detalhes abaixo após toque. Celular: KPIs em 1 coluna, Hero empilhado, gráfico combinado com ambos os eixos sem scroll horizontal e detalhe abaixo **somente após toque, fechável**. Ranking usa `layout="stacked"`; tabelas das outras seções usam `CommercialDataTable`. Foco, teclado, zoom 200–400%, descrições acessíveis e unidades distintas são critérios de aceite.

## 10. API e paridade CAIO

| Necessidade | Fonte planejada / autoridade | Consumidor |
|---|---|---|
| Lista de campanhas e anos com resultados | Consultas oficiais `GET /satisfaction-surveys/campaigns` (ou projeção agregada autorizada, a ajustar na etapa) | Hero sem expor campos restritos a `access` |
| Resultados e comparações | `GET /satisfaction-surveys/results`, com ano/campanha/grupo e filtros oficiais; retorno exclusivamente agregado para `access` | KPIs, ranking, gráfico combinado, detalhes contextuais e exportação autorizada |
| Respostas identificadas | `GET /satisfaction-surveys/campaigns/{campaign_id}/responses`, `GET /satisfaction-surveys/responses/{response_id}` | Somente gestores, consulta separada |
| Configuração | Navegação para [UI-02](./UI-02-CONFIGURACAO-PESQUISAS.md) | Gestores; servidor autoriza cada write |

**Gap técnico a tratar na execução:** listar anos/campanhas para usuário só com `commercial.access` pode exigir projeção própria no contrato agregado, sem ampliar acesso ao CRUD administrativo. Reusar `commercial-api` como owner, sem levar regra de agregação ao frontend. O CAIO conserva seis tools: paridade via `read`/`analyze`, mesmo serviço de domínio, mesma validação de permissões e nenhuma exposição de respostas privadas sob acesso agregado.

## 11. Mapa de componentes — lista de execução verificada

| Responsabilidade visual | Import/nome real | Origem comprovada |
|---|---|---|
| Hero | `CommercialPageHero` | `commercialUi.ts`, wrapper de `createDashboardPageHero` em PluginUI |
| Caminho | `CommercialPagePath` | `commercialUi.ts`, wrapper `createDashboardPagePath` |
| Ajuda no título | `CommercialSectionHintLabel` | `commercialUi.ts` → `SectionHintLabel` |
| Botões do Hero | `CommercialActionButton` | `commercialUi.ts` → `ActionButton` |
| Filtros e limpeza | `CommercialFilterBarShell`, `CommercialSelectField`, `CommercialMultiSelectField`, `CommercialTextField`, `CommercialClearFiltersButton`, `cmFiltersKit` | `commercialUi.ts`; padrão `AnalyticsFilters.tsx` |
| Painéis | `SectionCard`, `CommercialSectionCard` | PluginUI / `commercialUi.ts` |
| KPI | `CommercialMetricCard` | `commercialUi.ts` → `createMetricKpiCard` |
| Delta | `CommercialTrendDelta` | `commercialUi.ts` → `createDashboardTrendDelta` |
| Gráfico + controles | `ChartViewShell`, `MultiTypeSeriesChart`, `ChartTypeSegmentToggle`, `ChartSeriesColorsPopover` | PluginUI; padrão completo em `AnalyticsRolSeriesChart.tsx` |
| Preferências | `usePersistedChartPreferences`, `applySeriesViewPreferences`, `buildChartSeriesConfigItems`, `resetSeriesViewPreferences` | PluginUI |
| Exportação do gráfico | `CommercialTabularExportButtons` | `commercialUi.ts` → PluginUI |
| Barras dimensões | `CommercialHorizontalValueBars` | `commercialUi.ts` → `HorizontalValueBars`, contrato `max`, `items[].meta`, `layout` conferido |
| Comparação por grupos | `CommercialSectionCard`, `CommercialDataTable`, `DataTableColumn<T>` | wrappers de `commercialUi.ts` → `SectionCard` / `DataTable` do PluginUI; 5+10 linhas |
| Responsividade em cards (a validar) | `DataTableSection`, `CommercialDataCardsGrid`, `CommercialDataRecordCard` | PluginUI e `commercialUi.ts`; conferir integração em mobile antes de implementar |
| Tabelas de outras seções | `CommercialDataTable`, `CommercialPagination` | `commercialUi.ts` → PluginUI |
| Leitura detalhe | `CommercialHostDrawer`, `CommercialDetailCard`, `CommercialDetailFieldGrid` | `commercialUi.ts` |
| Estados | `CommercialLoadingCard`, `EmptyState`, `CommercialStateBanner` | PluginUI e `commercialUi.ts` |

**Lacunas honestas:** `CommercialTrendDelta` formata `%` e não serve aos deltas em pontos do Resumo. PENDING: expansão de “Mais filtros”, domínio fixo de eixos, tooltip completo e seleção por toque/teclado, lacunas temporais (`connectNulls`), responsividade real e paleta. Exports existentes não provam integração final. Não criar abstrações sem Abstraction Gate.

## 12. Critérios de aceite e testes

1. `CommercialPagePath` + **um Hero real do PluginUI**, com **todos** os filtros e ações globais dentro dele; Configuração só para gestão. Sem toolbar de filtros espalhada sob o Hero.
2. Após o Hero: **Resumo → Evolução histórica → Dez dimensões → Comparativos → Respostas privadas**; sem tabela histórica fixa na Evolução.
3. Cinco KPIs; base e período explícitos; trend apenas quando calculável; delta pontual correto, sem cor induzida.
4. Gráfico combinado IGS/NPS dual-axis, sem tabela fixa, com tipo, inspector, preferências e exportação do PluginUI; detalhes por campanha sob demanda e ano completo recalculado pelo backend, sem média de médias.
5. `CommercialHorizontalValueBars` usa `max={5}`, ranking, `meta=n válido`, dez perguntas oficiais e layout responsivo.
6. Comparativo aprovado: cinco indicadores visíveis + dez dimensões expansíveis **na mesma tabela**; Geral/Estratégicos/Demais, desktop em quatro colunas e celular em cards por indicador; mostrar bases autorizadas, não inventar estratificação, e `commercial.access` não consegue inferir grupos pequenos por diferença ou filtros.
7. Com `commercial.access`, nenhum request a endpoints identificados ou montagem do drawer; gestor lê resposta imutável. Backend decide todas as autorizações.
8. Loading, vazio, erro, supressão e indisponibilidade de fonte diferentes; retry global no Hero.
9. Todos os visuais vêm do PluginUI/CommercialUi existente; inventário residual de exports/props e testes de regressão do Portal antes do diff; nenhuma abstração/CSS novo sem Abstraction Gate.
10. Desktop/tablet/mobile, teclado, zoom, foco, contraste e leitores de tela verificados.
11. REST e CAIO `read`/`analyze` usam o mesmo serviço de domínio e testes de permissão; relatório final inclui branch, HEAD, working tree, arquivos, testes, resultados e gaps.
12. Segunda entrega de planos de ação continua obrigatória conforme Word; não antecipar sua UI nem exibir o indicador de ações como `0`.

**Implementação ainda não iniciada.** Reancorar no HEAD real, investigar contratos e testes canônicos da frente, aplicar menor diff correto e validar com usuário na ordem de cima para baixo.
