# UI-01 — Página de Resultados da Pesquisa de Satisfação do Cliente

> **Status:** proposta de UX refinada e registrada em 11/11/2026 após crítica do solicitante; **não implementada nem homologada visualmente em todas as seções**. Regra do Hero com todos os filtros e ações globais: **decisão aprovada**. A nova ordem das seções e composição do resumo foram aceitas para registro, sujeitas à revisão por etapas. Branch observada: `main`, HEAD `34d9106cbd86152a88821b6d3f38cb1b4997251e` (revalidar antes da implementação).
>
> **Owner visual:** `plugins/commercial` (MFE). **Autoridade de regras, métricas, acesso e privacidade:** `commercial-api`; origem de clientes e atributos comerciais conforme fonte oficial via `api-delpi`/TOTVS. Esta especificação não concede autorização de implementação ou alteração de contrato backend.
>
> **Referências:** [índice mestre](./REQUIREMENTS-INDEX.md), [Word e decisões de negócio](./BUSINESS-DECISIONS.md), [contrato da entrega 1](./SURVEY-FIRST-RELEASE-CONTRACT.md), [plano global de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md). Código verificado em `plugins/commercial/src/app/commercialUi.ts`, `features/overview/OverviewPage.tsx`, `features/analytics/AnalyticsOtdPage.tsx`, `features/analytics/AnalyticsOpportunitiesPage.tsx`, `features/analytics/components/AnalyticsClosingRateSeriesChart.tsx`, `plugins/plugin-ui/src/components/layout/PageHero.tsx`, `plugins/plugin-ui/src/components/charts/{HorizontalValueBars.tsx,ChartViewShell.tsx,MultiTypeSeriesChart.tsx}`.

## 1. Finalidade e critérios de UX

A entrada `Início > Marketing > Pesquisa de satisfação do cliente` abre diretamente a **página de Resultados**, rota candidata `/apps/commercial/satisfaction-results`, usando `pluginRoutes.ts`/`navigatePluginView`, não URL absoluta hardcoded em componentes. A visão serve a três perguntas: **como está a satisfação, como evoluiu e onde investigar oportunidades de melhoria**. O público `commercial.access` recebe exclusivamente agregados; `commercial.marketing` ou `commercial.manage` tem adicionalmente navegação para Configuração e consulta individual autorizada.

**Ordem proposta definitiva para revisão:** (1) `CommercialPagePath` e Hero; (2) Resumo executivo; (3) Evolução histórica; (4) Avaliação das dez dimensões; (5) Comparações por grupo; (6) consulta por empresa **somente para gestores**. O histórico tabular faz parte da própria seção Evolução, não é outra seção repetida. O indicador de ações concluídas será acrescentado na **entrega 2 obrigatória**, nunca simulado na primeira.

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
│ IGS:       ●───●────●────●────●────● (semestres 2024/1...2026/2)        │
│ [Tabela de apoio no mesmo SectionCard: campanha, n, IGS, NPS, taxa...]   │
├──────────────────────────────────────────────────────────────────────────┤
│ AVALIAÇÃO DAS 10 DIMENSÕES                                               │
│ [Ordem: menor média primeiro, ou ordem do questionário via Hero]          │
│ Prazo de entrega       ━━━━━━━   3,8  (n válido)                          │
│ Flexibilidade          ━━━━━━━━  4,0                                      │
│ ... completar dez itens; eixo/máximo fixo 5                              │
├──────────────────────────────────────────────────────────────────────────┤
│ COMPARAÇÃO GERAL / ESTRATÉGICOS / DEMAIS                                 │
│ IGS, NPS, taxa, satisfeitos, críticos, dimensões; amostra por grupo      │
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
│ [IGS] [NPS]               │
│ [Taxa] [Satisfeitos]      │
│ [Críticos]                │
├───────────────────────────┤
│ Evolução histórica        │
│ [gráfico largura total]   │
│ [tabela adaptativa]       │
├───────────────────────────┤
│ Dez dimensões             │
│ [barras layout=stacked]   │
├───────────────────────────┤
│ Comparações               │
│ [tabela adaptativa]       │
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

