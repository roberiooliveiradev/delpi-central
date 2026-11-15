# Revisão de UI — Portal Controladoria & Finanças (Início e Auditoria de Entradas)

Base: prints do owner em PROD (14/11/2026, 22h37) do Início, da Auditoria de Entradas (entrada), do carregamento e do resultado da análise de 01/11 a 15/11/2026 (filiais 01 e 02); código em `plugins/controllership-finance/src/features/{home,entry-audit}`; padrão em `docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md` (citado como §n).

As páginas já usam os adaptadores `Cf*` do `@delpi/plugin-ui` (PageHero, SectionCard, MetricStrip, DataTableSection, DistributionDonut, SemicircleProgressGauge, HorizontalValueBars, ScopeChipBar, ResolutionStatusCell). O problema é composição, vocabulário, formatação, estados e responsivo — não falta de componente.

## G — Em todas as páginas

| # | Problema | Regra | Correção |
|---|---|---|---|
| G1 | Dentro da Auditoria não há caminho de volta: a TopBar só tem «Início» e não existe trilha da página | §11 PagePath em páginas profundas | `PagePath`: Início › Notas fiscais › Auditoria de Entradas › Análise <período> › Ocorrência |
| G2 | Eyebrow inconsistente: «FISCAL» na entrada, «AUDITORIA DE ENTRADAS» no resultado; o card do Início chama a área de «Notas fiscais» | §10 PageHero | Eyebrow = área do Início («Notas fiscais»); título = página; descrição curta; densidade compact; ações e highlights no hero |
| G3 | Identificadores técnicos na tela: temas `cte`, `item`, `header`, `simples`, `coherence`, `key`; tipos `CTE, NFE`; filtros «Filial 01», «CTE», «NFE» | UX PT-BR; identifiers técnicos só no código | Vocabulário único no `entryAuditPresentation.ts`: CT-e, NF-e, Itens, Cabeçalho, Simples Nacional, Coerência fiscal, Chave de acesso; filial pelo nome curto das `options` («Matriz (SC)», «Filial ES») |
| G4 | Números em formato inglês: diferença `170.00`, `-29.92`, `-180.00` | §13 unidade explícita; pt-BR | Valores monetários em R$ pt-BR (`R$ 170,00`, `−R$ 29,92`); código (CST, origem, CFOP) mostra «—» na diferença |
| G5 | Severidade só como texto («Alta», «Média»); donut de severidade em tons de azul | §19 estado não depende de cor; status palette reservada | `StatusBadge` com ícone + rótulo + tom (Alta crítico, Média atenção, Baixa neutro, Info informativo) em tabela, filtros e donut |
| G6 | Botões sem ícone e sem ajuda; KPIs sem ícone e sem explicação | §20 lucide ~16px em botão, ~22px em KPI | Ícone em toda ação (Play, Download, RefreshCw, Plus, Check, RotateCcw, FileCode2, ExternalLink); `CfTitleWithHelp`/tooltip do kit em KPI, seção e ação não óbvia |
| G7 | Carregamento da análise é a frase «Carregando análise…» numa página vazia | §16 estados; `LoadingActivityCard` | Hero + esqueleto dos KPIs enquanto carrega; refreshing mantém o conteúdo; erro com «Tentar de novo»; parcial (filial indisponível) em `StateBanner` |
| G8 | Dimensionamento: campos do formulário ocupando a largura inteira (2.400 px); 7 KPIs num grid de 6 deixando «Resolvidas» órfão; gráficos soltos fora de card; metade da tela vazia ao lado do medidor | §12, §18 | Grids por breakpoint (§18), tudo em `SectionCard`, sem card dentro de card |
| G9 | Desempenho: a análise demora a abrir (o print mostra só o carregamento) | §16 initial × refreshing | Medir; carregar resumo + breakdowns primeiro e as abas sob demanda; paginação no servidor |

## H — Início

| # | Problema | Correção |
|---|---|---|
| H1 | Hero com «Competência —» e «Atenções —» vazios | Highlights com dado real: competência aberta mais recente (e estado do fechamento); atenções = bloqueios do fechamento + Alta pendentes da última auditoria + LNF pendentes (só o que o usuário pode ver). Sem dado → «Nenhuma competência aberta», nunca traço |
| H2 | «Últimos acessos» com o mesmo ícone de calendário para tudo | Ícone da rota (catálogo de ícones como `hubRouteIcons.tsx` do Comercial) |
| H3 | «Lançamento de notas fiscais» não indica que abre outro app | Ícone `ExternalLink` + tooltip «Abre o app Lançamento de Notas Fiscais» |

