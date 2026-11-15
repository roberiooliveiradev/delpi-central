# Prompt para o Cursor — UI review, U12 (revisão 2 do owner)

```text
PROMPT CURSOR — UI REVIEW · U12 — tabelas ordenáveis com escolha de colunas, filtros no hero,
gráficos reorganizados e troca de aba sem remontar (inclui a U11)

CONTEXTO
O owner abriu em HML a Auditoria de Entradas (entrada e análise 01/11–15/11) depois da U10 e pediu:
1. filtros e «Executar auditoria» dentro do hero, sem o card «Nova análise» (economizar espaço vertical);
2. sem coluna «Ação/Abrir» — a linha já abre o detalhe;
3. ordenação em todas as colunas de TODAS as tabelas (padrão do Portal);
4. escolha de colunas pelo usuário (o kit já tem);
5. gráficos reorganizados: legenda das roscas maior que o gráfico, barras com metade do card vazia,
   juntar gráficos num card e dar mais espaço à Evolução por dia;
6. trocar de aba (Ocorrências, Notas casadas, Sem par…) sem recarregar a página inteira.
O Claude conferiu no código e acrescentou achados nos mesmos prints (valores crus «408.00», termo
«field» na tela, paginação com quatro «?», comparação 15 dias × 31 dias dando −48,1%, evolução diária
misturando outubro e novembro no eixo, «99+» vermelho nas abas, filiais com a mesma razão social).
A U11 (previous null) não foi executada e entra aqui como W1a.

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/ui-review/
  review-2.md  ← diagnóstico T1–T9, E1–E4, A1–A10 com causa no código e layout alvo
  track.md §10 ← etapas W0–W8, critérios de aceite
Padrão: docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md (§9.3, §14, §15, §16,
§18, §22), 30-plugin-ui-reuse-map.md. Referências vivas no Comercial:
  filtros no hero  → plugins/commercial/src/features/customers/pages/CustomersPage.tsx (FilterBarShell
                     como children do PageHero)
  tabela completa  → plugins/commercial/src/features/satisfaction-surveys/SatisfactionSurveysPage.tsx
                     (columnPreferencesKey, fontSizePreferencesKey, viewLayoutPreferencesKey + renderCard)
  paginação        → plugins/commercial/src/app/dataTableUi.ts (sem hints)
  ordenação server → plugins/dashboard-production/src/pages/OtdPage.tsx (serverSort)
O kit já tem tudo: DataTableSection (sortable/sortValue, serverSort, columnPreferencesKey,
defaultColumnVisibility, renderCard), DistributionDonut (legendPlacement, size), HorizontalValueBars
(layout "stacked"), UnderlineNav (mode "tabs"), PageHero (children = faixa de filtros).
Mudança no plugin-ui só se faltar algo, aditiva, com caracterização e prova dos consumidores (V3).

CAUSA DO A1 (lida no código, EntryAuditAnalysisPage.tsx)
navigateWith → navigatePluginPath dispara popstate → routeEpoch++ → params novo → filtersFromUrl
devolve objeto novo → o efeito do summary (deps [analysisId, filters, refresh]) zera summary,
breakdowns, daily, rows e page e busca tudo de novo; breakdowns e daily dependem de summary e
repetem. Confirmar com contagem de requisições antes de corrigir.

MISSÃO — executar W0 → W8 sem parar entre etapas, um commit por etapa (W2: um por página ou grupo
pequeno de páginas), track.md atualizado a cada etapa.

W0  Inventário: matriz de todas as tabelas do MFE (página, tabela, paginação cliente/servidor,
    colunas ordenáveis, columnPreferencesKey, cards no celular, coluna «Abrir», <table> local) e
    medição de requisições ao trocar de aba na análise 01–15/11 em HML (antes). Registrar no track.
W1  BFF, aditivo, com testes:
    a) sem análise anterior → "previous": null no summary (daily.previous segue []); regra do
       anterior: mesmo número de dias, termina no dia anterior ao início, mesmas filiais e tipos,
       concluída; senão null. Contrato backend §6. CLARA: analyze/compare só com anterior válido.
    b) ordenação no servidor: sort=<coluna>&order=asc|desc em analyses, occurrences, documents,
       unmatched, cte, posted_outside e tes; lista branca por recurso; sem parâmetro = ordem de
       hoje; coluna fora da lista → 422. Manter compatível o `sort` atual de occurrences.
       Contrato §6 e api do MFE (entryAuditApi.ts).
W2  Padrão de tabela em TODAS as tabelas do MFE: colunas de dado ordenáveis (serverSort quando
    a paginação é no servidor; sortValue tipado no cliente), columnPreferencesKey
    "controllership-finance:<página>:<tabela>:columns:v1" + fontSizePreferencesKey, Tabela/Cards
    no celular em listas de registros, linha clicável sem coluna «Abrir», paginação sem hints,
    rótulo de filtros por uso. <table> local de registros → DataTableSection; matriz fica com
    motivo. Teste estrutural que falha se uma DataTableSection não tiver coluna ordenável ou
    columnPreferencesKey (exceções nomeadas no teste).
W3  Formatação por tipo de campo (R$, %, data, texto) para Protheus/XML/Diferença e rótulo de
    todos os campos das regras (nada de «field»); teste sobre o catálogo de regras.
W4  Entrada da auditoria: De, Até, Filiais, Tipos e «Executar auditoria» dentro do hero
    (FilterBarShell, uma moldura); explicação na ajuda do título; card «Nova análise» removido;
    progresso logo abaixo do hero; histórico com paginação e ordenação no servidor, sem coluna
    «Ação»; filial pelo código («Filial 01 · SC»; lista «Filiais 01 e 02»; razão social no title).
W5  Resultado — layout do review-2 §3: «Panorama» (Conformidade + Severidade, legendas abaixo)
    5/12 ao lado de «Evolução por dia» 7/12; «Onde estão as ocorrências» 12/12 com tema,
    fornecedor (top 8) e TES (top 8) em três colunas, barras stacked na largura toda, clique filtra
    a tabela; evolução com o anterior alinhado por dia, eixo dd/mm, legenda com as datas do
    anterior, sem anterior → só a série; «Lançadas fora do período» fora da Conformidade, com
    ajuda que diz o que a contagem é pela regra no código; «Filtros aplicados» só com filtros de
    detalhamento e escondida quando vazia; CLARA com botões em linha sem marcador. 1024: Panorama e
    Evolução empilhados; 390: tudo em uma coluna.
W6  Resultado — abas: filtros memorizados pela chave serializada só dos filtros (sem tab, page,
    page_size, sort, order); trocar de aba busca só a aba; atualizar não zera o que está na tela;
    CfUnderlineNav mode="tabs"; contadores exatos e neutros (sem «99+», sem vermelho); colunas por
    aba com os campos que a BFF já entrega (faltou → V4 com a lista); ordenação no servidor e menu
    Colunas em todas as abas. Teste: trocar de aba não chama summary/breakdowns/daily.
W7  HML: Playwright — ordenar cada coluna asc/desc e conferir a página 2; menu Colunas persiste
    após F5; troca de aba = 1 requisição da aba e 0 de summary/breakdowns/daily; 1440/1024/390
    claro/escuro; axe sem violação nova; perfis cf-access e cf-manage; análise sem anterior mostra
    «Sem análise do período anterior para comparar». Screenshots no report (não commitar).
W8  PROD: tags rollback-ui-review-u12-controllership-finance-api e -controllership-finance
    (e -plugin-ui se tocado); BFF primeiro, depois MFE; conferir pela leitura da CLARA que o
    summary de uma análise sem anterior traz previous null. Parar e pedir ao owner os prints da
    entrada e de uma análise em PROD (desktop e celular).

REGRAS INEGOCIÁVEIS
1. main, sem branch; git add só com caminhos explícitos (nunca -A, ., commit -a); push a cada etapa.
2. Componentes do kit pelos adaptadores Cf*; nada de tabela, card, hero, badge ou gráfico em CSS local.
3. Sem mudança de regra de negócio nem de permissão. Contrato só aditivo (W1), documentado no §6.
4. DoD por página: 1440/1024/390, claro e escuro, teclado e foco, estados do §16, ajuda no mesmo commit.
5. Sem dado real no repositório (CNPJ, fornecedor, valor, chave). Screenshots fora do git.
6. Paradas V1–V6 do track §2. Página não aberta = INCONCLUSIVE.

REPORT (ao parar)
W0: matriz de tabelas e requisições por troca de aba (antes). W1: parâmetros, lista branca, testes.
W2: tabelas corrigidas por página e exceções com motivo. W4–W6: antes/depois nos três tamanhos.
W6: requisições por troca de aba (depois). W7: resultado por teste. W8: tags, páginas abertas,
leitura da CLARA. Quadro final com critérios de aceite do track §10 (PASS/FAIL/INCONCLUSIVE).
```