**Decisão semântica:** todos os **filtros da página e ações globais** ficam dentro do Hero, inclusive eventual escolha entre IGS/NPS da série histórica ou ordenação das dimensões, se forem controles de consulta. Para simplificar a primeira entrega, **gráfico principal fixo em IGS e ordenação inicial menor média primeiro**; o backend também fornece NPS no histórico tabular. Só introduzir seletores adicionais no Hero após necessidade confirmada. Controles puramente de apresentação oferecidos pelo `ChartViewShell` (ex.: escolher tipo de gráfico) são opcionais, não necessários ao escopo mínimo; se forem adotados, validar com o solicitante se devem ficar no Hero para manter a regra. Ações contextuais de cada linha ou de modal (`Abrir resposta`, confirmação/cancelamento) ficam junto ao contexto, não no Hero.

**Volume e desempenho:** Ano/Campanha/Grupo sempre visíveis. Controles menos frequentes em “Mais filtros”, dentro do mesmo Hero; estado de filtros ativos permanece identificável. A seleção `Ano completo` só é oferecida se a API suportar consolidação adequada. Não usar `AnalyticsFilters` diretamente se sua semântica de pedidos/competência não corresponder à pesquisa: reutilizar **as primitivas oficiais**, não seus filtros operacionais.

## 4. Resumo executivo — composição PluginUI

**Objetivo:** responder imediatamente “como foi a pesquisa?” com contexto e tendência.

| Parte | Reuso PluginUI / Comercial | Regra exata |
|---|---|---|
| Container e subtítulo | `SectionCard` (PluginUI), `cmSectionCardClassNames`/`cmSectionLabels` ou `CommercialSectionCard` | Título “Resumo executivo”; informar campanha/período e `respondentes / participantes cadastrados` |
| IGS | `CommercialMetricCard` (`createMetricKpiCard`) | Média 1–5, valor `x,x / 5`, **delta em pontos de escala**, se comparável |
| NPS | `CommercialMetricCard` | -100 a +100; variação em **pontos de NPS**, nunca percentual |
| Taxa de resposta | `CommercialMetricCard` | respostas / participantes cadastrados; delta em **pontos percentuais (p.p.)**, não “convites enviados” |
| Satisfeitos (4–5) | `CommercialMetricCard` | percentual entre notas gerais válidas |
| Críticos (1–2) | `CommercialMetricCard` | percentual entre notas gerais válidas, não número de casos abertos |
| Variação | `CommercialTrendDelta` (`createDashboardTrendDelta`) quando props suportarem, ou `hint` de `CommercialMetricCard` | Mostrar somente com comparação válida, nomear o período anterior e denominadores; sem “positivo” automático para crescimento da taxa de críticos |
| Carregando/vazio/erro | `CommercialLoadingCard`, `EmptyState`, `CommercialStateBanner` | Não renderizar 0 para ausência; erro ≠ período sem respostas |

**Densidade:** cinco KPIs em uma faixa responsiva existente (`cm-home-kpi-grid` apenas se coerente com o Portal), sem sexto card “respondentes”. Respondentes entram no contexto do bloco. **Não separar críticos em barra com cor de alerta**: mesma hierarquia visual dos outros cinco indicadores; possível tratamento de cor só se houver política oficial. Não inventar metas de IGS, NPS ou limiar `IGS<4`.

**Comparações:** valor da pesquisa anterior é contexto com período, delta somente se ambos têm dados e método idêntico. Mudanças de população devem ficar visíveis para evitar inferir melhoria causal; comparar períodos de grupos distintos é análise descritiva, não comprovação de impacto.

## 5. Evolução histórica — um bloco, gráfico + tabela

**Objetivo:** responder “como mudou ao longo de vários anos?” imediatamente após o resumo. Não manter seção “Histórico anual” duplicada.

| Parte | Componente existente | Decisão |
|---|---|---|
| Container | `SectionCard`/`CommercialSectionCard` | “Evolução histórica” após KPIs |
| Gráfico temporal | `ChartViewShell` + `MultiTypeSeriesChart` exportados pelo PluginUI | Linha do **IGS**, eixo temporal por campanha real ordenada por datas, séries de um tipo/escala por vez |
| Configuração de série | `MultiTypeSeriesSpec` no gráfico, com cor por tokens/paleta do kit | Série `igs`, `chartType="line"`, `categoryKey` referente ao período; configurações exatas do pacote são autoridade |
| Alternativas de visualização | `ChartTypeSegmentToggle`, `ChartOverlayOptionsPopover`, `ChartSeriesColorsPopover` só se exigidos e aprovados | **Não adicionar controles à toolbar do gráfico por padrão**: todos os filtros e ações globais ficam no Hero |
| Tabela auxiliar no mesmo bloco | `CommercialDataTable`, eventualmente `CommercialPagination` | Campanha/período, n respondentes, n participantes, IGS, NPS, taxa, variação; tabela visível no mesmo bloco, sem seção redundante |
| Estados | `CommercialLoadingCard`, `EmptyState` | Uma campanha: sem tendência; nenhuma campanha: indisponível; série deve aceitar anos múltiplos |

