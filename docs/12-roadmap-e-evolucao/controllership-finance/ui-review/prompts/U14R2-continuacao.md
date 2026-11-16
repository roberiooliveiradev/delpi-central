# Prompt para o Cursor — UI review, U14R2 (continuação H2–H6 com a decisão DR-1)

```text
PROMPT CURSOR — UI REVIEW · U14R2 — continuar H2–H6 do working tree; DR-1 decidido: barras com
clique por dia, mudando o kit (aditivo)

CONTEXTO
H1 (Panorama) está em PROD e o Claude conferiu (15/11, 1440): card do Panorama 338 px, marcadores da
legenda 9–10 px, «73%» e «87» dentro dos gráficos. ACCEPT do H1.
H2–H6 pararam no verificador: OC-1 (AC visual sem medição HML) e DR-1 (BarSeriesChart sem clique por
ponto). DECISÃO DO OWNER (DR-1): opção (b) — barras na «Evolução por dia» COM clique no dia, mudando o
kit. Esta decisão é a dispensa para tocar o plugin-ui nesta etapa, só no que está abaixo.

Retomar do working tree (H2–H5 não commitados). Antes: git status e git diff --stat; conferir que
nada de outros agentes entrou no seu diff (houve commits concorrentes no plugin-ui, ex. 96e9b5bf —
rebase e git add só com caminhos explícitos).

K1 · plugin-ui — BarSeriesChart com seleção de ponto (aditivo)
   a) Props novas e opcionais em BarSeriesChart (via SeriesChartPrimitive/ChartPlotAreaGroup, sem
      afetar Line/Area/MultiType): `onPointSelect?(point, index)` e `selectedPointKey?`. Sem as props,
      render idêntico ao de hoje (caracterização: snapshot/estrutura antes = depois).
   b) Acessível: cada barra clicável vira alvo de teclado (Enter/Espaço), com aria-pressed na
      selecionada e rótulo «<data>: <valor>»; selecionada destacada, demais esmaecidas (mesmo
      padrão do DistributionDonut/HorizontalValueBars); clicar de novo na selecionada → onPointSelect
      com null (limpa), como na rosca.
   c) Testes do kit; prova dos consumidores atuais de BarSeriesChart/SeriesChartPrimitive
      (estoque-seguranca, tv-dashboard-presentation e os demais que o grep achar) — build e testes
      verdes, sem mudança visual.
   d) Publicação do plugin-ui (remote em runtime, consumido por vários portais): HML primeiro com
      smoke de pelo menos 3 portais consumidores + Controladoria; PROD com tag
      rollback-ui-review-u14r2-plugin-ui; plugin-ui ANTES do MFE.

K2 · MFE — Evolução por dia em barras
   Adaptador Cf* para BarSeriesChart; barras por dia (todos os dias do período); anterior como
   referência alinhada por dia; clique no dia → filtro `day` (o mesmo de hoje), clique de novo limpa;
   aparece em «Filtros aplicados». Eixo «Ocorrências». Teste de componente.

K3 · Fechar H2, H4, H5 (já no working tree) — conferir contra U14R-rework.md.

K4 · OC-1 / H6 — medição anexada ao pedido do verificador (obrigatória)
   Playwright em HML, 1440 e 390, com o resultado anexado no pedido:
   - Panorama: card ≤ 520 px; marcadores ≤ 16 px; rótulos centrais dentro do gráfico.
   - Tabela de ocorrências em 1440: scrollWidth ≤ clientWidth com storage limpo E com a chave
     `…occurrences:columns:v1` antiga presente.
   - Título «Pendentes» sem corte (scrollWidth ≤ clientWidth).
   - Evolução: número de barras = número de dias do período; clique numa barra → URL com day=; novo
     clique → sem day.
   - axe (AC-DOD-2) sem violação nova.

VERIFICAÇÃO
Pedido com objetivo = U14R H2–H6 + K1–K4 (AC de review-3 e de U14R-rework), escopo working tree com os
caminhos listados (MFE e plugin-ui), medições anexadas, rodada 1 (ordens anteriores: OC-1 e DR-1 com a
decisão do owner). Até 3 rodadas. DECISION_REQUIRED/EXECUTION_DRIFT → parar.

ENTREGA
Commits separados: plugin-ui (K1) e MFE (K2–K3). HML → PROD: plugin-ui primeiro, depois MFE (tag
rollback-ui-review-u14r2-controllership-finance). Parar ao concluir e pedir ao owner a conferência visual.

REGRAS
As da trilha. Mudança no plugin-ui só a do K1 (aditiva, caracterizada, consumidores provados).

REPORT
K1: API nova, caracterização, consumidores testados, smoke HML. K2: antes/depois. K4: tabela de
medições. Vereditos do verificador sem edição e tabela de rodadas.
```