## E — Auditoria de Entradas (entrada)

| # | Problema | Correção |
|---|---|---|
| E1 | Formulário empilhado em largura total; botão «Criar análise» parece desabilitado | Uma linha (desktop) com De · Até · Filiais · Tipos · [▶ Executar auditoria] primário; empilha ≤ 768 px; validação De ≤ Até; ajuda «O que a auditoria confere» |
| E2 | Depois de criar, não há acompanhamento visível | `ProgressTracker` por filial com etapa e contadores (XML lidos / a ler); ao concluir, abre o resultado |
| E3 | Histórico: «CTE, NFE», data «14/11/2026, 22:07:08», sem status visual, sem ação | Colunas Período · Filiais · Tipos · Situação (`StatusBadge`) · Ocorrências / Altas · Criada em (dd/mm/aaaa hh:mm) · ação «Abrir» (ChevronRight, foco por teclado); celular em cards |

## A — Resultado da análise

| # | Problema | Correção |
|---|---|---|
| A1 | Hero sem contexto da análise; «Exportar XLSX» e «Nova análise» com o mesmo peso | Título «Análise de 01/11 a 15/11/2026», badge da situação, meta (filiais, tipos, criada em/por); ações: Exportar (Download, secundária), Executar de novo (RefreshCw), Nova análise (Plus, ghost) |
| A2 | 7 KPIs, um órfão; «Diferença alta» ambíguo; sem comparação | 6 `MetricKpiCard` com ícone e ajuda: Notas conferidas · Valor conferido · Ocorrências pendentes (hint «n resolvidas») · Alta · Diferença nas Altas · Sem par em aberto; variação contra o período anterior (`TrendDelta`); KPI clicável filtra (Alta → severidade); grid 6 → 3 → 2 → 1 |
| A3 | Conformidade repete Limpas/Divergentes (legenda e cartões) e deixa metade vazia | Um `SectionCard`: medidor + legenda + `MetricStrip` com Sem par em aberto · Explicadas · Lançadas fora do período (informação) |
| A4 | Donut e barras soltos, sem título, temas em inglês, só por tema | Grade de `SectionCard` com título e ajuda: Severidade (donut com cores de status, clique filtra) · Tema · Fornecedor (top 10) · TES; 2 colunas desktop, 1 no celular |
| A5 | Falta a evolução por dia prevista no doc 02 | `ComparativeAreaChart` período × anterior quando o período tem mais de 1 dia |
| A6 | Escopo com códigos e sem os filtros cruzados | `ScopeChipBar` com rótulos de negócio e os filtros aplicados (severidade, tema, fornecedor, TES, dia); URL compartilhável |
| A7 | Abas soltas, nomes diferentes da CLARA («Sem correspondência») | `UnderlineNav` com contagem: Ocorrências · Notas casadas · Sem par · CT-e · TES utilizadas · Lançadas fora do período |
| A8 | Tabela: título «Ocorrências (159)» + «50 registros»; sem nota/série, sem campo, sem Protheus × XML; botão «Resolver» pesado em cada linha | Colunas Severidade (badge) · Nota/Série · Fornecedor · Regra · Campo · Protheus · XML · Diferença (R$ ou «—») · Status (`ResolutionStatusCell` compacta: ícone com tooltip «Marcar como resolvida» e estado); linha abre o detalhe; ordenação; contagem única; celular em cards |
| A9 | «Pergunte à CLARA» sem sugestão visível | Ícone, 3 sugestões clicáveis («Explique as Altas», «O que fazer com as notas sem par?», «Compare com o período anterior») |

## O — Detalhe da ocorrência

Sem print nesta revisão; conferir na U0 contra o doc 03: `PagePath`, hero com badge de severidade e regra, `DetailFieldGrid` (nota, série, fornecedor, TES, campo, Protheus, XML, diferença), blocos «Por quê» e «O que fazer», ficha citada pelo nome, ações Resolver/Reabrir com confirmação, XML (FileCode2), histórico em `Timeline`.

## F — Demais páginas do Portal

Fechamento mensal, documentos, relatórios, administração, Meu perfil e a experiência DRE entram na matriz de conformidade da U0. Desvios do padrão são corrigidos página a página na U6; mudança que não for ajuste de padrão (conteúdo, regra, fluxo) vira lista para decisão.