**Paridade do gráfico:** `ChartViewShell` possui slots `granularity`, `overlays`, `typeToggle`, `exportActions` e `children`; seu uso sem toolbar é válido. `MultiTypeSeriesChart` exige `data`, `categoryKey`, `series`, `chartType` e aceita `height`, `formatY`, `formatTooltipValue`. Aplicar unidade IGS (1–5), não interpolar campanhas ausentes e não depender do ano corrente hardcoded. Se controles de tipo/exportação forem realmente introduzidos, primeiro resolver coerência com a política de ações globais no Hero.

**Cálculo anual:** a API deve recomputar IGS e NPS usando respostas válidas de todas as campanhas no ano; não tirar média simples de NPS sem os denominadores. Ano completo pode ter empresas que responderam em duas campanhas; contar respostas por campanha e rotular claramente a unidade (empresa por campanha), sem chamar isso “empresas únicas no ano” sem regra específica.

## 6. Avaliação das dez dimensões — ranking justificável

| Parte | Componente real | Propriedades / comportamento |
|---|---|---|
| Container | `SectionCard` | Título “Avaliação por dimensão”, ajuda explicando notas 1–5 e `Não se aplica` |
| Ranking | `CommercialHorizontalValueBars` → `HorizontalValueBars` do PluginUI | Passar `items: {id,label,value,valueLabel?,meta?}[]`; usar `max={5}`, `aria-label`, `layout="columns"` desktop / `"stacked"` mobile |
| Texto de amostra | `items[].meta` | `n = [respostas válidas]`; não exibir valor inventado quando `n=0` |
| Ordem | Ordenação dos dados entregue ao componente | Default: menor média primeiro; empate: ordem oficial das 10 perguntas. Se permitir “ordem original”, seletor no Hero |
| Escala | Prop `max={5}` do kit | **Obrigatória**, porque o default do kit é o maior valor dos itens e distorceria as barras quando o maior fosse 4,7 |
| Interação | Omitir `onItemClick` na primeira entrega | Não criar drill-down que possa revelar respostas individuais por agregados pequenos |
| Cor e alertas | Tokens padrão do kit | **Não pintar abaixo de 4 como perigo** sem meta/limiar de criticidade aprovado |

As **dez dimensões e seus rótulos oficiais** vêm do Word/contrato da pesquisa. Os nomes presentes nos protótipos anteriores eram ilustrativos: usar textos oficiais e ordem oficial após conferência ao construir a configuração da tela. A API fornece número válido por dimensão (excluindo `Não se aplica`).

## 7. Comparativo de segmentos — evidência e proteção

Seção única “Comparação de clientes” com `SectionCard` + `CommercialDataTable`. Colunas: Indicador / Geral / Estratégicos / Demais, contendo IGS, NPS, taxa, satisfeitos, críticos e as dez dimensões (via estrutura de tabela existente com exibição responsiva/paginação se necessária). Mostrar `n` de cada grupo **na tabela ou cabeçalho da coluna**, sem cabeçalhos gigantes e sem inventar população.

- Grupos e atributos somente quando o backend conhecer origem, período e classificação oficial; caso ausentes, “Comparação indisponível”, não substituir por proxy.
- Limiar de privacidade e supressão no `commercial-api` **antes** da resposta da API, também impedindo reconstrução por subtração de grupos expostos (total − subgrupo).
- Não calcular percentuais reconstituindo registros no frontend. Valores da tabela são agregados autorizados.
- Taxas requerem denominadores compatíveis; comparações com campanhas diferentes precisam rótulo explícito.
- `CommercialPagination` e `CommercialDataListToolbar` apenas se o volume exigir, sem botões globais adicionais fora do Hero.
- `commercial.access` não recebe lista identificável de clientes, mesmo que o usuário tenha selecionado outro filtro de carteira.

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

