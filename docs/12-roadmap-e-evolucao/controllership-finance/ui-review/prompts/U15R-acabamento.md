# Prompt para o Cursor — UI review, U15R (últimos acabamentos)

```text
PROMPT CURSOR — UI REVIEW · U15R — área do gráfico ainda branca, valor de KPI cortado e ícone sobre o
título no celular, lasca do dia 0

CONTEXTO
Revisão do Claude sobre U15 (16/11/2026), conferida em PROD (análise 07–13/11, 1440×900 e 390×844):
ACCEPT_WITH_RESIDUAL. PASS em PROD: com day=2026-11-10 o gráfico mantém os 7 dias (10/11 destacado,
os outros esmaecidos — P2); hero em 390 com título quebrando e os 3 botões dentro da tela (P3); KPIs
em 2 colunas (P4a). Ficaram quatro pontos.

Q1 · Alta · Área do gráfico continua BRANCA no tema escuro (P1 só pela metade)
   A medição da U15 olhou o contêiner `.delpi-ui-series-chart` (transparente), mas o retângulo SVG
   `.delpi-ui-series-chart__plot-area` continua com fill="#ffffff" (medido em PROD). O kit já aceita
   sobrescrever pela parte: `chartParts={{ plotArea: { visible: true, style: { fill: "transparent" } } }}`
   (ver ConfigurableSeriesChart.test.tsx, «aplica opacity da parte plotArea»). Fazer no adaptador Cf*;
   conferir grade e rótulos nos dois temas. Sem mudar o kit.
   Medição: nenhum descendente do gráfico com fill/background branco no tema escuro (varrer TODOS os
   elementos, não só o contêiner).

Q2 · Média · Valor do KPI cortado com reticências
   1440 com filtro de dia: «R$ 136.125,…» (Valor conferido). 390: «R$ 1,06 …». O formato compacto só
   entra a partir de milhão; a regra (AC-KPI-1) é «se não couber, compactar». Compactar conforme o
   espaço (ex.: «R$ 136,1 mil», «R$ 1,06 mi») com o valor completo no title, e nunca reticências no
   valor. Teste com 136.125,47 e 1.060.126,08 em 1440 e 390.

Q3 · Média · Celular (390): ícone do KPI por cima do título
   Em 2 colunas, o ícone cobre «Diferença nas Altas» e «Sem par em aberto». No celular, ícone menor ou
   fora do fluxo do título (como no Comercial em 390); título e valor sem sobreposição. Medição: caixas
   do ícone e do título sem interseção.

Q4 · Baixa · Lasca da barra no dia 0
   Introduzida pelo próprio K1 da U14R2 (altura mínima de 4 px na barra clicável). Dia 0 sem barra
   visível; o alvo de clique/teclado pode continuar (transparente). Mudança no plugin-ui aditiva e
   pequena, com caracterização (sem onPointSelect nada muda) e prova dos consumidores; publicar o
   plugin-ui antes do MFE (tag rollback-ui-review-u15r-plugin-ui).

VERIFICAÇÃO
Pedido com Q1–Q4 e as medições acima anexadas (H6: AC visual sem medição = reprovado; medir o que pinta,
não só o contêiner). Até 3 rodadas.

ENTREGA
HML → PROD: plugin-ui (Q4) primeiro, depois MFE (tag rollback-ui-review-u15r-controllership-finance).
Parar ao concluir.

REGRAS
As da trilha. No plugin-ui, só o Q4.
```
