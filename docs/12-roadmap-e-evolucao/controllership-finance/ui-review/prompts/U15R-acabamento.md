# Prompt para o Cursor — UI review, U15R (gráfico no padrão do Comercial e últimos acabamentos)

> Versão 2 (16/11/2026): o owner apontou que a «Evolução por dia» usa o gráfico errado. O padrão dos
> Portais é o do Comercial (ChartViewShell + ChartTypeSegmentToggle + MultiTypeSeriesChart), que já
> troca entre coluna, linha e área e já tem clique por categoria (`onCategoryClick`). Isso substitui
> os itens Q1 e Q4 da versão 1. A escolha do BarSeriesChart foi recomendação do Claude (revisão da U14)
> e estava errada.

```text
PROMPT CURSOR — UI REVIEW · U15R — «Evolução por dia» no padrão de gráfico do Comercial; valor de KPI
cortado e ícone sobre o título no celular

CONTEXTO
Revisão do Claude sobre U15 (16/11/2026), conferida em PROD (análise 07–13/11, 1440 e 390):
ACCEPT_WITH_RESIDUAL. PASS: com day selecionado o diário mantém os 7 dias (P2); hero em 390 sem corte
(P3); KPIs em 2 colunas (P4a).
O owner apontou que o gráfico diário está no componente errado. Conferido no código: o Comercial usa
em todos os gráficos de série (21 usos de ChartViewShell, 14 de MultiTypeSeriesChart, 12 de
ChartTypeSegmentToggle) o pacote que troca o tipo de gráfico. Referência viva:
  plugins/commercial/src/features/customers/components/CustomerPurchaseEvolutionChart.tsx
  plugins/commercial/src/app/commercialUi.ts (createDashboardChartToolbarKit, export tabular)
O BarSeriesChart é o gráfico de deck/TV (fundo branco do deck, área de plot branca) — por isso o
fundo branco da U15 e a lasca do dia 0.

R1 · Alta · «Evolução por dia» no padrão do Comercial
   a) ChartViewShell + ChartTypeSegmentToggle family="period_compare" (coluna | linha | área; padrão
      «column») + MultiTypeSeriesChart, pelos adaptadores Cf* (criar no controllershipFinanceUi.ts como
      o Comercial faz no commercialUi.ts). Preferência persistida com usePersistedChartPreferences,
      storageKey «controllership-finance:entry-audit:daily».
   b) Séries: «Este período» e, quando houver anterior válido, «Período anterior» alinhado por dia
      (mesma regra de hoje). Todos os dias do período; eixo Y com o formato de contagem.
   c) Clique no dia: onCategoryClick → filtro day (clicar de novo no mesmo dia limpa); dia selecionado
      destacado (categoryFillKey com a cor de destaque para o dia selecionado e cor esmaecida para os
      outros, ou o recurso equivalente do componente). Continua valendo o AC-SEL-3: o diário não filtra
      a si mesmo.
   d) Exportar série (botões de exportação tabular como no Comercial) e cores da série
      (ChartSeriesColorsPopover) se o Comercial usa no mesmo tipo de gráfico — seguir o que ele faz.
   e) Tema claro e escuro sem fundo branco (o componente do Comercial já respeita o tema). Medição:
      nenhum descendente do gráfico com fill/background branco no escuro — varrer TODOS os elementos.
   f) Remover do MFE o uso do BarSeriesChart e o adaptador criado para ele. NÃO mexer no plugin-ui:
      a prop onPointSelect que a U14R2 acrescentou ao BarSeriesChart fica (aditiva, sem efeito em
      quem não usa) — registrar para o dono do plugin-ui decidir se mantém.
   g) Conferir os outros gráficos de série do MFE (ex.: relatórios da Central de Fechamento): se algum
      usa ComparativeAreaChart/BarSeriesChart onde o Comercial usaria o pacote acima, LISTAR no report
      (não migrar nesta etapa).

R2 · Média · Valor do KPI cortado com reticências
   1440 com filtro de dia: «R$ 136.125,…»; 390: «R$ 1,06 …». A regra AC-KPI-1 é «se não couber,
   compactar»: compactar conforme o espaço («R$ 136,1 mil», «R$ 1,06 mi»), valor completo no title,
   nunca reticências no valor. Teste com 136.125,47 e 1.060.126,08 em 1440 e 390.

R3 · Média · Celular (390): ícone do KPI por cima do título
   Em 2 colunas o ícone cobre «Diferença nas Altas» e «Sem par em aberto». Seguir o Comercial em 390
   (ícone menor ou fora do fluxo do título). Medição: caixas do ícone e do título sem interseção.

VERIFICAÇÃO
Pedido com R1–R3 e as medições anexadas (H6: AC visual sem medição = reprovado; medir o que pinta, não
só o contêiner): nº de categorias = dias do período; troca coluna/linha/área funcionando e persistida
após F5; clique/segundo clique em um dia põe/tira day; sem branco no escuro; KPI sem reticências em
1440 e 390; ícone × título sem interseção em 390. Até 3 rodadas.

ENTREGA
HML → PROD só do MFE (tag rollback-ui-review-u15r-controllership-finance). Parar ao concluir.

REGRAS
As da trilha. Não mexer no plugin-ui.
```