Desktop: Hero compacto, faixas de KPI responsivas, gráfico com largura total; dimensões em colunas. Tablet: Hero quebra filtros e KPIs conforme classes oficiais. Mobile: Hero empilha controles, ranking usa `layout="stacked"`, tabelas usam responsividade real de `CommercialDataTable`, sem implementar `MobileSurveyTable`. Foco, teclado, zoom 200%, descrições acessíveis e rótulos diferenciando pontos vs p.p. são critérios de aceite.

## 10. API e paridade CAIO

| Necessidade | Fonte planejada / autoridade | Consumidor |
|---|---|---|
| Lista de campanhas e anos com resultados | Consultas oficiais `GET /satisfaction-surveys/campaigns` (ou projeção agregada autorizada, a ajustar na etapa) | Hero sem expor campos restritos a `access` |
| Resultados e comparações | `GET /satisfaction-surveys/results`, com ano/campanha/grupo e filtros oficiais; retorno exclusivamente agregado para `access` | KPIs, ranking, gráfico e tabela |
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
| Gráfico | `ChartViewShell`, `MultiTypeSeriesChart` | PluginUI, uso real `AnalyticsClosingRateSeriesChart.tsx` |
| Barras dimensões | `CommercialHorizontalValueBars` | `commercialUi.ts` → `HorizontalValueBars`, contrato `max`, `items[].meta`, `layout` conferido |
| Tabelas | `CommercialDataTable`, `CommercialPagination` | `commercialUi.ts` → PluginUI |
| Leitura detalhe | `CommercialHostDrawer`, `CommercialDetailCard`, `CommercialDetailFieldGrid` | `commercialUi.ts` |
| Estados | `CommercialLoadingCard`, `EmptyState`, `CommercialStateBanner` | PluginUI e `commercialUi.ts` |

**Lacunas honestas:** props de `CommercialTrendDelta`, expansão exata do filtro “Mais filtros”, comportamento responsivo do `CommercialDataTable` e tokens/paleta do gráfico precisam ser conferidos no código e nos testes durante a execução; existência dos exports acima foi observada, mas sua adequação final a todas as interações não é prova de integração. Não criar wrappers/abstrações novas sem necessidade verificada.

## 12. Critérios de aceite e testes

1. `CommercialPagePath` + **um Hero real do PluginUI**, com **todos** os filtros e ações globais dentro dele; Configuração só para gestão. Sem toolbar de filtros espalhada sob o Hero.
2. Após o Hero: **Resumo → Evolução histórica → Dez dimensões → Comparativos → Respostas privadas**; sem tabela anual redundante fora da Evolução.
3. Cinco KPIs; base e período explícitos; trend apenas quando calculável; delta pontual correto, sem cor induzida.
4. Gráfico aceita multi-anos, linhas por campanhas cronológicas; tabela auxiliar apresenta amostras e NPS; ano completo recalcula sobre respostas, sem média de médias.
5. `CommercialHorizontalValueBars` usa `max={5}`, ranking, `meta=n válido`, dez perguntas oficiais e layout responsivo.
6. Comparativo possui denominações/amostras, não inventa estratificação; `commercial.access` não consegue inferir pequenos grupos ou acessar dados privados por filtros/combinações.
7. Com `commercial.access`, nenhum request a endpoints identificados ou montagem do drawer; gestor lê resposta imutável. Backend decide todas as autorizações.
8. Loading, vazio, erro, supressão e indisponibilidade de fonte diferentes; retry global no Hero.
9. Todos os visuais vêm do PluginUI/CommercialUi existente; inventário residual de exports/props e testes de regressão do Portal antes do diff; nenhuma abstração/CSS novo sem Abstraction Gate.
10. Desktop/tablet/mobile, teclado, zoom, foco, contraste e leitores de tela verificados.
11. REST e CAIO `read`/`analyze` usam o mesmo serviço de domínio e testes de permissão; relatório final inclui branch, HEAD, working tree, arquivos, testes, resultados e gaps.
12. Segunda entrega de planos de ação continua obrigatória conforme Word; não antecipar sua UI nem exibir o indicador de ações como `0`.

**Implementação ainda não iniciada.** Reancorar no HEAD real, investigar contratos e testes canônicos da frente, aplicar menor diff correto e validar com usuário na ordem de cima para baixo.
