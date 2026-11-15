# Prompt para o Cursor — UI review, U14R (rework da U14: Panorama quebrado em PROD)

```text
PROMPT CURSOR — UI REVIEW · U14R — HOTFIX do Panorama em PROD + AC que não passaram

CONTEXTO
Revisão do Claude sobre U14 (15/11/2026), conferida em PROD (minhadelpi.com.br, análise 07–13/11,
1440×900, medição no DOM): REWORK. A seleção nos gráficos funciona em PROD (AC-SEL-1 e AC-SEL-3
provados: Alta → severity=high, rosca mantém as 3 fatias; «Limpar seleção» → URL limpa, números
voltam). Mas o Panorama está QUEBRADO em PROD e três AC marcados PASS/residual não passam.

H1 · CRÍTICO · Panorama quebrado em PROD (introduzido em 92d25b1385, F4, AC-GRA-2)
   index.css:
     .cf-analysis-panorama__conformity [class*="semicircle"],
     .cf-analysis-panorama__severity [class*="distribution-donut"] { flex: 1 1 auto; min-height: 220px; }
   O seletor por substring casa com TODOS os descendentes BEM do kit (…__legend-dot, __legend-item,
   __center, __value, __center-label…). Medido em PROD: min-height 220px em 40+ elementos — marcadores
   da legenda viraram pílulas de 220 px de altura; «73%» e «87» saíram do gráfico (o «73%» aparece
   dentro do cartão «Notas conferidas»; o «87» acima do card); a coluna do Panorama passou de 890 px e
   a «Evolução por dia» ficou com um vazio enorme.
   Fazer AGORA, antes de qualquer outro item:
   a) Remover a regra; dimensionar pelo próprio componente (props de tamanho do kit: `size`/altura
      do gráfico) ou, se precisar de CSS, só na raiz exata (`.cf-semicircle-gauge`,
      `.cf-distribution-donut`) — nunca seletor `[class*=…]` sobre internos do kit. Procurar e remover
      outros `[class*=` no index.css do MFE que alcancem internos do kit.
   b) Evolução por dia sem vazio: o card não estica para a altura do Panorama (alinhamento ao topo
      ou gráfico ocupando a altura útil).
   c) Teste Playwright de GEOMETRIA (não só screenshot) em 1440 e 390: marcador de legenda ≤ 16 px de
      altura; rótulo central dentro do retângulo do gráfico; nenhum elemento do Panorama fora do card;
      card do Panorama ≤ 520 px de altura em 1440.
   d) Verificador → commit → HML → PROD só do MFE (tag rollback-ui-review-u14r-controllership-finance).
      Se o hotfix não estiver em PROD em até 1 h, voltar o MFE para a tag
      rollback-ui-review-u14-f1-controllership-finance (estado F1, sem o Panorama novo) e seguir.

H2 · AC-TAB-3 FAIL — tabela de ocorrências ainda rola em 1440 (medido: 1.451 px para 1.341 px)
   Causas medidas em PROD:
   a) A preferência de colunas salva antes da U14 (`controllership-finance:entry-audit:occurrences:
      columns:v1`, com field:true) vence o `defaultColumnVisibility` novo — todo usuário que já abriu
      a tela continua vendo «Campo». Subir a chave para `…:columns:v2` nas tabelas cujas colunas
      padrão mudaram (o kit não mescla padrão novo com preferência antiga).
   b) A coluna XML tem 336 px porque recebe a chave de acesso de 44 dígitos sem quebra. Exibir a
      chave abreviada (início…fim) com o valor completo no title e botão/ação de copiar, ou permitir
      quebra — e aplicar o teto de largura com reticências também em Protheus/XML.
   c) Prova: Playwright em 1440 com storage limpo E com a chave v1 antiga presente — scrollWidth ≤
      clientWidth do contêiner da tabela.

H3 · AC-GRA-3 FAIL — EXECUTION_DRIFT na premissa «o kit só tem área linear»
   O kit exporta BarSeriesChart (@delpi/plugin-ui/index; em uso em
   plugins/estoque-seguranca/src/components/ConsumptionAnalysisDistribution.tsx). Usar barras por dia,
   com o período anterior como referência alinhada por dia, pelo adaptador Cf* (criar o adaptador se
   faltar, como os demais).

H4 · AC-KPI-2 FAIL — título «Ocorrências pendentes» cortado (scrollWidth > clientWidth em 1440)
   O AC pedia título em uma linha encurtando, não cortando: «Pendentes» (ajuda explica).

H5 · Menor — ordem dos tipos: hero «NF-e e CT-e», tabela de análises «CT-e, NF-e». Usar
   DOCUMENT_TYPE_ORDER em todo lugar.

H6 · Processo de verificação (lição desta rodada)
   AC visual não pode ser PASS «no código». No pedido ao verificador, para cada AC visual, anexar a
   MEDIÇÃO (Playwright: larguras, alturas, scrollWidth/clientWidth, posição de rótulos) em HML, e
   pedir ao verificador que reprove AC visual sem medição. Rodar o axe (AC-DOD-2) — ficou
   INCONCLUSIVE na U14.

REGRAS
As da trilha e do prompt U14 (main sem branch; git add só com caminhos explícitos; verificador antes
de commit/deploy, até 3 rodadas; sem mexer no plugin-ui; sem mudança de regra/permissão).

ENTREGA
H1 sozinho e primeiro (hotfix em PROD). Depois H2–H5 numa fase só → verificador → HML → PROD
(tag rollback-ui-review-u14r2-controllership-finance). Parar ao concluir.

REPORT
H1: causa, diff, medição de geometria antes/depois, horário em PROD. H2: largura antes/depois com
storage limpo e com v1. H3: componente usado. H4/H5. axe. Vereditos do verificador sem edição.
```
