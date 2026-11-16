# Prompt para o Cursor — UI review, U15 (polimento após U14R2)

```text
PROMPT CURSOR — UI REVIEW · U15 — fundo branco do gráfico no tema escuro, gráfico diário filtrando
a si mesmo e hero no celular

CONTEXTO
Revisão do Claude sobre U14R2 (16/11/2026), conferida em PROD (análise 07–13/11) em 1440×900 e 390×844:
ACCEPT_WITH_RESIDUAL. PASS em PROD: título «Pendentes» sem corte; tabela de ocorrências cabe em 1440
(1.341 px, chave columns:v2, «Campo» oculto); Evolução em barras com 7 dias, clique em 10/11 → day=
e KPIs filtram, novo clique → limpa. Ficaram quatro pontos.

P1 · Alta · Gráfico diário com fundo BRANCO no tema escuro
   O BarSeriesChart do kit pinta `chartArea.fill` (padrão do deck: #ffffff) inline. O kit já aceita
   `options.theme: "dark" | "light"` e `options.backgroundColor` (seriesChartThemeStyle em
   seriesChartOptions.ts). Fazer no adaptador Cf*: theme conforme o tema do Portal (claro/escuro, o
   mesmo sinal que os demais componentes usam) e backgroundColor transparente; conferir texto, grade
   e rótulos nos dois temas. Sem mudar o kit.

P2 · Média · Selecionar um dia filtra o próprio gráfico diário
   Com day=2026-11-10, os outros dias viram 0 (medido: «09/11: 0 … 13/11: 0»), e o usuário não troca
   de dia sem limpar antes. Mesma regra do AC-SEL-3: o gráfico que seleciona é calculado sem o filtro
   da própria dimensão — `daily` sem `day` (BFF, aditivo, contrato §6, teste), dia selecionado
   destacado e os outros esmaecidos.

P3 · Média · Hero da análise no celular (390)
   Título «Análise de 07/11/2026 a 13/11/» cortado; o terceiro botão («Nova análise») fica fora da tela.
   Título quebra em linhas; ações quebram/empilham dentro do hero (conferir o PageHero do kit e o
   Comercial em 390). Último item do PagePath com reticências.

P4 · Baixa · Detalhes
   a) KPIs no celular: um por linha (6 cartões altos); dois por linha em 390, como no Comercial.
   b) Dia com 0 ocorrências desenha uma lasca de barra; 0 = sem barra (alvo de clique pode continuar
      acessível pelo teclado/rótulo).

VERIFICAÇÃO
Pedido ao verificador com P1–P4 e MEDIÇÃO anexada (H6): cor de fundo computada do gráfico nos dois
temas; com day selecionado, nº de dias com valor > 0 igual ao sem filtro; em 390, scrollWidth ≤
clientWidth no hero e todos os botões dentro da tela; KPIs 2 por linha. Até 3 rodadas.

ENTREGA
HML → PROD (BFF primeiro se P2 mexer na BFF): tags rollback-ui-review-u15-controllership-finance-api e
-controllership-finance. Parar ao concluir.

REGRAS
As da trilha. Sem mexer no plugin-ui (o que faltar → registrar e parar).
```
