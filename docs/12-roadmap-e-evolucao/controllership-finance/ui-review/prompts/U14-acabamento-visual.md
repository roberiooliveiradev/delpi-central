# Prompt para o Cursor — UI review, U14 (acabamento visual da Auditoria de Entradas)

```text
PROMPT CURSOR — UI REVIEW · U14 — acabamento visual da entrada e do resultado da análise; sai o card
«Pergunte à CLARA»

CONTEXTO
O Claude abriu em PROD (15/11/2026, navegador do owner) a entrada da Auditoria e a análise 07–13/11
(filiais 01+02), em 1440×900 e em ≈800 px, e mediu o DOM. O owner aprovou todos os apontamentos e
decidiu: a CLARA é um MCP usado no ChatGPT/Claude, não um assistente dentro do Portal — sai o card
«Pergunte à CLARA» e tudo que convida a usar a CLARA de dentro da tela.

MISSÃO — executar Y1 → Y6, um commit por item, push a cada commit, track.md atualizado.

Y1 · Entrada da Auditoria (EntryAuditHomePage)
 a) Cabeçalhos misturados: «Período/Situação/Criada em» em caixa normal (botão de ordenar) e
    «FILIAIS/TIPOS» em maiúsculas (sem ordenação). Tornar Filiais e Tipos ordenáveis (lista branca de
    análises na BFF: branches, document_types — aditivo, contrato §6, teste) e usar UM padrão de
    cabeçalho em todas as tabelas do MFE (o do Comercial: `sentenceHeadersWrap` do kit, ou o que o
    Comercial usa nas tabelas ordenáveis — conferir e seguir). A seta de ordenar fica junto do nome,
    não encostada na coluna seguinte.
 b) Filtros no hero sem moldura dupla: a faixa de filtros não pode ser uma segunda caixa com borda
    dentro do hero (§14 «uma moldura»; conferir CustomersPage do Comercial). «Executar auditoria» na
    mesma linha dos campos a partir de 1024 px; abaixo disso, botão em largura total.
 c) Barra da tabela: Tabela/Cards, Itens por página, Fonte e Colunas numa linha só, alinhados como no
    Comercial; com poucas linhas (≤ 10) a barra não pode ser mais alta que a própria tabela.

Y2 · Indicadores e hero do resultado (EntryAuditAnalysisPage)
 a) Valor não quebra no meio: «R$ 1.060.126,08» quebrou em «R$ 1.060.126,» + «08». Valor do KPI em
    uma linha (white-space: nowrap no valor); se não couber, formato compacto («R$ 1,06 mi») com o
    valor completo no title/ajuda. Títulos dos KPIs sem quebrar (encurtar: «Pendentes»).
 b) «Sem análise do período anterior para comparar» aparece em 3 cartões e deixa todos altos. Dizer
    UMA vez, numa linha discreta logo abaixo da faixa de KPIs; cartões sem o texto e da mesma altura.
 c) Hero: escopo «Filial 01 · SC · Filial 02 · ES · CT-e · NF-e» → «Filiais 01 (SC) e 02 (ES) ·
    NF-e e CT-e». Botões: hierarquia clara (Exportar principal; Executar de novo e Nova análise com a
    mesma variante secundária do kit); o cinza atual parece desabilitado.

Y3 · Gráficos do resultado
 a) Panorama: tirar os quadrinhos «SEM PAR EM ABERTO / EXPLICADAS» (texto quebra palavra a palavra e
    é cortado; «Sem par em aberto» já é KPI). «Explicadas» vira uma linha da legenda da Conformidade.
    Meia-lua e rosca com o mesmo tamanho visual (mesma altura de área de gráfico).
 b) Evolução por dia: eixo com TODOS os dias do período (07–13/11 mostrava só 09–13/11; dia sem
    ocorrência = 0 — conferir na regra que dia sem dado é 0 e não indisponível). Barras por dia
    (contagem discreta) em vez de curva suavizada que inventa valores entre os dias; com anterior, a
    série anterior como barra/linha de referência alinhada por dia. Título do eixo: «Ocorrências».
 c) Onde estão as ocorrências: TES com descrição («148 · Compra p/ industrialização»), não só o
    código. A BFF já tem a descrição da SF4 na aba TES; levar `label` aditivo em breakdowns.tes
    (contrato §6, teste) — se não der sem consulta nova ao Protheus, V4. Temas com rótulo de negócio:
    «Itens» → «Itens da nota», «Cabeçalho» → «Cabeçalho da nota» (catálogo de temas, sem mudar regra).

Y4 · Abas e tabela de ocorrências
 a) Contadores em todas as abas ou em nenhuma: CT-e e TES utilizadas estão sem número. Usar o total
    que a BFF já devolve (se uma aba não tiver total sem carregar, mostrar após a primeira carga).
 b) Coluna «Status» → «Situação» (vocabulário PT-BR; procurar outros cabeçalhos em inglês no MFE).
 c) Tabela cabe na tela de 1440: hoje 1.856 px para 1.341 px de espaço. defaultColumnVisibility
    sem «Campo» (o nome da regra já diz o campo) ou outra escolha justificada; Fornecedor e Regra com
    largura máxima e reticências (texto completo no title); Protheus/XML/Diferença alinhados à
    direita quando numéricos. Sem rolagem horizontal em 1440 com as colunas padrão.
 d) Itens por página padrão 25 nas tabelas da análise (o usuário pode trocar; preferência guardada
    pelo kit).

Y5 · Sai o «Pergunte à CLARA» (decisão do owner)
 a) Remover o card «Pergunte à CLARA» da análise (EntryAuditAnalysisPage) e o texto de ajuda
    correspondente (helpTooltips «A CLARA lê a mesma análise…»).
 b) Detalhe da ocorrência (EntryAuditOccurrencePage): remover o botão «Copiar pergunta para a CLARA»
    e o bloco «Sugestão da CLARA» — o campo `clara_suggestion` não é produzido pela BFF (nenhuma
    ocorrência no backend); remover do tipo do MFE.
 c) Página Ajuda e textos do Portal: nada que convide a usar a CLARA dentro do Portal. NÃO mexer na
    página de consentimento (ClaraConsentPage) nem no MCP, que seguem existindo.
 d) Teste: a análise e o detalhe não renderizam nada com «CLARA».

Y6 · Seleção nos gráficos (defeito achado pelo owner em PROD, 15/11)
 Reprodução: análise 07–13/11 → clicar «Alta» na rosca de Severidade → URL ganha severity=high,
 KPIs e gráficos filtram → clicar «Limpar seleção» abaixo da rosca: nada acontece (URL continua com
 severity=high; nenhuma navegação — conferido com history instrumentado).
 Causa: EntryAuditAnalysisPage, CfDistributionDonut
   onSelect={(item) => { if (item) navigateWith({ severity: severityToUrl(item.id) }); }}
 O kit chama onSelect(null) tanto em «Limpar seleção» quanto ao clicar de novo na fatia selecionada;
 o `if (item)` descarta o null. O chip «Severidade: Alta» em «Filtros aplicados» funciona.
 a) onSelect(null) → navigateWith({ severity: "" }). Clicar de novo na fatia selecionada limpa.
 b) Barras (tema, fornecedor, TES): clicar de novo na barra selecionada limpa o filtro (hoje só
    reaplica o mesmo valor) — mesmo comportamento da rosca.
 c) Gráfico que seleciona não filtra a si mesmo: com «Alta» selecionada a rosca virou uma fatia só
    (100%) e o usuário perde o contexto para trocar de severidade. Cada gráfico de seleção (rosca de
    severidade; barras de tema, fornecedor e TES) é calculado com todos os filtros de detalhamento
    MENOS o da própria dimensão; a fatia/barra selecionada fica destacada e as outras esmaecidas
    (o kit já faz isso com selectedId). KPIs, Conformidade, Evolução e tabela seguem com todos os
    filtros. Na BFF (breakdowns), aditivo e documentado no contrato §6; teste por dimensão.
 d) «Filtros aplicados» ganha «Limpar filtros» (remove todos os filtros de detalhamento de uma vez).
 e) Testes: selecionar Alta mantém as 3 fatias com Alta destacada; «Limpar seleção» e novo clique na
    fatia removem severity da URL e voltam os números; o mesmo para uma barra; «Limpar filtros» zera
    todos. Playwright em HML com a mesma reprodução.

DoD (cada item)
1440/1024/390, claro e escuro, teclado e foco, axe sem violação nova (exceções da U13 inalteradas),
ajuda no mesmo commit. Screenshots antes/depois no report (não commitar).

ENTREGA
HML → PROD. Tags rollback-ui-review-u14-controllership-finance (e -api se a BFF mudar em Y1a/Y3c/Y6c).
BFF primeiro, depois MFE. Parar ao concluir.

REGRAS
As da trilha (main sem branch; git add só com caminhos explícitos; sem mudança de regra de negócio
nem permissão; contrato só aditivo; sem dado real no repositório; paradas V1–V6). Não mexer no
plugin-ui (se faltar algo no kit, registrar e parar — V3).

REPORT
Por item: o que mudou, SHA, testes, antes/depois nos três tamanhos. Y3c: como a descrição da TES
chegou. Y4c: largura da tabela antes/depois em 1440. Y5: lista do que saiu. Quadro final.
```
